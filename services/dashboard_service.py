from __future__ import annotations

from typing import Any

import httpx

# AstrBot 统一日志对象。
from astrbot.api import logger

from ..utils.config_parser import get_int_value

# 渲染层：把结构化数据转成可直接回复的文本。
from .message_renderer import render_dashboard_message_with_count

# 请求层：负责向 Live Dashboard 拉取原始状态数据。
from .payload_client import fetch_current_payload


class DashboardService:
    """业务编排层：负责调用外部接口并渲染回复文本。"""

    def __init__(self, config: dict[str, Any]):
        """保存插件配置，供后续请求和渲染阶段使用。"""
        self.config = config
        timeout_sec = get_int_value(
            config, "request_timeout_sec", 30, min_value=1, max_value=60
        )
        self._http_client = httpx.AsyncClient(timeout=timeout_sec)

    async def close(self) -> None:
        """释放服务层资源。"""
        await self._http_client.aclose()
        logger.info("[视奸面板] HTTP 客户端已关闭")

    async def query_and_render(self) -> tuple[str, int]:
        """拉取实时状态并输出可发送文本与设备数量。"""
        # 读取基础地址（允许用户误填前后空格，因此先 strip）。
        base_url = str(self.config.get("base_url", "")).strip()
        # 地址未配置时直接返回可读提示，避免继续请求导致无意义异常。
        if not base_url:
            logger.warning("[视奸面板] 配置缺失：服务地址未填写")
            return "未配置 Live Dashboard 地址，请在插件配置中填写 base_url。", 0

        try:
            # 该日志用于调试阶段定位调用链路（默认 INFO 下不输出）。
            logger.debug("[视奸面板] 开始请求上游状态接口")

            # 从上游拉取当前状态 payload（dict）。
            payload = await fetch_current_payload(self.config, client=self._http_client)

            # 仅用于调试观察：统计上游返回的设备数量。
            device_count = (
                len(payload.get("devices", []))
                if isinstance(payload.get("devices"), list)
                else 0
            )
            logger.debug("[视奸面板] 上游请求成功，设备数：%s", device_count)

            # 把上游数据按配置开关渲染成最终回复文本，并返回展示设备数。
            rendered_message, render_device_count = render_dashboard_message_with_count(
                payload,
                self.config,
            )

            # 记录最终输出长度，方便定位“回复过长/过短”的问题。
            logger.info(
                "[视奸面板] 文本渲染完成，回复字符数：%s, 展示设备数：%s",
                len(rendered_message),
                render_device_count,
            )
            return rendered_message, render_device_count

        except httpx.TimeoutException:
            # 超时通常是上游慢或网络抖动，提示用户稍后再试。
            logger.warning("[视奸面板] 请求超时：Live Dashboard 响应过慢")
            return "请求超时：Live Dashboard 响应过慢，请稍后重试。", 0

        except httpx.HTTPStatusError as exc:
            # HTTP 层已连通，但返回非 2xx 状态。
            status_code = exc.response.status_code
            logger.warning("[视奸面板] HTTP 状态异常，状态码：%s", status_code)

            # 401/403 常见于代理鉴权或 token 配置问题。
            if status_code in (401, 403):
                return (
                    "鉴权失败：请检查 auth_token 是否正确，或确认服务端是否允许访问 /api/current。",
                    0,
                )

            # 其他状态码统一提示。
            return f"请求失败：服务端返回 HTTP {status_code}。", 0

        except httpx.RequestError as exc:
            # 网络层错误（DNS、连接失败、证书等）。
            logger.warning("[视奸面板] 网络请求异常：%s", exc)
            return "网络错误：无法连接到 Live Dashboard 服务。", 0

        except Exception as exc:  # noqa: BLE001
            # 兜底异常，避免插件因未预期错误中断命令处理。
            logger.exception("[视奸面板] 未预期异常：%s", exc)
            return "发生未预期错误：请查看 AstrBot 日志。", 0

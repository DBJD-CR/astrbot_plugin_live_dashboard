from __future__ import annotations

from typing import Any

import httpx

# AstrBot 统一日志对象，用于记录请求链路关键信息。
from astrbot.api import logger

# 配置读取工具：统一处理默认值、类型转换与边界裁剪。
from ..utils.config_parser import get_int_value, get_text_value


def _build_headers(config: dict[str, Any]) -> dict[str, str]:
    """构建请求头。

    当前策略：
    - 默认声明接收 JSON。
    - 若配置了 auth_token，则附加 Bearer 认证头。
    """
    headers: dict[str, str] = {"Accept": "application/json"}

    # 读取可选 token（空字符串表示不启用鉴权头）。
    auth_token = get_text_value(config, "auth_token", "")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    return headers


def _build_url(config: dict[str, Any]) -> str:
    """拼接上游 current 接口完整 URL。"""
    # 去掉 base_url 末尾斜杠，防止出现 //api/current。
    base_url = get_text_value(config, "base_url", "").rstrip("/")
    return f"{base_url}/api/current"


async def fetch_current_payload(
    config: dict[str, Any], *, client: httpx.AsyncClient | None = None
) -> dict[str, Any]:
    """获取 Live Dashboard 当前状态数据。

    返回值：
    - 成功时返回 JSON dict。
    - 失败时抛出异常，由上层服务统一处理并转用户提示。
    """
    # 读取超时配置，并限制在 1~60 秒之间，避免异常配置。
    timeout_sec = get_int_value(
        config, "request_timeout_sec", 30, min_value=1, max_value=60
    )
    # 根据配置构建目标 URL。
    url = _build_url(config)
    # 根据配置构建请求头（含可选鉴权）。
    headers = _build_headers(config)

    # 记录请求关键参数，便于排查“地址错/超时短/鉴权未生效”等问题。
    logger.info(
        "[视奸面板] 已发起请求，地址：%s, 超时：%s秒, 鉴权：%s",
        url,
        timeout_sec,
        "开启" if "Authorization" in headers else "关闭",
    )

    # 支持注入长生命周期客户端；未注入时回退到临时客户端。
    owns_client = client is None
    request_client = client or httpx.AsyncClient(timeout=timeout_sec)

    try:
        response = await request_client.get(url, headers=headers)

        # 先记录状态码，再由 raise_for_status 统一抛出非 2xx 异常。
        logger.info("[视奸面板] 收到响应，状态码：%s", response.status_code)
        response.raise_for_status()

        # 解析响应 JSON。
        data = response.json()
    finally:
        if owns_client:
            await request_client.aclose()

    # 防御式校验：要求最外层必须是对象，便于后续按键访问。
    if not isinstance(data, dict):
        logger.error("[视奸面板] 响应结构异常：响应体不是 JSON 对象")
        raise ValueError("/api/current 响应不是 JSON 对象")

    # 仅在 DEBUG 下输出字段概览，避免 INFO 日志过载。
    logger.debug("[视奸面板] 响应解析完成，字段列表：%s", list(data.keys()))
    return data

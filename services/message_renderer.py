from __future__ import annotations

import re
from typing import Any

# 日志对象：用于记录渲染链路的调试信息（主要使用 DEBUG）。
from astrbot.api import logger

# 配置读取工具：统一处理类型转换和默认值。
from ..utils.config_parser import (
    get_bool_value,
    get_int_value,
    get_text_value,
    parse_list_config,
)

# 时间格式化工具：把 ISO 时间转换为本地可读格式。
from ..utils.time_formatter import format_time_text
from .app_descriptions import (
    APP_DESCRIPTIONS_LOWER,
    APP_PLACEHOLDER_VALUES,
    DEFAULT_DESCRIPTION,
    DISPLAY_TITLE_PLACEHOLDER_VALUES,
    MUSIC_APP_NAMES,
    TITLE_TEMPLATES_LOWER,
)


def _is_online(device_item: dict[str, Any]) -> bool:
    """判断设备是否在线。

    兼容场景：
    - bool: True / False
    - int: 1 / 0
    - str: "1" / "true" / "True"
    """
    value = device_item.get("is_online", 0)

    # 布尔值直接返回。
    if isinstance(value, bool):
        return value
    # 数值按 1 表示在线。
    if isinstance(value, int):
        return value == 1
    # 字符串做兼容解析。
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true"}

    # 其他未知类型默认按离线处理（保守策略）。
    return False


def _clean_text(value: Any) -> str:
    """安全转字符串并去除首尾空白。"""
    if value is None:
        return ""
    return str(value).strip()


def _is_app_placeholder(app_name: str) -> bool:
    """判断 app_name 是否为占位值。"""
    return app_name.strip().lower() in APP_PLACEHOLDER_VALUES


def _normalize_display_title(display_title: str, app_name: str) -> str:
    """清理 display_title 占位值与重复值。"""
    title = display_title.strip()
    if not title:
        return ""

    lower_title = title.lower()
    if lower_title in DISPLAY_TITLE_PLACEHOLDER_VALUES:
        return ""

    app_clean = app_name.strip()
    if app_clean and lower_title == app_clean.lower():
        return ""

    return title


def _friendly_app_name(app_name: str) -> str:
    """用于“应用：”字段的友好展示值。"""
    name = app_name.strip()
    if not name:
        return "未识别应用"
    if _is_app_placeholder(name):
        return "未识别应用"
    return name


def _format_battery(extra_data: dict[str, Any]) -> str:
    """格式化电量文本。"""
    battery_percent = extra_data.get("battery_percent")
    battery_charging = extra_data.get("battery_charging")

    # 无有效电量数值时返回默认说明，保证字段稳定。
    if not isinstance(battery_percent, (int, float)):
        return "未知"

    # 电量百分比统一取整展示。
    percent_text = f"{round(float(battery_percent))}%"

    # 若上报了充电状态，则附加“充电中/未充电”。
    if isinstance(battery_charging, bool):
        return f"{percent_text} {'⚡充电中' if battery_charging else '未充电'}"

    return percent_text


def _extract_music(extra_data: dict[str, Any]) -> dict[str, str]:
    """抽取并规整音乐信息。"""
    music_data = extra_data.get("music")
    if not isinstance(music_data, dict):
        return {}

    return {
        "title": _clean_text(music_data.get("title")),
        "artist": _clean_text(music_data.get("artist")),
        "app": _clean_text(music_data.get("app")),
    }


def _format_music(extra_data: dict[str, Any]) -> str:
    """格式化音乐信息文本。"""
    music_data = _extract_music(extra_data)
    title_text = music_data.get("title", "")
    artist_text = music_data.get("artist", "")
    app_text = music_data.get("app", "")

    # 三项都为空则返回默认说明，保证字段稳定。
    if not any([title_text, artist_text, app_text]):
        return "暂无播放"

    # 优先组合为“歌手 - 歌名”。
    core_text = ""
    if title_text and artist_text:
        core_text = f"{artist_text} - {title_text}"
    else:
        core_text = title_text or artist_text or ""

    # 若包含播放器名，按“核心文本 (播放器)”展示。
    if app_text:
        if core_text:
            return f"{core_text} ({app_text})"
        return app_text

    return core_text


def _steam_title_to_description(display_title: str) -> str:
    """复刻上游 Steam 模板的特殊判断逻辑。"""
    title_lower = display_title.lower()

    if title_lower in {"steam", ""}:
        return "正在浏览 Steam 喵~"
    if title_lower == "好友列表":
        return "正在与 Steam 好友聊天喵~"
    if re.match(r"^[0-9a-f]{20,}$", display_title, flags=re.IGNORECASE):
        return "正在浏览 Steam 喵~"
    if (
        len(display_title) <= 20
        and " " not in display_title
        and not re.search(r"[a-z]{3,}", display_title, flags=re.IGNORECASE)
    ):
        return "正在与 Steam 好友聊天喵~"

    return f"正在Steam玩「{display_title}」喵~"


def _build_activity_description(
    app_name: str, display_title: str, extra_data: dict[str, Any]
) -> str:
    """复刻上游 getAppDescription 核心逻辑（Python 版）。"""
    cleaned_app = app_name.strip()
    cleaned_title = _normalize_display_title(display_title, cleaned_app)

    if not cleaned_app:
        return DEFAULT_DESCRIPTION

    app_lower = cleaned_app.lower()

    if app_lower == "idle":
        return "暂时离开了喵~"

    music_data = _extract_music(extra_data)
    is_music_app_foreground = app_lower in MUSIC_APP_NAMES

    base_text = ""

    # 若有 display_title，优先使用模板；但音乐应用且有 music.title 时跳过模板，避免与 ♪ 信息重复。
    if cleaned_title and not (is_music_app_foreground and music_data.get("title")):
        if app_lower == "steam":
            base_text = _steam_title_to_description(cleaned_title)
        else:
            template = TITLE_TEMPLATES_LOWER.get(app_lower)
            if template:
                base_text = template.format(title=cleaned_title)

    # 未命中模板时走描述映射。
    if not base_text:
        mapped = APP_DESCRIPTIONS_LOWER.get(app_lower)
        if mapped:
            base_text = mapped

    # 最终兜底：有标题显示标题，否则默认文案。
    if not base_text:
        if cleaned_title:
            base_text = f"正在玩「{cleaned_title}」喵~"
        else:
            base_text = DEFAULT_DESCRIPTION

    return base_text


def _parse_keyword_list(raw_text: str) -> list[str]:
    """解析关键词列表（支持逗号/分号/换行分隔）。"""
    return parse_list_config(raw_text, to_lower=True)


def _build_device_search_text(device_item: dict[str, Any]) -> str:
    """构建设备关键词匹配文本（仅 device_name，统一小写）。"""
    return _clean_text(device_item.get("device_name")).lower()


def _match_device_keywords(device_item: dict[str, Any], keywords: list[str]) -> bool:
    """关键词命中判断：任意关键词为子串即命中。"""
    if not keywords:
        return False

    haystack = _build_device_search_text(device_item)
    if not haystack:
        return False

    return any(keyword in haystack for keyword in keywords)


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    """判断文本是否命中任意关键词（大小写不敏感、子串匹配）。"""
    if not text or not keywords:
        return False

    haystack = text.lower()
    return any(keyword in haystack for keyword in keywords)


def _mask_sensitive_text(text: str, keywords: list[str], replacement: str) -> str:
    """对命中敏感关键词的文本执行替换。"""
    if _contains_keyword(text, keywords):
        return replacement
    return text


def _apply_device_keyword_filters_with_keywords(
    device_items: list[dict[str, Any]],
    whitelist_keywords: list[str],
    blacklist_keywords: list[str],
) -> list[dict[str, Any]]:
    """按已解析关键词对白名单/黑名单进行设备筛选。"""
    filtered_items = device_items

    # 白名单：仅保留命中关键词的设备。
    if whitelist_keywords:
        filtered_items = [
            item
            for item in filtered_items
            if _match_device_keywords(item, whitelist_keywords)
        ]

    # 黑名单：移除命中关键词的设备（优先级高于白名单）。
    if blacklist_keywords:
        filtered_items = [
            item
            for item in filtered_items
            if not _match_device_keywords(item, blacklist_keywords)
        ]

    logger.debug(
        "[视奸面板] 关键词筛选：白名单数：%s, 黑名单数：%s, 筛选前：%s, 筛选后：%s",
        len(whitelist_keywords),
        len(blacklist_keywords),
        len(device_items),
        len(filtered_items),
    )

    return filtered_items


def _select_devices_for_render(
    payload_data: dict[str, Any], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], int, int]:
    """统一产出渲染所需设备列表与在线/总数统计。"""
    all_devices_raw = payload_data.get("devices", [])
    all_devices = (
        [item for item in all_devices_raw if isinstance(item, dict)]
        if isinstance(all_devices_raw, list)
        else []
    )

    whitelist_keywords = _parse_keyword_list(
        get_text_value(config, "device_whitelist_keywords", "")
    )
    blacklist_keywords = _parse_keyword_list(
        get_text_value(config, "device_blacklist_keywords", "")
    )

    counted_devices = _apply_device_keyword_filters_with_keywords(
        all_devices,
        whitelist_keywords,
        blacklist_keywords,
    )
    total_count = len(counted_devices)
    online_count = sum(1 for item in counted_devices if _is_online(item))

    include_offline_devices = get_bool_value(config, "include_offline_devices", False)
    max_devices = get_int_value(config, "max_devices", 10, min_value=1, max_value=100)

    device_items = counted_devices
    if not include_offline_devices:
        device_items = [item for item in device_items if _is_online(item)]

    device_items.sort(
        key=lambda item: (
            0 if _is_online(item) else 1,
            str(item.get("device_name", "")),
        )
    )

    return device_items[:max_devices], online_count, total_count


def render_dashboard_message_with_count(
    payload_data: dict[str, Any], config: dict[str, Any]
) -> tuple[str, int]:
    """渲染文本并返回展示设备数，避免调用方重复计算。"""
    device_items, online_count, total_count = _select_devices_for_render(
        payload_data,
        config,
    )

    # 读取所有显示开关（由 _conf_schema.json 定义）。
    show_platform = get_bool_value(config, "show_platform", True)
    show_app_name = get_bool_value(config, "show_app_name", True)
    show_display_title = get_bool_value(config, "show_display_title", True)
    show_battery = get_bool_value(config, "show_battery", True)
    show_music = get_bool_value(config, "show_music", True)
    show_last_seen = get_bool_value(config, "show_last_seen", True)
    show_viewer_count = get_bool_value(config, "show_viewer_count", False)
    show_server_time = get_bool_value(config, "show_server_time", False)
    info_blacklist_keywords = _parse_keyword_list(
        get_text_value(config, "info_blacklist_keywords", "")
    )
    info_blacklist_replacement = (
        get_text_value(
            config, "info_blacklist_replacement", "不想让你看到我在干什么喵~"
        )
        or "不想让你看到我在干什么喵~"
    )

    # 初始化输出文本行。
    lines: list[str] = [
        "📊 Live Dashboard 状态面板",
        f"在线设备：{online_count}/{total_count}",
    ]

    # 调试日志：输出本次渲染基础统计与关键开关状态。
    logger.debug(
        "[视奸面板] 开始渲染消息，设备总数：%s, 在线数：%s, 显示平台：%s, 显示标题：%s",
        total_count,
        online_count,
        show_platform,
        show_display_title,
    )

    # 可选展示访客数。
    if show_viewer_count:
        viewer_count = payload_data.get("viewer_count")
        if isinstance(viewer_count, int):
            lines.append(f"当前访客：{viewer_count}")

    # 可选展示服务端时间。
    if show_server_time:
        server_time = payload_data.get("server_time")
        if isinstance(server_time, str) and server_time.strip():
            lines.append(f"服务端时间：{format_time_text(server_time)}")

    logger.debug("[视奸面板] 正在渲染设备列表...选中设备数：%s", len(device_items))

    # 没有可展示设备时返回简短提示。
    if not device_items:
        lines.append("")
        lines.append("暂无符合条件的设备状态喵。")
        return "\n".join(lines), 0

    # 设备区块与头部之间插入空行，提升可读性。
    lines.append("")

    # 逐台设备渲染。
    for device_item in device_items:
        # 设备基础信息。
        device_name = _clean_text(device_item.get("device_name")) or "未知设备"
        platform_text = _clean_text(device_item.get("platform")) or "unknown"
        app_name_raw = _clean_text(device_item.get("app_name"))
        display_title_raw = _clean_text(device_item.get("display_title"))
        status_online = _is_online(device_item)
        status_text = "在线" if status_online else "离线"

        # extra 字段容错处理。
        extra_data = device_item.get("extra", {})
        if not isinstance(extra_data, dict):
            extra_data = {}

        # 设备首行：设备名 + 在线状态 + 平台（可选）。
        head_text = f"• {device_name} [{status_text}]"
        if show_platform:
            head_text += f" ({platform_text})"
        lines.append(head_text)

        # 主叙事句：现在正在…（同样应用信息黑名单脱敏策略）。
        if status_online:
            activity_text = _build_activity_description(
                app_name_raw, display_title_raw, extra_data
            )
        else:
            activity_text = "离线休息中喵~"
        activity_text = _mask_sensitive_text(
            activity_text,
            info_blacklist_keywords,
            info_blacklist_replacement,
        )
        lines.append(f"  现在：{activity_text}")

        # 应用名（可选）：命中信息黑名单关键词时替换为统一文案。
        if show_app_name:
            app_name_text = _friendly_app_name(app_name_raw)
            app_name_text = _mask_sensitive_text(
                app_name_text,
                info_blacklist_keywords,
                info_blacklist_replacement,
            )
            lines.append(f"  应用：{app_name_text}")

        # display_title（可选）：命中信息黑名单关键词时替换为统一文案。
        if show_display_title:
            normalized_title = _normalize_display_title(display_title_raw, app_name_raw)
            title_text = normalized_title or "（无可展示标题）"
            if normalized_title:
                title_text = _mask_sensitive_text(
                    normalized_title,
                    info_blacklist_keywords,
                    info_blacklist_replacement,
                )
            lines.append(f"  标题：{title_text}")

        # 电量（可选）。
        if show_battery:
            battery_text = _format_battery(extra_data)
            lines.append(f"  🔋 电量：{battery_text}")

        # 音乐（可选）。
        if show_music:
            music_text = _format_music(extra_data)
            lines.append(f"  🎵 音乐：{music_text}")

        # 最后上报时间（可选）。
        if show_last_seen:
            last_seen = device_item.get("last_seen_at")
            if isinstance(last_seen, str) and last_seen.strip():
                lines.append(f"  🕒 上报：{format_time_text(last_seen)}")
            else:
                lines.append("  🕒 上报：暂无上报")

        # 每台设备之间留一个空行。
        lines.append("")

    # 去除尾部多余空行，保证回复结尾干净。
    while lines and not lines[-1].strip():
        lines.pop()

    # 合并文本并记录长度（DEBUG）。
    rendered = "\n".join(lines)
    logger.debug("[视奸面板] 渲染完成，回复字符数：%s", len(rendered))
    return rendered, len(device_items)

from __future__ import annotations

from typing import Any


def get_text_value(config: dict[str, Any], key: str, default: str = "") -> str:
    """读取字符串配置并去除首尾空白。

    设计目的：
    - 统一处理配置项中的 `None`、数字、布尔等非字符串输入。
    - 避免调用方重复写 `str(...).strip()` 的样板代码。
    """
    # 从配置中读取目标键，缺失时使用默认值。
    value = config.get(key, default)

    # 对 None 做特殊处理：保持默认值语义，避免把 None 转成字符串 "None"。
    if value is None:
        return default

    # 统一转字符串并去除首尾空白。
    return str(value).strip()


def get_bool_value(config: dict[str, Any], key: str, default: bool = False) -> bool:
    """读取布尔配置，兼容常见字符串写法。

    支持的“真值”字符串：
    - "1" / "true" / "yes" / "on"（大小写不敏感）
    """
    # 读取原始值。
    value = config.get(key, default)

    # 若本身就是 bool，直接返回。
    if isinstance(value, bool):
        return value

    # 字符串按约定真值集合解析。
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}

    # 其他类型（如 int/float/list）回退到 Python 原生 bool 语义。
    return bool(value)


def get_int_value(
    config: dict[str, Any],
    key: str,
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """读取整数配置，并可选执行上下限裁剪。

    典型用途：
    - 请求超时秒数
    - 最大展示数量
    - 各类阈值参数
    """
    # 先取原始配置值，缺失时使用默认值。
    value = config.get(key, default)

    # 尝试转换为 int，失败则回退默认值。
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default

    # 若配置了最小值，执行下限保护。
    if min_value is not None:
        number = max(min_value, number)

    # 若配置了最大值，执行上限保护。
    if max_value is not None:
        number = min(max_value, number)

    return number

from typing import Callable, Any

from dataclasses import dataclass


@dataclass(frozen=True)
class TableField:
    key: str
    validator: Callable = None
    default_value: Any = ''

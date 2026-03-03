from __future__ import annotations

from typing import Dict, List, Tuple

from django.db import models


class TasteLevel:
    _VALUES: Dict[int, Tuple[str, str]] = {
        1: ("LOW", "低"),
        2: ("MEDIUM", "中"),
        3: ("HIGH", "高"),
    }

    @classmethod
    def choices(cls) -> List[Tuple[int, str]]:
        return [(value, label) for value, (_, label) in cls._VALUES.items()]

    @classmethod
    def to_code(cls, db_value: int | None) -> str | None:
        if db_value is None:
            return None
        return cls._VALUES[db_value][0]

    @classmethod
    def to_label(cls, db_value: int | None) -> str | None:
        if db_value is None:
            return None
        return cls._VALUES[db_value][1]

    @classmethod
    def from_code(cls, code: str) -> int:
        for value, (item_code, _) in cls._VALUES.items():
            if item_code == code:
                return value
        raise KeyError(code)

    @classmethod
    def is_valid_value(cls, db_value: int | None) -> bool:
        return db_value in cls._VALUES

    @classmethod
    def is_valid_code(cls, code: str) -> bool:
        return any(item_code == code for item_code, _ in cls._VALUES.values())


class IngredientCategory(models.IntegerChoices):
    MEAT = 0, "肉"
    FISH = 1, "魚"
    EGG = 2, "卵"
    VEGETABLE = 3, "野菜"
    BEAN = 4, "豆"
    FROZEN = 5, "冷凍"

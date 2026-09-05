"""
Библиотека функций валидации параметров.

Сигнатура: def validator(ctx, value) -> str | None
    ctx   — FormulaContext (для проверки значений других параметров);
    value — вычисленное/введённое значение проверяемого параметра.
Возвращает текст ошибки или None (ошибок нет).

ВАЖНО: имя функции, указанное в `formula_config["validate"]` параметра, должно
СОВПАДАТЬ с именем функции в этом модуле — реестр строится автоматически.
"""

from .engine import FormulaContext


def validate_nonzero(ctx: FormulaContext, value):
    """Значение не должно быть равно нулю."""
    try:
        if value is not None and float(value) == 0:
            return "Значение не может быть равным 0"
    except (TypeError, ValueError):
        pass
    return None


def validate_positive(ctx: FormulaContext, value):
    """Значение должно быть положительным."""
    try:
        if value is None or float(value) <= 0:
            return "Значение должно быть положительным числом"
    except (TypeError, ValueError):
        return "Значение должно быть числом"
    return None


def validate_max_below_param(ctx: FormulaContext, value):
    """
    Пример зависимой валидации: значение не должно превышать значение другого
    параметра «Ограничение».
    """
    limit = ctx.get_opt("Ограничение")
    if limit is None:
        return None
    try:
        if float(value) > float(limit):
            return f"Значение не должно превышать {limit}"
    except (TypeError, ValueError):
        return None
    return None
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


def _find_actual_key(ctx: FormulaContext, *keywords: str, fallback: str) -> str:
    """Синхронный поиск фактического имени параметра по ключевым словам.

    Для валидаторов (не могут ходить в БД): смотрим ключи выбранных и
    вычисленных значений. Точное переопределение именем не поддерживается —
    валидатор применяется к конкретному параметру, а зависимости ищутся
    по ключевым словам (устойчиво к суффиксам размерности и переименованиям).
    """
    lowered = [str(k).strip().lower() for k in keywords if k and str(k).strip()]
    for name in list(ctx.selected or {}) + list(ctx.computed or {}):
        if name and any(kw in str(name).lower() for kw in lowered):
            return name
    return fallback


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

def validate_T_PK(ctx: FormulaContext, value):
    """
    Температура должна быть в диапазоне от -60°С до 600°С для пружинных и от -60°С до 250°С для пилотных
    """
    valve_type = ctx.get_opt(_find_actual_key(ctx, "тип клапана", fallback="Тип клапана"))
    if valve_type is None:
        return None
    try:
        if valve_type == "Пружинный (В)" and (float(value) > 600 or float(value) < -60):
            return "Температура должна быть в диапазоне от -60°С до 600°С для пружинных клапанов"
        if valve_type == "Пилотный (П)" and (float(value) > 250 or float(value) < -60):
            return "Температура должна быть в диапазоне от -60°С до 250°С для пилотных клапанов"
        # else:
        #     return value
    except (TypeError, ValueError):
        return None
    return None


def validate_pressure_setting(ctx: FormulaContext, value):
    """Давление настройки должно быть в диапазоне от 0 до 16 (кгс/см²)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "Давление настройки должно быть числом"
    if v < 0 or v > 16:
        return "Давление настройки не может быть меньше 0 и больше 16"
    return None


def validate_backpressure(ctx: FormulaContext, value):
    """Противодавление не должно превышать 70% давления настройки и быть меньше 0."""
    pn = ctx.get_opt(_find_actual_key(ctx, "давление настройки", fallback="Давление настройки"))
    if pn is None:
        return None
    try:
        v = float(value)
        limit = float(pn) * 0.7
    except (TypeError, ValueError):
        return None
    if v > limit or v < 0:
        return f"Значение не может быть больше 70% давления настройки ({limit:.2f}) и меньше 0"
    return None


def validate_mixture_composition(ctx: FormulaContext, value):
    """
    Проверяет состав смеси из select-input параметра «Характеристики среды»:
    значение — массив пар {название среды: мольная доля}. Долей должна быть
    суммарно ровно 100% и минимум две среды.
    """
    import json

    if value is None or value == "":
        return None

    raw = value
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return "Нужно выбрать состав из списка сред и указать их мольные доли (%)"

    if not isinstance(raw, list):
        return None

    pairs = []
    for item in raw:
        if not isinstance(item, dict) or not item:
            continue
        name = next(iter(item), None)
        share = item.get(name) if name is not None else None
        if name is None or share is None:
            continue
        try:
            pairs.append((str(name).strip(), float(share)))
        except (TypeError, ValueError):
            continue

    if len(pairs) < 2:
        return "Смесь не может состоять менее чем из двух сред!"

    total = sum(share for _, share in pairs)
    if abs(total - 100.0) > 0.0001:
        return f"Сумма мольных долей сред смеси должна составлять 100%, а не {total}%"

    return None
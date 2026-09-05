"""
Библиотека функций расчёта параметров.

Каждая функция принимает контекст `ctx` и возвращает значение параметра
(число, строка, список и т.п.). Значения зависимых параметров получаются через:

    ctx.get("Параметр")     # требует значение; если не выбрано — функция
                            # останавливается, в параметр вернётся просьба заполнить
    ctx.get_opt("Параметр") # None, если параметр не выбран
    ctx.num("Параметр")     # как get, но приводит к float

ВАЖНО: имя функции, указанное в `formula_config["func"]` параметра, должно
СОВПАДАТЬ с именем функции в этом модуле — реестр строится автоматически.
"""

from .engine import FormulaContext


def count_A(ctx: FormulaContext):
    """
    Пример функции из ТЗ: расчёт параметра А по Б, В и Г.

        Б и В могут быть определены таблицей, Г — ручной ввод.
        Если любой из них не выбран — пользователю вернётся просьба заполнить.
    """
    B = ctx.get("параметр Б")
    V = ctx.get("параметр В")
    G = ctx.get("параметр Г")

    if G != 0:
        return B * V / G
    return "Параметр Г определен неверно, значение не может быть равным '0'!"


def area_of_circle(ctx: FormulaContext):
    """Площадь круга по диаметру (пример использования ctx.num)."""
    from math import pi

    d = ctx.num("Диаметр")
    r = d / 2
    return round(pi * r * r, 4)


def duplicate_value(ctx: FormulaContext):
    """Возвращает значение другого параметра без изменений (передача значения)."""
    source = ctx.get("Исходный параметр")
    return source


async def file_by_construction(ctx: FormulaContext):
    construction = ctx.get("Тип среды")
    if not ctx.db or not ctx.product_id:
        return None

    target = "АМ211.jpg" if str(construction) == "Газ" else "АМ212.jpg"

    from sqlalchemy import text

    row = await ctx.db.execute(text(
        "SELECT file_url FROM parameter_files "
        "WHERE product_id = :pid AND name ILIKE :pattern LIMIT 1"
    ), {"pid": ctx.product_id, "pattern": f"%{target}%"})
    url = row.scalar_one_or_none()
    return url or None
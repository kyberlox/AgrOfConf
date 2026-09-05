"""
Интеграция новой системы формул в модуль табличного подбора.

- Параметры `type='Formula'`, у которых задан `formula_config.func`, вычисляются
  новым асинхронным движком (`compute_formulas`).
- Остальные формульные параметры (без нового конфига) обрабатываются старой
  системой `search_formula`/`CodeParametr` (fallback для совместимости).

Формат возвращаемых параметров сохраняется прежним (id, name, description,
all_values, response_value, visibility, required_type, sort, error).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.TablePakage.model.parameter_schema import ParameterSchema

from .engine import compute_formulas, FormulaContext
from .registry import get_validator


def _is_new_formula(param: Any) -> bool:
    """Параметр относится к новой системе формул?"""
    cfg = param.formula_config
    return isinstance(cfg, dict) and bool(cfg.get("func"))


async def _apply_new_formulas(
    db: AsyncSession,
    response_params: list[dict],
    selected_values: dict[str, Any],
    new_specs: list[dict],
    product_id: int,
) -> None:
    """Вычисляет новые формульные параметры и добавляет их в response_params."""
    results = await compute_formulas(db, new_specs, selected_values, product_id=product_id)

    name_to_existing = {item["name"]: item for item in response_params}

    for spec in new_specs:
        param = spec["param"]
        name = spec["name"]
        res = results.get(name, {})

        entry = name_to_existing.get(name)
        if entry is None:
            entry = {
                "id": param.id,
                "name": param.name,
                "description": param.description,
                "table_name": param.table_name,
                "all_values": None,
                "response_value": res.get("response_value"),
                "visibility": param.visibility,
                "editable": param.editable,
                "required_type": param.required_type,
                "sort": param.sort,
            }
            response_params.append(entry)

        if "error" in res:
            entry["error"] = res["error"]
        if "response_value" in res:
            entry["response_value"] = res["response_value"]


async def _add_input_params(
    db: AsyncSession,
    response_params: list[dict],
    selected_values: dict[str, Any],
    product_id: int,
) -> list[dict]:
    """Добавляет входные формульные параметры (без функции расчёта) в ответ.

    Такие параметры (например «Диаметр» с type=Formula, required_type=user_input
    и настроенным validate) пользователь заполняет вручную — они должны
    отображаться в форме подбора. Если задан валидатор — применяем его к введённому
    значению.
    """
    stmt = (
        select(ParameterSchema)
        .where(
            ParameterSchema.type == "Formula",
            ParameterSchema.product_id == product_id,
        )
        .order_by(ParameterSchema.sort)
    )
    result = await db.execute(stmt)
    formula_params = result.scalars().all()
    if not formula_params:
        return response_params

    existing_names = {item["name"] for item in response_params}
    ctx = FormulaContext(dict(selected_values), {})

    for param in formula_params:
        cfg = param.formula_config or {}
        if cfg.get("func"):
            continue  # такие считает асинхронный движок
        if param.name in existing_names:
            continue  # уже добавлен (например, legacy-обработчиком)

        rv = selected_values.get(param.name)
        error = None

        validate_name = cfg.get("validate")
        if validate_name and rv is not None:
            validator = get_validator(str(validate_name))
            if validator is not None:
                try:
                    msg = validator(ctx, rv)
                    if msg:
                        error = str(msg)
                except Exception as e:  # noqa: BLE001
                    error = str(e)

        entry = {
            "id": param.id,
            "name": param.name,
            "description": param.description,
            "table_name": param.table_name,
            "all_values": None,
            "response_value": rv,
            "visibility": param.visibility,
            "editable": param.editable,
            "required_type": param.required_type,
            "sort": param.sort,
        }
        if error:
            entry["error"] = error
        response_params.append(entry)

    return response_params


async def apply_new_and_legacy_formulas(
    db: AsyncSession,
    response_params: list[dict],
    selected_values: dict[str, Any],
    table_name_params: list[str],
    product_id: int,
) -> list[dict]:
    """
    Вычисляет формульные параметры продукта.

    Новые (с formula_config.func) — через асинхронный движок.
    Старые — через search_formula (fallback на CodeParametr).

    Возвращает обновлённый список параметров.
    """
    stmt = (
        select(ParameterSchema)
        .where(
            ParameterSchema.type.in_(["Formula", "Drawing"]),
            ParameterSchema.product_id == product_id,
        )
        .order_by(ParameterSchema.sort)
    )
    result = await db.execute(stmt)
    formula_params = result.scalars().all()

    new_specs: list[dict] = []
    legacy: list[Any] = []

    for param in formula_params:
        # Параметр типа «Файл» (Drawing) или «Формула» с заданной функцией —
        # считаем новым асинхронным движком (функция может возвращать URL файла).
        if _is_new_formula(param):
            new_specs.append({
                "id": param.id,
                "name": param.name,
                "formula_config": param.formula_config,
                "param": param,
            })
        elif param.type == "Formula":
            legacy.append(param)

    # Новые формулы — асинхронный движок.
    if new_specs:
        await _apply_new_formulas(db, response_params, selected_values, new_specs, product_id)

    # Старые формулы — fallback на CodeParametr.
    if legacy:
        from app.TableSearch.utils.formula_search import search_formula

        response_params = await search_formula(
            db,
            response_params,
            table_name_params=table_name_params,
            select_formula_params=selected_values,
            product_id=product_id,
        )

    # Входные формульные параметры (без функции расчёта) выводим в форме,
    # чтобы пользователь мог их заполнить (с применением валидатора).
    response_params = await _add_input_params(
        db, response_params, selected_values, product_id
    )

    # Параметры-чертежи (type='Drawing'): возвращают файл/картинку
    # в зависимости от выбранного значения другого параметра.
    response_params = await resolve_drawings(
        db, response_params, selected_values, product_id
    )

    return response_params


async def resolve_drawings(
    db: AsyncSession,
    response_params: list[dict],
    selected_values: dict[str, Any],
    product_id: int,
) -> list[dict]:
    """Добавляет параметры-чертежи в ответ, разрешив файл по выбранному значению.

    Конфигурация параметра-чертежа хранится в formula_config:
      {"type": "drawing", "drawing_of": "Маркировка", "use_first_chars": 5}
    Ищется запись в таблице product_drawing по product_id и имени
    (значение зависимого параметра, при необходимости укороченное до N символов).
    """
    stmt = (
        select(ParameterSchema)
        .where(
            ParameterSchema.type == "Drawing",
            ParameterSchema.product_id == product_id,
        )
        .order_by(ParameterSchema.sort)
    )
    result = await db.execute(stmt)
    drawing_params = result.scalars().all()
    if not drawing_params:
        return response_params

    name_to_entry = {item["name"]: item for item in response_params}
    drawings: list[dict] = []

    for param in drawing_params:
        cfg = param.formula_config or {}
        dep_name = cfg.get("drawing_of")
        if not dep_name:
            continue

        # Значение зависимого параметра (из текущего ответа или из выборки).
        dep_value = None
        dep_entry = name_to_entry.get(dep_name)
        if dep_entry and dep_entry.get("response_value"):
            dep_value = str(dep_entry["response_value"])
        elif selected_values.get(dep_name):
            dep_value = str(selected_values[dep_name])

        if not dep_value:
            continue

        use_first = cfg.get("use_first_chars")
        search_name = dep_value[:int(use_first)] if use_first else dep_value

        row = await db.execute(text(
            "SELECT file_url FROM product_drawing "
            "WHERE product_id = :pid AND name = :name LIMIT 1"
        ), {"pid": product_id, "name": search_name})
        url = row.scalar_one_or_none()
        if not url:
            continue

        drawings.append({
            "id": param.id,
            "name": param.name,
            "description": param.description,
            "table_name": None,
            "all_values": None,
            "response_value": url,
            "visibility": param.visibility,
            "editable": False,
            "required_type": "drawing",
            "sort": param.sort,
        })

    if not drawings:
        return response_params

    return response_params + drawings
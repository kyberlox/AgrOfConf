import re

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import time
from collections import defaultdict

from app.TablePakage.model.database import get_db
from app.TablePakage.model.product_files import ProductFiles
from app.TableSearch.utils.dm_search import ensure_dm_exists, get_full_search_from_dm
from ..utils.formula_search import search_formula
from app.formulas.integration import (
    apply_new_and_legacy_formulas,
    _is_mixture_on,
    _composition_param_names,
    _MIXTURE_OVERRIDE_MATCHERS,
    _match_pressure_entry,
    _match_valve_entry,
)

router = APIRouter(prefix="/module_search", tags=["Module_search"])


def natural_sort_key(value):
    value = str(value).strip().lower()

    if value in {"нет", "nan", "none", ""}:
        return (1, value)

    parts = re.split(r"(\d+(?:[.,]\d+)?)", value)

    key = []

    for part in parts:
        if not part:
            continue

        normalized_part = part.replace(",", ".")

        if re.fullmatch(r"\d+(?:\.\d+)?", normalized_part):
            key.append((0, float(normalized_part)))
        else:
            key.append((1, part))

    return (0, key)


async def get_formula_driven_param_names(
    db: AsyncSession,
    product_id: int,
) -> dict[tuple[str, str], str]:
    """Параметры, значения которых устанавливает алгоритм.

    Возвращает словарь (table_name|"", name) -> "pressure"|"valve". Это параметры
    таблицы давления (материал, T макс, давление настройки max, PN) и таблицы
    клапана (Тип ПК, диаметр седла и т.п.), а также формульный параметр
    «Предварительное номинальное давление». Их заполняет алгоритм
    (nominal_pressure / valve_selection), поэтому они исключаются из табличного
    подбора и им не подставляются табличные значения — у расчётных значений
    приоритет.

    Видимость этих параметров НЕ принудительная: она управляется свойством
    «Видим для пользователя» параметра (настраивается в админ-панели).

    Ключ включает table_name, чтобы не задеть одноимённые параметры других
    таблиц (например «Материал» из таблицы сред). Параметры исключаются из
    подбора только если у продукта заведён соответствующий формульный драйвер
    (иначе таблица остаётся обычным табличным подбором).
    """
    func_result = await db.execute(text(
        """
        SELECT formula_config ->> 'func' AS func
        FROM parameter_schemas
        WHERE product_id = :product_id AND type = 'Formula'
        """
    ), {"product_id": product_id})
    funcs = {row["func"] for row in func_result.mappings().all() if row["func"]}
    has_pressure_driver = "nominal_pressure" in funcs
    has_valve_driver = "valve_selection" in funcs

    if not has_pressure_driver and not has_valve_driver:
        return {}

    result = await db.execute(text(
        """
        SELECT name, table_name
        FROM parameter_schemas
        WHERE product_id = :product_id
          AND type = 'Table'
          AND table_name IS NOT NULL
        """
    ), {"product_id": product_id})

    by_table: dict[str, list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        name = (row["name"] or "").strip()
        tbl = (row["table_name"] or "").strip()
        if name and tbl:
            by_table[tbl].append({"name": name})

    driven: dict[tuple[str, str], str] = {}

    for tbl, params in by_table.items():
        low_names = {str(p["name"] or "").lower() for p in params}

        # Таблица давления: материал + (T макс / давление max / PN).
        has_material = any(
            "материал" in n or n == "material" for n in low_names
        )
        has_pressure = any(
            "t макс" in n or "максимальная температура" in n
            or "давление настройки max" in n
            or n.endswith("pn") or "pn (мпа)" in n
            for n in low_names
        )
        if has_pressure_driver and has_material and has_pressure:
            for p in params:
                low = str(p["name"] or "").lower()
                if _match_pressure_entry(low) is not None:
                    driven[(tbl, p["name"])] = "pressure"
            continue

        # Таблица клапана: «Тип ПК» + (диаметр седла / PN входное).
        has_type = any("тип пк" in n for n in low_names)
        has_seat = any("диаметр седла" in n for n in low_names)
        has_pn_in = any("pn входн" in n for n in low_names)
        if has_valve_driver and has_type and (has_seat or has_pn_in):
            for p in params:
                low = str(p["name"] or "").lower()
                if _match_valve_entry(low) is not None:
                    driven[(tbl, p["name"])] = "valve"

    # Формульный параметр «Предварительное номинальное давление» (функция
    # nominal_pressure) — результат подбора таблицы давления; значения
    # синхронизирует _fill_pressure_entries.
    if has_pressure_driver:
        formula_result = await db.execute(text(
            """
            SELECT name
            FROM parameter_schemas
            WHERE product_id = :product_id AND type = 'Formula'
            """
        ), {"product_id": product_id})
        for row in formula_result.mappings().all():
            name = (row["name"] or "").strip()
            if not name:
                continue
            low = name.lower()
            if "предварительное номинальное давление" in low or low == "pn":
                driven[("", name)] = "pressure"

    return driven


async def get_table_params_from_sql(
        db: AsyncSession,
        table_name: str,
        table_params: list[dict],
        selected_params: dict[str, str | int | list],
        formula_driven: dict[tuple[str, str], str] | None = None,
):
    """
    Делает подбор внутри одной конкретной таблицы Excel.
    table_params — параметры только этой таблицы.
    selected_params — выбранные пользователем параметры.
    formula_driven — параметры, значения которых устанавливает алгоритм
    (таблица давления/клапана): их нельзя использовать как критерии подбора,
    у расчётных значений приоритет.
    """

    where_clauses = []
    sql_params = {}

    for item in table_params:
        param_name = item["name"]

        if formula_driven and (table_name, param_name) in formula_driven:
            continue

        col = item["transliterated_name"]

        if param_name not in selected_params:
            continue

        value = selected_params[param_name]

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

            if not value:
                continue

        if isinstance(value, list):
            normalized_values = []

            for item_value in value:
                if item_value is None:
                    continue

                normalized_value = str(item_value).strip()

                if normalized_value:
                    normalized_values.append(normalized_value)

            # Если после очистки список пустой, параметр не выбран
            if not normalized_values:
                continue

            placeholders = []

            for idx, normalized_value in enumerate(normalized_values):
                param_key = f"{col}_{idx}"
                placeholders.append(f":{param_key}")
                sql_params[param_key] = normalized_value

            where_clauses.append(
                f'"{col}" IN ({", ".join(placeholders)})'
            )
        else:
            where_clauses.append(f'"{col}" = :{col}')
            sql_params[col] = str(value).strip()

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    select_parts = []
    column_to_param = {}

    for item in table_params:
        param_name = item["name"]
        col = item["transliterated_name"]

        select_parts.append(
            f'array_agg(DISTINCT "{col}") FILTER (WHERE "{col}" IS NOT NULL) AS "{col}"'
        )
        column_to_param[col] = param_name

    if not select_parts:
        return None, {}

    query = f"""
        SELECT
            {", ".join(select_parts)},
            COUNT(*) AS matched_rows
        FROM "{table_name}"
        {where_sql}
    """

    try:
        result = await db.execute(text(query), sql_params)
        row = result.mappings().first()
        return row, column_to_param

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка подбора по таблице {table_name}: {e}"
        )


async def find_search_errors_multi_table(
        db: AsyncSession,
        tables_map: dict[str, list[dict]],
        selected_params: dict[str, str | int | list],
        priority=None,
        formula_driven: dict[tuple[str, str], str] | None = None,
):
    """
    Проверяет ошибки подбора отдельно по каждой таблице.
    В отличие от основного цикла подбора, который применяет все параметры таблицы разом,
    эта функция ищет конкретный параметр, из-за которого комбинация стала невалидной,
    путём инкрементального добавления параметров в порядке сортировки.
    """

    errors = []

    for table_name, table_params in tables_map.items():
        table_param_names = {item["name"] for item in table_params}

        selected_for_table = {
            key: value
            for key, value in selected_params.items()
            if key in table_param_names
        }

        if not selected_for_table:
            continue

        # Сначала проверяем, что комбинация ВСЕХ выбранных параметров таблицы валидна
        row_all, _ = await get_table_params_from_sql(
            db=db,
            table_name=table_name,
            table_params=table_params,
            selected_params=selected_for_table,
            formula_driven=formula_driven,
        )

        if not row_all or row_all["matched_rows"] == 0:
            # Комбинация всех параметров невалидна — ищем конкретный проблемный параметр
            ordered_table_params = get_ordered_table_params(
                table_params,
                priority
            )

            incremental_selected = {}

            for param in ordered_table_params:
                param_name = param["name"]

                if param_name not in selected_for_table:
                    continue

                if formula_driven and (table_name, param_name) in formula_driven:
                    continue

                value = selected_for_table[param_name]

                if value is None:
                    continue

                if isinstance(value, str):
                    value = value.strip()

                    if not value:
                        continue

                if isinstance(value, list):
                    value = [
                        str(item).strip()
                        for item in value
                        if item is not None and str(item).strip()
                    ]

                    if not value:
                        continue

                incremental_selected[param_name] = value

                row, _ = await get_table_params_from_sql(
                    db=db,
                    table_name=table_name,
                    table_params=table_params,
                    selected_params=incremental_selected,
                    formula_driven=formula_driven,
                )

                if not row or row["matched_rows"] == 0:
                    errors.append({
                        "param_name": param_name,
                        "table_name": table_name,
                        "error": (
                            f"Параметр {param_name} выбран неверно. "
                            f"Вы выбрали значение: {value}."
                        )
                    })
                    break

    return errors


async def get_available_values_for_error_param(
        db: AsyncSession,
        table_name: str,
        table_params: list[dict],
        error_param_name: str,
        selected_params: dict[str, str | int | list],
        priority=None,
        formula_driven: dict[tuple[str, str], str] | None = None,
):
    """
    Возвращает допустимые значения для ошибочного параметра.
    """

    error_param = next(
        (
            item
            for item in table_params
            if item["name"] == error_param_name
        ),
        None
    )

    if error_param is None:
        return []

    ordered_params = get_ordered_table_params(
        table_params,
        priority
    )

    params_before_error = []

    for param in ordered_params:
        if param["name"] == error_param_name:
            break

        if formula_driven and (table_name, param["name"]) in formula_driven:
            continue

        params_before_error.append(param["name"])

    selected_before_error = {
        key: value
        for key, value in selected_params.items()
        if key in params_before_error
    }

    row, _ = await get_table_params_from_sql(
        db=db,
        table_name=table_name,
        table_params=table_params,
        selected_params=selected_before_error,
        formula_driven=formula_driven,
    )

    if not row:
        return []

    error_col = error_param["transliterated_name"]

    values = row[error_col]

    if not values:
        return []

    return sorted(
        (str(value) for value in values),
        key=natural_sort_key
    )


async def get_available_values_for_param(
        db,
        table_name,
        table_params,
        target_param_name,
        selected_params,
        formula_driven: dict[tuple[str, str], str] | None = None,
):
    selected_without_current = {
        key: value
        for key, value in selected_params.items()
        if key != target_param_name
    }

    row, table_column_to_param = await get_table_params_from_sql(
        db=db,
        table_name=table_name,
        table_params=table_params,
        selected_params=selected_without_current,
        formula_driven=formula_driven,
    )

    target_column = None

    for col, param_name in table_column_to_param.items():
        if param_name == target_param_name:
            target_column = col
            break

    if target_column is None or not row:
        return None  # []

    values = row[target_column] or None  # []
    if not values:
        return None

    return sorted(
        {str(value) for value in values},
        key=natural_sort_key
    )


def get_ordered_table_params(
        table_params: list[dict],
        priority: str | None = None
):
    ordered = sorted(
        table_params,
        key=lambda item: (
            item.get("sort")
            if item.get("sort") is not None
            else float(item["id"])
        )
    )

    if priority:
        priority_param = next(
            (
                item
                for item in ordered
                if item["name"] == priority
            ),
            None
        )

        if priority_param:
            ordered.remove(priority_param)
            ordered.insert(0, priority_param)

    return ordered


@router.post(
    "/process_table_data",
    description="Модуль табличного подбора",
)
async def process_table_data(
        product_id: int,
        selected_params: dict[str, str | int | float | list] | None = Body(None),
        db: AsyncSession = Depends(get_db),
):
    start_time = time.perf_counter()
    selected_params = dict(selected_params or {})

    priority = selected_params.pop("priority", None)

    product_name_result = await db.execute(
        text("""
            SELECT name
            FROM products
            WHERE id = :product_id
        """),
        {"product_id": product_id}
    )

    product_name = product_name_result.scalar_one_or_none()

    if product_name is None:
        raise HTTPException(status_code=404, detail="Продукция не найдена")

    schema_result = await db.execute(
        text("""
            SELECT
                id,
                name,
                transliterated_name,
                description,
                type,
                measuring_unit,
                table_name,
                visibility,
                editable,
                required_type,
                special,
                sort
            FROM parameter_schemas
            WHERE product_id = :product_id
              AND type = 'Table'
              AND table_name IS NOT NULL
            ORDER BY
                COALESCE(sort, id),
                id
        """),
        {"product_id": product_id}
    )

    full_info = schema_result.mappings().all()

    if not full_info:
        raise HTTPException(status_code=404, detail="Параметры не найдены")

    tables_map = defaultdict(list)

    for item in full_info:
        tables_map[item["table_name"]].append(dict(item))

    # Параметры, значения которых заполняет алгоритм (таблица давления и таблица
    # клапана). Их не используем как критерий табличного подбора и подставляем
    # им табличные значения, чтобы расчётные значения имели приоритет. Видимость
    # при этом не трогаем — её задаёт свойство «Видим для пользователя».
    formula_driven = await get_formula_driven_param_names(db, product_id)

    await ensure_dm_exists(db, product_id)

    full_value_parameters, full_matched_rows = await get_full_search_from_dm(
        db=db,
        product_id=product_id,
    )
    all_column_to_param = {param['transliterated_name']: param['name'] for param in full_info}
    # Если пользователь ничего не выбрал — просто возвращаем все доступные значения
    if not selected_params:
        response_params = []

        for item in full_info:
            name = item["name"]

            all_values = full_value_parameters.get(name)

            # Если datamart не отдал значения для колонки (например, для «Тип среды»),
            # получаем их напрямую из таблицы, иначе параметр невозможно выбрать.
            if not all_values:
                try:
                    avail = await get_available_values_for_param(
                        db=db,
                        table_name=item["table_name"],
                        table_params=tables_map[item["table_name"]],
                        target_param_name=name,
                        selected_params={},
                    )
                    if avail:
                        all_values = avail
                except Exception:  # noqa: BLE001
                    all_values = all_values or None

            response_value = None

            if isinstance(all_values, list) and len(all_values) == 1:
                response_value = all_values[0]

            driven_by_formula = (item["table_name"], name) in formula_driven

            response_params.append({
                "id": item["id"],
                "name": name,
                "description": item["description"],
                "table_name": item["table_name"],
                "all_values": all_values,
                "response_value": None if driven_by_formula else response_value,
                "visibility": item["visibility"],
                "editable": item["editable"],
                "required_type": item["required_type"],
                "special": bool(item["special"]),
                "sort": item["sort"],
            })
        response_params = await apply_new_and_legacy_formulas(
            db,
            response_params,
            {},
            list(tables_map.keys()),
            product_id,
        )

        # response_params = sorted(
        #     response_params,
        #     key=lambda param: param.get("sort") or param["id"]
        # )

        stmt_product_files = await db.execute(select(ProductFiles).where(ProductFiles.product_id == product_id))
        product_files = stmt_product_files.scalars().all()
        # product_files = [dict(row) for row in rows]
        # print(type(product_files), 'че получимли')
        response_params = sorted(
            response_params,
            key=lambda param: (
                param["sort"]
                if param.get("sort") is not None
                else param["id"]
            )
        )

        return {
            "product_id": product_id,
            "product_name": product_name,
            "files": product_files,
            "parameters": response_params,
            "matched_rows": full_matched_rows,
            "request_time": time.perf_counter() - start_time,
        }

    # Если параметры выбраны — делаем подбор отдельно по каждой таблице
    allowed_params = {item["name"] for item in full_info}

    # priority может указывать на формульный входной параметр (например «Диаметр»),
    # которого нет среди табличных параметров. Такой priority на порядок внутри
    # таблицы не влияет, поэтому игнорируем его, а не падаем с ошибкой.
    if priority is not None and priority not in allowed_params:
        priority = None

    # Когда включена смесь и задан состав, характеристики среды (вязкость,
    # плотность, теплоёмкости и т.п.) пересчитываются формулой и становятся
    # нередактируемыми (apply_mixture_overrides). Их значений в таблице нет,
    # поэтому использовать их как критерий табличного подбора и валидации
    # нельзя: сервер помечал бы присланное фронтом расчётное значение
    # ошибочным, сбрасывал его, фронт повторно запрашивал подбор — запросы
    # зацикливались. Исключаем такие параметры из табличного поиска.
    mixture_override_names = set()
    if _is_mixture_on(selected_params):
        comp_names = await _composition_param_names(db, product_id)
        if comp_names and any(
            name in selected_params
            and selected_params[name] is not None
            and str(selected_params[name]).strip()
            for name in comp_names
        ):
            for item in full_info:
                low_name = str(item["name"] or "").lower()
                if any(
                    kw in low_name
                    for _key, keywords in _MIXTURE_OVERRIDE_MATCHERS
                    for kw in keywords
                ):
                    mixture_override_names.add(item["name"])

    table_selected_params = {
        key: value
        for key, value in selected_params.items()
        if key not in mixture_override_names
    }

    # unknown_params = [
    #     param_name
    #     for param_name in selected_params
    #     if param_name not in allowed_params
    # ]

    # if unknown_params:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Неизвестные параметры: {unknown_params}"
    #     )

    total_matched_rows = 0

    for table_name, table_params in tables_map.items():
        table_param_names = {item["name"] for item in table_params}

        selected_for_table = {
            key: value
            for key, value in table_selected_params.items()
            if key in table_param_names
        }

        # Если в этой таблице нет выбранных пользователем параметров,
        # значит она не участвует в фильтрации.
        if not selected_for_table:
            continue

        row, table_column_to_param = await get_table_params_from_sql(
            db=db,
            table_name=table_name,
            table_params=table_params,
            selected_params=selected_for_table,
            formula_driven=formula_driven,
        )

        if not row:
            continue

        matched_rows = row["matched_rows"] or 0
        total_matched_rows += matched_rows

    errors = await find_search_errors_multi_table(
        db=db,
        tables_map=tables_map,
        selected_params=table_selected_params,
        priority=priority,
        formula_driven=formula_driven,
    )

    error_by_key = {
        (err["table_name"], err["param_name"]): err
        for err in errors
    }

    # Определяем позицию первой ошибки выбора пользователя В РАМКАХ КАЖДОЙ ТАБЛИЦЫ
    param_position_by_table = {}
    first_error_position_by_table = {}

    for table_name, table_params in tables_map.items():

        # Получаем порядок параметров:
        # priority будет первым, остальные идут по обычному sort
        ordered_table_params = get_ordered_table_params(
            table_params=table_params,
            priority=priority
        )

        # Сохраняем фактическую позицию каждого параметра
        for position, param in enumerate(ordered_table_params):
            param_position_by_table[(table_name, param["name"])] = position

        # Ищем позиции ошибочных параметров
        error_positions = []

        for param in ordered_table_params:
            key = (table_name, param["name"])

            if key in error_by_key:
                error_positions.append(
                    param_position_by_table[key]
                )

        if error_positions:
            first_error_position_by_table[table_name] = min(error_positions)

    error_filtered_values = {}

    for err in errors:
        table_name = err["table_name"]
        param_name = err["param_name"]

        table_params = tables_map.get(table_name)

        if not table_params:
            continue

        available_values = await get_available_values_for_error_param(
            db=db,
            table_name=table_name,
            table_params=table_params,
            error_param_name=param_name,
            selected_params=table_selected_params,
            priority=priority,
            formula_driven=formula_driven,
        )

        if available_values is not None:
            error_filtered_values[(table_name, param_name)] = available_values

    response_params = []

    for item in full_info:
        name = item["name"]
        table_name = item["table_name"]

        current_position = param_position_by_table.get(
            (table_name, name)
        )

        selected_value = selected_params.get(name)

        is_selected = selected_value is not None

        if isinstance(selected_value, str):
            is_selected = bool(selected_value.strip())

        elif isinstance(selected_value, list):
            is_selected = bool([
                value
                for value in selected_value
                if value is not None and str(value).strip()
            ])

        # Ошибка учитывается только в рамках своей таблицы
        first_error_in_table = first_error_position_by_table.get(table_name)

        is_after_error = (
                first_error_in_table is not None
                and current_position is not None
                and current_position > first_error_in_table
        )

        all_values = full_value_parameters.get(name) or []

        filtered_value = await get_available_values_for_param(
            db=db,
            table_name=table_name,
            table_params=tables_map[table_name],
            target_param_name=name,
            selected_params=table_selected_params,
            formula_driven=formula_driven,
        )

        # Если datamart не отдал значения (например, для «Тип среды») —
        # используем варианты, полученные из таблицы, иначе селект останется пустым.
        if not all_values and filtered_value:
            all_values = filtered_value

        error_item = error_by_key.get((table_name, name))

        # Для ошибочного параметра показываем допустимые варианты,
        # чтобы пользователь мог исправить ошибку
        if error_item:
            filtered_value = error_filtered_values.get((table_name, name))

            if filtered_value is None:
                filtered_value = all_values or None  # []

        # После первой ошибки в ТОЙ ЖЕ ТАБЛИЦЕ незаполненные параметры пока недоступны
        elif is_after_error:
            filtered_value = None

        # Обычный fallback применяется только до ошибки
        elif filtered_value is None:
            filtered_value = all_values or None  # []

        response_value = None

        driven_by_formula = (table_name, name) in formula_driven

        # Если параметр ошибочный — именно его сбрасываем
        if error_item:
            response_value = None

        # Параметры, заполняемые алгоритмом (таблица давления/клапана), никогда
        # не подставляем из таблицы и не приоритизируем запрос пользователя —
        # у значений алгоритма приоритет.
        elif driven_by_formula:
            response_value = None

        # Если параметр был выбран пользователем и не ошибочный —
        # оставляем выбранное значение, чтобы фронт не сбрасывал весь подбор
        # (явный выбор пользователя в приоритете).
        elif is_selected:
            response_value = selected_value

        # Если после фильтрации осталось одно значение — можно подставить его
        # (для параметров, которые пользователь явно не выбирал).
        elif isinstance(filtered_value, list) and len(filtered_value) == 1:
            response_value = filtered_value[0]

        elif isinstance(filtered_value, str):
            response_value = filtered_value

        elif isinstance(filtered_value, int):
            response_value = str(filtered_value)

        param_info = {
            "id": item["id"],
            "name": name,
            "description": item["description"],
            "table_name": table_name,
            "all_values": all_values,
            "response_value": response_value,
            "visibility": item["visibility"],
            "editable": item["editable"],
            "required_type": item["required_type"],
            "special": bool(item["special"]),
            "filtered_values": filtered_value,
            "sort": item["sort"],
        }

        if error_item:
            param_info["error"] = error_item["error"]

        response_params.append(param_info)
    time_before_fromula = time.perf_counter()

    # Объединяем выбранные значения: исходный запрос + авто-подставленные табличные.
    selected_values = dict(selected_params)
    for param_item in response_params:
        rv = param_item.get("response_value")
        if rv is not None and param_item["name"] not in selected_values:
            selected_values[param_item["name"]] = rv

    # Новые формулы — асинхронный движок; старые — fallback на CodeParametr.
    response_params = await apply_new_and_legacy_formulas(
        db,
        response_params,
        selected_values,
        list(tables_map.keys()),
        product_id,
    )

    # Получаем файлы продукта
    stmt_product_files = await db.execute(select(ProductFiles).where(ProductFiles.product_id == product_id))
    product_files = stmt_product_files.scalars().all()
    # product_files = [dict(row) for row in rows]
    # print(type(product_files), 'че получимли')
    response_params = sorted(
        response_params,
        key=lambda param: (
            param["sort"]
            if param.get("sort") is not None
            else param["id"]
        )
    )
    time_after_formula = time.perf_counter() - time_before_fromula
    print(
        f'Время формульного подбора {time_after_formula}, Время табличного подбора: {time_before_fromula - start_time}')
    # total_res = [param for param in response_params if ]
    return {
        "product_id": product_id,
        "product_name": product_name,
        "files": product_files,
        "parameters": response_params,
        "matched_rows": total_matched_rows,
        "request_time": time.perf_counter() - start_time,
    }

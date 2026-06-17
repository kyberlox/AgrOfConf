from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
from collections import defaultdict

from app.TablePakage.model.database import get_db
from app.TableSearch.utils.dm_search import ensure_dm_exists, get_full_search_from_dm
from ..utils.formula_search import search_formula

router = APIRouter(prefix="/module_search", tags=["Module_search"])


async def get_table_params_from_sql(
        db: AsyncSession,
        table_name: str,
        table_params: list[dict],
        selected_params: dict[str, str | int | list],
):
    """
    Делает подбор внутри одной конкретной таблицы Excel.
    table_params — параметры только этой таблицы.
    selected_params — выбранные пользователем параметры.
    """

    where_clauses = []
    sql_params = {}

    for item in table_params:
        param_name = item["name"]
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
):
    """
    Проверяет ошибки подбора отдельно по каждой таблице.
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

        incremental_selected = {}

        for param_name, value in selected_for_table.items():
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
):
    """
    Возвращает допустимые значения для ошибочного параметра,
    убирая сам ошибочный параметр из фильтрации.
    """

    selected_without_error = {
        key: value
        for key, value in selected_params.items()
        if key != error_param_name
    }

    row, column_to_param = await get_table_params_from_sql(
        db=db,
        table_name=table_name,
        table_params=table_params,
        selected_params=selected_without_error,
    )

    if not row:
        return None

    error_col = None

    for item in table_params:
        if item["name"] == error_param_name:
            error_col = item["transliterated_name"]
            break

    if not error_col:
        return None

    values = row[error_col]

    if not values:
        return None

    values = sorted(str(value) for value in values)

    if len(values) == 1:
        return values[0]

    return values


@router.post(
    "/process_table_data",
    description="Модуль табличного подбора",
)
async def process_table_data(
        product_id: int,
        selected_params: dict[str, str | int | list] | None = Body(None),
        db: AsyncSession = Depends(get_db),
):
    start_time = time.perf_counter()
    selected_params = selected_params or {}

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
                required_type,
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
            response_value = None

            if isinstance(all_values, list) and len(all_values) == 1:
                response_value = all_values[0]

            response_params.append({
                "id": item["id"],
                "name": name,
                "description": item["description"],
                "table_name": item["table_name"],
                "all_values": all_values,
                "response_value": response_value,
                "visibility": item["visibility"],
                "required_type": item["required_type"],
                "sort": item["sort"],
            })
        formula_params = await search_formula(db, response_params, table_name_params=list(tables_map.keys()),
                                              column_to_param=all_column_to_param)

        response_params = sorted(
            formula_params,
            key=lambda param: param.get("sort") or param["id"]
        )

        return {
            "product_id": product_id,
            "product_name": product_name,
            "parameters": response_params,
            "matched_rows": full_matched_rows,
            "request_time": time.perf_counter() - start_time,
        }

    # Если параметры выбраны — делаем подбор отдельно по каждой таблице
    allowed_params = {item["name"] for item in full_info}

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

    merged_filtered_values = defaultdict(set)
    total_matched_rows = 0

    for table_name, table_params in tables_map.items():
        table_param_names = {item["name"] for item in table_params}

        selected_for_table = {
            key: value
            for key, value in selected_params.items()
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
        )

        if not row:
            continue

        matched_rows = row["matched_rows"] or 0
        total_matched_rows += matched_rows

        for col, param_name in table_column_to_param.items():
            values = row[col]

            if not values:
                continue

            for value in values:
                merged_filtered_values[param_name].add(str(value))

    parameters_for_response = {}

    for param_name, values in merged_filtered_values.items():
        sorted_values = sorted(values)

        if len(sorted_values) == 1:
            parameters_for_response[param_name] = sorted_values[0]
        else:
            parameters_for_response[param_name] = sorted_values

    errors = await find_search_errors_multi_table(
        db=db,
        tables_map=tables_map,
        selected_params=selected_params,
    )

    error_by_key = {
        (err["table_name"], err["param_name"]): err
        for err in errors
    }

    # Определяем позицию первой ошибки выбора пользователя

    error_positions = []

    for item in full_info:
        key = (item["table_name"], item["name"])

        if key in error_by_key:
            error_positions.append(
                item.get("sort")
                if item.get("sort") is not None
                else float(item["id"])
            )

    first_error_position = min(error_positions) if error_positions else None

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
            selected_params=selected_params,
        )

        if available_values is not None:
            error_filtered_values[(table_name, param_name)] = available_values

    response_params = []

    for item in full_info:
        name = item["name"]
        table_name = item["table_name"]

        current_position = (
            item.get("sort")
            if item.get("sort") is not None
            else float(item["id"])
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

        is_after_error = (
                first_error_position is not None
                and current_position > first_error_position
        )

        all_values = full_value_parameters.get(name) or []
        filtered_value = parameters_for_response.get(name)

        error_item = error_by_key.get((table_name, name))

        # Для ошибочного параметра показываем допустимые варианты,
        # чтобы пользователь мог исправить ошибку
        if error_item:
            filtered_value = error_filtered_values.get((table_name, name))

            if filtered_value is None:
                filtered_value = all_values

        # После первой ошибки незаполненные параметры пока недоступны
        elif is_after_error and not is_selected:
            filtered_value = []

        # Обычный fallback применяется только до ошибки
        elif filtered_value is None:
            filtered_value = all_values

        response_value = None

        # Если параметр ошибочный — именно его сбрасываем
        if error_item:
            response_value = None

        # Если параметр был выбран пользователем и он не ошибочный —
        # оставляем выбранное значение, чтобы фронт не сбрасывал весь подбор
        elif is_selected:
            response_value = selected_value

        # Если после фильтрации осталось одно значение — можно подставить его
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
            "required_type": item["required_type"],
            "filtered_values": filtered_value,
            "sort": item["sort"],
        }

        if error_item:
            param_info["error"] = error_item["error"]

        response_params.append(param_info)

    formula_params = await search_formula(
        db,
        response_params,
        table_name_params=list(tables_map.keys()),
        select_formula_params=selected_params,
        column_to_param=all_column_to_param
    )

    response_params = sorted(
        formula_params,
        key=lambda param: param.get("sort") or param["id"]
    )

    return {
        "product_id": product_id,
        "product_name": product_name,
        "parameters": response_params,
        "matched_rows": total_matched_rows,
        "request_time": time.perf_counter() - start_time,
    }

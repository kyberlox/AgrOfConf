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
from .algorithms import (
    _filtered_media_names, _normalize_mixture_mode, _parse_composition_json,
    _validate_composition, MIXTURE_COMPOSITION_PARAM, MIXTURE_COMPOSITION_TYPE,
    MIXTURE_SWITCH, MIXTURE_TYPE_PARAM,
)


async def _composition_param_names(
    db: AsyncSession,
    product_id: int,
) -> set[str]:
    """Имена параметров-состава смеси продукта.

    Основной способ — тип 'FormulaMix'. Если такой параметр ещё не заведён,
    ищем по имени «Состав смеси» (обратная совместимость со старой настройкой).
    """
    result = await db.execute(text(
        "SELECT name FROM parameter_schemas "
        "WHERE product_id = :pid AND type = 'FormulaMix'"
    ), {"pid": product_id})
    names = {row[0] for row in result.all() if row and row[0]}
    if names:
        return names

    result = await db.execute(text(
        "SELECT name FROM parameter_schemas "
        "WHERE product_id = :pid AND name = 'Состав смеси'"
    ), {"pid": product_id})
    return {row[0] for row in result.all() if row and row[0]}


def _mixture_switch_key(selected_values: dict[str, Any]) -> str | None:
    """Фактическое имя чекбокса «Смесь» по ключевым словам в выбранных параметрах."""
    for name in selected_values or {}:
        low = str(name).lower()
        if "смесь" in low and "тип" not in low and "состав" not in low:
            return name
    return MIXTURE_SWITCH


def _mixture_type_key(selected_values: dict[str, Any]) -> str | None:
    """Фактическое имя select «Тип смеси» по ключевым словам."""
    for name in selected_values or {}:
        low = str(name).lower()
        if "тип смеси" in low or ("тип" in low and "смесь" in low):
            return name
    return MIXTURE_TYPE_PARAM


def _is_mixture_on(selected_values: dict[str, Any]) -> bool:
    """Включён ли чекбокс «Смесь» (True/False или строка)."""
    value = selected_values.get(_mixture_switch_key(selected_values))
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("", "нет", "false", "0")


# Параметры, которые скрываются, когда смесь собрана (включён чекбокс
# «Смесь» и выбран тип): агрегатное состояние и выбор рабочей среды
# определяются самим составом смеси.
_MIXTURE_HIDE_ON_KEYWORDS = (
    "агрегатное состояние",
    "название рабочей среды",
    "наименование рабочей среды",
    "рабочая среда",
)


async def _finalize_mixture_visibility(
    db: AsyncSession,
    response_params: list[dict],
    selected_values: dict[str, Any],
    product_id: int,
) -> list[dict]:
    """Управляет видимостью параметров смеси по состоянию чекбокса «Смесь».

    - Включена смесь и выбран тип → скрываем «Агрегатное состояние» и
      «Название рабочей среды»: их определяет состав смеси, а характеристики
      пересчитываются формулой (apply_mixture_overrides).
    - Выключена смесь → скрываем «Тип смеси» и параметр-состав
      (type='FormulaMix' или по имени «Состав смеси»).
    """
    if _is_mixture_on(selected_values):
        mode = _normalize_mixture_mode(selected_values.get(_mixture_type_key(selected_values)))
        if mode is None:
            return response_params  # тип ещё не выбран — смесь не собрана
        return [
            p for p in response_params
            if not any(kw in str(p.get("name") or "").lower() for kw in _MIXTURE_HIDE_ON_KEYWORDS)
        ]

    comp_names = await _composition_param_names(db, product_id)
    type_key = _mixture_type_key(selected_values)
    hidden = {type_key} | comp_names
    return [p for p in response_params if p.get("name") not in hidden]


# Табличные характеристики, которые при собранной смеси пересчитываются
# формулой: русское ключевое слово в названии параметра -> ключ результата
# расчёта смеси (_mixture_properties). Такой параметр становится нередактируемым.
_MIXTURE_OVERRIDE_MATCHERS = [
    ("agregatnoe_sostojanie", ("агрегатное состояние",)),
    # «Молекулярная масса» — молекулярная (в двухфазном потоке — жидкая фаза).
    ("molekuljarnaja_massa", ("молекул",)),
    # «Молярная масса» — молярная (в двухфазном потоке — паровая фаза).
    ("molar_mass", ("молярн",)),
    ("plotnost_zhidkosti", ("плотност",)),
    ("vjazkost_pa_s", ("вязкост",)),
    ("pokazatel_adiabaty", ("адиабат",)),
    ("isobaric_capacity", ("изобарн",)),
    ("isochoric_capacity", ("изохорн",)),
    ("factor", ("сжимаемост",)),
    ("latent_heat", ("удельная теплота парообразования", "теплота парообразования", "парообразован", "скрытая теплота")),
    ("material", ("материал", "material")),
]


def _to_float_safe(value, default=None):
    """Безопасное приведение значения к float (пустые строки, «нет», запятая)."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text_value = str(value).strip().replace(",", ".")
    if not text_value or text_value.lower() in ("нет", "none", "n/a", "-"):
        return default
    try:
        return float(text_value)
    except (TypeError, ValueError):
        return default


def _match_pressure_entry(lower_name: str) -> str | None:
    """Определяет, является ли параметр частью таблицы давления, и какой это ключ.

    По подстроке в имени (lowercase) возвращает ключ результата:
      «material», «t_max», «pressure_max» или «pn»; иначе None.
    """
    groups = [
        ("material", ("материал", "material")),
        ("t_max", ("t максимальное", "т максимальное", "t макс", "максимальная температура")),
        ("pressure_max", ("давление настройки max", "давление настройки максимальное", "давление max", "давление максимальное")),
        ("pn", ("pn",)),
    ]
    for key, kws in groups:
        if any(kw in lower_name for kw in kws):
            return key
    return None


# Формульный параметр «Предварительное номинальное давление»: в дополнение к
# заполнению табличных параметров давления синхронизируем его значение с PN.
_PRESSURE_FORMULA_KEYWORDS = (
    "предварительное номинальное давление",
    "номинальное давление",
    "pn",
)


def _fill_pressure_entries(response_params: list[dict], sel: dict | None) -> None:
    """Записывает результат подбора таблицы давления в табличные параметры.

    `sel` — dict из select_pressure_table (material, t_max, pressure_max, pn,
    _table). Заполняет только параметры таблицы давления (по table_name),
    помечает их нередактируемыми и скрывает. Значение формульного параметра
    «Предварительное номинальное давление» синхронизируется с подобранным PN.
    """
    if not sel:
        return

    pres_table = sel.get("_table")
    for entry in response_params:
        # Не трогаем одноимённые параметры других таблиц (например «Материал»
        # из таблицы сред).
        if pres_table and entry.get("table_name") != pres_table:
            continue
        key = _match_pressure_entry(str(entry.get("name") or "").lower())
        if key is None:
            continue
        if key == "material":
            entry["response_value"] = sel.get("material", entry.get("response_value"))
        else:
            entry["response_value"] = sel.get(key, entry.get("response_value"))
        entry["editable"] = False
        entry["visibility"] = False

    pn = sel.get("pn")
    if pn is None:
        return
    for entry in response_params:
        # Параметры таблицы давления уже заполнены выше.
        if pres_table and entry.get("table_name") == pres_table:
            continue
        # Значение формульного параметра «Предварительное номинальное давление»
        # держим актуальным (в смеси оно пересчитывается после переопределения
        # материала).
        low_name = str(entry.get("name") or "").lower()
        if any(kw in low_name for kw in _PRESSURE_FORMULA_KEYWORDS):
            entry["response_value"] = pn


async def apply_mixture_overrides(
    db: AsyncSession,
    response_params: list[dict],
    selected_values: dict[str, Any],
    product_id: int,
) -> list[dict]:
    """Пересчитывает табличные характеристики по формуле собранной смеси.

    Если у продукта есть параметр-состав (type='FormulaMix'), чекбокс «Смесь»
    включён, тип смеси выбран и состав валиден — значения табличных параметров
    (плотность, вязкость, молярная масса, агрегатное состояние, теплоёмкости,
    фактор сжимаемости, материал и т.п.) заменяются рассчитанными значениями
    смеси, а сами параметры помечаются как нередактируемые.

    Это заменяет отдельный параметр «Характеристики смеси»: характеристики
    определяются формулой, а не табличным поиском.
    """
    comp_names = await _composition_param_names(db, product_id)
    if not comp_names:
        return response_params
    if not _is_mixture_on(selected_values):
        return response_params

    from .algorithms import MissingParamError, _mixture_properties, select_pressure_table

    ctx = FormulaContext(dict(selected_values), {}, db=db, product_id=product_id)

    def _sel_value(*keywords: str):
        """Значение выбранного параметра по ключевым словам (через keyword-поиск)."""
        for name in selected_values or {}:
            low = str(name).lower().replace("ё", "е")
            if any(kw in low for kw in keywords):
                v = selected_values[name]
                if v is not None and str(v).strip() != "":
                    return v
        return None

    for comp_name in comp_names:
        try:
            props = await _mixture_properties(ctx, {"composition_param": comp_name})
        except (MissingParamError, ValueError) as exc:
            # Состав ещё не собран / невалиден — оставляем табличные значения.
            print(f"[mixture override] пропущен пересчёт смеси '{comp_name}': {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"[mixture override] ошибка пересчёта смеси '{comp_name}': {exc}")
            continue
        if not props:
            continue

        for entry in response_params:
            name = str(entry.get("name") or "").lower()
            for key, keywords in _MIXTURE_OVERRIDE_MATCHERS:
                if any(kw in name for kw in keywords):
                    entry["response_value"] = props.get(key, entry.get("response_value"))
                    entry["editable"] = False
                    break

        # Подбор строки таблицы давления (Т макс / Давл.max / PN) по материалу
        # смеси. Значения записывает _fill_pressure_entries (такие же, как в
        # формуле nominal_pressure), которая также синхронизирует формульный
        # параметр «Предварительное номинальное давление» с подобранным PN.
        material = props.get("material")
        if material:
            try:
                temperature_raw = _sel_value("температура рабочей среды", "температура")
                pressure_raw = _sel_value("давление настройки")
                temperature = _to_float_safe(temperature_raw)
                pressure = _to_float_safe(pressure_raw)
                sel = await select_pressure_table(
                    ctx, material, temperature=temperature, pressure_setting=pressure
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[mixture override] ошибка подбора таблицы давления '{comp_name}': {exc}")
                sel = None

            if sel:
                _fill_pressure_entries(response_params, sel)
        break
    return response_params


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
    results, computed = await compute_formulas(
        db, new_specs, selected_values, product_id=product_id
    )

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
                "special": bool(param.special),
                "sort": param.sort,
            }
            response_params.append(entry)

        # Статический список значений для «выбора из списка» (formula_config["values"]).
        cfg = spec.get("formula_config") or {}
        values = cfg.get("values")
        if isinstance(values, list):
            entry["all_values"] = values

        if "error" in res:
            entry["error"] = res["error"]
            entry["is_validation"] = res.get("is_validation", False)
        if "response_value" in res:
            entry["response_value"] = res["response_value"]

    # Формула «Предварительное номинальное давление» (nominal_pressure) кладёт
    # подбор таблицы давления в ctx.computed — записываем его в табличные
    # параметры (material / T max / Давл. max / PN) и скрываем их.
    _fill_pressure_entries(response_params, computed.get("_pressure_table"))


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
            ParameterSchema.type.in_(["Formula", MIXTURE_COMPOSITION_TYPE]),
            ParameterSchema.product_id == product_id,
        )
        .order_by(ParameterSchema.sort)
    )
    result = await db.execute(stmt)
    formula_params = result.scalars().all()
    if not formula_params:
        return response_params

    existing_names = {item["name"] for item in response_params}
    ctx = FormulaContext(dict(selected_values), {}, db=db, product_id=product_id)

    for param in formula_params:
        cfg = param.formula_config or {}
        if cfg.get("func"):
            continue  # такие считает асинхронный движок
        if param.name in existing_names:
            continue  # уже добавлен (например, legacy-обработчиком)

        rv = selected_values.get(param.name)
        error = None

        # === Логика смеси ===
        switch_value = selected_values.get(_mixture_switch_key(selected_values))

        # Параметр-состав смеси: тип 'FormulaMix' или (обратная совместимость)
        # имя «Состав смеси». В конфигураторе для него попап-редактор.
        # Показываем только если «Смесь» отмечена
        # И «Тип смеси» выбран (газовая/жидкостная/двухфазный поток).
        is_composition_param = (
            param.type == MIXTURE_COMPOSITION_TYPE
            or param.name == MIXTURE_COMPOSITION_PARAM
        )
        if is_composition_param:
            if not switch_value:
                continue  # чекбокс выключен — скрываем параметр
            mode = _normalize_mixture_mode(selected_values.get(_mixture_type_key(selected_values)))
            if mode is None:
                continue  # тип смеси ещё не выбран — скрываем состав
            values = await _filtered_media_names(ctx, mode)
            if not values:
                values = None
            pairs = _parse_composition_json(rv) if rv is not None else []
            comp_error = _validate_composition(pairs)
            if comp_error:
                error = comp_error

        # «Тип смеси»: показываем только если чекбокс «Смесь» отмечен.
        elif param.name == _mixture_type_key(selected_values):
            if not switch_value:
                continue  # чекбокс выключен — скрываем параметр
            values = cfg.get("values")
            if not isinstance(values, list):
                values = None

        else:
            values = cfg.get("values")
            if not isinstance(values, list):
                values = None

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
            "type": param.type,
            "description": param.description,
            "table_name": param.table_name,
            "all_values": values,
            "response_value": rv,
            "visibility": param.visibility,
            "editable": param.editable,
            "required_type": param.required_type,
            "special": bool(param.special),
            "sort": param.sort,
        }
        if error:
            entry["error"] = error
            entry["is_validation"] = True
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
            continue

        # Входные формульные параметры (например доли смеси) не имеют функции
        # и выводятся через _add_input_params — их НЕ трогает legacy-CodeParametr.
        if param.type == "Formula":
            fov = param.field_of_view
            if isinstance(fov, str):
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

    # Пересчитываем табличные характеристики по формуле смеси, если состав
    # собран (вместо отдельного параметра «Характеристики смеси»).
    response_params = await apply_mixture_overrides(
        db, response_params, selected_values, product_id
    )

    # Скрываем «Тип смеси»/параметр-состав, если чекбокс «Смесь» выключен.
    response_params = await _finalize_mixture_visibility(
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
            "special": bool(param.special),
            "sort": param.sort,
        })

    if not drawings:
        return response_params

    return response_params + drawings
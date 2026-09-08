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

import json
import re
import math

from .engine import FormulaContext, MissingParamError

# Имена параметров смеси (захардкожены по решению пользователя).
# «Смесь» — чекбокс (True/False): включает/выключает всю логику смеси.
# «Тип смеси» — select со значениями «газовая»/«жидкостная»/«двухфазный поток».
# «Состав смеси» — select-input (JSON-массив пар {среда: мольная доля}).
MIXTURE_SWITCH = "Смесь"
MIXTURE_TYPE_PARAM = "Тип смеси"
MIXTURE_COMPOSITION_PARAM = "Состав смеси"
# Отдельный тип формульного параметра «Состав смеси»: вместо завязки на имя
# параметр помечается в админке отдельным типом. В конфигураторе для него
# открывается попап-редактор состава.
MIXTURE_COMPOSITION_TYPE = "FormulaMix"

# Допустимые типы смеси (из select-параметра «Тип смеси»).
MIXTURE_MODES_OFF = {"нет", "Нет", "НЕТ", "нет.", ""}
MIXTURE_MODES = {
    "газовая": "Газ",
    "жидкостная": "Жидкость",
    "двухфазный поток": "Двухфазный поток",
}


def _normalize_mixture_mode(value) -> str | None:
    """
    Приводит значение параметра «Смесь» к каноническому виду.

    Возвращает строку-тип («газовая», «жидкостная», «двухфазный поток»)
    или None, если смесь выключена (значение отсутствует или «нет»).
    """
    if value is None:
        return None
    key = str(value).strip().lower()
    if key in MIXTURE_MODES_OFF or key not in MIXTURE_MODES:
        return None
    return key


async def _resolve_mixture_mode(ctx: FormulaContext, config: dict | None) -> str | None:
    """
    Определяет тип смеси по двум входным параметрам.

    - «Смесь» — чекбокс (True/False). Если выключен/не выбран — смесь не
      рассчитывается, возвращается None.
    - «Тип смеси» — select со значениями «газовая»/«жидкостная»/«двухфазный
      поток». Если чекбокс включён, а тип не выбран — поднимается
      MissingParamError (пользователь должен его заполнить).

    Имена параметров ищутся по ключевым словам (переименования и суффиксы
    размерности не страшны), а в formula_config можно переопределить ключами
    `mixture_param` и `type_param`.
    """
    config = config or {}
    switch_name = await _actual_param_name(
        ctx, config, "mixture_param",
        "смесь", "признак смеси",
        default=MIXTURE_SWITCH,
        exclude=("тип смеси", "состав смеси", "название смеси"),
    )
    switch_name = switch_name or MIXTURE_SWITCH
    switch = ctx.get_opt(switch_name)
    if not switch:
        # Чекбокс не отмечен / «нет» — смесь выключена.
        return None

    type_name = await _actual_param_name(
        ctx, config, "type_param",
        "тип смеси", "тип",
        default=MIXTURE_TYPE_PARAM,
        exclude=("состав", "перечень"),
    )
    type_name = type_name or MIXTURE_TYPE_PARAM
    mode = _normalize_mixture_mode(ctx.get_opt(type_name))
    if mode is None:
        raise MissingParamError(type_name)
    return mode


async def _auto_composition_param(ctx: FormulaContext) -> str | None:
    """
    Ищет параметр-состав смеси по типу 'FormulaMix' (единственный на продукт).

    Если таких несколько — берём первый по sort. Возвращает имя параметра или
    None, если параметр-состав не заведён в админке.
    """
    if not ctx.db or not ctx.product_id:
        return None
    from sqlalchemy import text

    row = await ctx.db.execute(text(
        "SELECT name FROM parameter_schemas "
        "WHERE product_id = :pid AND type = 'FormulaMix' "
        "ORDER BY COALESCE(sort, id) LIMIT 1"
    ), {"pid": ctx.product_id})
    return row.scalar_one_or_none()


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
    """Возвращает URL чертежа по маркировке."""
    construction = ctx.get("Маркировка")
    if not ctx.db or not ctx.product_id:
        return None

    target = construction[0:5]
    
    from sqlalchemy import text

    row = await ctx.db.execute(text(
        "SELECT file_url FROM parameter_files "
        "WHERE product_id = :pid AND name ILIKE :pattern LIMIT 1"
    ), {"pid": ctx.product_id, "pattern": f"%{target}%"})
    url = row.scalar_one_or_none()
    return url or None

async def has_product_device(ctx: FormulaContext):
    """Проверяет, есть ли у продукта рычаг."""
    has_device  = ctx.get('Устройство принудительного открытия')
    if has_device and has_device == 'требуется':
        return "Рычаг"
    return None

async def has_product_seal(ctx: FormulaContext):
    """Проверяет, есть ли у продукта сильфон."""
    has_seal  = ctx.get('Тип уплотнения')
    if has_seal and has_seal == 'сильфонное':
        return "Сильфон"
    return None



# === Расчёт характеристик смесей ===

def _gather_composition(ctx: FormulaContext, config: dict | None) -> list[tuple[str, float]]:
    """
    Собирает состав смеси.

    Поддерживаются два способа:

    1. Параметры-слоты «Среда N» / «Доля N» (отдельные параметры в форме).
    2. Один select-input параметр (config["composition_param"], по умолчанию
       «Состав смеси»), значением которого является JSON-массив пар
       [{название среды: доля}, ...] — так отдаёт компонент SelectInput.

    Возвращает список пар (название среды, мольная доля от 0 до 1).
    """
    config = config or {}
    composition_param = config.get("composition_param") or MIXTURE_COMPOSITION_PARAM

    # Способ 1: один select-input параметр с JSON-составом.
    if composition_param:
        raw = ctx.get_opt(composition_param)
        if raw is not None:
            pairs = _parse_composition_json(raw)
            if pairs:
                return pairs

    slots = config.get("slots")

    pairs: list[tuple[str, float]] = []

    if slots:
        iterator = iter(slots)
        for name, share_name in zip(iterator, iterator):
            substance = ctx.get_opt(name)
            share = ctx.get_opt(share_name)

            # Незаполненный слот пропускаем (гибкое число компонентов).
            if substance is None and share is None:
                continue
            if substance is None or share is None:
                raise MissingParamError(
                    name if substance is None else share_name
                )

            pairs.append((str(substance).strip(), float(share)))

        return pairs

    # Авто-детект слотов по шаблону имени.
    selected = ctx.selected or {}
    substances: dict[int, str] = {}
    shares: dict[int, float] = {}

    for raw_name, raw_value in selected.items():
        if raw_name is None or not str(raw_name).strip():
            continue
        name = str(raw_name).strip()

        match_substance = re.match(r"^\s*Сред[аы]\s*(\d+)\s*$", name)
        if match_substance and raw_value is not None and str(raw_value).strip():
            substances[int(match_substance.group(1))] = str(raw_value).strip()

        match_share = re.match(r"^\s*Доля\s*(\d+)\s*$", name)
        if match_share and raw_value is not None and str(raw_value).strip():
            shares[int(match_share.group(1))] = float(raw_value)

    for index in sorted(set(substances) | set(shares)):
        substance = substances.get(index)
        share = shares.get(index)

        if substance is None and share is None:
            continue
        if substance is None:
            raise MissingParamError(f"Среда {index}")
        if share is None:
            raise MissingParamError(f"Доля {index}")

        pairs.append((substance, share))

    if not pairs:
        # Fallback: если есть любые вовлечённые среды со стандартными именами
        # (например, «Среда N»/«Мольная доля N») — собираем и их.
        pairs = _gather_composition_generic(ctx)

    return pairs


def _parse_composition_json(raw) -> list[tuple[str, float]]:
    """
    Разбирает значение select-input параметра в пары (среда, доля).

    Принимает либо готовый список (приходит из запроса как JSON-массив), либо
    строку с JSON. Источник: компонент SelectInput отдаёт массив объектов вида
    [{ "Название среды": 50 }, { "Другая среда": 50 }].
    """
    value = raw
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return []

    if not isinstance(value, list):
        return []

    pairs: list[tuple[str, float]] = []
    for item in value:
        if not isinstance(item, dict) or not item:
            continue
        # Формат [{среда: доля}] — один ключ на элемент.
        if len(item) == 1:
            name, share = next(iter(item.items()))
        else:
            # Альтернативный формат: {"name": ..., "value": .../доля}.
            name = item.get("name") or item.get("Название рабочей среды")
            share = item.get("value") or item.get("Мольная доля")
        if name is None or share is None:
            continue
        try:
            pairs.append((str(name).strip(), float(share)))
        except (TypeError, ValueError):
            continue
    return pairs


def _gather_composition_generic(ctx: FormulaContext) -> list[tuple[str, float]]:
    """Собирает состав из выбранных значений даже с нестандартными именами слотов.

    Например, select-параметры могли называться «Среда 1» + «Мольная доля состава
    рабочей среды, % 1». Здесь ищем пары «название среды» + «процент» по общим
    шаблонам имён.
    """
    selected = ctx.selected or {}

    def _is_share_name(name: str) -> bool:
        return bool(re.match(r"^\s*(Доля|Мольная доля|Процент|%).*", name, re.I))

    share_items: dict[int, float] = {}
    substance_items: dict[int, str] = {}

    for raw_name, raw_value in selected.items():
        if raw_name is None or not str(raw_name).strip():
            continue
        name = str(raw_name).strip()
        if raw_value is None or not str(raw_value).strip():
            continue

        tail = re.search(r"(\d+)\s*$", name)
        index = int(tail.group(1)) if tail else None

        if _is_share_name(name):
            try:
                share_items[index] = float(raw_value)
            except (TypeError, ValueError):
                continue
        else:
            substance_items[index] = str(raw_value).strip()

    pairs: list[tuple[str, float]] = []
    for index in sorted(set(substance_items) | set(share_items)):
        substance = substance_items.get(index)
        share = share_items.get(index)
        if substance is None and share is None:
            continue
        if substance is None or share is None:
            continue
        pairs.append((substance, share))

    return pairs


def _validate_composition(composition: list[tuple[str, float]]) -> str | None:
    """Проверяет состав: минимум две среды и сумма долей = 100%. Возвращает текст ошибки."""
    if len(composition) < 2:
        return "Смесь не может состоять менее чем из двух сред!"

    total = sum(share for _, share in composition)
    if abs(total - 100.0) > 0.0001:
        return f"Сумма мольных долей сред смеси должна составлять 100%, а не {total}%"

    return None


async def _resolve_media_columns(ctx: FormulaContext, table_name: str | None = None) -> dict[str, str]:
    """
    Определяет колонки физической таблицы сред и их транслитерации.

    Возвращает map: русское название характеристики -> транслитерированное имя колонки.
    Если table_name указан — берутся колонки только этой таблицы (у продукта может
    быть несколько таблиц, а характеристики сред живут в одной из них).
    """
    from sqlalchemy import text

    if table_name is None:
        table_name = await _resolve_media_table(ctx)

    if not table_name:
        return {}

    rows = await ctx.db.execute(text(
        """
        SELECT name, transliterated_name
        FROM parameter_schemas
        WHERE product_id = :product_id AND type = 'Table' AND table_name = :tbl
        """
    ), {"product_id": ctx.product_id, "tbl": table_name})

    columns: dict[str, str] = {}

    for row in rows.mappings().all():
        name = (row["name"] or "").strip()
        translit = (row["transliterated_name"] or "").strip()
        if not name or not translit:
            continue

        columns[name] = translit

    return columns


async def _existing_table_columns(ctx: FormulaContext, table_name: str) -> set[str]:
    """Фактические колонки физической таблицы (чтобы не выбирать несуществующие)."""
    from sqlalchemy import text

    rows = await ctx.db.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = :tbl"
    ), {"tbl": table_name})
    return {row[0] for row in rows.all() if row and row[0]}


async def _resolve_media_table(ctx: FormulaContext) -> str | None:
    """Возвращает имя физической таблицы продукта (из Table-параметров) или None."""
    from sqlalchemy import text

    result = await ctx.db.execute(text(
        """
        SELECT table_name
        FROM parameter_schemas
        WHERE product_id = :product_id AND type = 'Table' AND table_name IS NOT NULL
        LIMIT 1
        """
    ), {"product_id": ctx.product_id})
    return result.scalar_one_or_none()


async def _filtered_media_names(ctx: FormulaContext, mode: str) -> list[str]:
    """
    Возвращает имена сред из таблицы продукта, отфильтрованные по агрегатному
    состоянию согласно режиму «Смесь»:

        «газовая»            — только «Газ»;
        «жидкостная»         — только «Жидкость»;
        «двухфазный поток»   — и газ, и жидкость.

    Используется, чтобы состав смеси предлагал пользователю только те среды,
    которые допустимы выбранным типом смеси.
    """
    from sqlalchemy import text

    table_name = await _resolve_media_table(ctx)
    if not table_name:
        return []

    columns = await _resolve_media_columns(ctx, table_name)
    env_name_col = None
    aggregate_col = None

    for name, translit in columns.items():
        lowered = name.lower()
        if env_name_col is None and ("рабочей среды" in lowered or "рабочая среда" in lowered or "среда" in lowered):
            env_name_col = translit
        if aggregate_col is None and ("агрегатное состояние" in lowered or "состояние" in lowered):
            aggregate_col = translit

    if not env_name_col or not aggregate_col:
        return []

    existing = await _existing_table_columns(ctx, table_name)
    if env_name_col not in existing or aggregate_col not in existing:
        return []

    allowed: set[str]
    if mode == "газовая":
        allowed = {"Газ"}
    elif mode == "жидкостная":
        allowed = {"Жидкость"}
    else:
        allowed = {"Газ", "Жидкость"}

    sql = f'SELECT DISTINCT "{env_name_col}", "{aggregate_col}" FROM "{table_name}"'
    rows = await ctx.db.execute(text(sql))
    names: list[str] = []
    for mapping in rows.mappings().all():
        name = mapping.get(env_name_col)
        state = mapping.get(aggregate_col)
        if not name or not state:
            continue
        if str(state).strip() in allowed:
            names.append(str(name).strip())

    return names


async def _schema_param_names(ctx: FormulaContext) -> list[str]:
    """Все имена параметров продукта из БД (схема), для поиска по ключевым словам."""
    cached = ctx.computed.get("_schema_param_names")
    if cached is not None:
        return cached

    names: list[str] = []
    if ctx.db and ctx.product_id:
        from sqlalchemy import text

        rows = await ctx.db.execute(text(
            "SELECT name FROM parameter_schemas "
            "WHERE product_id = :pid AND name IS NOT NULL"
        ), {"pid": ctx.product_id})
        names = [str(r[0]) for r in rows.all() if r and r[0]]

    ctx.computed["_schema_param_names"] = names
    return names


async def _actual_param_name(
    ctx: FormulaContext,
    config: dict | None,
    config_key: str | None,
    *keywords: str,
    default: str | None = None,
    exclude: tuple[str, ...] = (),
) -> str | None:
    """Определяет ФАКТИЧЕСКОЕ имя входного/табличного параметра по ключевым словам.

    Переименование параметров в админке и добавление размерности к названию
    (например «Температура рабочей среды, °C») не должно требовать правки
    алгоритма. Приоритет поиска:

      1) явное имя из formula_config[config_key] — но только если параметр
         действительно присутствует среди выбранных/вычисленных значений;
      2) ключ в ctx.selected / ctx.computed, чьё имя содержит ключевое слово
         (без учёта регистра);
      3) имя параметра продукта в БД (parameter_schemas);
      4) default — запасное имя.

    Ключевые слова проверяются ПО ПОРЯДКУ: первое, давшее совпадение, и
    определяет имя (самое специфичное указывайте первым). `exclude` позволяет
    отсечь похожие по имени параметры (например «Тип смеси» при поиске чекбокса
    «Смесь»).
    """
    config = config or {}

    if config_key:
        explicit = config.get(config_key)
        if explicit and str(explicit).strip():
            candidate = str(explicit)
            if candidate in ctx.selected or candidate in ctx.computed:
                return candidate

    kws = [str(k).strip().lower() for k in keywords if k and str(k).strip()]
    if not kws:
        return default
    excluded = [str(e).strip().lower() for e in (exclude or ()) if e and str(e).strip()]

    def _best(matched: list[str]) -> str | None:
        for name in matched:
            low = name.lower()
            if any(e in low for e in excluded):
                continue
            return name
        return None

    candidates = [
        str(k) for k in list(ctx.selected or {}) + list(ctx.computed or {})
        if isinstance(k, str) and k.strip()
    ]

    for kw in kws:
        best = _best([n for n in candidates if kw in n.lower()])
        if best is not None:
            return best

    for kw in kws:
        best = _best([n for n in await _schema_param_names(ctx) if kw in n.lower()])
        if best is not None:
            return best

    return default


def _to_float(value, default=None):
    """Безопасное приведение значения колонки к float.

    В таблицах сред характеристики могут хранить текст «нет», пустые строки
    или десятичные с запятой — такие значения не должны ломать расчёт смеси.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text_value = str(value).strip().replace(",", ".")
    if not text_value or text_value.lower() in ("нет", "none", "n/a", "не применимо", "-"):
        return default
    try:
        return float(text_value)
    except (TypeError, ValueError):
        return default


async def _mixture_properties(ctx: FormulaContext, config: dict | None) -> dict:
    """
    Сервисная функция: вычисляет все характеристики смеси разом.

    Используется функциями-характеристиками (mixture_density и др.) и
    кэшируется в ctx.computed["_mixture_full"], чтобы не повторять SQL по
    каждому параметру.

    Ожидаемый конфиг:
        mixture_param      — имя чекбокса «Смесь» (по умолчанию «Смесь»).
        type_param         — имя select «Тип смеси» (по умолчанию «Тип смеси»).
        composition_param  — имя select-input параметра состава
                             (по умолчанию «Состав смеси»).
        slots              — альтернативный способ задания состава: список имён
                             слотов «среда/доля» (чередует пары).
    """
    cached = ctx.computed.get("_mixture_full")
    if cached is not None:
        return cached

    config = config or {}

    # Если параметр-состав не указан в конфиге — ищем по типу 'FormulaMix'.
    if not config.get("composition_param"):
        auto_name = await _auto_composition_param(ctx)
        if auto_name:
            config = {**config, "composition_param": auto_name}

    # Тип смеси определяется по чекбоксу «Смесь» (вкл/выкл) и select «Тип смеси».
    mode = await _resolve_mixture_mode(ctx, config)
    if mode is None:
        # Чекбокс выключен — смесь не рассчитываем: возвращаем None, чтобы
        # фронт не показывал характеристики (обычный подбор одной среды).
        return None

    if not ctx.db or not ctx.product_id:
        raise MissingParamError("Среда")

    from sqlalchemy import text

    composition = _gather_composition(ctx, config)

    if not composition:
        # Подсказываем пользователю, какой параметр заполнить первым.
        slots = (config or {}).get("slots")
        first_name = (
            config.get("composition_param")
            or (slots[0] if slots else MIXTURE_COMPOSITION_PARAM)
        )
        raise MissingParamError(first_name)

    error = _validate_composition(composition)
    if error:
        raise ValueError(error)

    # Таблица сред определяется первой, чтобы колонки-характеристики собирались
    # только из неё (у продукта может быть несколько таблиц).
    table_name = await _resolve_media_table(ctx)
    if not table_name:
        raise MissingParamError("Название рабочей среды")

    columns = await _resolve_media_columns(ctx, table_name)
    existing = await _existing_table_columns(ctx, table_name)

    # Находим основные характеристики по русским названиям параметров продукта.
    def find_column(*keywords: str) -> str | None:
        for name, translit in columns.items():
            lowered = name.lower()
            if any(keyword.lower() in lowered for keyword in keywords):
                return translit
        return None

    env_name_col = find_column("название рабочей среды", "рабочая среда", "среда")
    if not env_name_col or env_name_col not in existing:
        raise MissingParamError("Название рабочей среды")

    aggregate_col = find_column("агрегатное состояние", "состояние")
    molar_mass_col = find_column("молярная масса", "молекулярная масса")
    density_col = find_column("плотность")
    viscosity_col = find_column("вязкость")
    adiabatic_col = find_column("показатель адиабаты", "адиабат")
    isobaric_col = find_column("изобарная теплоёмкость", "изобарн", "cp")
    isochoric_col = find_column("изохорная теплоёмкость", "изохорн", "cv")
    factor_col = find_column("фактор сжимаемости", "сжимаемости")
    latent_heat_col = find_column("удельная теплота парообразования", "теплота парообразования", "парообразован")
    material_col = find_column("материал")

    select_columns = [env_name_col]
    env_keys = [env_name_col]

    def _add_char_column(col: str | None) -> None:
        if col and col in existing:
            select_columns.append(col)
            env_keys.append(col)

    _add_char_column(aggregate_col)
    _add_char_column(molar_mass_col)
    _add_char_column(density_col)
    _add_char_column(viscosity_col)
    _add_char_column(adiabatic_col)
    _add_char_column(isobaric_col)
    _add_char_column(isochoric_col)
    _add_char_column(factor_col)
    _add_char_column(latent_heat_col)
    _add_char_column(material_col)

    envs_json: list[dict] = []
    env_types: set[str] = set()

    for env_name, percent in composition:
        share = percent / 100.0
        sql_columns = ", ".join(f'"{column}"' for column in select_columns)
        sql = f'SELECT {sql_columns} FROM "{table_name}" WHERE "{env_name_col}" = :env_name LIMIT 1'

        env_row = await ctx.db.execute(
            text(sql),
            {"env_name": env_name},
        )
        mapping = env_row.mappings().first()

        if not mapping:
            # Среда не найдена в таблице — пропускаем её.
            continue

        env_json = {
            "name": env_name,
            "r": share,
            "environment": str(mapping.get(aggregate_col) or "") if aggregate_col else "",
            "molekuljarnaja_massa": _to_float(mapping.get(molar_mass_col)),
            "plotnost_zhidkosti": _to_float(mapping.get(density_col)),
            "vjazkost_pa_s": _to_float(mapping.get(viscosity_col)),
            "isobaric_capacity": _to_float(mapping.get(isobaric_col)),
            "isochoric_capacity": _to_float(mapping.get(isochoric_col)),
            "pokazatel_adiabaty": _to_float(mapping.get(adiabatic_col)),
            "compressibility_factor": _to_float(mapping.get(factor_col), 1),
            "latent_heat": _to_float(mapping.get(latent_heat_col)),
            "material": mapping.get(material_col),
        }
        env_types.add(env_json["environment"])
        envs_json.append(env_json)

    if not envs_json:
        raise MissingParamError("Название рабочей среды")

    result = {
        "nazvanie_rabochej_sredy": "",
        "agregatnoe_sostojanie": "",
        "molekuljarnaja_massa": 0,
        "plotnost_zhidkosti": 0,
        "vjazkost_pa_s": 0,
        "isobaric_capacity": 0,
        "isochoric_capacity": 0,
        "pokazatel_adiabaty": 0,
        "factor": 1,
        "latent_heat": 0,
        "material": "",
        # Двухфазный поток (метод Ω, ISO 4126-10):
        "vapor_mass_fraction": 0,   # массовое паросодержание x0
        "plotnost_liquid": 0,       # плотность жидкой фазы, кг/м³
        "molar_mass_vapor": 0,      # молярная масса паровой фазы, г/моль
        "cp_liquid": 0,             # изобарная теплоёмкость жидкой фазы, Дж/(кг·К)
        "n_polytropic": 0,          # политропный показатель (для Ω)
    }

    homogeneous = len(env_types) == 1

    if homogeneous and "Жидкость" in env_types:
        result["agregatnoe_sostojanie"] = "Жидкость"

        ch_den = 0
        zn_den = 0
        pre_viscosity = 0
        mix_molar = 0
        mix_isobaric = 0
        mix_isochoric = 0
        latent_num = 0
        latent_den = 0

        for env in envs_json:
            r = env["r"]
            result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r * 100:.0f}% "
            mix_molar += float(env["molekuljarnaja_massa"] or 0) * r
            ch_den += float(env["plotnost_zhidkosti"] or 0) * r
            zn_den += r

            try:
                pre_viscosity += math.log10(float(env["vjazkost_pa_s"])) * r
            except (TypeError, ValueError):
                pass

            mix_isobaric += float(env["isobaric_capacity"] or 0) * r
            mix_isochoric += float(env["isochoric_capacity"] or 0) * r

            # Удельная теплота парообразования (Дж/кг): массовое усреднение.
            # Доли состава — объёмные, переводим в массовые через плотность.
            mass_share = float(env["plotnost_zhidkosti"] or 0) * r
            latent_num += float(env["latent_heat"] or 0) * mass_share
            latent_den += mass_share

        result["molekuljarnaja_massa"] = mix_molar
        result["plotnost_zhidkosti"] = ch_den / zn_den if zn_den else 0
        result["vjazkost_pa_s"] = 10 ** pre_viscosity
        result["isobaric_capacity"] = mix_isobaric
        result["isochoric_capacity"] = mix_isochoric
        result["latent_heat"] = latent_num / latent_den if latent_den else 0

        # Поля двухфазной ветки (однофазная жидкость): x0 = 0.
        result["vapor_mass_fraction"] = 0
        result["plotnost_liquid"] = result["plotnost_zhidkosti"]
        result["molar_mass_vapor"] = 0
        result["cp_liquid"] = mix_isobaric * 1000  # кДж/(кг·К) → Дж/(кг·К)
        result["n_polytropic"] = 0

    elif homogeneous and "Газ" in env_types:
        result["agregatnoe_sostojanie"] = "Газ"

        pre_M = 0
        viscosity_ch = 0
        viscosity_zn = 0
        adiabatic_index = 0
        density = 0
        isobaric = 0
        isochoric = 0
        factor = 0
        latent_num = 0

        for env in envs_json:
            r = env["r"]
            result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r * 100:.0f}% "

            M_i = float(env["molekuljarnaja_massa"] or 0)
            u_i = float(env["vjazkost_pa_s"] or 0)
            pre_M += M_i * r
            viscosity_ch += u_i * r * (M_i ** 0.5)
            viscosity_zn += r * (M_i ** 0.5)
            adiabatic_index += float(env["pokazatel_adiabaty"] or 0) * r
            density += M_i * r
            isobaric += float(env["isobaric_capacity"] or 0) * r
            isochoric += float(env["isochoric_capacity"] or 0) * r
            factor += float(env["compressibility_factor"] or 1) * r

            # Удельная теплота парообразования (Дж/кг): пересчитываем в мольный
            # вид (Дж/кмоль = Дж/кг * кг/кмоль), усредняем по мольным долям и
            # делим на молярную массу смеси -> снова Дж/кг.
            latent_num += float(env["latent_heat"] or 0) * r * M_i

        result["molekuljarnaja_massa"] = pre_M
        result["vjazkost_pa_s"] = viscosity_ch / viscosity_zn if viscosity_zn else 0
        result["pokazatel_adiabaty"] = adiabatic_index
        result["plotnost_zhidkosti"] = density / 22.4
        result["isobaric_capacity"] = isobaric
        result["isochoric_capacity"] = isochoric
        result["factor"] = factor
        result["latent_heat"] = latent_num / pre_M if pre_M else 0

        # Поля двухфазной ветки (однофазный газ): x0 = 1, паровой фазы нет.
        result["vapor_mass_fraction"] = 1
        result["plotnost_liquid"] = 0
        result["molar_mass_vapor"] = pre_M
        result["n_polytropic"] = adiabatic_index

    elif homogeneous:
        result["agregatnoe_sostojanie"] = next(iter(env_types))

        ch_den = 0
        zn_den = 0
        pre_viscosity = 0
        pre_M = 0
        latent = 0

        for env in envs_json:
            r = env["r"]
            result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r * 100:.0f}% "
            ch_den += float(env["plotnost_zhidkosti"] or 0) * r
            zn_den += r
            pre_viscosity += float(env["vjazkost_pa_s"] or 0) * r
            pre_M += float(env["molekuljarnaja_massa"] or 0) * r
            latent += float(env["latent_heat"] or 0) * r

        result["plotnost_zhidkosti"] = ch_den / zn_den if zn_den else 0
        result["vjazkost_pa_s"] = pre_viscosity
        result["molekuljarnaja_massa"] = pre_M
        result["latent_heat"] = latent

        # Поля двухфазной ветки: состояние однородное, не газ/жидкость → x0 = 0.
        result["vapor_mass_fraction"] = 0
        result["plotnost_liquid"] = result["plotnost_zhidkosti"]
        result["molar_mass_vapor"] = 0
        result["n_polytropic"] = 0

    else:
        result["agregatnoe_sostojanie"] = "Двухфазный поток"

        density_ch = 0
        density_zn = 0
        pre_u = 0
        latent = 0

        total_mass = 0
        gas_mass = 0
        gas_share = 0
        liq_mass = 0
        liq_mass_over_rho = 0
        liq_cp_num = 0
        adiabatic_num = 0

        for env in envs_json:
            r = env["r"]
            result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r * 100:.0f}% "

            M = float(env["molekuljarnaja_massa"] or 0)
            mass = M * r
            total_mass += mass
            adiabatic_num += float(env["pokazatel_adiabaty"] or 0) * r

            if env["environment"] == "Газ":
                gas_mass += mass
                gas_share += r
                density_ch += (M / 22.4) * r
                density_zn += r
            elif env["environment"] == "Жидкость":
                density_ch += float(env["plotnost_zhidkosti"] or 0) * r
                density_zn += r
                rho = float(env["plotnost_zhidkosti"] or 0)
                liq_mass += mass
                if rho > 0:
                    liq_mass_over_rho += mass / rho
                liq_cp_num += mass * float(env["isobaric_capacity"] or 0) * 1000

            pre_u += r * float(env["vjazkost_pa_s"] or 0) * float(env["molekuljarnaja_massa"] or 0)
            latent += float(env["latent_heat"] or 0) * r

        result["plotnost_zhidkosti"] = density_ch / density_zn if density_zn else 0
        result["vjazkost_pa_s"] = pre_u
        result["latent_heat"] = latent

        # Двухфазный поток (метод Ω): x0 по массовым долям компонентов.
        result["vapor_mass_fraction"] = gas_mass / total_mass if total_mass else 0
        result["plotnost_liquid"] = liq_mass / liq_mass_over_rho if liq_mass_over_rho else 0
        result["cp_liquid"] = liq_cp_num / liq_mass if liq_mass else 0
        result["molar_mass_vapor"] = gas_mass / gas_share if gas_share else 0
        result["n_polytropic"] = adiabatic_num

    # Материал: у среды с самой высокой долей (из компонентов), со спец-правилом H2S.
    material = []
    for env in envs_json:
        if env["name"] == "Сероводород" and env["r"] < 0.06:
            material.append("25Л")
        else:
            material.append(env.get("material") or "")

    if material:
        result["material"] = max(material, key=len)

    ctx.computed["_mixture_full"] = result
    return result


async def mixture_state(ctx: FormulaContext, config):
    """Агрегатное состояние смеси: «Газ», «Жидкость» или «Двухфазный поток»."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["agregatnoe_sostojanie"]


async def mixture_density(ctx: FormulaContext, config):
    """Плотность смеси, кг/м³ (для газа — при нормальных условиях)."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["plotnost_zhidkosti"]


async def mixture_molar_mass(ctx: FormulaContext, config):
    """Молярная масса смеси, г/моль."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["molekuljarnaja_massa"]


async def mixture_viscosity(ctx: FormulaContext, config):
    """Вязкость смеси (Па·с)."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["vjazkost_pa_s"]


async def mixture_adiabatic_index(ctx: FormulaContext, config):
    """Показатель адиабаты смеси."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["pokazatel_adiabaty"]


async def mixture_isobaric_capacity(ctx: FormulaContext, config):
    """Изобарная теплоёмкость смеси."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["isobaric_capacity"]


async def mixture_isochoric_capacity(ctx: FormulaContext, config):
    """Изохорная теплоёмкость смеси."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["isochoric_capacity"]


async def mixture_latent_heat(ctx: FormulaContext, config):
    """Удельная теплота парообразования смеси, Дж/кг."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["latent_heat"]


async def mixture_factor(ctx: FormulaContext, config):
    """Фактор сжимаемости смеси."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["factor"]


async def mixture_material(ctx: FormulaContext, config):
    """Материал, подобранный из компонентов смеси."""
    result = await _mixture_properties(ctx, config)
    return None if result is None else result["material"]


async def mixture_characteristics(ctx: FormulaContext, config):
    """Все характеристики смеси одним объектом.

    Возвращает dict с полями: агрегатное состояние, состав, молярная масса,
    плотность, вязкость, показатель адиабаты, теплоёмкости, фактор
    сжимаемости и материал. Ветка рассчитывается по агрегатному состоянию
    компонентов: газ / жидкость / двухфазный поток. Если чекбокс «Смесь»
    выключен — возвращается None, и параметр не показывается.

    Зависит от входных параметров (по умолчанию): чекбокс «Смесь»,
    select «Тип смеси», select-input «Состав смеси». Имена можно переопределить
    в formula_config ключами `mixture_param`, `type_param`, `composition_param`.
    """
    result = await _mixture_properties(ctx, config)
    if result is None:
        return None
    return {
        "Агрегатное состояние": result["agregatnoe_sostojanie"],
        "Состав": result["nazvanie_rabochej_sredy"].strip() or "—",
        "Молярная масса": result["molekuljarnaja_massa"],
        "Плотность": result["plotnost_zhidkosti"],
        "Вязкость": result["vjazkost_pa_s"],
        "Показатель адиабаты": result["pokazatel_adiabaty"],
        "Изобарная теплоёмкость": result["isobaric_capacity"],
        "Изохорная теплоёмкость": result["isochoric_capacity"],
        "Фактор сжимаемости": result["factor"],
        "Удельная теплота парообразования": result["latent_heat"],
        "Материал": result["material"],
    }


# ============================================================================
# Расчёт диаметра седла предохранительного клапана.
#
# Ветки по агрегатному состоянию среды:
#   * «Газ»        — ГОСТ 12.2.085-2017 приложение Д (Д.22)–(Д.26);
#   * «Жидкость»   — (Д.21);
#   * «Двухфазный поток» — метод Ω (ISO 4126-10), структура.
#
# Параметры расчёта кэшируются в ctx.computed["_seat_full"], чтобы все выходные
# параметры (давления, Kw, G, DN_s, площади, x0, Ω, ηc) считались однократно.
# ============================================================================

# Имена входных параметров расчёта седла (по умолчанию). Админ может переопределить
# их в formula_config каждого выходного параметра ключами force_open_param /
# pn_param / flow_param / count_param / membrane_param / backpressure_param /
# temperature_param.
_SEAT_FORCE_OPEN_PARAM = "Устройство принудительного открытия"
_SEAT_PN_PARAM = "Давление настройки"
_SEAT_FLOW_PARAM = "Максимальный аварийный расход жидкости и газа"
_SEAT_COUNT_PARAM = "Количество параллельно установленных и одновременно работающих клапанов (шт)"
_SEAT_MEMBRANE_PARAM = "Мембранно-предохранительное устройство"
_SEAT_BACKPRESSURE_PARAM = "Противодавление статическое"
_SEAT_TEMPERATURE_PARAM = "Температура рабочей среды, °C"


def _linear_interpolation(x1: float, y1: float, x2: float, y2: float, x: float) -> float:
    """Линейная интерполяция между точками (x1, y1) и (x2, y2) в точке x."""
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def _gas_kw(Ppo: float, Pn: float, Pp: float, Pno: float) -> float:
    """Коэффициент Kw (Д.22)–(Д.26) для газовой среды, повторяет legacy-расчёт."""
    ratio = Ppo / Pn
    rp = Pp / Pno
    # (Д.22)
    if ratio == 1.1:
        return 1 if rp <= 0.3 else 1.1027 + 0.4007 * rp - 2.4577 * rp ** 2
    # (Д.23)
    if ratio == 1.15:
        return 1 if rp <= 0.37 else 1.2857 - 0.7603 * rp
    # (Д.24)
    if ratio > 1.2 and rp >= 0.5:
        return 1
    # (Д.25): интерполяция между (Д.22) и (Д.23)
    if 1.1 < ratio <= 1.15:
        kw_1 = 1.1027 + 0.4007 * rp - 2.4577 * rp ** 2
        kw_2 = 1.2857 - 0.7603 * rp
        return _linear_interpolation(1.1, kw_1, 1.15, kw_2, ratio)
    # (Д.26): интерполяция между (Д.23) и (Д.24) — верх 1.21 (как в legacy)
    if 1.15 < ratio <= 1.2:
        kw_1 = 1.2857 - 0.7603 * rp
        return _linear_interpolation(1.15, kw_1, 1.21, 1, ratio)
    return 1


async def _medium_properties(ctx: FormulaContext, config: dict | None) -> dict:
    """Свойства рабочей среды для расчёта седла.

    Если смесь собрана (чекбокс «Смесь» включён) — возвращает характеристики
    смеси. Иначе — характеристики отдельной (не смесовой) среды из выбранных
    параметров: агрегатное состояние, молярная масса, плотность жидкости,
    вязкость, показатель адиабаты, теплота парообразования.

    Кэшируется в ctx.computed["_medium_full"].
    """
    cached = ctx.computed.get("_medium_full")
    if cached is not None:
        return cached

    config = config or {}

    mix = await _mixture_properties(ctx, config)
    if mix is not None:
        ctx.computed["_medium_full"] = mix
        return mix

    state_name = await _actual_param_name(
        ctx, config, "state_param",
        "агрегатное состояние", "состояние",
        default="Агрегатное состояние",
    )
    molar_name = await _actual_param_name(
        ctx, config, "molar_param",
        "молярная масса", "молекулярная масса",
        default="Молярная масса",
    )
    density_name = await _actual_param_name(
        ctx, config, "density_param",
        "плотность жидкости", "плотность",
        default="Плотность жидкости",
    )
    viscosity_name = await _actual_param_name(
        ctx, config, "viscosity_param",
        "вязкость",
        default="Вязкость (Па*с)",
    )
    adiabatic_name = await _actual_param_name(
        ctx, config, "adiabatic_param",
        "показатель адиабаты", "адиабат",
        default="Показатель адиабаты",
    )
    latent_name = await _actual_param_name(
        ctx, config, "latent_heat_param",
        "удельная теплота парообразования", "теплота парообразования", "парообразован",
        default="Удельная теплота парообразования",
    )
    material_name = await _actual_param_name(
        ctx, config, "material_param",
        "материал",
        default="Материал",
    )

    idx_config = {
        "state_param": state_name,
        "molar_param": molar_name,
        "density_param": density_name,
        "viscosity_param": viscosity_name,
        "adiabatic_param": adiabatic_name,
        "latent_heat_param": latent_name,
        "material_param": material_name,
    }

    result = {
        "agregatnoe_sostojanie": ctx.get_opt(state_name) or "",
        "molekuljarnaja_massa": _to_float(ctx.get_opt(molar_name)),
        "plotnost_zhidkosti": _to_float(ctx.get_opt(density_name)),
        "vjazkost_pa_s": _to_float(ctx.get_opt(viscosity_name)),
        "pokazatel_adiabaty": _to_float(ctx.get_opt(adiabatic_name)),
        "latent_heat": _to_float(ctx.get_opt(latent_name)),
        "material": ctx.get_opt(material_name) or "",
        "param_names": idx_config,
    }
    ctx.computed["_medium_full"] = result
    return result


def _omega_parameter(props: dict, P0: float, T0: float) -> float:
    """Параметр Ω (ISO 4126-10, метод Ω).

    props — свойства среды (vapor_mass_fraction, plotnost_liquid,
    molar_mass_vapor, cp_liquid, latent_heat); P0 — абсолютное давление в МПа;
    T0 — температура в К.

    Структура: Ω = x0·(νg0/νl0) + слагаемое равновесного вскипания.
    Точные коэффициенты калибруются по ISO 4126-10.
    """
    x0 = float(props.get("vapor_mass_fraction") or 0)
    rho_l = float(props.get("plotnost_liquid") or 0)
    M_v = float(props.get("molar_mass_vapor") or 0)
    cp_l = float(props.get("cp_liquid") or 0)
    h_lg = float(props.get("latent_heat") or 0)

    if rho_l <= 0 or M_v <= 0:
        raise ValueError("Для двухфазного расчёта нужны плотность жидкой фазы и молярная масса пара")

    R = 8.31446261815324
    P0_pa = P0 * 1e6
    # Плотность пара по идеальному газу, кг/м³ (M_v в г/моль).
    rho_g = P0_pa * M_v / (1000 * R * T0)
    nu_l0 = 1.0 / rho_l
    nu_g0 = 1.0 / rho_g

    # Изотермическая часть (без вскипания).
    omega = x0 * (nu_g0 / nu_l0)

    # Равновесное вскипание при дросселировании (структура; калибровка по ISO 4126-10).
    if h_lg > 0 and cp_l > 0:
        omega += (1 - x0) * cp_l * T0 * P0_pa * (nu_g0 - nu_l0) ** 2 / (nu_l0 * h_lg ** 2)

    return max(omega, 1e-9)


def _two_phase_critical_ratio(omega: float) -> float:
    """Критическое отношение давлений ηc = Pc/P0 (ISO 4126-10, структура)."""
    return 2 * omega / (2 * omega + 1)


def _two_phase_mass_flux(props: dict, P0: float, T0: float, B: float) -> float:
    """Массовая скорость двухфазного потока G, кг/(м²·с) (ISO 4126-10, структура).

    Критический режим (B <= ηc): Gc = C0·√(P0·ρl/ω).
    Докритический (B > ηc): с понижающим коэффициентом по DR=1−(1−B)/(1−ηc)).
    """
    omega = _omega_parameter(props, P0, T0)
    eta_c = _two_phase_critical_ratio(omega)
    rho_l = float(props.get("plotnost_liquid") or 0)
    C0 = 0.9  # коэффициент скорости (калибровка по ISO 4126-10)
    G_c = C0 * math.sqrt(P0 * 1e6 * rho_l / omega)
    if B <= eta_c:
        return G_c
    dr = (1 - B) / (1 - eta_c) if eta_c < 1 else 1
    return G_c * math.sqrt(max(1 - (1 - dr) ** 2, 0))


async def _seat_calc_full(ctx: FormulaContext, config: dict | None) -> dict:
    """Полный расчёт диаметра седла ПК; результат кэшируется в _seat_full."""
    cached = ctx.computed.get("_seat_full")
    if cached is not None:
        return cached

    config = config or {}
    P_atm = 0.101320
    R = 8.31446261815324

    # Гейт legacy-расчёта: седло считается, только когда выбран табличный
    # параметр «Устройство принудительного открытия» (значение «Да» или «Нет»).
    # Если он не выбран (продукт не подобран) — просим заполнить.
    force_open_name = await _actual_param_name(
        ctx, config, "force_open_param",
        "устройство принудительного открытия", "принудительного открытия",
        default=_SEAT_FORCE_OPEN_PARAM,
    )
    if force_open_name is None:
        force_open_name = _SEAT_FORCE_OPEN_PARAM
    force_open = ctx.get_opt(force_open_name)
    if force_open is None or force_open == "":
        raise MissingParamError(force_open_name)

    pn_name = await _actual_param_name(
        ctx, config, "pn_param",
        "давление настройки", "давление для настройки",
        default=_SEAT_PN_PARAM,
    )
    flow_name = await _actual_param_name(
        ctx, config, "flow_param",
        "максимальный аварийный расход", "аварийный расход", "расход жидкости и газа",
        default=_SEAT_FLOW_PARAM,
    )
    count_name = await _actual_param_name(
        ctx, config, "count_param",
        "количество параллельно установленных", "клапанов",
        default=_SEAT_COUNT_PARAM,
    )
    membrane_name = await _actual_param_name(
        ctx, config, "membrane_param",
        "мембранно-предохранительное", "мембран",
        default=_SEAT_MEMBRANE_PARAM,
    )
    backpressure_name = await _actual_param_name(
        ctx, config, "backpressure_param",
        "противодавление статическое", "противодавление",
        default=_SEAT_BACKPRESSURE_PARAM,
    )
    temperature_name = await _actual_param_name(
        ctx, config, "temperature_param",
        "температура рабочей среды", "рабочая среда",
        default=_SEAT_TEMPERATURE_PARAM,
    )

    Pn = ctx.num(pn_name)
    Gab = ctx.num(flow_name)
    N = ctx.num(count_name)
    pre_Kc = ctx.get(membrane_name)
    Pp = ctx.num(backpressure_name)
    T = ctx.num(temperature_name)

    Kc = 0.9 if pre_Kc == "Да" else 1

    # Давление начала открытия Pno и полного открытия Ppo.
    if Pn <= 0.3:
        Pno = Pn + 0.02
        Ppo = Pn + 0.05
    elif Pn <= 6:
        Pno = 1.07 * Pn
        Ppo = 1.15 * Pn
    else:
        Pno = 1.05 * Pn
        Ppo = 1.1 * Pn

    P1 = Ppo + P_atm
    P2 = Pp + P_atm
    B = P2 / P1

    props = await _medium_properties(ctx, config)
    state = props["agregatnoe_sostojanie"] or ""

    params_by_key = props.get("param_names") or {}

    u = props["vjazkost_pa_s"]
    if not u:
        raise MissingParamError(params_by_key.get("viscosity_param") or "Вязкость (Па*с)")

    x0 = 0
    omega = None
    eta_c = None

    if "Газ" in state:
        M = props["molekuljarnaja_massa"]
        n = props["pokazatel_adiabaty"]
        if not M:
            raise MissingParamError(params_by_key.get("molar_param") or "Молярная масса")
        if not n:
            raise MissingParamError(params_by_key.get("adiabatic_param") or "Показатель адиабаты")

        p1 = P1 * 1000 * M / (R * (T + 273.15))
        alpha = 0.8
        Kw = _gas_kw(Ppo, Pn, Pp, Pno)

        Bkr = (2 / (n + 1)) ** (n / (n - 1))
        if B <= Bkr:
            Kb = 1
            if n == 1:
                Kp_kr = 0.60653 ** 2
            else:
                Kp_kr = math.sqrt(2 * n / (n + 1)) * (2 / (n + 1)) ** (1 / (n - 1))
        else:
            Kp_kr = 1
            if n == 1:
                # Изотермическое истечение: экспонента e и натуральный логарифм.
                Kb = B ** 2 * -2 * math.exp(1) * math.log(B)
            else:
                Kb = (((n + 1) / (n - 1)) * (B ** (2 / n) - B ** ((n + 1) / n)) * ((n + 1) / 2)) ** 2

        Gideal = Kp_kr * Kb * math.sqrt(P1 * p1)
        x0 = 1
    elif "Жидкость" in state:
        p1 = props["plotnost_zhidkosti"]
        if not p1:
            raise MissingParamError(params_by_key.get("density_param") or "Плотность жидкости")
        alpha = 0.6
        # (Д.21) с исправленной границей: legacy-ветка `>1.15 and <=0.25`
        # недостижима, корректная граница — 0.15 (по ГОСТ 12.2.085 приложение Д).
        ratio = Pp / Pno
        if ratio <= 0.15:
            Kw = 1
        elif ratio <= 0.25:
            Kw = 0.875 + 1.8333 * ratio - 6.6667 * ratio ** 2
        else:
            Kw = 1.149 - 0.988 * ratio

        Kp = math.sqrt(2 * (1 - B))
        Gideal = Kp * math.sqrt(P1 * p1)
    else:
        # Двухфазный поток — метод Ω (ISO 4126-10).
        x0 = float(props.get("vapor_mass_fraction") or 0)
        p1 = props.get("plotnost_liquid") or props.get("plotnost_zhidkosti") or 0
        alpha = 0.8
        Kw = 1
        if p1 <= 0:
            raise MissingParamError(params_by_key.get("density_param") or "Плотность жидкости")
        omega = _omega_parameter(props, P1, T + 273.15)
        eta_c = _two_phase_critical_ratio(omega)
        Gideal = _two_phase_mass_flux(props, P1, T + 273.15, B)

    # Итерационный расчёт предварительного диаметра седла (как в legacy-raschet).
    DN_s = None
    pre_DN = 0
    Kv = 1
    while DN_s != pre_DN:
        pre_F = Gab / (3.6 * alpha * Kv * Kw * Kc * Gideal * N)
        pre_DN = math.sqrt(4 * pre_F / math.pi)
        Re = Gideal * p1 * pre_DN / u
        if 1000 <= Re <= 100000:
            Kv = (0.9935 + 2.8780 / Re ** 0.5 + 342.75 / Re ** 1.5) ** (-1)
        elif Re < 1000:
            Kv = 0.975 * math.sqrt(1 / 170 / (Re + 0.98))
        else:
            Kv = 1
        F = Gab / (3.6 * alpha * Kv * Kw * Kc * Gideal * N)
        DN_s = math.sqrt(4 * F / math.pi)
    DN_s = math.ceil(DN_s * 10) / 10

    S = math.pi * DN_s ** 2 / 4

    result = {
        "state": state,
        "Pn": Pn,
        "Pno": Pno,
        "Ppo": Ppo,
        "P1": P1,
        "P2": P2,
        "B": B,
        "Kw": Kw,
        "Gideal": Gideal,
        "alpha": alpha,
        "Kc": Kc,
        "p1": p1,
        "Kv": Kv,
        "DN_s": DN_s,
        "S": S,
        "S_eff": S * alpha,
        "x0": x0,
        "omega": omega,
        "eta_c": eta_c,
    }
    ctx.computed["_seat_full"] = result
    return result


async def valve_start_pressure(ctx: FormulaContext, config):
    """Давление начала открытия с противодавлением, кгс/см²."""
    r = await _seat_calc_full(ctx, config)
    return r["Pno"] * 10.197162


async def valve_full_pressure(ctx: FormulaContext, config):
    """Давление полного открытия с противодавлением, кгс/см²."""
    r = await _seat_calc_full(ctx, config)
    return r["Ppo"] * 10.197162


async def valve_inlet_pressure(ctx: FormulaContext, config):
    """Давление на входе, кгс/см² абс."""
    r = await _seat_calc_full(ctx, config)
    return r["P1"] * 10.197162


async def valve_outlet_pressure(ctx: FormulaContext, config):
    """Давление на выходе, кгс/см² абс."""
    r = await _seat_calc_full(ctx, config)
    return r["P2"] * 10.197162


async def valve_kw(ctx: FormulaContext, config):
    """Коэффициент Kw, учитывающий эффект неполного открытия из-за противодавления."""
    r = await _seat_calc_full(ctx, config)
    return r["Kw"]


async def valve_mass_velocity(ctx: FormulaContext, config):
    """Массовая скорость, кг/(м²·с)."""
    r = await _seat_calc_full(ctx, config)
    return r["Gideal"]


async def valve_seat_diameter(ctx: FormulaContext, config):
    """Предварительный диаметр седла клапана, мм."""
    r = await _seat_calc_full(ctx, config)
    return r["DN_s"]


async def valve_seat_area(ctx: FormulaContext, config):
    """Площадь седла клапана, мм²."""
    r = await _seat_calc_full(ctx, config)
    return r["S"]


async def valve_effective_area(ctx: FormulaContext, config):
    """Эффективная площадь седла клапана, мм²."""
    r = await _seat_calc_full(ctx, config)
    return r["S_eff"]


async def valve_vapor_quality(ctx: FormulaContext, config):
    """Массовое паросодержание x0 (0 — жидкость, 1 — газ, иначе из состава)."""
    r = await _seat_calc_full(ctx, config)
    return r["x0"]


async def valve_omega(ctx: FormulaContext, config):
    """Параметр Ω (двухфазный поток; для газа/жидкости — None)."""
    r = await _seat_calc_full(ctx, config)
    return r["omega"]


async def valve_critical_ratio(ctx: FormulaContext, config):
    """Критическое отношение давлений ηc (двухфазный поток; иначе None)."""
    r = await _seat_calc_full(ctx, config)
    return r["eta_c"]
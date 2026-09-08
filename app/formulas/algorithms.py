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


def _resolve_mixture_mode(ctx: FormulaContext, config: dict | None) -> str | None:
    """
    Определяет тип смеси по двум входным параметрам.

    - «Смесь» — чекбокс (True/False). Если выключен/не выбран — смесь не
      рассчитывается, возвращается None.
    - «Тип смеси» — select со значениями «газовая»/«жидкостная»/«двухфазный
      поток». Если чекбокс включён, а тип не выбран — поднимается
      MissingParamError (пользователь должен его заполнить).

    Имена параметров захардкожены, но в formula_config можно переопределить
    ключами `mixture_param` и `type_param`.
    """
    config = config or {}
    switch = ctx.get_opt(config.get("mixture_param") or MIXTURE_SWITCH)
    if not switch:
        # Чекбокс не отмечен / «нет» — смесь выключена.
        return None

    type_name = config.get("type_param") or MIXTURE_TYPE_PARAM
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
    mode = _resolve_mixture_mode(ctx, config)
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
            "molekuljarnaja_massa": mapping.get(molar_mass_col),
            "plotnost_zhidkosti": mapping.get(density_col),
            "vjazkost_pa_s": mapping.get(viscosity_col),
            "isobaric_capacity": mapping.get(isobaric_col),
            "isochoric_capacity": mapping.get(isochoric_col),
            "pokazatel_adiabaty": mapping.get(adiabatic_col),
            "compressibility_factor": mapping.get(factor_col),
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
        "material": "",
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

        result["molekuljarnaja_massa"] = mix_molar
        result["plotnost_zhidkosti"] = ch_den / zn_den if zn_den else 0
        result["vjazkost_pa_s"] = 10 ** pre_viscosity
        result["isobaric_capacity"] = mix_isobaric
        result["isochoric_capacity"] = mix_isochoric

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

        result["molekuljarnaja_massa"] = pre_M
        result["vjazkost_pa_s"] = viscosity_ch / viscosity_zn if viscosity_zn else 0
        result["pokazatel_adiabaty"] = adiabatic_index
        result["plotnost_zhidkosti"] = density / 22.4
        result["isobaric_capacity"] = isobaric
        result["isochoric_capacity"] = isochoric
        result["factor"] = factor

    elif homogeneous:
        result["agregatnoe_sostojanie"] = next(iter(env_types))

        ch_den = 0
        zn_den = 0
        pre_viscosity = 0
        pre_M = 0

        for env in envs_json:
            r = env["r"]
            result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r * 100:.0f}% "
            ch_den += float(env["plotnost_zhidkosti"] or 0) * r
            zn_den += r
            pre_viscosity += float(env["vjazkost_pa_s"] or 0) * r
            pre_M += float(env["molekuljarnaja_massa"] or 0) * r

        result["plotnost_zhidkosti"] = ch_den / zn_den if zn_den else 0
        result["vjazkost_pa_s"] = pre_viscosity
        result["molekuljarnaja_massa"] = pre_M

    else:
        result["agregatnoe_sostojanie"] = "Двухфазный поток"

        density_ch = 0
        density_zn = 0
        pre_u = 0

        for env in envs_json:
            r = env["r"]
            result["nazvanie_rabochej_sredy"] += f"{env['name']}:{r * 100:.0f}% "

            if env["environment"] == "Газ":
                M = float(env["molekuljarnaja_massa"] or 0)
                density_ch += (M / 22.4) * r
                density_zn += r
            elif env["environment"] == "Жидкость":
                density_ch += float(env["plotnost_zhidkosti"] or 0) * r
                density_zn += r

            pre_u += r * float(env["vjazkost_pa_s"] or 0) * float(env["molekuljarnaja_massa"] or 0)

        result["plotnost_zhidkosti"] = density_ch / density_zn if density_zn else 0
        result["vjazkost_pa_s"] = pre_u

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
        "Материал": result["material"],
    }
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

import re
import math

from .engine import FormulaContext, MissingParamError


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


# === Расчёт характеристик смесей ===

def _gather_composition(ctx: FormulaContext, config: dict | None) -> list[tuple[str, float]]:
    """
    Собирает состав смеси из параметров-слотов «Среда N» / «Доля N».

    Возвращает список пар (название среды, мольная доля от 0 до 1).
    Слоты можно задать явно в formula_config["slots"] (список имён, чередуя
    среду и долю), иначе они определяются автоматически: из выбранных значений
    берутся параметры с именами вида «Среда 1..N» и «Доля 1..N».
    """
    config = config or {}
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

    return pairs


def _validate_composition(composition: list[tuple[str, float]]) -> str | None:
    """Проверяет состав: минимум две среды и сумма долей = 100%. Возвращает текст ошибки."""
    if len(composition) < 2:
        return "Смесь не может состоять менее чем из двух сред!"

    total = sum(share for _, share in composition)
    if abs(total - 100.0) > 0.0001:
        return f"Сумма мольных долей сред смеси должна составлять 100%, а не {total}%"

    return None


async def _resolve_media_columns(ctx: FormulaContext) -> dict[str, str]:
    """
    Определяет физическую таблицу сред и её колонки для продукта.

    Возвращает map: русское название характеристики -> транслитерированное имя колонки.
    Колонки-характеристики ищутся по названиям параметров продукта (type='Table').
    """
    from sqlalchemy import text

    rows = await ctx.db.execute(text(
        """
        SELECT name, transliterated_name
        FROM parameter_schemas
        WHERE product_id = :product_id AND type = 'Table' AND table_name IS NOT NULL
        """
    ), {"product_id": ctx.product_id})

    columns: dict[str, str] = {}

    for row in rows.mappings().all():
        name = (row["name"] or "").strip()
        translit = (row["transliterated_name"] or "").strip()
        if not name or not translit:
            continue

        columns[name] = translit

    return columns


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


async def _mixture_properties(ctx: FormulaContext, config: dict | None) -> dict:
    """
    Сервисная функция: вычисляет все характеристики смеси разом.

    Используется функциями-характеристиками (mixture_density и др.) и
    кэшируется в ctx.computed["_mixture_full"], чтобы не повторять SQL по
    каждому параметру.
    """
    cached = ctx.computed.get("_mixture_full")
    if cached is not None:
        return cached

    if not ctx.db or not ctx.product_id:
        raise MissingParamError("Среда")

    from sqlalchemy import text

    composition = _gather_composition(ctx, config)

    if not composition:
        # Подсказываем пользователю, какой слот заполнить первым.
        slots = (config or {}).get("slots")
        first_name = slots[0] if slots else "Среда 1"
        raise MissingParamError(first_name)

    error = _validate_composition(composition)
    if error:
        raise ValueError(error)

    columns = await _resolve_media_columns(ctx)

    # Находим основные характеристики по русским названиям параметров продукта.
    def find_column(*keywords: str) -> str | None:
        for name, translit in columns.items():
            lowered = name.lower()
            if any(keyword.lower() in lowered for keyword in keywords):
                return translit
        return None

    env_name_col = find_column("название рабочей среды", "рабочая среда", "среда")
    aggregate_col = find_column("агрегатное состояние", "состояние")
    molar_mass_col = find_column("молярная масса", "молекулярная масса")
    density_col = find_column("плотность")
    viscosity_col = find_column("вязкость")
    adiabatic_col = find_column("показатель адиабаты", "адиабат")
    isobaric_col = find_column("изобарная теплоёмкость", "изобарн", "cp")
    isochoric_col = find_column("изохорная теплоёмкость", "изохорн", "cv")
    factor_col = find_column("фактор сжимаемости", "сжимаемости")
    material_col = find_column("материал")

    if not env_name_col:
        raise MissingParamError("Название рабочей среды")

    table_name = await _resolve_media_table(ctx)
    if not table_name:
        raise MissingParamError("Название рабочей среды")

    select_columns = [env_name_col]
    env_keys = [env_name_col]
    if aggregate_col:
        select_columns.append(aggregate_col)
        env_keys.append(aggregate_col)
    if molar_mass_col:
        select_columns.append(molar_mass_col)
        env_keys.append(molar_mass_col)
    if density_col:
        select_columns.append(density_col)
        env_keys.append(density_col)
    if viscosity_col:
        select_columns.append(viscosity_col)
        env_keys.append(viscosity_col)
    if adiabatic_col:
        select_columns.append(adiabatic_col)
        env_keys.append(adiabatic_col)
    if isobaric_col:
        select_columns.append(isobaric_col)
        env_keys.append(isobaric_col)
    if isochoric_col:
        select_columns.append(isochoric_col)
        env_keys.append(isochoric_col)
    if factor_col:
        select_columns.append(factor_col)
        env_keys.append(factor_col)
    if material_col:
        select_columns.append(material_col)
        env_keys.append(material_col)

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
        result["agregatnoe_sostojanie"] = "Неоднородная смесь"

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
    """Агрегатное состояние смеси: «Газ», «Жидкость» или «Неоднородная смесь»."""
    result = await _mixture_properties(ctx, config)
    return result["agregatnoe_sostojanie"]


async def mixture_density(ctx: FormulaContext, config):
    """Плотность смеси, кг/м³ (для газа — при нормальных условиях)."""
    result = await _mixture_properties(ctx, config)
    return result["plotnost_zhidkosti"]


async def mixture_molar_mass(ctx: FormulaContext, config):
    """Молярная масса смеси, г/моль."""
    result = await _mixture_properties(ctx, config)
    return result["molekuljarnaja_massa"]


async def mixture_viscosity(ctx: FormulaContext, config):
    """Вязкость смеси (Па·с)."""
    result = await _mixture_properties(ctx, config)
    return result["vjazkost_pa_s"]


async def mixture_adiabatic_index(ctx: FormulaContext, config):
    """Показатель адиабаты смеси."""
    result = await _mixture_properties(ctx, config)
    return result["pokazatel_adiabaty"]


async def mixture_isobaric_capacity(ctx: FormulaContext, config):
    """Изобарная теплоёмкость смеси."""
    result = await _mixture_properties(ctx, config)
    return result["isobaric_capacity"]


async def mixture_isochoric_capacity(ctx: FormulaContext, config):
    """Изохорная теплоёмкость смеси."""
    result = await _mixture_properties(ctx, config)
    return result["isochoric_capacity"]


async def mixture_factor(ctx: FormulaContext, config):
    """Фактор сжимаемости смеси."""
    result = await _mixture_properties(ctx, config)
    return result["factor"]


async def mixture_material(ctx: FormulaContext, config):
    """Материал, подобранный из компонентов смеси."""
    result = await _mixture_properties(ctx, config)
    return result["material"]
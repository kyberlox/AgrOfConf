import asyncio
import math
import sys
import types

sys.path.insert(0, "/tmp/opencode/stub")

# Стабы для sqlalchemy (тест не использует реальную БД).
import types as _t
_sa = _t.ModuleType("sqlalchemy")
_sa.select = lambda *a, **k: None
_sa.text = lambda s: s
_sa.create_engine = lambda *a, **k: None
class _AsyncSession:
    pass
_sa.AsyncSession = _AsyncSession
sys.modules["sqlalchemy"] = _sa
for _sub in ("sqlalchemy.ext", "sqlalchemy.ext.asyncio"):
    _m = _t.ModuleType(_sub)
    _m.AsyncSession = _AsyncSession
    sys.modules[_sub] = _m

fake_schema = types.ModuleType("app.TablePakage.model.parameter_schema")

class ParameterSchema:
    def __init__(self, **kw):
        self.type = kw.get("type")
        self.name = kw.get("name")

fake_schema.ParameterSchema = ParameterSchema
sys.modules["app.TablePakage.model.parameter_schema"] = fake_schema

sys.path.insert(0, "/home/kyberlox/Рабочий стол/конфигуратор ПК/код/old_version")

from app.formulas.integration import apply_mixture_overrides

PRESSURE_TABLE = "press_table"
VALVE_TABLE = "valve_table"
FLANGE_IN_TABLE = "flange_in"
FLANGE_OUT_TABLE = "flange_out"

PRESSURE_ROWS = [
    {"material": "25Л", "t_max": 200, "pressure_max": 6.0, "pn": 16},
    {"material": "25Л", "t_max": 300, "pressure_max": 10.0, "pn": 25},
    {"material": "20ГЛ", "t_max": 250, "pressure_max": 8.0, "pn": 16},
]

VALVE_ROWS = [
    {"tip_pk": "Тип A", "diametr_sedla": 25, "pn_vhodnoe": 16, "pn_vyhodnoe": 16,
     "dn_vhodnoi": 25, "dn_vyhodnoi": 25, "diapazon_davleniya": "2-6",
     "nom_pruzhiny": "П1", "material_pruzhiny": "12Х18Н10Т"},
    {"tip_pk": "Тип A", "diametr_sedla": 32, "pn_vhodnoe": 16, "pn_vyhodnoe": 16,
     "dn_vhodnoi": 32, "dn_vyhodnoi": 32, "diapazon_davleniya": "2-6",
     "nom_pruzhiny": "П2", "material_pruzhiny": "12Х18Н10Т"},
    {"tip_pk": "Тип A", "diametr_sedla": 25, "pn_vhodnoe": 25, "pn_vyhodnoe": 25,
     "dn_vhodnoi": 25, "dn_vyhodnoi": 25, "diapazon_davleniya": "2-10",
     "nom_pruzhiny": "П3", "material_pruzhiny": "12Х18Н10Т"},
    {"tip_pk": "Тип B", "diametr_sedla": 50, "pn_vhodnoe": 16, "pn_vyhodnoe": 16,
     "dn_vhodnoi": 50, "dn_vyhodnoi": 50, "diapazon_davleniya": "2-6",
     "nom_pruzhiny": "П4", "material_pruzhiny": "12Х18Н10Т"},
    {"tip_pk": "Пилотный (П)", "diametr_sedla": 25, "pn_vhodnoe": 16, "pn_vyhodnoe": 16,
     "dn_vhodnoi": 25, "dn_vyhodnoi": 25, "diapazon_davleniya": "2-6",
     "nom_pruzhiny": "П5", "material_pruzhiny": "12Х18Н10Т"},
    {"tip_pk": "Пружинный (В)", "diametr_sedla": 40, "pn_vhodnoe": 16, "pn_vyhodnoe": 16,
     "dn_vhodnoi": 40, "dn_vyhodnoi": 40, "diapazon_davleniya": "2-6",
     "nom_pruzhiny": "П6", "material_pruzhiny": "51ХФА"},
    {"tip_pk": "Пружинный (В)", "diametr_sedla": 50, "pn_vhodnoe": 16, "pn_vyhodnoe": 16,
     "dn_vhodnoi": 50, "dn_vyhodnoi": 50, "diapazon_davleniya": "2-10",
     "nom_pruzhiny": "П7", "material_pruzhiny": "50ХФА"},
]

MEDIA_TABLE = {
    "Газ": {"agregatnoe_sostojanie": "Газ", "molekuljarnaja_massa": 16, "plotnost_zhidkosti": 0.7,
            "vjazkost_pa_s": 0.00001, "isobaric_capacity": 2200, "isochoric_capacity": 1600,
            "pokazatel_adiabaty": 1.4, "factor": 1.0, "material_media": "25Л", "teplota_paroobrazovanija": 500000},
    "Кислород": {"agregatnoe_sostojanie": "Газ", "molekuljarnaja_massa": 32, "plotnost_zhidkosti": 1.4,
                 "vjazkost_pa_s": 0.00002, "isobaric_capacity": 920, "isochoric_capacity": 660,
                 "pokazatel_adiabaty": "нет", "factor": "нет", "material_media": "25Л", "teplota_paroobrazovanija": 200000},
}

FLANGE_IN_ROWS = [
    {"davlenie_vh": 16, "standart_ispolnenija_vh": "ГОСТ 33259-2015 (вх)", "flance_na_vhode": "Фланец вх PN16"},
    {"davlenie_vh": 25, "standart_ispolnenija_vh": "ГОСТ 33259-2015 (вх25)", "flance_na_vhode": "Фланец вх PN25"},
]

FLANGE_OUT_ROWS = [
    {"davlenie_vyh": 16, "standart_ispolnenija_vyh": "ГОСТ 33259-2015 (вых)", "flance_na_vyhode": "Фланец вых PN16"},
]

VALVE_SCHEMA_ROWS = [
    {"name": "Тип ПК", "transliterated_name": "tip_pk", "table_name": VALVE_TABLE},
    {"name": "Номинальный диаметр седла клапана, мм", "transliterated_name": "diametr_sedla", "table_name": VALVE_TABLE},
    {"name": "PN входное", "transliterated_name": "pn_vhodnoe", "table_name": VALVE_TABLE},
    {"name": "PN выходное", "transliterated_name": "pn_vyhodnoe", "table_name": VALVE_TABLE},
    {"name": "DN входной", "transliterated_name": "dn_vhodnoi", "table_name": VALVE_TABLE},
    {"name": "DN выходной", "transliterated_name": "dn_vyhodnoi", "table_name": VALVE_TABLE},
    {"name": "Диапазон давления настройки, кгс/см²", "transliterated_name": "diapazon_davleniya", "table_name": VALVE_TABLE},
    {"name": "№ пружины", "transliterated_name": "nom_pruzhiny", "table_name": VALVE_TABLE},
    {"name": "Материал пружины", "transliterated_name": "material_pruzhiny", "table_name": VALVE_TABLE},
]

PRESSURE_SCHEMA_ROWS = [
    {"name": "material", "transliterated_name": "material", "table_name": PRESSURE_TABLE},
    {"name": "T максимальное", "transliterated_name": "t_max", "table_name": PRESSURE_TABLE},
    {"name": "Давление настройки max (МПа)", "transliterated_name": "pressure_max", "table_name": PRESSURE_TABLE},
    {"name": "PN (МПа)", "transliterated_name": "pn", "table_name": PRESSURE_TABLE},
]

FLANGE_IN_SCHEMA_ROWS = [
    {"name": "Давление вх", "transliterated_name": "davlenie_vh", "table_name": FLANGE_IN_TABLE},
    {"name": "Стандарт исполнения вх", "transliterated_name": "standart_ispolnenija_vh", "table_name": FLANGE_IN_TABLE},
    {"name": "Фланец на входе", "transliterated_name": "flance_na_vhode", "table_name": FLANGE_IN_TABLE},
]

FLANGE_OUT_SCHEMA_ROWS = [
    {"name": "Давление вых", "transliterated_name": "davlenie_vyh", "table_name": FLANGE_OUT_TABLE},
    {"name": "Стандарт исполнения вых", "transliterated_name": "standart_ispolnenija_vyh", "table_name": FLANGE_OUT_TABLE},
    {"name": "Фланец на выходе", "transliterated_name": "flance_na_vyhode", "table_name": FLANGE_OUT_TABLE},
]

MEDIA_SCHEMA_ROWS = [
    {"name": "Название рабочей среды", "transliterated_name": "nazvanie_rabochej_sredy", "table_name": "media"},
    {"name": "Агрегатное состояние", "transliterated_name": "agregatnoe_sostojanie", "table_name": "media"},
    {"name": "Молярная масса", "transliterated_name": "molekuljarnaja_massa", "table_name": "media"},
    {"name": "Плотность", "transliterated_name": "plotnost_zhidkosti", "table_name": "media"},
    {"name": "Вязкость", "transliterated_name": "vjazkost_pa_s", "table_name": "media"},
    {"name": "Материал", "transliterated_name": "material_media", "table_name": "media"},
]

ALL_COLUMNS = [
    "nazvanie_rabochej_sredy", "agregatnoe_sostojanie", "molekuljarnaja_massa",
    "plotnost_zhidkosti", "vjazkost_pa_s", "isobaric_capacity", "isochoric_capacity",
    "pokazatel_adiabaty", "factor", "teplota_paroobrazovanija", "material_media",
    "material", "t_max", "pressure_max", "pn",
    "tip_pk", "diametr_sedla", "pn_vhodnoe", "pn_vyhodnoe", "dn_vhodnoi", "dn_vyhodnoi",
    "diapazon_davleniya", "nom_pruzhiny", "material_pruzhiny",
    "davlenie_vh", "standart_ispolnenija_vh", "flance_na_vhode",
    "davlenie_vyh", "standart_ispolnenija_vyh", "flance_na_vyhode",
]


class Row:
    def __init__(self, mapping):
        self._mapping = mapping

    def get(self, key, default=None):
        return self._mapping.get(key, default)

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self._mapping.values())[key]
        return self._mapping[key]

    def __contains__(self, key):
        return key in self._mapping


class Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        r = self._rows[0] if self._rows else None
        if r is None:
            return None
        if isinstance(r, str):
            return r
        if isinstance(r, Row):
            if "table_name" in r._mapping:
                return r._mapping["table_name"]
            return list(r._mapping.values())[0]
        return r

    def mappings(self):
        return Result(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


def _rows_from_dicts(dicts):
    return [Row(d) for d in dicts]


class FakeDB:
    async def execute(self, sql, params=None):
        sql_text = str(sql)
        params = params or {}
        if "formula_config ->> 'func'" in sql_text or "formula_config -> 'func'" in sql_text:
            return Result([Row({"func": "flange_standard_inlet"}),
                           Row({"func": "flange_standard_outlet"})])
        if "type = 'FormulaMix'" in sql_text:
            return Result([Row({"name": "Состав смеси"})])
        if "transliterated_name = :col" in sql_text or "transliterated_name = '" in sql_text:
            col = params.get("col")
            if col == "material":
                return Result([Row({"table_name": PRESSURE_TABLE})])
            if col == "tip_pk":
                return Result([Row({"table_name": VALVE_TABLE})])
            if col == "flance_na_vhode":
                return Result([Row({"table_name": FLANGE_IN_TABLE})])
            if col == "flance_na_vyhode":
                return Result([Row({"table_name": FLANGE_OUT_TABLE})])
            return Result([Row({"table_name": PRESSURE_TABLE})])
        if "information_schema.columns" in sql_text:
            return Result([Row({"column_name": c}) for c in ALL_COLUMNS])
        if "SELECT name, transliterated_name, table_name" in sql_text:
            return Result(_rows_from_dicts(
                MEDIA_SCHEMA_ROWS + PRESSURE_SCHEMA_ROWS + VALVE_SCHEMA_ROWS + FLANGE_IN_SCHEMA_ROWS + FLANGE_OUT_SCHEMA_ROWS
            ))
        if "SELECT name, transliterated_name" in sql_text:
            return Result(_rows_from_dicts(MEDIA_SCHEMA_ROWS))
        if "SELECT name, table_name" in sql_text and "type = 'Table'" in sql_text:
            return Result(_rows_from_dicts(
                MEDIA_SCHEMA_ROWS + PRESSURE_SCHEMA_ROWS + VALVE_SCHEMA_ROWS + FLANGE_IN_SCHEMA_ROWS + FLANGE_OUT_SCHEMA_ROWS
            ))
        if "SELECT table_name" in sql_text:
            return Result(["media"])
        if "SELECT DISTINCT table_name" in sql_text and "pid" in params:
            return Result([Row({"table_name": t}) for t in
                           ["media", PRESSURE_TABLE, VALVE_TABLE, FLANGE_IN_TABLE, FLANGE_OUT_TABLE]])
        if "SELECT DISTINCT" in sql_text:
            return Result([Row({"nazvanie_rabochej_sredy": "Газ", "agregatnoe_sostojanie": "Газ"})])
        if "SELECT name FROM parameter_schemas" in sql_text and "table_name = :tbl" in sql_text:
            names = {
                "media": MEDIA_SCHEMA_ROWS,
                PRESSURE_TABLE: PRESSURE_SCHEMA_ROWS,
                VALVE_TABLE: VALVE_SCHEMA_ROWS,
                FLANGE_IN_TABLE: FLANGE_IN_SCHEMA_ROWS,
                FLANGE_OUT_TABLE: FLANGE_OUT_SCHEMA_ROWS,
            }.get(params.get("tbl"), {})
            return Result(_rows_from_dicts(names) if names else [])
        if "SELECT name FROM parameter_schemas" in sql_text:
            return Result([])
        if "array_agg" in sql_text and ":dav" in sql_text:
            dav = params.get("dav")
            try:
                dav_num = float(dav)
            except (TypeError, ValueError):
                dav_num = None
            if "flange_in" in sql_text:
                rows = [d for d in FLANGE_IN_ROWS
                        if dav_num is not None and abs(float(d["davlenie_vh"]) - dav_num) < 1e-9]
                colmap = {"standart_ispolnenija_vh": "standart_ispolnenija_vh",
                          "flance_na_vhode": "flance_na_vhode"}
            elif "flange_out" in sql_text:
                rows = [d for d in FLANGE_OUT_ROWS
                        if dav_num is not None and abs(float(d["davlenie_vyh"]) - dav_num) < 1e-9]
                colmap = {"standart_ispolnenija_vyh": "standart_ispolnenija_vyh",
                          "flance_na_vyhode": "flance_na_vyhode"}
            else:
                return Result([])
            out = {}
            for col_alias in colmap:
                col = colmap[col_alias]
                vals = sorted({str(r[col]) for r in rows if r.get(col) is not None})
                out[col_alias] = list(vals)
            return Result([Row(out)])
        if "FROM \"" in sql_text:
            if ":tp" in sql_text:
                tp = params.get("tp")
                return Result([Row(d) for d in VALVE_ROWS if d["tip_pk"] == tp])
            if ":mat" in sql_text:
                mat = params.get("mat")
                return Result([Row(d) for d in PRESSURE_ROWS if d["material"] == mat])
            if "flange_in" in sql_text and ":p" in sql_text:
                p = params.get("p")
                return Result([Row(d) for d in FLANGE_IN_ROWS if abs(float(d["davlenie_vh"]) - float(p)) < 1e-9])
            if "flange_out" in sql_text and ":p" in sql_text:
                p = params.get("p")
                return Result([Row(d) for d in FLANGE_OUT_ROWS if abs(float(d["davlenie_vyh"]) - float(p)) < 1e-9])
            if params.get("env_name"):
                return Result([Row(MEDIA_TABLE.get(params["env_name"]) or {})])
        return Result([])


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


ok = True


def t(name, got, expected):
    global ok
    ok = ok and (got == expected)
    print(("OK " if got == expected else "FAIL ") + name + f" -> {got!r}")


db = FakeDB()

SELECTED = {
    "Смесь": True,
    "Тип смеси": "газовая",
    "Состав смеси": [{"Газ": 40}, {"Кислород": 60}],
    "Температура рабочей среды (°C)": "150",
    "Давление настройки (МПа)": "5.0",
}


def make_params():
    return [
        {"name": "Материал", "table_name": "media", "response_value": None, "editable": True, "visibility": True},
        {"name": "material", "table_name": PRESSURE_TABLE, "response_value": None, "editable": True, "visibility": True},
        {"name": "T максимальное", "table_name": PRESSURE_TABLE, "response_value": None, "editable": True, "visibility": True},
        {"name": "Давление настройки max (МПа)", "table_name": PRESSURE_TABLE, "response_value": None, "editable": True, "visibility": True},
        {"name": "PN (МПа)", "table_name": PRESSURE_TABLE, "response_value": None, "editable": True, "visibility": True},
        {"name": "Диаметр", "table_name": "other", "response_value": "200", "editable": True, "visibility": True},
        {"name": "Номинал", "table_name": "other", "response_value": "0", "editable": True, "visibility": True},
    ]

print("=== Давление / смесь ===")
params = run(apply_mixture_overrides(db, make_params(), SELECTED, 1))
by_name = {p["name"]: p for p in params}
t("pres: материал таблицы = 25Л", by_name["material"]["response_value"], "25Л")
t("pres: T максимальное = 200", by_name["T максимальное"]["response_value"], 200)
t("pres: Давление max = 6.0", float(by_name["Давление настройки max (МПа)"]["response_value"]), 6.0)
t("pres: PN = 16", by_name["PN (МПа)"]["response_value"], 16)
t("pres: видимость не меняется", by_name["material"]["visibility"], True)
t("pres: PN видимость не меняется", by_name["PN (МПа)"]["visibility"], True)
t("pres: media Материал НЕ скрыт (другая таблица)", by_name["Материал"]["visibility"], True)
t("pres: Диаметр не тронут", by_name["Диаметр"]["response_value"], "200")

params = run(apply_mixture_overrides(db, make_params(), {**SELECTED, "Давление настройки (МПа)": "11"}, 1))
by_name = {p["name"]: p for p in params}
t("pres: нет подходящей -> T не заполнен", by_name["T максимальное"]["response_value"], None)
t("pres: нет подходящей -> PN не заполнен", by_name["PN (МПа)"]["response_value"], None)

print("=== Формула nominal_pressure через движок ===")
from app.formulas.engine import compute_formulas

SELECTED2 = {
    "Материал": "25Л",
    "Температура рабочей среды (°C)": "150",
    "Давление настройки (МПа)": "5.0",
}
results, computed = run(compute_formulas(
    db,
    [{"name": "Предварительное номинальное давление", "formula_config": {"func": "nominal_pressure"}}],
    SELECTED2,
    1,
))
t("fn: pn = 16", results["Предварительное номинальное давление"]["response_value"], 16)
pres = computed["_pressure_table"]
t("fn: material=25Л", pres["material"], "25Л")
t("fn: t_max=200", pres["t_max"], 200)

results2, _ = run(compute_formulas(
    db,
    [{"name": "P", "formula_config": {"func": "nominal_pressure"}}],
    {"Материал": ""},
    1,
))
t("fn: без материала -> просьба заполнить", "Заполните параметр" in str(results2["P"].get("response_value")), True)

print("=== Таблица клапана (формулы) ===")
from app.formulas.integration import _fill_pressure_entries, _fill_valve_entries

SELECTED3 = {
    "Тип клапана": "Тип A",
    "Предварительный диаметр седла клапана": "28",
    "Предварительное номинальное давление": 16,
}
specs = [
    {"name": "Выбор седла клапана", "formula_config": {"func": "valve_selection"}},
    {"name": "Площадь седла клапана", "formula_config": {"func": "seat_circle_area"}},
    {"name": "Эффективная площадь седла клапана", "formula_config": {"func": "seat_effective_area"}},
]
results, computed = run(compute_formulas(db, specs, SELECTED3, 1))
area = math.pi * 32 ** 2 / 4
t("valve: seat=32", results["Выбор седла клапана"]["response_value"], 32)
t("valve: area", abs(results["Площадь седла клапана"]["response_value"] - area) < 1e-6, True)
t("valve: eff_area", abs(results["Эффективная площадь седла клапана"]["response_value"] - area) < 1e-6, True)
sel = computed["_valve_selection"]
t("valve: тип_пк=Тип A", sel["тип_пк"], "Тип A")
t("valve: pn_in=16", sel["pn_in"], 16)
t("valve: пружина П2", sel["spring_no"], "П2")
t("valve: DN входной=32", sel["dn_in"], 32)

SELECTED4 = {
    "Материал": "25Л",
    "Температура рабочей среды (°C)": "150",
    "Давление настройки (МПа)": "5.0",
    "Тип клапана": "Тип A",
    "Предварительный диаметр седла клапана": "28",
}
specs4 = [{"name": "Предварительное номинальное давление", "formula_config": {"func": "nominal_pressure"}}] + specs
results, computed = run(compute_formulas(db, specs4, SELECTED4, 1))
t("valve-dep: pn=16", results["Предварительное номинальное давление"]["response_value"], 16)
t("valve-dep: seat=32", results["Выбор седла клапана"]["response_value"], 32)
t("valve-dep: area", abs(results["Площадь седла клапана"]["response_value"] - area) < 1e-6, True)

# Площади без драйверной формулы «Выбор седла клапана» -> запасной подбор строки.
results5, _ = run(compute_formulas(
    db,
    [
        {"name": "Площадь седла клапана", "formula_config": {"func": "seat_circle_area"}},
        {"name": "Эффективная площадь седла клапана", "formula_config": {"func": "seat_effective_area"}},
    ],
    SELECTED3,
    1,
))
t("valve-nodrive: area", abs(results5["Площадь седла клапана"]["response_value"] - area) < 1e-6, True)
t("valve-nodrive: eff_area", abs(results5["Эффективная площадь седла клапана"]["response_value"] - area) < 1e-6, True)

print("=== Заполнение табличных параметров клапана (_fill_valve_entries) ===")
valve_params = [
    {"name": "Тип ПК", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Номинальный диаметр седла клапана, мм", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "PN входное", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "PN выходное", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "DN входной", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "DN выходной", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Диапазон давления настройки, кгс/см²", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "№ пружины", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Материал пружины", "table_name": VALVE_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Тип клапана", "table_name": None, "response_value": None, "editable": True, "visibility": True},
    {"name": "Диаметр трубы", "table_name": "other", "response_value": "500", "editable": True, "visibility": True},
]
_fill_valve_entries(valve_params, sel)
by = {p["name"]: p for p in valve_params}
t("fill: Тип ПК=Тип A", by["Тип ПК"]["response_value"], "Тип A")
t("fill: диаметр=32", by["Номинальный диаметр седла клапана, мм"]["response_value"], 32)
t("fill: PN входное=16", by["PN входное"]["response_value"], 16)
t("fill: № пружины=П2", by["№ пружины"]["response_value"], "П2")
t("fill: видимость не меняется (свойство админки)", by["№ пружины"]["visibility"], True)
t("fill: нередактируем", by["№ пружины"]["editable"], False)
t("fill: входной Тип клапана НЕ тронут", by["Тип клапана"]["response_value"], None)
t("fill: Диаметр трубы НЕ тронут", by["Диаметр трубы"]["response_value"], "500")

print("=== Таблицы фланцев (формулы) ===")
from app.formulas.integration import _fill_flange_entries, _finalize_connection_visibility

specs_flange = [
    {"name": "Выбор седла клапана", "formula_config": {"func": "valve_selection"}},
    {"name": "Стандарт фланца на входе", "formula_config": {"func": "flange_standard_inlet"}},
    {"name": "Стандарт фланца на выходе", "formula_config": {"func": "flange_standard_outlet"}},
]
results_f, computed_f = run(compute_formulas(db, specs_flange, SELECTED3, 1))
t("flange: вход standard по PN входное", results_f["Стандарт фланца на входе"]["response_value"], "ГОСТ 33259-2015 (вх)")
t("flange: выход standard по PN выходное", results_f["Стандарт фланца на выходе"]["response_value"], "ГОСТ 33259-2015 (вых)")
fin = computed_f["_flange_inlet"]
fout = computed_f["_flange_outlet"]
t("flange: давление входа = PN входное (16)", fin["давление"], 16)
t("flange: давление выхода = PN выходное (16)", fout["давление"], 16)
t("flange: фланец входа", fin["фланец"], "Фланец вх PN16")
t("flange: стандарт выхода", fout["стандарт"], "ГОСТ 33259-2015 (вых)")

# Фланцы ждут подбор седла (PN берётся из строки клапана), а подбор ждёт формулу PN.
results_f2, computed_f2 = run(compute_formulas(
    db,
    [
        {"name": "Предварительное номинальное давление", "formula_config": {"func": "nominal_pressure"}},
        {"name": "Выбор седла клапана", "formula_config": {"func": "valve_selection"}},
        {"name": "Стандарт фланца на входе", "formula_config": {"func": "flange_standard_inlet"}},
        {"name": "Стандарт фланца на выходе", "formula_config": {"func": "flange_standard_outlet"}},
    ],
    {**SELECTED4, "Тип клапана": "Тип A", "Предварительный диаметр седла клапана": "28"},
    1,
))
t("flange-dep: вх standard после подбора", results_f2["Стандарт фланца на входе"]["response_value"], "ГОСТ 33259-2015 (вх)")
t("flange-dep: вых standard после подбора", results_f2["Стандарт фланца на выходе"]["response_value"], "ГОСТ 33259-2015 (вых)")

# Без подбора клапана (нет диаметра) — None, а не ошибка «Заполните».
results_f3, _ = run(compute_formulas(db, specs_flange, {"Тип клапана": "Тип A"}, 1))
t("flange: без диаметра -> None", results_f3["Стандарт фланца на входе"]["response_value"], None)

# PN = 25: входная таблица имеет строку с давлением 25, выходная — нет.
# «Давление» всё равно должно = PN выходное (25), стандарт/фланец остаются пустыми.
SELECTED25 = {
    "Тип клапана": "Тип A",
    "Предварительный диаметр седла клапана": "20",
    "Предварительное номинальное давление": 25,
}
results_f4, computed_f4 = run(compute_formulas(db, specs_flange, SELECTED25, 1))
t("flange25: вход standard (есть строка 25)",
  results_f4["Стандарт фланца на входе"]["response_value"], "ГОСТ 33259-2015 (вх25)")
t("flange25: выход standard None (нет строки 25)",
  results_f4["Стандарт фланца на выходе"]["response_value"], None)
fout25 = computed_f4["_flange_outlet"]
t("flange25: давление выхода = 25 несмотря на отсутствие строки", fout25["давление"], 25)
t("flange25: стандарт выхода отсутствует в кэше", "стандарт" not in fout25, True)

print("=== Заполнение табличных параметров фланцев (_fill_flange_entries) ===")
flange_params = [
    {"name": "Давление", "table_name": FLANGE_IN_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Стандарт исполнения", "table_name": FLANGE_IN_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Фланец на входе", "table_name": FLANGE_IN_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Давление", "table_name": FLANGE_OUT_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Стандарт исполнения", "table_name": FLANGE_OUT_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Фланец на выходе", "table_name": FLANGE_OUT_TABLE, "response_value": None, "editable": True, "visibility": True},
    {"name": "Стандарт исполнения", "table_name": "other_flange", "response_value": "keep", "editable": True, "visibility": True},
    {"name": "Тип присоединения", "table_name": None, "response_value": "Под приварку", "editable": True, "visibility": True},
]
_fill_flange_entries(flange_params, computed_f)
byf = {(p["table_name"], p["name"]): p for p in flange_params}
t("fillf: давление входа=16", byf[(FLANGE_IN_TABLE, "Давление")]["response_value"], 16)
t("fillf: стандарт входа", byf[(FLANGE_IN_TABLE, "Стандарт исполнения")]["response_value"], "ГОСТ 33259-2015 (вх)")
t("fillf: фланец входа", byf[(FLANGE_IN_TABLE, "Фланец на входе")]["response_value"], "Фланец вх PN16")
t("fillf: давление выхода=16", byf[(FLANGE_OUT_TABLE, "Давление")]["response_value"], 16)
t("fillf: стандарт выхода", byf[(FLANGE_OUT_TABLE, "Стандарт исполнения")]["response_value"], "ГОСТ 33259-2015 (вых)")
t("fillf: давление нередактируемо", byf[(FLANGE_IN_TABLE, "Давление")]["editable"], False)
t("fillf: фланец редактируем", byf[(FLANGE_IN_TABLE, "Фланец на входе")]["editable"], True)
t("fillf: стандарт редактируем", byf[(FLANGE_IN_TABLE, "Стандарт исполнения")]["editable"], True)
t("fillf: видимость не меняется", byf[(FLANGE_IN_TABLE, "Фланец на входе")]["visibility"], True)
t("fillf: чужой Стандарт не тронут", byf[("other_flange", "Стандарт исполнения")]["response_value"], "keep")
t("fillf: Тип присоединения не тронут", byf[(None, "Тип присоединения")]["response_value"], "Под приварку")

# Пользователь выбрал «Фланец на входе» вручную — алгоритм не должен затирать.
flange_params_manual = [
    {"name": "Давление", "table_name": FLANGE_IN_TABLE, "response_value": None, "editable": True},
    {"name": "Стандарт исполнения", "table_name": FLANGE_IN_TABLE, "response_value": None, "editable": True},
    {"name": "Фланец на входе", "table_name": FLANGE_IN_TABLE, "response_value": None, "editable": True},
]
_run_sel = {
    "Давление вх": "16",
    "Стандарт исполнения": "ГОСТ 33259-2015 (вх)",
    "Фланец на входе": "Фланец вх PN16",
}
_fill_flange_entries(flange_params_manual, computed_f, _run_sel)
_byfm = {(p["table_name"], p["name"]): p for p in flange_params_manual}
t("fillf: ручн. давление не редактируемо", _byfm[(FLANGE_IN_TABLE, "Давление")]["editable"], False)
t("fillf: ручн. фланец редактируем", _byfm[(FLANGE_IN_TABLE, "Фланец на входе")]["editable"], True)

flange_params_manual2 = [
    {"name": "Давление", "table_name": FLANGE_OUT_TABLE, "response_value": None, "editable": True},
    {"name": "Стандарт исполнения", "table_name": FLANGE_OUT_TABLE, "response_value": None, "editable": True},
    {"name": "Фланец на выходе", "table_name": FLANGE_OUT_TABLE, "response_value": None, "editable": True},
]
_fill_flange_entries(flange_params_manual2, computed_f, {"Фланец на выходе": "СВОЁ ЗНАЧЕНИЕ"})
byfm2 = {(p["table_name"], p["name"]): p for p in flange_params_manual2}
t("fillf: ручн. фланец не затёрт", byfm2[(FLANGE_OUT_TABLE, "Фланец на выходе")]["response_value"], None)
t("fillf: стандарт при ручном фланце заполнен", byfm2[(FLANGE_OUT_TABLE, "Стандарт исполнения")]["response_value"], "ГОСТ 33259-2015 (вых)")

# Стабы для импорта module_search (тяжёлые зависимости: fastapi, TablePakage,
# TableSearch.utils и т.п. не нужны для _override_flange_filtered_values).
def _mkmod(name, **attrs):
    m = _t.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m

_mkmod("app.TablePakage.model.database", get_db=lambda *a, **k: None)
_mkmod("app.TablePakage.model.product_files",
       ProductFiles=type("ProductFiles", (), {"__init__": lambda self, **k: None}))
_mkmod("app.TableSearch.utils",
       ensure_dm_exists=lambda *a, **k: None,
       get_full_search_from_dm=lambda *a, **k: None,
       search_formula=lambda *a, **k: None)
_mkmod("app.TableSearch.utils.dm_search",
       ensure_dm_exists=lambda *a, **k: None,
       get_full_search_from_dm=lambda *a, **k: None)
_mkmod("app.TableSearch.utils.formula_search",
       search_formula=lambda *a, **k: None)
if "fastapi" not in sys.modules:
    class _FakeAPIRouter:
        def __init__(self, *a, **k):
            pass

        def post(self, *a, **k):
            return lambda f: f

    _mkmod("fastapi",
           APIRouter=_FakeAPIRouter,
           Depends=lambda *a, **k: None,
           Body=lambda *a, **k: None,
           HTTPException=Exception)

from app.TableSearch.router.module_search import _override_flange_filtered_values

override_info = [
    {"name": "Давление вх", "transliterated_name": "davlenie_vh", "table_name": FLANGE_IN_TABLE},
    {"name": "Стандарт исполнения вх", "transliterated_name": "standart_ispolnenija_vh", "table_name": FLANGE_IN_TABLE},
    {"name": "Фланец на входе", "transliterated_name": "flance_na_vhode", "table_name": FLANGE_IN_TABLE},
    {"name": "Давление вых", "transliterated_name": "davlenie_vyh", "table_name": FLANGE_OUT_TABLE},
    {"name": "Стандарт исполнения вых", "transliterated_name": "standart_ispolnenija_vyh", "table_name": FLANGE_OUT_TABLE},
    {"name": "Фланец на выходе", "transliterated_name": "flance_na_vyhode", "table_name": FLANGE_OUT_TABLE},
]
override_params = [
    {"name": "Давление вх", "table_name": FLANGE_IN_TABLE, "response_value": 16, "all_values": ["A"], "filtered_values": None},
    {"name": "Стандарт исполнения вх", "table_name": FLANGE_IN_TABLE, "response_value": None, "all_values": ["x"], "filtered_values": ["x"]},
    {"name": "Фланец на входе", "table_name": FLANGE_IN_TABLE, "response_value": None, "all_values": ["x"], "filtered_values": ["x"]},
    {"name": "Давление вых", "table_name": FLANGE_OUT_TABLE, "response_value": 16, "all_values": ["A"], "filtered_values": None},
    {"name": "Стандарт исполнения вых", "table_name": FLANGE_OUT_TABLE, "response_value": None, "all_values": ["x"], "filtered_values": ["x"]},
    {"name": "Фланец на выходе", "table_name": FLANGE_OUT_TABLE, "response_value": None, "all_values": ["x"], "filtered_values": ["x"]},
]
run(_override_flange_filtered_values(db, override_params, override_info))
byo = {(p["table_name"], p["name"]): p for p in override_params}
t("ovr: вх давление не тронут", byo[(FLANGE_IN_TABLE, "Давление вх")]["filtered_values"], None)
t("ovr: вх стандарт отфильтрован по PN 16", byo[(FLANGE_IN_TABLE, "Стандарт исполнения вх")]["filtered_values"], ["ГОСТ 33259-2015 (вх)"])
t("ovr: вх фланец PN 16", byo[(FLANGE_IN_TABLE, "Фланец на входе")]["all_values"], ["Фланец вх PN16"])
t("ovr: вых стандарт PN 16", byo[(FLANGE_OUT_TABLE, "Стандарт исполнения вых")]["filtered_values"], ["ГОСТ 33259-2015 (вых)"])
t("ovr: вых фланец PN 16", byo[(FLANGE_OUT_TABLE, "Фланец на выходе")]["all_values"], ["Фланец вых PN16"])

# Тест get_formula_driven_param_names: только «Давление» помечается driven
# для фланцевых таблиц.
from app.TableSearch.router.module_search import get_formula_driven_param_names
driven_result = run(get_formula_driven_param_names(db, product_id=1))
assert (FLANGE_IN_TABLE, "Давление вх") in driven_result, f"Давление вх should be driven: {driven_result}"
assert driven_result[(FLANGE_IN_TABLE, "Давление вх")] == "flange"
assert (FLANGE_IN_TABLE, "Стандарт исполнения вх") not in driven_result, f"Стандарт вх should NOT be driven: {driven_result}"
assert (FLANGE_IN_TABLE, "Фланец на входе") not in driven_result, f"Фланец вх should NOT be driven: {driven_result}"
assert (FLANGE_OUT_TABLE, "Давление вых") in driven_result, f"Давление вых should be driven: {driven_result}"
assert driven_result[(FLANGE_OUT_TABLE, "Давление вых")] == "flange"
assert (FLANGE_OUT_TABLE, "Стандарт исполнения вых") not in driven_result, f"Стандарт вых should NOT be driven: {driven_result}"
assert (FLANGE_OUT_TABLE, "Фланец на выходе") not in driven_result, f"Фланец вых should NOT be driven: {driven_result}"
t("driven: только давление помечено flange",
  sorted(k for k in driven_result if "flange" in k[0]),
  [(FLANGE_IN_TABLE, "Давление вх"), (FLANGE_OUT_TABLE, "Давление вых")])

# Без строки в таблице фланцев: «Давление» перезаписывается на PN,
# «Стандарт исполнения»/«Фланец» остаются старыми значениями.
flange_params_norow = [
    {"name": "Давление", "table_name": FLANGE_OUT_TABLE, "response_value": "OLD", "editable": True, "visibility": True},
    {"name": "Стандарт исполнения", "table_name": FLANGE_OUT_TABLE, "response_value": "OLDSTD", "editable": True, "visibility": True},
    {"name": "Фланец на выходе", "table_name": FLANGE_OUT_TABLE, "response_value": "OLDFL", "editable": True, "visibility": True},
]
_fill_flange_entries(flange_params_norow, computed_f4)
byf2 = {p["name"]: p for p in flange_params_norow}
t("fillf25: давление выхода перезаписано на 25", byf2["Давление"]["response_value"], 25)
t("fillf25: стандарт выхода НЕ затёрт (нет строки)", byf2["Стандарт исполнения"]["response_value"], "OLDSTD")
t("fillf25: фланец выхода НЕ затёрт (нет строки)", byf2["Фланец на выходе"]["response_value"], "OLDFL")
t("fillf25: давление нередактируемо", byf2["Давление"]["editable"], False)

print("=== Скрытие фланцевых таблиц по «Типу присоединения» ===")
vis_params = [
    {"name": "Давление", "table_name": FLANGE_IN_TABLE},
    {"name": "Стандарт исполнения", "table_name": FLANGE_IN_TABLE},
    {"name": "Фланец на входе", "table_name": FLANGE_IN_TABLE},
    {"name": "Стандарт исполнения", "table_name": FLANGE_OUT_TABLE},
    {"name": "Фланец на выходе", "table_name": FLANGE_OUT_TABLE},
    {"name": "Стандарт исполнения", "table_name": "other_flange"},
    {"name": "Тип клапана", "table_name": None},
]
filtered = run(_finalize_connection_visibility(
    db, list(vis_params), {"Тип присоединения": "Под приварку"}, 1
))
t("vis: Под приварку -> фланцевые таблицы скрыты", len(filtered), 2)
t("vis: остался чужой Стандарт", {p["name"] for p in filtered}, {"Стандарт исполнения", "Тип клапана"})
filtered2 = run(_finalize_connection_visibility(
    db, list(vis_params), {"Тип присоединения": "Фланцевое"}, 1
))
t("vis: Фланцевое -> всё остаётся", len(filtered2), len(vis_params))
filtered3 = run(_finalize_connection_visibility(db, list(vis_params), {}, 1))
t("vis: тип не выбран -> всё остаётся", len(filtered3), len(vis_params))

print("=== Сильфонное уплотнение (bellows_seal) ===")

def bellows(selected, extra_specs=()):
    return run(compute_formulas(
        db,
        list(extra_specs) + [{"name": "Сильфонное уплотнение", "formula_config": {"func": "bellows_seal"}}],
        selected,
        1,
    ))[0]["Сильфонное уплотнение"]["response_value"]

t("bells: пилотный -> Нет (без доп. параметров)",
  bellows({"Тип клапана": "Пилотный (П)"}), "Нет")

t("bells: пружинный 51ХФА + t130 -> Да",
  bellows({
      "Тип клапана": "Пружинный (В)",
      "Предварительный диаметр седла клапана": "30",
      "Предварительное номинальное давление": 16,
      "Температура рабочей среды (°C)": "130",
  }), "Да")

t("bells: пружинный 50ХФА + t200 -> ручной (None)",
  bellows({
      "Тип клапана": "Пружинный (В)",
      "Предварительный диаметр седла клапана": "45",
      "Предварительное номинальное давление": 16,
      "Температура рабочей среды (°C)": "200",
  }), None)

t("bells: пружинный 50ХФА + t300 -> Да",
  bellows({
      "Тип клапана": "Пружинный (В)",
      "Предварительный диаметр седла клапана": "45",
      "Предварительное номинальное давление": 16,
      "Температура рабочей среды (°C)": "300",
  }), "Да")

t("bells: другой тип + ручной выбор Да -> Да",
  bellows({"Тип клапана": "Тип A", "Сильфонное уплотнение": "Да"}), "Да")

t("bells: другой тип без выбора -> None",
  bellows({"Тип клапана": "Тип A"}), None)

t("bells: 51ХФА но t120 (не >) -> ручной (None)",
  bellows({
      "Тип клапана": "Пружинный (В)",
      "Предварительный диаметр седла клапана": "30",
      "Предварительное номинальное давление": 16,
      "Температура рабочей среды (°C)": "120",
  }), None)

# Зависимость от формулы PN (пружинный случай с полным пайплайном).
results_b, _ = run(compute_formulas(
    db,
    [
        {"name": "Предварительное номинальное давление", "formula_config": {"func": "nominal_pressure"}},
        {"name": "Выбор седла клапана", "formula_config": {"func": "valve_selection"}},
        {"name": "Сильфонное уплотнение", "formula_config": {"func": "bellows_seal"}},
    ],
    {
        "Материал": "25Л",
        "Температура рабочей среды (°C)": "130",
        "Давление настройки (МПа)": "5.0",
        "Тип клапана": "Пружинный (В)",
        "Предварительный диаметр седла клапана": "30",
    },
    1,
))
t("bells-dep: pn=16", results_b["Предварительное номинальное давление"]["response_value"], 16)
t("bells-dep: seat=40", results_b["Выбор седла клапана"]["response_value"], 40)
t("bells-dep: Да (из формулы PN)", results_b["Сильфонное уплотнение"]["response_value"], "Да")

print("=== Материал сильфона (bellows_material) ===")

def bellows_material_val(selected):
    return run(compute_formulas(
        db,
        [{"name": "Материал сильфона", "formula_config": {"func": "bellows_material"}}],
        selected,
        1,
    ))[0]["Материал сильфона"]["response_value"]

t("mat: Да -> 08Х18Н10Т", bellows_material_val({"Сильфонное уплотнение": "Да"}), "08Х18Н10Т")
t("mat: Нет -> —", bellows_material_val({"Сильфонное уплотнение": "Нет"}), "—")
t("mat: не выбрано -> Заполните", bellows_material_val({}), 'Заполните параметр "Сильфонное уплотнение"')

# Зависимость от формулы bellows_seal (пилотный -> Нет -> материал «—»).
results_m, _ = run(compute_formulas(
    db,
    [
        {"name": "Сильфонное уплотнение", "formula_config": {"func": "bellows_seal"}},
        {"name": "Материал сильфона", "formula_config": {"func": "bellows_material"}},
    ],
    {"Тип клапана": "Пилотный (П)"},
    1,
))
t("mat-dep: ждёт формулу Сильфонное уплотнение", results_m["Материал сильфона"]["response_value"], "—")

# Интеграция: select-варианты (values) попадают в all_values ответа.
from app.formulas.integration import _apply_new_formulas


class FakeParam:
    def __init__(self, name, sort=0):
        self.id = 0
        self.name = name
        self.description = None
        self.table_name = None
        self.visibility = True
        self.editable = True
        self.required_type = None
        self.special = None
        self.sort = sort


response_params_mat = []
run(_apply_new_formulas(
    db,
    response_params_mat,
    {"Тип клапана": "Пилотный (П)", "Сильфонное уплотнение": "Нет"},
    [{"param": FakeParam("Материал сильфона", 5), "name": "Материал сильфона",
      "formula_config": {"func": "bellows_material", "values": ["08Х18Н10Т", "—"]}}],
    1,
))
resp_mat = {p["name"]: p for p in response_params_mat}
t("mat-all: all_values из formula_config", resp_mat["Материал сильфона"]["all_values"], ["08Х18Н10Т", "—"])
t("mat-all: значение = — (Нет)", resp_mat["Материал сильфона"]["response_value"], "—")

print("=== Обязательные испытания (required_tests) ===")

def required_tests_val(selected):
    return run(compute_formulas(
        db,
        [{"name": "Обязательные испытания", "formula_config": {"func": "required_tests"}}],
        selected,
        1,
    ))[0]["Обязательные испытания"]["response_value"]

RESULTS_TEXT_H2S = (
    "По СТ ЦКБА 052-2008\n\n"
    "Испытания материала корпуса:\n"
    " 1) Хим. Состав \n"
    " 2) На растяжение при +20 град. С \n"
    " 3) KCU при -60 град. С \n"
    " 4) Твердость \n"
    " 5) Стойкость к МКК \n"
    " 6) ВИК \n"
    " 7) РК \n"
    " 8) Капиллярный контроль \n\n"
    "Испытания материала золотника и седла: \n"
    " 1) Хим. Состав \n"
    " 2) На растяжение при +20 град. С \n"
    " 3) Контроль неметаллических включений \n"
    " 4) Контроль макроструктуры \n"
    " 5) Твердость \n"
    " 6) Стойкость к МКК \n"
    " 7) ВИК \n"
    " 8) РК \n"
    " 9) Капиллярный контроль"
)
RESULTS_TEXT_CL2 = RESULTS_TEXT_H2S  # в ТЗ оба текста идентичны

# Среда не выбрана → «Не требуются».
t("req: среда не выбрана -> Не требуются", required_tests_val({}), "Не требуются")

# Единичная среда: сероводород.
t("req: сероводород", required_tests_val({"Название рабочей среды": "Сероводород"}), RESULTS_TEXT_H2S)

# Единичная среда: хлор.
t("req: хлор", required_tests_val({"Название рабочей среды": "Хлор"}), RESULTS_TEXT_CL2)

# Единичная среда: другая → «Не требуются».
t("req: вода -> Не требуются", required_tests_val({"Название рабочей среды": "Вода"}), "Не требуются")

# Смесь с сероводородом.
t("req: смесь с сероводородом",
  required_tests_val({
      "Смесь": True, "Тип смеси": "газовая",
      "Состав смеси": [{"Сероводород": 10}, {"Азот": 90}],
  }), RESULTS_TEXT_H2S)

# Смесь с хлором.
t("req: смесь с хлором",
  required_tests_val({
      "Смесь": True, "Тип смеси": "газовая",
      "Состав смеси": [{"Хлор": 5}, {"Азот": 95}],
  }), RESULTS_TEXT_CL2)

# Смесь без сероводорода/хлора → «Не требуются».
t("req: смесь без триггеров -> Не требуются",
  required_tests_val({
      "Смесь": True, "Тип смеси": "газовая",
      "Состав смеси": [{"Азот": 50}, {"Кислород": 50}],
  }), "Не требуются")

# Смесь: тип не выбран → MissingParamError → «Не требуются» (кэш по умолчанию).
t("req: смесь без типа -> Не требуются",
  required_tests_val({"Смесь": True}), "Не требуются")

# Смесь включена, тип не выбран, но единичная среда выбрана → среда не теряется.
t("req: смесь без типа, среда Сероводород -> текст",
  required_tests_val({"Смесь": True, "Название рабочей среды": "Сероводород"}),
  RESULTS_TEXT_H2S)

# Интеграция: all_values из formula_config["values"].
response_params_req = []
run(_apply_new_formulas(
    db,
    response_params_req,
    {"Название рабочей среды": "Сероводород"},
    [{"param": FakeParam("Обязательные испытания", 6), "name": "Обязательные испытания",
      "formula_config": {"func": "required_tests", "values": ["Не требуются", RESULTS_TEXT_H2S, RESULTS_TEXT_CL2]}}],
    1,
))
resp_req = {p["name"]: p for p in response_params_req}
t("req-all: all_values из formula_config",
  resp_req["Обязательные испытания"]["all_values"],
  ["Не требуются", RESULTS_TEXT_H2S, RESULTS_TEXT_CL2])
t("req-all: значение = сероводород",
  resp_req["Обязательные испытания"]["response_value"], RESULTS_TEXT_H2S)

# Значение «По способу сброса рабочей среды» (формула discharge_type) вычисляется
# раньше и не должно «перехватывать» поиск названия среды (в продукте 11 именно
# «По способу сброса рабочей среды» содержит в имени «рабочей среды»).
res_req_pollut, _ = run(compute_formulas(
    db,
    [
        {"name": "По способу сброса рабочей среды", "formula_config": {"func": "discharge_type"}},
        {"name": "Обязательные испытания", "formula_config": {"func": "required_tests"}},
    ],
    {"Название рабочей среды": "Сероводород"},
    1,
))
t("req: не мешает «По способу сброса рабочей среды»",
  res_req_pollut["Обязательные испытания"]["response_value"], RESULTS_TEXT_H2S)

print("=== Покраска (pokraska) ===")

PAINT_25L = [
    "Серый RAL7035 по технологической инструкции 38877941.25206.01013 АО \"НПО Регулятор\" ",
    "Серый RAL7035 cистема АКП С4 по № П2-05 ТИ-0002",
    "Красный RAL3020 по СТО Газпром 9.1-018-2012",
]
PAINT_20GL = [
    "Синий RAL5017 по технологической инструкции 38877941.25206.01013 АО \"НПО Регулятор\" ",
    "Синий RAL5017 система АКП С4 по № П2-05 ТИ-0002",
    "Красный RAL3020 по СТО Газпром 9.1-018-2012",
]
PAINT_OTHER = [
    "Голубой RAL5012 по технологической инструкции 38877941.25206.01013 АО \"НПО Регулятор\" ",
    "Голубой RAL5012 система АКП С4 по № П2-05 ТИ-0002",
    "Красный RAL3020 по СТО Газпром 9.1-018-2012",
]

def pokraska_compute(selected):
    return run(compute_formulas(
        db,
        [{"name": "Покраска", "formula_config": {"func": "pokraska"}}],
        selected,
        1,
    ))

res_p, computed_p = pokraska_compute({"Материал": "25Л"})
t("покр: 25Л -> первый Серый", res_p["Покраска"]["response_value"], PAINT_25L[0])
t("покр: 25Л -> все_values Серые", computed_p["_pokraska_values"], PAINT_25L)

res_p, computed_p = pokraska_compute({"Материал": "20ГЛ"})
t("покр: 20ГЛ -> первый Синий", res_p["Покраска"]["response_value"], PAINT_20GL[0])
t("покр: 20ГЛ -> все_values Синие", computed_p["_pokraska_values"], PAINT_20GL)

res_p, _ = pokraska_compute({"Материал": "12Х18Н10Т"})
t("покр: другой материал -> Голубой", res_p["Покраска"]["response_value"], PAINT_OTHER[0])

res_p, _ = pokraska_compute({"Материал": "25Л", "Материал пружины": "51ХФА"})
t("покр: «Материал пружины» не мешает -> Серый", res_p["Покраска"]["response_value"], PAINT_25L[0])

res_p, _ = pokraska_compute({"Материал": "25Л", "Сильфонное уплотнение": "Да"})
t("покр: «Сильфонное уплотнение» не мешает -> Серый", res_p["Покраска"]["response_value"], PAINT_25L[0])

# «Материал сильфона» (формула, считается раньше) не должен подменивать материал.
res_p, _ = run(compute_formulas(
    db,
    [
        {"name": "Материал сильфона", "formula_config": {"func": "bellows_material"}},
        {"name": "Покраска", "formula_config": {"func": "pokraska"}},
    ],
    {"Материал": "25Л", "Сильфонное уплотнение": "Да"},
    1,
))
t("покр: «Материал сильфона» не мешает -> Серый",
  res_p["Покраска"]["response_value"], PAINT_25L[0])

t("покр: материал не выбран -> Голубой",
  pokraska_compute({})[0]["Покраска"]["response_value"], PAINT_OTHER[0])

# Интеграция: динамический all_values попадает в response параметра.
response_params_pokr = []
run(_apply_new_formulas(
    db,
    response_params_pokr,
    {"Материал": "20ГЛ"},
    [{"param": FakeParam("Покраска", 7), "name": "Покраска",
      "formula_config": {"func": "pokraska", "values": PAINT_OTHER}}],
    1,
))
resp_pokr = {p["name"]: p for p in response_params_pokr}
t("покр-all: all_values перезаписан на Синие", resp_pokr["Покраска"]["all_values"], PAINT_20GL)
t("покр-all: значение = первый Синий", resp_pokr["Покраска"]["response_value"], PAINT_20GL[0])

print("=== Срок эксплуатации (service_life) ===")

def service_life_val(selected, specs=None):
    return run(compute_formulas(
        db,
        specs or [{"name": "Срок эксплуатации", "formula_config": {"func": "service_life"}}],
        selected,
        1,
    ))

# Ручное значение «Сильфонное уплотнение» = Да/Нет.
t("срок: сильфон Да -> 30 лет",
  service_life_val({"Сильфонное уплотнение": "Да"})[0]["Срок эксплуатации"]["response_value"],
  "30 лет")
t("срок: сильфон Нет -> 25 лет",
  service_life_val({"Сильфонное уплотнение": "Нет"})[0]["Срок эксплуатации"]["response_value"],
  "25 лет")
t("срок: сильфон не выбран -> 25 лет",
  service_life_val({})[0]["Срок эксплуатации"]["response_value"],
  "25 лет")

# Сильфон — формула bellows_seal (пилотный → Нет; ждёт на следующем проходе).
res_lf, _ = run(compute_formulas(
    db,
    [
        {"name": "Сильфонное уплотнение", "formula_config": {"func": "bellows_seal"}},
        {"name": "Срок эксплуатации", "formula_config": {"func": "service_life"}},
    ],
    {"Тип клапана": "Пилотный (П)"},
    1,
))
t("срок: формула bellows=Нет -> 25 лет",
  res_lf["Срок эксплуатации"]["response_value"], "25 лет")

res_lf, _ = run(compute_formulas(
    db,
    [
        {"name": "Сильфонное уплотнение", "formula_config": {"func": "bellows_seal"}},
        {"name": "Срок эксплуатации", "formula_config": {"func": "service_life"}},
    ],
    {
        "Тип клапана": "Пружинный (В)",
        "Предварительное номинальное давление": 16,
        "Предварительный диаметр седла клапана": "40",
        "Температура рабочей среды (°C)": "130",
    },
    1,
))
t("срок: формула bellows=Да -> 30 лет",
  res_lf["Срок эксплуатации"]["response_value"], "30 лет")

# Принудительный сброс (дисчарж «Открытого типа» перебивает сильфон на «Нет»).
res_lf, _ = run(compute_formulas(
    db,
    [
        {"name": "По способу сброса рабочей среды", "formula_config": {"func": "discharge_type"}},
        {"name": "Срок эксплуатации", "formula_config": {"func": "service_life"}},
    ],
    {
        "Сильфонное уплотнение": "Да",
        "Название рабочей среды": "Вода",
        "Тип клапана": "Пружинный (В)",
        "Предварительное номинальное давление": 16,
        "Предварительный диаметр седла клапана": "40",
        "Температура рабочей среды (°C)": "130",
    },
    1,
))
t("срок: override сброса на Нет -> 25 лет",
  res_lf["Срок эксплуатации"]["response_value"], "25 лет")

# Интеграция: статические values из formula_config.
response_params_lf = []
run(_apply_new_formulas(
    db,
    response_params_lf,
    {"Сильфонное уплотнение": "Да"},
    [{"param": FakeParam("Срок эксплуатации", 8), "name": "Срок эксплуатации",
      "formula_config": {"func": "service_life", "values": ["25 лет", "30 лет"]}}],
    1,
))
resp_lf = {p["name"]: p for p in response_params_lf}
t("срок-all: all_values из formula_config", resp_lf["Срок эксплуатации"]["all_values"], ["25 лет", "30 лет"])
t("срок-all: значение = 30 лет", resp_lf["Срок эксплуатации"]["response_value"], "30 лет")

print("=== По способу сброса рабочей среды (discharge_type) ===")

def discharge(selected):
    return run(compute_formulas(
        db,
        [
            {"name": "По способу сброса рабочей среды", "formula_config": {"func": "discharge_type"}},
            {"name": "Сильфонное уплотнение", "formula_config": {"func": "bellows_seal"}},
        ],
        selected,
        1,
    ))

SPRING_SPRING = {
    "Тип клапана": "Пружинный (В)",
    "Предварительный диаметр седла клапана": "30",
    "Предварительное номинальное давление": 16,
    "Температура рабочей среды (°C)": "130",
}

res_d, _ = discharge({**SPRING_SPRING, "Название рабочей среды": "Вода"})
t("disc: Вода + пр.режим -> Открытого типа",
  res_d["По способу сброса рабочей среды"]["response_value"], "Открытого типа")

res_d, computed_d = run(compute_formulas(
    db,
    [{"name": "По способу сброса рабочей среды", "formula_config": {"func": "discharge_type"}}],
    {**SPRING_SPRING, "Название рабочей среды": "Вода"}, 1,
))
t("disc: override установлен", computed_d.get("_bellows_override"), "Нет")

res_d, _ = discharge({**SPRING_SPRING, "Название рабочей среды": "Газ"})
t("disc: Газ -> Закрытого типа", res_d["По способу сброса рабочей среды"]["response_value"], "Закрытого типа")

res_d, _ = discharge({**SPRING_SPRING, "Название рабочей среды": "Вода", "Температура рабочей среды (°C)": "120"})
t("disc: 51ХФА при t120 -> Закрытого типа", res_d["По способу сброса рабочей среды"]["response_value"], "Закрытого типа")

res_d, _ = discharge({"Название рабочей среды": "Вода"})
t("disc: без Типа клапана -> Закрытого типа", res_d["По способу сброса рабочей среды"]["response_value"], "Закрытого типа")

res_d, _ = discharge(dict(SPRING_SPRING))
t("disc: без среды -> Закрытого типа", res_d["По способу сброса рабочей среды"]["response_value"], "Закрытого типа")

res_d, _ = discharge({
    **SPRING_SPRING,
    "Смесь": True,
    "Тип смеси": "газовая",
    "Состав смеси": [{"Вода": 50}, {"Азот": 50}],
})
t("disc: смесь из неагрессивных -> Открытого типа", res_d["По способу сброса рабочей среды"]["response_value"], "Открытого типа")

res_d, _ = discharge({
    **SPRING_SPRING,
    "Смесь": True,
    "Тип смеси": "газовая",
    "Состав смеси": [{"Вода": 50}, {"Газ": 50}],
})
t("disc: смесь с Газ -> Закрытого типа", res_d["По способу сброса рабочей среды"]["response_value"], "Закрытого типа")

# Полный пайплайн: PN формулой, discharge ждёт подбор → Открытого типа,
# Сильфонное уплотнение принудительно «Нет» (перебивается интеграцией).
def big_discharge_specs():
    return [
        {"param": FakeParam("Предварительное номинальное давление", 1), "name": "Предварительное номинальное давление",
         "formula_config": {"func": "nominal_pressure"}},
        {"param": FakeParam("Выбор седла клапана", 2), "name": "Выбор седла клапана",
         "formula_config": {"func": "valve_selection"}},
        {"param": FakeParam("Сильфонное уплотнение", 3), "name": "Сильфонное уплотнение",
         "formula_config": {"func": "bellows_seal"}},
        {"param": FakeParam("По способу сброса рабочей среды", 4), "name": "По способу сброса рабочей среды",
         "formula_config": {"func": "discharge_type", "values": ["Открытого типа", "Закрытого типа"]}},
    ]


response_params = []
run(_apply_new_formulas(
    db,
    response_params,
    {
        "Материал": "25Л",
        "Температура рабочей среды (°C)": "130",
        "Давление настройки (МПа)": "5.0",
        "Название рабочей среды": "Вода",
        "Тип клапана": "Пружинный (В)",
        "Предварительный диаметр седла клапана": "30",
    },
    big_discharge_specs(),
    1,
))
resp = {p["name"]: p["response_value"] for p in response_params}
t("dislpay: pn=16", resp["Предварительное номинальное давление"], 16)
t("dislpay: seat=40", resp["Выбор седла клапана"], 40)
t("dislpay: Открытого типа", resp["По способу сброса рабочей среды"], "Открытого типа")
t("dislpay: Сильфонное уплотнение перебито на Нет", resp["Сильфонное уплотнение"], "Нет")
t("dislpay: all_values заданы", next(p["all_values"] for p in response_params if p["name"] == "По способу сброса рабочей среды"), ["Открытого типа", "Закрытого типа"])

print("ALL OK" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
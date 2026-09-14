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
        if "type = 'FormulaMix'" in sql_text:
            return Result([Row({"name": "Состав смеси"})])
        if "transliterated_name = :col" in sql_text or "transliterated_name = '" in sql_text:
            col = params.get("col")
            if col == "material":
                return Result([Row({"table_name": PRESSURE_TABLE})])
            if col == "tip_pk":
                return Result([Row({"table_name": VALVE_TABLE})])
            return Result([Row({"table_name": PRESSURE_TABLE})])
        if "information_schema.columns" in sql_text:
            return Result([Row({"column_name": c}) for c in ALL_COLUMNS])
        if "SELECT name, transliterated_name, table_name" in sql_text:
            return Result(_rows_from_dicts(
                MEDIA_SCHEMA_ROWS + PRESSURE_SCHEMA_ROWS + VALVE_SCHEMA_ROWS
            ))
        if "SELECT name, transliterated_name" in sql_text:
            return Result(_rows_from_dicts(MEDIA_SCHEMA_ROWS))
        if "SELECT table_name" in sql_text:
            return Result(["media"])
        if "SELECT DISTINCT" in sql_text:
            return Result([Row({"nazvanie_rabochej_sredy": "Газ", "agregatnoe_sostojanie": "Газ"})])
        if "SELECT name FROM parameter_schemas" in sql_text:
            return Result([])
        if "FROM \"" in sql_text:
            if ":tp" in sql_text:
                tp = params.get("tp")
                return Result([Row(d) for d in VALVE_ROWS if d["tip_pk"] == tp])
            if ":mat" in sql_text:
                mat = params.get("mat")
                return Result([Row(d) for d in PRESSURE_ROWS if d["material"] == mat])
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
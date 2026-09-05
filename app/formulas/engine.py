"""
Ядро новой системы расчёта формул.

FormulaContext — контекст, через который функции расчёта и валидации получают
значения других параметров. `ctx.get("Параметр")` ТРЕБУЕТ значение: если параметр
не выбран, поднимается MissingParamError, а движок превращает его в сообщение
«Заполните параметр "..."».

compute_formulas — асинхронный решатель зависимостей: формулы, не зависящие друг
от друга, считаются параллельно (asyncio.gather); зависимые — на следующих
проходах.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Optional


class MissingParamError(Exception):
    """Поднимается, когда запрошен требуемый параметр, значение которого не выбрано."""

    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f'Не заполнен параметр "{param_name}"')


def _coerce(value: Any) -> Any:
    """Приводит «сырые» значения (в основном строки из запроса) к естественному виду."""
    if isinstance(value, str):
        text = value.strip()
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return float(text)
        except ValueError:
            pass
        return value
    return value


class FormulaContext:
    """
    Контекст доступа к значениям параметров внутри функций расчёта/валидации.

    - `get(name)`      — требует значение; иначе MissingParamError.
    - `get_opt(name)`  — возвращает None, если параметр не выбран.
    - `num(name)`      — как `get`, но приводит результат к float.
    """

    def __init__(
        self,
        selected: dict[str, Any],
        computed: dict[str, Any],
        db: Any = None,
        product_id: Optional[int] = None,
    ):
        # Значения входных/табличных параметров (из запроса пользователя).
        self.selected = selected
        # Кэш значений уже вычисленных формульных параметров.
        self.computed = computed
        # Опционально: сессия БД (для функций, которым нужны данные из БД).
        self.db = db
        # Опционально: идентификатор продукта (для запросов к файлам/чертежам).
        self.product_id = product_id

    # ---- внутренние помощники ----

    def _lookup(self, name: str) -> Any:
        """Возвращает значение или None, если оно не выбрано."""
        if name in self.computed and self.computed[name] is not None:
            return self.computed[name]

        raw = self.selected.get(name)
        if raw is None:
            return None
        if isinstance(raw, str) and not raw.strip():
            return None
        return raw

    # ---- публичный API ----

    def get(self, name: str) -> Any:
        """Возвращает значение параметра; если не выбрано — поднимает MissingParamError."""
        value = self._lookup(name)
        if value is None:
            raise MissingParamError(name)
        return _coerce(value)

    def get_opt(self, name: str) -> Optional[Any]:
        """Возвращает значение параметра или None, если он не выбран."""
        try:
            return self.get(name)
        except MissingParamError:
            return None

    def num(self, name: str) -> float:
        """Требует значение и приводит его к float."""
        return float(self.get(name))

    def require(self, name: str) -> Any:
        """Алиас для `get`."""
        return self.get(name)


def _message_for_missing(param_name: str) -> str:
    return f'Заполните параметр "{param_name}"'


async def _attempt(
    spec: dict,
    ctx: FormulaContext,
    formula_names: set[str],
):
    """
    Пытается вычислить один формульный параметр.

    Возвращает кортеж (status, ...):
      ("ok", value, error)
      ("missing_input", param_name)     — не хватает входного/табличного параметра
      ("missing_formula", param_name)   — не хватает результата другой формулы
      ("error", None, message)          — неизвестная функция / исключение
    """
    config = spec.get("formula_config") or {}
    func_name = config.get("func")

    # Ленивый импорт реестра — чтобы избежать циклических импортов.
    from .registry import UnknownAlgorithmError, get_algorithm, get_validator

    try:
        func = get_algorithm(func_name)
    except UnknownAlgorithmError as exc:
        return ("error", None, str(exc))

    try:
        value = func(ctx)
        # Алгоритм может быть асинхронным (например, если ему нужны данные из БД).
        if inspect.isawaitable(value):
            value = await value
    except MissingParamError as exc:
        if exc.param_name in formula_names:
            return ("missing_formula", exc.param_name)
        return ("missing_input", exc.param_name)
    except Exception as exc:  # noqa: BLE001 — любая ошибка внутри алгоритма
        return ("error", None, f'Ошибка расчёта параметра "{spec.get("name")}": {exc}')

    # Валидация результата (если задана).
    error = None
    validate_name = config.get("validate")
    if validate_name:
        validator = get_validator(validate_name)
        if validator is None:
            error = f'Неизвестная функция валидации "{validate_name}"'
        else:
            try:
                validate_error = validator(ctx, value)
                if validate_error:
                    error = str(validate_error)
            except MissingParamError as exc:
                if exc.param_name in formula_names:
                    return ("missing_formula", exc.param_name)
                return ("missing_input", exc.param_name)
            except Exception as exc:  # noqa: BLE001
                error = f'Ошибка валидации параметра "{spec.get("name")}": {exc}'

    return ("ok", value, error)


async def compute_formulas(
    db: Any,
    formula_params: list[dict],
    selected: dict[str, Any],
    product_id: Optional[int] = None,
) -> dict[str, dict]:
    """
    Вычисляет все новые формульные параметры.

    Аргументы:
        db — сессия БД (передаётся в контекст, может быть None).
        formula_params — список dict вида
            {"id": ..., "name": ..., "formula_config": {...}}
        selected — словарь выбранных значений: {имя_параметра: значение}.

    Возвращает:
        dict {имя_параметра: {"response_value": ..., "error": ... | None}}
    """
    formula_names = {
        spec["name"] for spec in formula_params
        if spec.get("name")
    }

    results: dict[str, dict] = {}
    computed: dict[str, Any] = {}
    ctx = FormulaContext(selected, computed, db=db, product_id=product_id)

    pending = [spec for spec in formula_params if (spec.get("formula_config") or {}).get("func")]
    max_passes = len(pending) + 5

    passes = 0
    while pending and passes < max_passes:
        passes += 1

        tasks = [_attempt(spec, ctx, formula_names) for spec in pending]
        outcomes = await asyncio.gather(*tasks)

        next_pending: list[dict] = []
        progress = False

        for spec, outcome in zip(pending, outcomes):
            status = outcome[0]
            name = spec["name"]

            if status == "ok":
                value, error = outcome[1], outcome[2]
                computed[name] = value
                entry = {"response_value": value}
                if error:
                    entry["error"] = error
                results[name] = entry
                progress = True
                continue

            if status == "missing_input":
                missing_name = outcome[1]
                # Терминально: не хватает входного параметра.
                results[name] = {
                    "response_value": _message_for_missing(missing_name),
                }
                continue

            if status == "missing_formula":
                # Зависимость от другой формулы — откладываем на следующий проход.
                next_pending.append(spec)
                continue

            # status == "error"
            results[name] = {"error": outcome[2]}

        if not next_pending:
            break

        # Защита от циклических зависимостей: если за проход ничего не решилось
        # и всё осталось в очереди — значит есть цикл либо все ждут друг друга.
        if not progress:
            for spec in next_pending:
                name = spec["name"]
                if name not in results:
                    results[name] = {
                        "error": f'Обнаружена циклическая зависимость для параметра "{name}"',
                    }
            break

        pending = next_pending

    # На случай выхода по лимиту проходов.
    for spec in pending:
        name = spec["name"]
        if name not in results:
            results[name] = {"error": "Не удалось вычислить параметр (возможна циклическая зависимость)"}

    return results
"""
Реестры функций расчёта и валидации.

Реестры строятся автоматически из содержимого модулей `algorithms` и
`validators`: собираются все вызываемые объекты, не начинающиеся с `_`.
Имя функции из БД сверяется с реестром — это исключает вызов произвольного кода
по строковому имени (безопасность).
"""

from __future__ import annotations

from typing import Any, Callable

from . import algorithms, validators


class UnknownAlgorithmError(Exception):
    """Поднимается, когда имя функции расчёта не найдено в реестре."""


def _collect(module: Any) -> dict[str, Callable]:
    return {
        name: fn
        for name, fn in vars(module).items()
        if callable(fn)
        and not name.startswith("_")
        # Исключаем импортированные объекты (например FormulaContext),
        # оставляем только функции, объявленные в этом модуле.
        and getattr(fn, "__module__", None) == module.__name__
    }


# Имена функций расчёта -> функции.
ALGORITHMS: dict[str, Callable] = _collect(algorithms)

# Имена функций валидации -> функции.
VALIDATORS: dict[str, Callable] = _collect(validators)


def get_algorithm(name: str) -> Callable:
    """Возвращает функцию расчёта по имени или поднимает UnknownAlgorithmError."""
    fn = ALGORITHMS.get(name)
    if fn is None:
        raise UnknownAlgorithmError(f'Неизвестная функция расчёта "{name}"')
    return fn


def get_validator(name: str) -> Callable | None:
    """Возвращает функцию валидации по имени или None."""
    return VALIDATORS.get(name)
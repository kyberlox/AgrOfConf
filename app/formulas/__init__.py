"""
Новая система расчёта формул.

Алгоритмы и валидаторы — обычные Python-функции в файлах `algorithms.py` и
`validators.py`. Привязка параметра к функциям хранится в JSON-поле
`formula_config` модели `ParameterSchema`.

Публичное API:
    compute_formulas(db, formula_params, selected) -> dict[name, {response_value|error}]
    FormulaContext            - контекст доступа к значениям внутри функций
    MissingParamError         - поднимается, когда требуемый параметр не выбран
    ALGORITHMS / VALIDATORS   - реестры имён функций
"""

from .engine import (
    FormulaContext,
    MissingParamError,
    compute_formulas,
)
from .registry import (
    ALGORITHMS,
    VALIDATORS,
    UnknownAlgorithmError,
    get_algorithm,
    get_validator,
)

__all__ = [
    "FormulaContext",
    "MissingParamError",
    "compute_formulas",
    "ALGORITHMS",
    "VALIDATORS",
    "UnknownAlgorithmError",
    "get_algorithm",
    "get_validator",
]
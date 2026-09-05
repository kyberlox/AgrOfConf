"""
Эндпоинты для работы с реестром формул.

Позволяют админ-интерфейсу получать список доступных функций расчёта и
валидации, чтобы исключить опечатки при указании имени функции у параметра.
"""

from fastapi import APIRouter

from .registry import ALGORITHMS, VALIDATORS

router = APIRouter(prefix="/formula_functions", tags=["Formula functions"])


@router.get("")
async def get_formula_functions():
    """Возвращает списки доступных функций расчёта и валидации."""
    return {
        "algorithms": sorted(ALGORITHMS.keys()),
        "validators": sorted(VALIDATORS.keys()),
    }
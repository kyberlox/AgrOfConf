"""
Хранилище VALIDATION-промтов продуктов и правил постановки значений по умолчанию.

- Промт хранится в текстовом файле на диске — `static/product_prompts/{product_id}.md`,
  по одному файлу на продукт. Файлы на диске выбраны вместо TEXT-колонки в PSQL,
  чтобы промт мог быть сколь угодно большим и не гонять лишние данные через ORM.
- RULES_TABLE (правила дефолтных значений) хранятся в JSON-файле `rules_table.json`,
  лежащем в той же директории, что и этот модуль (app/TableSearch/utils/).
  Структура файла: `{product_id: [{name, default}, ...]}`.

Если файла промта для продукта нет — используется общий VALIDATION_PROMPT из promt_ol.py.
Если в rules_table.json нет правил для продукта — возвращается пустой список.
При первом обращении файл инициализируется дефолтами из promt_ol.py.
"""
import json
import os
from pathlib import Path

from .promt_ol import RULES_TABLE as DEFAULT_RULES_TABLE

PROMPT_DIR = "./static/product_prompts"
os.makedirs(PROMPT_DIR, exist_ok=True)

# rules_table.json лежит рядом с этим модулем: app/TableSearch/utils/rules_table.json
RULES_FILE = Path(__file__).resolve().parent / "rules_table.json"


def _prompt_path(product_id: int) -> Path:
    return Path(PROMPT_DIR) / f"{product_id}.md"


def has_product_validation_prompt(product_id: int) -> bool:
    """Проверяет, сохранён ли для продукта свой VALIDATION-промт."""
    return _prompt_path(product_id).exists()


def get_product_validation_prompt(product_id: int) -> str:
    """Возвращает VALIDATION-промт продукта, либо стандартный, если свой не задан."""
    path = _prompt_path(product_id)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "" #VALIDATION_PROMPT


def save_product_validation_prompt(product_id: int, prompt: str) -> str:
    """Сохраняет VALIDATION-промт продукта на диск. Возвращает сохранённый текст."""
    prompt = prompt or ""
    path = _prompt_path(product_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt, encoding="utf-8")
    return prompt


def delete_product_validation_prompt(product_id: int) -> bool:
    """Удаляет VALIDATION-промт продукта. False, если файла не было."""
    path = _prompt_path(product_id)
    if path.exists():
        path.unlink()
        return True
    return False

def _load_rules() -> dict:
    """Загружает правила из rules_table.json.

    - Если файла нет или он пуст/битый — инициализируется дефолтами из promt_ol.py.
    """
    if RULES_FILE.exists():
        try:
            data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass

    # Инициализация файла дефолтными правилами (source of truth — промт-модуль).
    data = {str(key): value for key, value in DEFAULT_RULES_TABLE.items()}
    _save_rules(data)
    return data



def _save_rules(data: dict) -> None:
    """Записывает словарь правил в rules_table.json."""
    RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_product_rules(rules: list[dict], product_id: int) -> list[dict]:
    """
    Сохраняет правила постановки значений по умолчанию для продукта в файл rules_table.json.
    Формат: [{'name': ..., 'default': ...}, ...]

    Ключ всегда сохраняется как строка (JSON хранит только строковые ключи),
    поэтому повторное сохранение того же product_id перезаписывает, а не дублирует.
    """
    normalized = [
        r.model_dump() if hasattr(r, "model_dump") else r
        for r in rules
    ]
    data = _load_rules()
    key = str(product_id)
    data[key] = normalized
    _save_rules(data)
    return data[key]


def get_product_rules(product_id: int) -> list[dict]:
    """Возвращает правила постановки значений по умолчанию для продукта из файла rules_table.json.

    Ищет ключ и как int (на случай старых записей), и как str (формат JSON).
    """
    data = _load_rules()
    return data.get(product_id, data.get(str(product_id), []))

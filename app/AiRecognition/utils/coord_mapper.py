"""
Сопоставление строк Markdown-таблицы (ответ LLM) с боксами OCR-слов.

Роль в гибридной архитектуре:
- LLM возвращает только структуру (| ID | Параметр | Значение |);
- этот модуль находит для каждой строки координаты ЗНАЧЕНИЯ в пикселях,
  используя словоуровневые боксы локального OCR;
- результат — список ``positions`` в формате старого API
  (``{id, coord: {top,left,bottom,right}, file_index}``), поэтому фронтенд
  продолжает работать без изменений.

Логика:
1. Парсим markdown-строки таблицы (regex по ``| ID | Параметр | Значение |``).
2. Нормализуем текст значения (регистр, пробелы, запятые/точки, тире).
3. Ищем слова OCR на той же странице, чей текст пересекается со значением
   (подстрока в обе стороны) либо численно эквивалентен.
4. Объединяем найденные боксы в один охватывающий прямоугольник.
5. Фолбэк: если точное совпадение не найдено — берём ближайшую строку
   транскрипта по вертикали; если и она не подходит — позиция пропускается,
   но строка таблицы остаётся (координаты не критичны для создания ОЛ).
"""
import difflib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .ocr_engine import TextLine, WordBox, get_ocr_engine


# ---------------------------------------------------------------------------
# Парсинг таблицы
# ---------------------------------------------------------------------------

@dataclass
class TableRow:
    id: int
    parameter: str
    value: str


# | 5 | Давление (избыточное) | |
# | 6 | - Рабочее | 1.6, МПа |
_ROW_RE = re.compile(
    r"^\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|?\s*$"
)


def parse_markdown_table(md: str) -> List[TableRow]:
    """Извлекает строки | ID | Параметр | Значение | из markdown."""
    rows: List[TableRow] = []
    for line in md.splitlines():
        m = _ROW_RE.match(line)
        if not m:
            continue
        row_id = int(m.group(1))
        parameter = m.group(2).strip()
        value = m.group(3).strip()
        # Строка-разделитель |---|---| не попадает (там нет числа в 1-й колонке)
        rows.append(TableRow(id=row_id, parameter=parameter, value=value))
    return rows


# ---------------------------------------------------------------------------
# Нормализация текста
# ---------------------------------------------------------------------------

_TRANSLIT = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X",
}


def _normalize(text: str) -> str:
    """Нормализация для сравнения: нижний регистр, без пунктуации/пробелов,
    запятая→точка, кириллические омонимы латиницы → латиница.

    ВАЖНО: убираем ВСЮ пунктуацию, включая скобки, двоеточия и слэши —
    иначе ``"Давление (избыточное)"`` не матчится с OCR ``"Давление
    избыточное"`` (главная причина массовых пропусков позиций).
    """
    t = text.strip().lower()
    # Кириллица, похожая на латиницу (частые ошибки OCR): приводим к латинице
    for ru, en in _TRANSLIT.items():
        t = t.replace(ru.lower(), en)
    t = t.replace(",", ".")
    # Убираем пробелы, скобки, двоеточия, слэши, тире и прочую пунктуацию
    t = re.sub(r"[\s\u00a0()\[\]{}<>:;'\"«»…—–_\\/-]", "", t)
    return t


def _tokens(text: str) -> List[str]:
    """Разбивает текст на значимые токены (буквы/цифры), без пунктуации."""
    t = text.strip().lower()
    for ru, en in _TRANSLIT.items():
        t = t.replace(ru.lower(), en)
    t = re.sub(r"[^a-zа-яё0-9]", " ", t)
    return [tok for tok in t.split() if tok]


def _extract_number(text: str) -> Optional[float]:
    """Первое число из строки (для числовой эквивалентности)."""
    m = re.search(r"-?\d+(?:[.,]\d+)?", text)
    if not m:
        return None
    try:
        return float(m.group().replace(",", "."))
    except ValueError:
        return None


def _num_key(text: str) -> Optional[str]:
    """Числовой токен с СОХРАНЕНИЕМ десятичной точки.

    Нужен для строгого сравнения чисел: ``"1,6" -> "1.6"``, но
    ``"16" != "1.6"`` (иначе любое число на странице матчится с
    дробным значением — главная причина «расползания» боксов).
    """
    m = re.search(r"\d+(?:[.,]\d+)?", text)
    if not m:
        return None
    return m.group().replace(",", ".")


def _word_matches(word_text: str, value_text: str) -> bool:
    """Проверяет, соответствует ли слово OCR значению таблицы.

    Порядок проверок (от строгой к мягкой):
    1. Точное равенство нормализованных строк;
    2. Числовое равенство через ``_num_key`` ("1,6" == "1.6",
       но "16" != "1.6" и "6" != "1.6");
    3. Вхождение подстроки — только для текстовых (нечисловых)
       значений, длина >= 3 символов.
    """
    wn = _normalize(word_text)
    vn = _normalize(value_text)
    if not wn or not vn:
        return False
    if wn == vn:
        return True

    wkey = _num_key(word_text)
    vkey = _num_key(value_text)
    if wkey is not None and vkey is not None:
        # Оба содержат число — сравниваем строго, без подстрок.
        return wkey == vkey

    # Текстовое сопоставление по подстроке (единицы измерения и т.п.)
    if len(vn) >= 3 and (vn in wn or wn in vn):
        return True
    # Лёгкое fuzzy-совпадение (опечатки OCR: «МПа» vs «Мпа» и т.п.)
    if len(vn) >= 3 and difflib.SequenceMatcher(None, vn, wn).ratio() >= 0.85:
        return True
    return False


def _param_matches(text: str, param_text: str) -> bool:
    """Соответствие строки транскрипта названию параметра (якорь поиска).

    Устойчив к:
    - разнице в пунктуации (скобки/двоеточия — см. ``_normalize``);
    - пересказу/перестановке слов (токенный набор);
    - опечаткам OCR (fuzzy ≥ 0.85).
    """
    tn = _normalize(text)
    pn = _normalize(param_text)
    if not tn or not pn:
        return False
    if tn == pn:
        return True
    if len(pn) >= 3 and (pn in tn or tn in pn):
        return True

    # Токены: все значимые слова короткой стороны есть в длинной
    tt = _tokens(text)
    pt = _tokens(param_text)
    if tt and pt:
        short, long_ = (pt, tt) if len(pt) <= len(tt) else (tt, pt)
        if all(tok in long_ for tok in short):
            return True

    # Fuzzy по компактной строке (опечатки OCR)
    if len(pn) >= 4 and difflib.SequenceMatcher(None, pn, tn).ratio() >= 0.85:
        return True
    return False


# ---------------------------------------------------------------------------
# Поиск боксов
# ---------------------------------------------------------------------------

@dataclass
class Coord:
    top: int
    left: int
    bottom: int
    right: int


@dataclass
class Position:
    id: int
    coord: Coord
    file_index: int


def _line_matches(line: TextLine, value_text: str) -> bool:
    """Проверяет, содержит ли строка транскрипта искомое значение."""
    vn = _normalize(value_text)
    ln = _normalize(line.text)
    if not vn or not ln:
        return False
    if vn in ln or ln in vn:
        return True
    lnum = _extract_number(ln)
    vnum = _extract_number(vn)
    if lnum is not None and vnum is not None and lnum == vnum:
        return True
    return False


def find_words_for_value(words: List[WordBox], value_text: str) -> List[WordBox]:
    """Возвращает слова OCR, соответствующие значению таблицы."""
    value_clean = value_text.strip()
    if not value_clean or value_clean in {"-", "—"}:
        return []
    matched: List[WordBox] = []
    for w in words:
        if _word_matches(w.text, value_clean):
            matched.append(w)
    return matched


def _merge_boxes(words: List[WordBox]) -> Optional[Coord]:
    """Объединяет боксы слов в охватывающий прямоугольник (целые px)."""
    if not words:
        return None
    return Coord(
        top=int(min(w.y1 for w in words)),
        left=int(min(w.x1 for w in words)),
        bottom=int(max(w.y2 for w in words)),
        right=int(max(w.x2 for w in words)),
    )


def _tight_merge(words: List[WordBox], anchor_x: float = 0.0) -> Optional[Coord]:
    """Объединяет только ГОРИЗОНТАЛЬНО СМЕЖНЫЕ слова значения.

    Значение может встречаться в строке несколько раз (повторы единиц,
    одинаковые числа в соседних ячейках). Слова разбиваются на группы по
    разрыву между ними, берётся группа, ближайшая к ``anchor_x`` (обычно
    правый край названия параметра). Это исключает «расползание» бокса
    на всю страницу/строку.
    """
    if not words:
        return None
    ws = sorted(words, key=lambda w: w.x1)
    groups: List[List[WordBox]] = []
    cur = [ws[0]]
    for w in ws[1:]:
        prev = cur[-1]
        h = max(1.0, (prev.y2 - prev.y1 + w.y2 - w.y1) / 2)
        if w.x1 - prev.x2 <= h * 2.0:
            cur.append(w)
        else:
            groups.append(cur)
            cur = [w]
    groups.append(cur)

    def dist(g: List[WordBox]) -> float:
        cx = (min(x.x1 for x in g) + max(x.x2 for x in g)) / 2
        return abs(cx - anchor_x)

    best = min(groups, key=lambda g: (dist(g), len(g)))
    return _merge_boxes(best)


def _find_value_coord(
    lines: List[TextLine],
    param_line: TextLine,
    value_text: str,
) -> Optional[Coord]:
    """Ищет координаты значения ВБЛИЗИ строки параметра.

    Сначала — слова значения в самой строке параметра (обычно справа от
    названия), затем — в соседних строках в пределах вертикальной полосы
    (многострочные ячейки). Бокс строится ТОЛЬКО из слов значения
    (``_tight_merge``), а не из всей строки транскрипта.
    """
    if not value_text.strip() or value_text.strip() in {"-", "—"}:
        return None
    line_h = max(1.0, param_line.y2 - param_line.y1)
    band = max(line_h * 4.0, 40.0)  # допуск на многострочные ячейки
    param_cx = (param_line.x1 + param_line.x2) / 2

    candidates: List[Coord] = []
    for line in lines:
        if abs((line.y1 + line.y2) / 2 - (param_line.y1 + param_line.y2) / 2) > band:
            continue
        val_words = [w for w in line.words if _word_matches(w.text, value_text)]
        if not val_words:
            continue
        coord = _tight_merge(val_words, anchor_x=param_line.x2)
        if coord is not None:
            candidates.append(coord)

    if not candidates:
        return None
    # Ближайшая к параметру кандидатура: по вертикали, затем по горизонтали
    candidates.sort(key=lambda c: (abs(c.top - param_line.y1), abs(c.left - param_cx)))
    return candidates[0]


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def build_positions(
    md_table: str,
    pages_words: List[List[WordBox]],
    lines_by_page: Optional[Dict[int, List[TextLine]]] = None,
) -> List[Position]:
    """Сопоставляет строки таблицы с боксами OCR и возвращает positions.

    Стратегия (привязка к месту, а не к тексту по всей странице):

    1. Для каждой строки ``| ID | Параметр | Значение |`` сначала ищем
       строку транскрипта, содержащую НАЗВАНИЕ параметра (якорь);
    2. Рядом с якорем (в той же строке или в соседних в пределах полосы)
       ищем слова, соответствующие ЗНАЧЕНИЮ;
    3. Бокс строится из слов значения через ``_tight_merge`` — только
       смежные слова, без «расползания» на всю страницу/строку;
    4. Фолбэк (параметр не найден): строка с значением, но бокс всё равно
       ограничивается словами значения, а не всей строкой.

    :param md_table: markdown-таблица (ответ LLM);
    :param pages_words: список списков WordBox по страницам;
    :param lines_by_page: опционально — уже собранные строки транскрипта
        по страницам (ускоряет работу);
    """
    rows = parse_markdown_table(md_table)
    if not rows:
        return []

    # Слова по страницам
    words_by_page: Dict[int, List[WordBox]] = {}
    for page_words in pages_words:
        if page_words:
            words_by_page.setdefault(page_words[0].page_index, []).extend(page_words)

    # Строки транскрипта по страницам
    if lines_by_page is None:
        lines_by_page = {}
        engine = get_ocr_engine()
        for page_words in pages_words:
            if page_words:
                lines_by_page.setdefault(page_words[0].page_index, []).extend(
                    engine.cluster_into_lines(page_words)
                )

    positions: List[Position] = []
    for row in rows:
        best: Optional[Tuple[Coord, int]] = None   # (coord, file_index)
        param_line_found: Optional[Tuple[TextLine, int]] = None

        # 1) Основной путь: строка параметра → значение рядом с ней
        for file_index in sorted(words_by_page):
            lines = lines_by_page.get(file_index, [])
            param_lines = [l for l in lines if _param_matches(l.text, row.parameter)]
            if not param_lines:
                continue
            for pl in sorted(param_lines, key=lambda l: l.y1):
                if param_line_found is None:
                    param_line_found = (pl, file_index)
                coord = _find_value_coord(lines, pl, row.value)
                if coord is not None:
                    best = (coord, file_index)
                    break
            if best is not None:
                break

        # 2) Фолбэк: строка с значением в любом месте документа
        if best is None and row.value.strip() and row.value.strip() not in {"-", "—"}:
            for file_index in sorted(words_by_page):
                lines = lines_by_page.get(file_index, [])
                cand: Optional[Tuple[Coord, int]] = None
                for line in lines:
                    if not _line_matches(line, row.value):
                        continue
                    val_words = [w for w in line.words if _word_matches(w.text, row.value)]
                    coord = _tight_merge(val_words, anchor_x=line.x1) if val_words else None
                    if coord is not None:
                        cand = (coord, file_index)
                        break
                if cand is not None:
                    best = cand
                    break

        # 3) Деградация: значение пустое/не найдено → бокс самого параметра.
        #    Даём координаты КАЖДОЙ строке таблицы (иначе recall ~14%).
        if best is None and param_line_found is not None:
            pl, file_index = param_line_found
            # Бокс из слов строки параметра (не всей строки документа):
            if pl.words:
                coord = _merge_boxes(pl.words)
            else:
                coord = Coord(
                    top=int(pl.y1), left=int(pl.x1),
                    bottom=int(pl.y2), right=int(pl.x2),
                )
            best = (coord, file_index)

        if best is not None:
            coord, file_index = best
            positions.append(Position(id=row.id, coord=coord, file_index=file_index))

    return positions


def positions_to_dict(positions: List[Position]) -> List[dict]:
    """Сериализует positions в формат ответа API (пиксели)."""
    return [
        {
            "id": p.id,
            "coord": {
                "top": p.coord.top,
                "left": p.coord.left,
                "bottom": p.coord.bottom,
                "right": p.coord.right,
            },
            "file_index": p.file_index,
        }
        for p in positions
    ]


def _pct(value: Any, dim: float) -> Any:
    """Переводит пиксель в процент от размера страницы (с защитой от нуля)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    if not dim or dim <= 0:
        return value
    return round(v / dim * 100, 2)


def normalize_positions_percent(
    positions: List[dict],
    page_sizes: Dict[int, Tuple[int, int]],
) -> List[dict]:
    """Конвертирует пиксельные координаты ``positions`` в ПРОЦЕНТЫ.

    OCR возвращает пиксели при 300 DPI (например 2481×3508), а браузер
    рендерит изображение в произвольном CSS-масштабе. Процентные координаты
    масштабируются на ЛЮБОЙ размер элемента: ``top = 2002/3508 ≈ 57%`` —
    прямоугольник ложится точно на реальный бокс независимо от ширины картинки.

    :param positions: список ``{id, coord: {top,left,bottom,right}, file_index}``;
    :param page_sizes: ``{index_страницы: (width, height)}`` (из ``Page``);
    """
    result: List[dict] = []
    for pos in positions:
        coord = pos.get("coord") or {}
        w, h = page_sizes.get(int(pos.get("file_index", 0)), (0, 0))
        result.append({
            "id": pos.get("id"),
            "coord": {
                "top": _pct(coord.get("top"), h),
                "left": _pct(coord.get("left"), w),
                "bottom": _pct(coord.get("bottom"), h),
                "right": _pct(coord.get("right"), w),
            },
            "file_index": pos.get("file_index", 0),
        })
    return result
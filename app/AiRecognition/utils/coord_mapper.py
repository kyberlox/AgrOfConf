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
    line: Optional[int] = None  # глобальный индекс [N] строки транскрипта от LLM


# | 5 | Давление (избыточное) | 1.6, МПа | 42 |
# | 6 | - Рабочее | 1.6, МПа |
_ROW_RE = re.compile(
    r"^\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*(?:\|\s*(\d*))?\s*\|?\s*$"
)


def parse_markdown_table(md: str) -> List[TableRow]:
    """Извлекает строки | ID | Параметр | Значение [| Строка] | из markdown."""
    rows: List[TableRow] = []
    for line in md.splitlines():
        m = _ROW_RE.match(line)
        if not m:
            continue
        row_id = int(m.group(1))
        parameter = m.group(2).strip()
        value = m.group(3).strip()
        line_idx = m.group(4)
        line = int(line_idx) if line_idx and line_idx.isdigit() else None
        # Строка-разделитель |---|---| не попадает (там нет числа в 1-й колонке)
        rows.append(TableRow(id=row_id, parameter=parameter, value=value, line=line))
    return rows


# ---------------------------------------------------------------------------
# Нормализация текста
# ---------------------------------------------------------------------------

_TRANSLIT = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X",
}

# Кириллические омонимы латиницы → СТРОЧНАЯ латиница (однозначный, нижний
# регистр). В отличие от ``_TRANSLIT`` (заменяет на заглавную) — нужен там,
# где дальше работаем с нижним регистром и сопоставляем посимвольно
# (цифровая путаница O/0 и т.п.).
_CYR_LOWER = {
    "а": "a", "в": "b", "е": "e", "к": "k", "м": "m", "н": "h",
    "о": "o", "р": "p", "с": "c", "т": "t", "у": "y", "х": "x",
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
    t = "".join(_CYR_LOWER.get(ch, ch) for ch in t)
    t = t.replace(",", ".")
    # Убираем пробелы, скобки, двоеточия, слэши, тире и прочую пунктуацию
    t = re.sub(r"[\s\u00a0()\[\]{}<>:;'\"«»…—–_\\/-]", "", t)
    return t


def _tokens(text: str) -> List[str]:
    """Разбивает текст на значимые токены (буквы/цифры), без пунктуации."""
    t = text.strip().lower()
    t = "".join(_CYR_LOWER.get(ch, ch) for ch in t)
    t = re.sub(r"[^a-zа-яё0-9]", " ", t)
    return [tok for tok in t.split() if tok]


_DIGIT_CONFUSIONS = {
    "о": "0", "o": "0", "q": "0",       # O/о/Q → 0
    "l": "1", "i": "1", "|": "1", "!": "1",  # l/I/| → 1
    "s": "5",                            # s → 5
    "б": "6", "b": "6",                  # б/B → 6
}


def _ocr_numbers(text: str) -> Optional[str]:
    """Ключ числа с учётом типичных OCR-путаниц символов.

    OCR часто читает ``O`` как ``0``, ``l``/``I`` как ``1``, ``б``/``B`` как
    ``6`` и т.п. (в технических бланках это массовое). Применяем замены ТОЛЬКО
    там, где в токене уже есть цифра — иначе слово ``"масса"`` (s→5) получит
    ложный числовой ключ.

    Примеры: ``"1,б" -> "1.6"``, ``"О.6" -> "0.6"``, ``"масса" -> None``.
    """
    t = text.strip().lower()
    t = "".join(_CYR_LOWER.get(ch, ch) for ch in t)
    # Если вообще нет цифр — это не число, путаницу не применяем.
    if not re.search(r"\d", t):
        return None
    mapped = "".join(_DIGIT_CONFUSIONS.get(ch, ch) for ch in t)
    m = re.search(r"-?\d+(?:[.,]\d+)?", mapped)
    if not m:
        return None
    return m.group().replace(",", ".")


def _extract_number(text: str) -> Optional[float]:
    """Первое число из строки (для числовой эквивалентности)."""
    key = _ocr_numbers(text) or _num_key(text)
    if not key:
        return None
    try:
        return float(key)
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

    wkey = _ocr_numbers(word_text) or _num_key(word_text)
    vkey = _ocr_numbers(value_text) or _num_key(value_text)
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
    - частичному вхождению названия в строку (в строке таблицы рядом
      с названием обычно стоит значение);
    - опечаткам OCR (fuzzy ≥ 0.75).

    Смягчено специально для подъёма recall привязки строк: раньше жёсткий
    порог (fuzzy 0.85, длина ≥ 3, только «всё-в-подмножестве») терял больше
    половины строк таблицы, и они оставались вообще без координат.
    """
    tn = _normalize(text)
    pn = _normalize(param_text)
    if not tn or not pn:
        return False
    if tn == pn:
        return True
    # Явное вхождение названия в строку (рядом с названием — значение).
    if len(pn) >= 3 and pn in tn:
        return True
    if len(tn) >= 3 and tn in pn:
        return True

    # Токены: все значимые слова короткой стороны есть в длинной,
    # либо совпало не менее 60% токенов короткой стороны, либо токены
    # короткой стороны похожи на токены длинной (опечатки OCR).
    tt = _tokens(text)
    pt = _tokens(param_text)
    if tt and pt:
        if len(pt) <= len(tt):
            short, long_ = pt, tt
        else:
            short, long_ = tt, pt
        sset, lset = set(short), set(long_)
        inter = len(sset & lset)
        if inter == len(sset):
            return True
        # Несколько общих токенов (а не один служебный типа «тип»/«Р»).
        if inter >= 2 and inter / len(sset) >= 0.5:
            return True
        # Один значимый токен (>= 6 симв.) — дискриминатор названия:
        # «конструкции» есть, «среды» нет → строки различны. Короткие
        # служебные токены («тип», «Р», «PN») не считаются.
        single_distinct = any(
            len(tok) >= 6 and (
                tok in lset
                or any(  # noqa: B023
                    len(wtok) >= 6 and difflib.SequenceMatcher(None, tok, wtok).ratio() >= 0.85
                    for wtok in long_
                )
            )
            for tok in short
        )
        if single_distinct and len(sset) >= 2:
            return True
        # Опечатки OCR внутри токенов: не менее 60% токенов короткой стороны
        # имеют аналог в длинной стороне по префиксу/fuzzy.
        fuzzy_hits = sum(
            1 for tok in short if any(
                wtok == tok
                or (len(tok) >= 4 and (wtok.startswith(tok[:4]) or (len(wtok) >= 4 and tok.startswith(wtok[:4]))))
                or (len(tok) >= 4 and len(wtok) >= 4
                    and difflib.SequenceMatcher(None, tok, wtok).ratio() >= 0.75)
                for wtok in long_
            )
        )
        if len(short) and fuzzy_hits / len(short) >= 0.6:
            return True

    # Fuzzy по компактной строке (опечатки OCR)
    if len(pn) >= 4 and difflib.SequenceMatcher(None, pn, tn).ratio() >= 0.7:
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
    # Шум OCR в коротком значении (единицы, буквенные маркеры):
    # "мпа" vs "мра", "гал" vs "гал" и т.п.
    if len(vn) >= 4 and difflib.SequenceMatcher(None, ln, vn).ratio() >= 0.75:
        return True
    return False


def _word_match_any(line: TextLine, value_text: str) -> bool:
    """Есть ли хотя бы одно слово строки, совпавшее со значением."""
    vn = _normalize(value_text)
    if not vn:
        return False
    return any(_word_matches(w.text, value_text) for w in line.words)


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


def _split_word_clusters(words: List[WordBox], gap_factor: float = 2.0) -> List[List[WordBox]]:
    """Делит слова строки на горизонтальные кластеры («ячейки» таблицы).

    Кластер — последовательность слов без крупного горизонтального разрыва
    относительно высоты шрифта. Так внутри одной OCR-строки выделяются
    «имя параметра», «значение», «единица измерения» и т.п.
    """
    ws = sorted(words, key=lambda w: w.x1)
    if not ws:
        return []
    groups: List[List[WordBox]] = [[ws[0]]]
    for w in ws[1:]:
        prev = groups[-1][-1]
        h = max(1.0, (prev.y2 - prev.y1 + w.y2 - w.y1) / 2)
        if w.x1 - prev.x2 <= h * gap_factor:
            groups[-1].append(w)
        else:
            groups.append([w])
    return groups


def _clusters_value_words(clusters: List[List[WordBox]]) -> List[WordBox]:
    """Слова «значения» из кластеров строки: всё после первого кластера.

    Если среди остальных кластеров есть числовой — регион значения
    начинается с первого числового кластера (не тащим в бокс обозначения
    и промежуточные служебные колонки).
    """
    if len(clusters) < 2:
        return []
    start_i = 1
    for i, c in enumerate(clusters[1:], start=1):
        if any(re.search(r"\d", w.text) for w in c):
            start_i = i
            break
    return [w for c in clusters[start_i:] for w in c]


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


def _find_value_coord_geometric(
    lines: List[TextLine],
    param_line: TextLine,
) -> Optional[Coord]:
    """Геометрический бокс значения БЕЗ требования текстового совпадения.

    Используется, когда LLM-значение отличается от текста OCR (конвертация
    единиц, дефолты из правил, пересказ) — точного матча нет и не будет.
    Бокс строится по компоновке строк:
    1. правая часть собственной строки параметра (выделяется после группы имени);
    2. следующие строки в пределах полосы, выровненные по той же колонке
       (значения, записанные под названием параметра).
    """
    clusters = _split_word_clusters(list(param_line.words))

    # 1) Правая часть строки параметра — «значение» после группы имени.
    if len(clusters) >= 2:
        value_words = _clusters_value_words(clusters)
        if value_words:
            return _merge_boxes(value_words)

    # 2) Строки под параметром в пределах полосы (многострочные ячейки,
    #    значения под названием).
    line_h = max(1.0, param_line.y2 - param_line.y1)
    band = max(line_h * 4.0, 40.0)
    candidates: List[Tuple[float, Coord]] = []
    for line in lines:
        if line is param_line:
            continue
        dy = (line.y1 + line.y2) / 2 - (param_line.y1 + param_line.y2) / 2
        if dy <= 0 or dy > band:
            continue
        # Та же колонка: левое начало строки — от чуть левее названия
        # до чуть правее его конца.
        if line.x1 < param_line.x1 - band or line.x1 > param_line.x2 + line_h * 2:
            continue
        sub_clusters = _split_word_clusters(line.words)
        value_words = _clusters_value_words(sub_clusters) or list(line.words)
        if not value_words:
            continue
        coord = _merge_boxes(value_words)
        if coord is not None:
            candidates.append((dy, coord))
    if candidates:
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]
    return None


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def _line_windows(lines: List[TextLine]) -> List[Tuple[int, str]]:
    """Окна строк для поиска перенесённых названий параметров.

    Окно = текст строки + тексты следующих за ней строк, вертикально близких
    и выровненных по левому краю (название параметра, перенесённое OCR на
    2-3 строки). Иначе ``"Тип"`` и ``"среды"`` в разных строках никогда не
    соберутся в ``"Тип среды"`` — главная причина 0% попаданий якоря.

    Возвращает список ``(индекс первичной строки, текст-окно)``.
    """
    sorted_lines = sorted(lines, key=lambda l: (l.y1, l.x1))
    windows: List[Tuple[int, str]] = []
    i = 0
    n = len(sorted_lines)
    while i < n:
        line = sorted_lines[i]
        line_h = max(1.0, line.y2 - line.y1)
        parts = [line.text]
        j = i + 1
        while j < n:
            nxt = sorted_lines[j]
            if nxt.y1 > line.y2 + line_h * 1.8:
                # Слишком далеко по вертикали — это уже не продолжение ячейки.
                break
            # Вертикально близкая строка, выровненная по левому краю —
            # продолжение перенесённого названия. Горизонтальных соседей
            # (другие ячейки строки) просто пропускаем, не ломая цепочку.
            if abs(nxt.x1 - line.x1) <= line_h * 0.6:
                parts.append(nxt.text)
            j += 1
        windows.append((i, " ".join(parts)))
        i = j
    return windows


def build_positions(
    md_table: str,
    pages_words: List[List[WordBox]],
    lines_by_page: Optional[Dict[int, List[TextLine]]] = None,
    log_reasons: bool = False,
) -> List[Position]:
    """Сопоставляет строки таблицы с боксами OCR и возвращает positions.

    Стратегия (привязка к месту, а не к тексту по всей странице):

    1. Для каждой строки ``| ID | Параметр | Значение |`` сначала ищем
       строку транскрипта, содержащую НАЗВАНИЕ параметра (якорь);
    2. Рядом с якорем ищем слова, соответствующие ЗНАЧЕНИЮ (точный матч);
    3. Если точного матча нет — берём геометрический бокс (правая часть
       строки параметра / строки под ним): значение покрывается даже когда
       LLM нормализовал/конвертировал единицы или подставил дефолт;
    4. Фолбэк (параметр не найден): строка со значением в любом месте
       документа;
    5. Деградация: бокс строки параметра.

    ``log_reasons`` — печатает в лог причины отсутствия/способа получения
    координат по каждой строке (для диагностики низкого recall).

    :param md_table: markdown-таблица (ответ LLM);
    :param pages_words: список списков WordBox по страницам;
    :param lines_by_page: опционально — уже собранные строки транскрипта
        по страницам (ускоряет работу);
    :param log_reasons: печатать ли диагностику по строкам;
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

    # Глобальный индекс [N] строки транскрипта (как в build_transcript):
    # сквозная нумерация только по непустым страницам и линиям внутри страницы.
    line_idx_map: Dict[int, Tuple[int, TextLine]] = {}
    _line_no = 0
    for _file_index in sorted(lines_by_page):
        for _line in lines_by_page[_file_index]:
            line_idx_map[_line_no] = (_file_index, _line)
            _line_no += 1

    reasons = {
        "total": len(rows),
        "exact": 0,
        "geometric": 0,
        "fallback_value": 0,
        "fallback_geometric": 0,
        "param_only": 0,
        "missing": 0,
        "param_found": 0,
        "param_not_found": 0,
    }

    # Окна строк по страницам (для перенесённых названий параметров).
    windows_by_page: Dict[int, List[Tuple[int, str]]] = {}
    sorted_lines_by_page: Dict[int, List[TextLine]] = {}
    for file_index, lines in lines_by_page.items():
        windows_by_page[file_index] = _line_windows(lines)
        sorted_lines_by_page[file_index] = sorted(lines, key=lambda l: (l.y1, l.x1))

    positions: List[Position] = []
    for row in rows:
        best: Optional[Tuple[Coord, int]] = None   # (coord, file_index)
        param_line_found: Optional[Tuple[TextLine, int]] = None
        row_reason: Optional[str] = None

        # 0) Прямой путь: LLM вернул глобальный индекс [N] строки транскрипта,
        #    на которой находится значение. Надёжнее текстового сопоставления:
        #    не зависит от того, как модель пересказала имя параметра.
        if row.line is not None and row.line in line_idx_map:
            ln_file, ln = line_idx_map[row.line]
            pl_lines = lines_by_page.get(ln_file, [])
            confirms = (
                _param_matches(ln.text, row.parameter)
                or _line_matches(ln, row.value)
                or _word_match_any(ln, row.value)
                or _param_matches(ln.text, row.value)
            )
            if confirms:
                coord = _find_value_coord(pl_lines, ln, row.value)
                method = "exact"
                if coord is None and row.value.strip() and row.value.strip() not in {"-", "—"}:
                    coord = _find_value_coord_geometric(pl_lines, ln)
                    method = "geometric"
                if coord is not None:
                    best = (coord, ln_file)
                    row_reason = method
                    param_line_found = (ln, ln_file)

        # 1) Основной путь: строка параметра → значение рядом с ней
        for file_index in sorted(words_by_page):
            if best is not None:
                break
            lines = lines_by_page.get(file_index, [])
            s_lines = sorted_lines_by_page.get(file_index, [])
            windows = windows_by_page.get(file_index, [])
            param_lines = [
                s_lines[idx]
                for idx, wtext in windows
                if _param_matches(wtext, row.parameter)
            ]
            if not param_lines:
                continue
            for pl in param_lines:
                if param_line_found is None:
                    param_line_found = (pl, file_index)
                coord = _find_value_coord(lines, pl, row.value)
                method = "exact"
                if coord is None and row.value.strip() and row.value.strip() not in {"-", "—"}:
                    # Точного текстового матча нет — берём геометрический бокс
                    # (правая часть строки параметра / строки под ним). Это
                    # покрывает нормализованные LLM значения.
                    coord = _find_value_coord_geometric(lines, pl)
                    method = "geometric"
                if coord is not None:
                    best = (coord, file_index)
                    row_reason = method
                    break
            if best is not None:
                break

        if param_line_found is not None:
            reasons["param_found"] += 1
        else:
            reasons["param_not_found"] += 1

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
                    # Если слова не совпали строго (а строка с значением всё
                    # же найдена через _line_matches) — берём правую часть
                    # строки как геометрический бокс значения.
                    if coord is None:
                        sub_clusters = _split_word_clusters(line.words)
                        val_region = _clusters_value_words(sub_clusters) or list(line.words)
                        coord = _merge_boxes(val_region) if val_region else None
                        row_reason = "fallback_geometric"
                    else:
                        row_reason = "fallback_value"
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
            row_reason = "param_only"

        if best is not None:
            coord, file_index = best
            positions.append(Position(id=row.id, coord=coord, file_index=file_index))
            if row_reason in reasons:
                reasons[row_reason] += 1
        else:
            if row_reason is None:
                row_reason = "missing"
            reasons["missing"] += 1
            if log_reasons:
                near = _nearest_lines(lines_by_page, row, top_k=3)
                print(
                    f"  [coord_mapper] нет координат | id={row.id} | "
                    f"param={row.parameter!r} | value={row.value!r} | причина={row_reason}"
                )
                for j, (score, text) in enumerate(near, start=1):
                    print(f"      ~ ближайшая строка {j} (score={score:.2f}): {text[:160]!r}")

    if log_reasons:
        print("[coord_mapper] Итог по координатам:", reasons)

    return positions


def _nearest_lines(
    lines_by_page: Dict[int, List[TextLine]],
    row: "TableRow",
    top_k: int = 3,
) -> List[Tuple[float, str]]:
    """Самые близкие к ``row`` строки транскрипта (для диагностики пропусков).

    Строка считается близкой, если по пересечению токенов с именем или
    значением параметра она похожа на целевой источник. Нужно, чтобы понять,
    ПОЧЕМУ i-я строка не нашла бокс: назван параметр иначе / OCR испортил
    текст / значения в документе вообще нет.
    """
    candidates: List[Tuple[float, str]] = []
    pn = _normalize(row.parameter)
    vn = _normalize(row.value)
    for lines in lines_by_page.values():
        for line in lines:
            ln = _normalize(line.text)
            if not ln:
                continue
            score = 0.0
            for target in (pn, vn):
                if not target:
                    continue
                if target in ln or ln in target:
                    score = max(score, 1.0)
                else:
                    ptk = _tokens(target)
                    ltk = _tokens(ln)
                    if ptk and ltk:
                        overlap = len(set(ptk) & set(ltk))
                        score = max(score, overlap / max(len(ptk), len(ltk)))
            if score > 0:
                candidates.append((score, line.text))
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[:top_k]


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
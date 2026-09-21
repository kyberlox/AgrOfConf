"""
Локальный OCR-движок на базе RapidOCR (PP-OCR модели через ONNX Runtime).

Роль в гибридной архитектуре:
- LLM НЕ выдаёт координаты — геометрию даёт этот модуль;
- ``ocr_page()`` возвращает словоуровневые боксы в пикселях исходного JPEG;
- ``build_transcript()`` собирает текстовый транскрипт для текст-only LLM;
- ``coord_mapper`` использует боксы для сопоставления строк таблицы ↔ координат.

Особенности:
- Singleton: модель загружается один раз при первом вызове (лениво);
- Инференс выполняется в thread pool (``asyncio.to_thread``), чтобы не
  блокировать event loop FastAPI;
- In-memory LRU-кэш по SHA-256 JPEG: повторное распознавание той же
  страницы не пересчитывается;
- Если пакет rapidocr не установлен или модели недоступны — модуль
  "тихо" деградирует: ``is_available() == False``, а роутер уходит
  в vision-фолбэк.
"""
import asyncio
import hashlib
import logging
import os
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# RapidOCR подключается опционально: если пакет не установлен,
# приложение продолжает работать на vision-фолбэке.
try:
    from rapidocr_onnxruntime import RapidOCR as _RapidOCR
    RAPID_OCR_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RapidOCR = None
    RAPID_OCR_AVAILABLE = False


@dataclass
class WordBox:
    """Одно распознанное слово с боксом в пикселях исходного изображения."""
    text: str
    # box в формате RapidOCR: 4 точки [x, y]
    box: List[List[float]]
    score: float = 0.0
    page_index: int = 0

    @property
    def x1(self) -> float:
        return min(p[0] for p in self.box)

    @property
    def y1(self) -> float:
        return min(p[1] for p in self.box)

    @property
    def x2(self) -> float:
        return max(p[0] for p in self.box)

    @property
    def y2(self) -> float:
        return max(p[1] for p in self.box)


@dataclass
class TextLine:
    """Строка текста, собранная из слов с близким y (кластеризация)."""
    text: str
    x1: float
    y1: float
    x2: float
    y2: float
    page_index: int
    words: List[WordBox] = field(default_factory=list)


class _OcrEngine:
    """Singleton-движок RapidOCR с кэшем результатов."""

    _instance: Optional["_OcrEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "_OcrEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_inner()
        return cls._instance

    def _init_inner(self) -> None:
        self._engine = None
        self._cache: "OrderedDict[str, List[dict]]" = OrderedDict()
        self._cache_lock = threading.Lock()
        self._cache_size = int(os.getenv("OCR_CACHE_SIZE", "64"))
        # Максимум страниц, которые прогоняем через OCR за один документ.
        self.max_pages = int(os.getenv("MAX_OCR_PAGES", "10"))
        # ONNX Runtime НЕ thread-safe для конкурентных вызовов одной сессии:
        # параллельный инференс из нескольких потоков даёт segfault (процесс
        # падает БЕЗ Python-traceback). Поэтому все вызовы движка идут через
        # один мьютекс (последовательно).
        self._infer_lock = threading.Lock()
        # Если инференс упал — помечаем движок "сломанным" и отдаём пустой
        # результат, чтобы роутер ушёл в vision-фолбэк, а не ронял процесс.
        self._ocr_broken = False

    @property
    def available(self) -> bool:
        return RAPID_OCR_AVAILABLE and not self._ocr_broken

    def mark_broken(self) -> None:
        """Помечает движок неработоспособным (инференс упал/недоступен)."""
        self._ocr_broken = True

    def warm_up(self) -> None:
        """Прогрев: загружает модель (вызывать при старте приложения)."""
        if self.available:
            self._get_engine()

    def _get_engine(self):
        if self._engine is None:
            self._engine = _RapidOCR()
            logger.info("RapidOCR модель загружена")
        return self._engine

    # ---------------------------------------------------------------- cache
    def _cache_get(self, key: str) -> Optional[List[dict]]:
        with self._cache_lock:
            item = self._cache.get(key)
            if item is not None:
                self._cache.move_to_end(key)
                return item
        return None

    def _cache_set(self, key: str, value: List[dict]) -> None:
        with self._cache_lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    # ---------------------------------------------------------------- OCR
    @staticmethod
    def _jpeg_to_ndarray(jpeg_bytes: bytes) -> Optional[np.ndarray]:
        """Декодирует JPEG-байты в numpy-массив RGB.

        RapidOCR 1.2.x ожидает np.ndarray (или путь к файлу), а не сырые bytes.
        Подача bytes вызывает внутренние ошибки/падения в некоторых версиях.
        """
        try:
            img = Image.open(BytesIO(jpeg_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")
            return np.asarray(img)
        except Exception as e:  # pragma: no cover
            logger.warning("Не удалось декодировать JPEG для OCR: %s", e)
            return None

    def _run_ocr_sync(self, jpeg_bytes: bytes, page_index: int) -> List[WordBox]:
        """Синхронный OCR одной страницы (вызывается из thread pool)."""
        if not self.available:
            return []

        key = hashlib.sha256(jpeg_bytes).hexdigest()
        cached = self._cache_get(key)
        if cached is not None:
            return [WordBox(**w) for w in cached]

        arr = self._jpeg_to_ndarray(jpeg_bytes)
        if arr is None:
            return []

        # Весь инференс — под мьютексом: ONNX-сессия не поддерживает
        # конкурентные вызовы (иначе segfault и падение процесса).
        try:
            with self._infer_lock:
                engine = self._get_engine()
                result, _elapse = engine(arr)
        except Exception as e:
            logger.error("Ошибка OCR страницы %d: %s. Переключаемся на vision-фолбэк.", page_index, e)
            self.mark_broken()
            return []

        boxes: List[WordBox] = []
        if result:
            for box, text, score in result:
                if text and str(text).strip():
                    boxes.append(
                        WordBox(text=str(text).strip(), box=[[float(x), float(y)] for x, y in box],
                                score=float(score), page_index=page_index)
                    )
        # Кэшируем сериализуемое представление
        self._cache_set(key, [_word_to_dict(w) for w in boxes])
        return boxes

    async def ocr_page(self, jpeg_bytes: bytes, page_index: int = 0) -> List[WordBox]:
        """Асинхронный OCR страницы (JPEG → список слов с боксами)."""
        if not self.available:
            return []
        return await asyncio.to_thread(self._run_ocr_sync, jpeg_bytes, page_index)

    async def ocr_pages(self, pages_jpeg: List[Tuple[int, bytes]]) -> List[List[WordBox]]:
        """OCR нескольких страниц ПОСЛЕДОВАТЕЛЬНО (не параллельно!).

        Параллельный инференс (asyncio.gather) на одном экземпляре RapidOCR
        вызывал segfault/OOM и падение всего контейнера fastapi.
        """
        if not self.available:
            return [[] for _ in pages_jpeg]
        results: List[List[WordBox]] = []
        for idx, jpeg in pages_jpeg:
            results.append(await self.ocr_page(jpeg, idx))
            # Если движок "сломался" — остальные страницы отдаём пустыми,
            # чтобы роутер сразу ушёл в vision-фолбэк.
            if not self.available:
                while len(results) < len(pages_jpeg):
                    results.append([])
                break
        return results

    # ------------------------------------------------------------ transcript
    def cluster_into_lines(self, words: List[WordBox], y_tolerance: float = 12.0) -> List[TextLine]:
        """Публичная обёртка кластеризации слов в строки."""
        return self._cluster_into_lines(words, y_tolerance=y_tolerance)

    def _cluster_into_lines(self, words: List[WordBox], y_tolerance: float = 12.0) -> List[TextLine]:
        """Группирует слова одной страницы в строки по вертикальной близости.

        Слова сортируются по y1; соседние попадают в одну строку, если их
        вертикальные центры ближе ``y_tolerance`` пикселей. Внутри строки
        слова упорядочиваются слева направо.
        """
        if not words:
            return []
        sorted_words = sorted(words, key=lambda w: (w.y1, w.x1))
        lines: List[List[WordBox]] = []
        current: List[WordBox] = [sorted_words[0]]
        current_center = (sorted_words[0].y1 + sorted_words[0].y2) / 2

        for w in sorted_words[1:]:
            w_center = (w.y1 + w.y2) / 2
            if abs(w_center - current_center) <= y_tolerance:
                current.append(w)
            else:
                lines.append(current)
                current = [w]
                current_center = w_center
        lines.append(current)

        result: List[TextLine] = []
        for line_words in lines:
            line_words.sort(key=lambda w: w.x1)
            text = " ".join(w.text for w in line_words)
            result.append(TextLine(
                text=text,
                x1=min(w.x1 for w in line_words),
                y1=min(w.y1 for w in line_words),
                x2=max(w.x2 for w in line_words),
                y2=max(w.y2 for w in line_words),
                page_index=line_words[0].page_index,
                words=line_words,
            ))
        return result

    async def build_transcript(self, pages: List[List[WordBox]], y_tolerance: float = 12.0) -> str:
        """Строит текстовый транскрипт документа для текст-only LLM.

        Формат:
            === Страница N ===
            строка1
            строка2
            ...
        """
        parts: List[str] = []
        for page_words in pages:
            if not page_words:
                continue
            page_idx = page_words[0].page_index
            lines = self._cluster_into_lines(page_words, y_tolerance=y_tolerance)
            parts.append(f"=== Страница {page_idx} ===")
            parts.extend(l.text for l in lines)
        return "\n".join(parts)


# Глобальный singleton-экземпляр
_engine_instance: Optional[_OcrEngine] = None


def get_ocr_engine() -> _OcrEngine:
    """Возвращает singleton-экземпляр OCR-движка."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = _OcrEngine()
    return _engine_instance


def is_ocr_available() -> bool:
    """Доступен ли локальный OCR (пакет + модели)."""
    return RAPID_OCR_AVAILABLE


def warm_up_ocr() -> None:
    """Прогрев OCR-модели при старте приложения (безопасен, если нет пакета)."""
    try:
        get_ocr_engine().warm_up()
    except Exception as e:  # pragma: no cover
        logger.warning("Не удалось прогреть OCR: %s", e)


async def ocr_pages_to_wordboxes(pages_jpeg: List[Tuple[int, bytes]]) -> List[List[WordBox]]:
    """Удобная обёртка: список (index, jpeg_bytes) → списки WordBox по страницам."""
    engine = get_ocr_engine()
    return await engine.ocr_pages(pages_jpeg[: engine.max_pages])


async def build_transcript(pages_jpeg: List[Tuple[int, bytes]]) -> str:
    """OCR всех страниц и сборка текстового транскрипта одной функцией."""
    engine = get_ocr_engine()
    pages = await engine.ocr_pages(pages_jpeg[: engine.max_pages])
    return await engine.build_transcript(pages)


def _word_to_dict(w: WordBox) -> dict:
    return {"text": w.text, "box": w.box, "score": w.score, "page_index": w.page_index}
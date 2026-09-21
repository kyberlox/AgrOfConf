"""
Подсистема распознавания опросных листов (гибрид OCR + LLM).

- `router.AI` — FastAPI-роутер: upload_OL (гибридное распознавание),
  convert-ai-result (валидация под шаблон продукта), управление промтами;
- `utils.promt_ol` — промты распознавания/валидации;
- `utils.convert_ol_file` — конвертация UploadFile → JPEG-страницы;
- `utils.ocr_engine` — локальный OCR (RapidOCR) со словоуровневыми боксами;
- `utils.coord_mapper` — сопоставление строк таблицы ↔ боксов OCR (positions);
- `utils.prompt_storage` — хранение промтов продуктов и правил дефолтов.
"""
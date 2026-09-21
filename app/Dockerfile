FROM python:3.13

# Системные зависимости для PyMuPDF, Pillow, pandoc и LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Для PyMuPDF
    libmupdf-dev \
    # Для Pillow (JPEG/PNG)
    libjpeg62-turbo-dev \
    libpng-dev \
    # pandoc (для pypandoc) + pdf-engine (pdflatex как fallback)
    pandoc \
    texlive-latex-base \
    # LibreOffice для конвертации DOCX → PDF
    libreoffice-core \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*
    

WORKDIR /data/app
COPY ./requirements.txt /data/app/requirements.txt

RUN pip install --upgrade pip

ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# Ограничение потоков BLAS/OpenMP — стабилизирует ONNX Runtime в контейнере:
# без этого OMP_* поднимает по потоку на ядро → segfault/деградация под нагрузкой. УБРАЛИ ПОКА ЧТО
# ENV OMP_NUM_THREADS=2 \
#     OPENBLAS_NUM_THREADS=2 \
#     MKL_NUM_THREADS=2 \
#     NUMEXPR_NUM_THREADS=2

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8000"]
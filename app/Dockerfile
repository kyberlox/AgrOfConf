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

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8000"]
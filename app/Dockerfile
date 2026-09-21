FROM python:3.13

# Системные зависимости для PyMuPDF, Pillow, pandoc и LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    pandoc \
    texlive-latex-base \
    libreoffice-core \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv (копируем бинарник из официального образа — это самый быстрый способ)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /data/app
COPY ./requirements.txt /data/app/requirements.txt

# Используем uv для установки. Флаг --system ставит пакеты в системный Python,
# что эквивалентно тому, что делал pip раньше.
# Опция UV_INDEX_URL задаёт зеркало (аналог PIP_INDEX_URL).
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
RUN uv pip install --system --no-cache -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8000"]
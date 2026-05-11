FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'format=pdf' \
    'if [ "${1:-}" = "-f" ]; then' \
    '  format="$2"' \
    '  shift 2' \
    'fi' \
    'for file in "$@"; do' \
    '  libreoffice --headless --convert-to "$format" --outdir "$(dirname "$file")" "$file"' \
    'done' \
    > /usr/local/bin/unoconv \
    && chmod +x /usr/local/bin/unoconv

COPY requirements-docker.txt /app/
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . /app/
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn labauto.wsgi:application --bind 0.0.0.0:8000"]

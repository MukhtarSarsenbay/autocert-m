FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-docker.txt /app/
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . /app/
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn labauto.wsgi:application --bind 0.0.0.0:8000 --timeout ${GUNICORN_TIMEOUT:-180}"]

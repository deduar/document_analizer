FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --create-home --shell /bin/bash appuser

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY config.yaml /app/config.yaml

RUN chown -R appuser:appuser /app

ENV PYTHONPATH=/app/src

USER appuser

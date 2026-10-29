FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SAL_USE_VCLPLUGIN=svp
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer fonts-liberation fonts-dejavu-core fonts-noto-core \
    fonts-crosextra-carlito fonts-crosextra-caladea fonts-opensymbol \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home school && chown -R school:school /app
USER school
CMD ["sh", "-c", "exec gunicorn wsgi:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 60"]

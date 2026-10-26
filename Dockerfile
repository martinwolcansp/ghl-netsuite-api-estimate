# Dockerfile — ghl-netsuite-api-estimate (Etapa 3)
# Mismo esquema que Etapa 2 (ghl-netsuite-api-opportunities):
# python:3.11-slim + curl, puerto 8000.

FROM python:3.11-slim

WORKDIR /app

# curl: lo usa el healthcheck HTTP de Coolify para pegarle a /health desde
# dentro del contenedor.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Health check propio (además del que se configura en Coolify contra /health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

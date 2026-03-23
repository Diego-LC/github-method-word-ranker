FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app/src

# Instalar git para clonado de repositorios.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY tests ./tests

CMD ["python", "-m", "miner.main"]

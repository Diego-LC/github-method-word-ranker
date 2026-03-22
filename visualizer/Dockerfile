FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh ./entrypoint.sh
COPY src ./src
COPY tests ./tests

RUN chmod +x ./entrypoint.sh

EXPOSE 8501

CMD ["./entrypoint.sh"]

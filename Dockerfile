FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY config.yaml.example .

ENV GATEKEEPER_CONFIG=/app/config.yaml
ENV GATEKEEPER_DB=/app/data/gatekeeper.db

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.main:create_app()"]

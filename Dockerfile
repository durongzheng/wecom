FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .[celery]

COPY src/ ./src/
COPY src/config/.env ./src/config/.env  

CMD ["uvicorn", "wecom.main:app", "--host", "0.0.0.0", "--port", "8000"]
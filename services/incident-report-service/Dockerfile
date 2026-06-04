


FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
COPY tests/ ./tests/

# Add non-root user and give ownership of /app
RUN addgroup --system urbanflow && adduser --system --ingroup urbanflow urbanflow
RUN chown -R urbanflow:urbanflow /app

USER urbanflow

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"]
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


EXPOSE 8003
RUN addgroup --system urbanflow && adduser --system --ingroup urbanflow urbanflow
RUN chown -R urbanflow:urbanflow /app
USER urbanflow


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
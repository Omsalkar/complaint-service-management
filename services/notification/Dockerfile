FROM python:3.12-slim
WORKDIR /app
COPY common /app/common
COPY services/notification/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/notification/main.py .
ENV PYTHONPATH=/app SERVICE_NAME=notification-service
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8005"]

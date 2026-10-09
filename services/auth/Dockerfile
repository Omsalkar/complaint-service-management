FROM python:3.12-slim
WORKDIR /app
COPY common /app/common
COPY services/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/auth/main.py .
ENV PYTHONPATH=/app SERVICE_NAME=auth-service
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8001"]

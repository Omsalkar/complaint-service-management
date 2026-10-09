FROM python:3.12-slim
WORKDIR /app
COPY common /app/common
COPY services/complaint/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/complaint/main.py .
ENV PYTHONPATH=/app SERVICE_NAME=complaint-service
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8003"]

FROM python:3.11-slim

WORKDIR /app

COPY produce_messages.py .

# Cài thư viện
RUN pip install --no-cache-dir kafka-python minio pandas pyarrow fastparquet

CMD ["python", "produce_messages.py"]

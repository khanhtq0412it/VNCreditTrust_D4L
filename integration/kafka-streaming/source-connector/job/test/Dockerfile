FROM python:3.11-slim

WORKDIR /app

COPY produce_messages.py .

RUN pip install kafka-python

CMD ["python", "produce_messages.py"]

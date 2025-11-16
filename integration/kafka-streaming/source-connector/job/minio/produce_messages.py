from kafka import KafkaProducer
from minio import Minio
import pandas as pd
import json
import io
import time
import os

# -----------------------------
# Load config từ env
# -----------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_PREFIX = os.getenv("MINIO_PREFIX", "data-source")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

# -----------------------------
# MinIO client
# -----------------------------
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# -----------------------------
# Kafka producer
# -----------------------------
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# -----------------------------
# Memory-based tracking processed files
# -----------------------------
processed_files = set()

# -----------------------------
# Helper: read object from MinIO
# -----------------------------
def read_file_from_minio(bucket, object_name):
    response = minio_client.get_object(bucket, object_name)
    data = response.read()
    response.close()
    response.release_conn()
    return data

# -----------------------------
# Main loop
# -----------------------------
while True:
    try:
        objects = minio_client.list_objects(MINIO_BUCKET, prefix=MINIO_PREFIX, recursive=True)

        for obj in objects:
            if obj.object_name in processed_files:
                continue

            print(f"Processing new file: {obj.object_name}")
            data = read_file_from_minio(MINIO_BUCKET, obj.object_name)

            records = []

            if obj.object_name.endswith(".json"):
                try:
                    parsed = json.loads(data.decode("utf-8"))
                    if isinstance(parsed, dict):
                        records = [parsed]
                    elif isinstance(parsed, list):
                        records = parsed
                except Exception as e:
                    print(f"Failed to parse JSON {obj.object_name}: {e}")
                    continue

            elif obj.object_name.endswith(".parquet"):
                try:
                    df = pd.read_parquet(io.BytesIO(data))
                    records = df.to_dict(orient="records")
                except Exception as e:
                    print(f"Failed to parse Parquet {obj.object_name}: {e}")
                    continue

            else:
                print(f"Unknown file type, skipping: {obj.object_name}")
                continue

            for r in records:
                producer.send(KAFKA_TOPIC, value=r)
                print(f"Sent record: {r}")

            producer.flush()
            print(f"Finished file: {obj.object_name}")

            processed_files.add(obj.object_name)

    except Exception as e:
        print(f"Error in main loop: {e}")

    time.sleep(10)

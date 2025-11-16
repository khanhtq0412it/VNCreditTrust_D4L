from kafka import KafkaProducer
import json
import time

bootstrap_servers = 'kafka-cluster-kafka-bootstrap:9092'  # Kafka service trong k8s
topic_name = 'test'

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    key_serializer=lambda k: k.encode('utf-8'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for i in range(20):
    key = f"user-{i}"
    value = {"id": i, "name": f"User {i}"}
    producer.send(topic_name, key=key, value=value)
    print(f"Sent: {key} -> {value}")
    time.sleep(1)

producer.flush()
print("All messages sent!")

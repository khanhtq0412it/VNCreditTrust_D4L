# Kafka Source Connector (producer job)

This folder contains test and helper assets used to produce messages to Kafka
for development and connector testing.

Key contents
- `job/` — contains Dockerfiles, Kubernetes manifests, and small Python
  producer scripts that emit messages to Kafka or write to local directories for
  testing.

How to use
- Build and run the producer locally or in your cluster to feed test data into
  a Kafka topic. Example flow:
  1. Edit `job/minio/` manifests and `produce_messages.py` to point to your
     Kafka bootstrap server and topic.
  2. Build the Docker image and run locally or apply the Kubernetes manifests
     for a quick smoke test.

Development tips
- Use a local Kafka cluster (Confluent Platform, Redpanda, or Dockerized
  Kafka) for development and debugging.
- Keep credentials and environment overrides out of committed files — use
  `env.local` or Kubernetes Secrets in your cluster.

See the `kafka-streaming/README.md` for an overview.


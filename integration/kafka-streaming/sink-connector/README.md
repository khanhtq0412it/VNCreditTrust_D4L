# Kafka Sink Connector

This folder contains example Kafka Connect sink connector configuration files
used to sink data from Kafka into downstream systems (ClickHouse and S3), along
with example templates. These are intended as starting points — adjust for
connection strings, authentication, topic names, and transformation logic.

Files
- `kafka-clickhouse-sink-connector.yaml` — example connector config for
  ClickHouse sink (using a sink connector that supports ClickHouse). Update
  host, port, and credentials before deploying.
- `kafka-s3-sink-connector.yaml` — example sink config that writes messages to
  S3/MinIO (useful for archiving raw messages or preparing data for batch jobs).

Deployment notes
- Deploy these configs to Kafka Connect cluster via REST API or your connector
  management tooling.
- Protect credentials and secrets — use external secret stores or environment
  variables rather than inline secrets in YAML files.

Testing
- Use a development Kafka Connect instance and point connectors to a test
  ClickHouse or S3/MinIO endpoint.
- Monitor connector logs for errors and adjust converters/transformations as
  needed.

See `kafka-streaming/README.md` for more context.


# kafka-streaming

This folder contains example Kafka Connect configurations and small test jobs
used to produce and sink messages for this project. The materials are intended
for local testing and demonstration and should be adapted for production use.

Subfolders
- `source-connector/` — example producer jobs and Kubernetes manifests used to
  produce messages to Kafka and to assist in local testing.
- `sink-connector/` — example Kafka Connect sink configurations (ClickHouse, S3)
  that demonstrate how to persist messages from Kafka topics.

Usage notes
- Review connector properties carefully before applying. They may contain
  environment-specific hosts, credentials, or bucket names.
- The `source-connector/job/` directory includes small Dockerfiles and
  manifests to run a standalone producer for load testing and development.

See the READMEs in `source-connector/` and `sink-connector/` for details.


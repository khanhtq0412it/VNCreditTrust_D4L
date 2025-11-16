FROM quay.io/strimzi/kafka:0.45.1-kafka-3.9.0
USER root:root
COPY clickhouse-kafka-connect-v1.3.4/ /opt/kafka/plugins/clickhouse-kafka-connect-v1.3.4/
COPY confluentinc-kafka-connect-avro-converter-8.1.0/ /opt/kafka/plugins/kafka-connect-avro-converter-8.1.0/
COPY confluentinc-kafka-connect-s3-11.0.8/ /opt/kafka/plugins/kafka-connect-s3-11.0.8/
COPY confluentinc-kafka-connect-s3-source-3.0.3/ /opt/kafka/plugins/kafka-connect-s3-source-3.0.3/
USER 1001

# Kafka CRDs — README

Mục đích
- Chứa CustomResourceDefinition (CRD) cần thiết cho Strimzi Kafka operator và các Kafka-related CRs (Kafka, KafkaConnect, KafkaTopic...).

Lưu ý
- CRDs phải được apply trước khi tạo Custom Resources (CR) hoặc deploy operator nếu bạn không cài chart có tự động tạo CRDs.

Apply CRDs

```bash
kubectl apply -f kafka/crds/
```

Kiểm tra

```bash
kubectl get crd | grep kafka
# ví dụ
kubectl get crd kafkas.kafka.strimzi.io
```

Versioning
- CRDs thường phải khớp/hoặc tương thích với phiên bản Strimzi operator bạn cài. Nếu dùng Helm chart, chart có thể cài CRDs giúp bạn.



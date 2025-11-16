# Kafka UI — README

Mục đích
- Deploy Kafka UI (web UI) để quản trị và theo dõi Kafka clusters.

Prerequisites
- Namespace `kafka` hoặc chỉ định namespace trong lệnh Helm
- Helm >= 3

Install (Helm)

```bash
helm repo add kafka-ui https://provectus.github.io/kafka-ui
helm repo update
helm upgrade --install kafka-ui kafka-ui/kafka-ui -n kafka -f kafka/kafka-ui/values.yaml
```

Access
- Nếu chart triển khai Service type ClusterIP, dùng port-forward:

```bash
kubectl -n kafka port-forward svc/kafka-ui 8080:8080
# mở http://localhost:8080
```

Troubleshooting
- Kiểm tra pods:

```bash
kubectl -n kafka get pods -l app.kubernetes.io/name=kafka-ui
kubectl -n kafka logs <pod>
```

- Đảm bảo cấu hình `values.yaml` chứa kết nối tới Kafka (bootstrap servers) hoặc tham chiếu tới secret chứa credentials.

References
- kafka-ui repo: https://github.com/provectus/kafka-ui


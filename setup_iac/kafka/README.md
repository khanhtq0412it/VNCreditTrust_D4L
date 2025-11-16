# Kafka (Strimzi, Kafka Connect, Kafka UI) — README

Mục đích
- Chứa manifest, CRD và hướng dẫn để deploy Kafka trên Kubernetes bằng Strimzi operator, cùng với Kafka Connect (connector plugin bundles) và Kafka UI.

Thư mục chính
- `crds/` — CRDs cần apply (nếu không dùng Helm chart để cài Strimzi).
- `strimzi-kafka-operator/` — values / manifests để cài Strimzi operator.
- `kafka-cluster.yaml` — Kafka CR mẫu (số broker, storage, listeners...).
- `kafka-connect.yaml` — Kafka Connect CR mẫu.
- `kafka-connect-plugins/` — Dockerfile và script để đóng gói connector plugins (ví dụ ClickHouse connector).
- `kafka-ui/` — values.yaml và manifest để deploy Kafka UI.

Prerequisites
- kubectl configured
- Helm >= 3 (nếu dùng Helm)
- Docker (để build plugin images)
- Namespace `kafka` (recommended)

Apply CRDs
- Nếu sử dụng manifest cài thủ công, apply CRDs trước:

```bash
kubectl apply -f kafka/crds/
```

Install Strimzi operator (Helm)

```bash
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-cluster-operator strimzi/strimzi-kafka-operator \
  -n kafka --create-namespace -f kafka/strimzi-kafka-operator/values.yaml
```

Hoặc (nếu repo chứa manifests):

```bash
kubectl apply -f kafka/strimzi-kafka-operator/ -n kafka
```

Deploy Kafka cluster

```bash
kubectl apply -f kafka/kafka-cluster.yaml -n kafka
```

Deploy Kafka Connect
- Nếu cần plugin custom, build plugin image bằng `kafka/kafka-connect-plugins/Dockerfile` và `plugins-download.sh`.
- Sửa `kafka/kafka-connect.yaml` để tham chiếu image đã build (spec.image hoặc podTemplate container image).

Build plugin image (ví dụ)

```bash
cd kafka/kafka-connect-plugins
./plugins-download.sh   # kiểm tra script, edit nếu cần
docker build -t <registry>/kafka-connect-plugins:tag .
docker push <registry>/kafka-connect-plugins:tag
```

Deploy Kafka UI (Helm example)

```bash
helm repo add kafka-ui https://provectus.github.io/kafka-ui
helm repo update
helm upgrade --install kafka-ui kafka-ui/kafka-ui -n kafka -f kafka/kafka-ui/values.yaml
```

Health checks & troubleshooting
- Check operator logs:

```bash
kubectl -n kafka get pods
kubectl -n kafka logs deploy/strimzi-cluster-operator
```

- Check Kafka and Connect pods:

```bash
kubectl -n kafka get pods -l strimzi.io/name
kubectl -n kafka logs <pod>
```

Security
- Use TLS for Kafka listeners in production (Strimzi supports mTLS).
- Store credentials (keystore, truststore, passwords) in Kubernetes Secrets — encrypted with SOPS/SealedSecrets or external secret manager.
- Restrict RBAC for operator and service accounts.

References
- Strimzi docs: https://strimzi.io/docs/
- Kafka Connect: https://kafka.apache.org/documentation/#connect
- Kafka UI: https://github.com/provectus/kafka-ui

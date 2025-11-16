# Strimzi Kafka Operator — README

Mục đích
- Chứa cấu hình (ví dụ `values.yaml`) và manifest để cài Strimzi Kafka Operator trong namespace `kafka`.

Install (Helm)

```bash
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-cluster-operator strimzi/strimzi-kafka-operator \
  -n kafka --create-namespace -f kafka/strimzi-kafka-operator/values.yaml
```

Or (manifests)

```bash
kubectl apply -f kafka/strimzi-kafka-operator/ -n kafka
```

Notes
- Nếu cài bằng Helm, chart có thể cài CRDs; nếu không, apply `kafka/crds/` trước.
- Tùy chỉnh giá trị trong `values.yaml` (RBAC, resource limits, image versions) cho phù hợp môi trường.

Check

```bash
kubectl -n kafka get deploy -l name=strimzi-cluster-operator
kubectl -n kafka logs deploy/strimzi-cluster-operator
```



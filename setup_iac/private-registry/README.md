# Private Docker Registry — README

Mục đích
- Cung cấp manifest để triển khai một private Docker registry trong cluster (ví dụ dùng cho dev hoặc CI caching).

Nội dung
- `deployment.yaml` — manifest triển khai registry (Deployment/Service/PVC). Có thể tuỳ chỉnh giá trị về storage, service type (ClusterIP/NodePort) và authentication.

Prerequisites
- Kubernetes cluster
- PVC/StorageClass (hoặc use emptyDir cho dev)

Triển khai

```bash
kubectl create ns registry || true
kubectl apply -f private-registry/deployment.yaml -n registry
```

Access
- Nếu Service là ClusterIP, dùng port-forward hoặc expose qua Ingress/NodePort để truy cập từ CI/host.

```bash
kubectl -n registry port-forward svc/registry 5000:5000
# push/pull: docker login localhost:5000
```

Authentication & TLS (production)
- KHÔNG chạy registry public mà không có authentication + TLS.
- Options:
  - Sử dụng basic auth (htpasswd) + TLS termination tại Ingress
  - Dùng certificate và registry tuỳ cấu hình
- Lưu credentials trong Kubernetes Secret hoặc external secret manager.

Vai trò trong CI
- Có thể dùng registry này để cache build images hoặc mirror để giảm latency cho runners.
- Cấu hình runner/docker daemon để sử dụng registry mirror.

Maintenance
- Dọn dẹp images cũ theo policy (garbage collect)
- Giám sát disk usage trên PVC

References
- Docker Registry docs: https://docs.docker.com/registry/

Notes
- Nếu bạn dùng một mirror registry cho CI trong cluster, cân nhắc cấu hình network và DNS để runners có thể resolve registry hostname.

# Strimzi Kafka Operator — hướng dẫn
Cấu hình cơ bản
- Thêm secret cho basic auth (nếu bật auth) hoặc cấu hình TLS cho registry.
- Sử dụng PersistentVolume để lưu layer images.

Sử dụng từ dev/CI
- Nếu registry chạy trong cluster, expose bằng NodePort/Ingress hoặc mirror registry.
- Cấu hình Docker daemon trong CI runner để push/pull image từ registry.

Bảo mật
- Không chạy registry public mà không có authentication + TLS.
- Lưu credentials trong secret manager; mount vào CI pipeline thông qua CI secrets.

Mục đích
- Hướng dẫn cách deploy Strimzi operator cho quản lý Kafka cluster trong Kubernetes.

Nội dung
- `values.yaml` - file cấu hình mẫu nếu bạn cài operator bằng Helm.

Triển khai
- Bằng Helm (khuyến nghị khi muốn parametrize):
# Kafka Connect Plugins — hướng dẫn đóng gói
```bash
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-cluster-operator strimzi/strimzi-kafka-operator -n kafka --create-namespace -f kafka/strimzi-kafka-operator/values.yaml
```

- Bằng manifest (nếu có sẵn trong repo):

```bash
kubectl apply -f kafka/strimzi-kafka-operator/manifests/  # nếu repo chứa manifests
```

Kiểm tra
```bash
kubectl -n kafka get deploy -l name=strimzi-cluster-operator
kubectl -n kafka logs deploy/strimzi-cluster-operator
```

Ghi chú
- Cài CRDs (xem `kafka/crds/`) trước khi deploy operator.
- Nếu deploy trên cluster production, bật TLS/RoleBindings và cấu hình RBAC phù hợp.

Mục đích
- Hướng dẫn cách tải và đóng gói connector plugin cho Kafka Connect (ví dụ: ClickHouse connector) thành 1 Docker image để triển khai vào Kubernetes.

Nội dung thư mục
- `Dockerfile` - mẫu Dockerfile để build image plugin
- `plugins-download.sh` - script tải các JAR cần thiết (cấu hình theo manifest)
- `clickhouse-kafka-connect-v1.3.4/` - ví dụ bundle plugin đã được tải sẵn

Quy trình build image
1. Kiểm tra/tuỳ chỉnh `plugins-download.sh` để chỉ định plugin & phiên bản.
2. Chạy script để tải các JAR vào thư mục `lib/` (hoặc sử dụng các JAR đã có sẵn trong thư mục ví dụ)

```bash
cd kafka/kafka-connect-plugins
./plugins-download.sh  # nếu script require args, xem nội dung script
```

3. Build image

```bash
# đặt TAG và registry phù hợp
docker build -t my-registry.local:5000/kafka-connect-plugins:clickhouse-v1.3.4 .
# push image
docker push my-registry.local:5000/kafka-connect-plugins:clickhouse-v1.3.4
```

4. Cập nhật manifest Kafka Connect hoặc Helm values để sử dụng image mới (image: my-registry...)

Ví dụ sử dụng với Strimzi Kafka Connect (CR):
- Sửa field `spec.image` hoặc `spec.template.pod.spec.containers.image` trong `kafka-connect.yaml` để tham chiếu image đã build.

Lưu ý
- Giữ kích thước image tối thiểu: chỉ đóng gói các JAR cần thiết.
- Quản lý phiên bản: ghi rõ manifest/manifest.json trong thư mục plugin để trace được phiên bản plugin.
- Nếu muốn, dùng multi-stage build để giảm kích thước image.

Debug
- Nếu connector không load plugin: kiểm tra logs của Kafka Connect pod, mount point và classpath.
- Kiểm tra nội dung jar trong image bằng cách run container và liệt kê thư mục plugin.

# CRDs cho Kafka / Strimzi

Mục đích
- Chứa các CustomResourceDefinition (CRD) mà Strimzi và các thành phần Kafka cần để hoạt động. CRDs phải được apply trước khi cài Strimzi operator hoặc trước khi tạo Kafka CRs.
# Kafka / Strimzi / Kafka Connect — README
Sử dụng
```bash
# áp dụng tất cả CRDs trong thư mục
kubectl apply -f kafka/crds/
```

Kiểm tra
```bash
kubectl get crd | grep kafka
# hoặc kiểm tra CRDs cụ thể
kubectl get crd kafkas.kafka.strimzi.io
```

Ghi chú
- Nếu dùng Helm để cài Strimzi, chart sẽ tự deploy CRDs; nhưng trong CI hoặc manual install bạn có thể apply trước để đảm bảo thứ tự.

Mục đích
- Hướng dẫn deploy Kafka (Strimzi operator), Kafka Connect (với plugin bundles) và Kafka UI trong cluster.

Thành phần chính
- `crds/` — chứa các CustomResourceDefinition cần apply trước khi cài operator/cluster.
- `kafka-cluster.yaml` — manifest CR (Kafka) để tạo cluster Kafka (số broker, storage, listeners...)
- `kafka-connect.yaml` — manifest CR cho Kafka Connect
- `kafka-connect-plugins/` — chứa Dockerfile và script để đóng gói connector plugin (ví dụ ClickHouse connector)
- `kafka-ui/` — cấu hình values cho Kafka UI
- `strimzi-kafka-operator/` — cấu hình operator (chứa `values.yaml` trong repo)

Triển khai (order)
1. Apply CRDs:

```bash
kubectl apply -f kafka/crds/
```

2. Cài Strimzi Operator
- Tùy chọn: dùng Helm chart chính thức hoặc apply manifests từ Strimzi release.

Ví dụ (manifest):
```bash
kubectl apply -f kafka/strimzi-kafka-operator/  # nếu bạn có manifest/operator yaml
```

Ví dụ (Helm):
```bash
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-cluster-operator strimzi/strimzi-kafka-operator -n kafka --create-namespace -f kafka/strimzi-kafka-operator/values.yaml
```

3. Tạo Kafka cluster

```bash
kubectl apply -f kafka/kafka-cluster.yaml -n kafka
```

4. Kafka Connect
- Build image plugin (nếu cần) — xem `kafka/kafka-connect-plugins/README.md`
- Apply Kafka Connect CR

```bash
kubectl apply -f kafka/kafka-connect.yaml -n kafka
```

5. Kafka UI
- Deploy bằng Helm hoặc manifests; sử dụng `kafka/kafka-ui/values.yaml` để cấu hình

```bash
helm upgrade --install kafka-ui <chart-name> -f kafka/kafka-ui/values.yaml -n kafka
```

Kafka Connect plugins (overview)
- Thư mục `kafka-connect-plugins/` bao gồm script `plugins-download.sh` và `Dockerfile` mẫu.
- Quy trình: chạy script để tải các JAR cần, build Docker image chứa plugin, push lên registry và tham chiếu image đó trong Kafka Connect deployment.

Logging & debugging
- Kiểm tra operator pod:

```bash
kubectl -n kafka get pods
kubectl -n kafka logs deploy/strimzi-cluster-operator
```

- Kiểm tra Kafka pods / Connect pods logs:

```bash
kubectl -n kafka get pods -l strimzi.io/name
kubectl -n kafka logs <pod>
```

Security
- TLS & authentication: Strimzi hỗ trợ mTLS cho listeners. Cấu hình trong `kafka-cluster.yaml`.
- Secrets: lưu các keystore/truststore/credentials trong Secret được mã hoá.

Tài liệu tham khảo
- Strimzi docs: https://strimzi.io/docs/
- Kafka Connect documentation

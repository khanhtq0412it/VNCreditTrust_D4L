# MinIO — Deployment on Kubernetes (Dev Setup)

Hướng dẫn này mô tả cách deploy **MinIO Operator** và một **MinIO Tenant** trên Kubernetes bằng Helm cho môi trường development.

Mục tiêu
- Cung cấp object storage tương thích S3
- UI Console để quản trị bucket
- Cấu hình nhẹ phù hợp cho môi trường dev

Prerequisites
- Kubernetes cluster
- kubectl
- Helm >= 3
- Một StorageClass mặc định (hoặc pre-provision PVs)

Kiểm tra cluster

```bash
kubectl get nodes
```

1) Add Helm repository

```bash
helm repo add minio https://charts.min.io/
helm repo update
```

2) Deploy MinIO Operator

```bash
helm install --namespace minio-operator --create-namespace minio-operator minio/operator
```

Kiểm tra pod:

```bash
kubectl get pods -n minio-operator
```

3) Deploy MinIO Tenant

File `tenant.yaml` trong thư mục chứa thông tin về số server, volumes và yêu cầu tài nguyên.

```bash
helm install --namespace tenant-ns --create-namespace tenant minio/tenant -f tenant.yaml
```

Kiểm tra pod:

```bash
kubectl get pods -n tenant-ns
```

4) Check Services

```bash
kubectl get svc -n tenant-ns
```

Ví dụ service:
- `minio-operator-console` = UI Console
- `minio` = S3 API

5) Truy cập MinIO Console UI (port-forward)

```bash
kubectl -n tenant-ns port-forward svc/minio-operator-console 9443:9443
# mở https://localhost:9443
```

6) Lấy username / password

```bash
kubectl get secret -n tenant-ns
# tìm secret tên minio-operator-console-secret
kubectl get secret minio-operator-console-secret -n tenant-ns -o jsonpath="{.data.username}" | base64 --decode
kubectl get secret minio-operator-console-secret -n tenant-ns -o jsonpath="{.data.password}" | base64 --decode
```

7) Truy cập S3 API (tuỳ chọn)

```bash
kubectl -n tenant-ns port-forward svc/minio 443:443
# endpoint: https://localhost
```

Cleanup

```bash
helm uninstall tenant -n tenant-ns
kubectl delete namespace tenant-ns
helm uninstall minio-operator -n minio-operator
kubectl delete namespace minio-operator
```

Notes
- Thư mục hiện chứa cấu hình dev (single server pool) — điều chỉnh cho production (mode distributed, số replicas, resources).
- TLS có thể được cấu hình tự động bởi operator.
- UI truy cập qua port-forward cho môi trường dev.

References
- MinIO operator helm chart: https://github.com/minio/operator/tree/master/helm/operator
- MinIO Kubernetes docs: https://min.io/docs/minio/kubernetes/upstream/index.html

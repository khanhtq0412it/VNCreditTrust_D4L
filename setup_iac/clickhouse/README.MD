# ClickHouse — Kubernetes manifests

Mục đích
- Cung cấp manifest để triển khai ClickHouse (một hoặc nhiều instance) trên Kubernetes cho môi trường dev/staging/prod.
- Cấu hình sẵn service, StatefulSet/Deployment, example cho NodePort, và cấu hình kết nối tới external storage (S3/MinIO) để backup hoặc sử dụng ExternalTable.

Nội dung thư mục
- `clickhouse.yaml` — manifest chính (Deployment/StatefulSet, Service, PVCs) để chạy ClickHouse.
- `clickhouse-nodeport.yaml` — Service dưới dạng NodePort (tiện cho truy cập local/dev).
- `clickhouse-external-storage.yaml` — ví dụ cấu hình để kết nối tới S3/MinIO (backup, external table).
- `secret.yaml` — ví dụ Secret (KHÔNG commit credential thật; dùng SOPS/SealedSecrets hoặc Secret Manager).

Prerequisites
- Kubernetes cluster (v1.20+)
- kubectl configured (kubeconfig)
- StorageClass hoặc PV được provisioned để bind PVC
- (Tuỳ môi trường) Helm hoặc ClickHouse operator nếu muốn quản lý bằng operator thay vì manifest thuần

Lưu ý về secrets
- Không commit plaintext secrets. Thay vào đó dùng SOPS/SealedSecrets hoặc external secret manager (Vault, AWS/GCP secret manager).

Nhiệm vụ/Contract (rút gọn)
- Inputs: các manifest trong thư mục và (tuỳ chọn) file `secret.yaml` chứa thông tin S3/credentials.
- Output: ClickHouse pod(s) chạy, Service accessible nội bộ cluster hoặc NodePort để truy cập local.
- Error modes: PVC không bind được, thiếu Secrets, resource limits quá thấp gây OOM/CrashLoop.

Triển khai nhanh (dev)
1. Tạo namespace (nếu cần):

```bash
kubectl create ns clickhouse || true
```

2. Tạo Secret (ví dụ) — thay bằng SOPS/SealedSecrets trong GitOps:

```bash
kubectl apply -f clickhouse/secret.yaml -n clickhouse
```

3. Tạo PersistentVolumeClaim / đảm bảo StorageClass sẵn sàng (nếu dùng dynamic provisioning thì PVC trong manifest sẽ bind tự động).

4. Deploy ClickHouse:

```bash
kubectl apply -f clickhouse/clickhouse.yaml -n clickhouse
# (tùy chọn) nếu muốn truy cập từ host/local
kubectl apply -f clickhouse/clickhouse-nodeport.yaml -n clickhouse
```

5. (Tuỳ chọn) Cấu hình external storage (S3/MinIO) cho backup hoặc external table:

```bash
kubectl apply -f clickhouse/clickhouse-external-storage.yaml -n clickhouse
```

Kiểm tra trạng thái

```bash
kubectl -n clickhouse get pods
kubectl -n clickhouse get pvc
kubectl -n clickhouse logs -l app=clickhouse --tail=200
```

Truy cập ClickHouse client (local trên pod)

```bash
# mở shell vào pod
kubectl -n clickhouse exec -it <clickhouse-pod> -- bash
# hoặc port-forward nếu cần
kubectl -n clickhouse port-forward svc/clickhouse 8123:8123
# truy cập HTTP API
curl http://localhost:8123/
```

External Storage (S3/MinIO)
- `clickhouse-external-storage.yaml` là ví dụ cấu hình sử dụng endpoint S3/MinIO cho backup và thao tác với external tables.
- Đảm bảo secret chứa accessKey/secretKey và endpoint đã được mount hoặc tham chiếu đúng trong config.

Backup & Restore
- ClickHouse hỗ trợ cấu hình backup sang S3/MinIO bằng công cụ hoặc thao tác COPY/ATTACH table. Tùy theo kiến trúc, bạn có thể sử dụng snapshot/backup theo scripts và lưu vào bucket được cấu hình trong `clickhouse-external-storage.yaml`.

Tuning và production notes
- Điều chỉnh `resources.requests/limits` theo workload.
- Sử dụng StatefulSet với PVC per pod cho stateful data.
- Thiết kế số partition và replica theo yêu cầu availability và throughput.
- Giám sát metrics (Prometheus exporter) và set alert cho CPU/IO/latency.

Troubleshooting
- PVC không bind: kiểm tra `kubectl get pvc -n clickhouse` và StorageClass.
- Pod CrashLoop: kiểm tra logs `kubectl -n clickhouse logs <pod>`; thường do cấu hình memory/CPU hay permission truy cập volume.
- Kết nối đến S3 lỗi: kiểm tra endpoint, credentials, và network policy/firewall.

Liên kết hữu ích
- ClickHouse docs: https://clickhouse.com/docs/en/
- ClickHouse Kubernetes Operator (nếu đổi sang operator): https://github.com/Altinity/clickhouse-operator

Ghi chú
- File example `secret.yaml` chỉ mang tính minh họa; thay bằng cách quản lý secret phù hợp cho production.

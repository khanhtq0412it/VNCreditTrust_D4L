# Kafka Connect Plugins — README

Mục đích
- Chứa Dockerfile và script để đóng gói connector plugins (JAR files) thành một Docker image dùng cho Kafka Connect.
- Ví dụ: ClickHouse connector bundle đã được đặt trong `clickhouse-kafka-connect-v1.3.4/`.

Thư mục & nội dung
- `Dockerfile` — mẫu Dockerfile để build image chứa plugin bundles.
- `plugins-download.sh` — script (nếu có) để tải các JAR cần thiết từ nguồn chính thức hoặc mirror.
- `<plugin-name>/` — thư mục ví dụ đã chứa manifest.json, docs và `lib/` chứa JARs.

Workflow — build & push image
1. Kiểm tra/tuỳ chỉnh `plugins-download.sh` để chọn plugin và phiên bản. Hoặc dùng JAR có sẵn trong thư mục plugin.

2. Chạy script nếu cần để tạo thư mục `lib/` với các JAR:

```bash
cd kafka/kafka-connect-plugins
./plugins-download.sh
```

3. Build Docker image (edit TAG và registry theo môi trường):

```bash
docker build -t my-registry.local:5000/kafka-connect-plugins:clickhouse-v1.3.4 .
# hoặc nếu Dockerfile ở trong plugin subfolder
docker build -t my-registry.local:5000/kafka-connect-plugins:clickhouse-v1.3.4 clickhouse-kafka-connect-v1.3.4/
```

4. Push image lên registry (private registry hoặc Docker Hub):

```bash
docker push my-registry.local:5000/kafka-connect-plugins:clickhouse-v1.3.4
```

5. Cập nhật Kafka Connect CR/Deployment để sử dụng image mới (field `spec.image` hoặc trong `podTemplate`).

Best practices
- Chỉ đóng gói các JAR cần thiết để giảm kích thước image.
- Ghi rõ phiên bản plugin trong `manifest.json` hoặc tên image tag.
- Dùng multi-stage build để giảm kích thước cuối cùng.
- Test locally bằng cách chạy Kafka Connect container và kiểm tra classpath / plugin path.

Debug
- Nếu connector không load: kiểm tra logs của Kafka Connect pod để xem classpath hoặc lỗi ClassNotFound.
- Exec vào pod/container để liệt kê thư mục plugin và xác thực JARs:

```bash
kubectl -n kafka exec -it <connect-pod> -- ls -la /opt/kafka/plugins
kubectl -n kafka logs <connect-pod>
```

References
- Kafka Connect plugin packaging: https://kafka.apache.org/documentation/#connect_plugins



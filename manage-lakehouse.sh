#!/bin/bash
# Local Lakehouse Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ==========================================
# CÁC HÀM QUẢN LÝ HỆ THỐNG
# ==========================================

# Lệnh mới: Đóng gói lại môi trường khi có thay đổi requirements hoặc Dockerfile
build_images() {
    echo "Đang Build lại môi trường (Airflow, dbt & Spark)..."
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose-airflow.yaml build
    docker compose -f docker-compose-spark.yaml build
    echo "Build hoàn tất! Môi trường đã nạp đủ các thư viện mới."
}

start_services() {
    echo "Đang khởi động hệ thống Data Lakehouse..."
    cd "$SCRIPT_DIR"
    
    echo "0. Tạo mạng Docker (nếu chưa có)..."
    docker network create lakehouse-net || true
    
    echo "1. Bật Tầng Lưu trữ & Catalog (MinIO + Nessie)..."
        docker compose -f docker-compose-lake.yaml up -d
    sleep 5
    
    echo "2. Bật Động cơ Truy vấn (Trino)..."
    docker compose -f docker-compose-trino.yaml up -d

    echo "3. Bật Cụm Xử lý Lớn (Spark Cluster)..."
    docker compose -f docker-compose-spark.yaml up --build -d
    sleep 5

    echo "  -> Bật Hệ thống Giám sát (Prometheus & Grafana)..."
    docker compose -f docker-compose-monitoring.yaml up -d
    
    echo "4. Bật Hệ thống Điều phối (Airflow)..."
    # Thêm --build để chắc chắn nó luôn dùng image mới nhất nếu có thay đổi
    docker compose -f docker-compose-airflow.yaml up -d
    sleep 5
    
    echo "Tất cả dịch vụ đã Online!"
    echo "========================================"
    echo "  - MinIO Console   : http://localhost:9001 (admin/password123)"
    echo "  - Trino Web UI    : http://localhost:8082"
    echo "  - Spark Master UI : http://localhost:8083"
    echo "  - Airflow UI      : http://localhost:8081 (airflow/airflow)"
    echo "  - Nessie API      : http://localhost:19120"
    echo "========================================"

    init_trino
}

init_trino() {
    echo "Đang khởi tạo các Schema mặc định cho Trino..."
    docker exec -it trino-coordinator trino --catalog iceberg --file /etc/trino/init.sql || echo "Bỏ qua khởi tạo Schema tự động."
}

load_dbt_seed_data() {
    echo "Đang nạp dữ liệu Seed từ CSV lên Lakehouse..."
    docker exec -it airflow-worker /bin/bash -c "/opt/airflow/dbt_venv/bin/dbt seed --project-dir /opt/airflow/dbt_trino --profiles-dir /opt/airflow/dbt_trino"
    echo "Hoàn tất nạp dữ liệu Seed!"
}

# Tắt an toàn: Giữ lại toàn bộ dữ liệu Logistics và dọn dẹp Orphans
stop_services() {
    echo "Đang tắt hệ thống và dọn dẹp tàn dư (Dữ liệu vẫn được giữ lại an toàn)..."
    cd "$SCRIPT_DIR"
    
    docker compose -f docker-compose-airflow.yaml down --remove-orphans
    docker compose -f docker-compose-spark.yaml down --remove-orphans
    docker compose -f docker-compose-trino.yaml down --remove-orphans
    docker compose -f docker-compose-monitoring.yaml down --remove-orphans
    docker compose -f docker-compose-lake.yaml down --remove-orphans
    
    echo "Hệ thống đã tắt an toàn."
}

# Dọn dẹp cache và mạng lỗi (Không chạm vào Data)
clean_system() {
    echo "Đang dọn dẹp cache, networks lỗi và rác hệ thống..."
    stop_services
    docker system prune -f
    echo "Đã dọn dẹp sạch sẽ môi trường Docker!"
}

# Lệnh nguy hiểm: Đập đi xây lại từ đầu
destroy_services() {
    echo "CẢNH BÁO: Đang xóa toàn bộ container và DỮ LIỆU VOLUMES..."
    cd "$SCRIPT_DIR"
    
    docker compose -f docker-compose-airflow.yaml down -v --remove-orphans
    docker compose -f docker-compose-spark.yaml down -v --remove-orphans
    docker compose -f docker-compose-trino.yaml down -v --remove-orphans
    docker compose -f docker-compose-monitoring.yaml down -v --remove-orphans
    docker compose -f docker-compose-lake.yaml down -v --remove-orphans
    
    echo "Đã xóa sạch hệ thống."
}

# ==========================================
# ĐIỀU HƯỚNG LỆNH (MENU)
# ==========================================

case "${1:-help}" in
    "start")   start_services ;;
    "stop")    stop_services ;;
    "destroy") destroy_services ;;
    "clean")   clean_system ;;
    "seed")    load_dbt_seed_data ;;
    "build")   build_images ;;
    *)
        echo "Cách sử dụng: $0 [start|stop|destroy|clean|seed|build]"
        echo ""
        echo "  start   - Bật toàn bộ hệ thống Lakehouse (MinIO, Trino, Spark, Airflow...)"
        echo "  stop    - Tắt an toàn (Giữ lại dữ liệu MinIO, Postgres)"
        echo "  build   - Build lại môi trường khi có thay đổi trong requirements.txt"
        echo "  clean   - Dọn rác Docker hệ thống (An toàn cho data)"
        echo "  destroy - Xóa sạch hệ thống và dữ liệu (CẨN THẬN)"
        echo "  seed    - Nạp file CSV từ dbt vào Trino"
        ;;
esac
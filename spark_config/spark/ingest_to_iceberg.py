import argparse
import sys

# Import các công cụ từ thư mục utils
# (Lưu ý: Nếu bạn mount utils vào dags/utils thì sửa lại thành dags.utils.xxx nhé)
from dags.utils.config import settings
from dags.utils.spark_manager import get_or_create_spark_session
from dags.utils.nessie_manager import switch_to_branch
from dags.utils.spark_etl import LakehouseELT  

# ==============================================================================
# 1. NHẬN THAM SỐ TỪ AIRFLOW
# ==============================================================================
parser = argparse.ArgumentParser()
parser.add_argument('--schema', required=True)
parser.add_argument('--table', required=True)
args = parser.parse_args()

PG_SCHEMA = args.schema
TABLE_NAME = args.table

print(f"🚀 Bắt đầu tiến trình Ingest {PG_SCHEMA}.{TABLE_NAME} bằng Spark + Iceberg")

# ==============================================================================
# 2. KHỞI TẠO SPARK VÀ LAKEHOUSE ELT
# ==============================================================================
# Lấy Spark Session
spark = get_or_create_spark_session(f"Ingest_{PG_SCHEMA}_{TABLE_NAME}")

# Đảm bảo làm việc trên nhánh main của Nessie (Đã cấu hình sẵn trong ref="main" ở config.py)
# switch_to_branch(spark, "main")

# Khởi tạo cỗ máy ELT mà chúng ta vừa viết
elt = LakehouseELT(spark=spark, settings=settings)

# ==============================================================================
# 3. THỰC THI CHUYỂN DỮ LIỆU (Chỉ cần 1 lệnh duy nhất)
# ==============================================================================
# Phân luồng thông minh: Nếu bảng lớn, ta có thể dùng biến môi trường hoặc logic riêng 
# (Tạm thời cứ dùng hàm extract chuẩn đã viết trong class)

elt.extract_postgres_to_iceberg(
    pg_schema=PG_SCHEMA, 
    pg_table=TABLE_NAME, 
    target_namespace="landing"
)

print(f"✅ Tiến trình hoàn tất!")
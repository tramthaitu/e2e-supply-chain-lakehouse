from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os

class LakehouseELT:
    """
    Class quản lý luồng ELT chuẩn Lakehouse sử dụng Spark và Apache Iceberg.
    Đảm bảo tính chất ACID, Schema Evolution và Time Travel.
    """

    def __init__(self, spark: SparkSession, settings):
        self.spark = spark
        self.settings = settings
        self.jdbc_url = f"jdbc:postgresql://{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}"
        self.pg_properties = {
            "user": settings.PG_USER,
            "password": settings.PG_PASSWORD,
            "driver": "org.postgresql.Driver"
        }

    # ==========================================
    # 1. ĐỌC DỮ LIỆU (TỪ POSTGRES VÀO SPARK)
    # ==========================================
    def read_postgres_table(self, table_name: str, schema_name: str = "public"):
        """Đọc bảng từ Postgres vào Spark DataFrame"""
        return self.spark.read \
            .jdbc(url=self.jdbc_url, 
                  table=f"{schema_name}.{table_name}", 
                  properties=self.pg_properties)

    # ==========================================
    # 2. GHI DỮ LIỆU VÀO POSTGRES (Dùng Spark)
    # ==========================================
    def load_csv_to_postgres(self, file_path: str, schema_name: str, table_name: str, mode: str = "overwrite"):
        """
        Dùng Spark đọc CSV siêu tốc và đẩy vào Postgres.
        mode: 'overwrite' (ghi đè), 'append' (thêm vào)
        """
        if not os.path.exists(file_path):
            print(f"⚠️ Bỏ qua: Không tìm thấy file {file_path}")
            return

        print(f"⏳ Đang nạp CSV {file_path} vào Postgres bảng {schema_name}.{table_name}...")
        
        # Đọc CSV bằng Spark
        df = self.spark.read.csv(file_path, header=True, inferSchema=True)
        
        # Ghi vào Postgres
        df.write.jdbc(
            url=self.jdbc_url,
            table=f"{schema_name}.{table_name}",
            mode=mode,
            properties=self.pg_properties
        )
        print(f"✅ Đã nạp {df.count()} dòng vào Postgres.")

    # ==========================================
    # 3. CORE LAKEHOUSE: CHUYỂN POSTGRES -> ICEBERG
    # ==========================================
    def extract_postgres_to_iceberg(self, pg_schema: str, pg_table: str, target_namespace: str = "landing"):
        """
        [LAKEHOUSE CHUẨN] Ingest dữ liệu và tự động tạo bảng Iceberg.
        Có lưu trữ Metadata để theo dõi lịch sử (Time Travel).
        """
        print(f"🚀 Bắt đầu stream bảng {pg_schema}.{pg_table} sang Lakehouse...")
        
        # Đọc từ Postgres
        df = self.read_postgres_table(table_name=pg_table, schema_name=pg_schema)
        
        # Tên bảng đích trên Nessie/Iceberg
        target_table = f"iceberg.{target_namespace}.{pg_schema}_{pg_table}"
        
        # Ghi đè an toàn (Iceberg sẽ tạo snapshot mới chứ không xóa file vật lý cũ ngay lập tức)
        df.write \
            .format("iceberg") \
            .mode("overwrite") \
            .saveAsTable(target_table)
            
        print(f"🎯 Đã lưu thành công Iceberg Table: {target_table}")

    # ==========================================
    # 4. SUPERPOWER: LAKEHOUSE UPSERT (MERGE)
    # ==========================================
    def upsert_postgres_to_iceberg(self, pg_schema: str, pg_table: str, target_namespace: str, primary_key: str):
        """
        ĐÂY LÀ SỨC MẠNH CỦA LAKEHOUSE MÀ DUCKDB/PARQUET KHÔNG LÀM ĐƯỢC.
        Chỉ cập nhật những dòng thay đổi hoặc chèn dòng mới (Upsert/Merge).
        """
        print(f"🔄 Đang Upsert (Merge) bảng {pg_table} vào Lakehouse...")
        
        source_df = self.read_postgres_table(table_name=pg_table, schema_name=pg_schema)
        target_table = f"iceberg.{target_namespace}.{pg_schema}_{pg_table}"
        
        # Tạo view tạm cho bảng nguồn
        source_df.createOrReplaceTempView("source_updates")
        
        # Thực hiện câu lệnh SQL MERGE của Iceberg
        merge_sql = f"""
            MERGE INTO {target_table} t
            USING source_updates s
            ON t.{primary_key} = s.{primary_key}
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """
        self.spark.sql(merge_sql)
        print(f"✅ Đã Upsert thành công dữ liệu mới vào {target_table}.")
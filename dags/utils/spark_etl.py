from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os

class LakehouseELT:
    """
    Class quản lý luồng ELT chuẩn Lakehouse sử dụng Spark và Apache Iceberg.
    Chỉ chạy bên trong Container Spark, phục vụ việc Ingest và Upsert dữ liệu.
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

    def read_postgres_table(self, table_name: str, schema_name: str = "public"):
        """Đọc bảng từ Postgres vào Spark DataFrame"""
        return self.spark.read \
            .jdbc(url=self.jdbc_url, 
                  table=f"{schema_name}.{table_name}", 
                  properties=self.pg_properties)

    def extract_postgres_to_iceberg(self, pg_schema: str, pg_table: str, target_namespace: str = "landing"):
        """[LAKEHOUSE CHUẨN] Ingest dữ liệu thô từ Postgres sang bảng Iceberg."""
        print(f"🚀 Bắt đầu stream bảng {pg_schema}.{pg_table} sang Lakehouse...")
        
        self.spark.sql(f"CREATE NAMESPACE IF NOT EXISTS iceberg.{target_namespace}")
        
        df = self.read_postgres_table(table_name=pg_table, schema_name=pg_schema)
        target_table = f"iceberg.{target_namespace}.{pg_schema}_{pg_table}"
        
        df.write \
            .format("iceberg") \
            .mode("overwrite") \
            .saveAsTable(target_table)
            
        print(f"🎯 Đã lưu thành công Iceberg Table: {target_table}")

    def upsert_postgres_to_iceberg(self, pg_schema: str, pg_table: str, target_namespace: str, primary_key: str):
        """Lakehouse MERGE (Upsert) - Cập nhật dòng thay đổi, chèn dòng mới."""
        print(f"🔄 Đang Upsert (Merge) bảng {pg_table} vào Lakehouse...")
        
        self.spark.sql(f"CREATE NAMESPACE IF NOT EXISTS iceberg.{target_namespace}")
        
        source_df = self.read_postgres_table(table_name=pg_table, schema_name=pg_schema)
        target_table = f"iceberg.{target_namespace}.{pg_schema}_{pg_table}"
        
        source_df.createOrReplaceTempView("source_updates")
        
        merge_sql = f"""
            MERGE INTO {target_table} t
            USING source_updates s
            ON t.{primary_key} = s.{primary_key}
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """
        self.spark.sql(merge_sql)
        print(f"✅ Đã Upsert thành công dữ liệu mới vào {target_table}.")
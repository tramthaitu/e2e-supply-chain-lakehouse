from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(interpolate=True)

class Settings(BaseSettings):
    # --- PostgreSQL Source Settings ---
    PG_HOST: str = "postgres-source"
    PG_PORT: str = "5432"
    PG_DATABASE: str = "supply_chain_db"
    PG_USER: str = "admin"
    PG_PASSWORD: str = "admin_password"

    # --- MinIO & Nessie Core Settings ---
    MINIO_ROOT_USER: str = "admin"
    MINIO_ROOT_PASSWORD: str = "password123"
    MINIO_REGION: str = "us-east-1"
    AWS_S3_ENDPOINT: str = "http://minio:9000"
    WAREHOUSE: str = "s3://local-lakehouse"
    NESSIE_URI: str = "http://nessie-catalog:19120/api/v1"

    # --- Spark Auto-Parsed Settings ---
    # Quy tắc: _ sẽ thành . và __ sẽ thành - trong spark_manager.py
    SPARK_MASTER: str = "spark://spark-master:7077"
    
    spark_jars: str = "/opt/spark/custom_jars/"
    spark_sql_extensions: str = "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions"
    
    # Cấu hình Catalog Iceberg (Dùng chuẩn duy nhất S3FileIO + AWS SDK v2)
    spark_sql_catalog_iceberg: str = "org.apache.iceberg.spark.SparkCatalog"
    spark_sql_catalog_iceberg_catalog__impl: str = "org.apache.iceberg.nessie.NessieCatalog"
    spark_sql_catalog_iceberg_uri: str = "http://nessie-catalog:19120/api/v1"
    spark_sql_catalog_iceberg_ref: str = "main"
    spark_sql_catalog_iceberg_authentication_type: str = "NONE"
    spark_sql_catalog_iceberg_warehouse: str = "s3://local-lakehouse"
    spark_sql_catalog_iceberg_s3_endpoint: str = "http://minio:9000"
    spark_sql_catalog_iceberg_io__impl: str = "org.apache.iceberg.aws.s3.S3FileIO"
    spark_sql_catalog_iceberg_client_region: str = "us-east-1"
    spark_sql_catalog_iceberg_s3_access__key__id: str = "admin"
    spark_sql_catalog_iceberg_s3_secret__access__key: str = "password123"
    spark_sql_catalog_iceberg_s3_path__style__access: str = "true"

    # Cấu hình tối ưu tài nguyên
    spark_executor_memory: str = "1g"
    spark_driver_memory: str = "1g"
    spark_executor_cores: str = "1"
    spark_sql_iceberg_merge_schema: str = "true"
    spark_executor_extraJavaOptions: str = "-Daws.region=us-east-1"
    spark_driver_extraJavaOptions: str = "-Daws.region=us-east-1"
    
    class Config:
        env_file = "./.env"
        case_sensitive = True

settings = Settings()
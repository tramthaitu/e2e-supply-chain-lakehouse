# File: dags/dag_ingest_landing.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
from utils.docker_wrappers import DockerTasksClass  

# ================= 1. CẤU HÌNH BIẾN & HỆ THỐNG =================
DATA_DIR = "/opt/airflow/data_source"

SCHEMA_MAPPING = {
    'master_data': ['products.csv', 'customers.csv', 'promotions.csv', 'geography.csv'],
    'sales': ['orders.csv', 'order_items.csv', 'payments.csv', 'returns.csv', 'sales.csv'],
    'supply_chain': ['shipments.csv', 'inventory.csv'],
    'marketing': ['reviews.csv', 'web_traffic.csv']
}

# KHÔNG KHỞI TẠO db_client Ở ĐÂY ĐỂ TRÁNH LỖI DAGBAG TIMEOUT
def get_db_client():
    from utils.postgres_etl import PostgresLakehouseClient
    """Hàm khởi tạo Client - Chỉ chạy khi Task thực sự được kích hoạt"""
    return PostgresLakehouseClient(
        pg_host="postgres-source",
        pg_port="5432",
        pg_user="admin",
        pg_password="admin_password",
        pg_database="supply_chain_db"
    )

# Khởi tạo Class Docker để gọi Spark (An toàn khi để ở top-level vì không gọi network)
docker_task = DockerTasksClass(
    dbt_image="dbt_runner:latest",
    spark_image="custom-spark-lakehouse:latest",
    dbt_host_path="/mnt/c/E2E-Lakehouse-SupplyChain/dbt_trino",
    pyspark_host_path="/mnt/c/E2E-Lakehouse-SupplyChain/spark_config/spark",
    network_mode="lakehouse-net",
    bot_notice=None
)

# ================= 2. HÀM WRAPPER CHO PYTHON OPERATOR =================
def init_pg_schemas():
    client = get_db_client() 
    client.create_postgres_schemas(list(SCHEMA_MAPPING.keys()))

def load_csv_wrapper(schema: str, file_name: str):
    client = get_db_client() # Gọi lazy load
    file_path = os.path.join(DATA_DIR, file_name)
    table_name = file_name.replace('.csv', '')
    client.load_csv_to_postgres(file_path, schema, table_name)


# ================= 3. ĐỊNH NGHĨA DAG =================
default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='01_pipeline_ingest_landing_spark_iceberg',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    max_active_tasks=2, # 2 task Spark song song - an toàn sau khi nâng WSL2 lên 10GB/10 cores
    tags=['ingestion', 'spark', 'iceberg', 'postgres', 'polars'],
) as dag:

    # Task 1: Khởi tạo Schema trên Postgres
    task_init_schemas = PythonOperator(
        task_id='init_postgres_schemas',
        python_callable=init_pg_schemas
    )

    # Vòng lặp sinh Task động
    for schema, files in SCHEMA_MAPPING.items():
        for file_name in files:
            table_name = file_name.replace('.csv', '')

            # Task 2: Polars nạp CSV -> Postgres
            task_load_pg = PythonOperator(
                task_id=f'csv_to_pg_{schema}_{table_name}',
                python_callable=load_csv_wrapper,
                op_kwargs={'schema': schema, 'file_name': file_name}
            )

            # Task 3: Spark rút Postgres -> MinIO (Iceberg)
            script_args = f"ingest_to_iceberg.py --schema {schema} --table {table_name}"
            
            task_spark_ingest = docker_task.run_spark_task(
                task_id=f'spark_ingest_{schema}_{table_name}',
                spark_script=script_args,
                dag=dag
            )

            # Thiết lập thứ tự chạy
            task_init_schemas >> task_load_pg >> task_spark_ingest
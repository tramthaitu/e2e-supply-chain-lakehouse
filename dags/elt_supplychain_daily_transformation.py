# File: dags/elt_supplychain_daily_transformation.py
from airflow import DAG
from datetime import datetime, timedelta
from utils.docker_wrappers import DockerTasksClass
from utils.telegram_bot import TelegramBotNotice

# Khởi tạo Telegram Bot Notice để nhận cảnh báo qua điện thoại
bot_notice = TelegramBotNotice()

# Khởi tạo Class Docker để gọi dbt runner
docker_task = DockerTasksClass(
    dbt_image="dbt_runner:latest",
    spark_image="custom-spark-lakehouse:latest",
    dbt_host_path="/mnt/c/E2E-Lakehouse-SupplyChain/dbt_trino",
    pyspark_host_path="/mnt/c/E2E-Lakehouse-SupplyChain/spark_config/spark",
    network_mode="lakehouse-net",
    bot_notice=bot_notice
)

default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='elt_supplychain_daily_transformation',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule='0 1 * * *', # Chạy tự động lúc 1:00 sáng hàng ngày (sau khi nạp Spark xong)
    catchup=False,
    max_active_tasks=1,
    tags=['daily', 'Iceberg', 'Marts', 'dbt', 'Trino'],
) as dag:

    # Kiểm thử chất lượng tầng nguồn Bronze (Source Landing Tests)
    task_dbt_test_sources = docker_task.run_dbt_test_task(
        task_id='dbt_test_source_landing',
        selector='source:landing', # Chạy 2 custom test vừa gắn ở sources.yml
        target='prod',
        dag=dag
    )

    # Chụp lịch sử SCD Type 2 (khách hàng đổi địa chỉ, sản phẩm đổi giá)
    task_dbt_snapshot = docker_task.run_dbt_snapshot_task(
        task_id='dbt_snapshot_scd_type_2',
        target='prod',
        dag=dag
    )

    # Chạy tầng Staging (Làm sạch và chuẩn hóa kiểu dữ liệu)
    task_dbt_run_staging = docker_task.run_dbt_task(
        task_id='dbt_run_layer_staging',
        selector='staging',
        target='prod',
        dag=dag
    )

    # Kiểm thử chất lượng tầng Staging trước khi tính toán
    task_dbt_test_staging = docker_task.run_dbt_test_task(
        task_id='dbt_test_layer_staging',
        selector='staging',
        target='prod',
        dag=dag
    )

    # Chạy tầng Intermediate (Tính toán trung gian, giảm giá đơn hàng)
    task_dbt_run_intermediate = docker_task.run_dbt_task(
        task_id='dbt_run_layer_intermediate',
        selector='intermediate',
        target='prod',
        dag=dag
    )

    # Kiểm thử chất lượng tầng Intermediate
    task_dbt_test_intermediate = docker_task.run_dbt_test_task(
        task_id='dbt_test_layer_intermediate',
        selector='intermediate',
        target='prod',
        dag=dag
    )

    # Chạy tầng Marts - Bảng Chiều (Dimensions)
    task_dbt_run_marts_dim = docker_task.run_dbt_task(
        task_id='dbt_run_marts_dimensions',
        selector='dim',
        target='prod',
        dag=dag
    )

    # Chạy tầng Marts - Bảng Sự Kiện (Facts CDC Incremental)
    task_dbt_run_marts_fact = docker_task.run_dbt_task(
        task_id='dbt_run_marts_facts_cdc',
        selector='fact',
        target='prod',
        dag=dag
    )

    # Chạy tầng Báo cáo Điều hành (Daily Reports)
    task_dbt_run_daily_reports = docker_task.run_dbt_task(
        task_id='dbt_run_daily_reports',
        selector='daily_reports',
        target='prod',
        dag=dag
    )

    # Kiểm thử chất lượng tầng Vàng Gold (Marts & Reports Tests) trước khi lên Power BI
    task_dbt_test_marts = docker_task.run_dbt_test_task(
        task_id='dbt_test_marts_and_reports',
        selector='marts', # Chạy test cho dim, fact, daily_reports
        target='prod',
        dag=dag
    )

    # Thiết lập chuỗi chu trình "Write-Audit-Publish" đan xen Test cực kỳ chặt chẽ:
    (
        task_dbt_test_sources 
        >> task_dbt_snapshot 
        >> task_dbt_run_staging 
        >> task_dbt_test_staging 
        >> task_dbt_run_intermediate 
        >> task_dbt_test_intermediate 
        >> task_dbt_run_marts_dim 
        >> task_dbt_run_marts_fact 
        >> task_dbt_run_daily_reports 
        >> task_dbt_test_marts
    )

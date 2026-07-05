from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from typing import Optional
from datetime import timedelta
import os

class DockerTasksClass:
    """
    Docker tasks cho dbt (Isolated Container) & Spark trên nền tảng Local Lakehouse
    """

    def __init__(
        self,
        *,
        dbt_image: str = "dbt_runner:latest",
        spark_image: str = "custom-spark-lakehouse:latest", # Đã sửa thành custom image
        dbt_host_path: str,
        pyspark_host_path: str,
        bot_notice=None,
        docker_url: str = "unix://var/run/docker.sock",
        network_mode: str = "lakehouse-net", # ĐÃ SỬA: Dùng mạng Lakehouse
        mount_tmp_dir: bool = False,
    ) -> None:
        self.dbt_image = dbt_image
        self.spark_image = spark_image
        self.dbt_host_path = dbt_host_path
        self.pyspark_host_path = pyspark_host_path
        self.bot_notice = bot_notice
        self.docker_url = docker_url
        self.network_mode = network_mode
        self.mount_tmp_dir = mount_tmp_dir

        # Container constants
        self.dbt_dir = "/usr/app/dbt"         # Đường dẫn làm việc bên trong dbt container
        self.dbt_airflow_path = "/opt/airflow/dbt_trino"  # Đường dẫn thư mục dbt trong Airflow
        self.spark_app_dir = "/opt/app"       # Đường dẫn chứa code pyspark bên trong container

        print(" ------ class DockerTasksClass for Lakehouse was created!")

    # =========================
    # DBT TASKS (Chạy qua DockerOperator rất chuẩn)
    # =========================
    def run_dbt_task(self, *, task_id: str, selector: str, target: str = "dev", dag: Optional[DAG] = None):
        cmd = f"""
    set -e
    dbt deps --project-dir {self.dbt_dir}
    dbt run -s {selector} --project-dir {self.dbt_dir} --target {target} --fail-fast
    """
        return DockerOperator(
            task_id=task_id,
            image=self.dbt_image,
            api_version="auto",
            auto_remove="force",
            command=["bash", "-lc", cmd],
            docker_url=self.docker_url,
            network_mode=self.network_mode,
            working_dir=self.dbt_dir,
            mount_tmp_dir=self.mount_tmp_dir,
            mounts=[
                Mount(source=self.dbt_host_path, target=self.dbt_dir, type="bind"),
            ],
            on_execute_callback=(self.bot_notice.notify_task_start if self.bot_notice else None),
            on_success_callback=(self.bot_notice.notify_task_success if self.bot_notice else None),
            on_failure_callback=(self.bot_notice.notify_telegram_when_fail if self.bot_notice else None),
            dag=dag,
        )

    def run_dbt_freshness_task(self, *, task_id: str, selector: str, target: str = "dev", dag: Optional[DAG] = None):
        cmd = f"""
    set -e
    dbt deps --project-dir {self.dbt_dir}
    dbt source freshness --select {selector} --project-dir {self.dbt_dir} --target {target} --no-partial-parse
        """
        return DockerOperator(
            task_id=task_id,
            image=self.dbt_image,
            api_version="auto",
            auto_remove="force",
            command=["bash", "-lc", cmd],
            docker_url=self.docker_url,
            network_mode=self.network_mode,
            working_dir=self.dbt_dir,
            mount_tmp_dir=self.mount_tmp_dir,
            mounts=[Mount(source=self.dbt_host_path, target=self.dbt_dir, type="bind")],
            on_success_callback=(
                lambda ctx, _path=self.dbt_airflow_path: self.bot_notice.notify_dbt_completed(ctx, dbt_path=_path, mode="freshness")
                if self.bot_notice else None
            ),
            on_failure_callback=(self.bot_notice.notify_telegram_when_fail if self.bot_notice else None),
            dag=dag,
        )

    def run_dbt_test_task(self, *, task_id: str, selector: str, target: str = "dev", dag: Optional[DAG] = None):
        cmd = f"""
    set -e
    dbt deps --project-dir {self.dbt_dir}
    dbt test -s {selector} --project-dir {self.dbt_dir} --target {target}
        """
        return DockerOperator(
            task_id=task_id,
            image=self.dbt_image,
            api_version="auto",
            auto_remove="force",
            command=["bash", "-lc", cmd],
            docker_url=self.docker_url,
            network_mode=self.network_mode,
            working_dir=self.dbt_dir,
            mount_tmp_dir=self.mount_tmp_dir,
            mounts=[Mount(source=self.dbt_host_path, target=self.dbt_dir, type="bind")],
            on_execute_callback=(self.bot_notice.notify_task_start if self.bot_notice else None),
            on_success_callback=(
                lambda ctx, _path=self.dbt_airflow_path: self.bot_notice.notify_dbt_completed(ctx, dbt_path=_path, mode="test")
                if self.bot_notice else None
            ),
            on_failure_callback=(self.bot_notice.notify_telegram_when_fail if self.bot_notice else None),
            dag=dag,
        )

    def run_dbt_snapshot_task(self, *, task_id: str, target: str = "prod", dag: Optional[DAG] = None):
        cmd = f"""
    set -e
    dbt deps --project-dir {self.dbt_dir}
    dbt snapshot --project-dir {self.dbt_dir} --target {target}
        """
        return DockerOperator(
            task_id=task_id,
            image=self.dbt_image,
            api_version="auto",
            auto_remove="force",
            command=["bash", "-lc", cmd],
            docker_url=self.docker_url,
            network_mode=self.network_mode,
            working_dir=self.dbt_dir,
            mount_tmp_dir=self.mount_tmp_dir,
            mounts=[Mount(source=self.dbt_host_path, target=self.dbt_dir, type="bind")],
            on_execute_callback=(self.bot_notice.notify_task_start if self.bot_notice else None),
            on_success_callback=(self.bot_notice.notify_task_success if self.bot_notice else None),
            on_failure_callback=(self.bot_notice.notify_telegram_when_fail if self.bot_notice else None),
            dag=dag,
        )

    # =========================
    # SPARK TASKS
    # =========================
    def run_spark_task(self, *, task_id: str, spark_script: str, dag: Optional[DAG] = None, tz: str = "Asia/Ho_Chi_Minh"):
        
        # ĐÃ SỬA: Lệnh sạch sẽ, không có --conf, chỉ trỏ đúng đường dẫn tuyệt đối của spark-submit
        cmd = f"""
    set -e
    export PYTHONPATH=$PYTHONPATH:/opt/airflow:/opt/airflow/dags
    /opt/spark/bin/spark-submit --master spark://spark-master:7077 {self.spark_app_dir}/{spark_script}
        """
        
        # ĐÃ SỬA: Neo đường dẫn gốc chứa Jars ở máy vật lý
        default_jars_path ="/mnt/c/E2E-Lakehouse-SupplyChain/spark_config/jars"
        host_jars_path = os.getenv("HOST_SPARK_JARS_PATH", default_jars_path)

        return DockerOperator(
            task_id=task_id,
            image=self.spark_image,
            api_version="auto",
            auto_remove="force",
            command=["bash", "-lc", cmd],
            docker_url=self.docker_url,
            network_mode=self.network_mode,
            mount_tmp_dir=self.mount_tmp_dir,
            mounts=[
                Mount(source=self.pyspark_host_path, target=self.spark_app_dir, type="bind"),
                Mount(source=host_jars_path, target="/opt/spark/custom_jars", type="bind"),
                Mount(source="/mnt/c/E2E-Lakehouse-SupplyChain/dags", target="/opt/airflow/dags", type="bind")
            ],
            environment={
                "TZ": tz,
                "AWS_REGION": "us-east-1",
                "AWS_ACCESS_KEY_ID": "admin",
                "AWS_SECRET_ACCESS_KEY": "password123",
            },
            on_execute_callback=(self.bot_notice.notify_task_start if self.bot_notice else None),
            on_success_callback=(self.bot_notice.notify_task_success if self.bot_notice else None),
            on_failure_callback=(self.bot_notice.notify_telegram_when_fail if self.bot_notice else None),
            execution_timeout=timedelta(minutes=30),
            dag=dag,
        )
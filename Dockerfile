FROM apache/airflow:3.0.6

# =================================================================
# 1. CÀI ĐẶT JAVA & CÔNG CỤ HỆ THỐNG (BẮT BUỘC CHO SPARK)
# =================================================================
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    procps \
    curl \
    gcc \
    g++ \
    make \
    libc-dev \
    python3-dev \
 && apt-get autoremove -yqq --purge \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Cấu hình Java cho Windows/Intel/AMD
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# =================================================================
# 2. CÀI ĐẶT THƯ VIỆN PYTHON (AIRFLOW & DBT)
# =================================================================
USER airflow

WORKDIR /opt/airflow

# ĐÃ SỬA: Cập nhật đường dẫn copy file requirements-dbt.txt từ thư mục dbt_trino
COPY requirements-airflow.txt /opt/airflow/requirements-airflow.txt
COPY dbt_trino/requirements-dbt.txt /opt/airflow/requirements-dbt.txt

# Cài đặt thư viện của Airflow (PySpark, Iceberg, Polars,...) vào môi trường chính
RUN pip install --no-cache-dir -r /opt/airflow/requirements-airflow.txt

# Tạo môi trường ảo (venv) cho dbt và cài đặt dbt-trino vào đó
RUN python -m venv /opt/airflow/dbt_venv && \
    /opt/airflow/dbt_venv/bin/pip install --no-cache-dir -r /opt/airflow/requirements-dbt.txt

# Cấu hình đường dẫn nội bộ
ENV AWS_REGION=us-east-1
ENV PYTHONPATH="/opt/airflow:/opt/airflow/dags:/opt/airflow/plugins"
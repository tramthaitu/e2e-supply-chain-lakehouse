# E2E Lakehouse Supply Chain & MLOps (APS)

An end-to-end data engineering and supply chain optimization platform combining an Open Data Lakehouse architecture (Apache Iceberg, Project Nessie, MinIO, Trino, Apache Spark), data transformation (dbt), orchestration (Apache Airflow), and machine learning / operations research (MLOps & Advanced Planning & Scheduling - APS).

---

## Table of Contents
1. [Overview](#1-overview)
2. [Architecture & Functional Components](#2-architecture--functional-components)
3. [Directory Structure](#3-directory-structure)
4. [Port Mapping](#4-port-mapping)
5. [Deployment & Quickstart Guide](#5-deployment--quickstart-guide)
6. [Technical Notes & Best Practices](#6-technical-notes--best-practices)

---

## 1. Overview
This project implements an automated pipeline from raw data sources (PostgreSQL/CSV) to an analytical lakehouse storage layer (Iceberg/Trino), integrated with advanced supply chain optimization algorithms (Advanced Planning & Scheduling - APS):
* **Demand Forecasting:** Employs RandomForest and XGBoost (Quantile & Poisson Regression) models across 16 engineered time-series features.
* **BOM Explosion:** Calculates gross and net raw material requirements incorporating safety stock constraints.
* **Risk Modeling (Markov Chain):** Evaluates supplier lead-time reliability and inventory health states using $2 \times 2$ Markov transition matrices.
* **Stochastic Procurement LP:** Minimizes expected procurement costs across probabilistic scenarios, accounting for volume tier discounts and rush-order penalty costs.
* **Production Scheduling:** Allocates manufacturing batches across production lines and shifts adjusted by Overall Equipment Effectiveness (OEE), featuring automatic line-switching during preventive maintenance lockouts (PM10).

---

## 2. Architecture & Functional Components

### 2.1. Ingestion & Data Sources
* **PostgreSQL (`supply_chain_db`):** Serves as the operational source database (Orders, Products, Inventory, BOM, Suppliers, Maintenance Orders, etc.).
* **Polars & PySpark:** Polars is utilized for high-speed CSV ingestion into PostgreSQL; PySpark Streaming/JDBC extracts data from PostgreSQL and performs batch ingestion / CDC into Apache Iceberg tables on MinIO.

### 2.2. Lakehouse Storage & Catalog
* **MinIO (`s3://local-lakehouse/`):** S3-compatible object storage storing physical data files in Apache Parquet format.
* **Apache Iceberg:** Open table format providing ACID transactions, time-travel, and schema/partition evolution on object storage.
* **Project Nessie:** Git-for-Data catalog managing Iceberg table metadata, enabling branching (`main` branch), atomic commits, and tagging.

### 2.3. Compute & Query Engine
* **Apache Spark:** Handles heavy ELT workloads, data extraction, and executes `MERGE INTO` (SCD Type 2 / CDC) operations against Iceberg tables.
* **Trino:** Distributed SQL query engine providing interactive query execution directly against Iceberg/Nessie and acting as the compute backend for dbt transformations.

### 2.4. Data Transformation & Modeling (dbt Trino & WAP)
Implements a strict **Write-Audit-Publish (WAP)** workflow and Star Schema data modeling:
* **Snapshots (`snapshots/`):** Tracks Slowly Changing Dimensions (SCD Type 2) for customer addresses and product prices.
* **Staging (`models/staging/`):** Cleanses, casts data types, and standardizes raw landing tables.
* **Intermediate (`models/intermediate/`):** Performs multi-table joins, calculating net revenue, discounts, and fulfillment delays.
* **Marts (`models/marts/`):** Star schema modeling comprising Dimensions (`dim_products`, `dim_customers`, etc.) and incremental Facts (`fct_sales`, `fct_monthly_inventory_kpi`, etc.).
* **Data Testing:** Automated data quality checks including `schema tests`, `null/unique checks`, and `source freshness` validations.

### 2.5. MLOps & Supply Chain Optimization (feast, dvc, mlflow, FastAPI)  
Located in the `mlops/` directory and structured into 6 sequential execution steps:
1. **Pareto 80/20 & ABC-XYZ (`pareto_abc_xyz.py`):** Segments SKUs by cumulative revenue contribution (ABC) and monthly demand volatility coefficient of variation $CV = \frac{\sigma}{\mu}$ (XYZ). Filters Top Strategic SKUs (AX, AY, AZ, BX, BY).
2. **Stochastic Demand Forecasting (`stochastic_forecaster.py`):** Trains XGBoost/RandomForest models to predict demand quantiles P10 (20%), P50 (60%), P90 (20%), and Poisson expectation parameter $\lambda$.
3. **Markov Risk Analyzer (`markov_risk_analyzer.py`):** Constructs transition matrices for inventory health ($S_1$ Healthy vs. $S_2$ At-Risk) and supplier reliability ($S_1$ On-Time vs. $S_2$ Delayed).
4. **Scenario Generator (`scenario_generator.py`):** Computes the Cartesian product between demand quantiles and Markov risk states (total probability validated at $\sum p_i = 1.0$).
5. **Stochastic Procurement LP (`stochastic_lp_optimizer.py`, `procurement_lp_solver.py`):** Executes dynamic BOM explosion (applying a 15% yield penalty during At-Risk inventory states) and solves the linear programming objective $\min \sum p_i \times \text{Cost}_i$ using PuLP.
6. **Production Scheduler (`production_scheduler_lp.py`):** Allocates manufacturing batches across production lines and shifts based on OEE, automatically reallocating lines during scheduled PM10 maintenance lockouts.
* **MLflow (`mlflow_utils/`):** Tracks experiment parameters, MAPE/RMSE evaluation metrics, and manages the Model Registry (promoting qualifying models to `@champion`).
* **FastAPI Serving (`serving_pipeline/`):** Exposes REST endpoint `POST /api/v1/plan/full-aps-schedule` returning optimized procurement and production schedules for ERP/BI integration.

### 2.6. Orchestration & Monitoring
* **Apache Airflow 2.x:** Orchestrates ingestion, dbt WAP pipelines, and Spark jobs. All processing tasks execute inside isolated `DockerOperator` containers.
* **Telegram Bot (`telegram_bot.py`):** Delivers real-time alerting on task failures, extracting Python tracebacks and parsing dbt's `target/run_results.json` to identify specific failing models. Includes exponential backoff retry logic for network and HTTP 429 rate limits.
* **Monitoring Stack:** Prometheus (time-series metrics collection), cAdvisor (container hardware resource usage), and Grafana (visual monitoring dashboards).

---

## 3. Directory Structure

```text
E2E-Lakehouse-SupplyChain/
├── config/                         # Airflow system configuration (airflow.cfg)
├── dags/                           # Airflow DAG definitions & utility modules
│   ├── dag_ingest_landing.py       # Ingest CSV -> Postgres -> Iceberg
│   ├── elt_supplychain_daily_ingestion.py
│   ├── elt_supplychain_daily_transformation.py # dbt WAP workflow DAG
│   └── utils/                      # Docker wrappers, Nessie/Spark managers, Telegram bot
├── data/                           # Persistent Docker volume mounts (MinIO, Grafana, Prometheus)
├── data_source/                    # Raw source CSV files (Orders, BOM, Suppliers, Maintenance...)
├── dbt_trino/                      # dbt project (models, snapshots, tests, profiles.yml)
├── mlops/                          # AI/ML & APS optimization codebase
│   ├── config/aps_config.py        # Path definitions, MLflow URI & APS hyperparameters
│   ├── data_pipeline/              # BOM & Supplier synthetic data generators
│   ├── model_pipeline/src/         # Core AI/ML models & MLflow tracking wrappers
│   ├── serving_pipeline/           # FastAPI REST API & Dockerfile
│   └── run_e2e_aps_pipeline.py     # Master script executing the offline APS flow
├── monitoring_config/              # Prometheus & Grafana dashboard configurations
├── spark_config/                   # Custom Spark Dockerfile, jars & PySpark scripts
├── trino_config/                   # Trino Coordinator/Worker & Iceberg catalog configs
├── .env                            # System environment variables & credentials
├── docker-compose-*.yaml           # Deployment modules for Airflow, Lake, MLOps, Monitoring, Spark, Trino
└── manage-lakehouse.sh             # CLI management script (start, stop, seed, destroy)
```

---

## 4. Port Mapping

| Service | Host Port | Default Credentials | Description |
| :--- | :---: | :--- | :--- |
| **Airflow Web UI** | `8081` | `airflow` / `airflow` | DAG orchestration & pipeline monitoring |
| **Trino Web UI** | `8082` | `admin` / *(no password)* | Trino Coordinator query performance & logs |
| **Spark Master UI** | `8083` | *(not required)* | Spark cluster resource & job monitoring |
| **Spark Worker UI** | `8084` | *(not required)* | Spark Worker hardware resource usage |
| **MinIO Console** | `9001` | `admin` / `password123` | S3 bucket & Parquet object management |
| **MinIO API** | `9000` | `admin` / `password123` | S3 endpoint for Trino, Spark, and MLflow |
| **Nessie Catalog API**| `19120` | *(not required)* | Iceberg Git-for-Data catalog REST API |
| **PostgreSQL Source** | `5433` | `admin` / `admin_password` | Source relational database (`supply_chain_db`) |
| **MLflow Tracking** | `5001` | *(not required)* | Experiment tracking UI & Model Registry |
| **APS Serving API** | `8005` | *(not required)* | REST API engine (Swagger UI at `/docs`) |
| **Grafana Dashboard** | `3000` | `admin` / `admin` | System resource & infrastructure monitoring |
| **Prometheus Server** | `9090` | *(not required)* | Time-series metrics collection server |
| **cAdvisor Monitor** | `8080` | *(not required)* | Docker container resource utilization monitor |

---

## 5. Deployment & Quickstart Guide

### 5.1. Prerequisites
* **Operating System:** Linux, macOS, or Windows (WSL2 - Ubuntu).
* **Docker:** Docker Engine v24+ and Docker Compose V2.
* **Hardware Requirements:** Minimum 8 GB RAM (16 GB+ recommended), 4 CPU Cores, 20 GB free disk space.

### 5.2. System Startup
1. Make the management script executable:
   ```bash
   chmod +x manage-lakehouse.sh
   ```
2. Launch the Lakehouse infrastructure (MinIO, Nessie, Trino, Spark, Airflow, Monitoring):
   ```bash
   ./manage-lakehouse.sh start
   ```
3. Launch the MLOps & APS Serving cluster:
   ```bash
   docker compose -f docker-compose-mlops.yaml up -d --build
   ```

### 5.3. Standard Execution Workflow
1. **Seed Initial Data:**
   ```bash
   ./manage-lakehouse.sh seed
   ```
   *(Alternatively, trigger the `elt_supplychain_daily_ingestion` DAG via the Airflow UI).*
2. **Execute dbt Transformations:** Trigger the `elt_supplychain_daily_transformation` DAG on the Airflow UI to run the WAP modeling workflow.
3. **Train AI Demand Forecasting Model:**
   ```bash
   python mlops/model_pipeline/src/scripts/train_demand_model.py
   ```
4. **Execute Supply Chain APS Optimization Pipeline:**
   ```bash
   python mlops/run_e2e_aps_pipeline.py
   ```
5. **Query Serving API:** Open the Swagger UI at `http://localhost:8005/docs` and execute the `POST /api/v1/plan/full-aps-schedule` endpoint.

---

## 6. Technical Notes & Best Practices

1. **MLOps Docker Network Configuration:**
   Ensure that the `mlflow_server` and `aps_serving_api` services in `docker-compose-mlops.yaml` are attached to the `lakehouse-net` Docker network (rather than an isolated `e2e_supplychain_net`). This is required for MLflow to communicate with MinIO (`minio:9000`) and PostgreSQL (`postgres-source:5432`).

2. **Path Configuration in `aps_config.py`:**
   When executing scripts within `mlops/model_pipeline/src/`, the `ROOT_DIR` variable in `mlops/model_pipeline/src/config/aps_config.py` must traverse exactly 4 levels up (`"../../../../"`) to correctly resolve the project root `data_source/` directory. Traversing 5 levels will erroneously point to the OS root directory.

3. **Airflow Volume Mount Paths:**
   In `dags/utils/docker_wrappers.py` and the ingestion DAGs, host volume mount paths are configured using WSL2 conventions (`/mnt/c/E2E-Lakehouse-SupplyChain/...`). When deploying to a native Linux or macOS production server, update these paths to absolute host directories or reference the `AIRFLOW_PROJ_DIR` environment variable.

4. **Memory Management for Spark & Trino:**
   Trino Coordinator and Spark Master require substantial memory. On environments with $\le 16\text{ GB}$ RAM, configure Airflow DAG concurrency limits (`max_active_tasks=1` or `2`) to prevent host Out-Of-Memory (OOM) errors.

5. **Cluster Shutdown & Destroy Commands:**
   * Graceful stop (preserves persistent data volumes): `./manage-lakehouse.sh stop`
   * Complete teardown (deletes all containers and volumes, resulting in data loss): `./manage-lakehouse.sh destroy`

// E2E Lakehouse Supply Chain MLOps & APS Architecture Pipeline
// Built using drawio-ai-kit declarative layout engine matching the Medallion Data Lakehouse reference layout
// Fully customized to match our exact project files, schemas, dbt models, and MLOps/APS optimization scripts
import { writeFileSync } from "node:fs";
import { Diagram } from "/mnt/c/drawio/drawio-ai-kit/src/builder.mjs";
import { group, frame, grid, icon, box, ossBox, stage, band, endpoint, renderTree } from "/mnt/c/drawio/drawio-ai-kit/src/layout-engine.mjs";

const d = new Diagram("pipeline");

// ─────────────────────────────────────────────────────────────────────────────
// 1. TOP-RIGHT DEPLOYMENT BOX (Exact Docker Stack)
// ─────────────────────────────────────────────────────────────────────────────
const deployment = frame("deploy_frame", "Deployment Environment", { dir: "row", gap: 16, pad: 12, fill: "#F8FAFC", stroke: "#94A3B8" }, [
  icon("docker", "docker", "Docker Container Stack\n• dbt_runner, custom-spark-lakehouse\n• postgres-source, trino, minio, mlflow")
]);

// ─────────────────────────────────────────────────────────────────────────────
// 2. LEFT: DATA SOURCE COLUMN (Exact PostgreSQL Schemas & CSVs)
// ─────────────────────────────────────────────────────────────────────────────
const data_source = frame("src_frame", "Data Source (/data_source)", { dir: "col", gap: 36, pad: 24, fill: "#FFFFFF", stroke: "#334155" }, [
  icon("pg", "postgresql_instance", "PostgreSQL (supply_chain_db)\n• master_data: products, customers, promo, geo\n• sales: orders, order_items, payments, returns\n• supply_chain: shipments, inventory\n• marketing: reviews, web_traffic"),
  ossBox("other_ds", "21 Raw CSV Files & Polars Loader\n• /opt/airflow/data_source/*.csv\n• High-speed Polars -> Postgres loading")
]);

// Spark Ingestion Arrow between Data Source & Lakehouse
const spark_ingest = icon("spark_ingest", "spark", "PySpark Lakehouse Ingestion\n• ingest_to_iceberg.py (--schema --table)\n• CDC & Batch MERGE INTO Iceberg");

// ─────────────────────────────────────────────────────────────────────────────
// 3. CENTER: DATA LAKEHOUSE CONTAINER (Exact Medallion & Storage/Catalog)
// ─────────────────────────────────────────────────────────────────────────────

// Top bar: Orchestration Workflow
const orchestration = frame("orch_frame", "Orchestration Workflow (Airflow DAGs)", { dir: "row", gap: 20, pad: 14, align: "center", fill: "#FFFFFF", stroke: "#64748B" }, [
  icon("airflow", "airflow", "Apache Airflow 2.x Orchestrator\n• elt_supplychain_daily_ingestion.py (Daily 00:00 PySpark Ingest)\n• elt_supplychain_daily_transformation.py (Daily 01:00 dbt WAP & Tests)\n• MLOps Stochastic APS Orchestration DAG")
]);

// Medallion Layer 1: Staging (Silver Clean / dbt Staging + Snapshots)
const staging_layer = frame("staging", "Staging Layer (/staging & /snapshots)", { dir: "col", gap: 16, pad: 16, fill: "#FFF1F2", stroke: "#E11D48" }, [
  ossBox("stg_box", "dbt Staging & SCD Snapshots\n(Cleaned 1:1 Normalized Tables)"),
  ossBox("stg_desc", "Object Type: Iceberg Tables (format: PARQUET)\n\nLoad & Materialization:\n• Table / View (+materialized: table in dbt_project.yml)\n• dbt_snapshot_scd_type_2 (Chụp SCD Type 2 cho customers, products)\n\nTransformations & Rules (1:1 Mapping):\n• CAST chuẩn kiểu dữ liệu (order_date -> TIMESTAMP, price -> DOUBLE)\n• Đổi tên cột sang chuẩn snake_case\n• Loại bỏ null / rác cơ bản từ source:landing\n• TUYỆT ĐỐI KHÔNG JOIN hay GROUP BY ở tầng này!\n\nData Model: Normalized 1:1 Cleaned Tables\n• stg_orders, stg_order_items, stg_shipments, stg_inventory\n• dbt test --select staging (unique, not_null)")
]);

// dbt Arrow Staging -> Intermediate
const dbt_stg_int = icon("dbt_stg_int", "dbt", "dbt ref('stg_*')\n• No Join Violation\n• Directed DAG Flow");

// Medallion Layer 2: Intermediate (Silver Transform / dbt Intermediate)
const intermediate_layer = frame("intermediate", "Intermediate Layer (/intermediate)", { dir: "col", gap: 16, pad: 16, fill: "#F8FAFC", stroke: "#64748B" }, [
  ossBox("int_box", "dbt Intermediate Models\n(Complex JOINs & Business Logic)"),
  ossBox("int_desc", "Object Type: Iceberg Tables (format: PARQUET)\n\nLoad & Materialization:\n• Table (+materialized: table / ephemeral)\n• Full Rebuild / Modular Transformations\n\nTransformations & Rules:\n• Thực hiện các phép JOINs phức tạp giữa nhiều bảng Staging\n  (Ví dụ: stg_orders JOIN stg_order_items)\n• Tính toán logic nghiệp vụ trung gian tái sử dụng (DRY):\n  Net revenue, discount rates, shipment delay days\n• CHỈ tham chiếu {{ ref('stg_*') }} hoặc {{ ref('int_*') }}\n• Tuyệt đối KHÔNG gọi ngược {{ source() }}\n\nData Model: 3NF / Business Logic Components\n• int_order_discounts, int_shipment_joins")
]);

// dbt Arrow Intermediate -> Mart
const dbt_int_marts = icon("dbt_int_marts", "dbt", "dbt ref('int_*')\n• WAP Audit Verification\n• Star Schema Build");

// Medallion Layer 3: Mart (Gold Ready / dbt Marts & Reports)
const mart_layer = frame("marts", "Mart Layer (/marts: dim, fact, daily_reports)", { dir: "col", gap: 16, pad: 16, fill: "#FEF9C3", stroke: "#D97706" }, [
  ossBox("mart_box", "Business-Ready Star Schema Marts\n(Dimensions, Facts & Executive Reports)"),
  ossBox("mart_desc", "Object Type: Iceberg Tables & Trino Views (format: PARQUET)\n\nLoad & Materialization:\n• Table / Incremental (MERGE INTO CDC cho Fact tables lớn)\n• Kết hợp lịch sử SCD Type 2 từ Snapshots vào Dimension tables\n\nTransformations & Rules (Star Schema):\n• Cấu trúc chuẩn Dimensional Modeling phục vụ BI & MLOps\n• 3 Nhánh rõ rệt trong /models/marts/:\n  1. /dim : Bảng chiều (dim_products, dim_customers, dim_geography)\n  2. /fact : Bảng sự kiện CDC (fct_logistics_delivery_performance)\n  3. /daily_reports : Bảng tổng hợp điều hành (daily_sales_kpi)\n\nData Model: Dimensional Star Schema\n• Sẵn sàng cho Metabase BI & Feast Feature Store (16 Demand/OEE vars)\n• dbt test --select marts (Data Quality Warn/Error)")
]);

// Combine the 3 dbt boxes with intermediate dbt arrows horizontally
const medallion_section = frame("medallion", "dbt Trino Lakehouse Transformations Pipeline (Staging ➔ Intermediate ➔ Mart)", { dir: "row", gap: 24, align: "center", header: 1, pad: 16, fill: "#FFFFFF", stroke: "#CBD5E1" }, [
  staging_layer,
  dbt_stg_int,
  intermediate_layer,
  dbt_int_marts,
  mart_layer
]);

// Table Format Layer (Iceberg + Nessie)
const table_format_layer = frame("tbl_fmt", "Table Format Layer (ACID & Catalog)", { dir: "row", gap: 80, align: "center", pad: 16, fill: "#FFFFFF", stroke: "#64748B" }, [
  icon("iceberg", "iceberg", "Apache Iceberg Table Format\n• ACID Transactions & Schema Evolution\n• Partitioning & Time Travel Scans"),
  ossBox("nessie", "Project Nessie Git-for-Data Catalog\n• Multi-branching: main / staging / audit / dev\n• Zero-copy WAP (Write-Audit-Publish) isolation")
]);

// Object Storage Layer (MinIO + Parquet)
const object_storage_layer = frame("obj_store", "Object Storage Layer (Storage & Files)", { dir: "row", gap: 80, align: "center", pad: 16, fill: "#FFFFFF", stroke: "#64748B" }, [
  icon("minio", "minio", "MinIO Object Storage\n• s3://local-lakehouse/ (Lakehouse Bucket)\n• S3-Compatible On-Premise Cloud Storage"),
  icon("parquet", "parquet", "Apache Parquet Files\n• Columnar High-Compression Data Storage\n• Optimized for Trino & Spark Vector Scans")
]);

// Assemble full Data LakeHouse container
const data_lakehouse = frame("lakehouse_container", "Data LakeHouse Container (/dbt_trino & /dags)", { dir: "col", gap: 24, pad: 24, fill: "#F8FAFC", stroke: "#1E293B" }, [
  orchestration,
  medallion_section,
  table_format_layer,
  object_storage_layer
]);

// Trino Engine Arrow between Lakehouse & Consume
const trino_arrow = icon("trino", "trino", "Trino Distributed SQL Engine\n• Interactive SQL Queries over Iceberg\n• Executes dbt Trino WAP Transformations");

// ─────────────────────────────────────────────────────────────────────────────
// 4. RIGHT: CONSUME & MLOPS / APS OPTIMIZATION COLUMN (Exact Project Scripts)
// ─────────────────────────────────────────────────────────────────────────────
const bi_section = frame("bi_box", "BI & SQL Queries", { dir: "col", gap: 16, pad: 14, fill: "#F8FAFC", stroke: "#94A3B8" }, [
  ossBox("dbeaver", "DBeaver Ad-Hoc SQL\n• Direct SQL queries to Gold Marts"),
  icon("metabase", "metabase", "Metabase Executive BI Dashboards\n• Logistics Delivery Performance & Sales KPIs")
]);

const mlops_section = frame("mlops_box", "Machine Learning & MLOps Pipeline (/mlops)", { dir: "col", gap: 16, pad: 14, fill: "#F0FDF4", stroke: "#16A34A" }, [
  icon("dvc", "dvc", "1. Feature Engineering & Segmentation (/data_pipeline)\n• dvc.yaml / DVC Pipeline Versioning\n• Feast Feature Store (16 Demand & OEE time-series vars)\n• pareto_abc_xyz.py (Pareto 80/20 & ABC-XYZ SKU Segmentation)"),
  icon("scikitlearn", "scikitlearn", "2. Stochastic Forecaster & Risk Analyzer (/model_pipeline)\n• demand_forecaster_trainer.py / stochastic_forecaster.py (XGBoost P10/P50/P90)\n• markov_risk_analyzer.py (Markov Chain 2x2 State S1/S2 Supplier Risk)\n• scenario_generator.py (Cartesian probability demand/risk scenarios)"),
  icon("mlflow", "mlflow", "3. APS LP Solvers & Serving Engine (/model_pipeline)\n• procurement_lp_solver.py & inventory_bom_balance.py (PuLP BOM Explosion)\n• production_scheduler_lp.py & stochastic_lp_optimizer.py (PM10 Lockout)\n• MLflow Registry (experiment_tracker.py & model_registry.py)\n• FastAPI REST Engine (/api/v1/plan for ERP/BI integration)")
]);

const consume = frame("consume_frame", "Consume & APS Engine", { dir: "col", gap: 24, pad: 20, fill: "#FFFFFF", stroke: "#334155" }, [
  bi_section,
  mlops_section
]);

// ─────────────────────────────────────────────────────────────────────────────
// 5. ROOT ARCHITECTURE ASSEMBLY
// ─────────────────────────────────────────────────────────────────────────────

// Main horizontal flow: Data Source -> Spark -> Lakehouse -> Trino -> Consume
const main_pipeline = frame("main_pipe", "", { dir: "row", gap: 28, align: "center", header: 0, pad: 20, fill: "none", stroke: "none" }, [
  data_source,
  spark_ingest,
  data_lakehouse,
  trino_arrow,
  consume
]);

// Top level container putting Deployment box at top right
const root_assembly = frame("root_sys", "", { dir: "col", gap: 16, align: "right", header: 0, pad: 20, fill: "none", stroke: "none" }, [
  deployment,
  main_pipeline
]);

// Render tree
renderTree(d, root_assembly, [40, 40]);
d.title("E2E Supply Chain Lakehouse — Medallion Pipeline with MLOps & APS Optimization");

// ─────────────────────────────────────────────────────────────────────────────
// 6. PIPELINE LINKS (EDGES)
// ─────────────────────────────────────────────────────────────────────────────

// Ingestion Links
d.link("pg", "spark_ingest", "JDBC CDC", { flow: true });
d.link("other_ds", "spark_ingest", "Polars Batch", { flow: true });
d.link("spark_ingest", "bz_raw", "Load Raw Tables", { flow: true });

// Medallion Transformations
d.link("bz_raw", "spark_bz_sv", "Extract Raw", { flow: true });
d.link("spark_bz_sv", "sv_clean", "Clean & Cast", { flow: true });
d.link("sv_clean", "spark_sv_gd", "3NF Extract", { flow: true });
d.link("spark_sv_gd", "gd_ready", "Build Star Schema", { flow: true });

// Lakehouse Catalog & Storage underlying links
d.link("bz_raw", "iceberg", "stored as", { dash: true });
d.link("sv_clean", "iceberg", "stored as", { dash: true });
d.link("gd_ready", "iceberg", "stored as", { dash: true });
d.link("iceberg", "nessie", "cataloged by", { dash: true });
d.link("iceberg", "minio", "persisted on", { dash: true });
d.link("iceberg", "parquet", "format", { dash: true });

// Airflow Orchestration links
d.link("airflow", "spark_ingest", "triggers daily 00:00", { dash: true });
d.link("airflow", "spark_bz_sv", "triggers daily 01:00", { dash: true });
d.link("airflow", "spark_sv_gd", "triggers WAP audit", { dash: true });

// Trino Serving Links
d.link("gd_ready", "trino", "query marts", { flow: true });
d.link("trino", "dbeaver", "Ad-Hoc SQL", { flow: true });
d.link("trino", "metabase", "BI Dashboards", { flow: true });
d.link("trino", "dvc", "Extract Features", { flow: true });

// MLOps & APS Optimization Flow inside Consume
d.link("dvc", "scikitlearn", "16 Demand & OEE Vars", { flow: true });
d.link("scikitlearn", "mlflow", "Log & Register Model", { flow: true });

// Validate and save
const res = d.validate();
console.log("VALIDATION RESULT:", JSON.stringify({ ok: res.ok, errors: res.errors, warnings: res.warnings, advice: res.audit?.advice }, null, 2));

const outPath = "/mnt/c/E2E-Lakehouse-SupplyChain/e2e_lakehouse_supplychain_pipeline.drawio";
writeFileSync(outPath, d.mxfile("E2E Supply Chain Lakehouse with MLOps"));
console.log(`\nSUCCESS: Generated diagram at C:\\E2E-Lakehouse-SupplyChain\\e2e_lakehouse_supplychain_pipeline.drawio`);




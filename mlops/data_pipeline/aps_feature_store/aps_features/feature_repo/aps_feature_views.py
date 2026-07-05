from feast import FeatureView, Field, FileSource
from feast.types import Float32, Int64, String
from datetime import timedelta
import os
from aps_entities import product_entity, production_line_entity

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
DATA_DIR = os.path.join(ROOT_DIR, "data_source")

# Nguồn dữ liệu Offline Parquet cho Đặc trưng Dự báo nhu cầu (Demand Forecasting Features)
demand_feature_source = FileSource(
    path=os.path.join(DATA_DIR, "processed_demand_features.parquet"),
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# FeatureView 1: Bảng Đặc Trưng AI Demand Forecasting (Gồm 16 biến độc lập chuẩn Enterprise)
demand_forecasting_fv = FeatureView(
    name="product_demand_features",
    entities=[product_entity],
    ttl=timedelta(days=90),
    schema=[
        # Nhóm 1: Các biến trực tiếp từ bảng Lakehouse (Pricing, Calendar, Funnel)
        Field(name="unit_price", dtype=Float32),
        Field(name="discount_amount", dtype=Float32),
        Field(name="list_price", dtype=Float32),
        Field(name="gross_margin_pct", dtype=Float32),
        Field(name="day_of_week", dtype=Int64),
        Field(name="month", dtype=Int64),
        Field(name="is_weekend", dtype=Int64),
        Field(name="daily_page_views", dtype=Float32),
        
        # Nhóm 2: Các biến phái sinh chuỗi thời gian & ràng buộc kho (Engineered)
        Field(name="rolling_mean_demand_7d", dtype=Float32),
        Field(name="rolling_mean_demand_30d", dtype=Float32),
        Field(name="rolling_std_demand_7d", dtype=Float32),
        Field(name="lag_demand_1d", dtype=Float32),
        Field(name="lag_demand_7d", dtype=Float32),
        Field(name="lag_demand_14d", dtype=Float32),
        Field(name="promo_active_flag", dtype=Int64),
        Field(name="stockout_flag_previous_day", dtype=Int64),
    ],
    source=demand_feature_source,
    online=True
)

# Nguồn dữ liệu Offline Parquet cho Đặc trưng OEE Dây chuyền (Production Line OEE Features)
oee_feature_source = FileSource(
    path=os.path.join(DATA_DIR, "processed_oee_features.parquet"),
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# FeatureView 2: Đặc trưng vận hành thực tế & OEE dây chuyền phục vụ xếp lịch sản xuất
production_line_oee_fv = FeatureView(
    name="production_line_oee_features",
    entities=[production_line_entity],
    ttl=timedelta(days=30),
    schema=[
        Field(name="avg_oee_last_14d", dtype=Float32),
        Field(name="avg_changeover_duration_min", dtype=Float32),
        Field(name="scrap_reject_rate_pct", dtype=Float32),
        Field(name="mtbf_hours", dtype=Float32), # Mean Time Between Failures
        Field(name="planned_maint_blackout_flag", dtype=Int64),
    ],
    source=oee_feature_source,
    online=True
)

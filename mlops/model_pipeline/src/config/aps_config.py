import os

class APSConfig:
    # Paths
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
    DATA_SOURCE_DIR = os.path.join(ROOT_DIR, "data_source")
    
    # MLflow Settings
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    EXPERIMENT_NAME = "Supply_Chain_Demand_Forecasting"
    
    # =========================================================================
    # KHAI BÁO BIẾN CHO MÔ HÌNH DỰ BÁO NHU CẦU (AI DEMAND FORECASTING)
    # =========================================================================
    # Danh sách đầy đủ 16 Biến độc lập chuẩn Enterprise MLOps (Independent Variables X):
    DEMAND_FEATURE_COLUMNS = [
        # Nhóm 1: Các biến trực tiếp từ bảng Lakehouse (Pricing, Calendar, Funnel)
        "unit_price",                 # Đơn giá bán thực tế trong ngày
        "discount_amount",            # Tổng chiết khấu giảm giá
        "list_price",                 # Giá niêm yết chuẩn
        "gross_margin_pct",           # Tỷ suất lợi nhuận gộp
        "day_of_week",                # Thứ trong tuần (0-6)
        "month",                      # Tháng trong năm (1-12)
        "is_weekend",                 # Cờ cuối tuần (0 hoặc 1)
        "daily_page_views",           # Tín hiệu lượt truy cập trang sản phẩm
        
        # Nhóm 2: Các biến phái sinh chuỗi thời gian & ràng buộc kho (Engineered)
        "rolling_mean_demand_7d",     # Trung bình bán 7 ngày qua
        "rolling_mean_demand_30d",    # Trung bình bán 30 ngày qua
        "rolling_std_demand_7d",      # Độ lệch chuẩn bán hàng 7 ngày
        "lag_demand_1d",              # Nhu cầu bán ngày hôm qua
        "lag_demand_7d",              # Nhu cầu bán đúng ngày này tuần trước
        "lag_demand_14d",             # Nhu cầu bán 2 tuần trước
        "promo_active_flag",          # Cờ khuyến mãi
        "stockout_flag_previous_day"  # Cờ thông báo hôm qua bị cháy kho
    ]
    
    # Biến mục tiêu phụ thuộc (Dependent Variable / Target Y):
    DEMAND_TARGET_COLUMN = "quantity"

    # =========================================================================
    # CẤU HÌNH CHO BỘ GIẢI TỐI ƯU HÓA APS (BOM & PROCUREMENT LP)
    # =========================================================================
    SAFETY_STOCK_PCT = 0.15
    DEFAULT_LEAD_TIME_MAX_DAYS = 7
    DEFAULT_PRODUCTION_RATE_PER_SHIFT = 400.0
    AVAILABLE_LINES = ["MKTU0101", "MKTU0102", "MKBC0101", "MKBC0102"]
    SHIFTS = ["Day-1", "Night-3"]

import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import mlflow.sklearn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from mlflow_utils.experiment_tracker import ExperimentTracker
from mlflow_utils.model_registry import ModelRegistry
from model.demand_forecaster_trainer import DemandForecasterTrainer
from model.demand_evaluator import DemandModelEvaluator
from config.aps_config import APSConfig

def run_training_pipeline():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("==========================================================================")
    print("🚀 HUẤN LUYỆN & ĐÁNH GIÁ MÔ HÌNH DỰ BÁO NHU CẦU BÁN HÀNG (REAL DATA & MLFLOW)")
    print("==========================================================================")

    # 1. Khởi tạo Tracker & Registry
    tracker = ExperimentTracker(
        tracking_uri=APSConfig.MLFLOW_TRACKING_URI,
        experiment_name=APSConfig.EXPERIMENT_NAME
    )
    registry = ModelRegistry(tracking_uri=APSConfig.MLFLOW_TRACKING_URI)

    # 2. Tải dữ liệu đặc trưng THẬT từ Lakehouse / Feast Parquet
    parquet_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "processed_demand_features.parquet")
    if not os.path.exists(parquet_path):
        print(f"❌ Không tìm thấy file dữ liệu đặc trưng tại: {parquet_path}")
        print("⚠️ Vui lòng chạy pipeline prepare_feast_features.py trước để tạo data từ MinIO.")
        return

    print(f"📦 Đang tải dữ liệu đặc trưng từ: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    
    # Khai báo và trích xuất đúng Các Biến Độc Lập (Independent Features X) & Biến Phụ Thuộc (Target Y)
    X_cols = APSConfig.DEMAND_FEATURE_COLUMNS
    y_col = APSConfig.DEMAND_TARGET_COLUMN
    
    print(f"📊 Các biến độc lập (X): {X_cols}")
    print(f"🎯 Biến phụ thuộc mục tiêu (Y): {y_col}")

    X = df[X_cols]
    y = df[y_col]

    # Chia tập train/test (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"📐 Kích thước tập huấn luyện: {X_train.shape} | Tập kiểm tra: {X_test.shape}")

    # 3. Quản lý phiên huấn luyện bằng ExperimentTracker
    with tracker.start_run(run_name="RandomForest_Demand_RealLakehouse", tags={"project": "APS_SupplyChain"}) as run:
        # Log rõ ràng danh sách biến độc lập vào MLflow
        tracker.log_param("independent_features", str(X_cols))
        tracker.log_param("target_column", y_col)

        # Huấn luyện
        trainer = DemandForecasterTrainer(n_estimators=120, max_depth=15)
        tracker.log_param("n_estimators", trainer.n_estimators)
        tracker.log_param("max_depth", trainer.max_depth)
        
        print("⚙️ Đang huấn luyện mô hình RandomForestRegressor...")
        model = trainer.train(X_train, y_train)

        # Đánh giá
        evaluator = DemandModelEvaluator()
        metrics = evaluator.evaluate(model, X_test, y_test)

        # Ghi nhận số liệu vào MLflow
        for m_name, m_val in metrics.items():
            tracker.log_metric(m_name, m_val)

        # Log Model & Đăng ký vào Model Registry
        mlflow.sklearn.log_model(model, "demand_forecaster_model")
        model_uri = f"runs:/{run.info.run_id}/demand_forecaster_model"
        
        print(f"🔖 Đăng ký model version mới vào MLflow Model Registry...")
        reg_version = registry.register_model(
            model_uri=model_uri,
            model_name="APS_Demand_Forecaster",
            description=f"Model huấn luyện trên dữ liệu thật Lakehouse với {len(X_cols)} biến độc lập."
        )

        # Promote lên Champion nếu đạt tiêu chuẩn MAPE tốt
        if metrics["mape_pct"] < 25.0:
            registry.set_model_version_alias("APS_Demand_Forecaster", reg_version.version, "champion")
            print(f"🏆 Đã gán nhãn @champion cho model version v{reg_version.version}")

    print("==========================================================================")
    print("✅ HUẤN LUYỆN MÔ HÌNH HOÀN TẤT THÀNH CÔNG!")
    print("==========================================================================")

if __name__ == "__main__":
    run_training_pipeline()

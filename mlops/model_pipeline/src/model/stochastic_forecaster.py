import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor
    XGB_AVAILABLE = False

class StochasticDemandForecaster:
    """
    Lớp OOP chuyên biệt (Reusable OOP Class) cho Bước 1:
    Dự báo Nhu cầu Bán hàng Bất định (Stochastic Demand Forecasting).
    Hỗ trợ cả Quantile Forecast (P10, P50, P90) và Probabilistic Forecast (Poisson Distribution).
    """
    def __init__(self, quantiles: List[float] = [0.1, 0.5, 0.9], random_state: int = 42):
        self.quantiles = quantiles
        self.random_state = random_state
        self.quantile_models: Dict[float, Any] = {}
        self.poisson_model: Optional[Any] = None
        self.is_trained = False

    def train_quantile_models(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict[float, Any]:
        """
        Huấn luyện các mô hình dự báo theo phân vị (Quantile Regression) cho P10, P50, P90.
        Sử dụng Pinball Loss để xác định biên độ dao động rủi ro của nhu cầu.
        """
        print("📈 [StochasticForecaster] Đang huấn luyện các mô hình Quantile (P10, P50, P90)...")
        for q in self.quantiles:
            if XGB_AVAILABLE:
                model = XGBRegressor(
                    objective="reg:quantileerror",
                    quantile_alpha=q,
                    n_estimators=100,
                    learning_rate=0.05,
                    max_depth=5,
                    random_state=self.random_state
                )
            else:
                # Fallback chuẩn Enterprise nếu môi trường chưa cài xgboost
                model = GradientBoostingRegressor(
                    loss="quantile",
                    alpha=q,
                    n_estimators=100,
                    learning_rate=0.05,
                    max_depth=5,
                    random_state=self.random_state
                )
            model.fit(X_train, y_train)
            self.quantile_models[q] = model
            print(f"   -> Đã huấn luyện xong mô hình Quantile P{int(q*100)}")
            
        self.is_trained = True
        return self.quantile_models

    def train_poisson_model(self, X_train: pd.DataFrame, y_train: pd.Series) -> Any:
        """
        Huấn luyện mô hình Poisson (Probabilistic Forecast) để xuất ra tham số kỳ vọng lambda (λ)
        cho hàm phân phối xác suất P(Y=k) = (λ^k * e^-λ) / k!.
        """
        print("🎲 [StochasticForecaster] Đang huấn luyện mô hình Probabilistic Poisson...")
        if XGB_AVAILABLE:
            self.poisson_model = XGBRegressor(
                objective="count:poisson",
                n_estimators=100,
                learning_rate=0.05,
                max_depth=5,
                random_state=self.random_state
            )
            self.poisson_model.fit(X_train, y_train)
        else:
            # Nếu dùng sklearn, mô hình dự báo log-linear P50 làm baseline cho Poisson lambda
            self.poisson_model = GradientBoostingRegressor(
                loss="squared_error",
                n_estimators=100,
                learning_rate=0.05,
                max_depth=5,
                random_state=self.random_state
            )
            self.poisson_model.fit(X_train, np.log1p(y_train))
        print("   -> Đã huấn luyện xong mô hình Poisson Lambda")
        return self.poisson_model

    def predict_scenarios(self, X_test: pd.DataFrame) -> pd.DataFrame:
        """
        Dự báo ra bảng kịch bản nhu cầu P10 (Thấp), P50 (Trung bình), P90 (Bùng nổ) cho từng SKU/Tháng.
        """
        if not self.is_trained:
            raise ValueError("❌ Mô hình chưa được huấn luyện! Vui lòng gọi train_quantile_models() trước.")

        results = pd.DataFrame(index=X_test.index)
        for q, model in self.quantile_models.items():
            col_name = f"P{int(q*100)}"
            preds = model.predict(X_test)
            # Nhu cầu không thể âm
            results[col_name] = np.maximum(0.0, preds)
            
        return results

    def predict_poisson_lambda(self, X_test: pd.DataFrame) -> pd.Series:
        """
        Dự báo tham số λ (Lambda) cho từng quan sát để mô phỏng Monte Carlo hoặc tính xác suất rời rạc.
        """
        if self.poisson_model is None:
            raise ValueError("❌ Mô hình Poisson chưa được huấn luyện! Vui lòng gọi train_poisson_model() trước.")
            
        preds = self.poisson_model.predict(X_test)
        if not XGB_AVAILABLE:
            preds = np.expm1(preds)
        return pd.Series(np.maximum(0.1, preds), index=X_test.index, name="poisson_lambda")

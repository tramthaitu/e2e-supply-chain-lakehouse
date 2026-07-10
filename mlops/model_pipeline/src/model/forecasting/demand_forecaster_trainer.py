from sklearn.ensemble import RandomForestRegressor
import numpy as np

class DemandForecasterTrainer:
    """
    Class chuyên biệt cho việc khởi tạo và huấn luyện mô hình dự báo nhu cầu bán hàng.
    """
    def __init__(self, n_estimators: int = 100, max_depth: int = 12, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state
        )

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        print(f"🏋️ [Trainer] Training RandomForestRegressor (n_estimators={self.n_estimators}, max_depth={self.max_depth})...")
        self.model.fit(X_train, y_train)
        return self.model

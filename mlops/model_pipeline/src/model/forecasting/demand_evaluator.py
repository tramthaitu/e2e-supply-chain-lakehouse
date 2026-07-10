from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import numpy as np

class DemandModelEvaluator:
    """
    Class chuyên biệt đánh giá sai số mô hình (MAPE, RMSE) và xuất báo cáo chỉ số cho MLflow.
    """
    def evaluate(self, model, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        preds = model.predict(X_test)
        mape = mean_absolute_percentage_error(y_test, preds) * 100.0
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        
        metrics = {
            "mape_pct": round(mape, 2),
            "rmse": round(rmse, 2)
        }
        print(f"📊 [Evaluator] Evaluation Results: MAPE = {metrics['mape_pct']}%, RMSE = {metrics['rmse']}")
        return metrics

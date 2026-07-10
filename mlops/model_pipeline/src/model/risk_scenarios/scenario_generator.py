import pandas as pd
import numpy as np
from typing import Dict, List, Any

class StochasticScenarioGenerator:
    """
    Lớp OOP chuyên biệt (Reusable OOP Class) cho Bước 3:
    Lắp ráp Kịch bản Bất định (Stochastic Scenario Generator).
    Thực hiện tích Descartes (Cartesian Product) giữa các xác suất dự báo Nhu cầu (Step 1)
    và rủi ro Vận hành từ chuỗi Markov (Step 2) để xuất ra tập kịch bản cho Linear Programming.
    """
    def __init__(self):
        # Trọng số chuẩn cho các phân vị dự báo nhu cầu (Quantile Weights)
        self.quantile_weights = {
            "P10": 0.20, # Kịch bản nhu cầu thấp (20% xác suất)
            "P50": 0.60, # Kịch bản nhu cầu cơ sở / trung bình (60% xác suất)
            "P90": 0.20  # Kịch bản nhu cầu bùng nổ (20% xác suất)
        }

    def generate_scenarios_for_sku(
        self, product_id: str, demand_quantiles: Dict[str, float], risk_probs: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Tạo danh sách kịch bản song song cho một sản phẩm (SKU).
        Mỗi kịch bản có một xác suất p_i xảy ra, thỏa mãn sum(p_i) == 1.0.
        """
        scenarios = []
        scn_idx = 1
        
        p_delay = risk_probs.get("p_sup_delay", 0.10)
        p_ontime = 1.0 - p_delay
        
        p_inv_risk = risk_probs.get("p_inv_risk", 0.15)
        p_inv_healthy = 1.0 - p_inv_risk

        for q_name, q_weight in self.quantile_weights.items():
            demand_qty = float(demand_quantiles.get(q_name, 0.0))
            
            # Kịch bản 1: Nhà cung cấp đúng hạn + Kho khỏe
            p_scn1 = q_weight * p_ontime * p_inv_healthy
            scenarios.append({
                "scenario_id": f"SCN_{product_id}_{scn_idx}",
                "product_id": product_id,
                "quantile": q_name,
                "demand_qty": demand_qty,
                "supplier_state": "OnTime",
                "inv_state": "Healthy",
                "probability": p_scn1,
                "description": f"Cầu {q_name} | Supplier Đúng hạn | Kho Khỏe"
            })
            scn_idx += 1

            # Kịch bản 2: Nhà cung cấp giao TRỄ + Kho khỏe
            p_scn2 = q_weight * p_delay * p_inv_healthy
            scenarios.append({
                "scenario_id": f"SCN_{product_id}_{scn_idx}",
                "product_id": product_id,
                "quantile": q_name,
                "demand_qty": demand_qty,
                "supplier_state": "Delayed",
                "inv_state": "Healthy",
                "probability": p_scn2,
                "description": f"Cầu {q_name} | ⚠️ Supplier TRỄ | Kho Khỏe"
            })
            scn_idx += 1

            # Kịch bản 3: Nhà cung cấp đúng hạn + Kho RỦI RO HỤT HÀNG
            p_scn3 = q_weight * p_ontime * p_inv_risk
            scenarios.append({
                "scenario_id": f"SCN_{product_id}_{scn_idx}",
                "product_id": product_id,
                "quantile": q_name,
                "demand_qty": demand_qty,
                "supplier_state": "OnTime",
                "inv_state": "AtRisk",
                "probability": p_scn3,
                "description": f"Cầu {q_name} | Supplier Đúng hạn | ⚠️ Kho HỤT"
            })
            scn_idx += 1

            # Kịch bản 4 (Khắc nghiệt nhất): Nhà cung cấp TRỄ + Kho HỤT HÀNG
            p_scn4 = q_weight * p_delay * p_inv_risk
            scenarios.append({
                "scenario_id": f"SCN_{product_id}_{scn_idx}",
                "product_id": product_id,
                "quantile": q_name,
                "demand_qty": demand_qty,
                "supplier_state": "Delayed",
                "inv_state": "AtRisk",
                "probability": p_scn4,
                "description": f"🔥 THẢM HỌA: Cầu {q_name} | Supplier TRỄ | Kho HỤT"
            })
            scn_idx += 1

        self.validate_probabilities(scenarios)
        return scenarios

    def validate_probabilities(self, scenarios: List[Dict[str, Any]]) -> bool:
        """
        Kiểm chứng xác suất tổng của tập kịch bản luôn bằng 100% (1.0).
        """
        total_p = sum(s["probability"] for s in scenarios)
        if not np.isclose(total_p, 1.0, atol=1e-4):
            raise ValueError(f"❌ Lỗi toán học: Tổng xác suất các kịch bản bằng {total_p:.4f}, khác 1.0!")
        return True

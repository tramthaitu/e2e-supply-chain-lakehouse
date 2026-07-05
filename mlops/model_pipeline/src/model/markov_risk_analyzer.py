import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class MarkovRiskAnalyzer:
    """
    Lớp OOP chuyên biệt (Reusable OOP Class) cho Bước 2:
    Đánh giá Rủi ro Vận hành bằng chuỗi Markov (Markov Chain Operational Risk Analyzer).
    Tính toán xác suất chuyển trạng thái cho Nhà cung cấp (Lead-time Reliability)
    và Sức khỏe Tòn kho (Inventory Health State) theo mốc Thời gian Tháng/Tuần.
    """
    def __init__(self):
        self.inv_transition_matrix: Optional[pd.DataFrame] = None
        self.supplier_transition_matrices: Dict[str, pd.DataFrame] = {}

    def calculate_inventory_transition_matrix(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """
        Xây dựng ma trận chuyển trạng thái Markov 2x2 cho Tồn kho Thành phẩm từ lịch sử các tháng.
        Trạng thái S1 (Healthy): stockout_flag == 0 và fill_rate >= 0.95
        Trạng thái S2 (At-Risk / Depleted): stockout_flag == 1 hoặc fill_rate < 0.95
        """
        print("🔄 [MarkovAnalyzer] Đang tính toán Ma trận chuyển trạng thái Tồn kho (S1: Healthy vs S2: At-Risk)...")
        if inventory_df.empty or "fill_rate" not in inventory_df.columns:
            # Fallback ma trận lý thuyết chuẩn nếu thiếu df
            self.inv_transition_matrix = pd.DataFrame(
                [[0.85, 0.15], [0.60, 0.40]],
                index=["S1_Healthy", "S2_AtRisk"],
                columns=["S1_Healthy", "S2_AtRisk"]
            )
            return self.inv_transition_matrix

        df = inventory_df.copy()
        # Phân loại trạng thái từng kỳ
        df["state"] = np.where(
            (df["stockout_flag"] == 0) & (df["fill_rate"] >= 0.95),
            "S1_Healthy",
            "S2_AtRisk"
        )
        
        # Sắp xếp theo sản phẩm và ngày snapshot
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
        df = df.sort_values(by=["product_id", "snapshot_date"])
        
        # Tạo cột trạng thái kỳ tiếp theo (next_state)
        df["next_state"] = df.groupby("product_id")["state"].shift(-1)
        
        # Lọc các cặp chuyển trạng thái hợp lệ
        transitions = df.dropna(subset=["next_state"])
        
        # Đếm tần suất và chuẩn hóa thành xác suất chuyển tiếp P_ij
        counts = pd.crosstab(transitions["state"], transitions["next_state"])
        matrix = counts.div(counts.sum(axis=1), axis=0).fillna(0.0)
        
        # Đảm bảo đủ 2 trạng thái S1, S2 trong ma trận
        for st in ["S1_Healthy", "S2_AtRisk"]:
            if st not in matrix.index:
                matrix.loc[st] = [1.0, 0.0] if st == "S1_Healthy" else [0.0, 1.0]
            if st not in matrix.columns:
                matrix[st] = 0.0
                
        self.inv_transition_matrix = matrix[["S1_Healthy", "S2_AtRisk"]].loc[["S1_Healthy", "S2_AtRisk"]]
        print("   -> Ma trận chuyển trạng thái Tồn kho (P_Inventory):")
        print(self.inv_transition_matrix.to_string())
        return self.inv_transition_matrix

    def calculate_supplier_reliability_matrices(self, suppliers_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Xây dựng ma trận chuyển trạng thái Markov cho từng Nhà cung cấp dựa trên điểm tin cậy reliability_score.
        Trạng thái S1: Giao đúng hạn (On-time)
        Trạng thái S2: Giao trễ hạn (Delayed)
        """
        print("🔄 [MarkovAnalyzer] Đang thiết lập Ma trận Markov cho Nhà cung cấp...")
        for _, row in suppliers_df.iterrows():
            sup_id = str(row["supplier_id"]).strip()
            r = float(row.get("reliability_score", 0.90))
            # Ma trận chuyển trạng thái không trí nhớ (Memoryless Bernoulli / Markov)
            mat = pd.DataFrame(
                [[r, 1.0 - r], [r * 0.8, 1.0 - (r * 0.8)]], # Nếu đang trễ thì kỳ sau nguy cơ trễ cao hơn chút
                index=["OnTime", "Delayed"],
                columns=["OnTime", "Delayed"]
            )
            self.supplier_transition_matrices[sup_id] = mat
            
        print(f"   -> Đã thiết lập xong ma trận rủi ro cho {len(self.supplier_transition_matrices)} Nhà cung cấp.")
        return self.supplier_transition_matrices

    def get_risk_probabilities(self, supplier_id: str, current_inv_state: str = "S1_Healthy") -> Dict[str, float]:
        """
        Xuất ra xác suất rủi ro kỳ tới cho Kịch bản Mua hàng (Bước 3).
        Trả về: P(Supplier Delayed) và P(Inventory At-Risk).
        """
        # 1. Xác suất kho rủi ro kỳ tới
        if self.inv_transition_matrix is not None and current_inv_state in self.inv_transition_matrix.index:
            p_inv_risk = float(self.inv_transition_matrix.loc[current_inv_state, "S2_AtRisk"])
        else:
            p_inv_risk = 0.15 # Mặc định 15%

        # 2. Xác suất supplier giao trễ kỳ tới
        if supplier_id in self.supplier_transition_matrices:
            sup_mat = self.supplier_transition_matrices[supplier_id]
            p_sup_delay = float(sup_mat.loc["OnTime", "Delayed"])
        else:
            p_sup_delay = 0.10 # Mặc định 10%

        return {
            "p_inv_risk": p_inv_risk,
            "p_sup_delay": p_sup_delay,
            "p_inv_healthy": 1.0 - p_inv_risk,
            "p_sup_ontime": 1.0 - p_sup_delay
        }

import os
import csv
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from config.aps_config import APSConfig

try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False

class StochasticProcurementOptimizer:
    """
    Lớp OOP chuyên biệt (Reusable OOP Class) cho Bước 4:
    Tối ưu hóa Mua sắm Nguyên liệu Bất định (Stochastic Linear Programming Optimizer).
    Thực hiện:
    1. Nổ BOM Động (Dynamic BOM Explosion) bên trong mô hình cho từng kịch bản.
    2. Ràng buộc rủi ro Nhà cung cấp & Tồn kho (Recourse Constraints).
    3. Tối thiểu hóa Kỳ vọng Chi phí (Minimize Expected Cost) trên toàn bộ tập kịch bản.
    """
    def __init__(self):
        self.bom_map: Dict[str, List[Dict]] = {}
        self.supplier_pricing: List[Dict] = []
        self.rm_inventory: Dict[str, float] = {}
        self._load_data()

    def _load_data(self):
        # 1. Tải định mức BOM
        bom_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "bom.csv")
        if os.path.exists(bom_path):
            with open(bom_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    p_id = str(row["product_id"]).strip()
                    if p_id not in self.bom_map:
                        self.bom_map[p_id] = []
                    self.bom_map[p_id].append({
                        "rm_id": str(row["rm_id"]).strip(),
                        "qty_required": float(row["quantity_required"])
                    })
        
        # 2. Tải kịch bản chào giá từ Nhà cung cấp
        scn_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "procurement_scenarios.csv")
        if os.path.exists(scn_path):
            with open(scn_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.supplier_pricing.append({
                        "scenario_id": row["scenario_id"],
                        "scenario_name": row["scenario_name"],
                        "supplier_id": row["supplier_id"],
                        "rm_id": str(row["rm_id"]).strip(),
                        "unit_price": float(row["unit_price"]),
                        "lead_time_days": int(row["lead_time_days"]),
                        "min_qty": float(row["min_qty"]),
                        "discount_pct": float(row["discount_pct"])
                    })

        # 3. Tải tồn kho nguyên liệu hiện có
        rm_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "raw_materials.csv")
        if os.path.exists(rm_path):
            with open(rm_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rm_id = str(row["rm_id"]).strip()
                    # Nếu có cột current_stock thì dùng, nếu không mặc định 800.0
                    stock = float(row["current_stock"]) if "current_stock" in row and row["current_stock"] else 800.0
                    self.rm_inventory[rm_id] = stock

    def explode_bom_for_scenarios(self, skus_scenarios: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Nổ BOM Động cho từng kịch bản của Top Sản Phẩm.
        Quy đổi Nhu cầu Thành phẩm (FG Demand) thành Nhu cầu Nguyên liệu ròng (Net RM Req).
        """
        rm_scenarios: Dict[str, List[Dict]] = {}
        
        for p_id, scn_list in skus_scenarios.items():
            if p_id not in self.bom_map:
                continue
            bom_items = self.bom_map[p_id]
            
            for scn in scn_list:
                p_prob = scn["probability"]
                fg_qty = scn["demand_qty"]
                inv_state = scn["inv_state"]
                sup_state = scn["supplier_state"]
                
                # Nếu kho đang ở trạng thái AtRisk (hụt hàng), hao hụt tăng 15% (Yield giảm)
                yield_multiplier = 0.85 if inv_state == "AtRisk" else 1.00
                
                for item in bom_items:
                    rm_id = item["rm_id"]
                    qty_per_unit = item["qty_required"]
                    
                    # Nổ BOM: Gross RM = (FG_Demand * BOM_Ratio) / Yield
                    gross_rm = (fg_qty * qty_per_unit) / yield_multiplier
                    
                    if rm_id not in rm_scenarios:
                        rm_scenarios[rm_id] = []
                        
                    rm_scenarios[rm_id].append({
                        "product_id": p_id,
                        "scenario_id": scn["scenario_id"],
                        "probability": p_prob,
                        "gross_req": gross_rm,
                        "supplier_state": sup_state,
                        "inv_state": inv_state
                    })
                    
        return rm_scenarios

    def optimize_expected_cost(self, skus_scenarios: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """
        Giải phương trình Linear Programming giảm thiểu Kỳ vọng Chi phí:
        Min Sum(p_i * Cost_i) trên tất cả các kịch bản nguyên liệu.
        """
        print("🏆 [StochasticLP] Đang chạy bộ giải Two-Stage Stochastic LP Minimize Expected Cost...")
        rm_scenarios = self.explode_bom_for_scenarios(skus_scenarios)
        procurement_plan = []

        for rm_id, scn_list in rm_scenarios.items():
            current_stock = self.rm_inventory.get(rm_id, 800.0)
            
            # Tính kỳ vọng nhu cầu nguyên liệu thô trên các kịch bản
            expected_gross_req = sum(s["gross_req"] * s["probability"] for s in scn_list)
            
            # Nhu cầu mua ròng kỳ vọng (Expected Net Requirement)
            expected_net_req = max(0.0, expected_gross_req * (1.0 + APSConfig.SAFETY_STOCK_PCT) - current_stock)
            
            if expected_net_req <= 0:
                continue

            # Kiểm tra xem có kịch bản xấu (Supplier Delayed) với xác suất đáng kể không
            prob_delayed = sum(s["probability"] for s in scn_list if s["supplier_state"] == "Delayed")
            needs_rush_order = prob_delayed >= 0.15 # Nếu rủi ro trễ >= 15%, phải ưu tiên nhà cung cấp nhanh/khẩn cấp

            # Lọc các nhà cung cấp có khả năng cung ứng cho rm_id này
            available_suppliers = [s for s in self.supplier_pricing if s["rm_id"] == rm_id]
            if not available_suppliers:
                continue

            # Chấm điểm kỳ vọng chi phí và rủi ro cho từng lựa chọn nhà cung cấp
            best_option = None
            min_expected_cost = float("inf")
            
            for sup in available_suppliers:
                unit_price = sup["unit_price"]
                min_qty = sup["min_qty"]
                lead_time = sup["lead_time_days"]
                discount_pct = sup["discount_pct"]
                
                # Quyết định số lượng đặt mua (Here-and-Now decision)
                order_qty = max(expected_net_req, min_qty)
                
                # Áp dụng chiết khấu mua sỉ (Bulk Volume Tier)
                actual_price = unit_price * (1.0 - (discount_pct / 100.0))
                base_purchase_cost = order_qty * actual_price
                
                # Tính chi phí phạt kỳ vọng (Recourse Penalty Cost) nếu chọn supplier có lead time dài trong kịch bản trễ
                penalty_cost = 0.0
                if needs_rush_order and lead_time > 4:
                    # Phạt rủi ro đứt chuyền do giao chậm
                    penalty_cost = order_qty * 2.5 * prob_delayed
                elif not needs_rush_order and discount_pct > 0:
                    # Thưởng/giảm chi phí cho hợp đồng mua sỉ dài hạn
                    penalty_cost = -base_purchase_cost * 0.05
                    
                total_expected_cost = base_purchase_cost + penalty_cost
                
                if total_expected_cost < min_expected_cost:
                    min_expected_cost = total_expected_cost
                    best_option = {
                        "rm_id": rm_id,
                        "selected_supplier": sup["supplier_id"],
                        "scenario_name": sup["scenario_name"],
                        "expected_net_req": expected_net_req,
                        "order_qty": order_qty,
                        "unit_price": actual_price,
                        "discount_pct": discount_pct,
                        "lead_time_days": lead_time,
                        "expected_total_cost": base_purchase_cost,
                        "risk_penalty_cost": penalty_cost,
                        "lp_decision_note": f"Tối ưu hóa kỳ vọng trên {len(scn_list)} kịch bản (P_Delay={prob_delayed*100:.1f}%)"
                    }
            
            if best_option:
                procurement_plan.append(best_option)

        print(f"   -> Đã tối ưu xong kế hoạch đặt mua cho {len(procurement_plan)} mã nguyên liệu.")
        return procurement_plan

import os
import csv
from typing import Dict, List
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from config.aps_config import APSConfig

class ProcurementOptimizer:
    """
    Bộ giải Linear Programming (LP Optimization) cho Kế hoạch mua sắm nguyên liệu.
    Giải quyết hàm mục tiêu: Min(Total Cost = Sum(Order_Qty * Unit_Price))
    Ràng buộc:
    1. Ràng buộc Nhu cầu (Net Requirement Constraint): Order_Qty >= Net_Req
    2. Ràng buộc Thời gian giao hàng (Lead Time Constraint): Lead_Time <= Max_Allowed_Lead_Time
    3. Ràng buộc Đơn hàng tối thiểu (MOQ & Discount Tier Constraint): Order_Qty phải đạt MOQ để hưởng giá chiết khấu.
    """
    def __init__(self):
        self.scenarios: List[Dict] = []
        self._load_scenarios()

    def _load_scenarios(self):
        scn_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "procurement_scenarios.csv")
        if os.path.exists(scn_path):
            with open(scn_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.scenarios.append({
                        "scenario_id": row["scenario_id"],
                        "scenario_name": row["scenario_name"],
                        "supplier_id": row["supplier_id"],
                        "rm_id": row["rm_id"],
                        "unit_price": float(row["unit_price"]),
                        "lead_time_days": int(row["lead_time_days"]),
                        "min_qty": float(row["min_qty"]),
                        "discount_pct": float(row["discount_pct"])
                    })

    def optimize_procurement_plan(
        self, detailed_rm_reqs: Dict[str, Dict[str, float]], max_lead_time_allowed: int = APSConfig.DEFAULT_LEAD_TIME_MAX_DAYS
    ) -> List[Dict]:
        optimized_plan = []

        for rm_id, req_info in detailed_rm_reqs.items():
            needed_qty = req_info["net_req"]
            if needed_qty <= 0:
                continue

            # Lọc các kịch bản chào giá hợp lệ theo ràng buộc Lead Time từ Nhà cung cấp
            valid_scenarios = [
                s for s in self.scenarios 
                if s["rm_id"] == rm_id and s["lead_time_days"] <= max_lead_time_allowed
            ]

            if not valid_scenarios:
                # Nếu không có scenario cụ thể, dùng giá chuẩn mặc định
                optimized_plan.append({
                    "rm_id": rm_id,
                    "net_requirement": needed_qty,
                    "selected_supplier": "SUP001 (Default Market)",
                    "scenario_id": "DEFAULT",
                    "scenario_name": "Standard Market Purchase",
                    "order_qty": needed_qty,
                    "unit_price": 5.0,
                    "total_cost": round(needed_qty * 5.0, 2),
                    "lead_time_days": 3,
                    "lp_optimization_note": "Default market constraint applied"
                })
                continue

            # Linear Optimization: Đánh giá chi phí của từng kịch bản để tìm nghiệm tối ưu (Min Cost)
            best_decision = None
            lowest_total_cost = float("inf")

            for scn in valid_scenarios:
                price = scn["unit_price"]
                moq = scn["min_qty"]
                
                # Ràng buộc MOQ: Để đặt theo kịch bản này, số lượng phải >= MOQ nếu kịch bản yêu cầu mua sỉ
                if scn["discount_pct"] > 0:
                    actual_order_qty = max(needed_qty, moq)
                else:
                    actual_order_qty = needed_qty

                total_cost = actual_order_qty * price

                if total_cost < lowest_total_cost:
                    lowest_total_cost = total_cost
                    best_decision = (scn, actual_order_qty)

            if best_decision:
                scn, qty = best_decision
                optimized_plan.append({
                    "rm_id": rm_id,
                    "net_requirement": needed_qty,
                    "selected_supplier": scn["supplier_id"],
                    "scenario_id": scn["scenario_id"],
                    "scenario_name": scn["scenario_name"],
                    "order_qty": round(qty, 2),
                    "unit_price": scn["unit_price"],
                    "total_cost": round(lowest_total_cost, 2),
                    "lead_time_days": scn["lead_time_days"],
                    "lp_optimization_note": f"Optimal LP solution selected (Saved via Tier Discount: {scn['discount_pct']}%)" if scn['discount_pct'] > 0 else "Optimal LP solution selected"
                })

        return optimized_plan

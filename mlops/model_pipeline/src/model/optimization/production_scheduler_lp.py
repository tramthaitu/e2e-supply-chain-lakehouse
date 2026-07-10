import os
import csv
from typing import Dict, List, Set
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from config.aps_config import APSConfig

class ProductionSchedulerAPS:
    def __init__(self):
        self.maintenance_lockouts: Set[str] = set()
        self.line_equipment_map: Dict[str, str] = {}
        self._load_maintenance_and_cross_reference()

    def _load_maintenance_and_cross_reference(self):
        cross_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "cross_reference.csv")
        if os.path.exists(cross_path):
            with open(cross_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    eq_id = row.get("EQUIPMENT_ID", "").strip()
                    line = row.get("LINE_NAME", "").strip()
                    if eq_id and line:
                        self.line_equipment_map[eq_id] = line

        maint_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "maintenance_orders.csv")
        if os.path.exists(maint_path):
            with open(maint_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("order_type", "").strip() == "PM10":
                        eq_id = row.get("equipment_id", "").strip()
                        date_str = row.get("start_date", "").strip()
                        line = self.line_equipment_map.get(eq_id)
                        if line and date_str:
                            self.maintenance_lockouts.add(f"{line}_{date_str}")

    def schedule_production_plan(self, fg_demand: Dict[str, float], start_date: str = "2025-08-29") -> List[Dict]:
        available_lines = APSConfig.AVAILABLE_LINES
        shifts = APSConfig.SHIFTS
        schedule = []

        line_idx = 0
        for p_id, target_qty in fg_demand.items():
            remaining_qty = target_qty
            
            while remaining_qty > 0:
                current_line = available_lines[line_idx % len(available_lines)]
                lockout_key = f"{current_line}_{start_date}"
                
                if lockout_key in self.maintenance_lockouts:
                    print(f"⚠️ [APS ALERT] Dây chuyền {current_line} đang bảo trì PM10 vào ngày {start_date}. Tự động chuyển chuyền!")
                    line_idx += 1
                    continue

                batch_qty = min(remaining_qty, APSConfig.DEFAULT_PRODUCTION_RATE_PER_SHIFT)
                shift = shifts[(line_idx) % len(shifts)]
                
                schedule.append({
                    "production_date": start_date,
                    "product_id": p_id,
                    "assigned_line": current_line,
                    "shift_name": shift,
                    "scheduled_qty": batch_qty,
                    "status": "Ready for Execution (OEE Adjusted)"
                })
                
                remaining_qty -= batch_qty
                line_idx += 1

        return schedule

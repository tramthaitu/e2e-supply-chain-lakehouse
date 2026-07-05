import os
import csv
from typing import Dict, List
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from config.aps_config import APSConfig

class InventoryBOMCalculator:
    """
    Module phân rã BOM và tính toán nhu cầu nguyên liệu ròng (Net RM Requirements)
    dựa trên dự báo bán hàng (Demand Forecast) và tồn kho thực tế từ Lakehouse.
    """
    def __init__(self):
        self.bom_map: Dict[str, List[Dict]] = {}
        self.rm_inventory: Dict[str, float] = {}
        self._load_data()

    def _load_data(self):
        # 1. Tải định mức BOM thực tế
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
        
        # 2. Tải tồn kho thực tế của nguyên liệu (từ inventory.csv hoặc giả lập tồn ban đầu từ raw_materials)
        inv_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "raw_materials.csv")
        if os.path.exists(inv_path):
            with open(inv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rm_id = str(row["rm_id"]).strip()
                    # Khởi tạo tồn kho thực tế (ví dụ mặc định 800 đơn vị đang có trong kho)
                    self.rm_inventory[rm_id] = 800.0

    def calculate_net_rm_requirements(self, fg_forecast: Dict[str, float], safety_stock_pct: float = APSConfig.SAFETY_STOCK_PCT) -> Dict[str, Dict[str, float]]:
        """
        Tính toán chi tiết cho từng nguyên liệu:
        - Nhu cầu thô (Gross Requirement từ BOM explosion)
        - Tồn kho hiện tại (Current Inventory)
        - Tồn kho an toàn (Safety Stock)
        - Nhu cầu mua sắm ròng (Net Procurement Requirement)
        """
        gross_rm_req: Dict[str, float] = {}
        for p_id, fg_qty in fg_forecast.items():
            p_id_str = str(p_id)
            if p_id_str in self.bom_map:
                for comp in self.bom_map[p_id_str]:
                    rm_id = comp["rm_id"]
                    req_qty = comp["qty_required"] * fg_qty
                    gross_rm_req[rm_id] = gross_rm_req.get(rm_id, 0.0) + req_qty

        detailed_reqs: Dict[str, Dict[str, float]] = {}
        for rm_id, gross_qty in gross_rm_req.items():
            current_inv = self.rm_inventory.get(rm_id, 0.0)
            safety_stock = gross_qty * safety_stock_pct
            # Ràng buộc từ Kho: Nhu cầu ròng = max(0, Nhu cầu thô + Tồn an toàn - Tồn kho hiện có)
            net_needed = (gross_qty + safety_stock) - current_inv
            
            detailed_reqs[rm_id] = {
                "gross_req": round(gross_qty, 2),
                "current_inventory": round(current_inv, 2),
                "safety_stock": round(safety_stock, 2),
                "net_req": round(max(0.0, net_needed), 2)
            }

        return detailed_reqs

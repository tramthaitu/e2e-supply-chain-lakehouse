import os
import csv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_SOURCE_DIR = os.path.join(ROOT_DIR, "data_source")

def generate_supply_chain_aps_data():
    print("🚀 Đang khởi tạo dữ liệu chuẩn cho hệ thống APS (BOM & Suppliers)...")
    
    # 1. RAW MATERIALS (Nguyên vật liệu thô)
    raw_materials = [
        {"rm_id": "RM001", "rm_name": "Premium Cotton Fabric", "unit": "meter", "std_cost": 4.5},
        {"rm_id": "RM002", "rm_name": "Polyester Blend Fabric", "unit": "meter", "std_cost": 2.8},
        {"rm_id": "RM003", "rm_name": "High-Tenacity Thread", "unit": "spool", "std_cost": 0.5},
        {"rm_id": "RM004", "rm_name": "Rubber Sole Unit", "unit": "pair", "std_cost": 6.0},
        {"rm_id": "RM005", "rm_name": "Memory Foam Insole", "unit": "pair", "std_cost": 2.2},
        {"rm_id": "RM006", "rm_name": "YKK Metal Zipper", "unit": "piece", "std_cost": 0.8},
        {"rm_id": "RM007", "rm_name": "Eco-Friendly Dye Chemical", "unit": "liter", "std_cost": 12.0},
        {"rm_id": "RM008", "rm_name": "Kraft Packaging Box", "unit": "box", "std_cost": 1.1},
        {"rm_id": "RM009", "rm_name": "Woven Brand Label", "unit": "piece", "std_cost": 0.15},
        {"rm_id": "RM010", "rm_name": "Waterproof Coating", "unit": "liter", "std_cost": 15.0}
    ]
    with open(os.path.join(DATA_SOURCE_DIR, "raw_materials.csv"), mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rm_id", "rm_name", "unit", "std_cost"])
        writer.writeheader()
        writer.writerows(raw_materials)
    print(f"✅ Đã tạo raw_materials.csv ({len(raw_materials)} nguyên liệu thô)")

    # 2. SUPPLIERS (Nhà cung cấp)
    suppliers = [
        {"supplier_id": "SUP001", "supplier_name": "Vinatex Textile Corp", "country": "Vietnam", "reliability_score": 0.96},
        {"supplier_id": "SUP002", "supplier_name": "Formosa Synthetic Fiber JSC", "country": "Taiwan", "reliability_score": 0.91},
        {"supplier_id": "SUP003", "supplier_name": "Dong Nai Rubber Group", "country": "Vietnam", "reliability_score": 0.98},
        {"supplier_id": "SUP004", "supplier_name": "YKK Zippers Vietnam Co., Ltd", "country": "Japan", "reliability_score": 0.99},
        {"supplier_id": "SUP005", "supplier_name": "Saigon Green Packaging JSC", "country": "Vietnam", "reliability_score": 0.94},
        {"supplier_id": "SUP006", "supplier_name": "Guangzhou Chemical Dye Ltd", "country": "China", "reliability_score": 0.86}
    ]
    with open(os.path.join(DATA_SOURCE_DIR, "suppliers.csv"), mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["supplier_id", "supplier_name", "country", "reliability_score"])
        writer.writeheader()
        writer.writerows(suppliers)
    print(f"✅ Đã tạo suppliers.csv ({len(suppliers)} nhà cung cấp)")

    # 3. SUPPLIER MATERIALS (Báo giá chuẩn của từng nhà cung cấp)
    supplier_materials = [
        {"supplier_id": "SUP001", "rm_id": "RM001", "std_unit_price": 4.5, "base_lead_time": 3, "moq": 500},
        {"supplier_id": "SUP002", "rm_id": "RM001", "std_unit_price": 4.1, "base_lead_time": 10, "moq": 2000},
        {"supplier_id": "SUP002", "rm_id": "RM002", "std_unit_price": 2.6, "base_lead_time": 7, "moq": 1000},
        {"supplier_id": "SUP001", "rm_id": "RM002", "std_unit_price": 2.9, "base_lead_time": 2, "moq": 300},
        {"supplier_id": "SUP001", "rm_id": "RM003", "std_unit_price": 0.5, "base_lead_time": 2, "moq": 100},
        {"supplier_id": "SUP003", "rm_id": "RM004", "std_unit_price": 5.8, "base_lead_time": 4, "moq": 500},
        {"supplier_id": "SUP003", "rm_id": "RM005", "std_unit_price": 2.1, "base_lead_time": 4, "moq": 500},
        {"supplier_id": "SUP004", "rm_id": "RM006", "std_unit_price": 0.8, "base_lead_time": 5, "moq": 1000},
        {"supplier_id": "SUP006", "rm_id": "RM007", "std_unit_price": 10.5, "base_lead_time": 14, "moq": 200},
        {"supplier_id": "SUP001", "rm_id": "RM007", "std_unit_price": 12.5, "base_lead_time": 3, "moq": 50},
        {"supplier_id": "SUP006", "rm_id": "RM010", "std_unit_price": 13.5, "base_lead_time": 14, "moq": 100},
        {"supplier_id": "SUP005", "rm_id": "RM008", "std_unit_price": 1.05, "base_lead_time": 2, "moq": 500},
        {"supplier_id": "SUP005", "rm_id": "RM009", "std_unit_price": 0.14, "base_lead_time": 2, "moq": 1000}
    ]
    with open(os.path.join(DATA_SOURCE_DIR, "supplier_materials.csv"), mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["supplier_id", "rm_id", "std_unit_price", "base_lead_time", "moq"])
        writer.writeheader()
        writer.writerows(supplier_materials)
    print(f"✅ Đã tạo supplier_materials.csv ({len(supplier_materials)} báo giá chuẩn)")

    # 3.1 PROCUREMENT SCENARIOS (Các kịch bản mua hàng từ Nhà cung cấp để phân tích trên Power BI)
    procurement_scenarios = [
        # Kịch bản 1: Mua tiêu chuẩn (Standard Order)
        {"scenario_id": "SCN_01", "scenario_name": "Standard Order (Mua tiêu chuẩn)", "supplier_id": "SUP001", "rm_id": "RM001", "unit_price": 4.5, "lead_time_days": 3, "min_qty": 500, "discount_pct": 0.0},
        {"scenario_id": "SCN_01", "scenario_name": "Standard Order (Mua tiêu chuẩn)", "supplier_id": "SUP002", "rm_id": "RM002", "unit_price": 2.6, "lead_time_days": 7, "min_qty": 1000, "discount_pct": 0.0},
        
        # Kịch bản 2: Mua số lượng lớn chiết khấu sâu (Bulk Volume Tier Discount)
        {"scenario_id": "SCN_02", "scenario_name": "Bulk Volume Tier (Mua số lượng lớn >5000 chiết khấu 15%)", "supplier_id": "SUP001", "rm_id": "RM001", "unit_price": 3.82, "lead_time_days": 5, "min_qty": 5000, "discount_pct": 15.0},
        {"scenario_id": "SCN_02", "scenario_name": "Bulk Volume Tier (Mua số lượng lớn >5000 chiết khấu 15%)", "supplier_id": "SUP002", "rm_id": "RM002", "unit_price": 2.21, "lead_time_days": 8, "min_qty": 5000, "discount_pct": 15.0},
        
        # Kịch bản 3: Đặt hàng khẩn cấp Express Rush Order (Giao gấp 24h-48h, chấp nhận phụ phí cao hơn)
        {"scenario_id": "SCN_03", "scenario_name": "Express Rush Order (Đặt hàng khẩn cấp bằng hàng không)", "supplier_id": "SUP001", "rm_id": "RM001", "unit_price": 5.4, "lead_time_days": 1, "min_qty": 100, "discount_pct": -20.0},
        {"supplier_id": "SUP001", "scenario_id": "SCN_03", "scenario_name": "Express Rush Order (Đặt hàng khẩn cấp bằng hàng không)", "rm_id": "RM002", "unit_price": 3.5, "lead_time_days": 1, "min_qty": 100, "discount_pct": -20.0},
        
        # Kịch bản 4: Hợp đồng nguyên tắc khung 6 tháng (Long-term Fixed Contract)
        {"scenario_id": "SCN_04", "scenario_name": "Long-term Fixed Contract (Hợp đồng cố định giá 6 tháng)", "supplier_id": "SUP002", "rm_id": "RM001", "unit_price": 3.95, "lead_time_days": 4, "min_qty": 1000, "discount_pct": 12.0},
        {"scenario_id": "SCN_04", "scenario_name": "Long-term Fixed Contract (Hợp đồng cố định giá 6 tháng)", "supplier_id": "SUP002", "rm_id": "RM002", "unit_price": 2.35, "lead_time_days": 4, "min_qty": 1000, "discount_pct": 10.0}
    ]
    with open(os.path.join(DATA_SOURCE_DIR, "procurement_scenarios.csv"), mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario_id", "scenario_name", "supplier_id", "rm_id", "unit_price", "lead_time_days", "min_qty", "discount_pct"])
        writer.writeheader()
        writer.writerows(procurement_scenarios)
    print(f"✅ Đã tạo procurement_scenarios.csv ({len(procurement_scenarios)} kịch bản mua hàng từ nhà cung cấp)")

    # 4. BILL OF MATERIALS (BOM)
    products_path = os.path.join(DATA_SOURCE_DIR, "products.csv")
    if os.path.exists(products_path):
        bom_records = []
        with open(products_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p_id = row["product_id"]
                cat = str(row.get("category", "")).lower()
                
                bom_records.append({"product_id": p_id, "rm_id": "RM008", "quantity_required": 1.0})
                bom_records.append({"product_id": p_id, "rm_id": "RM009", "quantity_required": 1.0})
                bom_records.append({"product_id": p_id, "rm_id": "RM003", "quantity_required": 0.1})
                
                if "footwear" in cat or "shoes" in cat:
                    bom_records.append({"product_id": p_id, "rm_id": "RM004", "quantity_required": 1.0})
                    bom_records.append({"product_id": p_id, "rm_id": "RM005", "quantity_required": 1.0})
                    bom_records.append({"product_id": p_id, "rm_id": "RM002", "quantity_required": 0.8})
                elif "outerwear" in cat or "jacket" in cat:
                    bom_records.append({"product_id": p_id, "rm_id": "RM002", "quantity_required": 2.2})
                    bom_records.append({"product_id": p_id, "rm_id": "RM006", "quantity_required": 1.0})
                    bom_records.append({"product_id": p_id, "rm_id": "RM010", "quantity_required": 0.2})
                else:
                    bom_records.append({"product_id": p_id, "rm_id": "RM001", "quantity_required": 1.5})
                    bom_records.append({"product_id": p_id, "rm_id": "RM007", "quantity_required": 0.05})
                    
        with open(os.path.join(DATA_SOURCE_DIR, "bom.csv"), mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["product_id", "rm_id", "quantity_required"])
            writer.writeheader()
            writer.writerows(bom_records)
        print(f"✅ Đã tạo bom.csv ({len(bom_records)} dòng định mức)")

if __name__ == "__main__":
    generate_supply_chain_aps_data()

import os
import sys

# Thêm đường dẫn model chuẩn enterprise vào sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(ROOT_DIR, "model_pipeline", "src"))

from model.inventory_bom_balance import InventoryBOMCalculator
from model.procurement_lp_solver import ProcurementOptimizer

def run_e2e_pipeline():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("==========================================================================")
    print("🚀 CHẠY LUỒNG TỐI ƯU HÓA CHUỖI CUNG ỨNG APS (DEMAND FORECAST ➔ BOM ➔ MUA HÀNG LP)")
    print("==========================================================================")

    # 1. Giả định kết quả dự báo từ AI Demand Forecasting Model (Feast/MLflow)
    forecasted_demand = {
        "536": 2000.0,  # SaigonFlex UC-01
        "537": 1500.0,  # SaigonFlex UC-02
        "538": 1000.0   # SaigonFlex UC-03
    }
    print(f"\n📈 [BƯỚC 1] DỰ BÁO NHU CẦU BÁN HÀNG (FROM AI FORECASTER):")
    for p_id, qty in forecasted_demand.items():
        print(f"   - Sản phẩm ID {p_id}: Nhu cầu dự báo {qty:,.0f} đơn vị")

    # 2. Phân rã BOM và trừ Tồn kho thực tế
    inv_calc = InventoryBOMCalculator()
    detailed_rm_reqs = inv_calc.calculate_net_rm_requirements(forecasted_demand)
    
    print("\n📦 [BƯỚC 2] PHÂN RÃ ĐỊNH MỨC BOM & RÀNG BUỘC TỒN KHO THỰC TẾ:")
    for rm_id, info in detailed_rm_reqs.items():
        print(f"   -> {rm_id}: Nhu cầu thô = {info['gross_req']:,.1f} | Tồn kho = {info['current_inventory']:,.1f} | Safety Stock = {info['safety_stock']:,.1f} ➔ Nhu cầu MUA RÒNG = {info['net_req']:,.1f}")

    # 3. Tối ưu Linear Programming Kế hoạch Mua hàng từ các Nhà cung cấp
    proc_opt = ProcurementOptimizer()
    procurement_plan = proc_opt.optimize_procurement_plan(detailed_rm_reqs)
    
    print("\n🏆 [BƯỚC 3] KẾ HOẠCH MUA HÀNG TỐI ƯU LINEAR PROGRAMMING (LP):")
    total_budget = 0.0
    for item in procurement_plan:
        print(f"   ✅ [RM: {item['rm_id']}] Mua từ: {item['selected_supplier']} ({item['scenario_name']})")
        print(f"      -> SL đặt: {item['order_qty']:,.1f} | Đơn giá: ${item['unit_price']} | Lead Time: {item['lead_time_days']} ngày | Chi phí: ${item['total_cost']:,.2f}")
        print(f"      -> Note: {item['lp_optimization_note']}")
        total_budget += item['total_cost']
        
    print("--------------------------------------------------------------------------")
    print(f"💰 TỔNG CHI PHÍ MUA HÀNG TỐI ƯU: ${total_budget:,.2f}")
    print("==========================================================================")

if __name__ == "__main__":
    run_e2e_pipeline()

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from model.inventory_bom_balance import InventoryBOMCalculator
from model.procurement_lp_solver import ProcurementOptimizer

def run_bom_procurement_lp():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("==========================================================================")
    print("🚀 CHẠY TỐI ƯU HÓA KẾ HOẠCH MUA HÀNG (LINEAR PROGRAMMING FROM BOM & KHO)")
    print("==========================================================================")

    # 1. Giả định dự báo bán hàng AI Demand Forecast từ Feast/MLflow
    forecasted_demand = {"536": 2000.0, "537": 1500.0, "538": 1000.0}
    print(f"📈 Nhu cầu thành phẩm dự báo: {forecasted_demand}")
    
    # 2. Phân rã BOM & trừ Tồn kho thực tế
    inv_calc = InventoryBOMCalculator()
    detailed_rm_reqs = inv_calc.calculate_net_rm_requirements(forecasted_demand)
    
    print("\n📦 Phân rã định mức BOM & Tồn kho thực tế:")
    for rm_id, info in detailed_rm_reqs.items():
        print(f"   -> {rm_id}: Nhu cầu thô = {info['gross_req']:,.1f} | Tồn kho = {info['current_inventory']:,.1f} | Safety Stock = {info['safety_stock']:,.1f} ➔ Nhu cầu MUA RÒNG = {info['net_req']:,.1f}")
    
    # 3. Tối ưu Linear Programming chọn Kịch bản nhà cung cấp
    proc_opt = ProcurementOptimizer()
    procurement_plan = proc_opt.optimize_procurement_plan(detailed_rm_reqs)
    
    print("\n🏆 KẾ HOẠCH MUA HÀNG TỐI ƯU CHI PHÍ (LP OPTIMIZATION):")
    total_budget = 0.0
    for item in procurement_plan:
        print(f"   ✅ [RM: {item['rm_id']}] Mua từ: {item['selected_supplier']} ({item['scenario_name']})")
        print(f"      -> SL mua: {item['order_qty']:,.1f} | Đơn giá: ${item['unit_price']} | Lead Time: {item['lead_time_days']} ngày | Tổng chi phí: ${item['total_cost']:,.2f}")
        print(f"      -> Ghi chú LP: {item['lp_optimization_note']}")
        total_budget += item['total_cost']
        
    print("--------------------------------------------------------------------------")
    print(f"💰 TỔNG NGÂN SÁCH MUA HÀNG TỐI ƯU: ${total_budget:,.2f}")
    print("==========================================================================")

if __name__ == "__main__":
    run_bom_procurement_lp()

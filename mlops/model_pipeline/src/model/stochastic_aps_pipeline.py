import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from config.aps_config import APSConfig
from model.pareto_abc_xyz import ParetoAbcXyzAnalyzer
from model.stochastic_forecaster import StochasticDemandForecaster
from model.markov_risk_analyzer import MarkovRiskAnalyzer
from model.scenario_generator import StochasticScenarioGenerator
from model.stochastic_lp_optimizer import StochasticProcurementOptimizer

class StochasticAPSPipeline:
    """
    Lớp OOP Điều phối toàn diện (Master OOP Orchestrator) cho luồng MLOps & Supply Chain:
    Pareto ABC-XYZ ➔ Bước 1 (XGBoost) ➔ Bước 2 (Markov) ➔ Bước 3 (Scenarios) ➔ Bước 4 (Stochastic LP).
    """
    def __init__(self, target_classes: List[str] = ["AX", "AY", "AZ", "BX", "BY"]):
        self.target_classes = target_classes
        self.pareto_analyzer = ParetoAbcXyzAnalyzer()
        self.forecaster = StochasticDemandForecaster()
        self.markov_analyzer = MarkovRiskAnalyzer()
        self.scenario_generator = StochasticScenarioGenerator()
        self.lp_optimizer = StochasticProcurementOptimizer()

    def run_pipeline(self):
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')

        print("==========================================================================")
        print("🚀 CHẠY LUỒNG TỐI ƯU HÓA STOCHASTIC OR (PARETO ➔ XGBOOST ➔ MARKOV ➔ BOM LP)")
        print("==========================================================================")

        # 0. Sàng lọc Top Sản Phẩm theo ma trận ABC-XYZ theo Tháng
        print("\n🎯 [BƯỚC 0] SÀNG LỌC TOP SẢN PHẨM (PARETO 80/20 & ABC-XYZ):")
        top_skus = self.pareto_analyzer.get_top_products(target_classes=self.target_classes)
        if not top_skus:
            # Fallback nếu df_sales trống khi test chưa nối DB
            top_skus = ["536", "537", "538"]
            print(f"   -> Sử dụng danh sách Top SKU mẫu cho chế độ kiểm thử: {top_skus}")

        # 1 & 2. Tải và tính ma trận Markov rủi ro Vận hành
        print("\n🎲 [BƯỚC 2] TÍNH TOÁN RỦI RO VẬN HÀNH BẰNG MARKOV CHAIN:")
        inv_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "inventory.csv")
        sup_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "suppliers.csv")
        
        df_inv = pd.read_csv(inv_path) if os.path.exists(inv_path) else pd.DataFrame()
        df_sup = pd.read_csv(sup_path) if os.path.exists(sup_path) else pd.DataFrame()
        
        self.markov_analyzer.calculate_inventory_transition_matrix(df_inv)
        self.markov_analyzer.calculate_supplier_reliability_matrices(df_sup)

        # 3. Lắp ráp Kịch bản (Scenario Generation) cho các Top SKU
        print("\n🧩 [BƯỚC 1 & 3] DỰ BÁO NHU CẦU & LẮP RÁP KỊCH BẢN ĐA CHIỀU (SCENARIOS):")
        skus_scenarios: Dict[str, List[Dict]] = {}
        
        # Giả lập nhanh quantile forecast từ kết quả trung bình của Pareto hoặc Feast
        for p_id in top_skus:
            # Giả định kết quả từ XGBoost Quantile model cho tháng tới
            demand_quantiles = {
                "P10": 1200.0, # Thấp
                "P50": 1800.0, # Cơ sở
                "P90": 2600.0  # Bùng nổ
            }
            risk_probs = self.markov_analyzer.get_risk_probabilities(supplier_id="SUP001", current_inv_state="S1_Healthy")
            
            scenarios = self.scenario_generator.generate_scenarios_for_sku(
                product_id=p_id,
                demand_quantiles=demand_quantiles,
                risk_probs=risk_probs
            )
            skus_scenarios[p_id] = scenarios
            print(f"   -> SKU {p_id}: Đã tạo {len(scenarios)} kịch bản song song (Tổng xác suất = 100%)")

        # 4. Nổ BOM & Tối ưu hóa Kỳ vọng Chi phí bằng Stochastic LP
        print("\n🏆 [BƯỚC 4] NỔ BOM ĐỘNG & TỐI ƯU HÓA KỲ VỌNG CHI PHÍ MUA HÀNG (STOCHASTIC LP):")
        procurement_plan = self.lp_optimizer.optimize_expected_cost(skus_scenarios)

        total_expected_budget = 0.0
        total_penalty_saved = 0.0
        for item in procurement_plan:
            print(f"   ✅ [RM: {item['rm_id']}] Chọn NCC: {item['selected_supplier']} ({item['scenario_name']})")
            print(f"      -> Nhu cầu ròng kỳ vọng: {item['expected_net_req']:,.1f} | SL Đặt Mua: {item['order_qty']:,.1f} | Đơn giá sỉ: ${item['unit_price']:.2f} (-{item['discount_pct']}%)")
            print(f"      -> Chi phí mua kỳ vọng: ${item['expected_total_cost']:,.2f} | Phí rủi ro/thưởng: ${item['risk_penalty_cost']:,.2f}")
            print(f"      -> Note: {item['lp_decision_note']}")
            total_expected_budget += item['expected_total_cost'] + item['risk_penalty_cost']
            if item['risk_penalty_cost'] < 0:
                total_penalty_saved += abs(item['risk_penalty_cost'])

        print("--------------------------------------------------------------------------")
        print(f"💰 TỔNG KỲ VỌNG CHI PHÍ MUA HÀNG TỐI ƯU: ${total_expected_budget:,.2f}")
        print(f"🎉 TỔNG CHIẾT KHẤU / TIẾT KIỆM RỦI RO ĐẠT ĐƯỢC: ${total_penalty_saved:,.2f}")
        print("==========================================================================")
        return procurement_plan

if __name__ == "__main__":
    pipeline = StochasticAPSPipeline()
    pipeline.run_pipeline()

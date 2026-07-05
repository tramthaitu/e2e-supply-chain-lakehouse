import os
import csv
import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from config.aps_config import APSConfig

class ParetoAbcXyzAnalyzer:
    """
    Module phân tích Pareto (Luật 80/20) và ma trận phân lớp ABC-XYZ theo tháng (Monthly Bucket).
    Sàng lọc ra Top Sản Phẩm (nhóm A và các nhóm ổn định X, Y) để đưa vào 4 bước tối ưu hóa Stochastic OR.
    """
    def __init__(self):
        self.df_sales: pd.DataFrame = pd.DataFrame()
        self.segmentation_results: pd.DataFrame = pd.DataFrame()
        self._load_and_prepare_data()

    def _load_and_prepare_data(self):
        orders_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "orders.csv")
        items_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "order_items.csv")
        products_path = os.path.join(APSConfig.DATA_SOURCE_DIR, "products.csv")

        if not os.path.exists(orders_path) or not os.path.exists(items_path):
            print("❌ Không tìm thấy dữ liệu bán hàng trong data_source.")
            return

        print("📦 [PARETO ABC-XYZ] Đang tải dữ liệu bán hàng từ MinIO Lakehouse...")
        df_orders = pd.read_csv(orders_path, usecols=["order_id", "order_date", "order_status"])
        df_items = pd.read_csv(items_path, usecols=["order_id", "product_id", "quantity", "unit_price", "discount_amount"])
        df_products = pd.read_csv(products_path, usecols=["product_id", "product_name", "category"]) if os.path.exists(products_path) else pd.DataFrame()

        # Lọc đơn hàng thành công
        df_orders = df_orders[df_orders["order_status"] == "delivered"]
        df_merged = pd.merge(df_items, df_orders, on="order_id", how="inner")
        
        # Tính doanh thu ròng cho từng dòng
        df_merged["net_revenue"] = (df_merged["quantity"] * df_merged["unit_price"]) - df_merged["discount_amount"].fillna(0)
        df_merged["order_date"] = pd.to_datetime(df_merged["order_date"])
        
        # Gán mốc THÁNG (Monthly Bucket) theo yêu cầu
        df_merged["year_month"] = df_merged["order_date"].dt.to_period("M")
        df_merged["product_id"] = df_merged["product_id"].astype(str)
        
        if not df_products.empty:
            df_products["product_id"] = df_products["product_id"].astype(str)
            df_merged = pd.merge(df_merged, df_products, on="product_id", how="left")
            
        self.df_sales = df_merged

    def perform_segmentation(self) -> pd.DataFrame:
        """
        Thực hiện phân tích ABC (theo Doanh thu Pareto 80/20) và XYZ (theo hệ số biến thiên CV hàng tháng).
        """
        if self.df_sales.empty:
            return pd.DataFrame()

        print("⚙️ Đang phân tích Pareto 80/20 và hệ số biến thiên (CV) theo Tháng...")
        
        # 1. TỔNG HỢP THEO THÁNG (Monthly Bucket)
        monthly_sku = self.df_sales.groupby(["product_id", "year_month"]).agg({
            "quantity": "sum",
            "net_revenue": "sum",
            "product_name": "first",
            "category": "first"
        }).reset_index()

        # 2. PHÂN TÍCH ABC (Theo Doanh Thu)
        sku_summary = monthly_sku.groupby("product_id").agg({
            "net_revenue": "sum",
            "quantity": ["mean", "std", "sum"],
            "product_name": "first",
            "category": "first"
        })
        sku_summary.columns = ["total_revenue", "monthly_mean_qty", "monthly_std_qty", "total_qty"]
        sku_summary = sku_summary.reset_index().sort_values(by="total_revenue", ascending=False)

        # Tính tỷ lệ phần trăm tích lũy (Pareto 80/20)
        total_rev = sku_summary["total_revenue"].sum()
        sku_summary["rev_share_pct"] = (sku_summary["total_revenue"] / total_rev) * 100.0
        sku_summary["cum_rev_pct"] = sku_summary["rev_share_pct"].cumsum()

        # Phân lớp ABC: A (0-80%), B (80-95%), C (95-100%)
        def assign_abc(cum_pct):
            if cum_pct <= 80.0:
                return "A"
            elif cum_pct <= 95.0:
                return "B"
            else:
                return "C"

        sku_summary["abc_class"] = sku_summary["cum_rev_pct"].apply(assign_abc)

        # 3. PHÂN TÍCH XYZ (Theo Độ biến động Nhu cầu CV = Std / Mean)
        sku_summary["cv"] = sku_summary["monthly_std_qty"] / sku_summary["monthly_mean_qty"].replace(0, np.nan)
        sku_summary["cv"] = sku_summary["cv"].fillna(2.0) # Nếu chỉ bán 1 kỳ thì coi như biến động cao Z

        def assign_xyz(cv):
            if cv < 0.5:
                return "X" # Cầu ổn định, dễ đoán
            elif cv < 1.0:
                return "Y" # Cầu biến động trung bình / mùa vụ
            else:
                return "Z" # Cầu đứt quãng, giật cục khó đoán

        sku_summary["xyz_class"] = sku_summary["cv"].apply(assign_xyz)
        sku_summary["abc_xyz_matrix"] = sku_summary["abc_class"] + sku_summary["xyz_class"]

        self.segmentation_results = sku_summary
        return sku_summary

    def get_top_products(self, target_classes: List[str] = ["AX", "AY", "AZ", "BX", "BY"]) -> List[str]:
        """
        Lọc ra danh sách Top Sản Phẩm theo ma trận ABC-XYZ để đưa vào flow 4 bước Stochastic OR.
        Mặc định lấy toàn bộ Nhóm A và Nhóm B có cầu ổn định/mùa vụ (BX, BY).
        """
        if self.segmentation_results.empty:
            self.perform_segmentation()

        df_top = self.segmentation_results[self.segmentation_results["abc_xyz_matrix"].isin(target_classes)]
        top_ids = df_top["product_id"].tolist()
        
        print("==========================================================================")
        print(f"📊 [PARETO SUMMARY] ĐÃ LỌC RA {len(top_ids)} TOP SẢN PHẨM TRÊN TỔNG {len(self.segmentation_results)} SKU")
        print(f"🎯 Các lớp được chọn: {target_classes}")
        print("==========================================================================")
        
        # In tóm tắt phân bố
        matrix_counts = self.segmentation_results["abc_xyz_matrix"].value_counts().to_dict()
        for k, v in sorted(matrix_counts.items()):
            selected_flag = "✅ [CHỌN]" if k in target_classes else "❌ [BỎ QUA]"
            print(f"   • Nhóm {k}: {v:3d} SKU {selected_flag}")
            
        return top_ids

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    analyzer = ParetoAbcXyzAnalyzer()
    analyzer.perform_segmentation()
    top_skus = analyzer.get_top_products()
    print(f"\n📦 Danh sách Top 10 SKU đầu tiên: {top_skus[:10]}")

import os
import sys
import csv

# Đường dẫn thư mục gốc và nguồn dữ liệu tải về
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_SOURCE_DIR = os.path.join(ROOT_DIR, "data_source")
DOWNLOAD_DIR = r"C:\Users\Admin\Downloads\[ROUND 2] DATASET"

def harmonize_and_import_data():
    print("🚀 Đang đọc và chuẩn hóa dữ liệu OEE & Bảo trì từ thư mục Downloads...")
    
    # 1. Đọc danh sách product_id từ products.csv hiện có để lập ánh xạ (Mapping)
    products_path = os.path.join(DATA_SOURCE_DIR, "products.csv")
    product_ids = []
    if os.path.exists(products_path):
        with open(products_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_ids.append(row["product_id"])
    if not product_ids:
        # Fallback nếu chưa có products.csv
        product_ids = [str(i) for i in range(536, 600)]
    print(f"📦 Đã tải {len(product_ids)} product_id từ hệ thống hiện tại để chuẩn hóa.")

    # 2. Xử lý cross_reference.csv (Đổi tên cột OPERA NAME thành LINE_NAME cho khớp chuẩn)
    raw_cross = os.path.join(DOWNLOAD_DIR, "cross_reference.csv")
    target_cross = os.path.join(DATA_SOURCE_DIR, "cross_reference.csv")
    if os.path.exists(raw_cross):
        with open(raw_cross, mode="r", encoding="utf-8", errors="replace") as fin, \
             open(target_cross, mode="w", newline="", encoding="utf-8") as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout)
            header = next(reader, None)
            # Chuẩn hóa header thành EQUIPMENT_ID, LINE_NAME
            writer.writerow(["EQUIPMENT_ID", "LINE_NAME"])
            count_cross = 0
            for row in reader:
                if len(row) >= 2:
                    writer.writerow([row[0].strip(), row[1].strip()])
                    count_cross += 1
        print(f"✅ Đã chuẩn hóa cross_reference.csv ({count_cross} thiết bị nối với dây chuyền)")
    else:
        print(f"⚠️ Không tìm thấy {raw_cross}")

    # 3. Xử lý maintenance_order.csv (Lưu vào data_source với tên chuẩn maintenance_orders.csv)
    raw_maint = os.path.join(DOWNLOAD_DIR, "maintenance_order.csv")
    target_maint = os.path.join(DATA_SOURCE_DIR, "maintenance_orders.csv")
    if os.path.exists(raw_maint):
        with open(raw_maint, mode="r", encoding="utf-8", errors="replace") as fin, \
             open(target_maint, mode="w", newline="", encoding="utf-8") as fout:
            reader = csv.DictReader(fin)
            # Chuẩn hóa fieldnames
            writer = csv.DictWriter(fout, fieldnames=["order_id", "start_date", "equipment_id", "order_type", "description"])
            writer.writeheader()
            count_maint = 0
            for row in reader:
                writer.writerow({
                    "order_id": row.get("ORDER", "").strip(),
                    "start_date": row.get("BASIC_START_DATE", "").strip(),
                    "equipment_id": row.get("EQUIPMENT_ID", "").strip(),
                    "order_type": row.get("ORDER_TYPE", "").strip(),
                    "description": row.get("DESCRIPTION", "").strip()
                })
                count_maint += 1
        print(f"✅ Đã chuẩn hóa maintenance_orders.csv ({count_maint} lệnh bảo trì thiết bị)")
    else:
        print(f"⚠️ Không tìm thấy {raw_maint}")

    # 4. Xử lý production_logs.csv (Ánh xạ cột SIZE_TYPE sang product_id hiện có)
    raw_prod = os.path.join(DOWNLOAD_DIR, "production_logs.csv")
    target_prod = os.path.join(DATA_SOURCE_DIR, "production_logs.csv")
    if os.path.exists(raw_prod):
        size_type_map = {}
        count_prod = 0
        with open(raw_prod, mode="r", encoding="utf-8", errors="replace") as fin, \
             open(target_prod, mode="w", newline="", encoding="utf-8") as fout:
            reader = csv.reader(fin)
            header = next(reader, None)
            if header:
                # Loại bỏ cột SHIFT_NAME bị trùng lặp trong header gốc nếu có
                clean_header = []
                shift_indices = []
                for idx, col in enumerate(header):
                    col_name = col.strip()
                    if col_name == "SHIFT_NAME" and "SHIFT_NAME" in clean_header:
                        continue
                    clean_header.append(col_name)
                
                # Thêm cột product_id vào đầu để làm Foreign Key nối bảng
                clean_header = ["product_id"] + clean_header
                writer = csv.writer(fout)
                writer.writerow([h.lower() for h in clean_header])
                
                size_type_idx = header.index("SIZE_TYPE") if "SIZE_TYPE" in header else -1
                
                for row in reader:
                    if not row: continue
                    size_type_val = row[size_type_idx].strip() if size_type_idx >= 0 and size_type_idx < len(row) else "Unknown"
                    
                    # Ánh xạ deterministic (ổn định) từng size_type sang 1 product_id duy nhất
                    if size_type_val not in size_type_map:
                        mapped_id = product_ids[len(size_type_map) % len(product_ids)]
                        size_type_map[size_type_val] = mapped_id
                    p_id = size_type_map[size_type_val]
                    
                    # Ghi dòng dữ liệu đã thêm product_id vào
                    new_row = [p_id] + row[:len(clean_header)-1]
                    writer.writerow(new_row)
                    count_prod += 1
                    
        print(f"✅ Đã chuẩn hóa production_logs.csv ({count_prod:,} dòng log vận hành)")
        print(f"🔗 Đã ánh xạ thành công {len(size_type_map)} mã SIZE_TYPE sang danh sách product_id hiện có của bạn!")
    else:
        print(f"⚠️ Không tìm thấy {raw_prod}")

if __name__ == "__main__":
    harmonize_and_import_data()

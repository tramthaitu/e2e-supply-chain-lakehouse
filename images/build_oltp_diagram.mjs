// E2E Supply Chain — Complete OLTP Entity Relationship Diagram (ERD) - All 21 Tables
// Mỗi table được vẽ dưới dạng BẢNG HTML 2 CỘT CHUẨN MỰC (<table>) bên trong node để tuyệt đối KHÔNG BỊ NHẢY CHỮ.
import { writeFileSync } from "node:fs";
import { Diagram } from "/mnt/c/drawio/drawio-ai-kit/src/builder.mjs";
import { grid, renderTree, ossBox } from "/mnt/c/drawio/drawio-ai-kit/src/layout-engine.mjs";

const d = new Diagram("oltp_html_table_erd");

/**
 * Hàm tạo Node hình bảng chuẩn HTML (Table Grid) với 2 cột: [ Tên cột | Key / Note ]
 * Dùng <table> HTML bên trong label và tính toán chính xác chiều cao (h) dựa trên số dòng,
 * giúp chữ không bao giờ bị lệch hay nhảy vị trí do font chữ.
 */
function createTableBox(id, title, rows = []) {
  const h = 58 + rows.length * 22;
  const w = 320;

  const rowsHtml = rows.map(([colName, keyNote]) => {
    let keyStyle = "color: #6B7280;";
    if (keyNote.includes("PK")) keyStyle = "color: #DC2626; font-weight: bold;";
    else if (keyNote.includes("FK")) keyStyle = "color: #2563EB; font-weight: bold;";

    return `<tr style="border-bottom: 1px solid #E5E7EB;">
      <td style="padding: 4px 8px; font-family: 'Courier New', Courier, monospace; font-size: 11px; text-align: left; color: #111827;">${colName}</td>
      <td style="padding: 4px 8px; font-size: 11px; text-align: left; ${keyStyle}">${keyNote}</td>
    </tr>`;
  }).join("");

  const html = `<div style="font-family: Helvetica, Arial, sans-serif; width: 100%; box-sizing: border-box;">
    <div style="background-color: #F3F4F6; padding: 6px 10px; font-weight: bold; border-bottom: 2px solid #374151; font-size: 13px; text-align: left; color: #1F2937;">
      ${title}
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin: 0;">
      <thead>
        <tr style="background-color: #F9FAFB; border-bottom: 1px solid #D1D5DB; color: #4B5563;">
          <th style="padding: 4px 8px; text-align: left; width: 62%; font-weight: bold;">Tên cột</th>
          <th style="padding: 4px 8px; text-align: left; width: 38%; font-weight: bold;">Key / Note</th>
        </tr>
      </thead>
      <tbody>
        ${rowsHtml}
      </tbody>
    </table>
  </div>`;

  return ossBox(id, html, { w, h });
}

// ─────────────────────────────────────────────────────────────────────
//  GRID CHUNG UNIFIED (4 Cột × 6 Hàng = 21 Bảng)
// ─────────────────────────────────────────────────────────────────────
const erd = grid("erd", null, "supply_chain_db — Complete Entity Relationship Diagram (21/21 Tables from data_source)", {
  cols: 4, gap: 72, pad: 40,
  fill: "#FAFAFA", stroke: "#374151",
}, [
  // ── ROW 1: Master -> Order Flow ─────────────────────────────────────
  createTableBox("geography", "🗺️ geography.csv", [
    ["zip", "PK"],
    ["city", "-"],
    ["region", "-"],
    ["district", "-"]
  ]),

  createTableBox("customers", "👤 customers.csv", [
    ["customer_id", "PK"],
    ["zip", "FK"],
    ["city", "-"],
    ["signup_date", "-"],
    ["gender", "-"],
    ["age_group", "-"],
    ["acquisition_channel", "-"]
  ]),

  createTableBox("orders", "🧾 orders.csv (Central Hub)", [
    ["order_id", "PK"],
    ["customer_id", "FK"],
    ["zip", "FK"],
    ["order_date", "-"],
    ["order_status", "-"],
    ["payment_method", "-"],
    ["device_type", "-"],
    ["order_source", "-"]
  ]),

  createTableBox("order_items", "📋 order_items.csv", [
    ["order_id", "PK, FK"],
    ["product_id", "PK, FK"],
    ["promo_id", "FK"],
    ["promo_id_2", "FK"],
    ["quantity", "-"],
    ["unit_price", "-"],
    ["discount_amount", "-"]
  ]),

  // ── ROW 2: Order Sub-entities & Promotions ──────────────────────────
  createTableBox("payments", "💳 payments.csv", [
    ["order_id", "PK, FK"],
    ["payment_method", "-"],
    ["payment_value", "-"],
    ["installments", "-"]
  ]),

  createTableBox("shipments", "🚚 shipments.csv", [
    ["order_id", "PK, FK"],
    ["ship_date", "-"],
    ["delivery_date", "-"],
    ["shipping_fee", "-"]
  ]),

  createTableBox("returns", "↩️ returns.csv", [
    ["return_id", "PK"],
    ["order_id", "FK"],
    ["product_id", "FK"],
    ["return_date", "-"],
    ["return_reason", "-"],
    ["return_quantity", "-"],
    ["refund_amount", "-"]
  ]),

  createTableBox("promotions", "🎁 promotions.csv", [
    ["promo_id", "PK"],
    ["promo_name", "-"],
    ["promo_type", "-"],
    ["discount_value", "-"],
    ["start_date", "-"],
    ["end_date", "-"],
    ["applicable_category", "-"],
    ["promo_channel", "-"],
    ["stackable_flag", "-"],
    ["min_order_value", "-"]
  ]),

  // ── ROW 3: Reviews, Catalog Master & Inventory ──────────────────────
  createTableBox("reviews", "⭐ reviews.csv", [
    ["review_id", "PK"],
    ["order_id", "FK"],
    ["product_id", "FK"],
    ["customer_id", "FK"],
    ["review_date", "-"],
    ["rating", "-"],
    ["review_title", "-"]
  ]),

  createTableBox("products", "📦 products.csv (Catalog Hub)", [
    ["product_id", "PK"],
    ["supplier_id", "FK"],
    ["product_name", "-"],
    ["category", "-"],
    ["segment", "-"],
    ["size", "-"],
    ["color", "-"],
    ["price", "-"],
    ["cogs", "-"]
  ]),

  createTableBox("inventory", "🏭 inventory.csv", [
    ["snapshot_date", "PK"],
    ["product_id", "PK, FK"],
    ["stock_on_hand", "-"],
    ["units_received", "-"],
    ["units_sold", "-"],
    ["stockout_days", "-"],
    ["days_of_supply", "-"],
    ["fill_rate", "-"],
    ["stockout_flag", "-"],
    ["overstock_flag", "-"],
    ["reorder_flag", "-"],
    ["sell_through_rate", "-"],
    ["product_name", "-"],
    ["category", "-"],
    ["segment", "-"],
    ["year", "-"],
    ["month", "-"]
  ]),

  createTableBox("sales", "📈 sales.csv", [
    ["Date", "PK"],
    ["Revenue", "-"],
    ["COGS", "-"]
  ]),

  // ── ROW 4: Supply Chain BOM & Raw Materials ─────────────────────────
  createTableBox("suppliers", "🏢 suppliers.csv", [
    ["supplier_id", "PK"],
    ["supplier_name", "-"],
    ["country", "-"],
    ["reliability_score", "-"]
  ]),

  createTableBox("supplier_materials", "🔗 supplier_materials.csv (Bridge)", [
    ["supplier_id", "PK, FK"],
    ["rm_id", "PK, FK"],
    ["std_unit_price", "-"],
    ["base_lead_time", "-"],
    ["moq", "-"]
  ]),

  createTableBox("raw_materials", "🧱 raw_materials.csv", [
    ["rm_id", "PK"],
    ["rm_name", "-"],
    ["unit", "-"],
    ["std_cost", "-"]
  ]),

  createTableBox("bom", "🔩 bom.csv (Bill of Materials)", [
    ["product_id", "PK, FK"],
    ["rm_id", "PK, FK"],
    ["quantity_required", "-"]
  ]),

  // ── ROW 5: Procurement & Equipment Master ───────────────────────────
  createTableBox("procurement_scenarios", "📑 procurement_scenarios.csv", [
    ["scenario_id", "PK"],
    ["scenario_name", "-"],
    ["supplier_id", "FK"],
    ["rm_id", "FK"],
    ["unit_price", "-"],
    ["lead_time_days", "-"],
    ["min_qty", "-"],
    ["discount_pct", "-"]
  ]),

  createTableBox("web_traffic", "🌐 web_traffic.csv", [
    ["date", "PK"],
    ["sessions", "-"],
    ["unique_visitors", "-"],
    ["page_views", "-"],
    ["bounce_rate", "-"],
    ["avg_session_duration_sec", "-"],
    ["traffic_source", "-"]
  ]),

  createTableBox("cross_reference", "⚙️ cross_reference.csv (Eq Master)", [
    ["EQUIPMENT_ID", "PK"],
    ["LINE_NAME", "-"]
  ]),

  createTableBox("production_logs", "📊 production_logs.csv", [
    ["log_id", "PK"],
    ["equipment_id", "FK"],
    ["log_date", "-"],
    ["shift", "-"],
    ["oee_percentage", "-"],
    ["changeover_dur_min", "-"],
    ["scrap_rate_pct", "-"],
    ["target_output", "-"],
    ["actual_output", "-"]
  ]),

  // ── ROW 6: Maintenance Operations ───────────────────────────────────
  createTableBox("maintenance_orders", "🔧 maintenance_orders.csv", [
    ["order_id", "PK"],
    ["start_date", "-"],
    ["equipment_id", "FK"],
    ["order_type", "-"],
    ["description", "-"]
  ]),
]);

renderTree(d, erd, [48, 48]);
d.title("supply_chain_db — Complete Entity Relationship Diagram (21/21 Tables from data_source)");

// ─────────────────────────────────────────────────────────────────────
//  QUAN HỆ CARDINALITY (ĐÚNG YÊU CẦU + HOÀN THIỆN CÁC BẢNG LIÊN QUAN)
// ─────────────────────────────────────────────────────────────────────

// 1. orders ↔ payments: 1 : 1
d.link("orders", "payments", "1 : 1\n(thanh toán 1:1)", { dash: true });

// 2. orders ↔ shipments: 1 : 0 hoặc 1 (trạng thái shipped/delivered/returned)
d.link("orders", "shipments", "1 : 0..1\n(shipped/delivered/returned)", { dash: true });

// 3. orders ↔ returns: 1 : 0 hoặc nhiều (trạng thái returned)
d.link("orders", "returns", "1 : 0..N\n(trạng thái returned)", { dash: true });

// 4. orders ↔ reviews: 1 : 0 hoặc nhiều (trạng thái delivered, ∼20%)
d.link("orders", "reviews", "1 : 0..N\n(delivered, ∼20%)", { dash: true });

// 5. order_items ↔ promotions: nhiều : 0 hoặc 1
d.link("order_items", "promotions", "N : 0..1\n(khuyến mãi)", { dash: true });

// 6. products ↔ inventory: 1 : nhiều (1 dòng/sản phẩm/tháng)
d.link("products", "inventory", "1 : N\n(1 dòng/sản phẩm/tháng)", { dash: true });

// 7. Các bảng còn lại trong ERD (Chuẩn hóa logic khóa chính - ngoại)
d.link("geography",           "customers",           "1 : N\n(zip_code)",        { dash: true });
d.link("customers",           "orders",              "1 : N\n(đặt hàng)",       { dash: true });
d.link("orders",              "order_items",         "1 : N\n(chi tiết đơn)",   { dash: true });
d.link("products",            "order_items",         "1 : N\n(sản phẩm trong đơn)", { dash: true });
d.link("suppliers",           "products",            "1 : N\n(cung ứng)",       { dash: true });
d.link("products",            "bom",                 "1 : N\n(định mức BOM)",   { dash: true });
d.link("raw_materials",       "bom",                 "1 : N\n(nguyên liệu)",    { dash: true });

// Cầu nối N:N giữa suppliers và raw_materials qua supplier_materials & procurement_scenarios
d.link("suppliers",           "supplier_materials",  "1 : N\n(nhà cung cấp NL)", { dash: true });
d.link("raw_materials",       "supplier_materials",  "1 : N\n(báo giá NVL)",    { dash: true });
d.link("suppliers",           "procurement_scenarios", "1 : N\n(kịch bản giá)",   { dash: true });
d.link("raw_materials",       "procurement_scenarios", "1 : N\n(áp dụng NVL)",    { dash: true });

// Equipment Master (cross_reference) liên kết tới Log và Bảo trì
d.link("cross_reference",     "production_logs",     "1 : N\n(thiết bị sản xuất)", { dash: true });
d.link("cross_reference",     "maintenance_orders",  "1 : N\n(bảo trì thiết bị)", { dash: true });

// Khách hàng và Sản phẩm đánh giá
d.link("customers",           "reviews",             "1 : 0..N\n(người đánh giá)",{ dash: true });
d.link("products",            "reviews",             "1 : 0..N\n(sản phẩm được đánh giá)", { dash: true });

// Validate and save
const res = d.validate();
console.log("VALIDATION RESULT:", JSON.stringify(
  { ok: res.ok, errors: res.errors, warnings: res.warnings, advice: res.audit?.advice },
  null, 2
));

const outPath = "/mnt/c/E2E-Lakehouse-SupplyChain/oltp_postgres_schema.drawio";
writeFileSync(outPath, d.mxfile("supply_chain_db — Unified Complete ERD"));
console.log("\nSUCCESS: Generated diagram at C:\\E2E-Lakehouse-SupplyChain\\oltp_postgres_schema.drawio");


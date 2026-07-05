from feast import Entity

# Entity 1: Sản phẩm thành phẩm (Dùng cho bài toán Demand Forecasting & BOM explosion)
product_entity = Entity(
    name="product_id",
    value_type=Entity.ValueType.STRING,
    description="Mã định danh duy nhất của sản phẩm thành phẩm (Finished Goods ID)"
)

# Entity 2: Dây chuyền sản xuất (Dùng cho bài toán theo dõi OEE & Bảo trì PM10)
production_line_entity = Entity(
    name="line_name",
    value_type=Entity.ValueType.STRING,
    description="Tên định danh dây chuyền sản xuất tại nhà máy (Ví dụ: MKTU0101, MKBC0101)"
)

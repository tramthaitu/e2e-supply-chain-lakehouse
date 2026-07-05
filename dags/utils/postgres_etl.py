import os
import polars as pl
from sqlalchemy import create_engine, text

class PostgresLakehouseClient:
    """
    Client siêu nhẹ dành riêng cho Airflow (PythonOperator).
    Thao tác DDL và nạp CSV siêu tốc vào Postgres bằng Polars.
    """
    def __init__(self, pg_host, pg_port, pg_user, pg_password, pg_database):
        # URI cho Polars (ADBC)
        self.pg_uri = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        # URI cho SQLAlchemy (để chạy lệnh CREATE SCHEMA)
        self.pg_uri_sqlalchemy = f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

    def create_postgres_schemas(self, schemas: list):
        """Khởi tạo các Schema trong Postgres nếu chưa có."""
        engine = create_engine(self.pg_uri_sqlalchemy)
        with engine.connect() as conn:
            with conn.begin():
                for schema in schemas:
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
                    print(f"✅ Đã kiểm tra/tạo schema: {schema}")

    def load_csv_to_postgres(self, file_path: str, schema: str, table_name: str):
        """Đọc CSV bằng Polars và đẩy vào Postgres."""
        if not os.path.exists(file_path):
            print(f"⚠️ Bỏ qua: Không tìm thấy file {file_path}")
            return

        print(f"⏳ Đang nạp {file_path} vào Postgres bảng {schema}.{table_name}...")
        
        # Đọc bằng Polars (Nhẹ, không lo lỗi bộ nhớ của Airflow)
        df = pl.read_csv(file_path)
        full_table_name = f"{schema}.{table_name}"
        
        # Ghi đè vào Postgres
        df.write_database(
            table_name=full_table_name,
            connection=self.pg_uri,
            if_table_exists="replace",
            engine="adbc" 
        )
        print(f"✅ Đã nạp thành công {len(df)} dòng vào {full_table_name}")
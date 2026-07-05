from pyspark.sql import SparkSession

def create_branch(spark_session: SparkSession, new_branch: str, existing_branch: str = "main"):
    """Tạo nhánh mới từ nhánh hiện tại"""
    spark_session.sql(f"CREATE BRANCH IF NOT EXISTS {new_branch} IN iceberg FROM {existing_branch}")

def merge_branch(spark_session: SparkSession, source_branch: str, target_branch: str):
    """Gộp dữ liệu từ nhánh nguồn sang nhánh đích"""
    spark_session.sql(f"MERGE BRANCH {source_branch} INTO {target_branch} IN iceberg")

def delete_branch(spark_session: SparkSession, branch: str):
    """Xóa một nhánh"""
    spark_session.sql(f"DROP BRANCH {branch} IN iceberg")

def switch_to_branch(spark_session: SparkSession, branch: str):
    """Chuyển phiên làm việc hiện tại sang một nhánh cụ thể"""
    spark_session.sql(f"USE REFERENCE {branch} IN iceberg")
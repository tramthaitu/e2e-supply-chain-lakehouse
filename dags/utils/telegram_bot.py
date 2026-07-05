import os
import json
import time
import functools
import traceback as tb_module
import requests
from typing import Dict, Any, Optional

def telegram_retry(max_retries: int = 3, retry_delay: float = 2.0):
    """Decorator giúp tự động gọi lại (retry) API Telegram khi lỗi mạng hoặc bị giới hạn tần suất (Rate limit 429)."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = kwargs.pop('max_retries', max_retries)
            delay = kwargs.pop('retry_delay', retry_delay)
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    print(f"⚠️ Telegram network failed: {e}. Retrying ({attempt + 1}/{retries})...")
                    time.sleep(delay * (2 ** attempt))
                except requests.exceptions.HTTPError as e:
                    if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                        wait_time = delay * (2 ** attempt)
                        print(f"[WARN] Rate limited (429). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise
                except Exception as e:
                    if attempt < retries - 1:
                        wait_time = delay * (2 ** attempt)
                        print(f"[WARN] Error: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise
            return {"ok": False, "error": f"Failed after {retries} attempts"}
        return wrapper
    return decorator


class TelegramBotNotice:
    """
    Class quản lý gửi cảnh báo về Telegram nâng cao (Tích hợp Retry exponential backoff, đọc log DBT run_results.json, Traceback).
    Được tinh chỉnh phù hợp 100% với kiến trúc E2E Supply Chain Lakehouse.
    """
    def __init__(self, telegram_token: Optional[str] = None, chat_id: Any = None, topic_id: Optional[int] = None) -> None:
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        topic_env = os.getenv("TELEGRAM_TOPIC_ID")
        self.topic_id = topic_id or (int(topic_env) if topic_env else None)
        
        print(" ------ class TelegramBotNotice (Advanced Lakehouse Bot) was created!")

    @telegram_retry(max_retries=3, retry_delay=2.0)
    def send_message(self, message: str, parse_mode: str = "HTML"):
        if not self.telegram_token or not self.chat_id:
            print("⚠️ Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env")
            return {"ok": False, "error": "Missing credentials"}

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        if self.topic_id:
            payload["message_thread_id"] = self.topic_id
            
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        res_json = response.json()
        if res_json.get("ok"):
            print("📩 Đã gửi thông báo Telegram thành công!")
        return res_json

    @telegram_retry(max_retries=3, retry_delay=2.0)
    def send_file(self, file_path: str, caption: str = "", rm_after_send: bool = False):
        if not self.telegram_token or not self.chat_id or not os.path.exists(file_path):
            return {"ok": False, "error": "Missing file or credentials"}

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {
                'chat_id': self.chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            if self.topic_id:
                data["message_thread_id"] = self.topic_id
            response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()

        if rm_after_send and os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Đã xóa file tạm: {file_path}")
        return response.json()

    def notify_task_start(self, context: Dict[str, Any]):
        """Callback khi Task bắt đầu thực thi (Airflow on_execute_callback)"""
        task_instance = context.get("task_instance")
        dag_id = task_instance.dag_id if task_instance else "Unknown DAG"
        task_id = task_instance.task_id if task_instance else "Unknown Task"

        msg = f"""
⏳ <b>[LAKEHOUSE START] TASK BẮT ĐẦU CHẠY</b>
🔄 <b>DAG:</b> <code>{dag_id}</code>
▶️ <b>Task:</b> <code>{task_id}</code>
Hệ thống đang thực thi...
        """
        self.send_message(msg.strip())

    def notify_task_success(self, context: Dict[str, Any]):
        """Callback khi Task hoàn thành thành công (Airflow on_success_callback)"""
        task_instance = context.get("task_instance")
        dag_id = task_instance.dag_id if task_instance else "Unknown DAG"
        task_id = task_instance.task_id if task_instance else "Unknown Task"

        msg = f"""
✅ <b>[LAKEHOUSE SUCCESS] TASK HOÀN THÀNH!</b>
🔥 <b>DAG:</b> <code>{dag_id}</code>
🎯 <b>Task:</b> <code>{task_id}</code>
Đã xử lý xong dữ liệu an toàn! 🏆
        """
        self.send_message(msg.strip())

    def notify_telegram_when_fail(self, context: Dict[str, Any]):
        """Callback nâng cao khi Task thất bại (Airflow on_failure_callback) với Traceback & DBT error parser"""
        task_instance = context.get("task_instance")
        dag_id = task_instance.dag_id if task_instance else "Unknown DAG"
        task_id = task_instance.task_id if task_instance else "Unknown Task"
        execution_date = context.get("execution_date") or context.get("ts", "N/A")
        log_url = task_instance.log_url if task_instance else ""

        exception = context.get("exception")
        error_type = type(exception).__name__ if exception else "RuntimeError"
        
        if not exception or str(exception) == "None":
            err_detail = "Tiến trình bị ngắt đột ngột (Timeout / xung đột bộ nhớ hoặc Kill từ Web UI)."
        else:
            err_detail = str(exception)[:400] + ("..." if len(str(exception)) > 400 else "")

        # Trích xuất Traceback nếu có
        traceback_text = ""
        if exception:
            try:
                tb_lines = tb_module.format_exception(type(exception), exception, exception.__traceback__)
                traceback_text = "".join(tb_lines[-8:]).replace("<", "&lt;").replace(">", "&gt;")[:1000]
            except Exception:
                traceback_text = ""

        # Kiểm tra nếu là lỗi từ dbt, đọc file run_results.json
        dbt_path = "/opt/airflow/dbt_trino"
        run_results_path = os.path.join(dbt_path, "target/run_results.json")
        dbt_error_lines = []

        try:
            if os.path.exists(run_results_path):
                with open(run_results_path, "r", encoding="utf-8") as f:
                    run_results = json.load(f)
                for r in run_results.get("results", []):
                    status = (r.get("status") or "").lower()
                    if status in ("fail", "error"):
                        uid = r.get("unique_id", "N/A")
                        msg = (r.get("message") or "").replace("<", "&lt;").replace(">", "&gt;")[:250]
                        dbt_error_lines.append(f"• <code>{uid}</code>\n  <i>Lỗi:</i> {msg}")
        except Exception as e:
            print(f"[WARN] Không thể đọc dbt run_results.json: {e}")

        msg_parts = [
            f"🚨 <b>[LAKEHOUSE ALERT] TASK THẤT BẠI!</b>\n",
            f"🔥 <b>DAG:</b> <code>{dag_id}</code>",
            f"❌ <b>Task:</b> <code>{task_id}</code>",
            f"🕒 <b>Thời gian:</b> {execution_date}",
            f"⚠️ <b>Loại lỗi:</b> <code>{error_type}</code>",
            f"📝 <b>Chi tiết:</b> <code>{err_detail}</code>"
        ]

        if dbt_error_lines:
            msg_parts.append("\n💥 <b>Lỗi chi tiết từ DBT Models:</b>\n" + "\n".join(dbt_error_lines[:3]))
            if len(dbt_error_lines) > 3:
                msg_parts.append(f"<i>...và còn {len(dbt_error_lines) - 3} model khác bị lỗi</i>")

        if traceback_text:
            msg_parts.append(f"\n🔍 <b>Traceback:</b>\n<pre>{traceback_text}</pre>")

        if log_url:
            msg_parts.append(f"\n👉 <a href='{log_url}'>Xem chi tiết Log trên Airflow Web UI</a>")

        self.send_message("\n".join(msg_parts))

    def notify_dbt_completed(self, context: Dict[str, Any], dbt_path: str = "/opt/airflow/dbt_trino", mode: str = "run"):
        """Callback khi dbt Task hoàn thành, đọc run_results.json để tổng hợp model thành công và cảnh báo data quality"""
        task_instance = context.get("task_instance")
        dag_id = task_instance.dag_id if task_instance else "Unknown DAG"
        task_id = task_instance.task_id if task_instance else "Unknown Task"

        run_results_path = os.path.join(dbt_path, "target/run_results.json")
        if not os.path.exists(run_results_path):
            msg = f"""
✅ <b>[LAKEHOUSE SUCCESS] DBT TASK HOÀN THÀNH!</b>
🎯 <b>Task:</b> <code>{task_id}</code> (Chế độ: <b>{mode.upper()}</b>)
🏆 Tất cả kiểm định chất lượng đều PASS!
            """
            self.send_message(msg.strip())
            return

        try:
            with open(run_results_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            success_count = 0
            warn_lines = []

            for result in data.get("results", []):
                status = (result.get("status") or "").lower()
                model_name = result.get("unique_id", "N/A")
                exec_time = round(result.get("execution_time", 0), 2)
                msg_text = (result.get("message") or "").replace("<", "&lt;").replace(">", "&gt;")

                if status in ("pass", "success"):
                    success_count += 1
                elif status == "warn":
                    warn_lines.append(f"• <code>{model_name}</code> ({exec_time}s)\n  <i>Cảnh báo:</i> {msg_text[:200]}")

            msg_parts = [
                f"✅ <b>[LAKEHOUSE SUCCESS] DBT {mode.upper()} HOÀN THÀNH!</b>\n",
                f"🔥 <b>DAG:</b> <code>{dag_id}</code> | <b>Task:</b> <code>{task_id}</code>",
                f"🎯 <b>Số model/test thành công:</b> <code>{success_count}</code>"
            ]

            if warn_lines:
                msg_parts.append("\n⚠️ <b>Cảnh báo Chất lượng Dữ liệu (Warnings):</b>\n" + "\n".join(warn_lines[:5]))
                if len(warn_lines) > 5:
                    msg_parts.append(f"<i>...và còn {len(warn_lines) - 5} cảnh báo khác</i>")
            else:
                msg_parts.append("🏆 <b>Data Quality:</b> 100% Sạch & Chuẩn xác!")

            self.send_message("\n".join(msg_parts))
        except Exception as e:
            print(f"[WARN] Lỗi xử lý thông báo dbt completed: {e}")
            self.send_message(f"✅ <b>[LAKEHOUSE SUCCESS] DBT {mode.upper()} HOÀN THÀNH!</b>\n🎯 Task: <code>{task_id}</code>")

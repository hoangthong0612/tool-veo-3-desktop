# main.py
import tkinter as tk
from tkinter import ttk
import json
import os
import threading
import requests  # Đã import từ lần trước

from helper import load_config
from result_app import ResultApp
# Import các thành phần từ các file khác
from styles import setup_styles, BG_COLOR
from setup_window import SetupWindow
from main_app import MainApp


CONFIG_FILE = "config.json"


class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.geometry("900x700")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        # Biến lưu trữ thông tin
        self.cookie = ""
        self.api_key = ""
        self.access_token = ""  # <-- THÊM: Để lưu token sau khi đăng nhập

        setup_styles(self)

        load_config(self)

        self.setup_frame = SetupWindow(self, submit_command=self.start_validation_thread)
        self.main_app_frame = MainApp(self,create_story=self.create_story)

        # Logic điền form (giữ nguyên)
        if self.cookie or self.api_key:
            self.setup_frame.set_values(self.cookie, self.api_key)
            print("Đã tải config và điền vào form.")
        else:
            print("Không tìm thấy config, hiển thị form trống.")

        self.title("Đăng nhập")
        self.setup_frame.pack(expand=True, fill="both")

    # --- THAY ĐỔI HÀM NÀY ---
    def validate_credentials(self, cookie, api_key):
        """
        Kiểm tra cookie bằng cách gọi API thật.
        Trả về: (token, error_message)
        - Thành công: (access_token_string, None)
        - Thất bại: (None, "Lý do lỗi")
        """
        print("Đang gọi API để xác thực Cookie...")
        session_url = "https://labs.google/fx/api/auth/session"
        headers = {"Cookie": cookie}

        # (Nếu API key cần thiết, hãy thêm vào headers)
        # headers["X-API-Key"] = api_key

        try:
            response = requests.get(session_url, headers=headers, timeout=10)

            if not response.ok:
                return (None, f"Lỗi {response.status_code}: Không thể lấy token. Cookie hết hạn?")

            session_data = response.json()
            token = session_data.get("access_token")

            if not token:
                return (None, "Token không hợp lệ (Không tìm thấy access_token)")

            print("Xác thực Cookie thành công, nhận được token.")
            return (token, None)  # <-- Trả về token khi thành công

        except requests.exceptions.Timeout:
            return (None, "Lỗi: Hết thời gian chờ (timeout)")
        except requests.exceptions.ConnectionError:
            return (None, "Lỗi: Không thể kết nối đến máy chủ")
        except requests.exceptions.RequestException as e:
            return (None, f"Lỗi mạng: {e}")

    # --- THAY ĐỔI HÀM NÀY ---
    def validation_thread(self, cookie, api_key):
        """Hàm này chạy trên một luồng riêng biệt (background)."""
        token = None
        error_msg = None
        try:
            # 1. Gọi API, nhận về (token, error_msg)
            token, error_msg = self.validate_credentials(cookie, api_key)

        except Exception as e:
            error_msg = f"Lỗi hệ thống: {e}"
            token = None

        # 2. Gửi kết quả về luồng chính
        self.after(0, self.on_validation_complete, token, cookie, api_key, error_msg)

    def start_validation_thread(self):
        """Hàm này được gọi khi nhấn nút 'Tiếp Tục'."""
        cookie, api_key = self.setup_frame.get_values()

        if not cookie or not api_key:
            self.setup_frame.show_error("Vui lòng nhập đầy đủ Cookie và APIKey.")
            return

        self.setup_frame.show_loading()

        thread = threading.Thread(
            target=self.validation_thread,
            args=(cookie, api_key),
            daemon=True
        )
        thread.start()

    # --- THAY ĐỔI HÀM NÀY ---
    def on_validation_complete(self, token, cookie, api_key, error_msg=None):
        """
        Hàm này được gọi khi luồng nền hoàn thành.
        'token' sẽ có giá trị (string) nếu thành công, và là None nếu thất bại.
        """

        self.setup_frame.hide_loading()  # Tắt loading

        if token:  # <-- Kiểm tra token (thay vì is_valid)
            # --- THÀNH CÔNG ---
            print("Đăng nhập thành công, chuyển màn hình.")

            # Kiểm tra xem config có thay đổi không
            # (token mới luôn được coi là thay đổi nếu nó khác token cũ)
            config_changed = (
                    cookie != self.cookie or
                    api_key != self.api_key or
                    token != self.access_token
            )

            # Lưu các giá trị mới vào self
            self.cookie = cookie
            self.api_key = api_key
            self.access_token = token  # <-- Lưu token vào self

            if config_changed:
                print("Config đã thay đổi (hoặc có token mới), đang lưu file...")
                self.save_config()  # <-- Gọi save (giờ sẽ lưu cả token)

            # Chuyển màn hình
            self.setup_frame.pack_forget()
            self.main_app_frame.pack(expand=True, fill="both")
            self.title("Story to Video AI Generator")
        else:
            # --- THẤT BẠI ---
            print("Thông tin không hợp lệ.")
            if error_msg:
                self.setup_frame.show_error(error_msg)
            else:
                self.setup_frame.show_error("Cookie hoặc API Key không hợp lệ.")

    # --- THAY ĐỔI HÀM NÀY ---
    def save_config(self):
        """Lưu cookie, api_key, và access_token vào file config.json"""
        config_data = {
            "cookie": self.cookie,
            "api_key": self.api_key,
            "access_token": self.access_token  # <-- THÊM DÒNG NÀY
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Đã lưu config (bao gồm cả token) vào {CONFIG_FILE}")
        except Exception as e:
            print(f"Lỗi khi lưu config: {e}")

    def create_story(self):
        content, duration, language, aspect, style, folder = self.main_app_frame.get_all()
        result_app = ResultApp(self,content, duration, language, aspect, style, folder)
        self.main_app_frame.pack_forget()
        result_app.title = "Kết quả"
        result_app.pack(expand=True, fill="both")
    # --- THAY ĐỔI HÀM NÀY ---
    # def load_config(self):
    #     """Tải cookie, api_key, và access_token từ file config.json nếu có"""
    #     if os.path.exists(CONFIG_FILE):
    #         try:
    #             with open(CONFIG_FILE, 'r') as f:
    #                 config_data = json.load(f)
    #                 self.cookie = config_data.get("cookie", "")
    #                 self.api_key = config_data.get("api_key", "")
    #                 self.access_token = config_data.get("access_token", "")  # <-- THÊM DÒNG NÀY
    #         except Exception as e:
    #             print(f"Lỗi khi tải config: {e}")
    #             # (Có thể xóa file config lỗi nếu cần)
    #             # os.remove(CONFIG_FILE)


# -----------------------------------------------
# --- CHẠY ỨNG DỤNG ---
# -----------------------------------------------
if __name__ == "__main__":
    app = Application()
    app.mainloop()

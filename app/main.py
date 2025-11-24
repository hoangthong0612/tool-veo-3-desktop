# app/main.py
import customtkinter
import json
import os
import threading
import requests

from app.utils.helper import load_config
from app.views.result_view import ResultApp
from app.views.setup_window import SetupWindow
from app.views.main_app_view import MainApp
from app.views.upload_view import UploadView # <-- IMPORT MỚI

CONFIG_FILE = "config.json"

class Application(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("1100x700") # <-- Tăng chiều rộng để chứa menu
        self.resizable(False, False)

        # Biến lưu trữ thông tin
        self.cookie = ""
        self.api_key = ""
        self.access_token = ""

        # --- CẤU TRÚC LẠI GIAO DIỆN ---

        # 1. Tạo Menu Frame (Sidebar)
        self.menu_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        # (Sẽ pack_forget() lúc đầu)

        # 2. Tạo Content Frame (Container)
        # Đây là nơi chứa các màn hình (Setup, Main, Result)
        self.container = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True)

        # 3. Thêm các nút vào Menu Frame
        self.menu_label = customtkinter.CTkLabel(self.menu_frame, text="Menu",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"))
        self.menu_label.pack(pady=20, padx=20)

        self.new_project_button = customtkinter.CTkButton(self.menu_frame, text="New Project",
                                                         command=self.show_main_app_view)
        self.new_project_button.pack(pady=10, padx=20, fill="x")

        self.upload_button = customtkinter.CTkButton(self.menu_frame, text="Batch Video (Excel)",
                                                     command=self.show_upload_view,
                                                     fg_color="#E04F5F",
                                                     hover_color="#C03947")  # Màu khác cho dễ phân biệt
        self.upload_button.pack(pady=10, padx=20, fill="x")

        self.logout_button = customtkinter.CTkButton(self.menu_frame, text="Logout",
                                                    command=self.show_setup_view,
                                                    fg_color="transparent", border_width=2)
        self.logout_button.pack(pady=20, padx=20, fill="x", side="bottom")

        # 4. Khởi tạo các View (màn hình)
        # Lưu ý: Parent của chúng là self.container
        self.setup_frame = SetupWindow(self.container, submit_command=self.start_validation_thread)
        self.main_app_frame = MainApp(self.container, create_story=self.create_story)
        self.upload_view_frame = UploadView(self.container,
                                            back_command=self.show_main_app_view)  # <-- KHỞI TẠO VIEW MỚI
        self.result_app_frame = None # Sẽ được tạo khi cần

        # 5. Tải config và hiển thị màn hình đầu tiên
        load_config(self)
        if self.cookie or self.api_key:
            self.setup_frame.set_values(self.cookie, self.api_key)
            print("Đã tải config và điền vào form.")
        else:
            print("Không tìm thấy config, hiển thị form trống.")

        # 6. Hiển thị màn hình đăng nhập (không có menu)
        self.show_setup_view()

    # --- CÁC HÀM QUẢN LÝ VIEW (MỚI) ---
    def show_upload_view(self):
        """Hiển thị màn hình Upload Excel."""
        self.menu_frame.pack(side="left", fill="y")  # Đảm bảo menu hiện

        self.setup_frame.pack_forget()
        self.main_app_frame.pack_forget()
        if self.result_app_frame:
            self.result_app_frame.pack_forget()

        self.upload_view_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.title("Batch Video Processing")

    def show_setup_view(self):
        """Hiển thị màn hình đăng nhập VÀ ẨN menu."""
        # Ẩn menu
        self.menu_frame.pack_forget()

        # Ẩn các màn hình khác
        self.main_app_frame.pack_forget()
        if self.result_app_frame:
            self.result_app_frame.pack_forget()

        # Hiển thị màn hình setup
        self.title("Đăng nhập")
        self.setup_frame.pack(expand=True, fill="both")

    def show_main_app_view(self):
        """Hiển thị màn hình chính VÀ HIỆN menu."""
        # Hiện menu (nếu chưa hiện)
        self.menu_frame.pack(side="left", fill="y")

        # Ẩn các màn hình khác
        self.setup_frame.pack_forget()
        if self.result_app_frame:
            self.result_app_frame.pack_forget()

        # Hiển thị màn hình chính
        self.title("Story to Video AI Generator")
        self.main_app_frame.pack(expand=True, fill="both", padx=40, pady=40)

    # --- CÁC HÀM LOGIC (CẬP NHẬT) ---

    def on_validation_complete(self, token, cookie, api_key, error_msg=None):
        """Được gọi khi xác thực xong."""
        self.setup_frame.hide_loading()

        if token:
            print("Đăng nhập thành công, chuyển màn hình.")
            # ... (code lưu config giữ nguyên) ...
            config_changed = (
                    cookie != self.cookie or
                    api_key != self.api_key or
                    token != self.access_token
            )
            self.cookie = cookie
            self.api_key = api_key
            self.access_token = token
            if config_changed:
                print("Config đã thay đổi (hoặc có token mới), đang lưu file...")
                self.save_config()

            # --- THAY ĐỔI CHÍNH ---
            # Gọi hàm show_main_app_view thay vì pack thủ công
            self.show_main_app_view()
        else:
            print("Thông tin không hợp lệ.")
            if error_msg:
                self.setup_frame.show_error(error_msg)
            else:
                self.setup_frame.show_error("Cookie hoặc API Key không hợp lệ.")

    def create_story(self):
        """Lấy thông tin từ MainApp và tạo ResultApp"""
        content, duration, language, aspect, style, folder = self.main_app_frame.get_all()
        
        # Ẩn màn hình main
        self.main_app_frame.pack_forget()

        # Tạo hoặc tái tạo ResultApp
        if self.result_app_frame:
            self.result_app_frame.pack_forget() # Xóa cái cũ
            
        self.result_app_frame = ResultApp(
            self.container, 
            content, duration, language, aspect, style, folder,
            back_command=self.show_main_app_view # <-- Thêm lệnh quay lại
        )

        self.title("Kết quả - Đang Xử Lý...")
        self.result_app_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
    # ... (Các hàm validate_credentials, validation_thread, start_validation_thread, save_config giữ nguyên) ...
    def validate_credentials(self, cookie, api_key):
        # (Giữ nguyên code)
        print("Đang gọi API để xác thực Cookie...")
        session_url = "https://labs.google/fx/api/auth/session"
        headers = {"Cookie": cookie}
        try:
            response = requests.get(session_url, headers=headers, timeout=10)
            if not response.ok:
                return (None, f"Lỗi {response.status_code}: Không thể lấy token. Cookie hết hạn?")
            session_data = response.json()
            token = session_data.get("access_token")
            if not token:
                return (None, "Token không hợp lệ (Không tìm thấy access_token)")
            print("Xác thực Cookie thành công, nhận được token.")
            return (token, None)
        except requests.exceptions.Timeout:
            return (None, "Lỗi: Hết thời gian chờ (timeout)")
        except requests.exceptions.ConnectionError:
            return (None, "Lỗi: Không thể kết nối đến máy chủ")
        except requests.exceptions.RequestException as e:
            return (None, f"Lỗi mạng: {e}")

    def validation_thread(self, cookie, api_key):
        # (Giữ nguyên code)
        token = None
        error_msg = None
        try:
            token, error_msg = self.validate_credentials(cookie, api_key)
        except Exception as e:
            error_msg = f"Lỗi hệ thống: {e}"
            token = None
        self.after(0, self.on_validation_complete, token, cookie, api_key, error_msg)

    def start_validation_thread(self):
        # (Giữ nguyên code)
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

    def save_config(self):
        # (GiT giữ nguyên code)
        config_data = {
            "cookie": self.cookie,
            "api_key": self.api_key,
            "access_token": self.access_token
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Đã lưu config (bao gồm cả token) vào {CONFIG_FILE}")
        except Exception as e:
            print(f"Lỗi khi lưu config: {e}")
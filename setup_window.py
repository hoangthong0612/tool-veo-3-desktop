# setup_window.py
import tkinter as tk
from tkinter import ttk


class SetupWindow(ttk.Frame):
    def __init__(self, parent, submit_command):
        super().__init__(parent, style="TFrame")

        # Frame con để căn giữa nội dung
        center_frame = ttk.Frame(self, style="TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = ttk.Label(center_frame, text="Nhập Thông Tin", style="Title.TLabel")
        title.pack(pady=20)

        # --- Nhập Cookie ---
        cookie_label = ttk.Label(center_frame, text="Nhập Cookie")
        cookie_label.pack(anchor="w", pady=(10, 5))

        self.cookie_entry = ttk.Entry(center_frame, width=60, font=("Arial", 10))
        self.cookie_entry.pack(fill="x", ipady=5, padx=20)

        # --- Nhập APIKey ---
        apikey_label = ttk.Label(center_frame, text="Nhập APIKey")
        apikey_label.pack(anchor="w", pady=(10, 5))

        self.apikey_entry = ttk.Entry(center_frame, width=60, font=("Arial", 10), show="*")
        self.apikey_entry.pack(fill="x", ipady=5, padx=20)

        # --- Nhãn báo lỗi (dùng style Error.TLabel) ---
        self.error_label = ttk.Label(center_frame, text="", style="Error.TLabel")
        self.error_label.pack(pady=15)

        # --- THÊM: Loading Spinner ---
        self.loading_bar = ttk.Progressbar(center_frame, mode='indeterminate')
        # Tạm thời ẩn nó, chúng ta sẽ 'pack' nó khi cần

        # --- THÊM: Lưu lại nút submit ---
        self.submit_btn = ttk.Button(center_frame,
                                     text="Tiếp Tục",
                                     style="Create.TButton",
                                     command=submit_command)
        self.submit_btn.pack(fill="x", ipady=10, pady=20, padx=20)

    def get_values(self):
        """Trả về giá trị của hai ô nhập liệu"""
        return self.cookie_entry.get(), self.apikey_entry.get()

    def set_values(self, cookie, api_key):
        """Điền giá trị được tải từ config vào các ô entry."""
        self.cookie_entry.delete(0, tk.END)
        self.apikey_entry.delete(0, tk.END)
        if cookie:
            self.cookie_entry.insert(0, cookie)
        if api_key:
            self.apikey_entry.insert(0, api_key)

    def show_error(self, message):
        """Hiển thị thông báo lỗi"""
        self.error_label.config(text=message)

    # --- THÊM HÀM MỚI ---
    def show_loading(self):
        """Hiển thị trạng thái loading và vô hiệu hóa input."""
        self.error_label.config(text="")  # Xóa lỗi cũ
        # Ẩn nút và hiện loading bar
        self.submit_btn.pack_forget()
        self.loading_bar.pack(fill="x", padx=20, pady=20)
        self.loading_bar.start()

        # Vô hiệu hóa các ô nhập liệu
        self.cookie_entry.config(state="disabled")
        self.apikey_entry.config(state="disabled")

    # --- THÊM HÀM MỚI ---
    def hide_loading(self):
        """Tắt loading và kích hoạt lại input."""
        self.loading_bar.stop()
        self.loading_bar.pack_forget()
        self.submit_btn.pack(fill="x", ipady=10, pady=20, padx=20)

        # Kích hoạt lại
        self.cookie_entry.config(state="normal")
        self.apikey_entry.config(state="normal")
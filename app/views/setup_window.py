# setup_window.py
import customtkinter
import tkinter as tk # Vẫn cần cho tk.END

class SetupWindow(customtkinter.CTkFrame):
    def __init__(self, parent, submit_command):
        # fg_color="transparent" để nó dùng chung màu nền của cửa sổ cha
        super().__init__(parent, fg_color="transparent")

        # Frame con để căn giữa nội dung
        self.center_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = customtkinter.CTkLabel(self.center_frame, text="Nhập Thông Tin", 
                                       font=customtkinter.CTkFont(size=28, weight="bold"))
        title.pack(pady=20)

        # --- Nhập Cookie ---
        cookie_label = customtkinter.CTkLabel(self.center_frame, text="Nhập Cookie")
        cookie_label.pack(anchor="w", pady=(10, 5), padx=20)

        self.cookie_entry = customtkinter.CTkEntry(self.center_frame, width=400, 
                                                   font=("Arial", 12))
        self.cookie_entry.pack(fill="x", ipady=5, padx=20)

        # --- Nhập APIKey ---
        apikey_label = customtkinter.CTkLabel(self.center_frame, text="Nhập APIKey")
        apikey_label.pack(anchor="w", pady=(10, 5), padx=20)

        self.apikey_entry = customtkinter.CTkEntry(self.center_frame, width=400, 
                                                   font=("Arial", 12), show="*")
        self.apikey_entry.pack(fill="x", ipady=5, padx=20)

        # --- Nhãn báo lỗi ---
        self.error_label = customtkinter.CTkLabel(self.center_frame, text="", 
                                                  text_color="#FF5555")
        self.error_label.pack(pady=15)

        # --- Loading Spinner ---
        self.loading_bar = customtkinter.CTkProgressBar(self.center_frame, 
                                                        mode='indeterminate')
        
        # --- Nút submit ---
        self.submit_btn = customtkinter.CTkButton(self.center_frame,
                                                  text="Tiếp Tục",
                                                  command=submit_command,
                                                  font=customtkinter.CTkFont(size=14, weight="bold"))
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
        self.error_label.configure(text=message)

    def show_loading(self):
        """Hiển thị trạng thái loading và vô hiệu hóa input."""
        self.error_label.configure(text="")  # Xóa lỗi cũ
        self.submit_btn.pack_forget()
        self.loading_bar.pack(fill="x", padx=20, pady=20)
        self.loading_bar.start()

        self.cookie_entry.configure(state="disabled")
        self.apikey_entry.configure(state="disabled")

    def hide_loading(self):
        """Tắt loading và kích hoạt lại input."""
        self.loading_bar.stop()
        self.loading_bar.pack_forget()
        self.submit_btn.pack(fill="x", ipady=10, pady=20, padx=20)

        self.cookie_entry.configure(state="normal")
        self.apikey_entry.configure(state="normal")
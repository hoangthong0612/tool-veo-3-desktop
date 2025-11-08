import customtkinter
from app.main import Application

# Cài đặt giao diện chung cho toàn ứng dụng
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
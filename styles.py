# styles.py
from tkinter import ttk

# --- Màu sắc và Fonts ---
BG_COLOR = "#1E1E2F"
ENTRY_BG_COLOR = "#2B2B3A"
FG_COLOR = "#FFFFFF"
PURPLE_COLOR = "#7F00FF"
PURPLE_ACTIVE_COLOR = "#9933FF"
LABEL_FG_COLOR = "#B0B0C0"
ERROR_COLOR = "#FF5555"

def setup_styles(app):
    """
    Hàm này chứa tất cả cấu hình style cho toàn bộ ứng dụng.
    Nó nhận vào 'app' (instance của tk.Tk) để tạo style.
    """
    style = ttk.Style(app)
    style.theme_use("clam")

    # Cấu hình chung
    style.configure(".",
                    background=BG_COLOR,
                    foreground=FG_COLOR,
                    font=("Arial", 10))

    # Cấu hình Frame
    style.configure("TFrame", background=BG_COLOR)

    # Cấu hình Label
    style.configure("TLabel", background=BG_COLOR, foreground=LABEL_FG_COLOR)
    style.configure("Title.TLabel",
                    font=("Arial", 28, "bold"),
                    foreground=FG_COLOR,
                    anchor="center")
    style.configure("Subtitle.TLabel",
                    font=("Arial", 12),
                    foreground=LABEL_FG_COLOR,
                    anchor="center")
    style.configure("Error.TLabel",
                    background=BG_COLOR,
                    foreground=ERROR_COLOR,
                    anchor="center")

    # Cấu hình Nút
    style.configure("Suggest.TButton",
                    background=PURPLE_COLOR,
                    foreground=FG_COLOR,
                    font=("Arial", 9, "bold"),
                    borderwidth=0)
    style.map("Suggest.TButton",
              background=[('active', PURPLE_ACTIVE_COLOR)])

    style.configure("Create.TButton",
                    background=PURPLE_COLOR,
                    foreground=FG_COLOR,
                    font=("Arial", 12, "bold"),
                    borderwidth=0)
    style.map("Create.TButton",
              background=[('active', PURPLE_ACTIVE_COLOR)])

    style.configure("ActiveTab.TButton",
                    background=PURPLE_COLOR,
                    foreground=FG_COLOR,
                    font=("Arial", 11, "bold"),
                    borderwidth=0)
    style.map("ActiveTab.TButton",
              background=[('active', PURPLE_ACTIVE_COLOR)])

    style.configure("InactiveTab.TButton",
                    background=ENTRY_BG_COLOR,
                    foreground=FG_COLOR,
                    font=("Arial", 11, "bold"),
                    borderwidth=0)
    style.map("InactiveTab.TButton",
              background=[('active', PURPLE_ACTIVE_COLOR)])

    # Cấu hình Entry
    style.configure("TEntry",
                    fieldbackground=ENTRY_BG_COLOR,
                    foreground=FG_COLOR,
                    borderwidth=1,
                    bordercolor=ENTRY_BG_COLOR,
                    insertbackground=FG_COLOR)
    style.map("TEntry",
              bordercolor=[('focus', PURPLE_COLOR)],
              fieldbackground=[('focus', ENTRY_BG_COLOR)])

    # Cấu hình Combobox
    style.configure("TCombobox",
                    fieldbackground=ENTRY_BG_COLOR,
                    background=ENTRY_BG_COLOR,
                    foreground=FG_COLOR,
                    arrowcolor=FG_COLOR,
                    bordercolor=ENTRY_BG_COLOR,
                    insertbackground=FG_COLOR)
    style.map("TCombobox",
              fieldbackground=[('readonly', ENTRY_BG_COLOR)],
              background=[('readonly', ENTRY_BG_COLOR)])

    # Cấu hình Checkbutton
    style.configure("TCheckbutton",
                    background=BG_COLOR,
                    foreground=LABEL_FG_COLOR,
                    font=("Arial", 10))
    style.map("TCheckbutton",
              indicatorcolor=[('selected', PURPLE_COLOR), ('!selected', ENTRY_BG_COLOR)],
              background=[('active', BG_COLOR)])
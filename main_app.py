# main_app.py
import tkinter as tk
from tkinter import ttk

from result_app import ResultApp
# Import các màu cần thiết cho widget tk (không phải ttk)
from styles import ENTRY_BG_COLOR, FG_COLOR, BG_COLOR
from gemini_service import suggest_idea, generate_script_and_characters
import threading

class MainApp(ttk.Frame):
    def __init__(self, parent,create_story):
        super().__init__(parent, style="TFrame", padding="40 40 40 40")
        center_frame = ttk.Frame(self, style="TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        # --- Tiêu đề ---
        title_label = ttk.Label(self, text="Story to Video AI Generator", style="Title.TLabel")
        title_label.pack(pady=(10, 5), fill="x")

        subtitle_label = ttk.Label(self, text="Bring your stories to life with AI-powered video creation.",
                                   style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 30), fill="x")

        # --- Khung chứa Tab ---
        tab_frame = ttk.Frame(self)
        tab_frame.pack(pady=10)

        self.idea_tab_btn = ttk.Button(tab_frame, text="From Idea", style="ActiveTab.TButton", width=25,
                                       command=self.show_idea_tab)
        self.idea_tab_btn.pack(side="left", padx=5, ipady=5)

        self.script_tab_btn = ttk.Button(tab_frame, text="From Script", style="InactiveTab.TButton", width=25,
                                         command=self.show_script_tab)
        self.script_tab_btn.pack(side="left", padx=5, ipady=5)

        # --- Khung "Your Idea" ---
        idea_frame = ttk.Frame(self)
        idea_frame.pack(fill="x", pady=15)

        self.idea_label = ttk.Label(idea_frame, text="Your Idea")
        self.idea_label.pack(anchor="w", pady=(0, 5))

        # Frame chứa Text widget (dùng tk.Frame nên cần set màu thủ công)
        text_container = tk.Frame(idea_frame,
                                  bg=ENTRY_BG_COLOR,  # Màu từ styles.py
                                  borderwidth=1,
                                  relief="solid",
                                  highlightbackground=ENTRY_BG_COLOR,  # Màu từ styles.py
                                  highlightthickness=1)
        text_container.pack(fill="x", expand=True)

        # Dùng tk.Text nên cần set màu thủ công
        self.idea_text = tk.Text(text_container,
                                 height=8,
                                 bg=ENTRY_BG_COLOR,  # Màu từ styles.py
                                 fg=FG_COLOR,  # Màu từ styles.py
                                 font=("Arial", 10),
                                 borderwidth=0,
                                 highlightthickness=0,
                                 insertbackground=FG_COLOR)  # Màu từ styles.py
        self.idea_text.insert("1.0", "A cat astronaut exploring a planet made of cheese....")
        self.idea_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.suggest_btn_1 = ttk.Button(text_container, text="Suggest", style="Suggest.TButton")
        self.suggest_btn_1.place(relx=0.98, rely=0.95, anchor="se")

        # --- Khung Cài đặt ---
        settings_frame = ttk.Frame(self)
        settings_frame.pack(fill="x", pady=15)
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(2, weight=1)
        settings_frame.columnconfigure(3, weight=1)

        # Cột 1: Style
        style_frame = ttk.Frame(settings_frame)
        style_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        style_label = ttk.Label(style_frame, text="Style")
        style_label.pack(anchor="w", pady=(0, 5))
        style_entry_frame = ttk.Frame(style_frame, style="TEntry")
        style_entry_frame.pack(fill="x")
        self.style_entry = ttk.Entry(style_entry_frame)
        self.style_entry.insert(0, "Cinematic, hyper-realistic, 4K")
        self.style_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=8)
        suggest_btn_2 = ttk.Button(style_entry_frame, text="Suggest", style="Suggest.TButton")
        suggest_btn_2.pack(side="right", padx=(5, 8), pady=8)

        # Cột 2: Duration
        duration_frame = ttk.Frame(settings_frame)
        duration_frame.grid(row=0, column=1, sticky="ew", padx=10)
        duration_label = ttk.Label(duration_frame, text="Duration (seconds)")
        duration_label.pack(anchor="w", pady=(0, 5))
        self.duration_entry = ttk.Entry(duration_frame)
        self.duration_entry.insert(0, "16")
        self.duration_entry.pack(fill="x", ipady=4)

        # Cột 3: Aspect Ratio
        aspect_frame = ttk.Frame(settings_frame)
        aspect_frame.grid(row=0, column=2, sticky="ew", padx=10)
        aspect_label = ttk.Label(aspect_frame, text="Aspect Ratio")
        aspect_label.pack(anchor="w", pady=(0, 5))
        self.aspect_combo = ttk.Combobox(aspect_frame,
                                         values=["16:9", "9:16"],
                                         state="readonly")
        self.aspect_combo.set("16:9")
        self.aspect_combo.pack(fill="x", ipady=4)

        # Cột 4: Language
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.grid(row=0, column=3, sticky="ew", padx=(10, 0))
        lang_label = ttk.Label(lang_frame, text="Language")
        lang_label.pack(anchor="w", pady=(0, 5))
        self.lang_combo = ttk.Combobox(lang_frame,
                                       values=["English", "Vietnamese", "Japanese", "Spanish"],
                                       state="readonly")
        self.lang_combo.set("English")
        self.lang_combo.pack(fill="x", ipady=4)

        # --- Checkbox ---
        self.narrate_var = tk.BooleanVar()
        self.narrate_check = ttk.Checkbutton(self,
                                             text="Include AI-generated narration for each scene",
                                             variable=self.narrate_var)
        self.narrate_check.pack(anchor="w", pady=20)



        # --- Nút Create ---
        self.create_button = ttk.Button(self,
                                   text="Create Story & Characters",
                                   command=create_story,
                                   style="Create.TButton")
        self.create_button.pack(fill="x", ipady=10, pady=10, )
        center_frame = ttk.Frame(self, style="TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.loading_label = ttk.Label(center_frame, text="Đang xử lý...")
        self.progressbar = ttk.Progressbar(center_frame, mode='indeterminate')

    # --- Các hàm xử lý tab ---
    def show_idea_tab(self):
        self.idea_tab_btn.configure(style="ActiveTab.TButton")
        self.script_tab_btn.configure(style="InactiveTab.TButton")
        self.idea_label.config(text="Your Idea")
        self.idea_text.delete("1.0", tk.END)
        self.idea_text.insert("1.0", "A cat astronaut exploring a planet made of cheese....")
        self.suggest_btn_1.place(relx=0.98, rely=0.95, anchor="se")

    def show_script_tab(self):
        self.idea_tab_btn.configure(style="InactiveTab.TButton")
        self.script_tab_btn.configure(style="ActiveTab.TButton")
        self.idea_label.config(text="Nhập Script")
        self.idea_text.delete("1.0", tk.END)
        self.idea_text.insert("1.0", "Dán kịch bản (script) của bạn vào đây...")
        self.suggest_btn_1.place_forget()

    # def show_loading(self):
    #     """Hiển thị trạng thái loading và vô hiệu hóa input."""
    #     # self.error_label.config(text="")  # Xóa lỗi cũ
    #     # Ẩn nút và hiện loading bar
    #     print()
    #     self.create_button.pack_forget()
    #     self.loading_bar.pack(fill="x", padx=20, pady=20)
    #     self.loading_bar.start()
    #
    #     threading.Thread(target=self.run_api_in_thread, daemon=True).start()

    def run_api_in_thread(self,content, duration, language, aspect):
        """Hàm này chạy trong LUỒNG NỀN (không làm đơ GUI)"""
        try:
            idea = suggest_idea(idea=content)
            print(idea)


        except Exception as e:
            # Xử lý nếu API bị lỗi
            print(f"THREAD: Lỗi API: {e}")
            # self.controller.after(0, self.on_api_error, str(e))


    def create_story(self):
        content, duration, language, aspect = self.get_all()
        result_app = ResultApp(self,content, duration, language, aspect)
        self.pack_forget()
        result_app.pack(expand=True, fill="both")
        # self.show_loading()
        # self.create_button.config(state='disabled')
        # self.loading_label.pack(pady=5)
        # self.progressbar.pack(pady=10, fill="x", padx=50)
        # self.progressbar.start(10)  # Bắt đầu chạy animation
        # threading.Thread(target=self.run_api_in_thread,args=(content, duration, language, aspect), daemon=True).start()
        # print(idea)






    def get_all(self):
        # Lấy văn bản từ đầu (dòng 1, ký tự 0) đến cuối (tk.END)
        # "1.0" có nghĩa là: dòng 1, ký tự 0
        # tk.END là một hằng số đặc biệt chỉ vị trí cuối cùng
        # - "1c" để loại bỏ ký tự newline thừa mà .get() tự động thêm vào cuối
        content = self.idea_text.get("1.0", tk.END + "-1c")
        style = self.style_entry.get()
        duration = self.duration_entry.get()
        language = self.lang_combo.get()
        aspect = self.aspect_combo.get()

        return content, duration, language, aspect,style

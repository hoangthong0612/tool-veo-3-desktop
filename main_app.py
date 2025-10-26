import tkinter as tk
from tkinter import ttk
from result_app import ResultApp
from styles import ENTRY_BG_COLOR, FG_COLOR, BG_COLOR
from gemini_service import suggest_idea
import threading

class MainApp(ttk.Frame):
    def __init__(self, parent, create_story):
        super().__init__(parent, style="TFrame")

        # === Scrollable Canvas ===
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="TFrame", padding="40 40 40 40")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Cho phép cuộn bằng con lăn chuột
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # === BẮT ĐẦU CÁC PHẦN GIAO DIỆN TRONG scrollable_frame ===

        # --- Tiêu đề ---
        title_label = ttk.Label(self.scrollable_frame, text="Story to Video AI Generator", style="Title.TLabel")
        title_label.pack(pady=(10, 5), fill="x")

        subtitle_label = ttk.Label(
            self.scrollable_frame,
            text="Bring your stories to life with AI-powered video creation.",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(pady=(0, 30), fill="x")

        # --- Tab ---
        tab_frame = ttk.Frame(self.scrollable_frame)
        tab_frame.pack(pady=10)

        self.idea_tab_btn = ttk.Button(tab_frame, text="From Idea", style="ActiveTab.TButton", width=25,
                                       command=self.show_idea_tab)
        self.idea_tab_btn.pack(side="left", padx=5, ipady=5)

        self.script_tab_btn = ttk.Button(tab_frame, text="From Script", style="InactiveTab.TButton", width=25,
                                         command=self.show_script_tab)
        self.script_tab_btn.pack(side="left", padx=5, ipady=5)

        # --- Khung "Your Idea" ---
        idea_frame = ttk.Frame(self.scrollable_frame)
        idea_frame.pack(fill="x", pady=15)

        self.idea_label = ttk.Label(idea_frame, text="Your Idea")
        self.idea_label.pack(anchor="w", pady=(0, 5))

        # Scrollable Text
        text_container = tk.Frame(idea_frame, bg=ENTRY_BG_COLOR, borderwidth=1, relief="solid")
        text_container.pack(fill="x", expand=True)

        scrollbar_text = tk.Scrollbar(text_container)
        scrollbar_text.pack(side="right", fill="y")

        self.idea_text = tk.Text(
            text_container,
            height=8,
            bg=ENTRY_BG_COLOR,
            fg=FG_COLOR,
            font=("Arial", 10),
            borderwidth=0,
            highlightthickness=0,
            insertbackground=FG_COLOR,
            yscrollcommand=scrollbar_text.set
        )
        self.idea_text.insert("1.0", "A cat astronaut exploring a planet made of cheese....")
        self.idea_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar_text.config(command=self.idea_text.yview)

        self.suggest_btn_1 = ttk.Button(text_container, text="Suggest", style="Suggest.TButton")
        self.suggest_btn_1.place(relx=0.98, rely=0.95, anchor="se")

        # --- Cài đặt ---
        settings_frame = ttk.Frame(self.scrollable_frame)
        settings_frame.pack(fill="x", pady=15)
        for i in range(4):
            settings_frame.columnconfigure(i, weight=1)

        # Style
        style_frame = ttk.Frame(settings_frame)
        style_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(style_frame, text="Style").pack(anchor="w", pady=(0, 5))
        style_entry_frame = ttk.Frame(style_frame, style="TEntry")
        style_entry_frame.pack(fill="x")
        self.style_entry = ttk.Entry(style_entry_frame)
        self.style_entry.insert(0, "Cinematic, hyper-realistic, 4K")
        self.style_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=8)
        ttk.Button(style_entry_frame, text="Suggest", style="Suggest.TButton").pack(side="right", padx=(5, 8), pady=8)

        # Duration
        duration_frame = ttk.Frame(settings_frame)
        duration_frame.grid(row=0, column=1, sticky="ew", padx=10)
        ttk.Label(duration_frame, text="Duration (seconds)").pack(anchor="w", pady=(0, 5))
        self.duration_entry = ttk.Entry(duration_frame)
        self.duration_entry.insert(0, "16")
        self.duration_entry.pack(fill="x", ipady=4)

        # Aspect Ratio
        aspect_frame = ttk.Frame(settings_frame)
        aspect_frame.grid(row=0, column=2, sticky="ew", padx=10)
        ttk.Label(aspect_frame, text="Aspect Ratio").pack(anchor="w", pady=(0, 5))
        self.aspect_combo = ttk.Combobox(aspect_frame, values=["16:9", "9:16"], state="readonly")
        self.aspect_combo.set("16:9")
        self.aspect_combo.pack(fill="x", ipady=4)

        # Language
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.grid(row=0, column=3, sticky="ew", padx=(10, 0))
        ttk.Label(lang_frame, text="Language").pack(anchor="w", pady=(0, 5))
        self.lang_combo = ttk.Combobox(lang_frame, values=["English", "Vietnamese", "Japanese", "Spanish"], state="readonly")
        self.lang_combo.set("English")
        self.lang_combo.pack(fill="x", ipady=4)

        # Folder Save Path
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(15, 0))
        ttk.Label(folder_frame, text="Save Folder").pack(anchor="w", pady=(0, 5))

        self.folder_path = tk.StringVar()
        folder_entry_frame = ttk.Frame(folder_frame)
        folder_entry_frame.pack(fill="x")

        self.folder_entry = ttk.Entry(folder_entry_frame, textvariable=self.folder_path)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=8)

        def browse_folder():
            from tkinter import filedialog
            path = filedialog.askdirectory(title="Chọn thư mục lưu ảnh/video")
            if path:
                self.folder_path.set(path)

        ttk.Button(folder_entry_frame, text="Chọn...", command=browse_folder, style="Suggest.TButton").pack(side="right", padx=(5, 8), pady=8)

        # --- Checkbox ---
        self.narrate_var = tk.BooleanVar()
        self.narrate_check = ttk.Checkbutton(self.scrollable_frame,
                                             text="Include AI-generated narration for each scene",
                                             variable=self.narrate_var)
        self.narrate_check.pack(anchor="w", pady=20)

        # --- Nút Create ---
        self.create_button = ttk.Button(self.scrollable_frame,
                                   text="Create Story & Characters",
                                   command=create_story,
                                   style="Create.TButton")
        self.create_button.pack(fill="x", ipady=10, pady=10)

        # Loading UI (ẩn ban đầu)
        self.loading_label = ttk.Label(self.scrollable_frame, text="Đang xử lý...")
        self.progressbar = ttk.Progressbar(self.scrollable_frame, mode='indeterminate')

    # --- Các hàm ---
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

    def create_story(self):
        content, duration, language, aspect, style, folder = self.get_all()
        result_app = ResultApp(self, content, duration, language, aspect)
        self.pack_forget()
        result_app.pack(expand=True, fill="both")

    def get_all(self):
        content = self.idea_text.get("1.0", tk.END + "-1c")
        style = self.style_entry.get()
        duration = self.duration_entry.get()
        language = self.lang_combo.get()
        aspect = self.aspect_combo.get()
        folder = self.folder_path.get()
        return content, duration, language, aspect, style, folder

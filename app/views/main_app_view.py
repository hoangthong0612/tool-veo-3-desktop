# app/views/main_app_view.py
import customtkinter
import tkinter as tk 
from tkinter import filedialog
from app.views.result_view import ResultApp # <-- SỬA IMPORT

class MainApp(customtkinter.CTkScrollableFrame):
    def __init__(self, parent, create_story):
        super().__init__(parent, fg_color="transparent", 
                         scrollbar_button_color=None, 
                         scrollbar_button_hover_color=None)
        
        # --- Tiêu đề ---
        title_label = customtkinter.CTkLabel(self, text="Story to Video AI Generator", 
                                             font=customtkinter.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(10, 5), fill="x")

        subtitle_label = customtkinter.CTkLabel(
            self,
            text="Bring your stories to life with AI-powered video creation.",
            font=customtkinter.CTkFont(size=12)
        )
        subtitle_label.pack(pady=(0, 30), fill="x")

        # --- Tab (Sử dụng SegmentedButton) ---
        self.tab_var = tk.StringVar(value="From Idea")
        self.tab_control = customtkinter.CTkSegmentedButton(
            self,
            values=["From Idea", "From Script"],
            command=self.switch_tab,
            variable=self.tab_var,
            font=customtkinter.CTkFont(size=11, weight="bold")
        )
        self.tab_control.pack(pady=10)

        # --- Khung "Your Idea" / "Script" ---
        self.idea_label = customtkinter.CTkLabel(self, text="Your Idea")
        self.idea_label.pack(anchor="w", pady=(15, 5))

        self.idea_text = customtkinter.CTkTextbox(
            self,
            height=200, 
            font=("Arial", 12),
            wrap="word"
        )
        self.idea_text.insert("1.0", "A cat astronaut exploring a planet made of cheese....")
        self.idea_text.pack(fill="x", expand=True)

        # --- Cài đặt ---
        settings_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="x", pady=15)
        settings_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # Style
        style_frame = customtkinter.CTkFrame(settings_frame, fg_color="transparent")
        style_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        customtkinter.CTkLabel(style_frame, text="Style").pack(anchor="w", pady=(0, 5))
        self.style_entry = customtkinter.CTkEntry(style_frame)
        self.style_entry.insert(0, "Cinematic, hyper-realistic, 4K")
        self.style_entry.pack(fill="x")

        # Duration
        duration_frame = customtkinter.CTkFrame(settings_frame, fg_color="transparent")
        duration_frame.grid(row=0, column=1, sticky="ew", padx=10)
        customtkinter.CTkLabel(duration_frame, text="Duration (seconds)").pack(anchor="w", pady=(0, 5))
        self.duration_entry = customtkinter.CTkEntry(duration_frame)
        self.duration_entry.insert(0, "16")
        self.duration_entry.pack(fill="x")

        # Aspect Ratio
        aspect_frame = customtkinter.CTkFrame(settings_frame, fg_color="transparent")
        aspect_frame.grid(row=0, column=2, sticky="ew", padx=10)
        customtkinter.CTkLabel(aspect_frame, text="Aspect Ratio").pack(anchor="w", pady=(0, 5))
        self.aspect_combo = customtkinter.CTkComboBox(aspect_frame, values=["16:9", "9:16"], state="readonly")
        self.aspect_combo.set("16:9")
        self.aspect_combo.pack(fill="x")

        # Language
        lang_frame = customtkinter.CTkFrame(settings_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=3, sticky="ew", padx=(10, 0))
        customtkinter.CTkLabel(lang_frame, text="Language").pack(anchor="w", pady=(0, 5))
        self.lang_combo = customtkinter.CTkComboBox(lang_frame, values=["English", "Vietnamese", "Japanese", "Spanish"], state="readonly")
        self.lang_combo.set("English")
        self.lang_combo.pack(fill="x")

        # Folder Save Path
        folder_frame = customtkinter.CTkFrame(settings_frame, fg_color="transparent")
        folder_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(15, 0))
        customtkinter.CTkLabel(folder_frame, text="Save Folder").pack(anchor="w", pady=(0, 5))
        
        self.folder_path = tk.StringVar()
        
        folder_entry_frame = customtkinter.CTkFrame(folder_frame, fg_color="transparent")
        folder_entry_frame.pack(fill="x")
        
        self.folder_entry = customtkinter.CTkEntry(folder_entry_frame, textvariable=self.folder_path)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_button = customtkinter.CTkButton(folder_entry_frame, text="Chọn...", 
                                                     command=self.browse_folder, width=80)
        self.browse_button.pack(side="right")

        # --- Checkbox ---
        self.narrate_var = customtkinter.BooleanVar()
        self.narrate_check = customtkinter.CTkCheckBox(self,
                                             text="Include AI-generated narration for each scene",
                                             variable=self.narrate_var)
        self.narrate_check.pack(anchor="w", pady=20)

        # --- Nút Create ---
        self.create_button = customtkinter.CTkButton(self,
                                   text="Create Story & Characters",
                                   command=create_story,
                                   font=customtkinter.CTkFont(size=14, weight="bold"))
        self.create_button.pack(fill="x", ipady=10, pady=10)

        # Loading UI (ẩn ban đầu)
        self.loading_label = customtkinter.CTkLabel(self, text="Đang xử lý...")
        self.progressbar = customtkinter.CTkProgressBar(self, mode='indeterminate')

    def switch_tab(self, value):
        if value == "From Idea":
            self.idea_label.configure(text="Your Idea")
            self.idea_text.delete("1.0", tk.END)
            self.idea_text.insert("1.0", "A cat astronaut exploring a planet made of cheese....")
        else: 
            self.idea_label.configure(text="Nhập Script")
            self.idea_text.delete("1.0", tk.END)
            self.idea_text.insert("1.0", "Dán kịch bản (script) của bạn vào đây...")

    def browse_folder(self):
        path = filedialog.askdirectory(title="Chọn thư mục lưu ảnh/video")
        if path:
            self.folder_path.set(path)

    def get_all(self):
        content = self.idea_text.get("1.0", tk.END + "-1c")
        style = self.style_entry.get()
        duration = self.duration_entry.get()
        language = self.lang_combo.get()
        aspect = self.aspect_combo.get()
        folder = self.folder_path.get()
        return content, duration, language, aspect, style, folder
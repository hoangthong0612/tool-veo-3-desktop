import json
import tkinter as tk
from tkinter import ttk

from PIL.ImageChops import screen

from styles import ENTRY_BG_COLOR, FG_COLOR, BG_COLOR
import threading
from gemini_service import suggest_idea, generate_script_and_characters, generate_scene_prompts


class ResultApp(ttk.Frame):
    def __init__(self, parent, content, duration, language, aspect, style):
        super().__init__(parent, style="TFrame", padding="40 40 40 40")

        self.content = content
        self.duration = duration
        self.language = language
        self.aspect = aspect
        self.style = style

        title_label = ttk.Label(self, text="Story to Video AI Generator", style="Title.TLabel")
        title_label.pack(pady=(10, 5), fill="x")

        subtitle_label = ttk.Label(self, text="Bring your stories to life with AI-powered video creation.",
                                   style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 30), fill="x")

        self.loading_label = ttk.Label(self, text="Đang tải dữ liệu API...")
        self.progressbar = ttk.Progressbar(self, mode='indeterminate')
        self.result_scripts = None
        self.idea_text = tk.Text()
        self.script = tk.Text()

        # self.result_label = ttk.Label(self, text=content, font=("Arial", 12))
        # self.result_label.pack(pady=10)
        self.start_api_call()

    def start_api_call(self):
        """Hàm này được gọi khi nhấn button"""

        # 1. Vô hiệu hóa button và hiển thị loading
        self.loading_label.pack(pady=5)
        self.progressbar.pack(pady=10, fill="x", padx=50)
        self.progressbar.start(10)  # Bắt đầu chạy animation

        # 2. Khởi chạy luồng mới để gọi API
        # daemon=True để luồng tự tắt khi chương trình chính tắt
        threading.Thread(target=self.run_api_in_thread, daemon=True).start()

    def show_idea(self):
        idea = suggest_idea(self.content)
        idea_frame = ttk.Frame(self)
        idea_frame.pack(fill="x", pady=15)

        idea_label = ttk.Label(idea_frame, text="Your Idea")
        idea_label.pack(anchor="w", pady=(0, 5))
        # self.result_label = ttk.Label(self, text=idea, font=("Arial", 12))
        # self.result_label.pack(pady=10)
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
        self.idea_text.insert("1.0", idea)
        self.idea_text.pack(fill="both", expand=True, padx=10, pady=10)

    def show_script_and_characters(self):
        self.result_scripts = generate_script_and_characters(idea=self.idea_text.get("1.0", tk.END + "-1c"),
                                                             duration=self.duration,
                                                             style=self.style, mode='idea', language=self.language)
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=15)

        label = ttk.Label(frame, text="Kịch bản")
        label.pack(anchor="w", pady=(0, 5))
        # self.result_label = ttk.Label(self, text=idea, font=("Arial", 12))
        # self.result_label.pack(pady=10)
        text_container = tk.Frame(frame,
                                  bg=ENTRY_BG_COLOR,  # Màu từ styles.py
                                  borderwidth=1,
                                  relief="solid",
                                  highlightbackground=ENTRY_BG_COLOR,  # Màu từ styles.py
                                  highlightthickness=1)
        text_container.pack(fill="x", expand=True)

        # Dùng tk.Text nên cần set màu thủ công
        self.script = tk.Text(text_container,
                              height=8,
                              bg=ENTRY_BG_COLOR,  # Màu từ styles.py
                              fg=FG_COLOR,  # Màu từ styles.py
                              font=("Arial", 10),
                              borderwidth=0,
                              highlightthickness=0,
                              insertbackground=FG_COLOR)  # Màu từ styles.py
        self.script.insert("1.0", self.result_scripts['script'])
        self.script.pack(fill="both", expand=True, padx=10, pady=10)
        print(self.result_scripts)
        screens = generate_scene_prompts(language=self.language, duration=self.duration,
                               characters=self.result_scripts['characters'], style=self.style,include_narration=False)
        print("screen")
        print(screens)
    def run_api_in_thread(self):
        # try:
            self.show_idea()
            self.show_script_and_characters()

            # 3. Gửi kết quả về luồng chính để cập nhật GUI
            # Dùng root.after(0, ...) để yêu cầu luồng chính chạy hàm
            # self.controller.after(0, self.on_api_success, api_data)

        # except Exception as e:
        #     # Xử lý nếu API bị lỗi
        #     print(f"THREAD: Lỗi API: {e}")
            # self.controller.after(0, self.on_api_error, str(e))

import tkinter as tk
from tkinter import ttk
from styles import ENTRY_BG_COLOR, FG_COLOR, BG_COLOR

class ResultApp(ttk.Frame):
    def __init__(self, parent,content, duration, language, aspect):
        super().__init__(parent, style="TFrame", padding="40 40 40 40")
        print(content)
        title_label = ttk.Label(self, text="Story to Video AI Generator", style="Title.TLabel")
        title_label.pack(pady=(10, 5), fill="x")

        subtitle_label = ttk.Label(self, text="Bring your stories to life with AI-powered video creation.",
                                   style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 30), fill="x")

        self.result_label = ttk.Label(self, text=content, font=("Arial", 12))
        self.result_label.pack(pady=10)
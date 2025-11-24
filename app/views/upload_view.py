# app/views/upload_view.py
import customtkinter
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os
import time
import requests
import concurrent.futures
from app.services.api_service import create_project, generateVideoForScene, check_video_generation_status


class UploadView(customtkinter.CTkFrame):
    def __init__(self, parent, back_command):
        super().__init__(parent, fg_color="transparent")

        self.back_command = back_command
        self.df = None
        self.processing = False
        self.rows = []

        # --- UI Layout ---
        title_label = customtkinter.CTkLabel(self, text="Batch Video Generation (Excel)",
                                             font=customtkinter.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 10))

        file_frame = customtkinter.CTkFrame(self)
        file_frame.pack(fill="x", padx=20, pady=10)

        self.file_path_label = customtkinter.CTkLabel(file_frame, text="Chưa chọn file nào...")
        self.file_path_label.pack(side="left", padx=20)

        select_btn = customtkinter.CTkButton(file_frame, text="Chọn File Excel", command=self.select_file)
        select_btn.pack(side="right", padx=20, pady=10)

        # --- KHU VỰC CÀI ĐẶT (CẬP NHẬT) ---
        settings_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20)

        # Tỷ lệ khung hình
        customtkinter.CTkLabel(settings_frame, text="Tỷ lệ:").pack(side="left", padx=(0, 5))
        self.aspect_combo = customtkinter.CTkComboBox(settings_frame, values=["16:9", "9:16"], width=80)
        self.aspect_combo.set("16:9")
        self.aspect_combo.pack(side="left", padx=(0, 20))

        # Chọn Số Luồng (MỚI)
        customtkinter.CTkLabel(settings_frame, text="Số luồng:").pack(side="left", padx=(0, 5))
        self.thread_combo = customtkinter.CTkComboBox(settings_frame, values=["1", "3", "5", "8", "10"], width=70)
        self.thread_combo.set("5")  # Mặc định là 5
        self.thread_combo.pack(side="left")

        # Nút Bắt đầu
        self.start_btn = customtkinter.CTkButton(settings_frame, text="Bắt đầu Xử lý",
                                                 command=self.start_batch_processing,
                                                 state="disabled", fg_color="#2CC985")
        self.start_btn.pack(side="right")

        # Bảng hiển thị
        self.table_header = customtkinter.CTkFrame(self, height=30)
        self.table_header.pack(fill="x", padx=20, pady=(20, 0))

        headers = ["STT", "Prompt", "Trạng thái", "File Video"]
        widths = [50, 400, 150, 100]
        for i, h in enumerate(headers):
            customtkinter.CTkLabel(self.table_header, text=h, width=widths[i], anchor="w",
                                   font=("Arial", 12, "bold")).pack(side="left", padx=5)

        self.scroll_frame = customtkinter.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if file_path:
            self.file_path_label.configure(text=os.path.basename(file_path))
            try:
                self.df = pd.read_excel(file_path)
                if "Prompt" not in self.df.columns and "prompt" not in self.df.columns:
                    self.df.rename(columns={self.df.columns[0]: "Prompt"}, inplace=True)
                if "prompt" in self.df.columns:
                    self.df.rename(columns={"prompt": "Prompt"}, inplace=True)
                self.load_table_data()
                self.start_btn.configure(state="normal")
            except Exception as e:
                messagebox.showerror("Lỗi đọc file", str(e))

    def load_table_data(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.rows = []
        for index, row in self.df.iterrows():
            row_frame = customtkinter.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            customtkinter.CTkLabel(row_frame, text=str(index + 1), width=50, anchor="w").pack(side="left", padx=5)

            prompt_text = str(row.get("Prompt", ""))
            short_prompt = (prompt_text[:60] + '..') if len(prompt_text) > 60 else prompt_text
            customtkinter.CTkLabel(row_frame, text=short_prompt, width=400, anchor="w").pack(side="left", padx=5)

            status_lbl = customtkinter.CTkLabel(row_frame, text="Sẵn sàng", width=150, anchor="w", text_color="gray")
            status_lbl.pack(side="left", padx=5)

            action_btn = customtkinter.CTkButton(row_frame, text="Mở", width=80, height=24, state="disabled")
            action_btn.pack(side="left", padx=5)

            self.rows.append({
                "prompt": prompt_text,
                "status_lbl": status_lbl,
                "action_btn": action_btn,
                "index": index
            })

    def update_row_status(self, index, text, color="white", enable_open=None):
        row = self.rows[index]
        self.after(0, lambda: row["status_lbl"].configure(text=text, text_color=color))
        if enable_open:
            self.after(0,
                       lambda: row["action_btn"].configure(state="normal", command=lambda: os.startfile(enable_open)))

    def start_batch_processing(self):
        if self.df is None: return
        self.processing = True

        # Lấy số luồng từ ComboBox
        try:
            num_threads = int(self.thread_combo.get())
        except ValueError:
            num_threads = 5  # Fallback nếu lỗi

        self.start_btn.configure(state="disabled", text=f"Đang chạy ({num_threads} luồng)...")

        save_folder = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if not save_folder:
            self.processing = False
            self.start_btn.configure(state="normal", text="Bắt đầu Xử lý")
            return

        threading.Thread(target=self.run_process_thread, args=(save_folder, num_threads), daemon=True).start()

    def process_single_row(self, index, row_data, project_id, aspect_ratio, save_folder):
        """Hàm xử lý MỘT dòng (Có cơ chế Retry 3 lần)"""
        prompt = row_data["prompt"]
        if not prompt: return

        MAX_RETRIES = 3

        for attempt in range(MAX_RETRIES):
            try:
                # Cập nhật trạng thái (nếu là retry thì hiện rõ lần thử)
                if attempt == 0:
                    self.update_row_status(index, "⏳ Đang gửi request...", "#FFD700")
                else:
                    self.update_row_status(index, f"⚠️ Thử lại ({attempt + 1}/{MAX_RETRIES})...", "#FFA500")

                # 1. Gọi API Text-to-Video
                scene_dummy = {"videoPrompt": prompt}
                video_data = generateVideoForScene(scene_dummy, None, aspect_ratio, project_id)

                if not video_data or "operations" not in video_data:
                    # Nếu lỗi API, ném lỗi để vào except và retry
                    raise Exception("Lỗi API Generate")

                operation_name = video_data["operations"][0]["operation"]["name"]
                scene_id = video_data["operations"][0]["sceneId"]

                self.update_row_status(index, "⏳ Đang tạo video...", "#87CEEB")

                # 2. Poll status
                video_url = None
                poll_success = False

                # Vòng lặp poll (mỗi lần generate sẽ poll tối đa 60 lần ~ 5 phút)
                for _ in range(60):
                    if not self.processing: return
                    time.sleep(5)
                    check = check_video_generation_status(operation_name, scene_id)
                    if not check: continue

                    op = check['operations'][0]['operation']
                    if 'metadata' in op and 'video' in op['metadata'] and 'fifeUrl' in op['metadata']['video']:
                        video_url = op['metadata']['video']['fifeUrl']
                        poll_success = True
                        break

                if not poll_success:
                    raise Exception("Timeout Polling")

                # 3. Tải Video
                if video_url:
                    self.update_row_status(index, "⬇️ Đang tải...", "#87CEEB")
                    file_name = f"video_{index + 1}_{int(time.time())}.mp4"
                    file_path = os.path.join(save_folder, file_name)

                    with requests.get(video_url, stream=True) as r:
                        r.raise_for_status()
                        with open(file_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)

                    # Nếu chạy đến đây là THÀNH CÔNG -> Thoát vòng lặp retry
                    self.update_row_status(index, "✅ Hoàn tất", "#50FA7B", enable_open=file_path)
                    return

            except Exception as e:
                # Nếu có lỗi, in ra console và tiếp tục vòng lặp retry
                print(f"Lỗi dòng {index + 1} (Lần {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(3)  # Nghỉ 3s trước khi thử lại
                else:
                    # Nếu đã hết lượt thử mà vẫn lỗi
                    self.update_row_status(index, "❌ Thất bại", "#FF5555")

    def run_process_thread(self, save_folder, num_threads):
        try:
            self.after(0, lambda: messagebox.showinfo("Thông báo", "Đang tạo Project mới..."))
            project_res = create_project()
            if not project_res:
                raise Exception("Không tạo được Project")

            project_id = project_res["projectId"]
            aspect_ratio = self.aspect_combo.get()

            # Sử dụng số luồng người dùng chọn
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for i, row_data in enumerate(self.rows):
                    futures.append(
                        executor.submit(self.process_single_row, i, row_data, project_id, aspect_ratio, save_folder)
                    )
                concurrent.futures.wait(futures)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi", str(e)))
        finally:
            self.processing = False
            self.after(0, lambda: self.start_btn.configure(state="normal", text="Bắt đầu Xử lý"))
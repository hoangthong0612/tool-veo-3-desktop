import tkinter as tk
from tkinter import ttk
import base64
import time
import requests
import os
import threading
import subprocess
import platform
from PIL import Image, ImageTk
import concurrent.futures  # Thêm import này

# Giả sử các import này là chính xác
from styles import ENTRY_BG_COLOR, FG_COLOR, BG_COLOR
from gemini_service import suggest_idea, generate_script_and_characters, generate_scene_prompts
from api_service import (
    create_or_update_workflow,
    generate_image_subject_text,
    run_image_recipe,
    create_project,
    generateVideoForScene,
    check_video_generation_status
)


class ResultApp(ttk.Frame):
    def __init__(self, parent, content, duration, language, aspect, style, folder):
        super().__init__(parent, style="TFrame", padding="40 40 40 40")

        self.content = content
        self.duration = duration
        self.language = language
        self.aspect = aspect
        self.style = style
        self.folder = folder

        title_label = ttk.Label(self, text="Story to Video AI Generator", style="Title.TLabel")
        title_label.pack(pady=(10, 5), fill="x")

        subtitle_label = ttk.Label(
            self,
            text="Bring your stories to life with AI-powered video creation.",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(pady=(0, 30), fill="x")

        self.loading_label = ttk.Label(self, text="Đang tải dữ liệu API...")
        self.loading_label.pack(pady=5)
        self.progressbar = ttk.Progressbar(self, mode='indeterminate')
        self.progressbar.pack(pady=10, fill="x", padx=50)
        self.progressbar.start(10)

        # internal state
        self.workflow_id = None
        self.project_id = None
        self.characters = []
        self.screens = []
        self.table_rows = []
        self.thumbnail_images = []

        # Thread chạy API
        threading.Thread(target=self.run_api_in_thread, daemon=True).start()

    # ===============================
    # TẠO BẢNG SCENE RỖNG
    # ===============================
    def init_scene_table(self, scenes):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, pady=20)

        ttk.Label(frame, text="Danh sách Scene", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(frame, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers = ["STT", "Hình ảnh", "Prompt Hình Ảnh", "Prompt Video", "Trạng thái"]
        for i, h in enumerate(headers):
            ttk.Label(scrollable_frame, text=h, width=20, anchor="center", style="Subtitle.TLabel").grid(row=0,
                                                                                                         column=i,
                                                                                                         padx=5, pady=2)

        # Rows
        for idx, scene in enumerate(scenes):
            row = {}
            ttk.Label(scrollable_frame, text=str(idx + 1), width=6, anchor="center").grid(row=idx + 1, column=0, padx=5)
            row["image_label"] = ttk.Label(scrollable_frame, text="[Đang tải ảnh...]", width=20)
            row["image_label"].grid(row=idx + 1, column=1, padx=5)

            img_txt = tk.Text(scrollable_frame, width=40, height=4, wrap="word")
            img_txt.insert("1.0", scene.get("imagePrompt", ""))
            img_txt.config(state="disabled", bg="#f9f9f9")
            img_txt.grid(row=idx + 1, column=2, padx=5)

            vid_txt = tk.Text(scrollable_frame, width=40, height=4, wrap="word")
            vid_txt.insert("1.0", scene.get("videoPrompt", ""))
            vid_txt.config(state="disabled", bg="#f9f9f9")
            vid_txt.grid(row=idx + 1, column=3, padx=5)

            row["status_label"] = ttk.Label(scrollable_frame, text="⏳ Chờ xử lý...", width=25)
            row["status_label"].grid(row=idx + 1, column=4, padx=5)

            row["video_path"] = None

            self.table_rows.append(row)

    # ===============================
    # CẬP NHẬT ẢNH VÀ TRẠNG THÁI
    # ===============================
    def update_scene_image(self, index, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((140, 80))
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_images.append(photo)  # Giữ tham chiếu
            lbl = self.table_rows[index]["image_label"]
            lbl.config(image=photo, text="")
            lbl.image = photo

            # Chỉ cập nhật trạng thái nếu nó chưa ở trạng thái "tạo video"
            current_status = self.table_rows[index]["status_label"].cget("text")
            if current_status == "⏳ Đang tạo ảnh...":
                self.table_rows[index]["status_label"].config(text="🖼️ Ảnh đã tải xong")
        except Exception as e:
            print(f"update_scene_image error (index {index}): {e}")

    def update_scene_status(self, index, status_text):
        try:
            lbl = self.table_rows[index]["status_label"]
            lbl.config(text=status_text)
        except Exception as e:
            print(f"update_scene_status error (index {index}): {e}")

    # ===============================
    # MỞ VIDEO
    # ===============================
    def open_video(self, file_path):
        try:
            if platform.system() == "Darwin":
                subprocess.call(["open", file_path])
            elif platform.system() == "Windows":
                os.startfile(file_path)
            else:
                subprocess.call(["xdg-open", file_path])
        except Exception as e:
            print(f"Lỗi mở video: {e}")

    # ===============================
    # GÁN SỰ KIỆN CLICK CHO ẢNH
    # ===============================
    def make_thumbnail_clickable(self, index, video_path):
        """Gán sự kiện click để mở video cho thumbnail."""
        try:
            self.table_rows[index]["video_path"] = video_path
            lbl = self.table_rows[index]["image_label"]
            lbl.bind("<Button-1>", lambda event, path=video_path: self.open_video(path))
            lbl.config(cursor="hand2")
        except Exception as e:
            print(f"Lỗi khi gán click cho thumbnail {index}: {e}")

    # ===============================
    # (MỚI) HÀM XỬ LÝ TỪNG SCENE (CHO THREAD)
    # ===============================
    def process_scene(self, index, scene, image_folder, video_folder):
        """
        Hàm này được gọi trong một thread riêng biệt để xử lý 1 scene
        (tạo ảnh -> tạo video -> poll video -> tải video)
        Tất cả các lệnh cập nhật UI phải dùng self.after()
        """
        try:
            self._log_state(f"Scene {index + 1}/{len(self.screens)}: Bắt đầu xử lý...")

            # --- 1. Sinh ảnh scene ---
            self.after(0, lambda idx=index: self.update_scene_status(idx, "⏳ Đang tạo ảnh..."))
            image_data = run_image_recipe(
                workflow_id=self.workflow_id,
                aspect_ratio=self.aspect,
                style=self.style,
                characters=self.characters,
                scene=scene
            )

            image_path = None
            try:
                img_bytes = base64.b64decode(image_data.get("image", ""))
                image_path = os.path.join(image_folder, f"{index + 1}.png")
                with open(image_path, "wb") as f:
                    f.write(img_bytes)

                # Cập nhật ảnh (gửi về main thread)
                self.after(0, lambda idx=index, path=image_path: self.update_scene_image(idx, path))
            except Exception as e:
                self._log_state(f"Lỗi lưu ảnh scene {index + 1}: {e}")
                self.after(0, lambda idx=index: self.update_scene_status(idx, "⚠️ Lỗi tạo ảnh"))
                return  # Thoát khỏi hàm này cho scene này

            # --- 2. Tạo video scene ---
            self.after(0, lambda idx=index: self.update_scene_status(idx, "⏳ Đang tạo video..."))
            video_data = generateVideoForScene(
                scene=scene,
                aspect_ratio=self.aspect,
                project_id=self.project_id,
                image_data=image_data
            )

            operation_name = video_data["operations"][0]["operation"]["name"]
            scene_id = video_data["operations"][0]["sceneId"]

            # --- 3. Poll status & Tải video ---
            for attempt in range(60):
                time.sleep(5)
                try:
                    check_data = check_video_generation_status(name=operation_name, screen_id=scene_id)
                    op = check_data['operations'][0]['operation']
                    if 'metadata' in op and 'video' in op['metadata'] and 'fifeUrl' in op['metadata']['video']:
                        video_url = op['metadata']['video']['fifeUrl']
                        response_video = requests.get(video_url, stream=True, timeout=60)
                        if response_video.status_code == 200:
                            file_path = os.path.join(video_folder, f"{index + 1}.mp4")
                            with open(file_path, "wb") as f:
                                for chunk in response_video.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)

                            self._log_state(f"✅ Saved video scene {index + 1}: {file_path}")

                            self.after(0, lambda idx=index: self.update_scene_status(idx, "✅ Video đã tải xong"))
                            self.after(0, lambda idx=index, path=file_path: self.make_thumbnail_clickable(idx, path))

                            return  # Hoàn thành scene này, thread kết thúc
                except Exception:
                    pass

            self._log_state(f"⚠️ Timeout video scene {index + 1}")
            self.after(0, lambda idx=index: self.update_scene_status(idx, "⚠️ Lỗi tải video (timeout)"))

        except Exception as e:
            self._log_state(f"Lỗi nghiêm trọng scene {index + 1}: {e}")
            self.after(0, lambda idx=index, msg=str(e): self.update_scene_status(idx, f"⚠️ Lỗi: {msg[:30]}..."))
            raise e

    # ===============================
    # LUỒNG CHÍNH CHẠY API
    # ===============================
    def run_api_in_thread(self):
        try:
            self._log_state("Tạo workflow...")
            self.workflow_id = create_or_update_workflow()
            self._log_state(f"Workflow: {self.workflow_id}")

            self._log_state("Tạo project...")
            project_res = create_project()
            self.project_id = project_res.get("projectId")
            self._log_state(f"Project: {self.project_id}")

            self._log_state("Gợi ý ý tưởng...")
            # idea = suggest_idea(self.content)

            self._log_state("Tạo kịch bản & nhân vật...")
            result_scripts = generate_script_and_characters(
                idea=self.content,
                duration=self.duration,
                style=self.style,
                mode='idea',
                language=self.language
            )

            print("Kịch bản")
            print(result_scripts)

            character_folder = os.path.join(self.folder, "characters")
            image_folder = os.path.join(self.folder, "images")
            video_folder = os.path.join(self.folder, "video")
            os.makedirs(character_folder, exist_ok=True)
            os.makedirs(image_folder, exist_ok=True)
            os.makedirs(video_folder, exist_ok=True)

            # Sinh nhân vật
            self.characters = []
            for idx, ch in enumerate(result_scripts.get("characters", [])):
                desc = ch.get("description", "")
                name = ch.get("name", f"char_{idx + 1}")
                self._log_state(f"Tạo ảnh nhân vật: {name}...")
                image_data = generate_image_subject_text(
                    description=desc,
                    workflow_id=self.workflow_id,
                    aspect_ratio=self.aspect,
                    style=self.style
                )
                try:
                    image_bytes = base64.b64decode(image_data.get("image", ""))
                    image_path = os.path.join(character_folder, f"{name}.png")
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                except Exception as e:
                    self._log_state(f"Lỗi lưu ảnh nhân vật {name}: {e}")

                self.characters.append({
                    "id": image_data.get("id"),
                    "promptImage": image_data.get("promptImage"),
                    "refImageBase64": image_data.get("image"),
                    "refImageUrl": f"data:image/png;base64,{image_data.get('image', '')}",
                    "name": name,
                    "image_path": image_path
                })

            self._log_state("Tạo scene prompts...")
            self.screens = generate_scene_prompts(
                language=self.language,
                duration=self.duration,
                characters=result_scripts.get("characters", []),
                style=self.style,
                script=result_scripts.get('script',""),
                include_narration=False

            )

            # Hiển thị bảng ngay khi có scene
            self.after(0, lambda: self.init_scene_table(self.screens))

            # === (THAY ĐỔI) TẠO TASK BẤT ĐỒNG BỘ ===

            NUM_WORKERS = 8
            self._log_state(f"Bắt đầu tạo video cho {len(self.screens)} scene (chạy {NUM_WORKERS} luồng song song)...")

            # Sử dụng ThreadPoolExecutor để chạy các tác vụ song song
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:

                futures = []
                for index, scene in enumerate(self.screens):
                    # Gửi từng task (process_scene) vào executor
                    future = executor.submit(
                        self.process_scene,  # Hàm để chạy
                        index,  # Argument
                        scene,  # Argument
                        image_folder,  # Argument
                        video_folder  # Argument
                    )
                    futures.append(future)

                # Chờ tất cả các luồng hoàn thành
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()  # Lấy kết quả (hoặc exception) từ thread
                    except Exception as e:
                        self._log_state(f"Một luồng xử lý scene gặp lỗi: {e}")
                        print(f"THREAD POOL EXCEPTION: {e}")

            # Dòng này chỉ chạy KHI TẤT CẢ các scene đã được xử lý
            self.after(0, lambda: self.loading_label.config(text="✅ Hoàn tất tất cả scene!"))

        except Exception as e:
            self._log_state(f"THREAD ERROR: {e}")
            self.after(0, lambda: self.loading_label.config(text=f"Lỗi: {e}"))

    # ===============================
    # LOG TRẠNG THÁI
    # ===============================
    def _log_state(self, message: str):
        print(message)
        try:
            # Đảm bảo self.loading_label đã được tạo
            if hasattr(self, 'loading_label'):
                self.after(0, lambda: self.loading_label.config(text=message))
        except Exception as e:
            # Lỗi có thể xảy ra nếu cửa sổ đã bị đóng
            print(f"Lỗi _log_state (bỏ qua): {e}")
            pass
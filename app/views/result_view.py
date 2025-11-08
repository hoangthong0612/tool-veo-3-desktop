# app/views/result_view.py
import customtkinter
import tkinter as tk 
import base64
import time # <-- Cần cho việc delay
import requests # <-- Cần cho exception
import os
import threading
import subprocess
import platform
from PIL import Image, ImageTk
import concurrent.futures

# --- CÁC IMPORT (Giữ nguyên) ---
from app.utils.models import GenerationMode
from app.services.gemini_service import generate_full_video_plan
from app.services.api_service import (
    create_or_update_workflow,
    generate_image_subject_text,
    run_image_recipe,
    create_project,
    generateVideoForScene,
    check_video_generation_status
)


class ResultApp(customtkinter.CTkFrame):
    def __init__(self, parent, content, duration, language, aspect, style, folder, back_command):
        # (Hàm __init__ giữ nguyên)
        super().__init__(parent, fg_color="transparent")

        self.content = content
        self.duration = duration
        self.language = language
        self.aspect = aspect
        self.style = style
        self.folder = folder

        self.back_button = customtkinter.CTkButton(self, text="< Tạo dự án mới",
                                                   command=back_command,
                                                   fg_color="transparent",
                                                   anchor="w")
        self.back_button.pack(anchor="w", side="top")

        title_label = customtkinter.CTkLabel(self, text="Story to Video AI Generator", 
                                             font=customtkinter.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(0, 5), fill="x")

        subtitle_label = customtkinter.CTkLabel(
            self,
            text="Bring your stories to life with AI-powered video creation.",
            font=customtkinter.CTkFont(size=12)
        )
        subtitle_label.pack(pady=(0, 30), fill="x")

        self.loading_label = customtkinter.CTkLabel(self, text="Đang tải dữ liệu API...")
        self.loading_label.pack(pady=5)
        self.progressbar = customtkinter.CTkProgressBar(self, mode='indeterminate')
        self.progressbar.pack(pady=10, fill="x", padx=50)
        self.progressbar.start()

        # internal state
        self.workflow_id = None
        self.project_id = None
        self.characters = []
        self.screens = []
        self.table_rows = []
        self.thumbnail_images = []

        self.after(100, self.start_api_thread)

    def start_api_thread(self):
        # (Giữ nguyên)
        threading.Thread(target=self.run_api_in_thread, daemon=True).start()

    # --- HÀM HỖ TRỢ MỚI (BẮT ĐẦU) ---

    def _retry_operation(self, target_function, max_attempts=3, delay=5, operation_name=""):
        """
        Hàm hỗ trợ đa năng để thử lại một tác vụ nếu nó thất bại.
        'target_function' phải là một hàm (hoặc lambda) trả về giá trị "Truth-y" (như
        data, True) khi thành công và "Falsy" (như None, False) khi thất bại.
        """
        for attempt in range(max_attempts):
            try:
                # Chạy hàm (ví dụ: một lệnh gọi API)
                result = target_function()
                
                if result:
                    return result # Thành công, trả về kết quả
                
                # Thất bại (hàm trả về None/False)
                self._log_state(f"⚠️ {operation_name} thất bại (lần {attempt + 1}/{max_attempts}). Đang thử lại sau {delay}s...")
            
            except requests.exceptions.RequestException as e:
                # Lỗi mạng (timeout, connection error)
                self._log_state(f"⚠️ {operation_name} lỗi mạng (lần {attempt + 1}/{max_attempts}): {e}. Đang thử lại sau {delay}s...")
            except Exception as e:
                # Các lỗi khác (ví dụ: lỗi JSON, lỗi logic)
                self._log_state(f"⚠️ {operation_name} lỗi (lần {attempt + 1}/{max_attempts}): {e}. Đang thử lại sau {delay}s...")
            
            time.sleep(delay) # Chờ trước khi thử lại
            
        self._log_state(f"❌ {operation_name} thất bại vĩnh viễn sau {max_attempts} lần thử.")
        return None # Trả về None nếu tất cả các lần thử đều thất bại

    def _download_video_chunked(self, url, file_path):
        """
        Tải file video. Trả về True nếu thành công, None nếu thất bại.
        Được thiết kế để dùng bên trong _retry_operation.
        """
        try:
            response_video = requests.get(url, stream=True, timeout=60)
            if response_video.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response_video.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True # Tải thành công
            else:
                self._log_state(f"Lỗi tải video: Server trả về {response_video.status_code}")
                return None # Thất bại (để retry)
        except requests.exceptions.RequestException as e:
            self._log_state(f"Lỗi mạng khi tải video: {e}")
            return None # Thất bại (để retry)

    # --- HÀM HỖ TRỢ MỚI (KẾT THÚC) ---

    def init_scene_table(self, scenes):
        # (Giữ nguyên)
        frame = customtkinter.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, pady=20)
        customtkinter.CTkLabel(frame, text="Danh sách Scene", 
                               font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 10))
        scrollable_frame = customtkinter.CTkScrollableFrame(frame)
        scrollable_frame.pack(side="left", fill="both", expand=True)
        headers = ["STT", "Hình ảnh", "Prompt Hình Ảnh", "Prompt Video", "Trạng thái"]
        for i, h in enumerate(headers):
            customtkinter.CTkLabel(scrollable_frame, text=h, 
                                   font=customtkinter.CTkFont(size=12, weight="bold")).grid(row=0, column=i, padx=5, pady=2)
        for idx, scene in enumerate(scenes):
            row = {}
            customtkinter.CTkLabel(scrollable_frame, text=str(idx + 1), width=40).grid(row=idx + 1, column=0, padx=5)
            row["image_label"] = customtkinter.CTkLabel(scrollable_frame, text="[Đang tải ảnh...]", 
                                                        width=140, height=80)
            row["image_label"].grid(row=idx + 1, column=1, padx=5)
            img_txt = customtkinter.CTkTextbox(scrollable_frame, width=250, height=100, wrap="word", 
                                               font=("Arial", 11))
            img_txt.insert("1.0", scene.get("imagePrompt", ""))
            img_txt.configure(state="disabled") 
            img_txt.grid(row=idx + 1, column=2, padx=5)
            vid_txt = customtkinter.CTkTextbox(scrollable_frame, width=250, height=100, wrap="word",
                                               font=("Arial", 11))
            vid_txt.insert("1.0", scene.get("videoPrompt", ""))
            vid_txt.configure(state="disabled")
            vid_txt.grid(row=idx + 1, column=3, padx=5)
            row["status_label"] = customtkinter.CTkLabel(scrollable_frame, text="⏳ Chờ xử lý...", width=150)
            row["status_label"].grid(row=idx + 1, column=4, padx=5)
            row["video_path"] = None
            self.table_rows.append(row)

    
    def update_scene_image(self, index, image_path):
        # (Giữ nguyên)
        try:
            img = Image.open(image_path)
            img.thumbnail((140, 80))
            photo = customtkinter.CTkImage(light_image=img, dark_image=img, size=(140, 80))
            self.thumbnail_images.append(photo)
            lbl = self.table_rows[index]["image_label"]
            lbl.configure(image=photo, text="") 
            current_status = self.table_rows[index]["status_label"].cget("text")
            if current_status == "⏳ Đang tạo ảnh...":
                self.table_rows[index]["status_label"].configure(text="🖼️ Ảnh đã tải xong")
        except Exception as e:
            print(f"update_scene_image error (index {index}): {e}")

    def update_scene_status(self, index, status_text):
        # (Giữ nguyên)
        try:
            lbl = self.table_rows[index]["status_label"]
            lbl.configure(text=status_text)
        except Exception as e:
            print(f"update_scene_status error (index {index}): {e}")

    def open_video(self, file_path):
        # (Giữ nguyên)
        try:
            if platform.system() == "Darwin":
                subprocess.call(["open", file_path])
            elif platform.system() == "Windows":
                os.startfile(file_path)
            else:
                subprocess.call(["xdg-open", file_path])
        except Exception as e:
            print(f"Lỗi mở video: {e}")

    def make_thumbnail_clickable(self, index, video_path):
        # (GiGitữ nguyên)
        try:
            self.table_rows[index]["video_path"] = video_path
            lbl = self.table_rows[index]["image_label"]
            lbl.bind("<Button-1>", lambda event, path=video_path: self.open_video(path))
            lbl.configure(cursor="hand2")
        except Exception as e:
            print(f"Lỗi khi gán click cho thumbnail {index}: {e}")

    
    def process_scene(self, index, scene, image_folder, video_folder):
        """
        Hàm này được gọi trong một thread riêng biệt để xử lý 1 scene.
        ĐÃ CẬP NHẬT VỚI LOGIC RETRY.
        """
        try:
            self._log_state(f"Scene {index + 1}/{len(self.screens)}: Bắt đầu xử lý...")

            # --- 1. Sinh ảnh scene (CÓ RETRY) ---
            self.after(0, lambda idx=index: self.update_scene_status(idx, "⏳ Đang tạo ảnh..."))
            
            # Sử dụng lambda để truyền hàm và tham số vào retry_operation
            image_data = self._retry_operation(
                lambda: run_image_recipe(
                    workflow_id=self.workflow_id,
                    aspect_ratio=self.aspect,
                    style=self.style,
                    characters=self.characters,
                    scene=scene
                ),
                max_attempts=3,
                operation_name=f"Tạo ảnh Scene {index + 1}"
            )

            # Nếu retry 3 lần vẫn thất bại, dừng scene này
            if not image_data:
                 self._log_state(f"❌ Xử lý Scene {index + 1} thất bại (Tạo ảnh).")
                 self.after(0, lambda idx=index: self.update_scene_status(idx, "❌ Lỗi tạo ảnh"))
                 return

            # (Lưu ảnh - phần này không phải network, không cần retry)
            image_path = None
            try:
                img_bytes = base64.b64decode(image_data.get("image", ""))
                image_path = os.path.join(image_folder, f"{index + 1}.png")
                with open(image_path, "wb") as f:
                    f.write(img_bytes)
                self.after(0, lambda idx=index, path=image_path: self.update_scene_image(idx, path))
            except Exception as e:
                self._log_state(f"Lỗi lưu ảnh scene {index + 1}: {e}")
                self.after(0, lambda idx=index: self.update_scene_status(idx, "⚠️ Lỗi lưu ảnh"))
                return # Dừng nếu không lưu được ảnh

            # --- 2. Tạo video scene (CÓ RETRY) ---
            self.after(0, lambda idx=index: self.update_scene_status(idx, "⏳ Đang tạo video..."))
            
            video_data = self._retry_operation(
                lambda: generateVideoForScene(
                    scene=scene,
                    aspect_ratio=self.aspect,
                    project_id=self.project_id,
                    image_data=image_data
                ),
                max_attempts=3,
                operation_name=f"Bắt đầu video Scene {index + 1}"
            )
            
            if not video_data or "operations" not in video_data:
                self._log_state(f"❌ Xử lý Scene {index + 1} thất bại (Bắt đầu video).")
                self.after(0, lambda idx=index: self.update_scene_status(idx, "❌ Lỗi bắt đầu video"))
                return

            operation_name = video_data["operations"][0]["operation"]["name"]
            scene_id = video_data["operations"][0]["sceneId"]

            # --- 3. Poll status & Tải video (CÓ RETRY TẢI) ---
            # Vòng lặp Polling (60 lần, 5 phút)
            for attempt in range(60): 
                time.sleep(5)
                try:
                    # Kiểm tra trạng thái
                    check_data = check_video_generation_status(name=operation_name, screen_id=scene_id)
                    op = check_data['operations'][0]['operation']
                    
                    # Nếu video đã sẵn sàng
                    if 'metadata' in op and 'video' in op['metadata'] and 'fifeUrl' in op['metadata']['video']:
                        video_url = op['metadata']['video']['fifeUrl']
                        self._log_state(f"✅ Video Scene {index + 1} đã sẵn sàng. Đang tải...")
                        
                        file_path = os.path.join(video_folder, f"{index + 1}.mp4")
                        
                        # Thử tải video (có retry)
                        download_success = self._retry_operation(
                            lambda: self._download_video_chunked(video_url, file_path),
                            max_attempts=2, # Thử tải 2 lần
                            delay=3,
                            operation_name=f"Tải video Scene {index + 1}"
                        )
                        
                        if download_success:
                            self._log_state(f"✅ Đã lưu video scene {index + 1}: {file_path}")
                            self.after(0, lambda idx=index: self.update_scene_status(idx, "✅ Video đã tải xong"))
                            self.after(0, lambda idx=index, path=file_path: self.make_thumbnail_clickable(idx, path))
                            return # HOÀN THÀNH SCENE NÀY
                        else:
                            # Nếu tải thất bại 2 lần
                            self._log_state(f"❌ Tải video Scene {index + 1} thất bại.")
                            self.after(0, lambda idx=index: self.update_scene_status(idx, "⚠️ Lỗi tải video"))
                            return # Dừng scene này

                except Exception as e:
                    # Lỗi polling (ví dụ: mạng rớt), không sao, vòng lặp sẽ tiếp tục
                    self._log_state(f"Lỗi poll Scene {index + 1} (lần {attempt + 1}): {e}. Sẽ thử lại...")
                    pass 

            # Nếu vòng lặp 60 lần kết thúc mà không 'return'
            self._log_state(f"⚠️ Timeout video scene {index + 1}")
            self.after(0, lambda idx=index: self.update_scene_status(idx, "⚠️ Lỗi video (timeout)"))

        except Exception as e:
            self._log_state(f"Lỗi nghiêm trọng scene {index + 1}: {e}")
            self.after(0, lambda idx=index, msg=str(e): self.update_scene_status(idx, f"⚠️ Lỗi: {msg[:30]}..."))
            raise e

    
    def run_api_in_thread(self):
        # (Hàm này giữ nguyên, vì logic retry đã ở trong process_scene)
        try:
            self._log_state("Tạo workflow...")
            self.workflow_id = create_or_update_workflow()
            self._log_state(f"Workflow: {self.workflow_id}")
            self._log_state("Tạo project...")
            project_res = create_project()
            self.project_id = project_res.get("projectId")
            self._log_state(f"Project: {self.project_id}")
            self._log_state("Đang tạo kế hoạch video (kịch bản, nhân vật, cảnh)...")
            video_plan = generate_full_video_plan(
                mode=GenerationMode.IDEA, 
                idea=self.content,
                style=self.style,
                duration=self.duration,
                language=self.language,
                include_narration=False 
            )
            character_folder = os.path.join(self.folder, "characters")
            image_folder = os.path.join(self.folder, "images")
            video_folder = os.path.join(self.folder, "video")
            os.makedirs(character_folder, exist_ok=True)
            os.makedirs(image_folder, exist_ok=True)
            os.makedirs(video_folder, exist_ok=True)
            self.characters = []
            characters_list = video_plan.get("characters", [])
            self._log_state(f"Tìm thấy {len(characters_list)} nhân vật. Đang tạo ảnh tham chiếu...")
            
            # --- TẠO ẢNH NHÂN VẬT (CÓ RETRY) ---
            for idx, ch in enumerate(characters_list):
                desc = ch.get("description", "")
                name = ch.get("name", f"char_{idx + 1}")
                self._log_state(f"Đang tạo ảnh cho NV: {name}...")
                if not desc:
                    self._log_state(f"⚠️ Lỗi: Mô tả cho nhân vật {name} bị rỗng. Bỏ qua...")
                    continue
                
                # Thêm retry cho tạo ảnh nhân vật
                image_data = self._retry_operation(
                    lambda: generate_image_subject_text(
                        description=desc,
                        workflow_id=self.workflow_id,
                        aspect_ratio=self.aspect, 
                        style=self.style
                    ),
                    max_attempts=3,
                    operation_name=f"Tạo ảnh NV {name}"
                )

                if not image_data or not image_data.get("image"):
                    self._log_state(f"⚠️ LỖI: Không tìm thấy 'image' data cho NV {name} sau khi retry. (Safety Filter?). Bỏ qua.")
                    continue
                
                image_base64_data = image_data.get("image")
                try:
                    image_bytes = base64.b64decode(image_base64_data)
                    image_path = os.path.join(character_folder, f"{name}.png")
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    self._log_state(f"✅ Đã lưu ảnh cho NV: {name}")
                    self.characters.append({
                        "id": image_data.get("id"),
                        "promptImage": image_data.get("promptImage"),
                        "refImageBase64": image_base64_data,
                        "refImageUrl": f"data:image/png;base64,{image_base64_data}",
                        "name": name,
                        "image_path": image_path
                    })
                except Exception as e:
                    self._log_state(f"⚠️ Lỗi decode/lưu ảnh NV {name}: {e}")
                    continue

            # --- LẤY SCENE VÀ TẠO BẢNG ---
            self.screens = video_plan.get("scenes", [])
            if not self.screens:
                self._log_state("⚠️ LỖI NGHIÊM TRỌNG: Kế hoạch video không trả về 'scenes' nào.")
                raise Exception("Không tạo được scene, video plan bị lỗi.")
            self._log_state(f"Đã tạo {len(self.screens)} scene. Hiển thị bảng...")
            self.after(0, lambda: self.init_scene_table(self.screens))
            self.after(0, lambda: self.progressbar.stop()) 
            self.after(0, lambda: self.progressbar.pack_forget()) 
            
            # === TẠO TASK BẤT ĐỒNG BỘ ===
            NUM_WORKERS = 4 
            self._log_state(f"Bắt đầu tạo video cho {len(self.screens)} scene ({NUM_WORKERS} luồng song song)...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
                futures = [
                    executor.submit(self.process_scene, index, scene, image_folder, video_folder)
                    for index, scene in enumerate(self.screens)
                ]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result() 
                    except Exception as e:
                        self._log_state(f"Một luồng xử lý scene gặp lỗi: {e}")
                        print(f"THREAD POOL EXCEPTION: {e}")
            self.after(0, lambda: self.loading_label.configure(text="✅ Hoàn tất tất cả scene!"))
        
        except Exception as e:
            self._log_state(f"THREAD ERROR: {e}")
            self.after(0, lambda err=e: self.loading_label.configure(text=f"Lỗi: {err}"))
            self.after(0, lambda: self.progressbar.stop())

    def _log_state(self, message: str):
        # (Giữ nguyên)
        print(message)
        try:
            if hasattr(self, 'loading_label'):
                self.after(0, lambda: self.loading_label.configure(text=message))
        except Exception as e:
            print(f"Lỗi _log_state (bỏ qua): {e}")
            pass
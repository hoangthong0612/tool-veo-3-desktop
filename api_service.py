from type import Scene

API_BASE_URL = "https://api.example.com"  # thay bằng API thật của bạn
from tkinter import messagebox
import requests
import random
import time
from helper import get_config
import json
import uuid


def create_or_update_workflow():
    try:
        # Tạo sessionId ngẫu nhiên 13 chữ số
        session_id = ";" + ''.join(str(random.randint(0, 9)) for _ in range(13))

        url = "https://labs.google/fx/api/trpc/media.createOrUpdateWorkflow"
        headers = {
            "Cookie": get_config().get('cookie', "")
        }
        payload = {
            "json": {
                "clientContext": {
                    "tool": "BACKBONE",
                    "sessionId": session_id
                },
                "mediaGenerationIdsToCopy": [],
                "workflowMetadata": {
                    "workflowName": f"workflow_{int(time.time())}"
                }
            }
        }

        # Gọi API
        response = requests.post(url, headers=headers, json=payload)

        if not response.ok:
            messagebox.showerror("Lỗi", "Không có dữ liệu từ API.")
            return

        data = response.json()
        workflow_id = data.get("result", {}).get("data", {}).get("json", {}).get("result", {}).get("workflowId")

        if workflow_id:
            return workflow_id
        else:
            messagebox.showerror("Lỗi", "Không có dữ liệu từ API.")
            return

    except Exception as e:
        messagebox.showerror("Lỗi", e)


def generate_image_subject_text(workflow_id=None, description="", aspect_ratio="", style=""):
    try:

        if not workflow_id or not description:
            messagebox.showerror("Thiếu dữ liệu", "Vui lòng nhập đầy đủ Workflow ID và Prompt.")
            return None
        prompt = f"""
        Full-body character concept art. 
        A detailed portrait of the following character in a neutral, standing pose with no background (transparent or plain white). 
        Focus entirely on the character’s design and appearance — no scenery, no effects, no shadows. 
        The image should serve as a clear reference for the character's full-body look. 
        Style: ${style}. 
        Character description: ${description}
        """

        # Gọi API session để lấy token

        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ.")
            return None

        # Chuẩn bị request gọi API tạo ảnh
        aspect_map = {
            "9:16": "IMAGE_ASPECT_RATIO_PORTRAIT",
            "16:9": "IMAGE_ASPECT_RATIO_LANDSCAPE",
            "1:1": "IMAGE_ASPECT_RATIO_SQUARE"
        }

        session_id = ";" + ''.join(str(random.randint(0, 9)) for _ in range(13))
        payload = {
            "clientContext": {
                "workflowId": workflow_id,
                "tool": "BACKBONE",
                "sessionId": session_id
            },
            "imageModelSettings": {
                "imageModel": "IMAGEN_3_5",
                "aspectRatio": aspect_map.get(aspect_ratio, 'IMAGE_ASPECT_RATIO_PORTRAIT')
            },
            "prompt": prompt,
            "mediaCategory": "MEDIA_CATEGORY_SUBJECT"
        }

        res = requests.post(
            "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )

        if not res.ok:
            messagebox.showerror("Lỗi", f"Không có dữ liệu. Mã lỗi {res.status_code}")
            return None

        data = res.json()
        image_panels = data.get("imagePanels") or []

        # Truy cập an toàn tương tự ?. trong JS
        image_part = (
            image_panels[0]["generatedImages"][0].get("encodedImage")
            if image_panels and image_panels[0].get("generatedImages")
            else None
        )

        if not image_part:
            raise ValueError("Reference image data not found in response.")

        return {
            "image": image_part,
            "id": (
                image_panels[0]["generatedImages"][0].get("mediaGenerationId")
                if image_panels and image_panels[0].get("generatedImages")
                else None
            ),
            "promptImage": image_panels[0].get("prompt") if image_panels else None,
        }

    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi gọi API:\n{e}")
        return None


# Tỷ lệ khung hình API
ASPECT_RATIO_MAP = {
    "9:16": "IMAGE_ASPECT_RATIO_PORTRAIT",
    "16:9": "IMAGE_ASPECT_RATIO_LANDSCAPE",
    "1:1": "IMAGE_ASPECT_RATIO_SQUARE"
}


def run_image_recipe(workflow_id: str, scene: dict, characters: list, aspect_ratio: str, style: str):
    """
        Gọi API để tạo hình ảnh cho một cảnh, chỉ sử dụng các nhân vật có trong cảnh đó.
        """
    try:
        # 🔸 1. Kiểm tra tham số (Giữ nguyên)
        if not workflow_id or not scene:
            messagebox.showerror("Lỗi", "Thiếu workflow_id hoặc scene.")
            return None

        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ hoặc đã hết hạn.")
            return None

        # 🔸 2. Kiểm tra prompt (Giữ nguyên)
        image_prompt_text = scene.get("imagePrompt")
        if not image_prompt_text:
            msg = f"Lỗi nghiêm trọng: Scene {scene.get('sceneNumber')} có 'imagePrompt' rỗng. Không thể tạo ảnh."
            print(msg)
            messagebox.showerror("Lỗi Prompt", msg)
            return None

        full_image_prompt = f"{image_prompt_text}, in the style of {style}"

        # 🔸 3. Xử lý danh sách nhân vật (Giữ nguyên)
        image_parts = []
        required_char_names = scene.get("charactersInScene", [])

        if required_char_names:
            character_map = {char['name']: char for char in characters}
            for name in required_char_names:
                character = character_map.get(name)
                if character and character.get("refImageBase64") and character.get("id"):
                    image_parts.append({
                        "mediaInput": {
                            "mediaCategory": "MEDIA_CATEGORY_SUBJECT",
                            "mediaGenerationId": character["id"]
                        }
                    })
                # (Các print cảnh báo khác giữ nguyên)

        # 🔸 4. (ĐÃ CẬP NHẬT) Chuẩn bị Payload và URL động

        session_id = f";{random.randint(10 ** 12, (10 ** 13) - 1)}"
        api_url = ""
        payload = {}

        # Lấy giá trị aspect ratio, mặc định là PORTRAIT
        aspect_ratio_value = ASPECT_RATIO_MAP.get(aspect_ratio, "IMAGE_ASPECT_RATIO_PORTRAIT")

        # --- BẮT ĐẦU LOGIC RẼ NHÁNH ---
        if not image_parts:
            # --- TRƯỜNG HỢP 1: KHÔNG có nhân vật (len = 0) ---
            # Gọi API 'generateImage'
            api_url = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
            payload = {
                "clientContext": {
                    "workflowId": workflow_id,  # Dùng workflow_id động
                    "tool": "BACKBONE",
                    "sessionId": session_id
                },
                "imageModelSettings": {
                    "imageModel": "IMAGEN_3_5",  # Model như bạn yêu cầu
                    "aspectRatio": aspect_ratio_value
                },
                "seed": 1000000,  # Giữ seed cố định
                "prompt": full_image_prompt,  # Dùng prompt đã xử lý
                "mediaCategory": "MEDIA_CATEGORY_BOARD"
            }
            print(f"📤 Gửi payload (generateImage) cho Scene: {scene.get('sceneNumber')}")

        else:
            # --- TRƯỜNG HỢP 2: CÓ nhân vật (len > 0) ---
            # Gọi API 'runImageRecipe' (như cũ)
            api_url = "https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe"
            payload = {
                "clientContext": {
                    "workflowId": workflow_id,
                    "tool": "BACKBONE",
                    "sessionId": session_id
                },
                "seed": 1000000,
                "imageModelSettings": {
                    "imageModel": "R2I",
                    "aspectRatio": aspect_ratio_value
                },
                "userInstruction": full_image_prompt,
                "recipeMediaInputs": image_parts
            }
            print(f"📤 Gửi payload (runImageRecipe) cho Scene: {scene.get('sceneNumber')}")

        # --- KẾT THÚC LOGIC RẼ NHÁNH ---

        print(json.dumps(payload, indent=2))  # In payload ra để debug

        # 🔸 5. Gửi request (Giờ đã dùng api_url động)
        res = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=60
        )

        # 🔸 6. Xử lý phản hồi (ĐÃ CẬP NHẬT)
        if res.status_code != 200:
            print(f"Lỗi API tạo ảnh: {res.status_code} - {res.text}")
            messagebox.showerror("Lỗi API", f"Không thể tạo ảnh (Lỗi {res.status_code}). Chi tiết: {res.text}")
            return None

        data = res.json()
        print("--- DEBUG: Phản hồi THÔ từ API ---")
        print(json.dumps(data, indent=2))
        print("-----------------------------------")

        image_part = None
        media_id = None

        # --- BẮT ĐẦU LOGIC PARSE PHẢN HỒI (MỚI) ---
        if not image_parts:
            # Phản hồi từ 'generateImage'
            # Giả định cấu trúc là: {"generatedImages": [{"encodedImage": "...", "mediaGenerationId": "..."}]}
            try:
                generated_images = data.get("generatedImages", [])
                if not generated_images:
                    raise Exception("Không tìm thấy 'generatedImages' trong phản hồi.")

                first_image = generated_images[0]
                image_part = first_image.get("encodedImage")
                media_id = first_image.get("mediaGenerationId")
            except Exception as e:
                print(f"Lỗi Parse (generateImage): {e}. Phản hồi: {data}")
                messagebox.showerror("Lỗi", f"Lỗi phân tích phản hồi 'generateImage': {e}")
                return None
        else:
            # Phản hồi từ 'runImageRecipe' (như cũ)
            try:
                image_panels = data.get("imagePanels", [])
                if not image_panels or not image_panels[0].get("generatedImages"):
                    raise Exception("Không tìm thấy 'imagePanels' hoặc 'generatedImages' trong phản hồi.")

                first_image = image_panels[0]["generatedImages"][0]
                image_part = first_image.get("encodedImage")
                media_id = first_image.get("mediaGenerationId")
            except Exception as e:
                print(f"Lỗi Parse (runImageRecipe): {e}. Phản hồi: {data}")
                messagebox.showerror("Lỗi", f"Lỗi phân tích phản hồi 'runImageRecipe': {e}")
                return None

        # --- KẾT THÚC LOGIC PARSE PHẢN HỒI ---

        if not image_part:
            print(f"Lỗi Phản hồi: 'encodedImage' bị rỗng. Phản hồi: {data}")
            messagebox.showerror("Lỗi", "Reference image data not found in response (empty).")
            return None

        # Trả về kết quả đã chuẩn hóa
        return {
            "id": media_id,
            "image": image_part
        }

    except requests.exceptions.RequestException as e:
        print(f"Lỗi Mạng (RequestException): {e}")
        messagebox.showerror("Lỗi Mạng", f"Không thể kết nối đến server: {e}")
        return None
    except Exception as e:
        print(f"Lỗi không xác định trong run_image_recipe: {e}")
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
        return None


def create_project():
    try:
        url = "https://labs.google/fx/api/trpc/project.createProject"
        headers = {
            # 👇 Chỉ server mới được quyền gắn cookie header
            "Cookie": get_config().get('cookie', ""),
            "Content-Type": "application/json",
        }

        payload = {
            "json": {
                "projectTitle": "New",
                "toolName": "PINHOLE"
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if not response.ok:
            messagebox.showerror("Lỗi", "Không có dữ liệu từ API.")
            return

        data = response.json()
        project_id = (
            data.get("result", {})
            .get("data", {})
            .get("json", {})
            .get("result", {})
            .get("projectId")
        )
        return {"status": 1, "projectId": project_id}
    except Exception as e:
        messagebox.showerror("Lỗi", e)


def generateVideoForScene(scene: dict, image_data: dict, aspect_ratio: str, project_id: str):
    try:
        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ.")
            return None

            # --- 2️⃣ Xử lý aspect ratio & model ---
        aspect_ratio_setting = "VIDEO_ASPECT_RATIO_PORTRAIT"
        model_key = "veo_3_1_i2v_s_fast_portrait_ultra"

        if aspect_ratio == "16:9":
            aspect_ratio_setting = "VIDEO_ASPECT_RATIO_LANDSCAPE"
            model_key = "veo_3_1_i2v_s_fast_ultra"

        # --- 3️⃣ Gửi request tạo video ---
        video_url = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoStartImage"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        body = {
            "clientContext": {
                "projectId": project_id,
                "tool": "PINHOLE",
                "userPaygateTier": "PAYGATE_TIER_TWO"
            },
            "requests": [
                {
                    "aspectRatio": aspect_ratio_setting,
                    "seed": 100000,
                    "textInput": {"prompt": scene['videoPrompt']},
                    "promptExpansionInput": {
                        "prompt": scene['videoPrompt'],
                        "seed": 100000,
                        "templateId": "0TNlfC6bSF",
                        "imageInputs": [
                            {
                                "mediaId": image_data["id"],
                                "imageUsageType": "IMAGE_USAGE_TYPE_UNSPECIFIED"
                            }
                        ]
                    },
                    "videoModelKey": model_key,
                    "startImage": {"mediaId": image_data["id"]},
                    "metadata": {"sceneId": str(uuid.uuid4())}
                }
            ]
        }

        res = requests.post(video_url, headers=headers, data=json.dumps(body))

        if not res.ok:
            messagebox.showerror("Lỗi", "Token không hợp lệ.")
            return {"status": 0, "message": "Không có dữ liệu", "code": res.status_code}

        data = res.json()
        return data

    except Exception as e:
        messagebox.showerror("Lỗi", e)
        return {"status": 0, "message": "Lỗi proxy"}


def check_video_generation_status(name: str, screen_id: str):
    """
    Kiểm tra trạng thái video đang được sinh từ Google AI Sandbox API.
    Tương đương với đoạn Next.js POST request.
    """

    if not name or not screen_id:
        messagebox.showerror("Lỗi", "Thiếu tham số")
        return {"status": 0, "message": "Thiếu tham số"}

    try:
        # Lấy cookie từ biến môi trường (giống process.env.NEXT_PUBLIC_COOKIE_NAME)
        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ.")
            return None

        # Gọi API kiểm tra trạng thái video
        payload = {
            "operations": [
                {
                    "operation": {"name": name},
                    "sceneId": screen_id,
                    "status": "MEDIA_GENERATION_STATUS_PENDING"
                }
            ]
        }

        res = requests.post(
            "https://aisandbox-pa.googleapis.com/v1/video:batchCheckAsyncVideoGenerationStatus",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            data=json.dumps(payload)
        )

        if res.status_code != 200:
            return {"status": 0, "message": "Không có dữ liệu", "http_status": res.status_code}

        data = res.json()
        print("✅ Video generation status data:", data)
        return data

    except Exception as e:
        print("❌ Lỗi trong quá trình kiểm tra video:", e)
        return {"status": 0, "message": "Lỗi proxy"}

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


def run_image_recipe(workflow_id: str, scene: dict, characters: list, aspect_ratio: str, style: str):
    try:
        # 🔸 Kiểm tra tham số
        if not workflow_id or not scene:
            messagebox.showerror("Lỗi", "Thiếu tham số.")
            return None

        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ.")
            return None

        full_image_prompt = f"""{scene['imagePrompt']}, in the style of {style}"""
        # 🔸 Xử lý danh sách nhân vật (character)
        image_parts = []
        for character in characters:
            if character.get("refImageBase64"):
                image_parts.append({
                    "mediaInput": {
                        "mediaCategory": "MEDIA_CATEGORY_SUBJECT",
                        "mediaGenerationId": character["id"]
                    }
                })

        # 🔸 Xác định tỷ lệ ảnh
        aspect_map = {
            "9:16": "IMAGE_ASPECT_RATIO_PORTRAIT",
            "16:9": "IMAGE_ASPECT_RATIO_LANDSCAPE",
            "1:1": "IMAGE_ASPECT_RATIO_SQUARE"
        }

        # 🔸 Sinh sessionId ngẫu nhiên (13 ký tự)
        session_id = ";" + "".join([str(random.randint(0, 9)) for _ in range(13)])

        # 🔸 Dữ liệu gửi đi
        payload = {
            "clientContext": {
                "workflowId": workflow_id,
                "tool": "BACKBONE",
                "sessionId": session_id
            },
            "seed": 1000000,
            "imageModelSettings": {
                "imageModel": "R2I",
                "aspectRatio": aspect_map.get(aspect_ratio, "IMAGE_ASPECT_RATIO_PORTRAIT")
            },
            "userInstruction": full_image_prompt,
            "recipeMediaInputs": image_parts
        }

        print("📤 Payload gửi đi:")

        # 🔸 Gửi request tạo ảnh
        res = requests.post(
            "https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )

        if res.status_code != 200:
            messagebox.showerror("Lỗi", "Không có dữ liệu")

        data = res.json()
        image_panels = data.get("imagePanels", []) or []

        # Kiểm tra dữ liệu hợp lệ
        if not image_panels or not image_panels[0].get("generatedImages"):
            messagebox.showerror("Lỗi", "Reference image data not found in response.")
            return None
        # Lấy ảnh đầu tiên
        first_image = image_panels[0]["generatedImages"][0]
        image_part = first_image.get("encodedImage")
        media_id = first_image.get("mediaGenerationId")

        if not image_part:
            messagebox.showerror("Lỗi", "Reference image data not found in response.")
            return None

        return {
            "id": media_id,
            "image": image_part
        }

    except Exception as e:
        messagebox.showerror("Lỗi", e)


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


from app.utils.models import Scene # <-- SỬA IMPORT
from tkinter import messagebox
import requests
import random
import time
from app.utils.helper import get_config # <-- SỬA IMPORT
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
    Gọi API để tạo hình ảnh cho một cảnh.
    ĐÃ SỬA LỖI: Loại bỏ trường "name" không hợp lệ khỏi payload.
    """
    try:
        # 🔸 1. Kiểm tra tham số
        if not workflow_id or not scene:
            messagebox.showerror("Lỗi", "Thiếu workflow_id hoặc scene (run_image_recipe).")
            return None

        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ hoặc đã hết hạn (run_image_recipe).")
            return None

        # 🔸 2. Kiểm tra prompt
        image_prompt_text = scene.get("imagePrompt")
        if not image_prompt_text:
            msg = f"Lỗi nghiêm trọng: Scene {scene.get('sceneNumber')} có 'imagePrompt' rỗng. Không thể tạo ảnh."
            print(msg)
            messagebox.showerror("Lỗi Prompt", msg)
            return None

        full_image_prompt = f"{image_prompt_text}, in the style of {style}"
        scene_number_for_logging = scene.get('sceneNumber', 'Unknown')

        # ==================================================================
        # === BẮT ĐẦU PHẦN SỬA LỖI LOGIC (Loại bỏ trường "name") ===
        # ==================================================================

        # 🔸 3. Xử lý danh sách nhân vật
        image_parts = [] # Đây là danh sách payload CUỐI CÙNG gửi cho API
        required_char_names = scene.get("charactersInScene", [])

        if required_char_names:
            character_map = {char['name']: char for char in characters}
            
            # 1. Tìm TẤT CẢ các nhân vật hợp lệ trước
            # Danh sách này sẽ chứa các tuple (payload_dict, name_string)
            found_characters_for_scene = [] 
            for name in required_char_names:
                character = character_map.get(name)
                if character and character.get("id"):
                    
                    # Đây là đối tượng payload mà API CHẤP NHẬN
                    api_payload_object = {
                        "mediaInput": {
                            "mediaCategory": "MEDIA_CATEGORY_SUBJECT",
                            "mediaGenerationId": character["id"]
                        }
                    }
                    # Lưu cả payload và tên (để dùng cho cảnh báo)
                    found_characters_for_scene.append( (api_payload_object, name) )
                else:
                    print(f"⚠️ Cảnh báo Scene {scene_number_for_logging}: Yêu cầu nhân vật '{name}' nhưng không tìm thấy ID ảnh tham chiếu.")

            # 2. Kiểm tra giới hạn 3 nhân vật
            if len(found_characters_for_scene) > 3:
                characters_to_send = found_characters_for_scene[:3]
                characters_omitted = found_characters_for_scene[3:]
                
                # Chỉ lấy payload (phần tử [0] của tuple)
                image_parts = [char_tuple[0] for char_tuple in characters_to_send]
                
                # Chỉ lấy tên (phần tử [1] của tuple) để cảnh báo
                sent_names = [char_tuple[1] for char_tuple in characters_to_send]
                omitted_names = [char_tuple[1] for char_tuple in characters_omitted]
                
                msg = f"Cảnh báo Scene {scene_number_for_logging}:\n\n" \
                      f"Cảnh này yêu cầu {len(found_characters_for_scene)} nhân vật, nhưng API chỉ hỗ trợ tối đa 3.\n\n" \
                      f"Đang gửi: {sent_names}\n" \
                      f"Bỏ qua: {omitted_names}"
                
                print(f"❌ {msg}")
                messagebox.showwarning("Giới hạn API (3 Nhân vật)", msg)
                
            else:
                # Nếu từ 3 trở xuống, lấy tất cả payload
                image_parts = [char_tuple[0] for char_tuple in found_characters_for_scene]
        
        # ==================================================================
        # === KẾT THÚC PHẦN SỬA LỖI LOGIC ===
        # ==================================================================


        # 🔸 4. Chuẩn bị Payload và URL động (Giữ nguyên)
        session_id = f";{random.randint(10 ** 12, (10 ** 13) - 1)}"
        api_url = ""
        payload = {}

        aspect_ratio_value = ASPECT_RATIO_MAP.get(aspect_ratio, "IMAGE_ASPECT_RATIO_PORTRAIT")

        if not image_parts:
            # --- TRƯỜNG HỢP 1: KHÔNG có nhân vật (gọi generateImage) ---
            api_url = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
            payload = {
                "clientContext": {"workflowId": workflow_id, "tool": "BACKBONE", "sessionId": session_id},
                "imageModelSettings": {"imageModel": "IMAGEN_3_5", "aspectRatio": aspect_ratio_value},
                "seed": 1000000,
                "prompt": full_image_prompt,
                "mediaCategory": "MEDIA_CATEGORY_BOARD"
            }
            print(f"📤 Gửi payload (generateImage) cho Scene: {scene_number_for_logging}")

        else:
            # --- TRƯỜNG HỢP 2: CÓ nhân vật (gọi runImageRecipe) ---
            api_url = "https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe"
            payload = {
                "clientContext": {"workflowId": workflow_id, "tool": "BACKBONE", "sessionId": session_id},
                "seed": 1000000,
                "imageModelSettings": {"imageModel": "R2I", "aspectRatio": aspect_ratio_value},
                "userInstruction": full_image_prompt,
                "recipeMediaInputs": image_parts # <-- DANH SÁCH NÀY GIỜ ĐÃ SẠCH (KHÔNG CÓ "name")
            }
            print(f"📤 Gửi payload (runImageRecipe) cho Scene: {scene_number_for_logging} với {len(image_parts)} nhân vật.")


        # 🔸 5. Gửi request (Giữ nguyên)
        res = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=60
        )

        # 🔸 6. Xử lý phản hồi (Giữ nguyên)
        if res.status_code != 200:
            print(f"Lỗi API tạo ảnh: {res.status_code} - {res.text}")
            messagebox.showerror("Lỗi API", f"Không thể tạo ảnh (Lỗi {res.status_code}). Chi tiết: {res.text}")
            return None

        data = res.json()
        image_part = None
        media_id = None

        if not image_parts:
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

        if not image_part:
            print(f"Lỗi Phản hồi: 'encodedImage' bị rỗng. Phản hồi: {data}")
            messagebox.showerror("Lỗi", "Reference image data not found in response (empty).")
            return None

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
    """
    Tạo video.
    - Nếu có image_data: Gọi Image-to-Video (batchAsyncGenerateVideoStartImage).
    - Nếu image_data là None: Gọi Text-to-Video (batchAsyncGenerateVideo).
    """
    try:
        token = get_config().get('access_token', "")
        if not token:
            messagebox.showerror("Lỗi", "Token không hợp lệ (generateVideoForScene).")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # --- LOGIC RẼ NHÁNH T2V / I2V ---
        if image_data:
            # === CASE 1: IMAGE-TO-VIDEO (Có ảnh tham chiếu) ===
            video_url = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoStartImage"

            aspect_ratio_setting = "VIDEO_ASPECT_RATIO_PORTRAIT"
            model_key = "veo_3_1_i2v_s_fast_portrait_ultra"
            if aspect_ratio == "16:9":
                aspect_ratio_setting = "VIDEO_ASPECT_RATIO_LANDSCAPE"
                model_key = "veo_3_1_i2v_s_fast_ultra"

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

        else:
            # === CASE 2: TEXT-TO-VIDEO (Không có ảnh tham chiếu) ===
            video_url = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText"

            aspect_ratio_setting = "VIDEO_ASPECT_RATIO_PORTRAIT"
            model_key = "veo_3_1_t2v_fast_portrait_ultra"  # <-- Model T2V
            if aspect_ratio == "16:9":
                aspect_ratio_setting = "VIDEO_ASPECT_RATIO_LANDSCAPE"
                model_key = "veo_3_1_t2v_fast_ultra"  # <-- Model T2V Landscape

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
                        # Không có promptExpansionInput với imageInputs
                        # Không có startImage
                        "videoModelKey": model_key,
                        "metadata": {"sceneId": str(uuid.uuid4())}
                    }
                ]
            }

        # Gửi request
        res = requests.post(video_url, headers=headers, data=json.dumps(body))

        if not res.ok:
            print(f"Lỗi API Video: {res.text}")
            # Không show popup lỗi ở đây để tránh spam khi chạy batch
            return {"status": 0, "message": f"Lỗi API: {res.status_code}", "code": res.status_code}

        data = res.json()
        return data

    except Exception as e:
        print(f"Lỗi generateVideoForScene: {e}")
        return {"status": 0, "message": str(e)}


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

import json
from itertools import count

from google import genai
from google.genai import types
from helper import get_config
from type import GenerationMode, Language
import math

client = genai.Client(
    api_key=get_config().get('api_key', "")
)


def suggest_idea(idea):
    response = client.models.generate_content(
        model="gemini-2.5-flash",

        contents=f"""
            Generate a short, compelling story idea in English. The idea should be visual and suitable for a short video. Current idea fragment: "{idea}" 
        """,
    )
    return response.text


def generate_script_and_characters(mode: GenerationMode, idea="", style="", duration=16, script="",
                                   language="English", ):
    schema = {
        "properties": {
            "script": {"type": 'string', "description": f"""The full, coherent story script, in {language}."""},
            "characters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string",
                                        "description": "A highly detailed visual description of the character's appearance, in English. Ensure the character's facial features and ethnicity are appropriate for the story's geographical and cultural setting. Include details on facial features, hair, body type, clothing, accessories, and demeanor for consistent image generation, maximum 3 characters"},
                    },
                    "required": ["name", "description"]
                }
            },
            "landscapes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string",
                                        "description": "A detailed visual description of the landscape, setting, or environment, in English, including atmosphere, key elements, and color palette for consistent image generation.Maximum of 1"},
                    },
                    "required": ["name", "description"]
                }
            }
        },
        "required": ["script", "characters", "landscapes"],
        'type': 'object',
    }

    characterDescriptionInstruction = """For each character, provide a highly detailed visual description in English. This description is critical for AI image generation and must include specifics about their:
- Facial features (e.g., eye shape and color, nose, mouth, jawline). Ensure the character's facial features and ethnicity are appropriate for the story's geographical and cultural setting.
- Hair (e.g., color, length, style, texture)
- Body type (e.g., tall, short, slim, muscular)
- Clothing (be very specific about the type, style, colors, and textures of their garments)
- Key accessories or props (e.g., glasses, a specific hat, a futuristic watch)
- Overall demeanor (e.g., cheerful, grim, tired)."""

    landscapeDescriptionInstruction = """For each landscape, provide a highly detailed visual description in English, including the atmosphere, key elements, and color palette."""
    if mode == 'idea':
        prompt = f"""Based on the idea "{idea}" and style "{style}", write a coherent and engaging script in {language} for a {duration}-second video. Also, identify the main characters AND key landscapes/settings. The character and landscape names and their detailed descriptions MUST be in English. Only the script itself should be in {language}. {characterDescriptionInstruction} {landscapeDescriptionInstruction}"""
    else:
        prompt = f"""Analyze the following script, which is in {language}. Identify the main characters AND key landscapes/settings. The character and landscape names and their descriptions MUST be in English. Reformat the script if necessary to be more cinematic, keeping it in {language}. Script: '{script}'"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfigDict({
            'response_mime_type': 'application/json',
            'response_json_schema': schema
        })
    )
    return response.parsed


# idea = suggest_idea("Truyền thuyết sơn tinh thuỷ tinh việt nam")
# cont = json.loads(generate_script_and_characters(idea=idea, style="3d animation", mode='idea'))

def generate_scene_prompts(script="", characters=None, duration=16, style="", language="", include_narration=False):
    character_descriptions = '\n'.join([f"{c['name']}: {c['description']}" for c in characters])
    print("character_descriptions")
    print(character_descriptions)
    num_scenes = math.ceil(float(duration) / 8)

    scene_properties = {
        "sceneNumber": {
            "type": 'number',
        },
        "scriptPortion": {
            "type": "string",
            "description": f"The part of the script this scene covers, in {language}."
        },
        "imagePrompt": {"type": "string",
                        "description": f"A detailed prompt in English for generating a single, static keyframe image for this scene. Instead of using character or landscape names, embed their full descriptions directly into the prompt for maximum visual consistency. Style: {style}."},
        "videoPrompt": {
            "type": "string",
            "description": f"""A prompt in English describing the action for an 8-second video clip. If the script portion contains character dialogue (e.g., 'ANNA: Look out!'), you MUST incorporate the dialogue into this prompt (e.g., 'Anna shouts "Look out!" with a worried expression'). Style: {style}. The video should have music, but no other background noise or sound effects."""
        },
        # "charactersInScene": {
        #     "type": "array",
        #     "items": {"type": "string", },
        #     "description": "A list of the exact names of characters present in this scene. E.g., ['Bob', 'Alice']"
        # },

    }

    required_fields = ["sceneNumber", "scriptPortion", "imagePrompt", "videoPrompt"]
    if include_narration:
        scene_properties['narration'] = {
            "type": "string",
            "description": f"""If the script portion contains text for a narrator(not spoken by a character), provide that narration script here, in {language}.If the scene only contains dialogue, this field should be an empty string.The narration should be about 8 seconds long. """}
        required_fields.append("narration")

    scene_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": scene_properties,
            "required": required_fields
        }
    }

    narration_instruction = f""" 6. A narration script (in {language}). This is ONLY for a narrator's voice-over. If the scene only has dialogue, this field should be empty. """ if include_narration else ""
    prompt = f""" The user's script is in {language}. Break down this script into {num_scenes} distinct scenes. Each scene will be an 8-second video. For each scene, provide:
1. A concise portion of the script (in {language}), including character dialogue and actions.
2. A detailed image prompt (MUST be in English).
3. A detailed video prompt (MUST be in English).
4. A list of character names in the scene.
{narration_instruction}

IMPORTANT:
- The 'scriptPortion' and 'narration' MUST be in {language}.
- The 'imagePrompt' and 'videoPrompt' MUST be in English for the generation models.
- When creating image/video prompts, you MUST replace character/landscape names with their full descriptions provided below.
- CRITICAL for Video Prompt: If the script portion has character dialogue, you MUST include the dialogue text and the speaking action in the video prompt. For example, if the script is "ANNA: I found it!", the video prompt should be something like "Anna holds up a glowing orb and exclaims 'I found it!', her face lit with excitement".
- CRITICAL for Narration: The narration field is ONLY for a narrator's voice-over. DO NOT put character dialogue in the narration field.
---
SCRIPT: {script}
---
CHARACTERS:
{character_descriptions}
---
 """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfigDict({
            'response_mime_type': 'application/json',
            'response_json_schema': scene_schema
        })
    )
    return response.parsed


def generate_full_video_plan(
        mode: GenerationMode,
        idea: str = "",
        style: str = "",
        duration: int = 16,
        script: str = "",
        language: str = "English",
        include_narration: bool = False
):
    """
    Tạo ra một kế hoạch video hoàn chỉnh (nhân vật và các cảnh đã chia nhỏ)
    chỉ trong một lần gọi API duy nhất, với các prompt đã được "nhúng" mô tả.
    """

    scene_duration = 8
    num_scenes = math.ceil(float(duration) / scene_duration)

    # --- ĐỊNH NGHĨA SCHEMA ---

    # --- CẬP NHẬT (Thêm quy tắc LOGIC) ---
    scene_properties = {
        "sceneNumber": {
            "type": 'number',
            "description": "Số thứ tự của cảnh."
        },
        "scriptPortion": {
            "type": "string",
            "description": f"Phần kịch bản (lời thoại, hành động) cho cảnh này, bằng ngôn ngữ {language}."
        },
        "imagePrompt": {
            "type": "string",
            "description": f"""Một prompt chi tiết, MỘT DÒNG, BẰNG TIẾNG ANH để tạo ảnh tĩnh.
LOGIC: Bối cảnh, vật thể, và kiến trúc phải logic, chính xác và phù hợp với nhân vật, thời đại, và bối cảnh chung của câu chuyện.
NHẤT QUÁN: Nếu cảnh này có nhân vật, BẮT BUỘC phải sao chép (copy-paste) TOÀN BỘ mô tả chi tiết của nhân vật đó từ danh sách 'characters' vào prompt này. KHÔNG ĐƯỢC dùng tên.
KHÔNG CHỮ: Prompt phải mô tả bối cảnh không có bất kỳ chữ viết, văn bản, ký tự, hay biển báo nào.
STYLE: {style}."""
        },
        "videoPrompt": {
            "type": "string",
            "description": f"""Một prompt chi tiết, MỘT DÒNG, BẰNG TIẾNG ANH để tạo video {scene_duration} giây, phát triển TỪ ảnh tĩnh ('imagePrompt').
LOGIC: Bối cảnh, vật thể, và kiến trúc phải logic, chính xác và phù hợp với nhân vật, thời đại, và bối cảnh chung của câu chuyện.
PHẢI mô tả logic chuyển động liên tục (cử động nhân vật, tương tác môi trường, chuyển động camera).
NHẤT QUÁN: Nếu cảnh này có nhân vật, BẮT BUỘC phải sao chép (copy-paste) TOÀN BỘ mô tả chi tiết của nhân vật đó vào đây một lần nữa.
KHÔNG CHỮ: Prompt phải mô tả bối cảnh không có bất kỳ chữ viết, văn bản, ký tự, hay biển báo nào.
STYLE: {style}."""
        },
        "charactersInScene": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Danh sách TÊN CHÍNH XÁC của các nhân vật có trong cảnh này. (Ví dụ: ['Anna', 'Bob'])"
        }
    }
    # --- KẾT THÚC CẬP NHẬT ---

    scene_required_fields = ["sceneNumber", "scriptPortion", "imagePrompt", "videoPrompt", "charactersInScene"]

    if include_narration:
        scene_properties['narration'] = {
            "type": "string",
            "description": f"Lời dẫn của người tường thuật cho cảnh này, bằng ngôn ngữ {language}. ĐỂ TRỐNG nếu cảnh chỉ có lời thoại của nhân vật."
        }
        scene_required_fields.append("narration")

    # --- CẬP NHẬT (Xóa 'landscapes') ---
    schema = {
        'type': 'object',
        "properties": {
            # 'characters' vẫn giữ nguyên
            "characters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string",
                                        "description": "A highly detailed visual description of the character's appearance, in English. Include facial features, ethnicity, hair, body type, clothing, accessories, and demeanor for consistent image generation. Maximum 3 characters."},
                    },
                    "required": ["name", "description"]
                }
            },

            # --- 'landscapes' ĐÃ BỊ XÓA ---

            # 'scenes' vẫn giữ nguyên
            "scenes": {
                "type": "array",
                "description": f"Toàn bộ câu chuyện, được chia thành {num_scenes} cảnh tuần tự.",
                "items": {
                    "type": "object",
                    "properties": scene_properties,
                    "required": scene_required_fields
                }
            }
        },
        # Cập nhật 'required':
        "required": ["characters", "scenes"],
    }
    # --- KẾT THÚC CẬP NHẬT ---

    # --- ĐỊNH NGHĨA HƯỚNG DẪN (Instructions) ---

    characterDescriptionInstruction = """--- HƯỚNG DẪN TẠO NHÂN VẬT ---
For each character, provide a highly detailed visual description in English. This is critical for AI image generation. Include:
- Facial features (eye shape/color, nose, jawline) and ethnicity (appropriate for the story's setting).
- Hair (color, length, style).
- Body type (tall, slim, muscular).
- Clothing (specific type, style, colors).
- Key accessories or props.
- Overall demeanor (cheerful, grim)."""

    # --- landscapeDescriptionInstruction ĐÃ BỊ XÓA ---

    # --- CẬP NHẬT (Thêm QUY TẮC 2: LOGIC BỐI CẢNH) ---
    sceneGenerationInstruction = f"""--- HƯỚNG DẪN TẠO CẢNH (RẤT QUAN TRỌNG) ---
Bạn PHẢI chia câu chuyện thành {num_scenes} cảnh, mỗi cảnh {scene_duration} giây.
Với mỗi cảnh:
1.  Cung cấp `sceneNumber`, `scriptPortion`, `charactersInScene` (và `narration` nếu cần).
2.  Tạo `imagePrompt` (Tiếng Anh, 1 dòng).
3.  Tạo `videoPrompt` (Tiếng Anh, 1 dòng).

--- CÁC QUY TẮC BẮT BUỘC CHO PROMPT ---

QUY TẮC 1: (NHẤT QUÁN NHÂN VẬT)
- Đây là quy tắc quan trọng NHẤT.
- Đối với BẤT KỲ cảnh nào có chứa nhân vật (được liệt kê trong 'charactersInScene'):
- Bạn PHẢI tìm mô tả ('description') đầy đủ của nhân vật đó trong danh sách 'characters' mà BẠN TỰ TẠO RA.
- Bạn PHẢI sao chép (copy-paste) TOÀN BỘ mô tả đó, NGUYÊN VĂN, vào TRỰC TIẾP `imagePrompt` và `videoPrompt`.
- KHÔNG ĐƯỢC dùng tên (ví dụ: 'Sơn Tinh'). KHÔNG ĐƯỢC tóm tắt mô tả.
- VÍ DỤ SAI: 'Son Tinh stands on a mountain.'
- VÍ DỤ ĐÚNG: 'A tall, muscular ancient Vietnamese man with bronze skin, wearing a bronze armor plate and a helmet with feathers (description of Son Tinh) stands on a mountain.'

QUY TẮC 2: (LOGIC BỐI CẢNH)
- Bối cảnh, kiến trúc, công nghệ và các vật thể trong prompt (cả ảnh và video) PHẢI logic, chính xác về mặt lịch sử/văn hóa, và phù hợp với thời đại, bối cảnh chung của câu chuyện. 
- VÍ DỤ: Nếu là truyện "Sơn Tinh" (thời Vua Hùng), prompt KHÔNG ĐƯỢC chứa 'kiếm katana Nhật Bản', 'áo giáp hiệp sĩ châu Âu', 'điện thoại', hoặc 'tòa nhà bê tông'.

QUY TẮC 3: (KHÔNG CÓ VĂN BẢN)
- Cả `imagePrompt` và `videoPrompt` PHẢI yêu cầu một bối cảnh không có chữ.
- PHẢI thêm các cụm từ như "no text", "no words", "no writing", "text-free environment", "signs are visual gibberish" (ký tự vô nghĩa) vào prompt.

QUY TẮC 4: (LOGIC VIDEO 8 GIÂY)
- `videoPrompt` PHẢI mô tả một HÀNH ĐỘNG LIÊN TỤC trong 8 giây, phát triển từ `imagePrompt`.
- Mô tả rõ:
    - Chuyển động nhân vật (ví dụ: '...he raises his hand slowly, chanting a spell...')
    - Tương tác môi trường (ví dụ: '...as the wind blows his hair violently...')
    - Chuyển động camera (ví dụ: '...slow zoom in on his determined face...', '...camera pans left to follow the eagle...')
- Nếu `scriptPortion` có lời thoại (ví dụ: 'SƠN TINH: Ta sẽ thắng!'), `videoPrompt` PHẢI mô tả hành động đó (ví dụ: '...shouts "Ta sẽ thắng!" with a powerful voice...').
"""
    # --- KẾT THÚC CẬP NHẬT ---

    # --- TẠO PROMPT CHÍNH (Đã xóa landscapeDescriptionInstruction) ---

    if mode == "idea":
        prompt = f"""Bạn là một đạo diễn AI. Tạo một kế hoạch video hoàn chỉnh cho video {duration} giây.
Ý tưởng: "{idea}"
Phong cách: "{style}"
Ngôn ngữ kịch bản: {language}

Tuân thủ TUYỆT ĐỐI tất cả các hướng dẫn dưới đây để tạo ra JSON hoàn chỉnh.
Đặc biệt tuân thủ 4 QUY TẮC VÀNG trong 'HƯỚNG DẪN TẠO CẢNH'.

{characterDescriptionInstruction}
{sceneGenerationInstruction}
"""
    else:  # mode == GenerationMode.SCRIPT
        prompt = f"""Bạn là một nhà phân tích kịch bản AI. Phân tích kịch bản sau (ngôn ngữ: {language}) và chuyển nó thành kế hoạch video {duration} giây.
Phong cách: "{style}"

Kịch bản cung cấp:
'''
{script}
'''

Tuân thủ TUYỆT ĐỐI tất cả các hướng dẫn dưới đây để tạo ra JSON hoàn chỉnh.
Đặc biệt tuân thủ 4 QUY TẮC VÀNG trong 'HƯỚNG DẪN TẠO CẢNH'.

{characterDescriptionInstruction}
{sceneGenerationInstruction}
"""

    # --- Gọi API ---
    response = client.models.generate_content(
        # Nhắc lại: Nên dùng 'pro' cho các quy tắc phức tạp này
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfigDict({
            'response_mime_type': 'application/json',
            'response_json_schema': schema
        })
    )
    return response.parsed
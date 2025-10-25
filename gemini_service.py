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
                                        "description": "A highly detailed visual description of the character's appearance, in English. Ensure the character's facial features and ethnicity are appropriate for the story's geographical and cultural setting. Include details on facial features, hair, body type, clothing, accessories, and demeanor for consistent image generation"},
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

import json

from google import genai
from google.genai import types
from helper import get_config

from type import GenerationMode,Language

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
            "script": {"type": 'object', "description": f"""The full, coherent story script, in {language}."""},
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
        "required": ["script", "characters", "landscapes"]
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
        config={
            'response_mime_type': 'application/json',
            'response_json_schema': schema
        }
    )
    return response.text


# idea = suggest_idea("Truyền thuyết sơn tinh thuỷ tinh việt nam")
# cont = json.loads(generate_script_and_characters(idea=idea, style="3d animation", mode='idea'))

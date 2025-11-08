# app/utils/models.py
from dataclasses import dataclass, field
from typing import Literal, Optional, List
from enum import Enum

# --- Enums (Hợp nhất từ result_app.py) ---
class GenerationMode(Enum):
    IDEA = 'idea'
    SCRIPT = 'script'

# --- Type Aliases ---
AspectRatio = Literal['16:9', '9:16', '1:1']
Language = Literal['english', 'vietnamese', 'japanese', 'spanish'] # Thêm
File = bytes


# --- 2. Các Giao Diện Dữ Liệu (Dataclasses) ---

# Tương đương với: export interface Character
@dataclass
class Character:
    id: str
    name: str
    anchorID: str
    description: str
    refImage: Optional[File] = field(default=None)
    refImageUrl: Optional[str] = field(default=None)
    refImageBase64: Optional[str] = field(default=None)
    promptImage: Optional[str] = field(default=None)


# Tương đương với: export interface Landscape
@dataclass
class Landscape:
    id: str
    name: str
    description: str
    refImage: Optional[File] = field(default=None)
    refImageUrl: Optional[str] = field(default=None)
    refImageBase64: Optional[str] = field(default=None)


# Tương đương với: export interface Scene
@dataclass
class Scene:
    sceneNumber: int
    imagePrompt: str
    videoPrompt: str
    soundPrompt: str
    scriptPortion: str
    charactersInScene: List[str]
    landscapesInScene: List[str] # Dù không dùng nhưng vẫn giữ

    generatedImage: Optional[str] = field(default=None)
    generatedVideoUrl: Optional[str] = field(default=None)
    narration: Optional[str] = field(default=None)
    isGeneratingImage: Optional[bool] = field(default=None)
    isGeneratingVideo: Optional[bool] = field(default=None)
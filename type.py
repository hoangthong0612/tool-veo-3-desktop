from dataclasses import dataclass, field
from typing import Literal, Optional, List

# --- 1. Các Kiểu Kết Hợp Chuỗi (Type Aliases) ---
# Tương đương với: export type GenerationMode = 'idea' | 'script';
GenerationMode = Literal['idea', 'script']

# Tương đương với: export type AspectRatio = '16:9' | '9:16' | '1:1';
AspectRatio = Literal['16:9', '9:16', '1:1']

# Tương đương với: export type Language = 'en' | 'vi';
Language = Literal['english', 'vietnamese']

# Định nghĩa giả định cho kiểu File (có thể là bytes cho dữ liệu file)
File = bytes


# --- 2. Các Giao Diện Dữ Liệu (Dataclasses) ---

# Tương đương với: export interface Character
@dataclass
class Character:
    id: str
    name: str
    description: str
    # Các thuộc tính tùy chọn (optional) trong TypeScript được đặt là Optional[Type] 
    # và có default=None trong dataclasses
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
    scriptPortion: str
    # string[] trong TypeScript được chuyển thành List[str] trong Python
    charactersInScene: List[str]
    landscapesInScene: List[str]

    generatedImage: Optional[str] = field(default=None)  # base64 string
    generatedVideoUrl: Optional[str] = field(default=None)
    narration: Optional[str] = field(default=None)
    isGeneratingImage: Optional[bool] = field(default=None)
    isGeneratingVideo: Optional[bool] = field(default=None)
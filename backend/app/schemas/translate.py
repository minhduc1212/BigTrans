from pydantic import BaseModel, Field
from typing import List, Optional
from backend.app.engines.base import TranslationResult

class EngineInfo(BaseModel):
    id: str
    name: str
    available: bool = True
    supported_languages: List[str]

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to translate")
    source_lang: str = Field(default="auto", description="Source language code (e.g. 'auto', 'en', 'zh')")
    target_lang: str = Field(default="vi", description="Target language code (e.g. 'vi', 'en')")
    engines: List[str] = Field(..., min_length=1, description="List of translator engine IDs to use")

class TranslateResponse(BaseModel):
    results: List[TranslationResult]

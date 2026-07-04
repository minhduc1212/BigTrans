from abc import ABC, abstractmethod
from pydantic import BaseModel

class TranslationResult(BaseModel):
    engine_id: str
    engine_name: str
    translated_text: str | None
    detected_source_lang: str | None = None
    latency_ms: int
    success: bool
    error_message: str | None = None

class TranslatorEngine(ABC):
    engine_id: str
    display_name: str

    @abstractmethod
    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        """Translate text from source_lang to target_lang."""
        pass

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """List of ISO 639-1 language codes supported by this engine."""
        pass

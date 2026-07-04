import time
import asyncio
from deep_translator import GoogleTranslator
from backend.app.engines.base import TranslatorEngine, TranslationResult

class GooglePipEngine(TranslatorEngine):
    engine_id = "google_pip"
    display_name = "Google (via deep-translator)"

    def _map_lang(self, lang: str) -> str:
        mapping = {
            'auto': 'auto',
            'zh': 'zh-CN',
            'vi': 'vi',
            'en': 'en',
            'ja': 'ja',
            'ko': 'ko',
            'fr': 'fr',
            'de': 'de',
            'ru': 'ru',
            'es': 'es',
            'it': 'it'
        }
        return mapping.get(lang, lang)

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        start_time = time.time()
        source = self._map_lang(source_lang)
        target = self._map_lang(target_lang)
        
        try:
            def run_sync_translate():
                translator = GoogleTranslator(source=source, target=target)
                return translator.translate(text)

            translated_text = await asyncio.to_thread(run_sync_translate)
            latency = int((time.time() - start_time) * 1000)
            return TranslationResult(
                engine_id=self.engine_id,
                engine_name=self.display_name,
                translated_text=translated_text,
                latency_ms=latency,
                success=True
            )
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return TranslationResult(
                engine_id=self.engine_id,
                engine_name=self.display_name,
                translated_text=None,
                latency_ms=latency,
                success=False,
                error_message=str(e)
            )

    def supported_languages(self) -> list[str]:
        return ["auto", "vi", "zh", "en", "ja", "ko", "fr", "de", "ru", "es", "it"]

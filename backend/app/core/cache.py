import time
import hashlib
import threading
from typing import Dict, Optional, Tuple

class TranslationCache:
    """A simple thread-safe in-memory cache with TTL expiration."""
    def __init__(self):
        # Maps cache_key -> (translated_text, expiration_time, detected_source_lang)
        self._cache: Dict[str, Tuple[str, float, Optional[str]]] = {}
        self._lock = threading.Lock()

    def _make_key(self, text: str, source_lang: str, target_lang: str, engine_id: str) -> str:
        raw_key = f"{text}||{source_lang}||{target_lang}||{engine_id}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def get(self, text: str, source_lang: str, target_lang: str, engine_id: str) -> Optional[Tuple[str, Optional[str]]]:
        key = self._make_key(text, source_lang, target_lang, engine_id)
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                translated_text, expire_at, detected_lang = entry
                if expire_at > time.time():
                    return translated_text, detected_lang
                else:
                    # Clean up expired entry
                    del self._cache[key]
        return None

    def set(self, text: str, source_lang: str, target_lang: str, engine_id: str, translated_text: str, ttl_seconds: int, detected_lang: Optional[str] = None):
        key = self._make_key(text, source_lang, target_lang, engine_id)
        expire_at = time.time() + ttl_seconds
        with self._lock:
            self._cache[key] = (translated_text, expire_at, detected_lang)

translation_cache = TranslationCache()

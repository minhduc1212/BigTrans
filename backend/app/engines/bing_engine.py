import re
import json
import time
import httpx
import asyncio
from backend.app.engines.base import TranslatorEngine, TranslationResult

class BingEngine(TranslatorEngine):
    engine_id = "bing"
    display_name = "Bing Microsoft Translator"

    def __init__(self):
        self.ig = None
        self.iid = None
        self.key = None
        self.token = None
        self.last_fetch_time = 0
        self.cache_ttl = 600  # 10 minutes cache TTL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.bing.com/translator",
        }
        self.cookies = {}
        self._async_lock = None

    @property
    def lock(self):
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    def _map_lang(self, lang: str) -> str:
        mapping = {
            'auto': 'auto-detect',
            'zh': 'zh-Hans',
            'vi': 'vi',
            'en': 'en',
            'ja': 'ja',
            'ko': 'ko',
            'fr': 'fr',
            'de': 'de',
            'ru': 'ru'
        }
        return mapping.get(lang, lang)

    async def _fetch_tokens(self, client: httpx.AsyncClient):
        """Fetch current session parameters (IG, IID, key, token) from Bing Translator homepage."""
        url = "https://www.bing.com/translator"
        response = await client.get(url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch Bing Translator page: Status {response.status_code}")
            
        html = response.text
        
        # Save cookies back to store
        self.cookies = {name: val for name, val in client.cookies.items()}
        
        # Extract IG
        ig_match = (
            re.search(r'IG:"([^"]+)"', html) or 
            re.search(r'ig":"([^"]+)"', html) or 
            re.search(r'_G\.IG\s*=\s*"([^"]+)"', html)
        )
        if not ig_match:
            raise Exception("Failed to extract IG from Bing Translator page")
        self.ig = ig_match.group(1)
        
        # Extract IID
        iid_match = re.search(r'data-iid="([^"]+)"', html) or re.search(r'iid="([^"]+)"', html)
        if not iid_match:
            raise Exception("Failed to extract IID from Bing Translator page")
        self.iid = iid_match.group(1)
        
        # Extract Key & Token from params_AbusePreventionHelper
        abuse_match = re.search(r'params_AbusePreventionHelper\s*=\s*\[([^\]]+)\]', html)
        if not abuse_match:
            raise Exception("Failed to extract params_AbusePreventionHelper from Bing Translator page")
            
        try:
            parts = [p.strip().strip('"') for p in abuse_match.group(1).split(',')]
            if len(parts) < 2:
                raise ValueError("Abuse prevention helper array too short")
            self.key = parts[0]
            self.token = parts[1]
        except Exception as e:
            raise Exception(f"Error parsing AbusePreventionHelper parameters: {e}")
            
        self.last_fetch_time = time.time()

    async def _do_post_translate(self, client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
        translate_url = f"https://www.bing.com/ttranslatev3?isVertical=1&&IG={self.ig}&IID={self.iid}&SFX=1"
        
        payload = {
            "fromLang": source,
            "to": target,
            "text": text,
            "key": self.key,
            "token": self.token
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = await client.post(
            translate_url, 
            data=payload, 
            headers=headers,
            timeout=10
        )
        if response.status_code != 200:
            raise Exception(f"Translation POST request failed: Status {response.status_code}")
            
        try:
            result = response.json()
            translated_text = result[0]['translations'][0]['text']
            return translated_text
        except (IndexError, KeyError, ValueError) as e:
            raise Exception(f"Failed to parse translation response JSON: {e}. Raw response: {response.text}")

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        start_time = time.time()
        source = self._map_lang(source_lang)
        target = self._map_lang(target_lang)
        
        try:
            async with httpx.AsyncClient(headers=self.headers, cookies=self.cookies, follow_redirects=True) as client:
                async with self.lock:
                    current_time = time.time()
                    if (not self.ig or 
                        not self.iid or 
                        not self.key or 
                        not self.token or 
                        (current_time - self.last_fetch_time) > self.cache_ttl):
                        await self._fetch_tokens(client)
                
                try:
                    translated_text = await self._do_post_translate(client, text, source, target)
                except Exception:
                    # Retry once with refreshed tokens
                    async with self.lock:
                        if (time.time() - self.last_fetch_time) > 5:
                            await self._fetch_tokens(client)
                    translated_text = await self._do_post_translate(client, text, source, target)
                
                # Sync back any cookies changed during the translation request
                self.cookies = {name: val for name, val in client.cookies.items()}
                
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

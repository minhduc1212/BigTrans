import re
import json
import time
import httpx
import asyncio
from backend.app.engines.base import TranslatorEngine, TranslationResult

class GoogleEngine(TranslatorEngine):
    engine_id = "google"
    display_name = "Google Translate"

    def __init__(self):
        self.host_url = "https://translate.google.com"
        self.api_url = f"{self.host_url}/_/TranslateWebserverUi/data/batchexecute"
        self.rpcid = "MkEWBc"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Referer": "https://translate.google.com/",
            "Origin": "https://translate.google.com"
        }
        self.bl = None
        self.fsid = None
        self.cookies = {}
        self._async_lock = None

    @property
    def lock(self):
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    def _map_lang(self, lang: str) -> str:
        mapping = {
            'zh': 'zh-CN',
            'auto': 'auto',
            'vi': 'vi',
            'en': 'en',
            'ja': 'ja',
            'ko': 'ko',
            'fr': 'fr',
            'de': 'de',
            'ru': 'ru'
        }
        return mapping.get(lang, lang)

    async def _initialize_session(self, client: httpx.AsyncClient):
        """Fetch translate home page to get dynamic bl and f.sid parameters."""
        try:
            r = await client.get(self.host_url, headers=self.headers, timeout=10)
            r.raise_for_status()
            
            # Extract bl and f.sid from WIZ_global_data
            match = re.search(r'window.WIZ_global_data\s*=\s*(.*?);</script>', r.text)
            if not match:
                raise Exception("Failed to extract WIZ_global_data")
                
            wiz_data = json.loads(match.group(1))
            self.bl = wiz_data.get("cfb2h")
            self.fsid = wiz_data.get("FdrFJe")
            
            # Save cookies
            self.cookies = {name: val for name, val in r.cookies.items()}
        except Exception as e:
            raise Exception(f"Session initialization failed: {e}")

    async def _do_translate(self, client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
        inner_payload = [[text, source, target, True], [1]]
        inner_payload_str = json.dumps(inner_payload, ensure_ascii=False)
        outer_payload = [[[self.rpcid, inner_payload_str, None, "generic"]]]
        outer_payload_str = json.dumps(outer_payload, ensure_ascii=False)
        
        data = {
            "f.req": outer_payload_str
        }
        
        params = {
            "rpcids": self.rpcid,
            "source-path": "/",
            "f.sid": self.fsid,
            "bl": self.bl,
            "hl": target,
            "soc-app": "1",
            "soc-platform": "1",
            "soc-device": "1",
            "rt": "c"
        }
        
        r = await client.post(
            self.api_url, 
            headers=self.headers, 
            params=params, 
            data=data, 
            cookies=self.cookies,
            timeout=10
        )
        r.raise_for_status()
        
        resp_text = r.text
        if resp_text.startswith(")]}'"):
            resp_text = resp_text[4:].strip()
            
        lines = resp_text.splitlines()
        payload_line = None
        for line in lines:
            if self.rpcid in line:
                payload_line = line
                break
                
        if not payload_line:
            raise Exception("No translation payload found in response")
            
        json_data = json.loads(payload_line)
        inner_json_str = json_data[0][2]
        inner_data = json.loads(inner_json_str)
        
        parts = inner_data[1][0][0][5] or inner_data[1][0]
        translated_text = ' '.join([x[0] for x in parts if x[0]])
        return translated_text

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        start_time = time.time()
        source = self._map_lang(source_lang)
        target = self._map_lang(target_lang)
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                async with self.lock:
                    if not self.bl or not self.fsid:
                        await self._initialize_session(client)
                
                try:
                    translated_text = await self._do_translate(client, text, source, target)
                except Exception:
                    # Retry once with session refresh
                    async with self.lock:
                        await self._initialize_session(client)
                    translated_text = await self._do_translate(client, text, source, target)
                
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

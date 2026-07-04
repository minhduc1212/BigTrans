import time
import random
import uuid
import json
import httpx
from backend.app.engines.base import TranslatorEngine, TranslationResult

class DeeplEngine(TranslatorEngine):
    engine_id = "deepl"
    display_name = "DeepL Translator"

    def __init__(self, method='oneshot'):
        self.method = method
        self.instance_id = str(uuid.uuid4())
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.cookies = {}

    def _map_lang(self, lang: str, is_target: bool = True) -> str:
        lang_upper = lang.upper()
        if lang_upper == 'AUTO':
            return 'auto'
        if lang_upper == 'ZH':
            return 'zh-Hans' if is_target else 'zh'
        if lang_upper == 'EN':
            return 'en-US' if is_target else 'en'
        if lang_upper == 'PT':
            return 'pt-BR' if is_target else 'pt'
            
        mapping = {
            'AR': 'ar', 'BG': 'bg', 'CS': 'cs', 'DA': 'da', 'DE': 'de', 'EL': 'el',
            'EN-GB': 'en-GB', 'EN-US': 'en-US',
            'ES': 'es', 'ES-419': 'es-419', 'ET': 'et', 'FI': 'fi', 'FR': 'fr',
            'HE': 'he', 'HU': 'hu', 'ID': 'id', 'IT': 'it', 'JA': 'ja', 'KO': 'ko',
            'LT': 'lt', 'LV': 'lv', 'NB': 'nb', 'NL': 'nl', 'PL': 'pl',
            'PT-BR': 'pt-BR', 'PT-PT': 'pt-PT',
            'RO': 'ro', 'RU': 'ru', 'SK': 'sk', 'SL': 'sl', 'SV': 'sv',
            'TR': 'tr', 'UK': 'uk', 'VI': 'vi',
            'ZH-HANS': 'zh-Hans', 'ZH-HANT': 'zh-Hant'
        }
        return mapping.get(lang_upper, lang.lower())

    async def _warmup_cookies(self, client: httpx.AsyncClient):
        try:
            r = await client.get("https://www.deepl.com/translator", headers=self.headers, timeout=5)
            self.cookies = {name: val for name, val in r.cookies.items()}
        except Exception:
            pass

    async def _translate_oneshot(self, client: httpx.AsyncClient, text: str, source_lang: str, target_lang: str) -> str:
        url = "https://oneshot-free.www.deepl.com/v1/translate"
        target = self._map_lang(target_lang, is_target=True)
        source = self._map_lang(source_lang, is_target=False)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": "None",
            "Origin": "chrome-extension://cofdbpoegempjloogbagkncekinflcnj",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        payload = {
            "text": [text],
            "target_lang": target,
            "usage_type": "Translate",
            "app_information": {
                "os": "brex_windows",
                "os_version": "brex_chrome_120.0.0.0",
                "app_version": "1.86.0",
                "app_build": "chrome_web_store",
                "instance_id": self.instance_id
            }
        }
        
        if source and source != 'auto':
            payload["source_lang"] = source
            
        r = await client.post(url, headers=headers, json=payload, cookies=self.cookies, timeout=10)
        if r.status_code == 429:
            raise Exception("Rate limited (429) by DeepL oneshot endpoint")
        elif r.status_code != 200:
            raise Exception(f"HTTP status {r.status_code}: {r.text}")
            
        res = r.json()
        translations = res.get("translations", [])
        if not translations:
            raise Exception("No translations returned")
            
        return translations[0].get("text", "")

    async def _translate_jsonrpc(self, client: httpx.AsyncClient, text: str, source_lang: str, target_lang: str) -> str:
        url = "https://www2.deepl.com/jsonrpc"
        target = self._map_lang(target_lang, is_target=True).upper()
        source = self._map_lang(source_lang, is_target=False).upper()
        if source == 'AUTO':
            source = 'AUTO'
            
        i_count = text.count('i') + 1
        ts = int(time.time() * 1000)
        fake_timestamp = ts - (ts % i_count) + i_count
        request_id = random.randint(100000, 999999) * 100
        
        payload = {
            "jsonrpc": "2.0",
            "method": "LMT_handle_texts",
            "params": {
                "texts": [
                    {
                        "text": text,
                        "requestAlternatives": 3
                    }
                ],
                "splitting": "newlines",
                "lang": {
                    "source_lang_user_selected": source,
                    "target_lang": target
                },
                "timestamp": fake_timestamp,
                "commonJobParams": {
                    "wasSpoken": False,
                    "transitivity": "all"
                }
            },
            "id": request_id
        }
        
        req_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        if (request_id + 3) % 13 == 0 or (request_id + 5) % 29 == 0:
            req_str = req_str.replace('"method":"LMT_handle_texts"', '"method" : "LMT_handle_texts"')
        else:
            req_str = req_str.replace('"method":"LMT_handle_texts"', '"method": "LMT_handle_texts"')
            
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://www.deepl.com",
            "Referer": "https://www.deepl.com/"
        }
        
        r = await client.post(url, headers=headers, content=req_str.encode('utf-8'), cookies=self.cookies, timeout=10)
        if r.status_code == 429:
            raise Exception("Rate limited (429) by DeepL JSON-RPC endpoint")
        elif r.status_code != 200:
            raise Exception(f"HTTP status {r.status_code}: {r.text}")
            
        res = r.json()
        if "error" in res:
            error_msg = res["error"].get("message", "Unknown error")
            raise Exception(f"DeepL API Error: {error_msg}")
            
        results = res.get("result", {}).get("texts", [])
        if not results:
            raise Exception("No translations returned")
            
        return results[0].get("text", "")

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                if not self.cookies:
                    await self._warmup_cookies(client)
                
                translated_text = None
                if self.method == 'oneshot':
                    try:
                        translated_text = await self._translate_oneshot(client, text, source_lang, target_lang)
                    except Exception as e:
                        # Fallback
                        translated_text = await self._translate_jsonrpc(client, text, source_lang, target_lang)
                else:
                    try:
                        translated_text = await self._translate_jsonrpc(client, text, source_lang, target_lang)
                    except Exception as e:
                        # Fallback
                        translated_text = await self._translate_oneshot(client, text, source_lang, target_lang)
                
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

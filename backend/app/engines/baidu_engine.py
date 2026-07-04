import os
import sys
import time
import json
import asyncio
import requests
from playwright.sync_api import sync_playwright
from backend.app.engines.base import TranslatorEngine, TranslationResult

# Shared User-Agent to match token generation and requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Cache path for Baidu translate token (inside the engines directory)
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".baidu_token_cache.json")

def clean_punctuation(text: str) -> str:
    """Replaces Chinese punctuation with English equivalents for standard formatting."""
    text = text.replace('。', '.')
    text = text.replace('，', ',')
    text = text.replace('“', '"')
    text = text.replace('”', '"')
    text = text.replace('‘', "'")
    text = text.replace('’', "'")
    text = text.replace('；', ';')
    return text

def get_tokens_via_playwright():
    """
    Launch a headless browser using Playwright to extract a valid
    Acs-Token and Cookie from the fanyi.baidu.com AIT translator page.
    """
    try:
        with sync_playwright() as p:
            # Disable automation flags to avoid detection
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800}
            )
            # Inject script to hide webdriver property
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()
            
            # Block media/analytics
            def block_resources(route):
                url = route.request.url
                if any(x in url for x in [".png", ".jpg", ".jpeg", ".gif", "google-analytics", "hm.baidu.com", "fclog.baidu.com"]):
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", block_resources)
            
            captured_token = None
            
            # Request interceptor to catch the Acs-Token header
            def handle_request(request):
                nonlocal captured_token
                if "translateIncognitoAi" in request.url:
                    headers = request.headers
                    for h_name, h_val in headers.items():
                        if h_name.lower() == 'acs-token':
                            captured_token = h_val

            page.on("request", handle_request)
            
            # Navigate to translation page
            page.goto("https://fanyi.baidu.com/mtpe-individual/transText#/", wait_until="load")
            
            # Dismiss popup modals
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
            
            # Target the contenteditable input element
            editable_selector = "div[contenteditable='true']"
            page.wait_for_selector(editable_selector, timeout=10000)
            
            # Click and focus
            try:
                page.click(editable_selector, timeout=5000)
            except Exception:
                page.click(editable_selector, force=True)
                
            page.focus(editable_selector)
            page.wait_for_timeout(200)
            
            # Type text to trigger translation request
            page.keyboard.type("我加载了神秘学面板")
            
            # Wait for request to fire
            page.wait_for_timeout(4000)
            
            # Extract cookies
            cookies = context.cookies()
            cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            browser.close()
            
            if not captured_token:
                raise Exception("Failed to intercept translate request to capture Acs-Token.")
                
            return captured_token, cookies_str
    except Exception as e:
        raise Exception(f"Playwright token retrieval failed: {e}")

class BaiduAITranslator:
    """
    Baidu AI Translator using fanyi.baidu.com AIT Translate API (Incognito mode).
    """
    def __init__(self, from_lang='zh', to_lang='vie'):
        self.url = "https://fanyi.baidu.com/ait/text/translate"
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.session = requests.Session()
        self.acs_token = None
        self.cookie = None
        self.load_cache()

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    self.acs_token = cache.get("acs_token")
                    self.cookie = cache.get("cookie")
            except Exception:
                pass

    def save_cache(self):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"acs_token": self.acs_token, "cookie": self.cookie}, f)
        except Exception:
            pass

    def refresh_tokens(self):
        token, cookie = get_tokens_via_playwright()
        self.acs_token = token
        self.cookie = cookie
        self.save_cache()

    def translate(self, query: str, retry_on_error: bool = True) -> str:
        if not query:
            return ""

        if not self.acs_token or not self.cookie:
            self.refresh_tokens()

        try:
            return self._do_translate(query)
        except Exception as e:
            if retry_on_error:
                self.refresh_tokens()
                return self._do_translate(query)
            else:
                raise e

    def _do_translate(self, query: str) -> str:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "Origin": "https://fanyi.baidu.com",
            "Referer": "https://fanyi.baidu.com/mtpe-individual/transText#/",
            "Acs-Token": self.acs_token,
            "Cookie": self.cookie,
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }

        payload = {
            "query": query,
            "from": self.from_lang,
            "to": self.to_lang,
            "reference": "",
            "corpusIds": [],
            "qcSettings": ["1","2","3","4","5","6","7","8","9","10","11"],
            "domain": "common"
        }

        response = self.session.post(self.url, json=payload, headers=headers, stream=True)
        if response.status_code != 200:
            raise Exception(f"HTTP Connection Failed: {response.status_code}")

        translated_paragraphs = {}

        for line in response.iter_lines():
            if not line:
                continue
            
            decoded_line = line.decode('utf-8').strip()
            
            if decoded_line.startswith("data:"):
                data_json = decoded_line[5:].strip()
                try:
                    data = json.loads(data_json)
                except json.JSONDecodeError:
                    continue

                errno = data.get("errno", 0)
                if errno != 0:
                    errmsg = data.get("errmsg", "Unknown error")
                    raise Exception(f"Baidu Translate API Error {errno}: {errmsg}")

                event_data = data.get("data")
                if not event_data:
                    continue

                event_name = event_data.get("event")

                if event_name in ("Translating", "TranslationSucceed"):
                    translation_list = event_data.get("list", [])
                    for item in translation_list:
                        para_idx = item.get("paraIdx", 0)
                        dst_text = item.get("dst", "")
                        translated_paragraphs[para_idx] = dst_text

        sorted_paras = [translated_paragraphs[idx] for idx in sorted(translated_paragraphs.keys())]
        final_translation = "".join(sorted_paras)
        return final_translation

class BaiduEngine(TranslatorEngine):
    engine_id = "baidu"
    display_name = "Baidu Translate"

    def _map_lang(self, lang: str) -> str:
        mapping = {
            'auto': 'auto',
            'zh': 'zh',
            'vi': 'vie',
            'en': 'en',
            'ja': 'jp',
            'ko': 'kor',
            'fr': 'fra',
            'de': 'de',
            'ru': 'ru',
            'es': 'spa',
            'it': 'it'
        }
        return mapping.get(lang, lang)

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        start_time = time.time()
        source = self._map_lang(source_lang)
        target = self._map_lang(target_lang)
        
        try:
            def run_sync_translate():
                translator = BaiduAITranslator(from_lang=source, to_lang=target)
                cleaned = clean_punctuation(text)
                return translator.translate(cleaned)

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

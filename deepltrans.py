import sys
import time
import random
import uuid
import json
import requests

# Ensure UTF-8 console output for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class DeeplTranslator:
    """
    Custom DeepL Translator reverse engineering the DeepL APIs.
    Supports both:
    1. The newer Chrome Extension stateless "oneshot" API (highly recommended and robust).
    2. The classic "jsonrpc" API with timestamp obfuscation and formatting tricks.
    
    Automatically falls back to the other method if one fails or encounters rate limits.
    """
    def __init__(self, source='auto', target='vi', method='oneshot'):
        self.source = source
        self.target = target
        self.method = method
        self.session = requests.Session()
        
        # Keep a persistent instance ID for the oneshot API
        self.instance_id = str(uuid.uuid4())
        
        # Seed cookies for the oneshot API (best-effort)
        self._warmup_cookies()
        
    def _map_lang(self, lang, is_target=True):
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

    def _warmup_cookies(self):
        """Warm up the cookie jar and establish a session by visiting DeepL translator home page."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            self.session.get("https://www.deepl.com/translator", headers=headers, timeout=5)
        except Exception:
            pass

    def translate(self, text):
        if not text:
            return ""
            
        if self.method == 'oneshot':
            try:
                return self._translate_oneshot(text)
            except Exception as e:
                print(f"oneshot method failed ({e}). Falling back to jsonrpc...", file=sys.stderr)
                try:
                    return self._translate_jsonrpc(text)
                except Exception as e2:
                    raise Exception(f"Translation failed: {e2}")
        else:
            try:
                return self._translate_jsonrpc(text)
            except Exception as e:
                print(f"jsonrpc method failed ({e}). Falling back to oneshot...", file=sys.stderr)
                try:
                    return self._translate_oneshot(text)
                except Exception as e2:
                    raise Exception(f"Translation failed: {e2}")

    def _translate_oneshot(self, text):
        """Translate using the stateless Chrome Extension oneshot API."""
        url = "https://oneshot-free.www.deepl.com/v1/translate"
        target_lang = self._map_lang(self.target, is_target=True)
        source_lang = self._map_lang(self.source, is_target=False)
        
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
            "target_lang": target_lang,
            "usage_type": "Translate",
            "app_information": {
                "os": "brex_windows",
                "os_version": "brex_chrome_120.0.0.0",
                "app_version": "1.86.0",
                "app_build": "chrome_web_store",
                "instance_id": self.instance_id
            }
        }
        
        if source_lang and source_lang != 'auto':
            payload["source_lang"] = source_lang
            
        r = self.session.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 429:
            raise Exception("Rate limited (429) by DeepL oneshot endpoint")
        elif r.status_code != 200:
            raise Exception(f"HTTP status {r.status_code}: {r.text}")
            
        res = r.json()
        translations = res.get("translations", [])
        if not translations:
            raise Exception("No translations returned")
            
        return translations[0].get("text", "")

    def _translate_jsonrpc(self, text):
        """Translate using the classic JSON-RPC API with timestamp and format obfuscation."""
        url = "https://www2.deepl.com/jsonrpc"
        target_lang = self._map_lang(self.target, is_target=True).upper()
        source_lang = self._map_lang(self.source, is_target=False).upper()
        if source_lang == 'AUTO':
            source_lang = 'AUTO'
            
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
                    "source_lang_user_selected": source_lang,
                    "target_lang": target_lang
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
        
        r = self.session.post(url, headers=headers, data=req_str.encode('utf-8'), timeout=10)
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

if __name__ == '__main__':
    # Initialise translator (default: auto to vi)
    translator = DeeplTranslator(source='auto', target='vi')
    
    text = "The protagonist suddenly transmigrated into a cultivation world."
    print(f"Original text: {text}")
    
    translated_text = translator.translate(text)
    print(f"Translated text: {translated_text}")

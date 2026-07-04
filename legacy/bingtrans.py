import sys
import re
import time
import requests
import json

# Ensure UTF-8 console output for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class BingTranslator:
    def __init__(self, source='auto', target='vi'):
        self.source = self._map_lang(source)
        self.target = self._map_lang(target)
        self.session = requests.Session()
        
        # Token cache
        self.ig = None
        self.iid = None
        self.key = None
        self.token = None
        self.last_fetch_time = 0
        self.cache_ttl = 600  # 10 minutes cache TTL
        
        # Headers mimicking a standard browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.bing.com/translator",
        }
        self.session.headers.update(self.headers)
        
    def _map_lang(self, lang):
        mapping = {
            'auto': 'auto-detect',
            'zh-CN': 'zh-Hans',
            'zh-TW': 'zh-Hant',
        }
        return mapping.get(lang, lang)

    def _fetch_tokens(self):
        """Fetch current session parameters (IG, IID, key, token) from Bing Translator homepage."""
        url = "https://www.bing.com/translator"
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch Bing Translator page: Status {response.status_code}")
            
        html = response.text
        
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

    def translate(self, text):
        """Translate the given text."""
        if not text:
            return ""
            
        # Check cache validity
        current_time = time.time()
        if (not self.ig or 
            not self.iid or 
            not self.key or 
            not self.token or 
            (current_time - self.last_fetch_time) > self.cache_ttl):
            self._fetch_tokens()
            
        # Try to translate
        try:
            return self._do_post_translate(text)
        except Exception as e:
            # If failed, clear cache, fetch new tokens, and try once more
            print(f"Translation failed ({e}). Retrying with new tokens...", file=sys.stderr)
            self._fetch_tokens()
            return self._do_post_translate(text)

    def _do_post_translate(self, text):
        translate_url = f"https://www.bing.com/ttranslatev3?isVertical=1&&IG={self.ig}&IID={self.iid}&SFX=1"
        
        payload = {
            "fromLang": self.source,
            "to": self.target,
            "text": text,
            "key": self.key,
            "token": self.token
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = self.session.post(translate_url, data=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Translation POST request failed: Status {response.status_code}")
            
        try:
            result = response.json()
            # The structure is: [{"translations": [{"text": "...", "to": "..."}], ...}]
            translated_text = result[0]['translations'][0]['text']
            return translated_text
        except (IndexError, KeyError, ValueError) as e:
            raise Exception(f"Failed to parse translation response JSON: {e}. Raw response: {response.text}")

if __name__ == '__main__':
    # Initialise translator (default: auto to vi)
    translator = BingTranslator(source='auto', target='vi')
    
    text = "The protagonist suddenly transmigrated into a cultivation world."
    print(f"Original text: {text}")
    
    translated_text = translator.translate(text)
    print(f"Translated text: {translated_text}")

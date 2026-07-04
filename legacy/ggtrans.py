import sys
import re
import json
import requests

# Ensure UTF-8 console output for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class GoogleTranslator:
    """
    Custom Google Translator using Google Translate's public RPC batchexecute endpoint.
    Automatically initializes the session, extracts WIZ_global_data tokens (bl, f.sid),
    and executes requests using the requests library.
    """
    def __init__(self, source='auto', target='vi'):
        self.source = self._map_lang(source)
        self.target = self._map_lang(target)
        self.session = requests.Session()
        self.host_url = "https://translate.google.com"
        self.api_url = f"{self.host_url}/_/TranslateWebserverUi/data/batchexecute"
        self.rpcid = "MkEWBc"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Referer": "https://translate.google.com/",
            "Origin": "https://translate.google.com"
        }
        
        # Session state
        self.bl = None
        self.fsid = None
        
    def _map_lang(self, lang):
        mapping = {
            'zh': 'zh-CN',
            'auto': 'auto',
            'vi': 'vi'
        }
        return mapping.get(lang, lang)
        
    def _initialize_session(self):
        """Fetch translate home page to get dynamic bl and f.sid parameters."""
        try:
            r = self.session.get(self.host_url, headers=self.headers, timeout=10)
            r.raise_for_status()
            
            # Extract bl and f.sid from WIZ_global_data
            match = re.search(r'window.WIZ_global_data\s*=\s*(.*?);</script>', r.text)
            if not match:
                raise Exception("Failed to extract WIZ_global_data")
                
            wiz_data = json.loads(match.group(1))
            self.bl = wiz_data.get("cfb2h")
            self.fsid = wiz_data.get("FdrFJe")
        except Exception as e:
            raise Exception(f"Session initialization failed: {e}")

    def translate(self, text):
        if not text:
            return ""
            
        # Initialize session parameters if not loaded
        if not self.bl or not self.fsid:
            self._initialize_session()
            
        try:
            return self._do_translate(text)
        except Exception as e:
            # Retry once with a refreshed session on failure
            print(f"Translation failed ({e}). Refreshing session...", file=sys.stderr)
            self._initialize_session()
            return self._do_translate(text)

    def _do_translate(self, text):
        inner_payload = [[text, self.source, self.target, True], [1]]
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
            "hl": self.target,
            "soc-app": "1",
            "soc-platform": "1",
            "soc-device": "1",
            "rt": "c"
        }
        
        r = self.session.post(self.api_url, headers=self.headers, params=params, data=data, timeout=10)
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

if __name__ == '__main__':
    # Initialise translator (default: auto to vi)
    translator = GoogleTranslator(source='auto', target='vi')
    
    text = "The protagonist suddenly transmigrated into a cultivation world."
    print(f"Original text: {text}")
    
    translated_text = translator.translate(text)
    print(f"Translated text: {translated_text}")

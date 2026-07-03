import os
import sys
import json
import time
import requests
from playwright.sync_api import sync_playwright

# Ensure UTF-8 console output for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Shared User-Agent to match token generation and requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Cache path for Baidu translate token
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".baidu_token_cache.json")

def get_tokens_via_playwright():
    """
    Launch a headless browser using Playwright to extract a valid
    Acs-Token and Cookie from the fanyi.baidu.com AIT translator page.
    """
    print("Launching headless browser via Playwright to refresh Baidu token...", file=sys.stderr)
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
            
            # Block media/analytics, keep CSS so layout doesn't trigger CAPTCHA
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
            
            # Dismiss popup modals (like Document Translation Pro announcement)
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
    It automatically launches Playwright to fetch and refresh cookies & tokens if they expire.
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
        """Load token and cookie from cache file if it exists."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    self.acs_token = cache.get("acs_token")
                    self.cookie = cache.get("cookie")
            except Exception:
                pass

    def save_cache(self):
        """Save token and cookie to cache file."""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"acs_token": self.acs_token, "cookie": self.cookie}, f)
        except Exception:
            pass

    def refresh_tokens(self):
        """Refresh token and cookies via Playwright."""
        token, cookie = get_tokens_via_playwright()
        self.acs_token = token
        self.cookie = cookie
        self.save_cache()

    def translate(self, query: str, stream: bool = False, retry_on_error: bool = True) -> str:
        """
        Translate the input query. Automatically retries with refreshed tokens on failure.
        """
        if not query:
            return ""

        # Fetch tokens if they aren't loaded
        if not self.acs_token or not self.cookie:
            print("No cached tokens found. Fetching via Playwright...", file=sys.stderr)
            self.refresh_tokens()

        try:
            return self._do_translate(query, stream)
        except Exception as e:
            if retry_on_error:
                print(f"Translation failed ({e}). Refreshing tokens and retrying...", file=sys.stderr)
                self.refresh_tokens()
                return self._do_translate(query, stream)
            else:
                raise e

    def _do_translate(self, query: str, stream: bool) -> str:
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

                # Print intermediate stream to console if enabled
                if event_name == "Intermediate" and stream:
                    word_list = event_data.get("list", [])
                    for word in word_list:
                        dst_chunk = word.get("dst", "")
                        sys.stdout.write(dst_chunk)
                        sys.stdout.flush()

                # Get final segment translation
                elif event_name in ("Translating", "TranslationSucceed"):
                    translation_list = event_data.get("list", [])
                    for item in translation_list:
                        para_idx = item.get("paraIdx", 0)
                        dst_text = item.get("dst", "")
                        translated_paragraphs[para_idx] = dst_text

        if stream:
            print()

        sorted_paras = [translated_paragraphs[idx] for idx in sorted(translated_paragraphs.keys())]
        final_translation = "".join(sorted_paras)
        return final_translation


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


def translate_file(input_path: str, output_path: str):
    """
    Reads lines from an input file, translates them, and writes to an output file.
    """
    if not os.path.exists(input_path):
        print(f"Input file '{input_path}' not found.", file=sys.stderr)
        return

    print(f"Reading from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Initialize translator
    translator = BaiduAITranslator(from_lang='zh', to_lang='vie')
    translated_content = []

    print(f"Translating {len(lines)} lines...")
    for idx, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            translated_content.append("")
            continue
            
        cleaned_line = clean_punctuation(line)
        print(f"[{idx}/{len(lines)}] Translating: {cleaned_line[:30]}...")
        try:
            # We translate each paragraph/line
            translated_line = translator.translate(cleaned_line)
            print(f" -> Result: {translated_line}")
            translated_content.append(translated_line)
        except Exception as e:
            print(f" -> ERROR: {e}", file=sys.stderr)
            translated_content.append(f"[ERROR: {e}]")

    print(f"Writing results to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for trans_line in translated_content:
            f.write(trans_line + '\n')
    print("Done!")


if __name__ == '__main__':
    # If file arguments are given, run file translation. Otherwise run interactive translation.
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "result.txt"
        translate_file(input_file, output_file)
    else:
        # Check if local test.txt exists, translate it to result.txt if it does
        if os.path.exists("test.txt"):
            translate_file("test.txt", "result.txt")
        else:
            # Test default translation
            translator = BaiduAITranslator(from_lang='zh', to_lang='vie')
            test_query = "我加载了神秘学面板"
            print(f"Test Query: {test_query}")
            result = translator.translate(test_query)
            print(f"Translation: {result}")

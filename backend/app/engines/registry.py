from backend.app.engines.google_engine import GoogleEngine
from backend.app.engines.bing_engine import BingEngine
from backend.app.engines.deepl_engine import DeeplEngine
from backend.app.engines.baidu_engine import BaiduEngine
from backend.app.engines.google_pip_engine import GooglePipEngine
from backend.app.engines.sogou_engine import SogouEngine
from backend.app.engines.youdao_engine import YoudaoEngine
from backend.app.engines.base import TranslatorEngine

ENGINE_REGISTRY: dict[str, TranslatorEngine] = {
    "google": GoogleEngine(),
    "google_pip": GooglePipEngine(),
    "bing": BingEngine(),
    "deepl": DeeplEngine(),
    "baidu": BaiduEngine(),
    "sogou": SogouEngine(),
    "youdao": YoudaoEngine(),
}

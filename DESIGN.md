# DESIGN.md — Gibsnart

> Tài liệu thiết kế kỹ thuật cho **Gibsnart** — website dịch thuật hỗ trợ nhiều engine dịch (Bing, Google, Baidu, ...) chạy song song để người dùng so sánh kết quả.
> Đây là bản mở rộng từ ý tưởng gốc, kèm giả định (assumption) được đánh dấu rõ để bạn điều chỉnh.

---

## 1. Idea

**Tên sản phẩm:** Gibsnart

**Vấn đề giải quyết:** Mỗi công cụ dịch (Google, Bing, Baidu, DeepL...) có điểm mạnh/yếu khác nhau tùy cặp ngôn ngữ và loại văn bản. Người dùng hiện phải mở nhiều tab, dịch riêng lẻ từng nơi rồi tự so sánh. Gibsnart gom tất cả vào **1 giao diện duy nhất**: chọn nhiều engine cùng lúc → nhập 1 lần → nhận nhiều bản dịch song song để đối chiếu.

**Đối tượng dùng:** người học ngoại ngữ, dịch giả, người cần dịch nhanh văn bản ngắn/trung bình và muốn kiểm chứng chéo giữa các engine.

**Điểm khác biệt cốt lõi so với 1 website dịch thông thường:** kiến trúc phải coi "translator engine" là một **plugin/adapter có thể cắm-rút**, không hard-code riêng cho từng bên — vì danh sách "Bing, Google, Baidu, ...." (dấu `...` trong ý tưởng gốc) ngụ ý sẽ còn thêm engine sau này (DeepL, Yandex, Papago, LLM-based...).

---

## 2. Tech Stack

### Backend — FastAPI
- **Lý do chọn:** async-native (quan trọng vì phải gọi nhiều engine dịch song song), tự sinh OpenAPI docs, type-safe với Pydantic — khớp tốt với việc mỗi engine trả JSON schema khác nhau cần chuẩn hóa.
- Python 3.11+, `httpx.AsyncClient` để gọi API các engine (không dùng `requests` vì đồng bộ, sẽ chặn event loop khi gọi 3-4 engine cùng lúc).
- `pydantic v2` cho schema request/response.

### Frontend — Vue.js
- Vue 3 + Composition API + `<script setup>`.
- **Giả định (cần bạn xác nhận):** dùng Pinia cho state management (danh sách engine đang chọn, ngôn ngữ, lịch sử dịch gần đây), Vite làm build tool, TailwindCSS cho styling. Nếu bạn đã có stack cụ thể khác (Vuetify, Element Plus, Options API...) thì thay vào phần này.
- Component tách theo chức năng: `EngineSelector.vue`, `LanguagePicker.vue`, `TextInput.vue`, `ResultCard.vue` (mỗi engine trả kết quả hiển thị trong 1 `ResultCard`).

### Giao tiếp Backend ↔ Frontend
- REST JSON qua FastAPI. **Cân nhắc dùng WebSocket hoặc SSE (Server-Sent Events)** cho endpoint dịch — vì nếu chọn 4 engine cùng lúc mà 1 engine chậm (Baidu hay timeout), người dùng vẫn muốn thấy kết quả của 3 engine kia hiện ra ngay thay vì đợi cả 4 xong mới trả về 1 lần. Đây là điểm thiết kế quan trọng, chi tiết ở mục 4.

---

## 3. Kiến trúc — Engine Adapter Pattern

Đây là phần quan trọng nhất của thiết kế, vì hệ thống phải dễ dàng thêm/bớt engine dịch mà không sửa code nghiệp vụ chính.

```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── translate.py          # route /translate
│   ├── engines/
│   │   ├── base.py               # abstract class TranslatorEngine
│   │   ├── google_engine.py
│   │   ├── bing_engine.py
│   │   ├── baidu_engine.py
│   │   └── registry.py           # đăng ký engine, map "id" -> instance
│   ├── schemas/
│   │   └── translate.py          # Pydantic models: request/response chuẩn hóa
│   └── core/
│       ├── config.py             # API key từng engine, timeout, rate limit
│       └── cache.py              # cache kết quả dịch (tùy chọn, mục 6)
```

### 3.1 Abstract base — hợp đồng chung cho mọi engine

```python
# engines/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class TranslationResult(BaseModel):
    engine_id: str
    engine_name: str
    translated_text: str | None
    detected_source_lang: str | None = None
    latency_ms: int
    success: bool
    error_message: str | None = None

class TranslatorEngine(ABC):
    engine_id: str
    display_name: str

    @abstractmethod
    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        ...

    @abstractmethod
    def supported_languages(self) -> list[str]:
        ...
```

**Mọi engine mới chỉ cần implement class này** — không đụng vào route hay logic gọi song song. Đây là điểm mấu chốt giúp thêm "DeepL" hay "Yandex" sau này chỉ tốn 1 file mới + 1 dòng đăng ký ở `registry.py`.

### 3.2 Registry — nơi khai báo engine khả dụng

```python
# engines/registry.py
ENGINE_REGISTRY: dict[str, TranslatorEngine] = {
    "google": GoogleEngine(),
    "bing": BingEngine(),
    "baidu": BaiduEngine(),
}
```

Frontend gọi `GET /engines` để lấy danh sách engine + ngôn ngữ hỗ trợ của từng engine (không hard-code danh sách engine ở frontend — vì khi backend thêm engine mới, frontend tự động hiển thị thêm mà không cần deploy lại).

### 3.3 Xử lý sự khác biệt giữa các engine (điểm dễ bị bỏ sót)

Mỗi engine thật (Google/Bing/Baidu) có:
- **Mã ngôn ngữ khác nhau** cho cùng 1 ngôn ngữ (ví dụ tiếng Việt: Google dùng `vi`, một số API khác dùng `vie` hoặc `VN`). → cần bảng mapping riêng trong mỗi adapter, chuẩn hóa về 1 bộ mã ISO chung (ví dụ ISO 639-1) ở tầng giao diện người dùng, rồi mỗi adapter tự convert sang mã riêng của engine đó trước khi gọi.
- **Giới hạn độ dài văn bản** khác nhau (một số engine free tier giới hạn ~5000 ký tự/request). → mỗi adapter tự khai báo `max_text_length`, backend cảnh báo/tự động chia nhỏ nếu vượt (xem mục 5).
- **Auth khác nhau:** Google Cloud Translate dùng API key/service account, Bing dùng subscription key qua header, Baidu dùng `appid` + `secret` + MD5 sign theo từng request. → nhét toàn bộ chi tiết auth này bên trong adapter, không lộ ra tầng route.

---

## 4. Flow chi tiết (mở rộng từ flow gốc)

```
[Chọn Engine(s)] → [Chọn ngôn ngữ nguồn/đích] → [Nhập/dán text]
        → [Gửi request dịch song song tới các engine đã chọn]
        → [Hiển thị kết quả từng engine ngay khi có, không đợi engine chậm nhất]
        → [Copy 1 bản dịch cụ thể, hoặc copy tất cả]
```

### 4.1 Bước "Chọn Engine" — cần UX rõ về trạng thái engine
- Checkbox multi-select, mặc định nhớ lựa chọn lần trước (localStorage phía frontend).
- Engine nào đang bị lỗi/hết quota (backend biết qua health check định kỳ) nên hiển thị disabled + tooltip lý do, tránh người dùng chọn phải engine chắc chắn fail.

### 4.2 Bước gọi dịch — song song thật sự, không chờ nhau
Đây là lý do nên cân nhắc SSE thay vì REST thường:

```python
# api/translate.py (minh họa ý tưởng, không phải code hoàn chỉnh)
@router.get("/translate/stream")
async def translate_stream(text: str, source: str, target: str, engines: list[str]):
    async def event_generator():
        tasks = {
            engine_id: asyncio.create_task(
                ENGINE_REGISTRY[engine_id].translate(text, source, target)
            )
            for engine_id in engines
        }
        for engine_id, task in tasks.items():
            try:
                result = await asyncio.wait_for(task, timeout=8.0)
            except asyncio.TimeoutError:
                result = TranslationResult(
                    engine_id=engine_id, engine_name=engine_id,
                    translated_text=None, latency_ms=8000,
                    success=False, error_message="timeout"
                )
            yield f"data: {result.model_dump_json()}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Lưu ý quan trọng:** dùng `asyncio.as_completed` hoặc gather kèm early-yield thay vì vòng lặp tuần tự theo `tasks.items()` như minh họa trên (minh họa trên vẫn chờ theo thứ tự khai báo, chưa tối ưu) — engine nào xong trước phải trả về trước, không phụ thuộc thứ tự người dùng chọn. Antigravity/dev cần implement bằng `asyncio.as_completed(tasks.values())` thực sự để đạt đúng UX "hiện dần".

- Timeout riêng cho từng engine (không để 1 engine chậm kéo timeout chung).
- Nếu 1 engine lỗi: hiển thị lỗi rõ ràng trong `ResultCard` của engine đó, KHÔNG làm fail toàn bộ response của các engine còn lại.

### 4.3 Bước copy kết quả
- Copy từng bản dịch riêng (nút copy trên mỗi `ResultCard`).
- Copy tất cả dạng liệt kê `[Tên Engine]: bản dịch` — hữu ích khi người dùng muốn dán đi so sánh ở nơi khác.
- Toast nhỏ xác nhận "Đã copy" (UX feedback tối thiểu, dễ bị quên khi implement).

---

## 5. Xử lý edge case cần thiết kế từ đầu

| Trường hợp | Xử lý |
|---|---|
| Text rỗng | Chặn ở frontend trước khi gọi API (validation ngay khi submit) |
| Text vượt giới hạn ký tự của 1 engine | Với engine đó: hoặc tự động chia nhỏ + ghép lại kết quả, hoặc trả lỗi rõ "vượt giới hạn X ký tự" — chọn 1 trong 2 và áp dụng nhất quán, không im lặng cắt bớt text |
| Ngôn ngữ nguồn = "Auto-detect" | Không phải engine nào cũng hỗ trợ detect — adapter cần tự xử lý (ví dụ tự detect bằng thư viện riêng nếu engine không hỗ trợ, rồi mới gọi dịch) |
| Cùng lúc gọi 5+ engine cho nhiều người dùng | Cần rate limiting ở tầng backend theo IP/session để tránh 1 người dùng spam làm cạn quota API trả phí (Google/Baidu đều tính phí theo ký tự) |
| Engine yêu cầu API key trả phí hết hạn/hết quota | Health check định kỳ (mục 4.1) + circuit breaker: tự động tạm loại engine khỏi danh sách khả dụng một khoảng thời gian sau N lần lỗi liên tiếp, tránh gọi phí vô ích vào endpoint chắc chắn fail |

---

## 6. Cache (đề xuất thêm — cân nhắc theo nhu cầu thực tế)

Nhiều API dịch trả phí theo số ký tự. Nếu nhiều người dùng dịch cùng 1 câu phổ biến, cache giúp giảm chi phí đáng kể.

- Key cache: hash(`text + source_lang + target_lang + engine_id`).
- Redis (nếu deploy có sẵn) hoặc in-memory LRU cache (nếu quy mô nhỏ, single instance).
- TTL hợp lý (ví dụ 7 ngày) — bản dịch không đổi theo thời gian nên có thể cache dài.
- **Đánh dấu rõ trong response** nếu kết quả đến từ cache hay gọi API thật (hữu ích khi debug, không bắt buộc hiển thị cho người dùng cuối).

---

## 7. API Contract (đề xuất)

```
GET  /engines
     → [{ "id": "google", "name": "Google Translate", "available": true, "supported_languages": [...] }, ...]

GET  /translate/stream?text=...&source=auto&target=vi&engines=google,bing,baidu
     → Server-Sent Events, mỗi event là 1 TranslationResult JSON (mục 3.1)

POST /translate  (bản không-stream, dự phòng cho client không hỗ trợ SSE, hoặc dùng cho API/automation)
     body: { "text": str, "source_lang": str, "target_lang": str, "engines": [str] }
     → { "results": [TranslationResult, ...] }  # đợi tất cả xong mới trả 1 lần
```

Giữ cả 2 endpoint (stream + non-stream) để linh hoạt: frontend web dùng stream cho UX mượt, nhưng vẫn có REST thường cho trường hợp tích hợp đơn giản (script, Postman, mobile app sau này...).

---

## 8. Việc thêm 1 engine mới sau này (test case cho tính mở rộng của thiết kế)

Ví dụ thêm DeepL:
1. Tạo `engines/deepl_engine.py`, implement `TranslatorEngine`.
2. Thêm entry vào `ENGINE_REGISTRY`.
3. Thêm API key DeepL vào `core/config.py` (đọc từ biến môi trường, không hard-code).
4. Không cần sửa route, không cần sửa frontend (frontend tự lấy danh sách qua `/engines`).

Nếu một thay đổi thiết kế nào ở trên khiến bước "thêm engine mới" vẫn phải sửa route/frontend, đó là dấu hiệu vi phạm nguyên tắc adapter pattern — cần refactor lại.

---

## 9. Việc chưa quyết định — cần bạn xác nhận trước khi code

- [ ] Có cần tài khoản người dùng / lưu lịch sử dịch không, hay stateless hoàn toàn (chỉ lưu tạm ở localStorage)?
- [ ] Các engine dịch qua API chính thức trả phí (Google Cloud Translate, Bing Translator API, Baidu Translate API) hay qua scraping/unofficial endpoint? (Ảnh hưởng lớn tới độ ổn định, rate limit, và rủi ro pháp lý/ToS — nên làm rõ trước khi implement adapter.)
- [ ] Giới hạn số engine chọn cùng lúc là bao nhiêu (không giới hạn có thể gây tốn phí/API quá tải)?
- [ ] Có cần hỗ trợ dịch file (docx/txt) ngoài dịch text nhập tay không, hay chỉ trong phạm vi text?
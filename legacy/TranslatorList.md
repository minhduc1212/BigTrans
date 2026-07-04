# Danh sách thư viện dịch thuật Python & hỗ trợ tiếng Việt

## 1. `translators`
```
pip install translators
```

Hỗ trợ tiếng Việt: **hầu hết đều có**, vì đây toàn là các dịch vụ lớn của Trung/Nga/toàn cầu vốn đã hỗ trợ đa ngôn ngữ.

| Engine | Có tiếng Việt |
|---|---|
| alibaba | ✅ |
| baidu | ✅ |
| bing | ✅ |
| caiyun | ✅ |
| google | ✅ |
| hujiang | ✅ |
| iciba | ✅ |
| iflytek | ✅ |
| itranslate | ✅ |
| judic | ✅ |
| niutrans | ✅ |
| papago | ✅ |
| qqFanyi / qqTranSmart (Tencent) | ✅ |
| reverso | ✅ |
| sogou | ✅ |
| sysTran | ✅ |
| tilde | ✅ |
| translateCom | ✅ |
| volcEngine | ✅ |
| xunjie | ✅ |
| yandex | ✅ |
| yeekit | ✅ |
| youdao | ✅ |
| deepl | ✅ (từ giữa 2025) |
| myMemory | ✅ |
| lingvanex | ✅ |
| elia / mglip / mirai / modernMt / languageWire / lara | ✅ (đa số) |
| apertium / argos | ⚠️ hạn chế, chất lượng thấp hơn |

> Với dịch tiểu thuyết Trung → Việt, hay dùng nhất: **bing, google, sogou, youdao, baidu, tencent (qqFanyi)** — vì các engine Trung Quốc quen văn phong tiểu thuyết mạng (tiên hiệp, huyền huyễn...).

---

## 2. `deep-translator`
```
pip install deep-translator
```

```python
from deep_translator import (GoogleTranslator, ChatGptTranslator, MicrosoftTranslator,
                              PonsTranslator, LingueeTranslator, MyMemoryTranslator,
                              YandexTranslator, PapagoTranslator, DeeplTranslator, QcriTranslator)
```

| Class | Có tiếng Việt | Ghi chú |
|---|---|---|
| GoogleTranslator | ✅ | miễn phí |
| MicrosoftTranslator | ✅ | cần API key |
| YandexTranslator | ✅ | cần API key |
| MyMemoryTranslator | ✅ | miễn phí |
| DeeplTranslator | ✅ | mới thêm từ 6/2025, cần API key (có gói free) |
| PapagoTranslator | ✅ | Naver hỗ trợ vi |
| ChatGptTranslator | ✅ | cần OpenAI API key |
| QcriTranslator | ❌ | chuyên tiếng Ả Rập |
| PonsTranslator | ❌ | từ điển song ngữ châu Âu, không có vi |
| LingueeTranslator | ❌ | từ điển song ngữ châu Âu, không có vi |

---

## 3. `translate`
```
pip install translate
```

Engine hỗ trợ: **MyMemory** (mặc định), **Microsoft**, **DeepL**, **Yandex**, **LibreTranslate**.

→ Cả 5 engine đều có tiếng Việt (MyMemory, Microsoft, Yandex, LibreTranslate hỗ trợ `vi` từ lâu; DeepL mới có từ 2025).

---

## 4. `translatepy`
```
pip install translatepy
```

Bọc: Google, Bing (Microsoft), Yandex, Reverso, MyMemory, DeepL, LibreTranslate, TranslateCom...

→ Về cơ bản đều có `vi`, trừ khi dùng bản `translatepy` cũ chưa cập nhật DeepL.

---

## 5. `googletrans` / `py-googletrans`
```
pip install googletrans==4.0.0-rc1
```
Chỉ 1 engine (Google Translate không chính thức) → **có tiếng Việt**.

---

## 6. `mtranslate`
```
pip install mtranslate
```
Chỉ gọi Google Translate → **có tiếng Việt**.

---

## 7. `argos-translate` / LibreTranslate (dịch offline)
```
pip install argostranslate
```
Cần tải riêng gói ngôn ngữ `zh → vi`. Có gói mô hình Trung→Việt nhưng chất lượng dịch tiểu thuyết/văn học thường **kém hơn hẳn** Bing/Google/Youdao vì model nhỏ, không quen văn phong tiên hiệp/ngôn tình.

---

## Tóm gọn — engine nào dịch Trung → Việt tốt nhất cho tiểu thuyết

| Thứ hạng | Engine | Nhận xét |
|---|---|---|
| 1 | **Bing** | dân dịch truyện đánh giá tốt cho văn phong tiểu thuyết Trung |
| 2 | **Youdao / Sogou / Baidu / Tencent** (chỉ có trong `translators`) | quen thuật ngữ tiên hiệp, huyền huyễn hơn Google |
| 3 | **Google** | ổn định, dễ dùng nhất |
| 4 | **DeepL** | câu văn mượt nhưng mới hỗ trợ Việt, thuật ngữ tiểu thuyết Trung chưa quen bằng Bing/Youdao |


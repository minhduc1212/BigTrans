# Gibsnart Technical Documentation 📘

This document provides a detailed breakdown of the Gibsnart architecture, request flow, engine adapters, concurrency patterns, and the frontend client design.

---

## 1. System Architecture & Component Map

Gibsnart is built on a decoupled architecture containing an asynchronous **FastAPI** backend and a reactive **Vue 3** single-page application.

```
┌────────────────────────────────────────────────────────┐
│                    Vue.js Frontend                     │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ LanguagePicker   │  │  TextInput   │  │ History  │  │
│  └────────┬─────────┘  └──────┬───────┘  └────┬─────┘  │
│           │                   │               │        │
│           ▼                   ▼               ▼        │
│  ┌──────────────────────────────────────────────────┐  │
│  │                    store.js                      │  │
│  └────────────────────────┬─────────────────────────┘  │
└───────────────────────────┼────────────────────────────┘
                            │ (GET /translate/stream)
                            ▼
┌────────────────────────────────────────────────────────┐
│                    FastAPI Backend                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │                    main.py                       │  │
│  └────────────────────────┬─────────────────────────┘  │
│                           │                            │
│                           ▼                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │               api/translate.py                   │  │
│  │        (Concurrently queries engines)             │  │
│  └───────┬────────────────┬────────────────┬────────┘  │
│          │                │                │           │
│          ▼                ▼                ▼           │
│     GoogleEngine     BaiduEngine       YoudaoEngine    │
│    (Custom Async)    (Playwright)     (Library Async)  │
└────────────────────────────────────────────────────────┘
```

### Key Modules:
- **`backend/app/main.py`**: The application entrypoint. Configures FastAPI and mounts `CORSMiddleware` to allow cross-origin requests from the Vite frontend.
- **`backend/app/api/translate.py`**: Declares translation routes (streaming and POST). Manages concurrent tasks using async helpers.
- **`backend/app/core/cache.py`**: Implements a thread-safe in-memory cache using SHA256 hashes of queries to prevent duplicate requests.
- **`backend/app/engines/base.py`**: Abstract base class (`TranslatorEngine`) defining the interface for all engine adapters.

---

## 2. Dynamic Translation Flow (SSE Stream)

The streaming translation route (`/translate/stream`) works as follows:

```
[Client]                [Router]              [Engine 1]            [Engine 2]
   │                       │                      │                     │
   │─── GET SSE Stream ───>│                      │                     │
   │    (Text & Engines)   │                      │                     │
   │                       │─── Check Cache ─────>│                     │
   │                       │    (Hits cache)      │                     │
   │                       │                      │                     │
   │                       │─── Query Async ───────────────────────────>│
   │                       │                      │                     │
   │<── Yield Engine 1 ────│                      │                     │
   │    (Instant Cache)    │                      │                     │
   │                       │                      │                     │
   │                       │<── Yield result ───────────────────────────│
   │                       │                      │                     │
   │<── Yield Engine 2 ────│                      │                     │
   │                       │                      │                     │
```

1. **Initiation**: The Vue store creates a browser `EventSource` pointing to `/api/v1/translate/stream` with query parameters.
2. **Concurreny Setup**: In the router, an array of coroutine tasks is initialized:
   ```python
   tasks = [run_engine_translation(engine_id, text, source, target) for engine_id in engine_ids]
   ```
3. **Execution & Interleaving**: We iterate over tasks as they finish using `asyncio.as_completed(tasks)`. This allows results to be streamed back to the client immediately, ensuring slow engines do not block fast ones.
4. **Cache Hook**: If a query exists in the in-memory cache, it resolves with `latency_ms = 0` and bypasses network requests completely.

---

## 3. Engine Adapter Implementations

Each engine implementation inherits from `TranslatorEngine` and conforms to standard ISO 639-1 language codes. 

### A. Custom HTTP Adapters (Async)
- **Google Translator** (`google`): Fetches the main Google Translate homepage, extracts dynamic authorization variables (`bl` and `f.sid`) from `window.WIZ_global_data` via regex, and simulates the standard Google RPC batch execution POST endpoint (`/data/batchexecute`).
- **Bing Translator** (`bing`): Fetches `www.bing.com/translator` to acquire session parameters (`IG`, `IID`, `key`, and `token`) from `params_AbusePreventionHelper`, then posts to `/ttranslatev3`.

*Both adapters utilize `asyncio.Lock` properties to prevent multiple concurrent requests from triggering race conditions and authorization errors.*

### B. Headless Browser Adapters (Sync-to-Async)
- **Baidu AIT Translator** (`baidu`): Extracts cookies and headers by running a headless Chromium browser instance using Playwright, caches the session in `.baidu_token_cache.json`, and triggers the incognito API.
*Because Playwright and the token generator are synchronous, calls are offloaded to secondary threads using `asyncio.to_thread` to prevent event-loop blockages.*

### C. Library Wrappers
- **Sogou** (`sogou`) & **Youdao** (`youdao`): Leverages the `translators` library.
- **Google Pip** (`google_pip`): Leverages the `deep-translator` library.
*Like the Baidu adapter, these are executed inside `asyncio.to_thread` workers to protect event loop responsiveness.*

---

## 4. In-Memory Cache Implementation

The cache class (`TranslationCache` in `backend/app/core/cache.py`) uses a standard Python dictionary protected by a threading lock:

- **Key Generation**: Hash key is created using:
  `hash = sha256(text + "||" + source_lang + "||" + target_lang + "||" + engine_id)`
- **Thread Safety**: Uses `threading.Lock()` to serialize updates from concurrent asyncio tasks.
- **Eviction**: Records expiry timestamps during insertion. Expired keys are checked and deleted on lookup.

---

## 5. Frontend Reactive Architecture

The Vue application uses a unified store pattern in `store.js`:

```javascript
export const store = reactive({
  engines: [],          // Available engines from /engines
  selectedEngines: [],  // User-selected list
  translations: {},     // Reactive dictionary holding query results
  
  async translate() {
    // 1. Initialise cards as "loading"
    // 2. Fetch /translate/stream (or fallback to POST if query is long)
    // 3. Update reactive translations dictionary chunk-by-chunk
  }
})
```

### Component Breakdown:
1. **`App.vue`**: Primary layout dashboard. Applies the current theme class (`theme-dark` / `theme-light`) to `document.body` and structures the interface.
2. **`LanguagePicker.vue`**: Language select dropdowns and swaps. Swapping is disabled when the source language is set to `Auto Detect`.
3. **`TextInput.vue`**: Textarea binding, character count, stream toggle, clear action, and Ctrl+Enter trigger.
4. **`EngineSelector.vue`**: Engine checklist displaying description cards and capability tags.
5. **`ResultCard.vue`**: Side-by-side card slots rendering states (shimmer skeletons during loading, red notices on errors, copy buttons, and latency statistics on success).

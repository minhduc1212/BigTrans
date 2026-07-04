# Gibsnart Parallel Translator 🌐🤖

Gibsnart is a premium, high-performance web-based translation hub that runs multiple translation engines in parallel, allowing web novel readers and translators to compare outputs side-by-side. 

By querying Google, Bing, Baidu, DeepL, Youdao, and Sogou concurrently, Gibsnart ensures you get the absolute best phrasing, especially for Chinese-to-Vietnamese cultivation terms and fantasy prose.

---

## ✨ Features

- 🏎️ **Parallel Queries**: Translates using multiple engines at the same time.
- ⚡ **Server-Sent Events (SSE)**: Results stream in real-time as soon as each engine finishes.
- 🌓 **Light & Dark Themes**: Fully refined minimalist light and dark modes in clean neutral zinc/slate styles.
- 🔌 **Engine Adapter Pattern**: Modular backend allows clean plug-and-play adding of new engines.
- 💾 **TTL Caching**: Caches queries for 7 days to conserve quotas and increase repeat request speeds to `0 ms`.
- 📋 **Batch Copy**: One-click copy for individual engines or copy all formatted results together.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Async HTTPX, Playwright (for Baidu token handshakes), Uvicorn.
- **Libraries**: `translators` (Youdao, Sogou), `deep-translator` (Google Pip).
- **Frontend**: Vue 3 + Vite, `@lucide/vue` icons, Vanilla CSS.

---

## 🚀 Running the Project

For a detailed walkthrough of the codebase, request flows, and internal engine adapters, please read the [Gibsnart Technical Documentation (DOC.md)](file:///D:/LT/BigComTrans/DOC.md).

### 1. Backend Setup
Make sure you are in the project root directory. Use the Python virtual environment to run Uvicorn:
```powershell
.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload
```
The interactive OpenAPI docs will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup
Navigate into the `frontend` directory, install dependencies, and start the Vite dev server:
```powershell
cd frontend
npm run dev
```
The web client dashboard will be available at: [http://localhost:5173](http://localhost:5173) (or the next available port like `5175`).

---

## 📂 Project Structure

```text
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # Route handlers (REST & SSE Stream)
│   │   ├── core/             # Configuration & TTL cache manager
│   │   ├── engines/          # Individual engine adapters (Google, Bing, Baidu, DeepL, etc.)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── main.py           # Application entrypoint & CORS middleware
├── frontend/                 # Vite + Vue 3 Application
│   ├── src/
│   │   ├── components/       # Language picker, text input, engine selector, result cards
│   │   ├── store.js          # Shared reactive state store & SSE listener
│   │   ├── style.css         # Custom premium CSS theme styles
│   │   └── App.vue           # Primary layout dashboard
├── legacy/                   # Deprecated standalone testing scripts
├── DOC.md                    # Detailed code flow & architecture documentation
└── README.md                 # Project guide
```

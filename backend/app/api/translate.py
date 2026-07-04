import asyncio
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import List

from backend.app.engines.registry import ENGINE_REGISTRY
from backend.app.engines.base import TranslationResult
from backend.app.schemas.translate import EngineInfo, TranslateRequest, TranslateResponse
from backend.app.core.config import settings
from backend.app.core.cache import translation_cache

router = APIRouter()

async def run_engine_translation(engine_id: str, text: str, source: str, target: str) -> TranslationResult:
    """Helper to run a translation with cache checks and error handling."""
    if engine_id not in ENGINE_REGISTRY:
        return TranslationResult(
            engine_id=engine_id,
            engine_name=engine_id,
            translated_text=None,
            latency_ms=0,
            success=False,
            error_message="Engine not registered"
        )
        
    engine = ENGINE_REGISTRY[engine_id]
    
    # Check cache first
    if settings.CACHE_ENABLED:
        cached = translation_cache.get(text, source, target, engine_id)
        if cached is not None:
            translated_text, detected_lang = cached
            return TranslationResult(
                engine_id=engine_id,
                engine_name=engine.display_name,
                translated_text=translated_text,
                detected_source_lang=detected_lang,
                latency_ms=0,
                success=True
            )
            
    # Execute translate
    try:
        result = await asyncio.wait_for(
            engine.translate(text, source, target),
            timeout=settings.DEFAULT_TIMEOUT
        )
    except asyncio.TimeoutError:
        result = TranslationResult(
            engine_id=engine_id,
            engine_name=engine.display_name,
            translated_text=None,
            latency_ms=int(settings.DEFAULT_TIMEOUT * 1000),
            success=False,
            error_message="timeout"
        )
    except Exception as e:
        result = TranslationResult(
            engine_id=engine_id,
            engine_name=engine.display_name,
            translated_text=None,
            latency_ms=0,
            success=False,
            error_message=str(e)
        )
        
    # Save cache on success
    if result.success and result.translated_text and settings.CACHE_ENABLED:
        translation_cache.set(
            text, source, target, engine_id,
            result.translated_text,
            settings.CACHE_TTL_SECONDS,
            result.detected_source_lang
        )
        
    return result

@router.get("/engines", response_model=List[EngineInfo])
def get_engines():
    """Get list of supported translation engines and their supported languages."""
    return [
        EngineInfo(
            id=engine_id,
            name=engine.display_name,
            available=True,
            supported_languages=engine.supported_languages()
        )
        for engine_id, engine in ENGINE_REGISTRY.items()
    ]

@router.get("/translate/stream")
async def translate_stream(
    text: str = Query(..., min_length=1),
    source: str = Query("auto"),
    target: str = Query("vi"),
    engines: str = Query(..., description="Comma-separated list of engine IDs")
):
    """
    Translate text using multiple engines concurrently, returning results via Server-Sent Events (SSE).
    Results are returned as soon as each engine completes.
    """
    engine_ids = [e.strip() for e in engines.split(",") if e.strip()]
    if not engine_ids:
        raise HTTPException(status_code=400, detail="No engines selected")
        
    tasks = [
        run_engine_translation(engine_id, text, source, target)
        for engine_id in engine_ids
    ]
    
    async def event_generator():
        # Yield results as they complete
        for task in asyncio.as_completed(tasks):
            result = await task
            yield f"data: {result.model_dump_json()}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/translate", response_model=TranslateResponse)
async def translate_post(request: TranslateRequest):
    """
    Translate text using multiple engines concurrently, returning results in a single response after all finish.
    """
    tasks = [
        run_engine_translation(engine_id, request.text, request.source_lang, request.target_lang)
        for engine_id in request.engines
    ]
    results = await asyncio.gather(*tasks)
    return TranslateResponse(results=list(results))

"""FastAPI application entry point.

Registers all API routers:
events, memories, knowledge, intelligence, agents, prediction.
"""

import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.events import router as events_router
from app.api.v1.memories import router as memories_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.agents import router as agents_router
from app.api.v1.prediction import router as prediction_router
from app.api.v1.profile import router as profile_router
from app.api.v1.conversation import router as conversation_router
from app.api.v1.system import router as system_router
from app.api.v1.emotion import router as emotion_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logger import logger
from app.core.security import verify_api_key
import app.models
from app.voice_ws_v2 import router as voice_router_v2

RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60
request_counts: dict[str, list[float]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Machine is starting...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")
    from app.core.scheduler import scheduler
    scheduler.start()
    yield
    logger.info("Machine is shutting down...")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan, docs_url="/docs")
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="static")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def log_and_rate_limit(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
    if request.url.path.startswith(settings.API_PREFIX) and request.client and request.client.host != "127.0.0.1":
        client_ip = request.client.host
        now = time.time()
        key = f"{client_ip}:{request.url.path}"
        if key not in request_counts:
            request_counts[key] = []
        request_counts[key] = [t for t in request_counts[key] if now - t < RATE_LIMIT_WINDOW]
        request_counts[key].append(now)
        if len(request_counts[key]) > RATE_LIMIT_REQUESTS:
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    return response


app.include_router(events_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(memories_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(knowledge_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(intelligence_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(agents_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(prediction_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(profile_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(system_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(conversation_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])
app.include_router(emotion_router, prefix=settings.API_PREFIX, dependencies=[Depends(verify_api_key)])


@app.get("/")
def root():
    return {"status": "Machine is online", "version": settings.APP_VERSION}


@app.get("/go")
async def go_to_dashboard():
    return RedirectResponse(url="/dashboard/")


app.include_router(voice_router_v2)

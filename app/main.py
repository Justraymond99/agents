from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import build_router
from app.config.settings import get_settings
from app.runtime import build_runtime

settings = get_settings()
runtime = build_runtime(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await runtime.initialize()
    try:
        yield
    finally:
        await runtime.shutdown()


app = FastAPI(
    title="ATLAS",
    description="Multi-agent personal orchestration harness",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def require_api_token(request: Request, call_next: object) -> object:
    if settings.api_token and request.url.path != "/health":
        expected = f"Bearer {settings.api_token}"
        if request.headers.get("authorization") != expected:
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
    return await call_next(request)  # type: ignore[operator]


app.include_router(build_router(runtime))


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "atlas"}

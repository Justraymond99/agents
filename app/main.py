from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import build_router
from app.runtime import build_runtime

runtime = build_runtime()


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
app.include_router(build_router(runtime))


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "atlas"}

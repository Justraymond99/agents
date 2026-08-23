from fastapi import FastAPI

from app.api.routes import build_router
from app.runtime import build_runtime

runtime = build_runtime()

app = FastAPI(
    title="ATLAS",
    description="Multi-agent personal orchestration harness",
    version="0.1.0",
)
app.include_router(build_router(runtime))


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "atlas"}

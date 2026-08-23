from fastapi import FastAPI

app = FastAPI(
    title="ATLAS",
    description="Multi-agent personal orchestration harness",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "atlas"}

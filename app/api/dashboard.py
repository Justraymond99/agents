from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


def build_dashboard_router() -> APIRouter:
    router = APIRouter()

    @router.get("/dashboard", response_class=HTMLResponse)
    async def dashboard() -> str:
        return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>ATLAS</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 920px; margin: 40px auto; padding: 0 20px; background:#0b1020; color:#e8ecf3; }
    .card { background:#151d33; border:1px solid #26324f; border-radius:14px; padding:18px; margin:14px 0; }
    input, button { font:inherit; padding:10px 12px; border-radius:8px; border:1px solid #3a496d; }
    input { width:70%; background:#0f1628; color:#fff; }
    button { cursor:pointer; background:#eef3ff; color:#10182a; font-weight:700; }
    pre { white-space:pre-wrap; overflow-wrap:anywhere; background:#0a0f1d; padding:12px; border-radius:8px; }
  </style>
</head>
<body>
  <h1>ATLAS</h1>
  <p>Multi-agent orchestration control surface.</p>
  <div class="card">
    <h2>Submit task</h2>
    <input id="goal" placeholder="What should ATLAS do?" />
    <button onclick="submitTask()">Run</button>
    <pre id="taskResult">Ready.</pre>
  </div>
  <div class="card">
    <h2>Runtime</h2>
    <button onclick="loadMetrics()">Refresh metrics</button>
    <pre id="metrics">No metrics loaded.</pre>
  </div>
<script>
const headers = {'Content-Type':'application/json'};
async function submitTask() {
  const goal = document.getElementById('goal').value.trim();
  if (!goal) return;
  const response = await fetch('/tasks', {method:'POST', headers, body:JSON.stringify({goal})});
  document.getElementById('taskResult').textContent = JSON.stringify(await response.json(), null, 2);
}
async function loadMetrics() {
  const response = await fetch('/metrics');
  document.getElementById('metrics').textContent = JSON.stringify(await response.json(), null, 2);
}
</script>
</body>
</html>"""

    return router

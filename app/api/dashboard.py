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
    body {
      font-family: system-ui, sans-serif;
      max-width: 920px;
      margin: 40px auto;
      padding: 0 20px;
      background: #0b1020;
      color: #e8ecf3;
    }
    .card {
      background: #151d33;
      border: 1px solid #26324f;
      border-radius: 14px;
      padding: 18px;
      margin: 14px 0;
    }
    input, button {
      font: inherit;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid #3a496d;
    }
    input {
      width: 70%;
      background: #0f1628;
      color: #fff;
    }
    button {
      cursor: pointer;
      background: #eef3ff;
      color: #10182a;
      font-weight: 700;
    }
    pre {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #0a0f1d;
      padding: 12px;
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <h1>ATLAS</h1>
  <p>Multi-agent orchestration control surface.</p>

  <div class="card">
    <h2>API authentication</h2>
    <input id="apiToken" type="password" placeholder="ATLAS_API_TOKEN (optional)" />
    <button onclick="saveToken()">Use token</button>
    <button onclick="clearToken()">Clear</button>
    <pre id="authStatus">No browser token configured.</pre>
  </div>

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
const tokenStorageKey = 'atlas.apiToken';

function apiHeaders(includeJson = false) {
  const headers = {};
  const token = sessionStorage.getItem(tokenStorageKey);
  if (includeJson) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function refreshAuthStatus() {
  const hasToken = Boolean(sessionStorage.getItem(tokenStorageKey));
  document.getElementById('authStatus').textContent = hasToken
    ? 'Browser token configured for this tab.'
    : 'No browser token configured.';
}

function saveToken() {
  const value = document.getElementById('apiToken').value.trim();
  if (value) sessionStorage.setItem(tokenStorageKey, value);
  document.getElementById('apiToken').value = '';
  refreshAuthStatus();
}

function clearToken() {
  sessionStorage.removeItem(tokenStorageKey);
  document.getElementById('apiToken').value = '';
  refreshAuthStatus();
}

async function renderJson(response, elementId) {
  const element = document.getElementById(elementId);
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = {status: response.status, error: 'Response was not JSON'};
  }
  element.textContent = JSON.stringify(payload, null, 2);
}

async function submitTask() {
  const goal = document.getElementById('goal').value.trim();
  if (!goal) return;
  const response = await fetch('/tasks', {
    method: 'POST',
    headers: apiHeaders(true),
    body: JSON.stringify({goal}),
  });
  await renderJson(response, 'taskResult');
}

async function loadMetrics() {
  const response = await fetch('/metrics', {headers: apiHeaders()});
  await renderJson(response, 'metrics');
}

refreshAuthStatus();
</script>
</body>
</html>"""

    return router

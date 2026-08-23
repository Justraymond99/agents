# ATLAS MCP client setup

ATLAS exposes an MCP server from `app.mcp_server`.

## Local start

```bash
python -m app.mcp_server
```

The default MCP transport is stdio. Keep `ATLAS_OPENAI_API_KEY` and any runtime configuration in the environment of the process launching ATLAS.

## Cursor

Add ATLAS as a stdio MCP server in Cursor's MCP configuration. The command should run the repository's Python environment:

```json
{
  "mcpServers": {
    "atlas": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/absolute/path/to/agents"
    }
  }
}
```

## Codex

Configure a local stdio MCP server named `atlas` using the same command and working directory. Once connected, the client can call:

- `submit_task`
- `get_task_status`
- `get_task_result`
- `query_memory`
- `write_memory`

ATLAS remains the orchestration and memory layer; the editor/agent client is only an interface.

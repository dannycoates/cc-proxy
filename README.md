# cc-proxy

A mitmproxy addon that logs Claude API requests and responses as JSON lines.

## Installation

```bash
uv sync
```

## Usage

```bash
# Start the proxy on port 8080 (default)
./cc-proxy

# Custom port
./cc-proxy 9090

# Pipe to jq for pretty printing
./cc-proxy | jq

# Save to file
./cc-proxy >> claude.jsonl
```

Configure your client to use `http://localhost:8080` as the HTTPS proxy.

## Output Format

Each line is a JSON object:

**Requests** (application/json bodies):
```json
{"request": {"model": "claude-sonnet-4-...", "messages": [...]}}
```

**Responses** (parsed from SSE stream):
```json
{"response": [{"type": "text", "text": "Hello!"}, {"type": "tool_use", "id": "toolu_...", "name": "Read", "input": {...}}]}
```

Content block types: `text`, `thinking`, `tool_use`

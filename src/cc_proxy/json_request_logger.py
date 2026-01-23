"""
Mitmproxy addon that logs Claude API request/response bodies.

Usage:
    mitmdump -s src/cc_proxy/json_request_logger.py
"""

import json

from mitmproxy import http


class JSONRequestLogger:
    """
    Addon that intercepts HTTP requests/responses and outputs them wrapped:
    - Requests: {"request": <original_json_body>}
    - Responses: {"response": [<content_blocks>]} (parsed from SSE stream)
    """

    def request(self, flow: http.HTTPFlow):
        if not flow.request.content:
            return

        content_type = flow.request.headers.get("content-type", "").lower()
        if "json" not in content_type:
            return

        try:
            request_json = flow.request.json()
        except json.JSONDecodeError:
            return

        print(json.dumps({"request": request_json}), flush=True)

    def response(self, flow: http.HTTPFlow):
        if not flow.response or not flow.response.content:
            return

        content_type = flow.response.headers.get("content-type", "").lower()
        if "text/event-stream" not in content_type:
            return

        content = self._parse_sse_stream(flow.response.content)
        if content:
            print(json.dumps({"response": content}), flush=True)

    def _parse_sse_stream(self, body: bytes) -> list | None:
        """Parse SSE stream and reconstruct message content.

        Handles raw response bodies that may include HTTP headers or
        chunked transfer encoding markers by skipping non-SSE lines.
        """
        content_blocks = {}  # index -> accumulated content

        lines = body.decode("utf-8", errors="replace").split("\n")
        current_event = None

        for line in lines:
            line = line.strip()
            # Skip empty lines, HTTP headers, chunk size markers, etc.
            if not line or (not line.startswith("event:") and not line.startswith("data:")):
                continue
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                if current_event == "content_block_start":
                    idx = data["index"]
                    block = data["content_block"]
                    content_blocks[idx] = {
                        "type": block["type"],
                        "content": "",
                        # Preserve tool_use metadata
                        "id": block.get("id"),
                        "name": block.get("name"),
                    }
                elif current_event == "content_block_delta":
                    idx = data["index"]
                    delta = data["delta"]
                    if delta["type"] == "text_delta":
                        content_blocks[idx]["content"] += delta["text"]
                    elif delta["type"] == "thinking_delta":
                        content_blocks[idx]["content"] += delta["thinking"]
                    elif delta["type"] == "input_json_delta":
                        content_blocks[idx]["content"] += delta["partial_json"]

        # Build final content array
        result = []
        for idx in sorted(content_blocks.keys()):
            block = content_blocks[idx]
            if block["type"] == "text":
                result.append({"type": "text", "text": block["content"]})
            elif block["type"] == "thinking":
                result.append({"type": "thinking", "thinking": block["content"]})
            elif block["type"] == "tool_use":
                try:
                    input_json = json.loads(block["content"]) if block["content"] else {}
                except json.JSONDecodeError:
                    input_json = {}
                result.append({
                    "type": "tool_use",
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": input_json,
                })
        return result if result else None


addons = [JSONRequestLogger()]

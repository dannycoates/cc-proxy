"""
SSE stream parser for Claude API responses.

Reconstructs the full message object from SSE events.
"""

import json
import os


def parse_sse_stream(body: bytes, include_signature: bool | None = None) -> dict | None:
    """Parse SSE stream and reconstruct message content.

    Handles raw response bodies that may include HTTP headers or
    chunked transfer encoding markers by skipping non-SSE lines.

    Args:
        body: Raw SSE response body as bytes
        include_signature: If True, include signature in thinking blocks.
            If None, checks CC_PROXY_INCLUDE_SIGNATURE env var. Default is False.

    Returns:
        Reconstructed message dict, or None if parsing fails
    """
    if include_signature is None:
        include_signature = os.environ.get("CC_PROXY_INCLUDE_SIGNATURE", "").lower() in (
            "1", "true", "yes"
        )

    content_blocks = {}  # index -> accumulated content
    message = None

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
            if current_event == "message_start":
                message = data["message"]
            elif current_event == "message_delta":
                if message:
                    delta = data.get("delta", {})
                    message.update(delta)
                    if "usage" in data:
                        message["usage"] = data["usage"]
            elif current_event == "content_block_start":
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
                elif delta["type"] == "signature_delta":
                    content_blocks[idx]["signature"] = content_blocks[idx].get(
                        "signature", ""
                    ) + delta["signature"]

    # Build final content array
    content = []
    for idx in sorted(content_blocks.keys()):
        block = content_blocks[idx]
        if block["type"] == "text":
            content.append({"type": "text", "text": block["content"]})
        elif block["type"] == "thinking":
            thinking_block = {"type": "thinking", "thinking": block["content"]}
            if block.get("signature") and include_signature:
                thinking_block["signature"] = block["signature"]
            content.append(thinking_block)
        elif block["type"] == "tool_use":
            try:
                input_json = json.loads(block["content"]) if block["content"] else {}
            except json.JSONDecodeError:
                input_json = {}
            content.append({
                "type": "tool_use",
                "id": block.get("id"),
                "name": block.get("name"),
                "input": input_json,
            })
    if message:
        message["content"] = content
        return message
    return None

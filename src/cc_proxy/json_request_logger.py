"""
Mitmproxy addon that logs Claude API request/response bodies.

Usage:
    mitmdump -s src/cc_proxy/json_request_logger.py
"""

import json

from mitmproxy import http

from cc_proxy.sse_parser import parse_sse_stream


class JSONRequestLogger:
    """
    Addon that intercepts HTTP requests/responses and outputs them wrapped:
    - Requests: {"request": <original_json_body>}
    - Responses: {"response": <message>} (parsed from SSE stream)
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

        content = parse_sse_stream(flow.response.content)
        if content:
            print(json.dumps({"response": content}), flush=True)


addons = [JSONRequestLogger()]

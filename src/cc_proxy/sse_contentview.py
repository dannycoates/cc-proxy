"""
Mitmproxy content view that reconstructs Claude API SSE streams as JSON.

Usage:
    mitmproxy -s src/cc_proxy/sse_contentview.py
"""

import json

from mitmproxy import contentviews

from cc_proxy.sse_parser import parse_sse_stream


class SSEMessageContentview(contentviews.Contentview):
    """
    Content view that parses SSE event streams from Claude API responses
    and displays them as reconstructed JSON message objects.
    """

    name = "SSE Message"
    syntax_highlight = "javascript"

    def prettify(self, data: bytes, metadata: contentviews.Metadata) -> str:
        message = parse_sse_stream(data)
        if message:
            return json.dumps(message, indent=2)
        return data.decode("utf-8", errors="replace")

    def render_priority(
        self, data: bytes, metadata: contentviews.Metadata
    ) -> float:
        if metadata.content_type and "text/event-stream" in metadata.content_type:
            return 2
        return 0


contentviews.add(SSEMessageContentview())

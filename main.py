
import hashlib
import re
from contextvars import ContextVar

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.transport_security import TransportSecuritySettings


EMAIL = "26ds1000025@ds.study.iitm.ac.in"

# Store headers separately for each active request
request_headers = ContextVar("request_headers", default={})


class HeaderMiddleware:
    """Capture HTTP request headers for the current request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        token = request_headers.set(headers)
        try:
            await self.app(scope, receive, send)
        finally:
            request_headers.reset(token)


mcp = FastMCP(
    "Live Exam MCP Server",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "mcp-server-ln6h.onrender.com",
            "mcp-server-ln6h.onrender.com:*",
        ],
    ),
)


@mcp.tool()
async def solve_challenge(ctx: Context) -> str:
    """Return the required hash for the challenge in the HTTP headers."""

    headers = request_headers.get()
    challenge = headers.get("x-exam-challenge", "")

    if not re.fullmatch(r"[0-9a-f]{32}", challenge):
        raise ValueError("Missing or invalid X-Exam-Challenge header")

    normalized_email = EMAIL.strip().lower()
    message = f"{challenge}:{normalized_email}"

    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
    return digest[:16]


# Create the MCP Streamable HTTP application
mcp_app = mcp.streamable_http_app()

# Wrap it to capture per-request HTTP headers
app = HeaderMiddleware(mcp_app)


import hashlib
import re

from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Live Exam MCP Server")

EMAIL = "26ds1000025@ds.study.iitm.ac.in"


@mcp.tool()
async def solve_challenge(ctx: Context) -> str:
    """Solve the exam challenge supplied in the HTTP request headers."""

    # Read headers from this individual MCP request
    headers = ctx.headers or {}

    challenge = headers.get("x-exam-challenge")

    # Reject missing or incorrectly formatted challenges
    if not challenge or not re.fullmatch(r"[0-9a-f]{32}", challenge):
        raise ValueError("Missing or invalid X-Exam-Challenge header")

    # Normalize the registered email
    normalized_email = EMAIL.strip().lower()

    # Calculate SHA-256 of challenge:email
    message = f"{challenge}:{normalized_email}"
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()

    # Return only the first 16 lowercase hexadecimal characters
    return digest[:16]


# Expose the MCP Streamable HTTP endpoint at /mcp
app = mcp.streamable_http_app()

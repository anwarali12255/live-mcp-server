import hashlib
import os
from contextvars import ContextVar

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

EMAIL = "24f2006704@ds.study.iitm.ac.in"

request_headers = ContextVar("request_headers", default={})

mcp = FastMCP(
    "Exam Challenge Server",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        allowed_hosts=[
            "live-mcp-server-1-fvb7.onrender.com",
            "live-mcp-server-1-fvb7.onrender.com:*",
        ],
        allowed_origins=[
            "https://live-mcp-server-1-fvb7.onrender.com",
        ],
    ),
)

class HeaderMiddleware:
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


@mcp.tool(structured_output=False)
def solve_challenge() -> str:
    """Solve the challenge provided in the current HTTP request headers."""
    headers = request_headers.get()
    challenge = headers.get("x-exam-challenge")

    if not challenge:
        raise ValueError("Missing X-Exam-Challenge header")

    message = f"{challenge}:{EMAIL}".encode("utf-8")
    return hashlib.sha256(message).hexdigest()[:16]


app = HeaderMiddleware(mcp.streamable_http_app())

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
    )

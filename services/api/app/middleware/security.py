"""Security headers and bounded request bodies, including chunked uploads."""

from tempfile import SpooledTemporaryFile

from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse

from app.core.config import settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "frame-ancestors 'none'; object-src 'none'; base-uri 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",
}


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secured_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for key, value in SECURITY_HEADERS.items():
                    headers.setdefault(key, value)
                if scope["path"].startswith("/api/"):
                    headers["Cache-Control"] = "private, no-store"
                if scope.get("scheme") == "https":
                    headers["Strict-Transport-Security"] = "max-age=31536000"
            await send(message)

        if scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, secured_send)
        limit = settings.MAX_UPLOAD_BYTES + 64 * 1024 if scope["path"].rstrip("/") == "/api/v1/evidence" else 1024 * 1024
        headers = Headers(scope=scope)
        try:
            declared_size = int(headers.get("content-length", "0"))
            if declared_size < 0:
                raise ValueError
        except ValueError:
            return await JSONResponse({"detail": "Invalid Content-Length"}, 400)(scope, receive, secured_send)
        if declared_size > limit:
            return await JSONResponse({"detail": "Request body exceeds the size limit"}, 413)(scope, receive, secured_send)

        # Spool before multipart/JSON parsing; never hold an unbounded request in memory.
        with SpooledTemporaryFile(max_size=1024 * 1024) as body:
            total = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                total += len(chunk)
                if total > limit:
                    return await JSONResponse({"detail": "Request body exceeds the size limit"}, 413)(scope, receive, secured_send)
                await run_in_threadpool(body.write, chunk)
                if not message.get("more_body", False):
                    break
            await run_in_threadpool(body.seek, 0)
            sent = 0
            finished = False

            async def replay():
                nonlocal sent, finished
                if finished:
                    return await receive()
                chunk = await run_in_threadpool(body.read, 64 * 1024)
                sent += len(chunk)
                finished = sent >= total
                return {"type": "http.request", "body": chunk, "more_body": not finished}

            await self.app(scope, replay, secured_send)

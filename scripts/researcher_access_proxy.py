"""Loopback-only static host and same-origin API proxy for controlled research access."""

from __future__ import annotations

import argparse
import json
import mimetypes
import uuid
from http.client import HTTPConnection, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


MAX_RESPONSE_BYTES = 8 * 1024 * 1024
PROXY_PREFIXES = ("/api/",)
PROXY_EXACT_PATHS = {"/healthz", "/readyz"}
FORWARDED_REQUEST_HEADERS = {"accept", "authorization", "content-type", "idempotency-key"}
FORWARDED_RESPONSE_HEADERS = {"content-type", "cache-control", "etag", "last-modified"}


def is_proxy_path(path: str) -> bool:
    normalized = urlsplit(path).path
    return normalized in PROXY_EXACT_PATHS or normalized.startswith(PROXY_PREFIXES)


def resolve_static_path(web_root: Path, request_path: str) -> Path | None:
    raw = unquote(urlsplit(request_path).path)
    parts = [part for part in raw.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        return None
    root = web_root.resolve()
    candidate = root.joinpath(*parts).resolve()
    if root != candidate and root not in candidate.parents:
        return None
    if candidate.is_file():
        return candidate
    if not Path(raw).suffix:
        index = root / "index.html"
        return index if index.is_file() else None
    return None


def security_headers() -> dict[str, str]:
    return {
        "Content-Security-Policy": (
            "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cache-Control": "no-store",
    }


class ResearchAccessHandler(BaseHTTPRequestHandler):
    web_root = Path("apps/web/dist")
    api_base_url = "http://127.0.0.1:5050"
    max_request_bytes = 1024 * 1024

    def do_GET(self):  # noqa: N802
        self._dispatch()

    def do_HEAD(self):  # noqa: N802
        self._dispatch()

    def do_POST(self):  # noqa: N802
        self._dispatch()

    def do_PATCH(self):  # noqa: N802
        self._dispatch()

    def do_PUT(self):  # noqa: N802
        self._dispatch()

    def do_DELETE(self):  # noqa: N802
        self._dispatch()

    def do_OPTIONS(self):  # noqa: N802
        self._dispatch()

    def _dispatch(self) -> None:
        if is_proxy_path(self.path):
            self._proxy_api()
        elif self.command in {"GET", "HEAD"}:
            self._serve_static()
        else:
            self._json_error(404, "not_found", "没有找到该入口")

    def _serve_static(self) -> None:
        target = resolve_static_path(self.web_root, self.path)
        if target is None:
            self._json_error(404, "not_found", "没有找到该页面")
            return
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        for key, value in security_headers().items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _proxy_api(self) -> None:
        request_id = uuid.uuid4().hex
        length = int(self.headers.get("Content-Length") or 0)
        if length < 0 or length > self.max_request_bytes:
            self._json_error(413, "request_too_large", "请求内容过大", request_id)
            return
        body = self.rfile.read(length) if length else None
        target = urlsplit(self.api_base_url)
        connection_cls = HTTPSConnection if target.scheme == "https" else HTTPConnection
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() in FORWARDED_REQUEST_HEADERS
        }
        headers["X-Request-ID"] = request_id
        connection = connection_cls(target.hostname, target.port, timeout=20)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(response_body) > MAX_RESPONSE_BYTES:
                self._json_error(502, "upstream_response_too_large", "服务响应超出安全限制", request_id)
                return
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() in FORWARDED_RESPONSE_HEADERS:
                    self.send_header(key, value)
            for key, value in security_headers().items():
                self.send_header(key, value)
            self.send_header("X-Request-ID", request_id)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except (OSError, TimeoutError):
            self._json_error(502, "upstream_unavailable", "服务暂时不可用，请稍后重试", request_id)
        finally:
            connection.close()

    def _json_error(self, status: int, code: str, message: str, request_id: str | None = None) -> None:
        safe_request_id = request_id or uuid.uuid4().hex
        body = json.dumps(
            {"ok": False, "error": {"code": code, "message": message, "request_id": safe_request_id}},
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for key, value in security_headers().items():
            self.send_header(key, value)
        self.send_header("X-Request-ID", safe_request_id)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        # Do not write paths, tokens or participant content to ordinary stdout logs.
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="SafeHome controlled loopback reverse proxy")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--api-base-url", default="http://127.0.0.1:5050")
    parser.add_argument("--max-request-bytes", type=int, default=1024 * 1024)
    args = parser.parse_args()
    if args.listen_host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("研究者访问代理只允许监听loopback")
    if not (args.web_root / "index.html").is_file():
        raise SystemExit("Web构建产物不存在")
    ResearchAccessHandler.web_root = args.web_root.resolve()
    ResearchAccessHandler.api_base_url = args.api_base_url
    ResearchAccessHandler.max_request_bytes = args.max_request_bytes
    ThreadingHTTPServer((args.listen_host, args.port), ResearchAccessHandler).serve_forever()


if __name__ == "__main__":
    main()

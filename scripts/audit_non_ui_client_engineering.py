"""Non-UI client engineering guard for Web and WeChat mini-program transports."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_AUTH = ROOT / "apps" / "web" / "src" / "services" / "authState.ts"
MINIPROGRAM = ROOT / "apps" / "miniprogram"
ALLOWED_CONTAINER_CALLERS = {
    "services/api.js",
    "pages/debug/index.js",
}


def main() -> int:
    failures: list[str] = []

    auth = WEB_AUTH.read_text(encoding="utf-8")
    if "window.sessionStorage.setItem(AUTH_TOKEN_KEY" not in auth:
        failures.append("Web bearer token is no longer saved to sessionStorage")
    if "window.localStorage.setItem(AUTH_TOKEN_KEY" in auth:
        failures.append("Web bearer token must not be persisted with localStorage.setItem")
    if "window.localStorage.removeItem(AUTH_TOKEN_KEY" not in auth:
        failures.append("Web legacy localStorage token cleanup is missing")

    direct_callers = []
    for path in MINIPROGRAM.rglob("*.js"):
        if "wx.cloud.callContainer" not in path.read_text(encoding="utf-8", errors="ignore"):
            continue
        relative = path.relative_to(MINIPROGRAM).as_posix()
        if relative not in ALLOWED_CONTAINER_CALLERS:
            direct_callers.append(relative)
    if direct_callers:
        failures.append(
            "Mini-program CloudBase calls must use services/api.js; unexpected callers: "
            + ", ".join(sorted(direct_callers))
        )

    api_source = (MINIPROGRAM / "services" / "api.js").read_text(encoding="utf-8")
    for required in ["X-Request-ID", "Authorization", "normalizeApiError", "callContainer"]:
        if required not in api_source:
            failures.append(f"Mini-program central transport missing invariant: {required}")

    if failures:
        print("Non-UI client engineering audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Non-UI client engineering audit passed: Web session auth + centralized mini-program transport")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

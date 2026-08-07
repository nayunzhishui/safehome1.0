"""Non-UI client engineering guard for Web and WeChat mini-program transports."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_AUTH = ROOT / "apps" / "web" / "src" / "services" / "authState.ts"
MINIPROGRAM = ROOT / "apps" / "miniprogram"
# api.js is the primary transport. minorSafeguardsApi.js is an inherited,
# intentionally narrow safety transport kept separate until the large api.js
# can be refactored safely; CI enforces the same request/auth/error invariants.
ALLOWED_CONTAINER_CALLERS = {
    "services/api.js",
    "services/minorSafeguardsApi.js",
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
            "Mini-program CloudBase calls must stay inside reviewed transport modules; unexpected callers: "
            + ", ".join(sorted(direct_callers))
        )

    transport_invariants = {
        "services/api.js": ["X-Request-ID", "Authorization", "normalizeApiError", "callContainer"],
        "services/minorSafeguardsApi.js": ["X-Request-ID", "Authorization", "normalizeError", "callContainer", "clearAuthSession"],
    }
    for relative, required_values in transport_invariants.items():
        source = (MINIPROGRAM / relative).read_text(encoding="utf-8")
        for required in required_values:
            if required not in source:
                failures.append(f"Mini-program transport {relative} missing invariant: {required}")

    if failures:
        print("Non-UI client engineering audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "Non-UI client engineering audit passed: Web session auth + "
        "reviewed mini-program transport allowlist/invariants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

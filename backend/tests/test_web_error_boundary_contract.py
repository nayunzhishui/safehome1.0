"""Web顶层错误恢复静态契约。"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_web_root_uses_error_boundary_and_bounded_lazy_recovery():
    main = (ROOT / "apps" / "web" / "src" / "main.tsx").read_text(encoding="utf-8")
    boundary = (ROOT / "apps" / "web" / "src" / "components" / "ErrorBoundary.tsx").read_text(encoding="utf-8")

    assert "lazyWithRetry as lazy" in main
    assert "<ErrorBoundary>" in main
    assert "sessionStorage" in boundary
    assert '!== "1"' in boundary
    assert "window.location.reload()" in boundary
    assert "error.message" not in boundary
    assert "componentStack" not in boundary
    assert "重新加载" in boundary

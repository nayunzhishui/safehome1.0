"""Static acceptance audit for T36-F14 synthetic-only online analysis."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    service = (ROOT / "backend/services/research_online_analysis_service.py").read_text(encoding="utf-8")
    route = (ROOT / "backend/routes/research_analysis.py").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/pages/ResearchAnalysisWorkbench.tsx").read_text(encoding="utf-8")
    mini = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")
    checks = {
        "real_data_blocked": "real_participant_analysis_blocked" in service,
        "small_sample_suppressed": "small_sample_suppressed" in service,
        "graph_limits": "MAX_GRAPH_NODES" in service and "MAX_GRAPH_EDGES" in service,
        "catalog_route": 'bp.get("/catalog")' in route,
        "synthetic_execute_route": 'bp.post("/jobs/<job_id>/execute-synthetic")' in route,
        "web_gate_visible": "真实参与者处理关闭" in web,
        "mini_gate_visible": "真实参与者分析关闭" in mini,
        "non_diagnostic_boundary": "BOUNDARY_NOTICE" in service,
    }
    failed = [key for key, value in checks.items() if not value]
    print({"checks": checks, "failed": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

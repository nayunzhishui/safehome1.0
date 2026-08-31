import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _wechat_login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_research_workspace_lists_and_reads_multi_module_participant(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "research-matrix-user")
    diary = client.post(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scene": "亲子沟通",
            "event_description": "我先停下来听完，再说自己的担心。",
            "parent_emotion": "着急",
        },
    )
    assert diary.status_code == 201
    program = client.post(
        "/api/programs/self_compassion_exam_anxiety/entries",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_no": 1, "reflection": "我愿意先完成一个小步骤。", "recommendation_source": "user_choice"},
    )
    assert program.status_code == 201

    matrix = client.get(f"/api/research/participants?q={user_id}", headers=ADMIN_HEADERS)
    assert matrix.status_code == 200
    data = matrix.get_json()["data"]
    assert data["count"] == 1
    assert data["items"][0]["user_id"] == user_id
    assert data["items"][0]["diary_count"] == 1
    assert data["items"][0]["program_count"] == 1

    dossier = client.get(f"/api/research/participants/{user_id}", headers=ADMIN_HEADERS)
    assert dossier.status_code == 200
    detail = dossier.get_json()["data"]
    assert detail["participant"]["user_id"] == user_id
    assert detail["participant"]["anonymous_id"].startswith("anon_")
    assert next(item for item in detail["modules"] if item["key"] == "diaries")["count"] == 1
    assert "contact" not in detail["participant"]

    diaries = client.get(f"/api/research/participants/{user_id}/modules/diaries?page=1&page_size=10", headers=ADMIN_HEADERS)
    assert diaries.status_code == 200
    assert diaries.get_json()["data"]["items"][0]["event_description"]

    projects = client.get(f"/api/research/participants/{user_id}/modules/project_tests?page=1&page_size=10", headers=ADMIN_HEADERS)
    assert projects.status_code == 200
    assert projects.get_json()["data"]["items"][0]["reflection"]
    assert "原始填写" in detail["boundary_notice"]


def test_research_workspace_requires_research_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.get("/api/research/participants").status_code == 401


def test_researcher_dossier_exposes_participant_exploratory_analysis(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    user_id, token = _wechat_login(client, "research-participant-analysis")
    for index, (scene, emotion) in enumerate(
        [
            ("亲子沟通", "着急"),
            ("亲子沟通", "着急"),
            ("作业拖延", "担心"),
            ("作业拖延", "担心"),
            ("亲子沟通", "担心"),
        ]
    ):
        response = client.post(
            "/api/diaries",
            headers={"Authorization": f"Bearer {token}"},
            json={"scene": scene, "event_description": f"记录{index}", "parent_emotion": emotion},
        )
        assert response.status_code == 201

    dossier = client.get(f"/api/research/participants/{user_id}", headers=ADMIN_HEADERS)
    assert dossier.status_code == 200
    analysis_tab = next(
        item for item in dossier.get_json()["data"]["modules"] if item["key"] == "exploratory_analysis"
    )
    assert analysis_tab["label"] == "情绪与互动线索"
    assert analysis_tab["count"] == 1

    module = client.get(
        f"/api/research/participants/{user_id}/modules/exploratory_analysis",
        headers=ADMIN_HEADERS,
    )
    assert module.status_code == 200
    data = module.get_json()["data"]
    assert data["items"][0]["availability"] == "available"
    assert data["items"][0]["raw_text_included"] is False
    assert data["items"][0]["other_participant_data_included"] is False


def test_researcher_miniprogram_renders_affect_and_network_analysis_module():
    script = (PROJECT_ROOT / "apps/miniprogram/pages/researcher-dashboard/index.js").read_text(encoding="utf-8")
    markup = (PROJECT_ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")

    assert "safehome.participant-exploratory-analysis.v1" in script
    assert "record.exploratoryAnalysis" in markup
    assert "情感计算" in markup
    assert "场景—情绪网络" in markup


def test_researcher_miniprogram_opens_read_only_knowledge_and_network_benchmark_views():
    script = (PROJECT_ROOT / "apps/miniprogram/pages/researcher-dashboard/index.js").read_text(encoding="utf-8")
    markup = (PROJECT_ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")
    api = (PROJECT_ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")

    assert "getAiKnowledgeInventory" in script
    assert "retrieveAiKnowledge" in script
    assert "searchKnowledge" in markup
    assert "已审核知识库" in markup
    assert "listOfflineBenchmarkRuns" in api
    assert "网络分析基准" in markup
    assert "networkPolicy" in script
    assert "offlineBenchmarkRuns" in script

    registry = json.loads((PROJECT_ROOT / "content/researcher_capability_registry.json").read_text(encoding="utf-8"))
    analysis_capability = next(item for item in registry["capabilities"] if item["id"] == "research.analysis.read")
    assert "GET /api/ai-qa/knowledge/retrieve" in analysis_capability["operations"]
    assert "GET /api/research/benchmarks/runs" in analysis_capability["operations"]


def test_researcher_analysis_workspace_has_explicit_content_sections():
    markup = (PROJECT_ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")

    assert "研究者分析工作台" in markup
    assert "analysis-section--status" in markup
    assert "analysis-section--evidence" in markup
    assert "analysis-section--quality" in markup
    assert "analysis-section--tasks" in markup
    assert "运行护栏" in markup
    assert "已审核资料" in markup
    assert "模型质量" in markup
    assert "任务明细" in markup
    assert markup.index("analysis-section--status") < markup.index("analysis-section--evidence")
    assert markup.index("analysis-section--evidence") < markup.index("analysis-section--quality")
    assert markup.index("analysis-section--quality") < markup.index("analysis-section--tasks")


def test_researcher_analysis_workspace_omits_redundant_static_explanations():
    markup = (PROJECT_ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")

    assert "移动端只读查看任务、证据和聚合质量" not in markup
    assert "先确认数据与模型处于什么状态" not in markup
    assert "查找可追溯的证据来源" not in markup
    assert "核对合成基准与隐私阈值" not in markup
    assert "查看在线分析任务状态" not in markup
    assert "治疗性评估请进入“评估证据”工作区" not in markup
    assert "输入停止 350 毫秒后搜索" not in markup
    assert "幂等执行 · 租约并发 · 失败可恢复" not in markup

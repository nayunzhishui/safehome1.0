import importlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
VOCABULARY = json.loads((ROOT / "content/emotion_vocabulary.json").read_text(encoding="utf-8"))


def _vocabulary():
    sys.path.insert(0, str(BACKEND))
    from services.emotion_vocabulary_service import EmotionVocabulary

    return EmotionVocabulary(VOCABULARY)


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "emotion-vocabulary.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def test_vocabulary_follows_the_annotation_ontology_and_awaits_expert_review():
    ontology = json.loads((ROOT / "content/emotion_annotation_ontology.json").read_text(encoding="utf-8"))
    codes = {item["code"] for item in VOCABULARY["categories"]} | {VOCABULARY["unknown"]["code"]}
    assert codes == {item["code"] for item in ontology["emotion_labels"]}
    assert {"calm", "positive"} <= {item["code"] for item in VOCABULARY["categories"]}
    for key in ("parent_words", "child_words"):
        words = [word for item in VOCABULARY["categories"] for word in item[key]]
        assert len(words) == len(set(words))
    assert len([word for item in VOCABULARY["categories"] for word in item["parent_words"]]) >= 30
    body = [word for region in VOCABULARY["body_regions"] for word in region["words"]]
    assert len(body) == len(set(body)) >= 14
    assert VOCABULARY["max_selected"] == 3
    assert VOCABULARY["review_status"] == "engineering_complete_expert_review_pending"


def test_stored_emotions_parse_new_typed_and_old_records():
    vocabulary = _vocabulary()
    entries = vocabulary.parse("着急、憋屈（难过失望）、开心")
    assert [(item.word, item.label, item.custom) for item in entries] == [
        ("着急", "担心焦虑", False),
        ("憋屈", "难过失望", True),
        ("开心", "开心欣慰", False),
    ]
    assert vocabulary.primary_label("失望") == "难过失望"
    assert vocabulary.primary_label("沉默", "child") == "说不清"
    assert vocabulary.primary_label("词表里没有的词") == "说不清"
    assert vocabulary.primary_label(None) == ""
    assert vocabulary.labels("着急、担心、失望") == ["担心焦虑", "难过失望"]
    assert vocabulary.display("着急、憋屈（难过失望）") == "着急、憋屈"
    assert vocabulary.count_words(["着急、担心", "着急", None]) == Counter({"着急": 2, "担心": 1})


def test_validation_allows_three_emotions_and_needs_a_category_for_typed_words():
    vocabulary = _vocabulary()
    assert vocabulary.validation_error("着急、担心、憋屈（难过失望）") is None
    assert vocabulary.validation_error("焦虑") is None
    assert "最多选 3 个" in vocabulary.validation_error("着急、担心、失望、内疚")
    assert "类别" in vocabulary.validation_error("憋屈（不存在的类）")
    assert "8 个字" in vocabulary.validation_error("一二三四五六七八九（难过失望）")


def test_diary_endpoint_saves_multiple_emotions_and_rejects_a_fourth(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    login = client.post("/api/auth/wechat-login", json={"code": "emotion-vocabulary-parent"}).get_json()["data"]
    headers = {"Authorization": f"Bearer {login['token']}"}
    base = {"scene": "亲子沟通", "event_description": "合成记录", "parent_emotion_intensity": 6}

    rejected = client.post("/api/diaries", headers=headers, json={**base, "parent_emotion": "着急、担心、失望、内疚"})
    assert rejected.status_code == 400
    assert rejected.get_json()["error"]["details"]["field"] == "parent_emotion"
    saved = client.post(
        "/api/diaries",
        headers=headers,
        json={
            **base,
            "parent_emotion": "着急、憋屈（难过失望）",
            "child_emotion": "看不出来",
            "body_sensation": "胸口紧、心跳快：合成补充",
        },
    )
    assert saved.status_code == 201
    assert saved.get_json()["data"]["parent_emotion"] == "着急、憋屈（难过失望）"


def test_body_alarm_rule_covers_the_tension_words_offered_on_the_form():
    rules = json.loads((ROOT / "content/feedback_rules.json").read_text(encoding="utf-8"))["rules"]
    keywords = set(next(rule for rule in rules if rule["id"] == "parent_body_alarm")["match_keywords"])
    assert {"胸口紧", "心跳快", "呼吸急", "头胀", "肩膀紧", "喉咙发紧", "手发抖"} <= keywords
    assert "没力气" not in keywords and "说不清" not in keywords


def test_generated_miniprogram_vocabulary_is_current():
    spec = importlib.util.spec_from_file_location(
        "generate_emotion_vocabulary", BACKEND / "scripts" / "generate_emotion_vocabulary.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for path, content in module.outputs().items():
        assert path.read_text(encoding="utf-8") == content

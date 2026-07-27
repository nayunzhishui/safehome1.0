"""AI问答安全骨架回归；真实供应商和参与者入口仍保持关闭。"""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_prompt_template_is_a_real_entity_with_role_limits():
    from services.ai_qa_prompt import PROMPT_TEMPLATE_VERSION, build_system_prompt, build_user_prompt

    assert PROMPT_TEMPLATE_VERSION
    assert "不得" in build_system_prompt()
    assert "[S1]" in build_user_prompt(
        "我该怎么记录",
        [{"title": "记录卡", "excerpt": "先写清具体事件。"}],
    )


def test_conclusion_language_and_invalid_citation_are_blocked():
    from services.ai_qa_prompt import contains_conclusion, validate_output

    assert contains_conclusion("你符合抑郁发作的标准")
    assert contains_conclusion("这属于典型的回避型依恋")
    assert contains_conclusion("you have depression")
    assert not contains_conclusion("先记录具体事件，选一个小步骤")
    result = validate_output(
        "[S9] 先写清具体事件。",
        [{"title": "记录卡", "excerpt": "先写清具体事件。"}],
    )
    assert "invalid_citation_marker" in result["violations"]


def test_grounding_degrades_unrelated_answer():
    from services.ai_qa_safety_service import post_check

    citations = [{"title": "记录卡", "excerpt": "先写清具体事件，再选一个低负担、可暂停的小步骤。"}]
    check = post_check("[S1] 宇宙飞船在木星轨道加速时会产生潮汐现象。", citations)
    assert not check["ok"]
    assert "low_grounding" in check["violations"]
    assert check["grounding_method"] == "lexical_overlap_heuristic_v1"


def test_fake_provider_is_grounded_costed_and_has_hard_timeout_contract():
    from services.ai_qa_provider import FakeProvider
    from services.ai_qa_safety_service import post_check

    citations = [{"title": "记录卡", "excerpt": "先写清具体事件，再选一个低负担、可暂停的小步骤。"}]
    provider = FakeProvider()
    result = provider.generate("我该怎么记录", citations, timeout_seconds=0.1)
    assert provider.supports_hard_timeout
    assert post_check(result.text, citations)["ok"]
    assert result.cost_micros > 0
    assert result.token_estimate > 0

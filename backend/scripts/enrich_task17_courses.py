"""Idempotently upgrade Task 17 courses into structured learning units."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COURSES_PATH = PROJECT_ROOT / "content" / "courses.json"

COURSE_UPDATES = {
    "understand_child_emotion": {
        "curriculum_node": "emotion_reflex_arc",
        "learning_objectives": ["区分可观察行为、可能的情绪和仍需询问的信息", "先用一句确认感受，再讨论规则或下一步"],
        "core_concept": "先描述事实并确认感受，不急着给孩子下结论。",
        "common_misconceptions": [
            {"statement": "确认感受就是同意孩子的行为。", "correction": "确认的是当下感受，行为边界仍可在情绪稍稳后讨论。"}
        ],
        "worked_example": "孩子摔下书包说不想学。家长先说：我看到你进门后很用力放下书包，今天可能很累。你想先安静两分钟，还是告诉我最难的是哪一段？",
        "counter_example": "你每次都这样，一遇到困难就逃避。这个说法把一次行为变成固定评价，也没有确认孩子当前需要。",
        "knowledge_checks": [{"id": "emotion_fact_check", "prompt": "哪句话最接近先描述事实、再确认感受？", "options": [{"value": "label", "label": "你就是不负责任"}, {"value": "observe", "label": "我看到你把书放下后一直没说话，今天是不是有点累？"}], "correct_value": "observe", "feedback_correct": "这句话先描述看到的情况，并为孩子留下确认或修正的空间。", "feedback_incorrect": "固定评价容易增加防御。先说看到的事实，再提出一个可回答的问题。"}],
        "guided_practice": {"card_id": "emotion_naming", "instruction": "回想一次最近的互动，只写一个事实、一个可能的情绪和一个开放问题。"},
        "transfer_task": "未来一周选择一次低强度互动，先说观察和感受，再决定是否讨论规则。",
        "reflection_prompts": ["我把哪句评价改成了观察？", "孩子是否有机会修正我的猜测？"],
        "booster_plan": {"review_after_days": 7, "prompt": "一周后回看：哪一种开场最容易让对话继续？", "next_course_id": "nonjudgmental_companion"},
        "audience_adaptation": {"primary": "parent", "parent": "使用亲子日常场景，强调成人先调节回应。", "student": "学生版只用于理解自己的情绪表达，不要求承担家长责任。", "adult": "成人可替换为同事或家人互动场景。"},
    },
    "parent_emotion_regulation_intro": {
        "curriculum_node": "body_signals",
        "learning_objectives": ["识别一个属于自己的情绪升高身体信号", "在开口前完成一次短暂停顿"],
        "core_concept": "暂停不是压抑情绪，而是为回应增加一个可选择的间隔。",
        "common_misconceptions": [{"statement": "暂停就是忍住不说，直到情绪消失。", "correction": "暂停是先注意身体和情绪，再选择更安全、具体的表达。"}],
        "worked_example": "发现声音变大、肩膀发紧时，先让双脚踩地并慢呼气三次，再说：我现在有点急，想慢一点把这件事说清楚。",
        "counter_example": "强迫自己完全不许生气，同时继续提高音量讲道理。这样既没有照顾身体信号，也没有增加选择空间。",
        "knowledge_checks": [{"id": "pause_check", "prompt": "哪一种做法更接近有效暂停？", "options": [{"value": "suppress", "label": "不准自己有情绪，继续把道理讲完"}, {"value": "notice", "label": "注意到肩膀紧，慢呼气后再说第一句话"}], "correct_value": "notice", "feedback_correct": "先识别身体信号，再降低回应速度，能为下一步增加选择。", "feedback_incorrect": "压住感受不等于调节。先识别一个信号，再完成一个短暂停顿。"}],
        "guided_practice": {"card_id": "parent_body_grounding", "instruction": "现在找一个身体接触点，慢呼气三次，并写下准备降低音量说的第一句话。"},
        "transfer_task": "下一次低强度着急时，先识别身体信号，再决定继续说、稍后说或寻求帮助。",
        "reflection_prompts": ["我最早注意到的身体信号是什么？", "暂停后第一句话有什么变化？"],
        "booster_plan": {"review_after_days": 7, "prompt": "一周后回看：哪个身体信号最适合作为暂停提醒？", "next_course_id": "nonjudgmental_companion"},
        "audience_adaptation": {"primary": "parent", "parent": "聚焦家长在亲子互动中的自我调节。", "student": "学生版不使用管教语境，只练习学习或同伴互动前暂停。", "adult": "成人版可用于工作或家庭冲突前降速。"},
    },
    "nonjudgmental_companion": {
        "curriculum_node": "cognitive_flexibility",
        "learning_objectives": ["把一个判断句改写为观察句", "理解确认感受与同意行为之间的区别"],
        "core_concept": "少一点固定判断，多保留一种可能和一次询问。",
        "common_misconceptions": [{"statement": "只要语气温柔，评价孩子也没有关系。", "correction": "温柔语气仍可能包含固定标签；重点是回到具体行为、影响和需要。"}],
        "worked_example": "把“你怎么这么懒”改为“我看到作业打开十分钟还没开始，哪一步最难进入？”",
        "counter_example": "你虽然不是故意的，但总是让人失望。这句话仍然把行为扩展为整体评价。",
        "knowledge_checks": [{"id": "judgment_check", "prompt": "哪句话保留了更多理解空间？", "options": [{"value": "fixed", "label": "你就是不在乎"}, {"value": "open", "label": "我看到消息一直没有回复，刚才发生了什么？"}], "correct_value": "open", "feedback_correct": "这句话描述具体情况，并允许对方补充信息。", "feedback_incorrect": "固定判断会缩小对话空间。先描述具体情况，再问一个问题。"}],
        "guided_practice": {"card_id": "nonjudgmental_response", "instruction": "写下一句最近说过的评价，把它改成事实、感受和一个小请求。"},
        "transfer_task": "本周选择一次低风险沟通，先使用观察句和一个开放问题，不连续追问。",
        "reflection_prompts": ["我删掉了哪个固定标签？", "对方补充了什么我原先不知道的信息？"],
        "booster_plan": {"review_after_days": 7, "prompt": "一周后回看：哪一句观察最容易说出口？", "next_course_id": "repair_after_conflict_course"},
        "audience_adaptation": {"primary": "parent", "parent": "避免用固定特征解释孩子。", "student": "可用于同伴或自我对话，避免把一次失败等同于整个人。", "adult": "可用于伴侣、家人或同事沟通。"},
    },
    "repair_after_conflict_course": {
        "curriculum_node": "relationship_repair",
        "learning_objectives": ["在安全前提下区分恢复连接与立即解决问题", "使用一句承担自己部分责任的修复开场"],
        "core_concept": "修复先恢复一点安全和可对话空间，不要求立刻达成一致。",
        "common_misconceptions": [{"statement": "只要先道歉，对方就应该马上原谅。", "correction": "修复不是交换条件；对方可以需要时间，也可以拒绝当下继续对话。"}],
        "worked_example": "刚才我声音很大，让对话更难继续。这部分是我的责任。我想重新说一次；你现在不想谈也可以，我们可以晚些时候再决定。",
        "counter_example": "我都道歉了，你还想怎么样？这句话要求对方立即接受，没有给出安全和选择空间。",
        "knowledge_checks": [{"id": "repair_safety_check", "prompt": "哪种情况不适合直接进行共同修复练习？", "options": [{"value": "calm", "label": "双方已经降温，可以选择稍后谈"}, {"value": "unsafe", "label": "存在威胁、暴力、胁迫或明显报复风险"}], "correct_value": "unsafe", "feedback_correct": "现实安全优先。存在威胁、暴力或胁迫时，应停止共同练习并寻求现实支持。", "feedback_incorrect": "共同修复只适合基本安全、双方可自由选择的情境。"}],
        "guided_practice": {"card_id": "parent_after_conflict_repair", "instruction": "只写一句承担自己部分责任的话，不要求对方立即回应。"},
        "transfer_task": "仅在双方基本安全且冲突已经降温时，尝试一次简短修复；不安全时跳过并寻求支持。",
        "reflection_prompts": ["我承担了哪一部分，而没有把责任推回对方？", "我是否允许对方选择时间和方式？"],
        "booster_plan": {"review_after_days": 7, "prompt": "一周后回看：修复前需要满足哪些安全条件？", "next_course_id": None},
        "audience_adaptation": {"primary": "parent", "parent": "成人负责自己的语气和行为，不要求孩子照顾成人情绪。", "student": "学生不承担修复家庭关系的主要责任，可选择可信成年人支持。", "adult": "伴侣或成人关系中必须保留拒绝、暂停和退出权。"},
    },
    "exam_pressure_communication": {
        "curriculum_node": "behavior_and_avoidance",
        "learning_objectives": ["区分任务困难、结果担心、比较压力和不确定感", "把一个笼统要求改成十分钟内可开始的小动作"],
        "core_concept": "先找到卡住的位置，再共同选择一个足够小的开始动作。",
        "common_misconceptions": [{"statement": "压力大时多催几次能帮助孩子行动。", "correction": "重复催促可能增加威胁感；先确认卡点，再讨论一个可完成的小动作。"}],
        "worked_example": "家长问：现在最卡的是不知道做什么，还是担心做不好？学生选择担心做不好。双方约定先用十分钟只标出不会的题，不要求全部完成。",
        "counter_example": "别人都在努力，你必须今晚全部补完。这句话增加比较和一次性要求，没有识别具体卡点。",
        "knowledge_checks": [{"id": "exam_micro_action", "prompt": "哪个目标更适合作为今天的最小开始？", "options": [{"value": "all", "label": "今晚彻底解决所有薄弱科目"}, {"value": "small", "label": "用十分钟标出三道最不确定的题"}], "correct_value": "small", "feedback_correct": "目标具体、短时且可观察，更容易用于开始和复盘。", "feedback_incorrect": "一次解决全部问题通常过大。把动作缩小到十分钟内可开始。"}],
        "guided_practice": {"card_id": "exam_micro_start", "instruction": "选择一个十分钟内能开始的动作，写清开始时间、材料和停止点。"},
        "transfer_task": "下一次考试压力升高时，先问卡点，再共同选择一个十分钟动作；完成后只复盘过程。",
        "reflection_prompts": ["这次压力主要来自哪一种卡点？", "最小动作是否真的能在十分钟内开始？"],
        "booster_plan": {"review_after_days": 7, "prompt": "一周后回看：哪些小动作帮助开始，哪些仍然太大？", "next_course_id": None},
        "audience_adaptation": {"primary": "parent_student", "parent": "以询问和共同选择替代比较与命令。", "student": "保留自主选择和拒绝当下讨论的权利。", "adult": "可替换为工作任务或资格考试场景。"},
    },
}

PATHWAYS = [
    {
        "id": "up_supportive_path_v1",
        "title": "从看见情绪到巩固练习",
        "audiences": ["parent", "student", "adult"],
        "review_status": "draft_requires_psychology_review",
        "boundary_notice": "这条路径用于支持性心理教育和练习选择，不构成诊断或治疗方案。",
        "nodes": [
            {"code": "emotion_reflex_arc", "title": "理解情绪反射弧", "course_ids": ["understand_child_emotion"], "status": "content_available"},
            {"code": "emotion_awareness", "title": "觉察情绪与身体信号", "course_ids": ["parent_emotion_regulation_intro"], "status": "content_available"},
            {"code": "cognitive_flexibility", "title": "保留第二种理解", "course_ids": ["nonjudgmental_companion"], "status": "content_available"},
            {"code": "behavior_and_avoidance", "title": "把回避变成小行动", "course_ids": ["exam_pressure_communication"], "status": "content_available"},
            {"code": "body_signals", "title": "照顾身体压力信号", "course_ids": ["parent_emotion_regulation_intro", "exam_pressure_communication"], "status": "content_available"},
            {"code": "relationship_repair", "title": "安全前提下的沟通与修复", "course_ids": ["repair_after_conflict_course"], "status": "content_available"},
            {"code": "maintenance", "title": "巩固与复发预防", "course_ids": [], "status": "content_gap_requires_review"},
        ],
        "excluded_from_automatic_release": ["exposure", "interoceptive_exposure", "sleep_restriction"],
    }
]


def main() -> int:
    payload = json.loads(COURSES_PATH.read_text(encoding="utf-8"))
    if payload.get("version") == "2026.07-course-v1":
        payload["version"] = "2026.07-task17-course-v2"
    payload.setdefault("updated_at", "2026-07-11")
    payload.setdefault("pathways", PATHWAYS)
    for course in payload.get("courses", []):
        for key, value in COURSE_UPDATES[course["id"]].items():
            course.setdefault(key, value)
        course.setdefault("review_status", "draft_requires_psychology_review")
    COURSES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Task 17 courses enriched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

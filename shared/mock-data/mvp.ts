import type {
  Checkin,
  EmotionDiary,
  FeedbackResult,
  Goal,
  SupervisionRequest,
  TrainingCard,
  WeeklyReport,
} from "../types/api";

import { MOCK_USER_ID } from "../constants/api";

export const mockGoal: Goal = {
  id: "goal_mock_001",
  user_id: MOCK_USER_ID,
  scene: "作业拖延",
  smart_goal: "本周在孩子开始作业前，先用一句观察句替代催促。",
  motivation: "减少晚上作业时的冲突。",
  start_date: "2026-05-20",
  status: "active",
  created_at: "2026-05-20T10:00:00+08:00",
  updated_at: "2026-05-20T10:00:00+08:00",
};

export const mockDiary: EmotionDiary = {
  id: "diary_mock_001",
  user_id: MOCK_USER_ID,
  goal_id: mockGoal.id,
  event_time: "2026-05-20T20:30:00+08:00",
  scene: "作业拖延",
  event_description: "孩子回家后一直没开始写作业，我说了好几次你怎么又这样。",
  parent_emotion: "着急",
  parent_emotion_intensity: 8,
  child_emotion: "烦躁",
  child_emotion_intensity: 7,
  automatic_thought: "他就是故意拖，不想学。",
  body_sensation: "胸口发紧，说话变快。",
  behavior: "反复催促，语气变重。",
  raw_text: "我说多少遍了，你必须马上写。",
  created_at: "2026-05-20T20:35:00+08:00",
  updated_at: "2026-05-20T20:35:00+08:00",
};

export const mockFeedback: FeedbackResult = {
  id: "feedback_mock_001",
  diary_id: mockDiary.id,
  tags: ["judgmental_language", "negative_attribution", "repeated_urging"],
  labels: ["评判性语言", "负性归因", "情绪性行为：反复催促"],
  trigger_summary: "本次记录中可先关注：评判性语言、负性归因、情绪性行为：反复催促。",
  pattern_summary: "这些标签只描述本次互动中可观察到的语言或行为模式，不代表对家长或孩子的诊断。",
  supportive_feedback: "你不是不关心孩子，而是当压力升高时，大脑会自动寻找一个明确原因。现在可以先把评价换成对事实和感受的描述。",
  alternative_response: "把“你怎么又这样”换成“我看到这件事又卡住了，我们先看看发生了什么”。",
  recommended_card_ids: ["nonjudgmental_response", "emotion_naming", "cognitive_flexibility"],
  risk_level: "low",
};

export const mockTrainingCards: TrainingCard[] = [
  {
    id: "emotion_naming",
    type: "emotion_awareness",
    title: "情绪识别卡：先命名情绪",
    purpose: "帮助家长在回应孩子前，先识别自己和孩子的情绪。",
    tags: ["emotion_awareness", "high_emotion_intensity"],
    steps: [
      "暂停 3 秒，先不急着讲道理。",
      "在心里说出自己的情绪。",
      "再尝试命名孩子的情绪。",
      "用一句非评判的话开头。",
    ],
    example: "我看到你现在很难受，我们先把发生了什么说清楚。",
    duration_minutes: 3,
    enabled: true,
  },
  {
    id: "three_second_pause",
    type: "behavior_substitution",
    title: "3 秒暂停卡：开口前先停一下",
    purpose: "降低自动催促、吼叫或指责的概率。",
    tags: ["high_demand_language", "emotional_behavior"],
    steps: [
      "发现自己想立刻批评时，先闭嘴 3 秒。",
      "做一次慢呼吸。",
      "把第一句指责换成一个观察句。",
      "只提出一个具体请求。",
    ],
    example: "我看到作业还没开始。我们先一起看今天最先做哪一项。",
    duration_minutes: 1,
    enabled: true,
  },
];

export const mockCheckin: Checkin = {
  id: "checkin_mock_001",
  user_id: MOCK_USER_ID,
  card_id: "three_second_pause",
  diary_id: mockDiary.id,
  completed: 1,
  emotion_before: 8,
  emotion_after: 5,
  reflection: "暂停后语气更慢，孩子愿意说第一句话。",
  created_at: "2026-05-20T21:00:00+08:00",
};

export const mockWeeklyReport: WeeklyReport = {
  id: "weekly_mock_001",
  user_id: MOCK_USER_ID,
  week_start: "2026-05-18",
  week_end: "2026-05-24",
  frequent_scenes: [["作业拖延", 1]],
  frequent_emotions: [["着急", 1]],
  common_patterns: [["judgmental_language", 1]],
  completed_cards: ["three_second_pause"],
  next_week_suggestion: "下周建议继续选择一个高频场景，优先练习一张最容易执行的训练卡。",
};

export const mockSupervisionRequest: SupervisionRequest = {
  id: "supervision_mock_001",
  user_id: MOCK_USER_ID,
  diary_id: mockDiary.id,
  message: "想请老师看看我这次回应还能怎么调整。",
  contact: "demo@example.com",
  risk_hint: "无高风险，仅请求人工建议。",
  risk_level: "low",
  status: "pending",
  supervisor_reply: null,
  created_at: "2026-05-20T21:10:00+08:00",
  replied_at: null,
};

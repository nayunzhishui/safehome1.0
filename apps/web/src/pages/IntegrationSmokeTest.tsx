import { useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { EmotionDiary, FeedbackResult, TrainingCard } from "../../../../shared/types/api";

type StepStatus = "idle" | "running" | "success" | "error";

interface SmokeState {
  status: StepStatus;
  message: string;
  diary?: EmotionDiary;
  feedback?: FeedbackResult;
  cards?: TrainingCard[];
}

const api = new SafeHomeApiClient();

export function IntegrationSmokeTest() {
  const [state, setState] = useState<SmokeState>({
    status: "idle",
    message: "请先启动 backend，再点击按钮进行最小联调。",
  });

  async function runSmokeTest() {
    setState({ status: "running", message: "正在创建情绪事件记录..." });

    try {
      const diary = await api.createDiary({
        scene: "作业拖延",
        event_description: "孩子一直不开始写作业，我忍不住催了很多次。",
        parent_emotion: "着急",
        parent_emotion_intensity: 8,
        automatic_thought: "他就是故意拖。",
        behavior: "反复催促。",
      });

      setState({ status: "running", message: "正在生成即时反馈...", diary });

      const feedback = await api.generateFeedback({ diary_id: diary.id });

      setState({ status: "running", message: "正在获取训练卡推荐...", diary, feedback });

      const cards = await api.recommendCards({ tags: feedback.tags });

      setState({
        status: "success",
        message: "联调通过：已完成记录、反馈、训练卡推荐三步。",
        diary,
        feedback,
        cards: cards.items,
      });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "联调失败，请确认 backend 是否已启动。",
      });
    }
  }

  return (
    <section className="panel smokePanel">
      <p className="eyebrow">SafeHome MVP</p>
      <h1>最小联调测试</h1>
      <p className="summary">只验证三步数据流：创建情绪事件记录、生成即时反馈、获取训练卡推荐。</p>

      <button className="primaryButton" type="button" onClick={runSmokeTest} disabled={state.status === "running"}>
        {state.status === "running" ? "联调中..." : "运行联调测试"}
      </button>

      <div className={`status ${state.status}`}>{state.message}</div>

      {state.diary && (
        <section className="resultBlock">
          <h2>情绪事件记录</h2>
          <p>{state.diary.event_description}</p>
        </section>
      )}

      {state.feedback && (
        <section className="resultBlock">
          <h2>即时反馈</h2>
          <p>{state.feedback.supportive_feedback}</p>
          <p className="muted">标签：{state.feedback.labels.join("、")}</p>
        </section>
      )}

      {state.cards && (
        <section className="resultBlock">
          <h2>推荐训练卡</h2>
          <ul>
            {state.cards.map((card) => (
              <li key={card.id}>{card.title}</li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}

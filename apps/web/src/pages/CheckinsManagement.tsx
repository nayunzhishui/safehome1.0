import { useEffect, useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { Checkin, TrainingCard } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface CheckinsState {
  status: LoadStatus;
  message: string;
  checkins: Checkin[];
  cards: TrainingCard[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();

function formatDateTime(value?: string | null) {
  if (!value) {
    return "未记录";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function displayText(value?: string | number | null) {
  if (value === undefined || value === null || value === "") {
    return "未填写";
  }
  return String(value);
}

function getEmotionDelta(checkin: Checkin) {
  if (typeof checkin.emotion_before !== "number" || typeof checkin.emotion_after !== "number") {
    return null;
  }
  return checkin.emotion_after - checkin.emotion_before;
}

export function CheckinsManagement() {
  const [state, setState] = useState<CheckinsState>({
    status: "idle",
    message: "正在准备练习尝试记录。",
    checkins: [],
    cards: [],
  });

  const cardTitleById = useMemo(() => {
    return new Map(state.cards.map((card) => [card.id, card.title]));
  }, [state.cards]);

  const selectedCheckin = useMemo(() => {
    return state.checkins.find((checkin) => checkin.id === state.selectedId) ?? state.checkins[0];
  }, [state.checkins, state.selectedId]);

  const recordedAttemptCount = state.checkins.filter((checkin) => checkin.completed === 1).length;
  const linkedDiaryCount = state.checkins.filter((checkin) => checkin.diary_id).length;
  const withReflectionCount = state.checkins.filter((checkin) => checkin.reflection).length;

  async function loadCheckins() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取练习尝试记录...",
    }));

    try {
      const [checkins, cards] = await Promise.all([api.listCheckins({ limit: 50 }), api.listCards()]);
      setState({
        status: "success",
        message: checkins.items.length > 0 ? "已读取小程序端保存的练习尝试记录。" : "当前还没有练习尝试记录。",
        checkins: checkins.items,
        cards: cards.items,
        selectedId: checkins.items[0]?.id,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: error instanceof Error ? error.message : "读取失败，请确认 backend 是否已启动。",
      }));
    }
  }

  useEffect(() => {
    void loadCheckins();
  }, []);

  return (
    <section className="dashboardShell" aria-label="练习尝试记录后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Research Platform</p>
          <h1>练习尝试记录</h1>
          <p className="summary">查看小程序端保存的训练卡练习和复盘情况，用于观察用户尝试了哪些小动作、留下了哪些过程线索。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={loadCheckins} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新记录"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="练习尝试概况">
        <MetricCard label="尝试记录" value={state.checkins.length} />
        <MetricCard label="已记录尝试" value={recordedAttemptCount} />
        <MetricCard label="关联记录" value={linkedDiaryCount} />
        <MetricCard label="含复盘" value={withReflectionCount} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="练习尝试列表">
          <div className="sectionTitleRow">
            <h2>尝试列表</h2>
            <span className="countBadge">{state.checkins.length} 条</span>
          </div>

          {state.checkins.length === 0 ? (
            <div className="emptyState">还没有练习尝试记录。请先在小程序记录一次训练卡练习。</div>
          ) : (
            <div className="recordList">
              {state.checkins.map((checkin) => {
                const cardTitle = cardTitleById.get(checkin.card_id) ?? checkin.card_id;
                const delta = getEmotionDelta(checkin);

                return (
                  <button
                    className={`recordItem ${selectedCheckin?.id === checkin.id ? "active" : ""}`}
                    key={checkin.id}
                    type="button"
                    onClick={() => setState((current) => ({ ...current, selectedId: checkin.id }))}
                  >
                    <span className="recordScene">{cardTitle}</span>
                    <span className="recordDescription">{checkin.reflection || "未填写复盘"}</span>
                    <span className="recordMeta">
                      {checkin.completed === 1 ? "已记录尝试" : "这次还没有完整记录"} · {formatDateTime(checkin.created_at)}
                      {delta !== null ? ` · 情绪变化 ${delta > 0 ? "+" : ""}${delta}` : ""}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="练习尝试详情">
          <div className="sectionTitleRow">
            <h2>尝试详情</h2>
            {selectedCheckin && <span className="countBadge">ID {selectedCheckin.id.slice(0, 8)}</span>}
          </div>

          {selectedCheckin ? (
            <div className="detailContent">
              <DetailRow label="家长用户" value={selectedCheckin.user_id} />
              <DetailRow label="训练卡" value={cardTitleById.get(selectedCheckin.card_id) ?? selectedCheckin.card_id} />
              <DetailRow label="训练卡技术标识（仅研究）" value={selectedCheckin.card_id} />
              <DetailRow label="关联记录技术标识（仅研究）" value={selectedCheckin.diary_id} />
              <DetailRow label="记录状态" value={selectedCheckin.completed === 1 ? "已记录尝试" : "这次还没有完整记录"} />
              <DetailRow label="练习前情绪强度" value={selectedCheckin.emotion_before} />
              <DetailRow label="练习后情绪强度" value={selectedCheckin.emotion_after} />
              <DetailRow
                label="前后情绪变化"
                value={getEmotionDelta(selectedCheckin) === null ? null : `${getEmotionDelta(selectedCheckin)! > 0 ? "+" : ""}${getEmotionDelta(selectedCheckin)}`}
              />
              <DetailRow label="家长复盘" value={selectedCheckin.reflection} />
              <DetailRow label="创建时间" value={formatDateTime(selectedCheckin.created_at)} />

              <section className="guidanceBox" aria-label="试点评估用途">
                <h3>试点评估用途</h3>
                <p>
                  练习记录用于观察家长尝试了哪些训练卡、做到哪一步、前后情绪有什么变化，以及下次想轻一点尝试什么。这里不展示诊断性标签，也不判断家长或孩子是否存在心理问题。
                </p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧练习尝试记录后，这里会显示详情。</div>
          )}
        </section>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="metricCard">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DetailRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{displayText(value)}</span>
    </div>
  );
}

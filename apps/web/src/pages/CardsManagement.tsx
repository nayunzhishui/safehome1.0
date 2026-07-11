import { useEffect, useMemo, useState } from "react";

import trainingCardsContent from "../../../../content/training_cards.json";
import type { TrainingCard } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface CardsState {
  status: LoadStatus;
  message: string;
  cards: TrainingCard[];
  selectedId?: string;
}

const contentCards = trainingCardsContent.cards as TrainingCard[];

function displayText(value?: string | number | boolean | null) {
  if (value === undefined || value === null || value === "") {
    return "未填写";
  }
  if (typeof value === "boolean") {
    return value ? "启用" : "停用";
  }
  return String(value);
}

export function CardsManagement() {
  const [state, setState] = useState<CardsState>({
    status: "idle",
    message: "正在准备训练卡内容。",
    cards: [],
  });

  const selectedCard = useMemo(() => {
    return state.cards.find((card) => card.id === state.selectedId) ?? state.cards[0];
  }, [state.cards, state.selectedId]);

  const enabledCards = state.cards.filter((card) => card.enabled);
  const disabledCards = state.cards.filter((card) => !card.enabled);
  const cardTypes = new Set(state.cards.map((card) => card.type));
  const reviewStatuses = new Set(state.cards.map((card) => card.review_status || "未标记"));

  function loadCards() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取训练卡内容...",
    }));

    setState({
      status: "success",
      message: contentCards.length > 0 ? "已读取本地训练卡内容。" : "当前还没有训练卡内容。",
      cards: contentCards,
      selectedId: contentCards[0]?.id,
    });
  }

  useEffect(() => {
    void loadCards();
  }, []);

  return (
    <section className="dashboardShell" aria-label="训练卡管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Management</p>
          <h1>训练卡管理</h1>
          <p className="summary">只读查看当前内容库中的训练卡，用于确认卡片标题、审核状态、适用边界、步骤和示例是否适合试点使用。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={loadCards} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新本地内容"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="训练卡概况">
        <MetricCard label="训练卡总数" value={state.cards.length} />
        <MetricCard label="启用卡片" value={enabledCards.length} />
        <MetricCard label="停用卡片" value={disabledCards.length} />
        <MetricCard label="审核状态" value={reviewStatuses.size} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="训练卡列表">
          <div className="sectionTitleRow">
            <h2>训练卡列表</h2>
            <span className="countBadge">{cardTypes.size} 类</span>
          </div>

          {state.cards.length === 0 ? (
            <div className="emptyState">还没有训练卡。请检查后端内容库是否已初始化。</div>
          ) : (
            <div className="recordList">
              {state.cards.map((card) => (
                <button
                  className={`recordItem ${selectedCard?.id === card.id ? "active" : ""}`}
                  key={card.id}
                  type="button"
                  onClick={() => setState((current) => ({ ...current, selectedId: card.id }))}
                >
                  <span className="recordScene">{card.title}</span>
                  <span className="recordDescription">{card.purpose}</span>
                  <span className="recordMeta">
                    {card.enabled ? "启用" : "停用"} · {card.review_status || "未标记"} · {card.duration_minutes} 分钟
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="训练卡详情">
          <div className="sectionTitleRow">
            <h2>训练卡详情</h2>
            {selectedCard && <span className="countBadge">ID {selectedCard.id}</span>}
          </div>

          {selectedCard ? (
            <div className="detailContent">
              <DetailRow label="卡片标题" value={selectedCard.title} />
              <DetailRow label="卡片类型" value={selectedCard.type} />
              <DetailRow label="启用状态" value={selectedCard.enabled} />
              <DetailRow label="审核状态" value={selectedCard.review_status} />
              <DetailRow label="审核备注" value={selectedCard.reviewer_note} />
              <DetailRow label="治理审核" value={selectedCard.governance_review_status} />
              <DetailRow label="证据等级" value={selectedCard.evidence_level} />
              <DetailRow label="主要机制" value={selectedCard.mechanism_code} />
              <DetailRow label="安全级别" value={selectedCard.safety_level} />
              <DetailRow label="释放方式" value={selectedCard.release_policy} />
              <DetailRow label="预计时长" value={`${selectedCard.duration_minutes} 分钟`} />
              <DetailRow label="建议频率" value={selectedCard.minimum_dose?.suggested_frequency} />
              <DetailRow label="初始周期" value={selectedCard.minimum_dose ? `${selectedCard.minimum_dose.initial_cycle_days} 天` : undefined} />
              <DetailRow label="练习目的" value={selectedCard.purpose} />
              <DetailRow label="理论来源" value={selectedCard.theory_source} />
              <DetailRow label="目标技能" value={selectedCard.target_skill} />
              <DetailRow label="标签" value={selectedCard.tags.join("、")} />
              <DetailRow label="适合场景" value={(selectedCard.suitable_for || []).join("、")} />
              <DetailRow label="不适合场景" value={(selectedCard.not_suitable_for || []).join("、")} />
              <DetailRow label="完成标准" value={selectedCard.completion_criteria} />
              <DetailRow label="进阶条件" value={selectedCard.progression_criteria} />
              <DetailRow label="停止规则" value={(selectedCard.stop_rules || []).join("\n")} />
              <DetailRow label="执行核对" value={(selectedCard.fidelity_check || []).join("\n")} />
              <DetailRow label="结果关联" value={(selectedCard.outcome_links || []).join("、")} />
              <DetailRow label="练习步骤" value={selectedCard.steps.map((step, index) => `${index + 1}. ${step}`).join("\n")} />
              <DetailRow label="复盘问题" value={(selectedCard.reflection_questions || []).map((question, index) => `${index + 1}. ${question}`).join("\n")} />
              <DetailRow label="示例" value={selectedCard.example} />

              <section className="guidanceBox" aria-label="内容边界提示">
                <h3>内容边界</h3>
                <p>
                  训练卡用于支持家长进行情绪觉察、亲子沟通和自我复盘练习。页面只展示内容库，不做诊断判断，也不替代心理咨询、医学诊断或危机干预。
                </p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧训练卡后，这里会显示详情。</div>
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

function DetailRow({ label, value }: { label: string; value?: string | number | boolean | null }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{displayText(value)}</span>
    </div>
  );
}

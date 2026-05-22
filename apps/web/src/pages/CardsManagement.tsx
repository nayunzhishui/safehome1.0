import { useEffect, useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { TrainingCard } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface CardsState {
  status: LoadStatus;
  message: string;
  cards: TrainingCard[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();

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
  const tags = new Set(state.cards.flatMap((card) => card.tags));

  async function loadCards() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取训练卡内容...",
    }));

    try {
      const result = await api.listCards();
      setState({
        status: "success",
        message: result.items.length > 0 ? "已读取训练卡内容。" : "当前还没有训练卡内容。",
        cards: result.items,
        selectedId: result.items[0]?.id,
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
    void loadCards();
  }, []);

  return (
    <section className="dashboardShell" aria-label="训练卡管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Management</p>
          <h1>训练卡管理</h1>
          <p className="summary">只读查看当前内容库中的训练卡，用于确认卡片标题、标签、步骤和示例是否适合试点使用。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={loadCards} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新训练卡"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="训练卡概况">
        <MetricCard label="训练卡总数" value={state.cards.length} />
        <MetricCard label="启用卡片" value={enabledCards.length} />
        <MetricCard label="停用卡片" value={disabledCards.length} />
        <MetricCard label="标签数量" value={tags.size} />
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
                    {card.enabled ? "启用" : "停用"} · {card.type} · {card.duration_minutes} 分钟
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
              <DetailRow label="预计时长" value={`${selectedCard.duration_minutes} 分钟`} />
              <DetailRow label="练习目的" value={selectedCard.purpose} />
              <DetailRow label="标签" value={selectedCard.tags.join("、")} />
              <DetailRow label="练习步骤" value={selectedCard.steps.map((step, index) => `${index + 1}. ${step}`).join("\n")} />
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

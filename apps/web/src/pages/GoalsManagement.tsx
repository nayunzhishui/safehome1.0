import { useEffect, useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { Goal, GoalStatus } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface GoalsState {
  status: LoadStatus;
  message: string;
  goals: Goal[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();

const STATUS_LABELS: Record<GoalStatus, string> = {
  active: "进行中",
  done: "已完成",
  paused: "已暂停",
};

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

export function GoalsManagement() {
  const [state, setState] = useState<GoalsState>({
    status: "idle",
    message: "点击刷新，可以查看小程序端保存的本周目标。",
    goals: [],
  });

  const selectedGoal = useMemo(() => {
    return state.goals.find((goal) => goal.id === state.selectedId) ?? state.goals[0];
  }, [state.goals, state.selectedId]);

  async function loadGoals() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取目标数据...",
    }));

    try {
      const result = await api.listGoals();
      setState({
        status: "success",
        message: result.items.length > 0 ? "已读取小程序端保存的目标。" : "当前还没有目标。请先在小程序中设定本周小目标。",
        goals: result.items,
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
    void loadGoals();
  }, []);

  return (
    <section className="dashboardShell" aria-label="目标管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">SafeHome Admin</p>
          <h1>目标管理</h1>
          <p className="summary">查看家长在小程序端设定的本周目标，用于确认目标是否具体、可练习、可追踪。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            查看记录后台
          </a>
          <button className="primaryButton" type="button" onClick={loadGoals} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新目标"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="目标概况">
        <MetricCard label="全部目标" value={state.goals.length} />
        <MetricCard label="进行中" value={state.goals.filter((goal) => goal.status === "active").length} />
        <MetricCard label="已完成" value={state.goals.filter((goal) => goal.status === "done").length} />
        <MetricCard label="已暂停" value={state.goals.filter((goal) => goal.status === "paused").length} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="目标列表">
          <div className="sectionTitleRow">
            <h2>目标列表</h2>
            <span className="countBadge">{state.goals.length} 条</span>
          </div>

          {state.goals.length === 0 ? (
            <div className="emptyState">还没有目标。请先在小程序首页进入“设定本周小目标”。</div>
          ) : (
            <div className="recordList">
              {state.goals.map((goal) => (
                <button
                  className={`recordItem ${selectedGoal?.id === goal.id ? "active" : ""}`}
                  key={goal.id}
                  type="button"
                  onClick={() => setState((current) => ({ ...current, selectedId: goal.id }))}
                >
                  <span className="recordScene">{goal.scene}</span>
                  <span className="recordDescription">{goal.smart_goal}</span>
                  <span className="recordMeta">
                    {STATUS_LABELS[goal.status]} · {formatDateTime(goal.created_at)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="目标详情">
          <div className="sectionTitleRow">
            <h2>目标详情</h2>
            {selectedGoal && <span className="countBadge">ID {selectedGoal.id.slice(0, 8)}</span>}
          </div>

          {selectedGoal ? (
            <div className="detailContent">
              <DetailRow label="家长用户" value={selectedGoal.user_id} />
              <DetailRow label="高频场景" value={selectedGoal.scene} />
              <DetailRow label="本周目标" value={selectedGoal.smart_goal} />
              <DetailRow label="练习动机" value={selectedGoal.motivation} />
              <DetailRow label="开始日期" value={selectedGoal.start_date} />
              <DetailRow label="当前状态" value={STATUS_LABELS[selectedGoal.status]} />
              <DetailRow label="创建时间" value={formatDateTime(selectedGoal.created_at)} />
              <DetailRow label="更新时间" value={formatDateTime(selectedGoal.updated_at)} />

              <section className="guidanceBox" aria-label="研究用途提示">
                <h3>试点评估用途</h3>
                <p>
                  目标页用于观察家长常见冲突场景、练习意愿和目标是否足够具体。这里不做诊断判断，只帮助研究人员确认数据是否完整。
                </p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧目标后，这里会显示详情。</div>
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

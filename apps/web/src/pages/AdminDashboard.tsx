import { useEffect, useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { EmotionDiary } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface AdminDashboardState {
  status: LoadStatus;
  message: string;
  diaries: EmotionDiary[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();

function formatTime(value?: string | null) {
  if (!value) {
    return "未记录时间";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
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

export function AdminDashboard() {
  const [state, setState] = useState<AdminDashboardState>({
    status: "idle",
    message: "点击刷新，可以查看当前测试用户的情绪事件记录。",
    diaries: [],
  });

  const selectedDiary = useMemo(() => {
    return state.diaries.find((diary) => diary.id === state.selectedId) ?? state.diaries[0];
  }, [state.diaries, state.selectedId]);

  async function loadDiaries() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取情绪事件记录...",
    }));

    try {
      const result = await api.listDiaries({ limit: 50 });
      setState({
        status: "success",
        message: result.items.length > 0 ? "已读取最新情绪事件记录。" : "当前还没有情绪事件记录。",
        diaries: result.items,
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
    void loadDiaries();
  }, []);

  return (
    <section className="dashboardShell" aria-label="网页端最小管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">SafeHome Admin</p>
          <h1>记录查看后台</h1>
          <p className="summary">第一版只用于查看情绪事件记录，帮助确认小程序保存的数据是否正常。</p>
        </div>
        <div className="dashboardActions">
          <button className="primaryButton" type="button" onClick={loadDiaries} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新记录"}
          </button>
          <a className="secondaryButton" href={api.buildAdminExportUrl({ type: "diaries" })}>
            导出 CSV
          </a>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="dashboardGrid">
        <section className="listPanel" aria-label="情绪记录列表">
          <div className="sectionTitleRow">
            <h2>情绪记录列表</h2>
            <span className="countBadge">{state.diaries.length} 条</span>
          </div>

          {state.diaries.length === 0 ? (
            <div className="emptyState">还没有记录。请先在小程序中完成一次情绪事件记录。</div>
          ) : (
            <div className="recordList">
              {state.diaries.map((diary) => (
                <button
                  className={`recordItem ${selectedDiary?.id === diary.id ? "active" : ""}`}
                  key={diary.id}
                  type="button"
                  onClick={() => setState((current) => ({ ...current, selectedId: diary.id }))}
                >
                  <span className="recordScene">{diary.scene}</span>
                  <span className="recordDescription">{diary.event_description}</span>
                  <span className="recordMeta">
                    {formatTime(diary.created_at)} · 家长情绪强度 {displayText(diary.parent_emotion_intensity)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="情绪记录详情">
          <div className="sectionTitleRow">
            <h2>记录详情</h2>
            {selectedDiary && <span className="countBadge">ID {selectedDiary.id.slice(0, 8)}</span>}
          </div>

          {selectedDiary ? (
            <div className="detailContent">
              <DetailRow label="发生场景" value={selectedDiary.scene} />
              <DetailRow label="发生了什么" value={selectedDiary.event_description} />
              <DetailRow label="家长情绪" value={`${selectedDiary.parent_emotion} / 强度 ${selectedDiary.parent_emotion_intensity}`} />
              <DetailRow
                label="孩子情绪"
                value={`${displayText(selectedDiary.child_emotion)} / 强度 ${displayText(selectedDiary.child_emotion_intensity)}`}
              />
              <DetailRow label="当时的想法" value={selectedDiary.automatic_thought} />
              <DetailRow label="说了什么/做了什么" value={selectedDiary.behavior} />
              <DetailRow label="身体感觉" value={selectedDiary.body_sensation} />
              <DetailRow label="创建时间" value={formatTime(selectedDiary.created_at)} />
            </div>
          ) : (
            <div className="emptyState">选择左侧记录后，这里会显示详情。</div>
          )}
        </section>
      </div>
    </section>
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

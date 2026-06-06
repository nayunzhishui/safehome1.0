import { useEffect, useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import { getStoredAdminToken, setStoredAdminToken } from "../services/adminToken";
import type { EmotionDiary, FeedbackResult, TrainingCard } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";
type InsightStatus = "idle" | "loading" | "success" | "error";
type ExportStatus = "idle" | "loading" | "success" | "error";

interface AdminDashboardState {
  status: LoadStatus;
  message: string;
  diaries: EmotionDiary[];
  selectedId?: string;
}

interface DiaryInsight {
  feedback: FeedbackResult;
  cards: TrainingCard[];
}

const api = new SafeHomeApiClient();
const RAW_TEXT_PREFIXES = [
  { key: "childReaction", label: "孩子反应", prefix: "孩子反应：" },
  { key: "shortTermResult", label: "短期结果", prefix: "短期结果：" },
  { key: "longTermImpact", label: "长期影响", prefix: "长期影响：" },
] as const;

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

function parseRawText(value?: string | null) {
  const result: Record<(typeof RAW_TEXT_PREFIXES)[number]["key"], string> = {
    childReaction: "",
    shortTermResult: "",
    longTermImpact: "",
  };
  const extraLines: string[] = [];

  if (!value) {
    return { ...result, extra: "" };
  }

  value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const match = RAW_TEXT_PREFIXES.find((item) => line.startsWith(item.prefix));
      if (match) {
        result[match.key] = line.slice(match.prefix.length).trim();
      } else {
        extraLines.push(line);
      }
    });

  return { ...result, extra: extraLines.join("\n") };
}

export function AdminDashboard() {
  const [state, setState] = useState<AdminDashboardState>({
    status: "idle",
    message: "点击刷新，可以查看云端最新情绪事件记录。",
    diaries: [],
  });
  const [insights, setInsights] = useState<Record<string, DiaryInsight>>({});
  const [insightStatus, setInsightStatus] = useState<InsightStatus>("idle");
  const [insightMessage, setInsightMessage] = useState("选择一条记录后，可以生成对应的即时反馈和训练卡推荐。");
  const [adminToken, setAdminToken] = useState(getStoredAdminToken);
  const [exportStatus, setExportStatus] = useState<ExportStatus>("idle");
  const [exportMessage, setExportMessage] = useState("导出需要后台令牌。云端验收请填写云托管 ADMIN_EXPORT_TOKEN。");

  const selectedDiary = useMemo(() => {
    return state.diaries.find((diary) => diary.id === state.selectedId) ?? state.diaries[0];
  }, [state.diaries, state.selectedId]);
  const selectedInsight = selectedDiary ? insights[selectedDiary.id] : undefined;
  const selectedRawText = useMemo(() => parseRawText(selectedDiary?.raw_text), [selectedDiary?.raw_text]);

  async function loadDiaries() {
    const token = adminToken.trim();
    if (!token) {
      setState((current) => ({
        ...current,
        status: "error",
        message: "请先填写后台令牌。云端验收请填写云托管 ADMIN_EXPORT_TOKEN，而不是本地默认令牌。",
      }));
      return;
    }

    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取情绪事件记录...",
    }));

    try {
      const result = await api.listDiaries({ limit: 50 }, token);
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

  async function loadInsight() {
    if (!selectedDiary) {
      return;
    }
    const token = adminToken.trim();
    if (!token) {
      setInsightStatus("error");
      setInsightMessage("请先填写后台令牌。云端验收请填写云托管 ADMIN_EXPORT_TOKEN，而不是本地默认令牌。");
      return;
    }

    if (insights[selectedDiary.id]) {
      setInsightStatus("success");
      setInsightMessage("已显示这条记录的即时反馈和训练卡推荐。");
      return;
    }

    setInsightStatus("loading");
    setInsightMessage("正在生成即时反馈和推荐训练卡...");

    try {
      const feedback = await api.generateFeedback({ diary_id: selectedDiary.id }, token);
      const cards = await api.recommendCards({ tags: feedback.tags, limit: 3 });
      setInsights((current) => ({
        ...current,
        [selectedDiary.id]: {
          feedback,
          cards: cards.items,
        },
      }));
      setInsightStatus("success");
      setInsightMessage("已生成即时反馈和训练卡推荐。");
    } catch (error) {
      setInsightStatus("error");
      setInsightMessage(error instanceof Error ? error.message : "生成失败，请确认 backend 是否已启动。");
    }
  }

  async function downloadCsv() {
    const token = adminToken.trim();
    if (!token) {
      setExportStatus("error");
      setExportMessage("请先填写后台导出令牌。");
      return;
    }

    setExportStatus("loading");
    setExportMessage("正在导出情绪记录 CSV...");

    try {
      const blob = await api.downloadAdminExport({ type: "diaries", adminToken: token });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "safehome_diaries.csv";
      link.click();
      URL.revokeObjectURL(url);
      setExportStatus("success");
      setExportMessage("导出已开始。如果浏览器拦截下载，请检查下载栏。");
    } catch (error) {
      setExportStatus("error");
      setExportMessage(error instanceof Error ? error.message : "导出失败，请确认令牌是否正确。");
    }
  }

  return (
    <section className="dashboardShell" aria-label="网页端最小管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">SafeHome Admin</p>
          <h1>记录查看后台</h1>
          <p className="summary">第一版只用于查看情绪事件记录，帮助确认小程序保存的数据是否正常。</p>
        </div>
        <div className="dashboardActions">
          <label className="tokenField">
            <span>后台令牌</span>
            <input
              type="password"
              value={adminToken}
              onChange={(event) => {
                setAdminToken(event.target.value);
                setStoredAdminToken(event.target.value);
              }}
              placeholder="填写 ADMIN_EXPORT_TOKEN 后刷新"
            />
          </label>
          <button className="primaryButton" type="button" onClick={loadDiaries} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新记录"}
          </button>
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
                  onClick={() => {
                    setState((current) => ({ ...current, selectedId: diary.id }));
                    setInsightStatus(insights[diary.id] ? "success" : "idle");
                    setInsightMessage(
                      insights[diary.id] ? "已显示这条记录的即时反馈和训练卡推荐。" : "选择一条记录后，可以生成对应的即时反馈和训练卡推荐。",
                    );
                  }}
                >
                  <span className="recordScene">{diary.scene}</span>
                  <span className="recordDescription">{diary.event_description}</span>
                  <span className="recordMeta">
                    {formatTime(diary.created_at)} · 家长情绪强度 {displayText(diary.parent_emotion_intensity)}
                    {diary.goal_id ? " · 已关联目标" : ""}
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
              <DetailRow label="关联目标" value={selectedDiary.goal_id ? selectedDiary.goal_id : "未关联"} />
              <DetailRow label="发生场景" value={selectedDiary.scene} />
              <DetailRow label="事件时间" value={formatTime(selectedDiary.event_time)} />
              <DetailRow label="发生了什么" value={selectedDiary.event_description} />
              <DetailRow label="家长情绪" value={`${selectedDiary.parent_emotion} / 强度 ${selectedDiary.parent_emotion_intensity}`} />
              <DetailRow
                label="孩子情绪"
                value={`${displayText(selectedDiary.child_emotion)} / 强度 ${displayText(selectedDiary.child_emotion_intensity)}`}
              />
              <DetailRow label="当时的想法" value={selectedDiary.automatic_thought} />
              <DetailRow label="说了什么/做了什么" value={selectedDiary.behavior} />
              <DetailRow label="身体感觉" value={selectedDiary.body_sensation} />
              <DetailRow label="孩子反应" value={selectedRawText.childReaction} />
              <DetailRow label="短期结果" value={selectedRawText.shortTermResult} />
              <DetailRow label="长期影响" value={selectedRawText.longTermImpact} />
              <DetailRow label="补充原文" value={selectedRawText.extra} />
              <DetailRow label="创建时间" value={formatTime(selectedDiary.created_at)} />

              <section className="guidanceBox" aria-label="记录详情用途提示">
                <h3>查看边界</h3>
                <p>这里用于检查小程序记录是否完整，不展示诊断性标签，也不对家长或孩子做评判。</p>
              </section>

              <div className="insightPanel">
                <div className="sectionTitleRow">
                  <h3>即时反馈与训练卡</h3>
                  <button className="secondaryButton" type="button" onClick={loadInsight} disabled={insightStatus === "loading"}>
                    {insightStatus === "loading" ? "生成中..." : selectedInsight ? "刷新显示" : "生成反馈和推荐"}
                  </button>
                </div>
                <div className={`status compact ${insightStatus}`}>{insightMessage}</div>

                {selectedInsight && (
                  <div className="insightContent">
                    <section className="feedbackBox">
                      <h4>即时反馈</h4>
                      <p>{selectedInsight.feedback.supportive_feedback}</p>
                      <p className="muted">识别标签：{selectedInsight.feedback.labels.join("、") || "无"}</p>
                      <p className="muted">替代回应：{selectedInsight.feedback.alternative_response}</p>
                    </section>

                    <section className="cardsBox">
                      <h4>推荐训练卡</h4>
                      {selectedInsight.cards.length > 0 ? (
                        <div className="cardList">
                          {selectedInsight.cards.map((card) => (
                            <article className="trainingCard" key={card.id}>
                              <span className="recordMeta">{card.type}</span>
                              <strong>{card.title}</strong>
                              <p>{card.purpose}</p>
                              <p className="muted">替代话术：{card.example}</p>
                            </article>
                          ))}
                        </div>
                      ) : (
                        <p className="muted">当前没有匹配到训练卡。</p>
                      )}
                    </section>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="emptyState">选择左侧记录后，这里会显示详情。</div>
          )}
        </section>
      </div>

      <section className="exportPanel" aria-label="数据导出">
        <div className="sectionTitleRow">
          <div>
            <h2>数据导出</h2>
            <p className="summary">云端后台需要填写与云托管环境变量 `ADMIN_EXPORT_TOKEN` 一致的令牌。</p>
          </div>
          <button className="primaryButton" type="button" onClick={downloadCsv} disabled={exportStatus === "loading"}>
            {exportStatus === "loading" ? "导出中..." : "导出情绪记录 CSV"}
          </button>
        </div>
        <label className="tokenField">
          <span>后台导出令牌</span>
          <input
            type="password"
            value={adminToken}
            onChange={(event) => {
              setAdminToken(event.target.value);
              setStoredAdminToken(event.target.value);
            }}
            placeholder="请输入后台导出令牌"
          />
        </label>
        <div className={`status compact ${exportStatus}`}>{exportMessage}</div>
      </section>
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

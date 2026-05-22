import { useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface FeedbackExportRow {
  id: string;
  user_id: string;
  diary_id: string;
  tags_json: string;
  trigger_summary: string;
  pattern_summary: string;
  supportive_feedback: string;
  alternative_response: string;
  recommended_card_ids_json: string;
  risk_level: string;
  created_at: string;
}

interface FeedbackState {
  status: LoadStatus;
  message: string;
  feedback: FeedbackExportRow[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();
const LOCAL_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token";

function parseCsv(text: string): FeedbackExportRow[] {
  const normalized = text.replace(/^\uFEFF/, "").trim();
  if (!normalized || normalized === "empty") {
    return [];
  }

  const rows: string[][] = [];
  let current = "";
  let row: string[] = [];
  let inQuotes = false;

  for (let index = 0; index < normalized.length; index += 1) {
    const char = normalized[index];
    const next = normalized[index + 1];

    if (char === '"' && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      row.push(current);
      current = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") {
        index += 1;
      }
      row.push(current);
      rows.push(row);
      row = [];
      current = "";
    } else {
      current += char;
    }
  }

  row.push(current);
  rows.push(row);

  const [headers = [], ...dataRows] = rows;
  return dataRows.map((items) => {
    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      record[header] = items[index] ?? "";
    });
    return record as unknown as FeedbackExportRow;
  });
}

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

function summarizeJsonList(value: string) {
  if (!value) {
    return "未记录";
  }

  try {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed)) {
      if (parsed.length === 0) {
        return "未记录";
      }
      return parsed.map((item) => String(item)).join("、");
    }
  } catch {
    return value;
  }

  return value;
}

export function FeedbackManagement() {
  const [state, setState] = useState<FeedbackState>({
    status: "idle",
    message: "点击读取，可以通过当前 CSV 导出接口查看已生成的反馈结果。",
    feedback: [],
  });
  const [adminToken, setAdminToken] = useState(LOCAL_ADMIN_EXPORT_TOKEN);

  const selectedFeedback = useMemo(() => {
    return state.feedback.find((item) => item.id === state.selectedId) ?? state.feedback[0];
  }, [state.feedback, state.selectedId]);

  const linkedDiaries = new Set(state.feedback.map((item) => item.diary_id).filter(Boolean));
  const mediumOrHighFeedback = state.feedback.filter((item) => item.risk_level !== "low").length;
  const recommendedCards = new Set(
    state.feedback.flatMap((item) => {
      try {
        const parsed = JSON.parse(item.recommended_card_ids_json || "[]") as unknown;
        return Array.isArray(parsed) ? parsed.map((id) => String(id)) : [];
      } catch {
        return [];
      }
    }),
  );

  async function loadFeedback() {
    const token = adminToken.trim();
    if (!token) {
      setState((current) => ({
        ...current,
        status: "error",
        message: "请先填写后台导出令牌。",
      }));
      return;
    }

    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取反馈结果 CSV...",
    }));

    try {
      const blob = await api.downloadAdminExport({ type: "feedback", adminToken: token });
      const text = await blob.text();
      const feedback = parseCsv(text);
      setState({
        status: "success",
        message: feedback.length > 0 ? "已读取反馈结果。" : "当前还没有已生成的反馈结果。",
        feedback,
        selectedId: feedback[0]?.id,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: error instanceof Error ? error.message : "读取失败，请确认 backend 是否已启动，令牌是否正确。",
      }));
    }
  }

  return (
    <section className="dashboardShell" aria-label="反馈结果后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Research Platform</p>
          <h1>反馈结果</h1>
          <p className="summary">只读查看已生成的规则反馈结果，用于检查反馈边界、标签和训练卡推荐是否稳定。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={loadFeedback} disabled={state.status === "loading"}>
            {state.status === "loading" ? "读取中..." : "读取反馈结果"}
          </button>
        </div>
      </div>

      <label className="tokenField">
        后台导出令牌
        <input value={adminToken} onChange={(event) => setAdminToken(event.target.value)} />
      </label>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="反馈结果概况">
        <MetricCard label="反馈结果" value={state.feedback.length} />
        <MetricCard label="关联记录" value={linkedDiaries.size} />
        <MetricCard label="中高提示" value={mediumOrHighFeedback} />
        <MetricCard label="推荐卡片" value={recommendedCards.size} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="反馈结果列表">
          <div className="sectionTitleRow">
            <h2>反馈列表</h2>
            <span className="countBadge">{state.feedback.length} 条</span>
          </div>

          {state.feedback.length === 0 ? (
            <div className="emptyState">还没有反馈结果。请先在情绪记录详情或小程序反馈流程中生成反馈。</div>
          ) : (
            <div className="recordList">
              {state.feedback.map((item) => (
                <button
                  className={`recordItem ${selectedFeedback?.id === item.id ? "active" : ""}`}
                  key={item.id}
                  type="button"
                  onClick={() => setState((current) => ({ ...current, selectedId: item.id }))}
                >
                  <span className="recordScene">{item.risk_level || "low"}</span>
                  <span className="recordDescription">{item.pattern_summary || item.supportive_feedback || "未填写反馈内容"}</span>
                  <span className="recordMeta">
                    {item.user_id || "未知用户"} · {formatDateTime(item.created_at)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="反馈结果详情">
          <div className="sectionTitleRow">
            <h2>反馈详情</h2>
            {selectedFeedback && <span className="countBadge">ID {selectedFeedback.id.slice(0, 8)}</span>}
          </div>

          {selectedFeedback ? (
            <div className="detailContent">
              <DetailRow label="家长用户" value={selectedFeedback.user_id} />
              <DetailRow label="关联记录" value={selectedFeedback.diary_id} />
              <DetailRow label="标签" value={summarizeJsonList(selectedFeedback.tags_json)} />
              <DetailRow label="触发点摘要" value={selectedFeedback.trigger_summary} />
              <DetailRow label="互动模式" value={selectedFeedback.pattern_summary} />
              <DetailRow label="支持性反馈" value={selectedFeedback.supportive_feedback} />
              <DetailRow label="替代回应" value={selectedFeedback.alternative_response} />
              <DetailRow label="推荐训练卡" value={summarizeJsonList(selectedFeedback.recommended_card_ids_json)} />
              <DetailRow label="风险提示" value={selectedFeedback.risk_level} />
              <DetailRow label="创建时间" value={formatDateTime(selectedFeedback.created_at)} />

              <section className="guidanceBox" aria-label="反馈边界提示">
                <h3>边界提示</h3>
                <p>
                  反馈结果用于检查规则输出和推荐卡片是否稳定，不用于诊断家长、孩子或家庭关系。需要进一步理解时，应回到具体记录和支持性练习建议。
                </p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧反馈结果后，这里会显示详情。</div>
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

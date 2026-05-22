import { useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface WeeklyReportExportRow {
  id: string;
  user_id: string;
  week_start: string;
  week_end: string;
  frequent_scenes_json: string;
  frequent_emotions_json: string;
  common_patterns_json: string;
  completed_cards_json: string;
  next_week_suggestion: string;
  created_at: string;
}

interface ReportsState {
  status: LoadStatus;
  message: string;
  reports: WeeklyReportExportRow[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();
const LOCAL_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token";

function parseCsv(text: string): WeeklyReportExportRow[] {
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
    return record as unknown as WeeklyReportExportRow;
  });
}

function formatDate(value?: string | null) {
  if (!value) {
    return "未记录";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
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
      return parsed
        .map((item) => {
          if (Array.isArray(item)) {
            return item.join(" x ");
          }
          return String(item);
        })
        .join("、");
    }
  } catch {
    return value;
  }

  return value;
}

export function ReportsManagement() {
  const [state, setState] = useState<ReportsState>({
    status: "idle",
    message: "点击读取，可以通过当前 CSV 导出接口查看已生成的周报记录。",
    reports: [],
  });
  const [adminToken, setAdminToken] = useState(LOCAL_ADMIN_EXPORT_TOKEN);

  const selectedReport = useMemo(() => {
    return state.reports.find((item) => item.id === state.selectedId) ?? state.reports[0];
  }, [state.reports, state.selectedId]);

  const uniqueUsers = new Set(state.reports.map((item) => item.user_id).filter(Boolean));
  const withSuggestions = state.reports.filter((item) => item.next_week_suggestion).length;

  async function loadReports() {
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
      message: "正在读取周报记录 CSV...",
    }));

    try {
      const blob = await api.downloadAdminExport({ type: "reports", adminToken: token });
      const text = await blob.text();
      const reports = parseCsv(text);
      setState({
        status: "success",
        message: reports.length > 0 ? "已读取周报记录。" : "当前还没有已生成的周报记录。",
        reports,
        selectedId: reports[0]?.id,
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
    <section className="dashboardShell" aria-label="周报记录后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Research Platform</p>
          <h1>周报记录</h1>
          <p className="summary">只读查看已经生成的周度复盘记录。当前页面不主动生成新周报，避免额外写入本地数据库。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={loadReports} disabled={state.status === "loading"}>
            {state.status === "loading" ? "读取中..." : "读取周报记录"}
          </button>
        </div>
      </div>

      <label className="tokenField">
        后台导出令牌
        <input value={adminToken} onChange={(event) => setAdminToken(event.target.value)} />
      </label>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="周报概况">
        <MetricCard label="周报记录" value={state.reports.length} />
        <MetricCard label="关联用户" value={uniqueUsers.size} />
        <MetricCard label="含下周建议" value={withSuggestions} />
        <MetricCard label="读取方式" value="CSV" />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="周报列表">
          <div className="sectionTitleRow">
            <h2>周报列表</h2>
            <span className="countBadge">{state.reports.length} 条</span>
          </div>

          {state.reports.length === 0 ? (
            <div className="emptyState">还没有周报记录。请先在小程序或测试流程中生成周度复盘。</div>
          ) : (
            <div className="recordList">
              {state.reports.map((report) => (
                <button
                  className={`recordItem ${selectedReport?.id === report.id ? "active" : ""}`}
                  key={report.id}
                  type="button"
                  onClick={() => setState((current) => ({ ...current, selectedId: report.id }))}
                >
                  <span className="recordScene">
                    {formatDate(report.week_start)} - {formatDate(report.week_end)}
                  </span>
                  <span className="recordDescription">{report.next_week_suggestion || "未填写下周建议"}</span>
                  <span className="recordMeta">
                    {report.user_id || "未知用户"} · {formatDateTime(report.created_at)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="周报详情">
          <div className="sectionTitleRow">
            <h2>周报详情</h2>
            {selectedReport && <span className="countBadge">ID {selectedReport.id.slice(0, 8)}</span>}
          </div>

          {selectedReport ? (
            <div className="detailContent">
              <DetailRow label="家长用户" value={selectedReport.user_id} />
              <DetailRow label="周开始" value={formatDate(selectedReport.week_start)} />
              <DetailRow label="周结束" value={formatDate(selectedReport.week_end)} />
              <DetailRow label="高频场景" value={summarizeJsonList(selectedReport.frequent_scenes_json)} />
              <DetailRow label="常见情绪" value={summarizeJsonList(selectedReport.frequent_emotions_json)} />
              <DetailRow label="常见模式" value={summarizeJsonList(selectedReport.common_patterns_json)} />
              <DetailRow label="完成训练卡" value={summarizeJsonList(selectedReport.completed_cards_json)} />
              <DetailRow label="下周建议" value={selectedReport.next_week_suggestion} />
              <DetailRow label="创建时间" value={formatDateTime(selectedReport.created_at)} />

              <section className="guidanceBox" aria-label="周报边界提示">
                <h3>边界提示</h3>
                <p>
                  周报用于帮助研究者查看家长练习和记录趋势，只做复盘线索整理，不用于诊断家长、孩子或家庭关系。
                </p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧周报后，这里会显示详情。</div>
          )}
        </section>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
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

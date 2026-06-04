import { useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { AssessmentResult, Checkin, RiskLevel } from "../../../../shared/types/api";

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
  profileResults: AssessmentResult[];
  checkins: Checkin[];
  selectedId?: string;
}

interface ProfileScores {
  profile_name?: string;
  confidence?: number;
  risk_level?: RiskLevel;
  requires_review?: boolean;
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

function parseProfileScores(result: AssessmentResult): ProfileScores {
  try {
    return JSON.parse(result.scores_json || "{}") as ProfileScores;
  } catch {
    return {};
  }
}

function isStudentProfile(result: AssessmentResult): boolean {
  return result.worksheet_id === "student_profile_v1" || result.category === "学生画像";
}

function buildTrendSuggestion(profileResults: AssessmentResult[], checkins: Checkin[]) {
  const reviewCount = profileResults.filter((item) => parseProfileScores(item).requires_review).length;
  const highRiskCount = profileResults.filter((item) => parseProfileScores(item).risk_level === "high").length;
  const completedCount = checkins.filter((item) => item.completed).length;

  if (highRiskCount > 0 || reviewCount > 0) {
    return "下周优先安排人工关注和现实支持确认，暂不把高风险个案推入普通自动训练。";
  }
  if (completedCount > 0) {
    return "下周继续保留一张最容易完成的训练卡，观察练习前后感受是否有轻微变化。";
  }
  if (profileResults.length > 0) {
    return "下周可以参考阶段性画像推荐的一张训练卡，先记录一次 3-5 分钟小练习。";
  }
  return "下周先完成一次具体记录或一次支持性测评，再生成更稳定的趋势线索。";
}

export function ReportsManagement() {
  const [state, setState] = useState<ReportsState>({
    status: "idle",
    message: "点击读取，可以通过当前 CSV 导出接口查看已生成的周报记录。",
    reports: [],
    profileResults: [],
    checkins: [],
  });
  const [adminToken, setAdminToken] = useState(LOCAL_ADMIN_EXPORT_TOKEN);

  const selectedReport = useMemo(() => {
    return state.reports.find((item) => item.id === state.selectedId) ?? state.reports[0];
  }, [state.reports, state.selectedId]);

  const uniqueUsers = new Set(state.reports.map((item) => item.user_id).filter(Boolean));
  const withSuggestions = state.reports.filter((item) => item.next_week_suggestion).length;
  const studentProfiles = state.profileResults.filter(isStudentProfile);
  const reviewProfiles = studentProfiles.filter((item) => parseProfileScores(item).requires_review);
  const highRiskProfiles = studentProfiles.filter((item) => parseProfileScores(item).risk_level === "high");
  const completedCheckins = state.checkins.filter((item) => item.completed).length;
  const trendSuggestion = buildTrendSuggestion(studentProfiles, state.checkins);

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
      const [blob, profileResults, checkins] = await Promise.all([
        api.downloadAdminExport({ type: "reports", adminToken: token }),
        api.listAssessmentResults({ limit: 100 }),
        api.listCheckins({ limit: 100 }),
      ]);
      const text = await blob.text();
      const reports = parseCsv(text);
      setState({
        status: "success",
        message: reports.length > 0 ? "已读取周报记录。" : "当前还没有已生成的周报记录。",
        reports,
        profileResults: profileResults.items || [],
        checkins: checkins.items || [],
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
          <p className="summary">只读查看已经生成的周度复盘记录。周报是过程复盘，画像只是阶段性补充线索，不用于固定判断。</p>
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

      <section className="guidanceBox" aria-label="周报与画像关系">
        <h2>周报与画像关系</h2>
        <p>
          本周复盘主要来自情绪记录、练习尝试和人工关注状态；如果有阶段性画像，只作为理解近期压力状态的补充线索。画像不是固定判断，重点仍是找到下周可以尝试的一小步。
        </p>
      </section>

      <div className="metricGrid" aria-label="周报概况">
        <MetricCard label="周报记录" value={state.reports.length} />
        <MetricCard label="关联用户" value={uniqueUsers.size} />
        <MetricCard label="含下周建议" value={withSuggestions} />
        <MetricCard label="画像复测" value={studentProfiles.length} />
        <MetricCard label="需复核画像" value={reviewProfiles.length} />
        <MetricCard label="高风险画像" value={highRiskProfiles.length} />
        <MetricCard label="练习尝试" value={completedCheckins} />
        <MetricCard label="读取方式" value="CSV + API" />
      </div>

      <section className="panel" aria-label="趋势增强">
        <div className="sectionTitleRow">
          <h2>趋势增强</h2>
          <span className="countBadge">P3-1</span>
        </div>
        <div className="overviewGrid">
          <article className="guidanceBox">
            <h3>阶段性画像线索</h3>
            <p>已读取 {studentProfiles.length} 条学生画像结果。这里只作为补充线索查看，其中 {reviewProfiles.length} 条需要人工关注，{highRiskProfiles.length} 条为高风险。</p>
          </article>
          <article className="guidanceBox">
            <h3>练习积累</h3>
            <p>已读取 {state.checkins.length} 条练习尝试记录，其中 {completedCheckins} 条已记录尝试。</p>
          </article>
        </div>
        <section className="guidanceBox" aria-label="下周一个小任务">
          <h3>下周一个小任务</h3>
          <p>{trendSuggestion}</p>
        </section>
      </section>

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
              <DetailRow label="已记录训练卡" value={summarizeJsonList(selectedReport.completed_cards_json)} />
              <DetailRow label="下周建议" value={selectedReport.next_week_suggestion} />
              <DetailRow label="创建时间" value={formatDateTime(selectedReport.created_at)} />

              <section className="guidanceBox" aria-label="周报边界提示">
                <h3>边界提示</h3>
                <p>
                  周报用于帮助研究者查看家长练习和记录趋势，只做复盘线索整理；阶段性画像只作为补充线索，不用于诊断家长、孩子或家庭关系。
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

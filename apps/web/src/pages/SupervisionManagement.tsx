import { useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface SupervisionExportRow {
  id: string;
  user_id: string;
  diary_id: string;
  message: string;
  contact: string;
  risk_hint: string;
  risk_level: string;
  status: string;
  supervisor_reply: string;
  created_at: string;
  replied_at: string;
}

interface SupervisionState {
  status: LoadStatus;
  message: string;
  requests: SupervisionExportRow[];
  selectedId?: string;
}

const api = new SafeHomeApiClient();
const LOCAL_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token";

function parseCsv(text: string): SupervisionExportRow[] {
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
    return record as unknown as SupervisionExportRow;
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

export function SupervisionManagement() {
  const [state, setState] = useState<SupervisionState>({
    status: "idle",
    message: "点击读取，可以通过当前 CSV 导出接口查看督导请求。",
    requests: [],
  });
  const [adminToken, setAdminToken] = useState(LOCAL_ADMIN_EXPORT_TOKEN);

  const selectedRequest = useMemo(() => {
    return state.requests.find((item) => item.id === state.selectedId) ?? state.requests[0];
  }, [state.requests, state.selectedId]);

  async function loadSupervisionRequests() {
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
      message: "正在读取督导请求 CSV...",
    }));

    try {
      const blob = await api.downloadAdminExport({ type: "supervision", adminToken: token });
      const text = await blob.text();
      const requests = parseCsv(text);
      setState({
        status: "success",
        message: requests.length > 0 ? "已读取督导请求。" : "当前还没有督导请求。",
        requests,
        selectedId: requests[0]?.id,
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
    <section className="dashboardShell" aria-label="人工督导后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">SafeHome Admin</p>
          <h1>督导请求</h1>
          <p className="summary">通过已有 CSV 导出接口只读查看小程序端提交的人工督导请求。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={loadSupervisionRequests} disabled={state.status === "loading"}>
            {state.status === "loading" ? "读取中..." : "读取督导请求"}
          </button>
        </div>
      </div>

      <label className="tokenField">
        后台导出令牌
        <input value={adminToken} onChange={(event) => setAdminToken(event.target.value)} />
      </label>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="督导请求概况">
        <MetricCard label="全部请求" value={state.requests.length} />
        <MetricCard label="待查看" value={state.requests.filter((item) => item.status === "pending").length} />
        <MetricCard label="高风险提示" value={state.requests.filter((item) => item.risk_level === "high").length} />
        <MetricCard label="已回复" value={state.requests.filter((item) => item.status === "replied").length} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="督导请求列表">
          <div className="sectionTitleRow">
            <h2>请求列表</h2>
            <span className="countBadge">{state.requests.length} 条</span>
          </div>

          {state.requests.length === 0 ? (
            <div className="emptyState">还没有督导请求。请先在小程序反馈页提交“让老师进一步看看”。</div>
          ) : (
            <div className="recordList">
              {state.requests.map((request) => (
                <button
                  className={`recordItem ${selectedRequest?.id === request.id ? "active" : ""}`}
                  key={request.id}
                  type="button"
                  onClick={() => setState((current) => ({ ...current, selectedId: request.id }))}
                >
                  <span className="recordScene">{request.status || "pending"}</span>
                  <span className="recordDescription">{request.message || "未填写内容"}</span>
                  <span className="recordMeta">
                    {request.user_id || "未知用户"} · {formatDateTime(request.created_at)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="督导请求详情">
          <div className="sectionTitleRow">
            <h2>请求详情</h2>
            {selectedRequest && <span className="countBadge">ID {selectedRequest.id.slice(0, 8)}</span>}
          </div>

          {selectedRequest ? (
            <div className="detailContent">
              <DetailRow label="家长用户" value={selectedRequest.user_id} />
              <DetailRow label="关联记录" value={selectedRequest.diary_id} />
              <DetailRow label="提交内容" value={selectedRequest.message} />
              <DetailRow label="联系方式" value={selectedRequest.contact} />
              <DetailRow label="风险提示" value={selectedRequest.risk_hint} />
              <DetailRow label="风险等级" value={selectedRequest.risk_level} />
              <DetailRow label="当前状态" value={selectedRequest.status} />
              <DetailRow label="人工回复" value={selectedRequest.supervisor_reply} />
              <DetailRow label="提交时间" value={formatDateTime(selectedRequest.created_at)} />
              <DetailRow label="回复时间" value={formatDateTime(selectedRequest.replied_at)} />

              <section className="guidanceBox" aria-label="督导边界提示">
                <h3>边界提示</h3>
                <p>
                  这里仅用于查看小程序提交的补充支持请求，不做诊断判断。若请求内容涉及紧急安全风险，应优先转向线下专业人员或紧急支持。
                </p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧请求后，这里会显示详情。</div>
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

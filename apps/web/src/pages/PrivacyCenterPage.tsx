import { useEffect, useState } from "react";

import { API_ENDPOINTS } from "../../../../shared/constants/api";
import { getStoredAuthToken, getStoredAuthUser } from "../services/authState";
import { getAnonymousUserId } from "../services/userIdentity";

type ConsentItem = {
  user_id: string;
  consent_type: string;
  agreed: boolean;
  consent_version: string | null;
  agreed_at: string | null;
  revoked_at: string | null;
};

type ConsentStatus = {
  user_id: string;
  items: ConsentItem[];
};

type LoadStatus = "idle" | "loading" | "success" | "error";

const CONSENT_LABELS: Record<string, string> = {
  user_agreement: "用户协议",
  privacy_policy: "隐私政策",
  non_diagnostic_notice: "非诊断声明",
  anonymous_research: "匿名研究授权",
  research_authorization: "研究授权",
};

export function PrivacyCenterPage() {
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [message, setMessage] = useState("");
  const [data, setData] = useState<ConsentStatus | null>(null);
  const [revokeStatus, setRevokeStatus] = useState<LoadStatus>("idle");
  const [revokeMessage, setRevokeMessage] = useState("");

  const authToken = getStoredAuthToken();
  const authUser = getStoredAuthUser();
  const userId = authUser?.id || getAnonymousUserId();
  const authHeaders = authToken ? { Authorization: `Bearer ${authToken}` } : {};

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setStatus("loading");
    setMessage("正在读取授权状态...");
    try {
      const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
      const resp = await fetch(`${base}${API_ENDPOINTS.privacyConsentStatus}?user_id=${encodeURIComponent(userId)}`, {
        headers: authHeaders,
      });
      const body = await resp.json();
      if (!body.ok) {
        setStatus("error");
        setMessage(body.error?.message ?? "读取失败");
        return;
      }
      setData(body.data);
      setStatus("success");
      setMessage("");
    } catch {
      setStatus("error");
      setMessage("网络请求失败，请确认后端已启动。");
    }
  }

  async function handleRevoke(consentType: string) {
    if (!window.confirm(`确认撤回「${CONSENT_LABELS[consentType] ?? consentType}」？撤回后您将不再参与后续研究导出。`)) {
      return;
    }
    setRevokeStatus("loading");
    setRevokeMessage("正在处理...");
    try {
      const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
      const resp = await fetch(`${base}${API_ENDPOINTS.privacyRevokeConsent}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ user_id: userId, consent_type: consentType, reason: "用户主动撤回" }),
      });
      const body = await resp.json();
      if (body.ok) {
        setRevokeStatus("success");
        setRevokeMessage("已撤回授权。");
        await loadStatus();
      } else {
        setRevokeStatus("error");
        setRevokeMessage(body.error?.message ?? "撤回失败");
      }
    } catch {
      setRevokeStatus("error");
      setRevokeMessage("网络请求失败。");
    }
  }

  function consentLabel(consentType: string): string {
    return CONSENT_LABELS[consentType] ?? consentType;
  }

  return (
    <section className="dashboardShell" aria-label="隐私中心">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Privacy Center</p>
          <h1>隐私中心</h1>
        </div>
        <p className="subtitle">
          {authUser ? "账号编号" : "匿名编号"}：<code>{userId}</code>
        </p>
      </div>

      <section className="guidanceBox" aria-label="隐私说明">
        <h2>关于你的隐私</h2>
        <ul>
          <li>本项目不要求填写姓名、手机号等强身份信息。</li>
          <li>匿名编号用于数据关联和后续追踪，可随时更换。</li>
          <li>系统反馈不构成医学或心理诊断。</li>
          <li>撤回研究授权后，你的数据将不再进入后续研究导出。</li>
          <li>已用于历史汇总的数据需由项目负责人按研究管理流程处理。</li>
          <li>如需删除数据，请联系项目负责人并提供匿名编号。</li>
        </ul>
      </section>

      <div className={`status compact ${status}`}>{message}</div>

      {data ? (
        <section className="metricGrid" aria-label="授权状态">
          {data.items.map((item) => (
            <div className="metricCard" key={item.consent_type}>
              <span>{consentLabel(item.consent_type)}</span>
              <strong style={{ color: item.agreed ? "var(--color-success, #16a34a)" : "var(--color-warning, #ca8a04)" }}>
                {item.agreed ? "已同意" : "未同意"}
              </strong>
              {item.agreed_at ? <small>同意时间：{item.agreed_at.slice(0, 10)}</small> : null}
              {item.revoked_at ? <small>撤回时间：{item.revoked_at.slice(0, 10)}</small> : null}
              {(item.consent_type === "anonymous_research" || item.consent_type === "research_authorization") && item.agreed ? (
                <button
                  className="pill muted"
                  disabled={revokeStatus === "loading"}
                  onClick={() => handleRevoke(item.consent_type)}
                  style={{ marginTop: 8 }}
                >
                  撤回授权
                </button>
              ) : null}
            </div>
          ))}
        </section>
      ) : null}

      <div className={`status compact ${revokeStatus}`} style={{ marginTop: 16 }}>
        {revokeMessage}
      </div>

      <section className="metricGrid" aria-label="数据操作" style={{ marginTop: 24 }}>
        <div className="metricCard">
          <span>导出我的摘要数据</span>
          <strong>JSON</strong>
          <small>不含自由文本原文和联系方式</small>
          <button
            className="pill muted"
            style={{ marginTop: 8 }}
            onClick={async () => {
              try {
                const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
                const resp = await fetch(`${base}${API_ENDPOINTS.privacyExportMyData}?user_id=${encodeURIComponent(userId)}`, {
                  headers: authHeaders,
                });
                const body = await resp.json();
                if (body.ok) {
                  const blob = new Blob([JSON.stringify(body.data, null, 2)], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `safehome-data-export-${userId.slice(0, 12)}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                } else {
                  alert(body.error?.message ?? "导出失败");
                }
              } catch {
                alert("网络请求失败");
              }
            }}
          >
            下载摘要
          </button>
        </div>

        <div className="metricCard">
          <span>提交删除请求</span>
          <strong>不硬删数据</strong>
          <small>请求进入后台队列，由项目负责人处理</small>
          <button
            className="pill muted"
            style={{ marginTop: 8 }}
            onClick={async () => {
              const reason = window.prompt("请简要说明删除原因（可选）：");
              if (reason === null) return;
              if (!window.confirm("确认提交删除数据请求？此操作不会立即删除数据，请求将进入后台审核队列。")) return;
              try {
                const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
                const resp = await fetch(`${base}${API_ENDPOINTS.privacyDeleteMyData}`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json", ...authHeaders },
                  body: JSON.stringify({ user_id: userId, reason: reason || undefined }),
                });
                const body = await resp.json();
                if (body.ok) {
                  alert("删除请求已提交，项目负责人将后续处理。");
                } else {
                  alert(body.error?.message ?? "提交失败");
                }
              } catch {
                alert("网络请求失败");
              }
            }}
          >
            提交删除请求
          </button>
        </div>
      </section>

      <section className="guidanceBox" aria-label="边界说明" style={{ marginTop: 24 }}>
        <h2>边界说明</h2>
        <ul>
          <li>撤回授权不影响你已经保存的数据，仅停止未来研究导出。</li>
          <li>删除请求不会立即删除数据，需由项目负责人审核后处理。</li>
          <li>导出摘要不含自由文本原文、联系方式、后台审计或风险处置私密备注。</li>
          <li>如有安全风险或紧急情况，请优先联系线下专业支持。</li>
        </ul>
      </section>
    </section>
  );
}

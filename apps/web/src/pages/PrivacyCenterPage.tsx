import { useEffect, useState } from "react";

import { API_ENDPOINTS } from "../../../../shared/constants/api";
import { clearAuthSession, getStoredAuthToken, getStoredAuthUser } from "../services/authState";
import { getAnonymousUserId } from "../services/userIdentity";
import { safeHomeApi } from "../services/safehomeApi";
import type { IdentityStatus, PrivacyRequest } from "../../../../shared/types/api";

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

const REQUEST_STATUS_LABELS: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  completed: "已完成",
  rejected: "未通过",
  cancelled: "已取消",
};

export function PrivacyCenterPage() {
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [message, setMessage] = useState("");
  const [data, setData] = useState<ConsentStatus | null>(null);
  const [revokeStatus, setRevokeStatus] = useState<LoadStatus>("idle");
  const [revokeMessage, setRevokeMessage] = useState("");
  const [privacyRequests, setPrivacyRequests] = useState<PrivacyRequest[]>([]);
  const [identityStatus, setIdentityStatus] = useState<IdentityStatus | null>(null);
  const [identityMessage, setIdentityMessage] = useState("");

  const authToken = getStoredAuthToken();
  const authUser = getStoredAuthUser();
  const userId = authUser?.id || getAnonymousUserId();
  const authHeaders: Record<string, string> = authToken ? { Authorization: `Bearer ${authToken}` } : {};

  useEffect(() => {
    loadStatus();
    loadPrivacyRequests();
    if (authUser && ["parent", "student", "user"].includes(authUser.role)) {
      void safeHomeApi.getIdentityStatus()
        .then(setIdentityStatus)
        .catch(() => setIdentityMessage("登录方式状态暂时没有读取成功，请稍后刷新。"));
    }
  }, []);

  async function unbindIdentity(identityType: "wechat" | "phone") {
    if (!identityStatus) return;
    const label = identityType === "wechat" ? "微信登录" : "手机号登录";
    if (!window.confirm(`确认撤销${label}？这会退出所有设备，但不会删除日记、测评或训练记录。`)) return;
    setIdentityMessage("正在撤销登录方式...");
    try {
      await safeHomeApi.unbindIdentity(identityType, identityStatus.auth_epoch);
      clearAuthSession();
      window.location.href = "/login";
    } catch (error) {
      setIdentityMessage(error instanceof Error ? error.message : "撤销失败，请刷新后重试。");
    }
  }

  async function loadPrivacyRequests() {
    try {
      const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
      const resp = await fetch(`${base}${API_ENDPOINTS.privacyRequests}?page=1&page_size=20&user_id=${encodeURIComponent(userId)}`, {
        headers: authHeaders,
      });
      const body = await resp.json();
      if (body.ok) setPrivacyRequests(body.data.items ?? []);
    } catch {
      setRevokeMessage("删除申请状态暂时没有读取成功，请稍后重试。");
    }
  }

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

  async function cancelPrivacyRequest(item: PrivacyRequest) {
    if (!window.confirm("确认取消这条待处理的删除申请？")) return;
    try {
      const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
      const key = `privacy-cancel-${item.id}-${Date.now()}`;
      const resp = await fetch(`${base}${API_ENDPOINTS.privacyRequests}/${encodeURIComponent(item.id)}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": key, ...authHeaders },
        body: JSON.stringify({ reason: "参与者主动取消" }),
      });
      const body = await resp.json();
      if (!body.ok) {
        setRevokeStatus("error");
        setRevokeMessage(body.error?.message ?? "取消失败");
        return;
      }
      setRevokeStatus("success");
      setRevokeMessage("删除申请已取消。");
      await loadPrivacyRequests();
    } catch {
      setRevokeStatus("error");
      setRevokeMessage("网络请求失败，申请状态没有改变。");
    }
  }

  async function appealPrivacyRequest(item: PrivacyRequest) {
    const reason = window.prompt("请补充希望继续核对的内容（必填，不超过500字）：");
    if (!reason?.trim()) return;
    try {
      await safeHomeApi.appealPrivacyRequest(item.id, reason.trim(), `privacy-appeal-${item.id}-${Date.now()}`);
      setRevokeStatus("success");
      setRevokeMessage("申请已重新提交。 ");
      await loadPrivacyRequests();
    } catch {
      setRevokeStatus("error");
      setRevokeMessage("暂时无法重新提交，请刷新后重试。 ");
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

      {identityStatus ? (
        <section className="guidanceBox" aria-labelledby="identity-status-title">
          <h2 id="identity-status-title">登录方式</h2>
          <p className="subtitle">{identityStatus.privacy_notice}</p>
          <div className="metricGrid">
            {(["wechat", "phone"] as const).map((identityType) => {
              const descriptor = identityStatus.identities[identityType];
              const label = identityType === "wechat" ? "微信登录" : "手机号登录";
              return (
                <div className="metricCard" key={identityType}>
                  <span>{label}</span>
                  <strong>{descriptor.state === "unbound" ? "未连接" : "已连接"}</strong>
                  <small>系统不会在这里显示身份值</small>
                  {descriptor.can_unbind ? (
                    <button className="pill muted" type="button" onClick={() => { void unbindIdentity(identityType); }}>
                      撤销此登录方式
                    </button>
                  ) : null}
                </div>
              );
            })}
          </div>
          <p className="subtitle">撤销登录方式会退出所有设备，但不会删除业务记录。</p>
          {identityMessage ? <div className="status compact" role="status" aria-live="polite">{identityMessage}</div> : null}
        </section>
      ) : null}

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
          <strong>受控处理</strong>
          <small>先预览范围；正式执行必须满足保存策略、权限和审计门禁</small>
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
                  alert(body.data.already_active ? "已有一条删除申请正在处理中。" : "删除请求已提交，项目负责人将后续处理。");
                  await loadPrivacyRequests();
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

      <section className="guidanceBox" aria-label="删除申请状态" style={{ marginTop: 24 }}>
        <h2>删除申请进度</h2>
        {privacyRequests.length ? (
          <ul>
            {privacyRequests.map((item) => (
              <li key={item.id}>
                <strong>{REQUEST_STATUS_LABELS[item.status] ?? item.status}</strong>
                {` · 提交于 ${item.created_at.slice(0, 10)} · 更新于 ${item.updated_at.slice(0, 10)}`}
                {item.status === "pending" ? (
                  <button className="pill muted" type="button" onClick={() => void cancelPrivacyRequest(item)} style={{ marginLeft: 10 }}>
                    取消申请
                  </button>
                ) : null}
                {item.status === "rejected" ? (
                  <button className="pill muted" type="button" onClick={() => void appealPrivacyRequest(item)} style={{ marginLeft: 10 }}>
                    补充说明并重新提交
                  </button>
                ) : null}
                {item.participant_notice ? <p>{item.participant_notice}</p> : null}
                {item.execution_proof_hash ? <small className="privacyProof">执行证明：{item.execution_proof_hash}</small> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p>当前没有删除申请。</p>
        )}
      </section>

      <section className="guidanceBox" aria-label="边界说明" style={{ marginTop: 24 }}>
        <h2>边界说明</h2>
        <ul>
          <li>撤回授权不影响你已经保存的数据，仅停止未来研究导出。</li>
          <li>删除请求不会立即执行；负责人确认保存矩阵后，系统按白名单删除或匿名化并生成证明。</li>
          <li>导出摘要不含自由文本原文、联系方式、后台审计或风险处置私密备注。</li>
          <li>如有安全风险或紧急情况，请优先联系线下专业支持。</li>
        </ul>
      </section>
    </section>
  );
}

import { useEffect, useState } from "react";

import { API_ENDPOINTS } from "../../../../shared/constants/api";
import { getStoredAuthToken, getStoredAuthUser, type AuthUser } from "../services/authState";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface FamilyMember {
  id: string;
  parent_user_id: string;
  student_user_id: string | null;
  relation_label: string | null;
  status: string;
  created_at: string;
  confirmed_at: string | null;
  revoked_at: string | null;
  summary_boundary: string;
}

function authHeaders(): Record<string, string> {
  const token = getStoredAuthToken();
  return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

async function apiCall(url: string, options: RequestInit = {}): Promise<{ ok: boolean; data?: unknown; error?: { message: string } }> {
  const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL ?? "";
  const resp = await fetch(`${base}${url}`, { ...options, headers: { ...authHeaders(), ...(options.headers as Record<string, string> || {}) } });
  return resp.json() as Promise<{ ok: boolean; data?: unknown; error?: { message: string } }>;
}

export function FamilyBindPage() {
  const user: AuthUser | null = getStoredAuthUser();
  const isParent = user?.role === "parent";
  const isStudent = user?.role === "student";
  const isLoggedIn = !!user && !!getStoredAuthToken();

  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [membersStatus, setMembersStatus] = useState<LoadStatus>("idle");
  const [membersMessage, setMembersMessage] = useState("");

  const [bindCode, setBindCode] = useState("");
  const [codeStatus, setCodeStatus] = useState<LoadStatus>("idle");
  const [codeMessage, setCodeMessage] = useState("");

  const [inputCode, setInputCode] = useState("");
  const [bindStatus, setBindStatus] = useState<LoadStatus>("idle");
  const [bindMessage, setBindMessage] = useState("");

  useEffect(() => {
    if (isLoggedIn) loadMembers();
  }, []);

  async function loadMembers() {
    setMembersStatus("loading");
    try {
      const body = await apiCall(API_ENDPOINTS.familyMembers);
      if (body.ok) {
        setMembers((body.data as { items: FamilyMember[] }).items || []);
        setMembersStatus("success");
      } else {
        setMembersStatus("error");
        setMembersMessage(body.error?.message ?? "读取失败");
      }
    } catch {
      setMembersStatus("error");
      setMembersMessage("网络请求失败");
    }
  }

  async function createBindCode() {
    setCodeStatus("loading");
    setCodeMessage("");
    try {
      const body = await apiCall(API_ENDPOINTS.familyCreateBindCode, {
        method: "POST",
        body: JSON.stringify({ relation_label: "家长" }),
      });
      if (body.ok) {
        const data = body.data as { bind_code: string };
        setBindCode(data.bind_code);
        setCodeStatus("success");
        setCodeMessage("绑定码已生成，请分享给学生。");
      } else {
        setCodeStatus("error");
        setCodeMessage(body.error?.message ?? "生成失败");
      }
    } catch {
      setCodeStatus("error");
      setCodeMessage("网络请求失败");
    }
  }

  async function bindWithCode() {
    if (inputCode.length !== 6) {
      setBindStatus("error");
      setBindMessage("绑定码必须是 6 位数字");
      return;
    }
    setBindStatus("loading");
    try {
      const body = await apiCall(API_ENDPOINTS.familyBindStudent, {
        method: "POST",
        body: JSON.stringify({ bind_code: inputCode }),
      });
      if (body.ok) {
        setBindStatus("success");
        setBindMessage("绑定成功！");
        setInputCode("");
        await loadMembers();
      } else {
        setBindStatus("error");
        setBindMessage(body.error?.message ?? "绑定失败");
      }
    } catch {
      setBindStatus("error");
      setBindMessage("网络请求失败");
    }
  }

  async function unbind(linkId: string) {
    if (!window.confirm("确认撤销此绑定？")) return;
    try {
      const body = await apiCall(`${API_ENDPOINTS.familyUnbind}`, {
        method: "DELETE",
        body: JSON.stringify({ link_id: linkId }),
        headers: { "Content-Type": "application/json" },
      } as RequestInit);
      if (body.ok) {
        await loadMembers();
      } else {
        alert(body.error?.message ?? "操作失败");
      }
    } catch {
      alert("网络请求失败");
    }
  }

  function statusBadge(status: string): string {
    if (status === "active") return "已绑定";
    if (status === "pending") return "等待确认";
    if (status === "revoked") return "已撤销";
    return status;
  }

  if (!isLoggedIn) {
    return (
      <section className="dashboardShell">
        <div className="dashboardHeader">
          <h1>家庭绑定</h1>
          <p>请先<a href="/login">登录</a>或<a href="/register">注册</a>。</p>
        </div>
      </section>
    );
  }

  return (
    <section className="dashboardShell" aria-label="家庭绑定">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Family</p>
          <h1>家庭绑定</h1>
        </div>
        <p className="subtitle">当前角色：{user?.role ?? "未知"}｜{user?.nickname ?? user?.username ?? "未命名"}</p>
      </div>

      <section className="guidanceBox" aria-label="说明">
        <h2>绑定说明</h2>
        <ul>
          <li>家长生成 6 位绑定码，学生输入确认后建立关联。</li>
          <li>家长默认只查看授权摘要，不查看学生自由文本原文。</li>
          <li>绑定后可随时撤销。</li>
        </ul>
      </section>

      {isParent ? (
        <section className="guidanceBox" style={{ marginTop: 16 }}>
          <h2>生成绑定码</h2>
          <p>点击下方按钮生成一个新的 6 位绑定码，分享给学生完成绑定。</p>
          <button className="pill" onClick={() => { void createBindCode(); }} disabled={codeStatus === "loading"}>
            生成绑定码
          </button>
          {bindCode ? (
            <div className="metricCard" style={{ marginTop: 12 }}>
              <span>绑定码</span>
              <strong style={{ fontSize: "2rem", letterSpacing: "0.3em", fontFamily: "monospace" }}>{bindCode}</strong>
              <small>有效期：24 小时，超过 5 次尝试后失效</small>
            </div>
          ) : null}
          <div className={`status compact ${codeStatus}`}>{codeMessage}</div>
        </section>
      ) : null}

      {isStudent ? (
        <section className="guidanceBox" style={{ marginTop: 16 }}>
          <h2>输入绑定码</h2>
          <label className="tokenField">
            绑定码
            <input value={inputCode} onChange={(e) => setInputCode(e.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="6 位数字" maxLength={6} />
          </label>
          <button className="pill" onClick={() => { void bindWithCode(); }} disabled={bindStatus === "loading"}>
            确认绑定
          </button>
          <div className={`status compact ${bindStatus}`}>{bindMessage}</div>
        </section>
      ) : null}

      <section style={{ marginTop: 24 }}>
        <h2>当前绑定关系</h2>
        <div className={`status compact ${membersStatus}`}>{membersMessage}</div>
        {members.length === 0 && membersStatus === "success" ? (
          <p className="muted">暂无绑定关系。</p>
        ) : (
          <div className="metricGrid">
            {members.map((m) => (
              <div className="metricCard" key={m.id}>
                <span>{m.relation_label ?? "未标记关系"}</span>
                <strong>{statusBadge(m.status)}</strong>
                {m.student_user_id ? <small>学生 ID：{m.student_user_id.slice(0, 12)}...</small> : null}
                {m.confirmed_at ? <small>确认时间：{m.confirmed_at.slice(0, 10)}</small> : null}
                {m.status === "active" || m.status === "pending" ? (
                  <button className="pill muted" style={{ marginTop: 8 }} onClick={() => { void unbind(m.id); }}>
                    撤销绑定
                  </button>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}

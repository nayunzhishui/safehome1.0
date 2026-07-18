import { useState } from "react";

import { saveAuthSession } from "../services/authState";
import { formatSafeHomeError, safeHomeApi } from "../services/safehomeApi";
import type { DataClaimPreview } from "../../../../shared/types/api";
import { DataClaimPrompt } from "../components/DataClaimPrompt";

function destinationForRole(role: string): string {
  if (["admin", "researcher", "supervisor"].includes(role)) return "/dashboard";
  if (role === "student") return "/student";
  return "/";
}

export function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState("");
  const [claimPreview, setClaimPreview] = useState<DataClaimPreview | null>(null);
  const [destination, setDestination] = useState("/");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password) {
      setStatus("error");
      setMessage("请填写用户名和密码");
      return;
    }
    setStatus("loading");
    setMessage("正在登录...");
    try {
      const data = await safeHomeApi.login({ username: username.trim(), password });
      saveAuthSession(data.token, data.user);
      const nextDestination = destinationForRole(data.user.role);
      const preview = ["parent", "student", "user"].includes(data.user.role)
        ? await safeHomeApi.getDataClaimPreview().catch(() => null)
        : null;
      if (preview?.available) {
        setClaimPreview(preview);
        setDestination(nextDestination);
        setStatus("idle");
        setMessage("登录成功。你可以先决定是否合并本机试用记录。");
        return;
      }
      window.location.href = nextDestination;
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "登录失败，请确认账号密码。"));
    }
  }

  async function confirmClaim() {
    if (!claimPreview?.claim_id) return;
    setStatus("loading");
    setMessage("正在合并本机试用记录...");
    try {
      const result = await safeHomeApi.claimAnonymousData(claimPreview.claim_id);
      setMessage(`已合并 ${result.total_records} 条记录。`);
      window.location.href = destination;
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "合并失败，请稍后在账号页面重试。"));
    }
  }

  return (
    <section className="dashboardShell" aria-label="登录">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">SafeHome</p>
          <h1>登录</h1>
        </div>
        <p className="subtitle">使用已注册的账号登录。匿名试用请直接访问首页。</p>
      </div>

      {claimPreview ? (
        <DataClaimPrompt
          preview={claimPreview}
          status={status}
          message={message}
          onConfirm={() => { void confirmClaim(); }}
          onSkip={() => { window.location.href = destination; }}
        />
      ) : <form className="authForm" onSubmit={(e) => { void handleSubmit(e); }}>
        <label className="tokenField">
          用户名
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="请输入用户名" autoComplete="username" />
        </label>
        <label className="tokenField">
          密码
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="请输入密码" autoComplete="current-password" />
        </label>
        {message ? <div className={`status compact ${status}`} role={status === "error" ? "alert" : "status"} aria-live="polite">{message}</div> : null}
        <button className="primaryButton authSubmit" type="submit" disabled={status === "loading"}>
          登录
        </button>
      </form>}

      <p className="authLinks">
        还没有账号？<a href="/register">注册新账号</a> ｜ <a href="/privacy">隐私中心</a>
      </p>
    </section>
  );
}

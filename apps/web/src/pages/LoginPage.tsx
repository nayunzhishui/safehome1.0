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
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

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
      if (data.user.must_change_password) {
        setDestination(nextDestination);
        setMustChangePassword(true);
        setStatus("idle");
        setMessage("首次登录，请先设置新密码。完成后才可进入研究工作台。");
        return;
      }
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

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setStatus("error");
      setMessage("两次输入的新密码不一致。");
      return;
    }
    setStatus("loading");
    setMessage("正在更新密码...");
    try {
      const data = await safeHomeApi.changePassword({
        current_password: password,
        new_password: newPassword,
      });
      saveAuthSession(data.token, data.user);
      window.location.href = destination;
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "密码更新失败，请检查后重试。"));
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

      {mustChangePassword ? (
        <form className="authForm" onSubmit={(e) => { void handlePasswordChange(e); }}>
          <h2>首次登录，请先设置新密码</h2>
          <p className="subtitle">新密码至少 12 位，并包含三类字符。更新后临时密码和旧会话立即失效。</p>
          <label className="tokenField">
            新密码
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" />
          </label>
          <label className="tokenField">
            再次输入新密码
            <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" />
          </label>
          {message ? <div className={`status compact ${status}`} role={status === "error" ? "alert" : "status"}>{message}</div> : null}
          <button className="primaryButton authSubmit" type="submit" disabled={status === "loading"}>更新密码并继续</button>
        </form>
      ) : claimPreview ? (
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

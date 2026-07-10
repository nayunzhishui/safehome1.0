import { useState } from "react";

import { saveAuthSession } from "../services/authState";
import { formatSafeHomeError, safeHomeApi } from "../services/safehomeApi";

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
      window.location.href = destinationForRole(data.user.role);
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "登录失败，请确认账号密码。"));
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

      <form onSubmit={(e) => { void handleSubmit(e); }} style={{ maxWidth: 400 }}>
        <label className="tokenField">
          用户名
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="请输入用户名" autoComplete="username" />
        </label>
        <label className="tokenField">
          密码
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="请输入密码" autoComplete="current-password" />
        </label>
        <div className={`status compact ${status}`}>{message}</div>
        <button className="pill" type="submit" disabled={status === "loading"} style={{ marginTop: 12 }}>
          登录
        </button>
      </form>

      <p style={{ marginTop: 16 }}>
        还没有账号？<a href="/register">注册新账号</a> ｜ <a href="/privacy">隐私中心</a>
      </p>
    </section>
  );
}

import { useState } from "react";

import { API_ENDPOINTS } from "../../../../shared/constants/api";
import { saveAuthSession } from "../services/authState";

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
      const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL || "http://127.0.0.1:5050";
      const url = `${base}${API_ENDPOINTS.authLogin}`;
      let resp: Response;
      try {
        resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: username.trim(), password }),
        });
      } catch {
        setStatus("error");
        setMessage(`无法连接后端，请确认 Flask 服务已启动（${base}）`);
        return;
      }
      let body: { ok: boolean; data?: { token: string; user: unknown }; error?: { message?: string } };
      try {
        body = await resp.json() as typeof body;
      } catch {
        setStatus("error");
        setMessage(`后端返回了非 JSON 响应（HTTP ${resp.status}），请查看 Flask 日志。`);
        return;
      }
      if (resp.status === 404) {
        setStatus("error");
        setMessage("注册接口不存在或路径不匹配，请确认后端已部署最新版本并注册了 auth blueprint。");
      } else if (resp.status >= 500) {
        setStatus("error");
        setMessage(`后端注册接口异常（HTTP ${resp.status}），请查看 Flask 日志。`);
      } else if (body.ok) {
        saveAuthSession(body.data!.token, body.data!.user);
        window.location.href = "/dashboard";
      } else {
        setStatus("error");
        setMessage(body.error?.message ?? `登录失败（HTTP ${resp.status}）`);
      }
    } catch {
      setStatus("error");
      setMessage("发生未知错误，请刷新页面重试。");
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

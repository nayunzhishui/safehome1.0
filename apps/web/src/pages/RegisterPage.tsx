import { useState } from "react";

import { API_ENDPOINTS } from "../../../../shared/constants/api";
import { getAnonymousUserId } from "../services/userIdentity";
import { saveAuthSession } from "../services/authState";

const ROLES = [
  { value: "parent", label: "家长" },
  { value: "student", label: "学生" },
];

export function RegisterPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("parent");
  const [nickname, setNickname] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (username.trim().length < 3) {
      setStatus("error");
      setMessage("用户名至少需要 3 个字符");
      return;
    }
    if (password.length < 8) {
      setStatus("error");
      setMessage("密码至少需要 8 个字符");
      return;
    }
    setStatus("loading");
    setMessage("正在注册...");
    try {
      const base = import.meta.env.VITE_SAFEHOME_API_BASE_URL || "http://127.0.0.1:5050";
      const url = `${base}${API_ENDPOINTS.authRegister}`;
      let resp: Response;
      try {
        resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: username.trim(),
            password,
            role,
            nickname: nickname.trim() || undefined,
            anonymous_id: getAnonymousUserId(),
          }),
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
        setMessage(body.error?.message ?? `注册失败（HTTP ${resp.status}）`);
      }
    } catch {
      setStatus("error");
      setMessage("发生未知错误，请刷新页面重试。");
    }
  }

  return (
    <section className="dashboardShell" aria-label="注册">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">SafeHome</p>
          <h1>注册</h1>
        </div>
        <p className="subtitle">
          注册后可使用正式账号登录。匿名试用无需注册，直接访问首页即可。
        </p>
      </div>

      <form onSubmit={(e) => { void handleSubmit(e); }} style={{ maxWidth: 400 }}>
        <label className="tokenField">
          用户名
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="至少3个字符" autoComplete="username" />
        </label>
        <label className="tokenField">
          密码
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="至少8个字符" autoComplete="new-password" />
        </label>
        <label className="tokenField">
          角色
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </label>
        <p className="subtitle" style={{ margin: "0 0 12px" }}>
          研究者、督导和管理员账号由项目负责人单独开通。
        </p>
        <label className="tokenField">
          昵称（可选）
          <input value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="选填" />
        </label>
        <div className={`status compact ${status}`}>{message}</div>
        <button className="pill" type="submit" disabled={status === "loading"} style={{ marginTop: 12 }}>
          注册
        </button>
      </form>

      <p style={{ marginTop: 16 }}>
        已有账号？<a href="/login">登录</a> ｜ <a href="/privacy">隐私中心</a>
      </p>
    </section>
  );
}

import { useState } from "react";

import { saveAuthSession } from "../services/authState";
import { formatSafeHomeError, safeHomeApi } from "../services/safehomeApi";

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
      const data = await safeHomeApi.register({
        username: username.trim(),
        password,
        role,
        nickname: nickname.trim() || undefined,
      });
      saveAuthSession(data.token, data.user);
      window.location.href = "/dashboard";
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "注册失败，请稍后重试。"));
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

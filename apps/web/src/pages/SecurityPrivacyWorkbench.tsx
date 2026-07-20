import { useCallback, useEffect, useMemo, useState } from "react";

import type { SecurityAuthorizationOperation, SecurityWorkbench } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "安全证据暂时无法读取，请稍后重试。";
}

function statusLabel(status: string): string {
  return ({ passed: "通过", failed: "未通过", evidence_pending: "待外部证据", open: "待处理", resolved: "已处理" } as Record<string, string>)[status] || status;
}

export function SecurityPrivacyWorkbench() {
  const actor = getStoredAuthUser();
  const isAdmin = actor?.role === "admin";
  const [data, setData] = useState<SecurityWorkbench | null>(null);
  const [query, setQuery] = useState("");
  const [action, setAction] = useState("all");
  const [status, setStatus] = useState("正在读取安全、隐私与滥用防护证据…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const next = await safeHomeApi.getSecurityWorkbench();
    setData(next);
    setStatus("工程证据已更新；临时展示越权仍阻断正式权限验收。");
  }, []);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  const operations = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return (data?.registry.authorization_matrix || []).filter((item) => {
      const matchesAction = action === "all" || item.action === action;
      const haystack = `${item.method} ${item.path} ${item.object_type} ${item.allowed_roles.join(" ")}`.toLowerCase();
      return matchesAction && (!normalized || haystack.includes(normalized));
    });
  }, [action, data, query]);

  async function runScan() {
    setBusy(true); setStatus("正在运行本地脱敏安全扫描…");
    try {
      const result = await safeHomeApi.runSecurityScan();
      setStatus(result.hard_checks_passed ? "本地硬门禁通过；联网依赖告警、测试云与真人签字仍待补。" : `扫描发现 ${result.blockers.length} 个阻断项。`);
      await load();
    } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  async function resolveEvent(id: string) {
    setBusy(true);
    try { await safeHomeApi.resolveSecurityEvent(id); await load(); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  const registry = data?.registry;
  const latestRun = data?.runs[0] as { status?: string; summary?: { checks?: Array<{ id: string; status: string; severity: string }> } } | undefined;
  const openEvents = (data?.events || []).filter((item) => item.status === "open");

  return (
    <section className="dashboardShell securityWorkbench" aria-label="安全隐私与滥用防护工作台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">T31 · 工程防护</p>
          <h1>安全、隐私与滥用防护</h1>
          <p className="summary">用同一份机器契约核对资产、对象权限、威胁、删除证明和配置扫描。页面不展示密钥、令牌或参与者原文。</p>
        </div>
        <span className="gateBadge gateBlocked">正式权限验收未通过</span>
      </div>
      <div className="status" role="status" aria-live="polite">{status}</div>

      <section className="securityBoundary" aria-label="正式验收边界">
        <div>
          <span className="panelKicker">已知例外</span>
          <h2>临时展示越权继续保留</h2>
          <p>{registry?.temporary_showcase_exception.stop_condition || "正式试点或生产发布前必须停用并重跑权限矩阵。"}</p>
        </div>
        <dl className="aiQaFacts">
          <div><dt>API操作</dt><dd>{registry?.authorization_summary.operation_count ?? "—"}</dd></div>
          <div><dt>展示例外</dt><dd>{registry?.authorization_summary.showcase_bypass_operation_count ?? "—"}</dd></div>
          <div><dt>真实AI</dt><dd>关闭</dd></div>
          <div><dt>自动批准</dt><dd>禁止</dd></div>
        </dl>
      </section>

      <div className="securitySummaryGrid">
        <article className="panel"><span className="panelKicker">数据资产</span><strong>{registry?.asset_inventory.length ?? "—"}</strong><p>身份、量表、日记、消息、导出、离线、AI、备份均登记处理与删除边界。</p></article>
        <article className="panel"><span className="panelKicker">威胁场景</span><strong>{(registry?.web_miniprogram_threats.length || 0) + (registry?.ai_threats.length || 0)}</strong><p>每项包含缓解、检测、负责人和剩余风险。</p></article>
        <article className="panel"><span className="panelKicker">删除核验</span><strong>{data?.deletion_verifications.length ?? 0}</strong><p>正式执行必须在同一事务内证明白名单查询归零或身份已匿名化。</p></article>
        <article className="panel"><span className="panelKicker">待处理事件</span><strong>{openEvents.length}</strong><p>异常登录、账号停用和安全控制动作只记录最小元数据。</p></article>
      </div>

      <div className="securityColumns">
        <section className="panel" aria-label="自动扫描">
          <div className="panelHeading"><div><span className="panelKicker">不返回秘密值</span><h2>配置与供应链扫描</h2></div>{isAdmin ? <button className="primaryButton" type="button" disabled={busy || !data?.scan_execution_enabled} onClick={() => void runScan()}>运行本地扫描</button> : null}</div>
          <div className="securityCheckList">
            {(latestRun?.summary?.checks || registry?.automated_scans.map((id) => ({ id, status: "待运行", severity: "工程检查" })) || []).map((item) => <div key={item.id}><strong>{item.id}</strong><span>{statusLabel(item.status)}</span><small>{item.severity}</small></div>)}
          </div>
          <p className="boundaryCallout">联网漏洞库、CloudBase日志、网关身份头、真机深链和备份擦除只能形成外部证据包，不能在此自动签字。</p>
        </section>

        <section className="panel" aria-label="威胁模型">
          <div className="panelHeading"><div><span className="panelKicker">缓解 + 检测 + 剩余风险</span><h2>关键威胁</h2></div></div>
          <div className="threatList">{[...(registry?.web_miniprogram_threats || []), ...(registry?.ai_threats || [])].map((item) => <article key={item.id}><div><strong>{item.id}</strong><span>{item.owner}</span></div><p>{item.mitigation}</p><small>剩余：{item.residual_risk}</small></article>)}</div>
        </section>
      </div>

      <section className="panel" aria-label="对象权限矩阵">
        <div className="panelHeading"><div><span className="panelKicker">服务端为唯一权限依据</span><h2>全接口对象权限矩阵</h2></div><span>{operations.length} 项</span></div>
        <div className="securityFilters">
          <label><span>搜索路径、对象或角色</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="例如 privacy / researcher" /></label>
          <label><span>动作</span><select value={action} onChange={(event) => setAction(event.target.value)}>{["all", "create", "read", "update", "send", "export", "delete"].map((value) => <option key={value} value={value}>{value === "all" ? "全部动作" : value}</option>)}</select></label>
        </div>
        <div className="tableScroller" tabIndex={0} aria-label="对象权限矩阵，可横向滚动">
          <table className="securityMatrix"><thead><tr><th>方法与路径</th><th>对象/动作</th><th>允许角色</th><th>对象范围</th><th>幂等</th></tr></thead><tbody>{operations.map((item: SecurityAuthorizationOperation) => <tr key={item.operation_id}><td><strong>{item.method}</strong><code>{item.path}</code></td><td>{item.object_type}<small>{item.action}</small></td><td>{item.allowed_roles.join("、")}</td><td>{item.object_scope}</td><td>{item.idempotency.required ? "必须" : item.idempotency.supported ? "支持" : "—"}</td></tr>)}</tbody></table>
        </div>
      </section>

      <section className="panel" aria-label="安全事件">
        <div className="panelHeading"><div><span className="panelKicker">最小元数据</span><h2>安全事件与恢复</h2></div></div>
        {data?.events.length ? <div className="securityEventList">{data.events.map((item) => <article key={String(item.id)}><div><strong>{String(item.event_type)}</strong><span>{statusLabel(String(item.status))}</span></div><p>{String(item.severity)} · {String(item.created_at)}</p>{isAdmin && item.status === "open" ? <button className="secondaryButton" type="button" disabled={busy} onClick={() => void resolveEvent(String(item.id))}>标记已处理</button> : null}</article>)}</div> : <p className="emptyState">当前没有已记录的安全事件。</p>}
      </section>
    </section>
  );
}

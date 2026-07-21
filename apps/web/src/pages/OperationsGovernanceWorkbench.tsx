import { useCallback, useEffect, useMemo, useState } from "react";

import type { OperationsGovernanceWorkbench, OperationsIncident, OperationsReleasePackage } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const STATUS_LABELS: Record<string, string> = {
  proposed: "待回放/送审", under_review: "审核中", approved: "工程批准完成",
  changes_requested: "需修订", active_local_synthetic: "本地合成活动",
  active_production: "生产活动", paused: "已暂停", superseded: "已被新版本替代", retired: "已退役",
};

const INCIDENT_LABELS: Record<OperationsIncident["incident_type"], string> = {
  unauthorized_access: "越权访问", data_leak: "数据泄漏", severe_adverse_event: "严重不良事件", ai_safety_failure: "AI安全失败",
};

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "运营治理数据暂时无法读取，请稍后重试。";
}

function shortHash(value?: string): string {
  return value ? `${value.slice(0, 10)}…${value.slice(-6)}` : "—";
}

export function OperationsGovernanceWorkbench() {
  const actor = getStoredAuthUser();
  const isAdmin = actor?.role === "admin";
  const canEvidence = isAdmin || actor?.role === "supervisor";
  const [data, setData] = useState<OperationsGovernanceWorkbench | null>(null);
  const [packageVersion, setPackageVersion] = useState(`ops-${new Date().toISOString().slice(0, 10)}-v1`);
  const [riskLevel, setRiskLevel] = useState<"low" | "medium" | "high">("high");
  const [incidentType, setIncidentType] = useState<OperationsIncident["incident_type"]>("ai_safety_failure");
  const [incidentCapability, setIncidentCapability] = useState("");
  const [status, setStatus] = useState("正在核对能力、发布包、回放、漂移和停用证据…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const next = await safeHomeApi.getOperationsGovernanceWorkbench();
    setData(next);
    setIncidentCapability((current) => current || next.registry.capabilities[0]?.id || "");
    setStatus("本地运营工程证据已更新；人工、伦理、云、真机和生产批准仍未签署。");
  }, []);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  const summary = useMemo(() => ({
    capabilities: data?.registry.capability_count || 0,
    operations: data?.registry.operation_count || 0,
    cards: data?.asset_cards.cards.length || 0,
    incidents: data?.incidents.filter((item) => item.status !== "closed").length || 0,
  }), [data]);

  async function act(label: string, callback: () => Promise<unknown>) {
    setBusy(true); setStatus(label);
    try { await callback(); await load(); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  function approvalDomain(): "research" | "psychology" | "security" | null {
    if (actor?.role === "researcher") return "research";
    if (actor?.role === "supervisor") return "psychology";
    if (actor?.role === "admin") return "security";
    return null;
  }

  function packageActions(item: OperationsReleasePackage) {
    const domain = approvalDomain();
    return (
      <div className="opsActionRow">
        {["proposed", "changes_requested", "paused"].includes(item.status) ? <button type="button" className="secondaryButton" disabled={busy} onClick={() => void act("正在执行固定合成回放…", () => safeHomeApi.runOperationsReplay(item.id))}>运行固定回放</button> : null}
        {["proposed", "changes_requested"].includes(item.status) ? <button type="button" className="primaryButton" disabled={busy} onClick={() => void act("正在送交独立审核…", () => safeHomeApi.submitOperationsPackage(item.id))}>送审</button> : null}
        {item.status === "under_review" ? <button type="button" className="secondaryButton" disabled={busy} onClick={() => void act("正在登记独立审核证据…", () => safeHomeApi.reviewOperationsPackage(item.id, { decision: "recommended", evidence_ref: "evidence://web/task34/independent-review" }))}>登记审核建议</button> : null}
        {item.status === "under_review" && domain ? <button type="button" className="secondaryButton" disabled={busy} onClick={() => void act(`正在登记${domain}批准证据…`, () => safeHomeApi.approveOperationsPackage(item.id, { domain, decision: "approved", evidence_ref: `evidence://web/task34/${domain}` }))}>登记本角色批准</button> : null}
        {item.status === "approved" && isAdmin ? <button type="button" className="primaryButton" disabled={busy} onClick={() => void act("正在切换本地合成发布指针…", () => safeHomeApi.releaseOperationsPackage(item.id))}>仅发布到本地合成环境</button> : null}
        {item.status === "active_local_synthetic" && isAdmin ? <button type="button" className="dangerButton" disabled={busy} onClick={() => void act("正在暂停发布包…", () => safeHomeApi.changeOperationsPackageState(item.id, "pause", "human_selected_safety_pause"))}>立即暂停</button> : null}
        {item.status === "paused" && isAdmin ? <button type="button" className="primaryButton" disabled={busy} onClick={() => void act("正在核对暂停后的新回放证据并恢复…", () => safeHomeApi.changeOperationsPackageState(item.id, "resume", "human_selected_verified_resume"))}>核对后恢复</button> : null}
        {item.status === "superseded" && isAdmin ? <button type="button" className="secondaryButton" disabled={busy} onClick={() => void act("正在原子恢复不可变旧包…", () => safeHomeApi.rollbackOperationsRuntime(item.id))}>回滚到此版本</button> : null}
      </div>
    );
  }

  return (
    <section className="dashboardShell operationsGovernance" aria-label="内容、数据与模型运营治理工作台">
      <div className="dashboardHeader operationsHeader">
        <div>
          <p className="eyebrow">T34 · 可追溯、可停用、可恢复</p>
          <h1>内容、数据与模型运营治理</h1>
          <p className="summary">把能力、制品、固定回放、专业批准、漂移复核和严重事件放进同一条可审计链路。工程完成与允许上线始终分开。</p>
        </div>
        <span className="gateBadge gateBlocked">生产发布未批准</span>
      </div>

      <div className="status" role="status" aria-live="polite">{status}</div>

      <div className="opsMetricStrip" aria-label="运营治理摘要">
        <article><strong>{summary.capabilities}</strong><span>能力模块</span></article>
        <article><strong>{summary.operations}</strong><span>机器契约操作</span></article>
        <article><strong>{summary.cards}</strong><span>数据/规则/模型卡</span></article>
        <article><strong>{summary.incidents}</strong><span>待处理事件</span></article>
      </div>

      <section className="panel" aria-labelledby="capability-title">
        <div className="panelHeading"><div><span className="panelKicker">能力与开放边界</span><h2 id="capability-title">每项能力都有用途、角色、开关和回滚</h2></div><span>{data?.registry.operation_count || 0} 项操作全覆盖</span></div>
        <div className="opsCapabilityGrid">
          {(data?.registry.capabilities || []).map((item) => <article key={item.id}><div><strong>{item.title}</strong><span>{item.data.sensitivity}</span></div><p>{item.intended_use}</p><small>{item.open_roles.join("、")} · {item.operation_ids.length}项操作</small><small>负责人：{item.owner.accountable_role}（{item.owner.named_owner_status}）</small></article>)}
        </div>
        <p className="boundaryCallout">临时展示越权继续保留，但正式权限验收为未通过；治疗性评估仅允许合成L0，真实参与者仍被D01—D26及伦理责任链阻断。</p>
      </section>

      <div className="opsColumns">
        <section className="panel" aria-labelledby="package-title">
          <div className="panelHeading"><div><span className="panelKicker">不可变发布包</span><h2 id="package-title">新修订必须新版本</h2></div></div>
          <div className="opsCreateRow">
            <label><span>版本</span><input value={packageVersion} onChange={(event) => setPackageVersion(event.target.value)} /></label>
            <label><span>风险级别</span><select value={riskLevel} onChange={(event) => setRiskLevel(event.target.value as typeof riskLevel)}><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label>
            <button type="button" className="primaryButton" disabled={busy || !packageVersion.trim()} onClick={() => void act("正在生成内容寻址不可变包…", () => safeHomeApi.createOperationsPackage({ package_version: packageVersion.trim(), risk_level: riskLevel, target_environment: "local_synthetic" }))}>提出发布包</button>
          </div>
          <div className="opsPackageList">
            {(data?.packages || []).map((item) => <article key={item.id}><div className="opsPackageHeading"><div><strong>{item.package_version}</strong><span>{STATUS_LABELS[item.status] || item.status}</span></div><small>{item.artifact_count}个制品 · {shortHash(item.manifest_hash)}</small></div><p>{item.risk_level}风险 · {item.target_environment} · 提出者 {item.proposed_by}</p><div className="opsApprovalDots" aria-label="专业批准状态">{["research", "psychology", "security"].map((domain) => <span key={domain} className={item.approvals?.some((approval) => approval.domain === domain && approval.decision === "approved") ? "isReady" : "isPending"}>{domain}</span>)}</div>{packageActions(item)}</article>)}
            {!data?.packages.length ? <p className="emptyState">尚无发布包。生成包不会自动批准或上线。</p> : null}
          </div>
        </section>

        <section className="panel" aria-labelledby="replay-title">
          <span className="panelKicker">固定合成回放</span>
          <h2 id="replay-title">推荐、拒答、风险阻断与文案差异</h2>
          <div className="opsReplayList">{(data?.packages || []).flatMap((item) => (item.replay_runs || []).slice(0, 1).map((run) => <article key={run.id}><div><strong>{item.package_version}</strong><span className={run.high_severity_regressions ? "isBlocked" : "isReady"}>{run.status}</span></div><p>{run.metrics.passed}/{run.metrics.total}通过 · 高严重度回归{run.high_severity_regressions} · 文案差异{run.wording_diff_count}</p></article>))}</div>
          <p className="boundaryCallout">高严重度回归直接阻断发布。固定集合通过只说明工程基线，没有证明现实安全或有效。</p>
        </section>
      </div>

      <div className="opsColumns">
        <section className="panel" aria-labelledby="drift-title">
          <div className="panelHeading"><div><span className="panelKicker">漂移复核</span><h2 id="drift-title">只触发人工检查</h2></div><button type="button" className="secondaryButton" disabled={busy} onClick={() => void act("正在汇总无正文的运营指标…", () => safeHomeApi.createOperationsMonitorSnapshot())}>生成聚合快照</button></div>
          <div className="opsDriftList">{(data?.monitor_snapshots || []).slice(0, 5).map((item) => <article key={item.id}><div><strong>{item.environment} · {item.window_days}天</strong><span className={item.review_required ? "isPending" : "isReady"}>{item.review_required ? "需人工复核" : "暂无阈值信号"}</span></div><p>{item.drift_signals.map((signal) => signal.metric).join("、") || "当前没有超过工程阈值的聚合信号"}</p></article>)}</div>
          <p className="boundaryCallout">覆盖率、未知标签、推荐集中、不符合、不适、人工升级和供应商错误只用于运营复核，不判断参与者或家庭变差。</p>
        </section>

        <section className="panel" aria-labelledby="incident-title">
          <div className="panelHeading"><div><span className="panelKicker">事件与停用</span><h2 id="incident-title">先止损，再保全证据</h2></div></div>
          <div className="opsIncidentForm">
            <label><span>能力</span><select value={incidentCapability} onChange={(event) => setIncidentCapability(event.target.value)}>{(data?.registry.capabilities || []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
            <label><span>事件类型</span><select value={incidentType} onChange={(event) => setIncidentType(event.target.value as OperationsIncident["incident_type"])}>{Object.entries(INCIDENT_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <button type="button" className="dangerButton" disabled={busy || !incidentCapability} onClick={() => void act("正在停用能力并排队最小化通知…", () => safeHomeApi.reportOperationsIncident({ capability_id: incidentCapability, incident_type: incidentType, severity: "critical", summary_code: "human_reported_governance_incident", evidence_refs: ["evidence://web/task34/human-investigation-required"] }))}>报告并停用</button>
          </div>
          <div className="opsIncidentList">{(data?.incidents || []).map((item) => <article key={item.id}><div><strong>{INCIDENT_LABELS[item.incident_type]}</strong><span>{item.status}</span></div><p>{item.capability_id} · 证据保全 {shortHash(item.evidence_hold_hash)}</p><small>{item.notifications.length}个通知任务 · 能力保持停用</small></article>)}</div>
        </section>
      </div>

      <section className="panel opsExternalGate" aria-label="外部发布证据">
        <div><span className="panelKicker">人工门禁</span><h2>工程完成不等于发布批准</h2><p>真实负责人、伦理、隐私安全、测试云、微信开发者工具、Android/iOS和生产双人控制仍需外部证据。</p></div>
        {canEvidence ? <button type="button" className="secondaryButton" disabled={busy} onClick={() => void act("正在生成待外部核对证据包…", () => safeHomeApi.createOperationsEvidencePackage())}>生成待人工核对证据包</button> : null}
      </section>
    </section>
  );
}

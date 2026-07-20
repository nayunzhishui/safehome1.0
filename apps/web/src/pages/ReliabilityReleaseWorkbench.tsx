import { useCallback, useEffect, useMemo, useState } from "react";

import type { ReliabilityWorkbench } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const DRILL_LABELS: Record<string, string> = {
  content_missing: "内容文件缺失",
  database_timeout: "数据库超时",
  provider_failure: "外部服务失败",
  token_invalidated: "登录凭证失效",
  duplicate_message: "重复消息",
  artifact_corrupted: "模型制品损坏",
};

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "可靠性证据暂时无法读取，请稍后重试。";
}

function percent(value: number | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 1000) / 10}%` : "—";
}

export function ReliabilityReleaseWorkbench() {
  const actor = getStoredAuthUser();
  const isAdmin = actor?.role === "admin";
  const canPackage = actor?.role === "admin" || actor?.role === "supervisor";
  const [data, setData] = useState<ReliabilityWorkbench | null>(null);
  const [scenario, setScenario] = useState("provider_failure");
  const [status, setStatus] = useState("正在汇总请求链路、可靠任务与恢复证据…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const next = await safeHomeApi.getReliabilityWorkbench();
    setData(next);
    setStatus("工程证据已更新；本地结果仍不能替代测试云观察和人工复核。");
  }, []);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  const latestMetrics = useMemo(() => data?.slo_snapshots[0]?.metrics || {}, [data]);
  const deadLetters = (data?.jobs || []).filter((item) => item.status === "dead_letter");

  async function act(label: string, callback: () => Promise<unknown>) {
    setBusy(true); setStatus(label);
    try { await callback(); await load(); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  return (
    <section className="dashboardShell reliabilityWorkbench" aria-label="可靠性与发布工程工作台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">T32 · 可恢复工程</p>
          <h1>可靠性与发布证据</h1>
          <p className="summary">统一观察七条关键旅程、可靠任务、故障演练和功能开关。只记录技术元数据，不采集参与者原文、令牌或请求正文。</p>
        </div>
        <span className="gateBadge gateBlocked">测试云阈值尚未冻结</span>
      </div>

      <div className="status" role="status" aria-live="polite">{status}</div>

      <ol className="releaseSignalRail" aria-label="发布证据路径">
        <li className="isReady"><span>1</span><div><strong>本地机器证据</strong><small>请求追踪、幂等、租约、退避、死信与回滚已进入同一闭环</small></div></li>
        <li className="isPending"><span>2</span><div><strong>测试云观察</strong><small>等待 CloudBase 网关、MySQL 恢复、连续窗口与真机证据</small></div></li>
        <li className="isBlocked"><span>3</span><div><strong>人工上线门禁</strong><small>值班负责人、安全隐私伦理复核和上线决定均保持待办</small></div></li>
      </ol>

      <div className="reliabilityColumns">
        <section className="panel" aria-label="旅程观测">
          <div className="panelHeading"><div><span className="panelKicker">七条核心旅程</span><h2>最近本地观测</h2></div>{isAdmin ? <button className="primaryButton" type="button" disabled={busy} onClick={() => void act("正在生成本地SLO快照…", () => safeHomeApi.createReliabilitySloSnapshot())}>生成快照</button> : null}</div>
          <div className="journeyMetricList">
            {(data?.registry.journeys || []).map((journey) => {
              const metric = latestMetrics[journey.journey_id];
              return <article key={journey.journey_id}><div><strong>{journey.label}</strong><small>{metric?.requests ?? 0} 次请求</small></div><dl><div><dt>成功</dt><dd>{percent(metric?.success_rate)}</dd></div><div><dt>P95</dt><dd>{metric ? `${metric.latency_p95_ms} ms` : "—"}</dd></div><div><dt>恢复</dt><dd>{percent(metric?.recovery_rate)}</dd></div></dl></article>;
            })}
          </div>
          <p className="boundaryCallout">当前数字仅是本地合成与工程请求证据，不用于承诺正式环境服务水平。</p>
        </section>

        <section className="panel" aria-label="可靠任务与恢复">
          <div className="panelHeading"><div><span className="panelKicker">可重放、可追责</span><h2>任务恢复队列</h2></div><span>{deadLetters.length} 项待人工恢复</span></div>
          <div className="reliableJobList">
            {(data?.jobs || []).slice(0, 8).map((job) => <article key={job.id}><div><strong>{job.job_type}</strong><span className={`jobState jobState-${job.status}`}>{job.status}</span></div><p>{job.source_type} · 尝试 {job.attempt_count}/{job.max_attempts}</p>{isAdmin && job.status === "dead_letter" ? <button className="secondaryButton" type="button" disabled={busy} onClick={() => void act("正在恢复死信任务…", () => safeHomeApi.recoverReliabilityJob(job.id))}>确认依赖恢复后重试</button> : null}</article>)}
            {!data?.jobs.length ? <p className="emptyState">当前没有排队任务；正文仍保留在原业务表中。</p> : null}
          </div>
        </section>
      </div>

      <div className="reliabilityColumns">
        <section className="panel" aria-label="功能开关">
          <div className="panelHeading"><div><span className="panelKicker">版本化、按角色、可回滚</span><h2>功能开关</h2></div></div>
          <div className="featureFlagList">{(data?.feature_flags || []).map((flag) => <article key={flag.flag_name}><div><strong>{flag.flag_name}</strong><span>{flag.enabled ? "开启" : "关闭"}</span></div><p>v{flag.version} · {flag.rollout_percent}% · {flag.role_scope.join("、")}</p></article>)}</div>
        </section>

        <section className="panel" aria-label="故障演练和证据包">
          <div className="panelHeading"><div><span className="panelKicker">固定合成场景</span><h2>恢复演练</h2></div></div>
          <label className="reliabilitySelect"><span>演练场景</span><select value={scenario} onChange={(event) => setScenario(event.target.value)} disabled={!isAdmin || busy}>{(data?.registry.fault_scenarios || []).map((item) => <option key={item.scenario} value={item.scenario}>{DRILL_LABELS[item.scenario] || item.scenario}</option>)}</select></label>
          <div className="dashboardActions">
            {isAdmin ? <button className="primaryButton" type="button" disabled={busy} onClick={() => void act("正在运行固定合成故障演练…", () => safeHomeApi.runReliabilityDrill(scenario))}>运行演练</button> : null}
            {canPackage ? <button className="secondaryButton" type="button" disabled={busy} onClick={() => void act("正在生成脱敏证据包…", () => safeHomeApi.createReliabilityEvidencePackage())}>生成证据包</button> : null}
          </div>
          <p className="boundaryCallout">证据包不含参与者正文，也不会代替值班、安全隐私伦理、真机或上线负责人作出决定。</p>
        </section>
      </div>
    </section>
  );
}

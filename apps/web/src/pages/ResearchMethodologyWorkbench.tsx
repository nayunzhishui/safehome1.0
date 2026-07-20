import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  ResearchMethodologyCheck,
  ResearchMethodologyConfig,
  ResearchMethodologyEvidence,
  ResearchMethodologyRegistry,
  ResearchMethodologySimulation,
  ResearchMethodologyVersion,
} from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "操作失败，请核对研究方法门禁和账号权限。";
}

export function ResearchMethodologyWorkbench() {
  const actor = getStoredAuthUser();
  const isAdmin = actor?.role === "admin";
  const canPackage = ["supervisor", "admin"].includes(actor?.role || "");
  const [config, setConfig] = useState<ResearchMethodologyConfig | null>(null);
  const [registry, setRegistry] = useState<ResearchMethodologyRegistry | null>(null);
  const [versions, setVersions] = useState<ResearchMethodologyVersion[]>([]);
  const [evidence, setEvidence] = useState<ResearchMethodologyEvidence>({ checks: [], simulations: [], packages: [] });
  const [latestCheck, setLatestCheck] = useState<ResearchMethodologyCheck | null>(null);
  const [latestSimulation, setLatestSimulation] = useState<ResearchMethodologySimulation | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("正在读取冻结前研究方法结构…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [nextConfig, nextRegistry, nextVersions, nextEvidence] = await Promise.all([
      safeHomeApi.getResearchMethodologyConfig(),
      safeHomeApi.getResearchMethodologyRegistry(),
      safeHomeApi.listResearchMethodologyVersions(),
      safeHomeApi.getResearchMethodologyEvidence(),
    ]);
    setConfig(nextConfig);
    setRegistry(nextRegistry);
    setVersions(nextVersions.items);
    setEvidence(nextEvidence);
    setStatus("结构已更新；人工冻结和主要结果分析仍未开放。");
  }, []);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  async function runAction(label: string, action: () => Promise<void>) {
    setBusy(true); setStatus(`${label}…`);
    try { await action(); setStatus(`${label}完成；仅形成工程证据。`); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  const measures = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return (registry?.measures || []).filter((item) => !normalized || `${item.display_name} ${item.measure_id}`.toLowerCase().includes(normalized));
  }, [query, registry]);
  const ninePoint = registry?.measures.find((item) => item.measure_id === "regulatory_focus_relationship_18");
  const latestVersion = versions[0];

  return (
    <section className="dashboardShell methodologyWorkbench" aria-label="研究方法冻结准备工作台">
      <div className="dashboardHeader">
        <div><p className="eyebrow">T30 · 冻结前结构</p><h1>心理测量与研究方法工作台</h1><p className="summary">先定义问题、分母、量尺、缺失和分析边界，再由真人核对与签字。此页不读取真实结局，也不提供自动冻结按钮。</p></div>
        <span className="gateBadge gateBlocked">人工签字待完成</span>
      </div>
      <div className="status" role="status" aria-live="polite">{status}</div>

      <section className="methodologyBoundary" aria-label="不可越过的研究边界">
        <div><span className="panelKicker">当前阶段</span><h2>{config?.status === "draft_before_freeze" ? "结构草案已建立，尚未正式冻结" : "正在读取门禁"}</h2><p>{config?.boundary_notice || "研究负责人、伦理/治理、数据和工程负责人均需线下核对证据。"}</p></div>
        <dl className="aiQaFacts">
          <div><dt>真实结局读取</dt><dd>0 行</dd></div><div><dt>验证性分析</dt><dd>关闭</dd></div>
          <div><dt>自动签字</dt><dd>禁止</dd></div><div><dt>未决事项</dt><dd>{config?.unresolved_blocker_count ?? "—"} 项</dd></div>
        </dl>
      </section>

      <div className="methodologyColumns">
        <section className="panel" aria-label="版本与机器证据">
          <div className="panelHeading"><div><span className="panelKicker">可复现结构</span><h2>版本与机器检查</h2></div>{isAdmin ? <button className="secondaryButton" type="button" disabled={busy} onClick={() => void runAction("同步不可变注册表", async () => { await safeHomeApi.syncResearchMethodologyRegistry(); await load(); })}>同步版本</button> : null}</div>
          {latestVersion ? <div className="versionPlate"><strong>{latestVersion.version}</strong><code>{latestVersion.registry_hash.slice(0, 16)}…</code><span>{latestVersion.status}</span></div> : <p className="emptyState">管理员同步后才能运行机器检查和合成仿真。</p>}
          <div className="methodologyActions">
            <button className="primaryButton" type="button" disabled={busy || !latestVersion || !config?.workbench_enabled} onClick={() => void runAction("运行机器结构检查", async () => { const result = await safeHomeApi.runResearchMethodologyChecks(latestVersion?.id); setLatestCheck(result); await load(); })}>运行结构检查</button>
            <button className="secondaryButton" type="button" disabled={busy || !latestVersion || !config?.workbench_enabled} onClick={() => void runAction("运行合成可行性仿真", async () => { const result = await safeHomeApi.runResearchMethodologySimulation(latestVersion?.id); setLatestSimulation(result); await load(); })}>运行合成仿真</button>
            {canPackage ? <button className="secondaryButton" type="button" disabled={busy || evidence.checks.length === 0 || evidence.simulations.length === 0} onClick={() => void runAction("生成待真人签字证据包", async () => { await safeHomeApi.createResearchMethodologyEvidencePackage(latestVersion?.id); await load(); })}>生成证据包</button> : null}
          </div>
          <div className="methodologyEvidenceGrid">
            <div><strong>{latestCheck?.hard_check_passed ?? (evidence.checks.length ? "已留存" : "待运行")}</strong><span>结构检查</span></div>
            <div><strong>{latestSimulation?.metrics.contains_real_data === false || evidence.simulations.length ? "仅合成" : "待运行"}</strong><span>仿真数据</span></div>
            <div><strong>{evidence.packages.length}</strong><span>待签字证据包</span></div>
          </div>
          <p className="boundaryCallout">证据包状态固定为 draft_for_human_signature；生成证据包不等于研究、伦理或发布批准。</p>
        </section>

        <section className="panel" aria-label="研究问题与报告规范">
          <div className="panelHeading"><div><span className="panelKicker">先问题，后分析</span><h2>五条产品研究线</h2></div></div>
          <ol className="methodologyQuestionList">{(registry?.product_lines || []).map((item) => <li key={item.id}><strong>{item.primary_question}</strong><span>{item.prohibited_interpretation}</span></li>)}</ol>
          <h3 className="sectionSubheading">报告规范映射</h3>
          <div className="standardChips">{(registry?.reporting_standards || []).map((item) => <a key={item.id} href={item.official_url} target="_blank" rel="noreferrer"><strong>{item.id}</strong><span>{item.status}</span></a>)}</div>
        </section>
      </div>

      <section className="panel" aria-label="测量登记">
        <div className="panelHeading"><div><span className="panelKicker">{registry?.measures.length || 0} 项测量</span><h2>测量、量尺与用途登记</h2></div><label className="methodologySearch"><span>筛选测量</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="名称或 ID" /></label></div>
        <div className="scoreSeparationNotice"><div><strong>九点原分</strong><span>1–9 · raw_scores_json</span></div><span aria-hidden="true">→</span><div><strong>模型兼容输入</strong><span>1–5 · transformed_scores_json</span></div><p>{ninePoint ? "两个量尺分字段、分版本保存；页面和报告必须标注量尺。" : "正在读取九点量表登记。"}</p></div>
        <div className="measureTableWrap"><table className="methodologyTable"><thead><tr><th>测量</th><th>题数</th><th>证据/审核</th><th>冻结状态</th></tr></thead><tbody>{measures.map((item) => <tr key={item.measure_id}><td><strong>{item.display_name}</strong><code>{item.measure_id}</code></td><td>{item.item_count}</td><td>{String(item.review_status || "待核验")}</td><td><span className="gateBadge gateBlocked">{item.freeze_status}</span></td></tr>)}</tbody></table></div>
      </section>

      <div className="methodologyColumns compact">
        <section className="panel"><span className="panelKicker">数据质量</span><h2>缺失与纵向计划</h2><p>区分未暴露、未开始、中断、技术失败、主动撤回和失访；不默认填 0、不默认均值插补、不把横断面聚类解释为个人发展轨迹。</p></section>
        <section className="panel"><span className="panelKicker">仍需真人决定</span><h2>冻结前阻断项</h2><ul className="blockerList">{(registry?.unresolved_blockers || []).map((item) => <li key={item}>{item}</li>)}</ul></section>
      </div>
    </section>
  );
}

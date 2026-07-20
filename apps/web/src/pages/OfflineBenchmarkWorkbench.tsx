import { useCallback, useEffect, useMemo, useState } from "react";

import type { OfflineAgreementSummary, OfflineBenchmarkConfig, OfflineBenchmarkRun, OfflineBlindCase, OfflineDatasetCard } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const LABELS = ["anxiety", "fear", "anger", "irritation", "sadness", "helplessness", "guilt", "shame", "calm", "positive", "unmapped"];

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "操作失败，请核对权限和离线门禁。";
}

export function OfflineBenchmarkWorkbench() {
  const actor = getStoredAuthUser();
  const isAdmin = actor?.role === "admin";
  const canReview = ["supervisor", "admin"].includes(actor?.role || "");
  const [config, setConfig] = useState<OfflineBenchmarkConfig | null>(null);
  const [cards, setCards] = useState<OfflineDatasetCard[]>([]);
  const [runs, setRuns] = useState<OfflineBenchmarkRun[]>([]);
  const [cases, setCases] = useState<OfflineBlindCase[]>([]);
  const [agreement, setAgreement] = useState<OfflineAgreementSummary | null>(null);
  const [selectedCase, setSelectedCase] = useState<OfflineBlindCase | null>(null);
  const [label, setLabel] = useState("unmapped");
  const [status, setStatus] = useState("正在读取离线基准门禁…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [nextConfig, cardList, runList, blindCases] = await Promise.all([
      safeHomeApi.getOfflineBenchmarkConfig(),
      safeHomeApi.listOfflineDatasetCards(),
      safeHomeApi.listOfflineBenchmarkRuns(),
      safeHomeApi.listOfflineBlindCases(),
    ]);
    setConfig(nextConfig); setCards(cardList.items); setRuns(runList.items); setCases(blindCases.items);
    setSelectedCase((current) => current || blindCases.items[0] || null);
    if (canReview) setAgreement(await safeHomeApi.getOfflineAgreement());
    setStatus("离线基准状态已更新。外部数据仍未下载。");
  }, [canReview]);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  async function runAction(labelText: string, action: () => Promise<void>) {
    setBusy(true); setStatus(`${labelText}…`);
    try { await action(); setStatus(`${labelText}完成。`); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  const blockedCards = useMemo(() => cards.filter((card) => card.ingest_status.startsWith("blocked_")), [cards]);
  const latest = runs[0];

  return (
    <section className="dashboardShell benchmarkWorkbench" aria-label="公开数据与离线算法基准">
      <div className="dashboardHeader">
        <div><p className="eyebrow">T29 · 仅限离线研究</p><h1>公开数据与算法基准</h1><p className="summary">先核对许可和内容权利，再比较规则与网络算法。公开不等于可下载，也不等于可训练。</p></div>
        <span className="gateBadge gateBlocked">生产替换关闭</span>
      </div>
      <div className="status" role="status" aria-live="polite">{status}</div>

      <section className="benchmarkBoundary" aria-label="当前边界">
        <div><span className="panelKicker">治理状态</span><h2>{config?.enabled ? "合成离线基准可运行" : "离线基准已停用"}</h2><p>{config?.boundary_notice || "正在读取数据集登记。"}</p></div>
        <dl className="aiQaFacts">
          <div><dt>外部下载</dt><dd>关闭</dd></div><div><dt>真实参与者原文</dt><dd>禁止</dd></div>
          <div><dt>生产规则替换</dt><dd>禁止</dd></div><div><dt>合成案例</dt><dd>{config?.synthetic_case_count || 0} 条</dd></div>
        </dl>
      </section>

      <div className="benchmarkColumns">
        <section className="panel" aria-label="数据集卡">
          <div className="panelHeading"><div><span className="panelKicker">许可先行</span><h2>数据集卡</h2></div>{isAdmin ? <button className="secondaryButton" disabled={busy} type="button" onClick={() => void runAction("同步登记", async () => { await safeHomeApi.syncOfflineDatasetCards(); await load(); })}>同步登记</button> : null}</div>
          {cards.length ? <div className="datasetCardList">{cards.map((card) => <article key={card.id}><div><strong>{card.name}</strong><span>{card.language} · {card.platform}</span></div><span className={`gateBadge ${card.ingest_status.includes("ready") ? "gatePassed" : "gateBlocked"}`}>{card.ingest_status}</span><p>{card.review_note}</p><small>{card.license} · {card.content_rights_status}</small></article>)}</div> : <p className="emptyState">管理员同步本地登记后显示。同步不会下载外部数据。</p>}
          <p className="boundaryCallout">当前有 {blockedCards.length} 个外部来源只登记链接；权利未批准时本地路径和哈希必须为空。</p>
        </section>

        <section className="panel" aria-label="离线运行">
          <div className="panelHeading"><div><span className="panelKicker">工程证据</span><h2>合成基准运行</h2></div></div>
          <div className="benchmarkRunActions"><button className="primaryButton" disabled={busy || !config?.enabled} type="button" onClick={() => void runAction("运行情感规则基准", async () => { await safeHomeApi.runOfflineBenchmark("affect"); await load(); })}>情感规则基准</button><button className="secondaryButton" disabled={busy || !config?.enabled} type="button" onClick={() => void runAction("运行网络算法基准", async () => { await safeHomeApi.runOfflineBenchmark("network"); await load(); })}>网络算法基准</button></div>
          {latest ? <article className="benchmarkResult"><span className="gateBadge gatePassed">{latest.status}</span><h3>{latest.benchmark_type}</h3><div className="metricGrid compactMetrics"><div><strong>{String(latest.metrics.sample_count ?? (Array.isArray(latest.metrics.synthetic_graphs) ? latest.metrics.synthetic_graphs.length : "—"))}</strong><span>样本/图组</span></div><div><strong>{String(latest.metrics.macro_f1_against_generator_seed ?? latest.metrics.passed ?? "—")}</strong><span>F1/检查</span></div><div><strong>{latest.raw_text_included ? "是" : "否"}</strong><span>含原文</span></div><div><strong>{latest.production_replacement_allowed ? "是" : "否"}</strong><span>可替换生产</span></div></div><p>证据哈希：<code>{latest.artifact_hash.slice(0, 16)}…</code></p></article> : <p className="emptyState">尚无运行。运行结果只用于工程比较。</p>}
        </section>
      </div>

      <section className="panel" aria-label="双人盲标">
        <div className="panelHeading"><div><span className="panelKicker">人工工作尚未完成</span><h2>合成中文双人盲标</h2></div><span className="gateBadge gateBlocked">不是人工金标准</span></div>
        <p className="mutedText">标注者看不到生成标签或他人答案。至少200例、两名独立标注者、一致性达标和督导裁决后，才可申请人工金标准发布。</p>
        <div className="blindAnnotationGrid">
          <div className="blindCaseList" role="listbox" aria-label="合成案例">{cases.map((item) => <button className={selectedCase?.id === item.id ? "selected" : ""} type="button" key={item.id} onClick={() => setSelectedCase(item)}><span>{item.id}</span><strong>{item.text}</strong><em>{item.already_annotated ? "已标" : "待标"}</em></button>)}</div>
          <div className="annotationForm">{selectedCase ? <><h3>{selectedCase.id}</h3><p>{selectedCase.text}</p><label className="fieldLabel" htmlFor="benchmark-label">主要情绪标签</label><select id="benchmark-label" value={label} onChange={(event) => setLabel(event.target.value)}>{LABELS.map((item) => <option key={item}>{item}</option>)}</select><button className="primaryButton" disabled={busy} type="button" onClick={() => void runAction("保存盲标", async () => { await safeHomeApi.saveOfflineAnnotation(selectedCase.id, { emotion_label: label, valence: label === "positive" || label === "calm" ? 0.7 : label === "unmapped" ? 0 : -0.7, arousal: label === "calm" ? 0.2 : 0.7, context: "synthetic_daily_reflection", reflex_node: "emotion" }); await load(); })}>保存当前标注</button></> : <p className="emptyState">没有可标注案例。</p>}</div>
        </div>
        {canReview ? <p className="boundaryCallout">双人完整案例 {agreement?.complete_double_annotated_cases || 0}/200；情绪κ {agreement?.emotion_cohen_kappa ?? "待计算"}；人工金标准仍未发布。</p> : null}
      </section>
    </section>
  );
}

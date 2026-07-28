import { useCallback, useEffect, useMemo, useState } from "react";

import type { OfflineAdjudicationQueueItem, OfflineAgreementSummary, OfflineAnnotationGovernance, OfflineBenchmarkConfig, OfflineBenchmarkRun, OfflineBlindCase, OfflineDatasetCard, OfflineEmotionLabel, OfflineModelMonitoringStatus, OfflineModelReleaseGateStatus, OfflineModelReviewQueueItem, OfflineModelShadowRun, OfflineModelVersion, OfflineSplitReport } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const LABELS: OfflineEmotionLabel[] = ["anxiety", "fear", "anger", "irritation", "sadness", "helplessness", "guilt", "shame", "calm", "positive", "unknown", "unmapped"];

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
  const [governance, setGovernance] = useState<OfflineAnnotationGovernance | null>(null);
  const [adjudicationQueue, setAdjudicationQueue] = useState<OfflineAdjudicationQueueItem[]>([]);
  const [splitReport, setSplitReport] = useState<OfflineSplitReport | null>(null);
  const [modelVersions, setModelVersions] = useState<OfflineModelVersion[]>([]);
  const [shadowRuns, setShadowRuns] = useState<OfflineModelShadowRun[]>([]);
  const [shadowQueue, setShadowQueue] = useState<OfflineModelReviewQueueItem[]>([]);
  const [codeCommit, setCodeCommit] = useState("");
  const [monitoring, setMonitoring] = useState<OfflineModelMonitoringStatus | null>(null);
  const [releaseGate, setReleaseGate] = useState<OfflineModelReleaseGateStatus | null>(null);
  const [selectedCase, setSelectedCase] = useState<OfflineBlindCase | null>(null);
  const [labels, setLabels] = useState<OfflineEmotionLabel[]>(["unknown"]);
  const [intensity, setIntensity] = useState<0 | 1 | 2 | 3 | 4>(0);
  const [polarity, setPolarity] = useState<"affirmed" | "negated" | "uncertain">("uncertain");
  const [needsHuman, setNeedsHuman] = useState(false);
  const [rationale, setRationale] = useState("");
  const [adjudicationLabel, setAdjudicationLabel] = useState<OfflineEmotionLabel>("unknown");
  const [adjudicationRationale, setAdjudicationRationale] = useState("");
  const [status, setStatus] = useState("正在读取离线基准门禁…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [nextConfig, cardList, runList, blindCases, nextGovernance, versionList, shadowRunList, shadowQueueList, monitorStatus, releaseGateStatus] = await Promise.all([
      safeHomeApi.getOfflineBenchmarkConfig(),
      safeHomeApi.listOfflineDatasetCards(),
      safeHomeApi.listOfflineBenchmarkRuns(),
      safeHomeApi.listOfflineBlindCases(),
      safeHomeApi.getOfflineAnnotationGovernance(),
      safeHomeApi.listOfflineModelVersions(),
      safeHomeApi.listOfflineModelShadowRuns(),
      safeHomeApi.listOfflineModelReviewQueue(),
      safeHomeApi.getOfflineModelMonitoring(),
      safeHomeApi.getOfflineModelReleaseGate(),
    ]);
    setGovernance(nextGovernance);
    setConfig(nextConfig); setCards(cardList.items); setRuns(runList.items); setCases(blindCases.items);
    setModelVersions(versionList.items); setShadowRuns(shadowRunList.items); setShadowQueue(shadowQueueList.items);
    setMonitoring(monitorStatus);
    setReleaseGate(releaseGateStatus);
    setSelectedCase((current) => current || blindCases.items[0] || null);
    if (canReview) {
      const [nextAgreement, nextQueue, nextSplit] = await Promise.all([
        safeHomeApi.getOfflineAgreement(),
        safeHomeApi.listOfflineAdjudicationQueue(),
        safeHomeApi.getOfflineSplitReport(),
      ]);
      setAgreement(nextAgreement);
      setAdjudicationQueue(nextQueue.items);
      setSplitReport(nextSplit);
    }
    setStatus("离线基准状态已更新。外部数据仍未下载。");
  }, [canReview]);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  async function runAction(labelText: string, action: () => Promise<void>) {
    setBusy(true); setStatus(`${labelText}…`);
    try { await action(); setStatus(`${labelText}完成。`); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  const blockedCards = useMemo(() => cards.filter((card) => card.ingest_status.startsWith("blocked_")), [cards]);
  const latest = runs[0];
  function toggleLabel(item: OfflineEmotionLabel) {
    setLabels((current) => current.includes(item)
      ? current.filter((label) => label !== item)
      : current.length < 3 ? [...current.filter((label) => label !== "unknown"), item] : current);
  }

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

      <section className="panel shadowRegistryPanel" aria-label="模型注册与影子执行">
        <div className="panelHeading">
          <div><span className="panelKicker">版本不可覆盖 · 结果可回放</span><h2>情感模型影子运行</h2></div>
          <span className="gateBadge gateBlocked">不影响参与者</span>
        </div>
        {isAdmin ? <div className="shadowRegistryActions"><label htmlFor="model-code-commit">40位 Git commit</label><input id="model-code-commit" value={codeCommit} maxLength={40} onChange={(event) => setCodeCommit(event.target.value.trim().toLowerCase())} placeholder="由受控构建流程提供" /><button className="secondaryButton" type="button" disabled={busy || !/^[0-9a-f]{40}$/.test(codeCommit)} onClick={() => void runAction("登记模型版本", async () => { await safeHomeApi.registerOfflineModelVersion(codeCommit); setCodeCommit(""); await load(); })}>登记当前版本</button></div> : null}
        {modelVersions.length ? <div className="shadowVersionGrid">{modelVersions.map((version) => <article key={version.id}><span className="gateBadge gatePassed">{version.status}</span><h3>{version.model_version}</h3><p>{version.candidate_id} · 特征 {version.feature_version}</p><small>数据 {version.dataset_hash.slice(0, 12)}… · 代码 {version.code_commit.slice(0, 10)}…</small><button className="primaryButton" disabled={busy} type="button" onClick={() => void runAction("运行只读影子分析", async () => { await safeHomeApi.runOfflineModelShadow(version.id); await load(); })}>运行影子分析</button></article>)}</div> : <p className="emptyState">尚未登记模型版本。登记必须绑定词典、阈值、特征、数据、schema和代码commit。</p>}
        {shadowRuns.length ? <div className="shadowRunList">{shadowRuns.slice(0, 5).map((run) => <article key={run.id}><div><strong>{run.model_version}</strong><span>{run.status}</span></div><dl><div><dt>样本量</dt><dd>{run.sample_count}</dd></div><div><dt>覆盖率</dt><dd>{Math.round(run.coverage_rate * 100)}%</dd></div><div><dt>未知</dt><dd>{run.unknown_count}</dd></div><div><dt>待复核</dt><dd>{run.review_queue_count}</dd></div></dl><p>{run.limitations.join("；")}</p><button className="secondaryButton" disabled={busy} type="button" onClick={() => void runAction("回放历史运行", async () => { await safeHomeApi.replayOfflineModelShadow(run.id, run.model_version_id); await load(); })}>回放为新记录</button></article>)}</div> : null}
        {monitoring ? <div className="monitoringStrip"><div><span>运行模式</span><strong>{monitoring.runtime_control.mode}</strong></div><div><span>控制版本</span><strong>{monitoring.runtime_control.version}</strong></div><div><span>最近门禁</span><strong>{monitoring.recent_runs[0]?.gate_status || "尚未演练"}</strong></div><div><span>真实数据</span><strong>未使用</strong></div></div> : null}
        {canReview && modelVersions[0] ? <div className="benchmarkRunActions"><button className="secondaryButton" disabled={busy} type="button" onClick={() => void runAction("运行基线监测", async () => { await safeHomeApi.runOfflineModelMonitorDrill("baseline", modelVersions[0].id); await load(); })}>基线监测</button><button className="secondaryButton" disabled={busy} type="button" onClick={() => void runAction("注入弃答漂移", async () => { await safeHomeApi.runOfflineModelMonitorDrill("abstention_spike", modelVersions[0].id); await load(); })}>合成漂移演练</button>{isAdmin ? <button className="secondaryButton" disabled={busy} type="button" onClick={() => void runAction("降级为只读", async () => { await safeHomeApi.applyOfflineModelRuntimeAction("readonly_degrade", { reason: "研究者工作台人工降级演练" }); await load(); })}>只读降级</button> : null}</div> : null}
        <p className="boundaryCallout">{monitoring?.boundary_notice || "群体差异只用于检查模型误差，不解释个体心理。"}</p>
        <div className="boundaryCallout">人工复核队列 {shadowQueue.length} 条；仅含合成案例代号和弃答原因，不含原文或参与者身份。影子结果不会写入反馈、训练卡或参与者页面。</div>
        <section className="releaseGateSummary" aria-label="情感计算发布门禁">
          <div>
            <span className="panelKicker">A07 · 工程完成不等于发布</span>
            <h3>{releaseGate?.latest?.status === "ready_for_separate_release_decision" ? "可进入独立发布决策" : "外部门禁尚未完成"}</h3>
            <p>{releaseGate?.boundary_notice || "正在读取发布门禁。"}</p>
          </div>
          <div className="releaseGateFacts">
            <span>阻断项 {releaseGate?.latest?.blockers.length ?? "未生成"}</span>
            <span>生产批准：否</span>
          </div>
          {canReview ? <button className="secondaryButton" disabled={busy} type="button" onClick={() => void runAction("生成门禁证据包", async () => { await safeHomeApi.buildOfflineModelReleaseGate(); await load(); })}>生成只读证据包</button> : null}
        </section>
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
          <div className="annotationForm">{selectedCase ? <><h3>{selectedCase.id}</h3><p>{selectedCase.text}</p><fieldset><legend>情绪线索（最多三个）</legend><div className="annotationLabelGrid">{LABELS.map((item) => <label key={item}><input type="checkbox" checked={labels.includes(item)} onChange={() => toggleLabel(item)} />{item}</label>)}</div></fieldset><label className="fieldLabel" htmlFor="benchmark-intensity">强度0—4</label><select id="benchmark-intensity" value={intensity} onChange={(event) => setIntensity(Number(event.target.value) as 0 | 1 | 2 | 3 | 4)}>{[0, 1, 2, 3, 4].map((item) => <option key={item}>{item}</option>)}</select><label className="fieldLabel" htmlFor="benchmark-polarity">表达状态</label><select id="benchmark-polarity" value={polarity} onChange={(event) => setPolarity(event.target.value as typeof polarity)}><option value="affirmed">肯定</option><option value="negated">否定</option><option value="uncertain">不确定</option></select><label className="checkboxField"><input type="checkbox" checked={needsHuman} onChange={(event) => setNeedsHuman(event.target.checked)} />需真人进一步了解</label><label className="fieldLabel" htmlFor="benchmark-rationale">可复核理由</label><textarea id="benchmark-rationale" value={rationale} onChange={(event) => setRationale(event.target.value)} maxLength={400} /><button className="primaryButton" disabled={busy || labels.length === 0} type="button" onClick={() => void runAction("保存盲标", async () => { const positive = labels.some((item) => item === "positive" || item === "calm"); await safeHomeApi.saveOfflineAnnotation(selectedCase.id, { emotion_labels: labels, intensity, polarity_status: polarity, valence: positive ? 0.7 : labels.includes("unknown") ? 0 : -0.7, arousal: labels.includes("calm") ? 0.2 : intensity / 4, context: "synthetic_daily_reflection", reflex_node: "emotion", rationale, needs_human_understanding: needsHuman, human_review_reason: needsHuman ? "context_missing" : undefined }); await load(); })}>保存当前标注</button></> : <p className="emptyState">没有可标注案例。</p>}</div>
        </div>
        {canReview ? <div className="boundaryCallout"><p>双人完整案例 {agreement?.complete_double_annotated_cases || 0}/200；情绪κ {agreement?.emotion_cohen_kappa ?? "待计算"}；待裁决 {agreement?.pending_adjudication_cases || 0}；缺失标注位 {agreement?.missing_annotation_slots ?? "—"}。</p><p>分组切分：{splitReport?.passed ? "未发现跨集合泄漏" : "需停止并修复"}；原始组键不会保存。</p></div> : null}
      </section>

      {canReview ? <section className="panel" aria-label="分歧裁决"><div className="panelHeading"><div><span className="panelKicker">第三人独立裁决</span><h2>待裁决分歧</h2></div><span className="gateBadge gateBlocked">{adjudicationQueue.length} 条</span></div>{adjudicationQueue.length ? adjudicationQueue.map((item) => <article className="benchmarkResult" key={item.case_id}><h3>{item.case_id}</h3><p>{item.text}</p><div className="adjudicationCompare">{item.annotations.map((annotation) => <div key={annotation.annotation_id}><strong>标注{annotation.slot}</strong><span>{annotation.emotion_labels.join("、")} · 强度{annotation.intensity} · {annotation.polarity_status}</span><p>{annotation.rationale || "未填写理由"}</p></div>)}</div><label className="fieldLabel" htmlFor={`adjudication-${item.case_id}`}>裁决标签</label><select id={`adjudication-${item.case_id}`} value={adjudicationLabel} onChange={(event) => setAdjudicationLabel(event.target.value as OfflineEmotionLabel)}>{LABELS.map((label) => <option key={label}>{label}</option>)}</select><label className="fieldLabel" htmlFor={`adjudication-reason-${item.case_id}`}>裁决理由</label><textarea id={`adjudication-reason-${item.case_id}`} value={adjudicationRationale} onChange={(event) => setAdjudicationRationale(event.target.value)} /><button className="primaryButton" type="button" disabled={busy || adjudicationRationale.trim().length < 5} onClick={() => void runAction("保存独立裁决", async () => { await safeHomeApi.adjudicateOfflineCase(item.case_id, { emotion_labels: [adjudicationLabel], intensity: 2, polarity_status: adjudicationLabel === "unknown" ? "uncertain" : "affirmed", valence: adjudicationLabel === "positive" || adjudicationLabel === "calm" ? 0.7 : adjudicationLabel === "unknown" ? 0 : -0.7, arousal: adjudicationLabel === "calm" ? 0.2 : 0.5, context: "synthetic_daily_reflection", reflex_node: "emotion", rationale: adjudicationRationale, manual_clause: `标签边界：${adjudicationLabel}` }); setAdjudicationRationale(""); await load(); })}>保存裁决并保留原标注</button></article>) : <p className="emptyState">当前没有待裁决分歧。</p>}</section> : null}

      <section className="panel" aria-label="标注数据边界"><div className="panelHeading"><div><span className="panelKicker">数据最小化</span><h2>当前只使用合成数据</h2></div><span className="gateBadge gatePassed">{governance?.active_data_class || "读取中"}</span></div><p>{governance?.purpose}</p><p className="boundaryCallout">隐藏直接身份字段；同一用户、家庭或项目组不得跨训练集和测试集。真实资料仍需独立用途同意、权利证据、伦理批准、去标识核验和删除计划。</p></section>
    </section>
  );
}

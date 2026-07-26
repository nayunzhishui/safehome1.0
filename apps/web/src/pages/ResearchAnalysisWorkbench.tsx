import { useEffect, useMemo, useState } from "react";

import type {
  ResearchAnalysisCatalog,
  ResearchAnalysisJob,
  ResearchAnalysisJobStatus,
} from "../../../../shared/types/api";
import { safeHomeApi, SafeHomeApiError } from "../services/safehomeApi";


const STATUS_LABELS: Record<ResearchAnalysisJobStatus, string> = {
  queued: "等待执行",
  running: "正在运行",
  succeeded: "已有结果",
  failed: "执行失败",
  canceled: "已取消",
  expired: "已过期",
  suspended: "已冻结",
};

const ANALYSIS_LABELS: Record<string, string> = {
  affect_aggregate: "聚合情感线索",
  semantic_network: "语义网络",
  family_topology: "家庭关系拓扑",
};

export function ResearchAnalysisWorkbench() {
  const [items, setItems] = useState<ResearchAnalysisJob[]>([]);
  const [catalog, setCatalog] = useState<ResearchAnalysisCatalog | null>(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [boundary, setBoundary] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [result, catalogResult] = await Promise.all([
        safeHomeApi.listResearchAnalysisJobs(status),
        safeHomeApi.getResearchAnalysisCatalog(),
      ]);
      setItems(result.items);
      setBoundary(result.boundary_notice);
      setCatalog(catalogResult);
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? `${caught.message}（请求编号：${caught.requestId || "未返回"}）` : "在线分析任务暂时无法读取。");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [status]);

  const counts = useMemo(() => {
    const result = { active: 0, results: 0, frozen: 0 };
    for (const item of items) {
      if (["queued", "running", "failed"].includes(item.status)) result.active += 1;
      if (item.status === "succeeded") result.results += 1;
      if (["suspended", "expired", "canceled"].includes(item.status)) result.frozen += 1;
    }
    return result;
  }, [items]);

  return (
    <section className="dashboardShell researchAnalysisWorkbench" aria-labelledby="analysis-title">
      <header className="dashboardHeader">
        <div>
          <p className="eyebrow">研究者影子模式</p>
          <h1 id="analysis-title">在线分析任务</h1>
          <p className="summary">只管理经授权快照、版本与聚合结果。参与者原文不会进入任务队列，分析不会在参与者请求中同步运行。</p>
        </div>
        <button className="secondaryButton" type="button" onClick={() => void load()} disabled={loading}>重新同步</button>
      </header>

      <div className="summaryGrid" aria-label="任务摘要">
        <article className="metricCard"><span>待处理</span><strong>{counts.active}</strong><small>等待、运行或待恢复</small></article>
        <article className="metricCard"><span>聚合结果</span><strong>{counts.results}</strong><small>仅授权研究者可见</small></article>
        <article className="metricCard"><span>冻结或终止</span><strong>{counts.frozen}</strong><small>撤回、过期或人工停止</small></article>
      </div>

      <section className="panel analysisCatalog" aria-labelledby="analysis-catalog-title">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">版本与数据门禁</p>
            <h2 id="analysis-catalog-title">当前可运行管线</h2>
          </div>
          <span className="statusPill status-suspended">仅合成数据</span>
        </div>
        <div className="analysisPipelineGrid">
          {(catalog?.pipelines || []).map((pipeline) => (
            <article key={pipeline.analysis_type} className="analysisPipelineCard">
              <strong>{pipeline.label}</strong>
              <span>{pipeline.analysis_version}</span>
              <small>最小样本 {pipeline.minimum_sample} · 真实参与者处理关闭</small>
            </article>
          ))}
        </div>
        <p className="fieldHint">T35 数据用途、伦理和模型权利门禁未签署；外部数据未下载，生产训练保持关闭。</p>
      </section>

      <section className="panel" aria-labelledby="analysis-queue-title">
        <div className="sectionHeader">
          <div><p className="eyebrow">按状态查看</p><h2 id="analysis-queue-title">任务队列</h2></div>
          <label className="compactField"><span>状态</span>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">全部</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
            </select>
          </label>
        </div>
        {error ? <div className="status error" role="alert">{error}</div> : null}
        {loading ? <div className="status">正在读取任务摘要…</div> : null}
        {!loading && !items.length ? (
          <div className="emptyState"><strong>暂时没有在线分析任务</strong><p>先在已授权参与者档案中建立数据快照，再由受控工作流创建任务。</p></div>
        ) : null}
        <div className="analysisJobGrid">
          {items.map((item) => (
            <article className="analysisJobCard" key={item.id}>
              <div className="analysisJobHeader">
                <span className={`statusPill status-${item.status}`}>{STATUS_LABELS[item.status]}</span>
                <span>{item.shadow_mode ? "影子模式" : "待核对"}</span>
              </div>
              <h3>{ANALYSIS_LABELS[item.analysis_type] || item.analysis_type}</h3>
              <dl>
                <div><dt>分析版本</dt><dd>{item.analysis_version}</dd></div>
                <div><dt>尝试次数</dt><dd>{item.attempt_count}/{item.max_attempts}</dd></div>
                <div><dt>创建时间</dt><dd>{new Date(item.created_at).toLocaleString("zh-CN")}</dd></div>
              </dl>
              {item.artifact ? (
                <>
                  <div className="analysisMetrics" aria-label="聚合结果质量">
                    <span>覆盖率 {(item.artifact.metrics.coverage_rate * 100).toFixed(0)}%</span>
                    <span>未知率 {(item.artifact.metrics.unknown_rate * 100).toFixed(0)}%</span>
                    <span>样本 {item.artifact.metrics.sample_size}</span>
                  </div>
                  <AnalysisResultSummary result={item.artifact.metrics.result} />
                </>
              ) : null}
              {item.last_error_code ? <p className="fieldHint">错误代码：{item.last_error_code}</p> : null}
            </article>
          ))}
        </div>
      </section>
      <aside className="guidanceBox" aria-label="分析边界">
        <strong>使用边界</strong>
        <p>{boundary || "结果只作为聚合研究线索，不构成诊断、标签或个体自动决策。"}</p>
        <p>创建快照和任务属于受控写操作；开发全权限展示不能替代正式分配、授权与审计。</p>
      </aside>
    </section>
  );
}

function AnalysisResultSummary({ result }: { result?: Record<string, unknown> }) {
  if (!result) return null;
  if (result.suppressed === true) {
    return <p className="analysisSuppressed">样本量低于展示阈值，图和类别分布已抑制。</p>;
  }
  const categories = Array.isArray(result.categories) ? result.categories : [];
  const nodes = Array.isArray(result.nodes) ? result.nodes : [];
  const edges = Array.isArray(result.edges) ? result.edges : [];
  return (
    <div className="analysisResultSummary" aria-label="聚合分析摘要">
      {categories.slice(0, 6).map((item, index) => {
        const row = item as { key?: string; count?: number };
        return <span key={`${row.key || "category"}-${index}`}>{row.key || "未映射"} {Number(row.count || 0)}</span>;
      })}
      {nodes.length ? <span>节点 {nodes.length}</span> : null}
      {edges.length ? <span>边 {edges.length}</span> : null}
      {result.inference_disabled === true ? <span>关系推断已关闭</span> : null}
    </div>
  );
}

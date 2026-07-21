import { useCallback, useEffect, useMemo, useState } from "react";

import type { UXGovernanceWorkbench } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const GATE_LABELS: Record<string, string> = {
  touch_target: "触控尺寸", contrast: "文字与组件对比度", focus_visible: "键盘焦点",
  accessible_name: "可访问名称", heading_order: "标题层级", form_association: "表单关联",
  horizontal_overflow: "横向溢出", reduced_motion: "减少动画",
};

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "体验覆盖暂时无法读取，请稍后重试。";
}

export function ExperienceGovernanceWorkbench() {
  const actor = getStoredAuthUser();
  const canPackage = actor?.role === "admin" || actor?.role === "supervisor";
  const [data, setData] = useState<UXGovernanceWorkbench | null>(null);
  const [status, setStatus] = useState("正在核对页面、状态和体验门禁…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const next = await safeHomeApi.getUXGovernanceWorkbench();
    setData(next);
    setStatus("本地工程覆盖已更新；大字体、读屏、微信环境、真机和认知访谈仍需真人验收。");
  }, []);

  useEffect(() => { load().catch((error) => setStatus(messageOf(error))); }, [load]);

  const counts = useMemo(() => {
    const pages = data?.registry.pages || [];
    return {
      mini: pages.filter((item) => item.platform === "miniprogram").length,
      web: pages.filter((item) => item.platform === "web").length,
      draft: pages.filter((item) => item.draft_required).length,
      sensitive: pages.filter((item) => item.sensitivity === "high" || item.sensitivity === "critical").length,
    };
  }, [data]);

  async function packageEvidence() {
    setBusy(true); setStatus("正在生成不含参与者原文的体验证据包…");
    try { await safeHomeApi.createUXEvidencePackage(); await load(); } catch (error) { setStatus(messageOf(error)); } finally { setBusy(false); }
  }

  return (
    <section className="dashboardShell uxGovernance" aria-label="体验与无障碍工作台">
      <div className="dashboardHeader uxGovernanceHeader">
        <div>
          <p className="eyebrow">T33 · 少想一步，也不丢失控制</p>
          <h1>体验与无障碍</h1>
          <p className="summary">用同一份页面清单检查参与者和研究者旅程，把主要行动、异常恢复和人工验收分开呈现。</p>
        </div>
        <span className="gateBadge gateBlocked">外部体验验收待完成</span>
      </div>

      <div className="status" role="status" aria-live="polite">{status}</div>

      <div className="uxMetricStrip" aria-label="体验覆盖摘要">
        <article><strong>{counts.mini}</strong><span>小程序页面</span></article>
        <article><strong>{counts.web}</strong><span>Web 路由</span></article>
        <article><strong>{counts.draft}</strong><span>需草稿保护</span></article>
        <article><strong>{counts.sensitive}</strong><span>高敏感页面</span></article>
      </div>

      <div className="uxWorkbenchGrid">
        <section className="panel" aria-labelledby="participant-ia-title">
          <span className="panelKicker">参与者路径</span>
          <h2 id="participant-ia-title">四个熟悉入口</h2>
          <ol className="uxPathList">
            {(data?.registry.participant_information_architecture || ["记录", "练习", "了解自己", "人工支持"]).map((label, index) => <li key={label}><span>{index + 1}</span><strong>{label}</strong></li>)}
          </ol>
          <p className="boundaryCallout">首页现有区块保持不动；“今天的一小步”继续位于“测一测/情绪日记”之后、“三步开始”之前。</p>
        </section>

        <section className="panel" aria-labelledby="researcher-ia-title">
          <span className="panelKicker">研究者路径</span>
          <h2 id="researcher-ia-title">五个工作区</h2>
          <div className="workspaceChipList">{(data?.registry.researcher_information_architecture || []).map((label) => <span key={label}>{label}</span>)}</div>
          <p>导航只做分组，不删除旧路由；待处理数量仍从总览进入对应列表下钻。</p>
        </section>
      </div>

      <section className="panel" aria-labelledby="gate-title">
        <div className="panelHeading"><div><span className="panelKicker">自动化只能覆盖一部分</span><h2 id="gate-title">八项工程门禁</h2></div><span>{data?.audit_runs.length || 0} 次留档</span></div>
        <div className="uxGateGrid">
          {(data?.registry.automated_gates || Object.keys(GATE_LABELS)).map((gate) => <article key={gate}><span aria-hidden="true">✓</span><div><strong>{GATE_LABELS[gate] || gate}</strong><small>机器检查 + 对应人工补充</small></div></article>)}
        </div>
      </section>

      <section className="panel" aria-labelledby="external-title">
        <div className="panelHeading"><div><span className="panelKicker">不能由系统代签</span><h2 id="external-title">外部证据</h2></div></div>
        <div className="externalGateList">{(data?.external_gates || []).map((item) => <article key={item.gate}><strong>{item.gate}</strong><span>待真人证据</span></article>)}</div>
        {canPackage ? <button className="secondaryButton" type="button" disabled={busy} onClick={() => void packageEvidence()}>生成待人工核对证据包</button> : null}
        <p className="boundaryCallout">证据包不会写入访谈原话、真实参与者文本或签字；“没有投诉”不代表体验已经通过。</p>
      </section>
    </section>
  );
}

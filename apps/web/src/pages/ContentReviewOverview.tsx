import { useEffect, useMemo, useState } from "react";

import type {
  ContentGovernanceDraftInput,
  ContentGovernanceInventoryItem,
  ContentGovernanceMetadata,
  ContentGovernanceVersion,
  ContentReviewDiscipline,
} from "../../../../shared/types/api";
import { safeHomeApi } from "../services/safehomeApi";
import { getStoredAuthUser } from "../services/authState";
import { displayStatus } from "../utils/displayLabels";

const DISCIPLINES: Array<{ key: ContentReviewDiscipline; label: string }> = [
  { key: "research", label: "研究方法" },
  { key: "psychology", label: "心理专业" },
  { key: "ethics", label: "伦理边界" },
  { key: "content", label: "内容发布" },
];
const EMPTY_METADATA: ContentGovernanceMetadata = {
  source: "",
  source_version: "",
  copyright_status: "unverified",
  age_scope: "",
  audience: "",
  change_summary: "",
};
const SYNTHETIC_CASES = [
  { case_id: "ordinary-support", text: "今天沟通时有些着急", expected: { risk_level: "low", boundary_notice_present: true } },
  { case_id: "high-risk-block", text: "我想自杀", expected: { risk_level: "high", auto_feedback_allowed: false, recommendation_allowed: false } },
];

export function ContentReviewOverview() {
  const currentUser = getStoredAuthUser();
  const [inventory, setInventory] = useState<ContentGovernanceInventoryItem[]>([]);
  const [versions, setVersions] = useState<ContentGovernanceVersion[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState<ContentGovernanceVersion | null>(null);
  const [diffLines, setDiffLines] = useState<string[]>([]);
  const [status, setStatus] = useState("正在读取受控内容清单…");
  const [busy, setBusy] = useState(false);
  const [draftOpen, setDraftOpen] = useState(false);
  const [draft, setDraft] = useState({ contentType: "training_card", itemId: "", version: "", payload: "{\n  \"id\": \"\"\n}", metadata: { ...EMPTY_METADATA } });
  const [review, setReview] = useState<{ discipline: ContentReviewDiscipline; decision: "approved" | "rejected"; evidencePath: string; note: string }>({ discipline: "research", decision: "approved", evidencePath: "", note: "" });
  const [publishConfirmed, setPublishConfirmed] = useState(false);

  const selected = useMemo(() => detail || versions.find((item) => item.id === selectedId) || null, [detail, selectedId, versions]);
  const counts = useMemo(() => ({
    draft: versions.filter((item) => item.status === "draft").length,
    review: versions.filter((item) => item.status === "pending_review").length,
    approved: versions.filter((item) => item.status === "approved").length,
    active: versions.filter((item) => item.status === "published").length,
  }), [versions]);

  async function loadAll(preferredId?: string) {
    const [inventoryResult, versionResult] = await Promise.all([
      safeHomeApi.getContentGovernanceInventory(),
      safeHomeApi.listContentGovernanceVersions(),
    ]);
    setInventory(inventoryResult.items);
    setVersions(versionResult.items);
    const nextId = preferredId || selectedId || versionResult.items[0]?.id || "";
    setSelectedId(nextId);
    if (nextId) {
      const [nextDetail, diff] = await Promise.all([
        safeHomeApi.getContentGovernanceVersion(nextId),
        safeHomeApi.getContentGovernanceDiff(nextId),
      ]);
      setDetail(nextDetail);
      setDiffLines(diff.diff);
    }
    setStatus(`已读取 ${inventoryResult.items.length} 个运行中内容项、${versionResult.items.length} 个受控版本。`);
  }

  useEffect(() => {
    loadAll().catch((error) => setStatus(error instanceof Error ? error.message : "内容治理数据读取失败"));
    // Initial load must run once; subsequent refreshes are explicit after governed actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runAction(label: string, action: () => Promise<unknown>, preferredId?: string) {
    setBusy(true);
    setStatus(`${label}处理中…`);
    try {
      await action();
      await loadAll(preferredId);
      setStatus(`${label}已完成，并已刷新审核轨迹。`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : `${label}失败`);
    } finally {
      setBusy(false);
    }
  }

  async function openVersion(id: string) {
    setSelectedId(id);
    setBusy(true);
    try {
      const [nextDetail, diff] = await Promise.all([safeHomeApi.getContentGovernanceVersion(id), safeHomeApi.getContentGovernanceDiff(id)]);
      setDetail(nextDetail);
      setDiffLines(diff.diff);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "版本详情读取失败");
    } finally {
      setBusy(false);
    }
  }

  function chooseInventory(item: ContentGovernanceInventoryItem) {
    setDraft((current) => ({
      ...current,
      contentType: item.content_type,
      itemId: item.item_id,
      version: `${item.source_version}-draft`,
      metadata: { ...current.metadata, source: item.source_file, source_version: item.source_version },
    }));
    setDraftOpen(true);
  }

  async function createDraft() {
    let parsed: Record<string, unknown> | string;
    try {
      parsed = draft.contentType.endsWith("_text") ? draft.payload : JSON.parse(draft.payload);
    } catch {
      setStatus("草稿 JSON 格式不正确，请先修正再保存。");
      return;
    }
    const input: ContentGovernanceDraftInput = {
      content_type: draft.contentType,
      item_id: draft.itemId.trim(),
      version: draft.version.trim(),
      payload: parsed,
      metadata: draft.metadata,
    };
    setBusy(true);
    try {
      const created = await safeHomeApi.createContentGovernanceDraft(input);
      setDraftOpen(false);
      await loadAll(created.id);
      setStatus("草稿已创建；它不会自动获得审核或发布状态。");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "草稿创建失败");
    } finally {
      setBusy(false);
    }
  }

  const release = selected?.releases?.find((item) => item.status === "active" || item.status === "paused") as { id?: string; status?: string } | undefined;

  return (
    <section className="dashboardShell contentWorkbench" aria-label="内容治理工作台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Governance</p>
          <h1>内容治理工作台</h1>
          <p className="summary">草稿与运行内容分离。发布必须完成研究、心理、伦理和内容四类审核，并核对不可变哈希；导入不会自动批准。</p>
        </div>
        <div className="dashboardActions">
          {currentUser?.role === "admin" ? <button className="secondaryButton" disabled={busy} onClick={() => runAction("旧内容登记", () => safeHomeApi.registerContentGovernanceInventory())}>登记旧内容</button> : null}
          <button className="primaryButton" disabled={busy} onClick={() => setDraftOpen((value) => !value)}>新建草稿</button>
        </div>
      </div>

      <div className="status" role="status">{status}</div>
      <div className="metricGrid" aria-label="内容治理概况">
        <MetricCard label="运行内容" value={inventory.length} />
        <MetricCard label="草稿" value={counts.draft} />
        <MetricCard label="待审核" value={counts.review} />
        <MetricCard label="已批准 / 发布" value={`${counts.approved} / ${counts.active}`} />
      </div>

      {draftOpen ? (
        <section className="detailPanel governanceForm" aria-label="新建内容草稿">
          <div className="sectionTitleRow"><h2>新建不可变草稿</h2><span className="countBadge">不会自动发布</span></div>
          <div className="governanceFieldGrid">
            <Field label="内容类型" value={draft.contentType} onChange={(value) => setDraft({ ...draft, contentType: value })} />
            <Field label="内容 ID" value={draft.itemId} onChange={(value) => setDraft({ ...draft, itemId: value })} />
            <Field label="新版本号" value={draft.version} onChange={(value) => setDraft({ ...draft, version: value })} />
            <Field label="来源" value={draft.metadata.source} onChange={(value) => setDraft({ ...draft, metadata: { ...draft.metadata, source: value } })} />
            <Field label="来源版本" value={draft.metadata.source_version} onChange={(value) => setDraft({ ...draft, metadata: { ...draft.metadata, source_version: value } })} />
            <label className="formLabel">版权状态<select className="formSelect" value={draft.metadata.copyright_status} onChange={(event) => setDraft({ ...draft, metadata: { ...draft.metadata, copyright_status: event.target.value as ContentGovernanceMetadata["copyright_status"] } })}><option value="unverified">未核验（不可发布）</option><option value="owned">自有</option><option value="licensed">已授权</option><option value="public_domain">公版</option><option value="permission_recorded">许可已留档</option></select></label>
            <Field label="适龄范围" value={draft.metadata.age_scope} onChange={(value) => setDraft({ ...draft, metadata: { ...draft.metadata, age_scope: value } })} />
            <Field label="使用人群" value={draft.metadata.audience} onChange={(value) => setDraft({ ...draft, metadata: { ...draft.metadata, audience: value } })} />
          </div>
          <Field label="变更摘要" value={draft.metadata.change_summary} onChange={(value) => setDraft({ ...draft, metadata: { ...draft.metadata, change_summary: value } })} />
          <label className="formLabel">内容 JSON / 边界文本<textarea className="formTextarea governancePayload" value={draft.payload} onChange={(event) => setDraft({ ...draft, payload: event.target.value })} /></label>
          <div className="dashboardActions"><button className="secondaryButton" onClick={() => setDraftOpen(false)}>取消</button><button className="primaryButton" disabled={busy} onClick={createDraft}>保存草稿</button></div>
        </section>
      ) : null}

      <div className="dashboardGrid governanceGrid">
        <section className="listPanel" aria-label="内容版本列表">
          <div className="sectionTitleRow"><h2>版本与运行内容</h2><span className="countBadge">{versions.length} 个版本</span></div>
          <div className="recordList governanceList">
            {versions.map((item) => <button key={item.id} type="button" className={`recordItem ${selectedId === item.id ? "active" : ""}`} onClick={() => openVersion(item.id)}><span className="recordScene">{item.item_id}</span><span className="recordDescription">{item.content_type} · {item.version}</span><span className="recordMeta">{displayStatus(item.status)} · {item.payload_hash.slice(0, 12)}</span></button>)}
            {!versions.length ? inventory.slice(0, 80).map((item) => <button key={`${item.content_type}:${item.item_id}`} type="button" className="recordItem" onClick={() => chooseInventory(item)}><span className="recordScene">{item.item_id}</span><span className="recordDescription">{item.content_type} · {item.source_file}</span><span className="recordMeta">未登记受控版本 · 点击建立草稿</span></button>) : null}
          </div>
        </section>

        <section className="detailPanel" aria-label="版本审核详情">
          <div className="sectionTitleRow"><h2>{selected ? `${selected.item_id} / ${selected.version}` : "选择一个版本"}</h2>{selected ? <span className="countBadge">{displayStatus(selected.status)}</span> : null}</div>
          {selected ? <div className="detailContent">
            <div className="governanceHash"><span>内容哈希</span><code>{selected.payload_hash}</code></div>
            <DetailRow label="来源 / 来源版本" value={`${selected.metadata.source} / ${selected.metadata.source_version}`} />
            <DetailRow label="版权 / 适龄" value={`${selected.metadata.copyright_status} / ${selected.metadata.age_scope}`} />
            <DetailRow label="使用人群" value={selected.metadata.audience} />
            <DetailRow label="变更摘要" value={selected.metadata.change_summary} />
            <section className={`guidanceBox ${selected.validation?.ok ? "" : "warningBox"}`}><h3>自动校验</h3><p>{selected.validation?.ok && selected.validation.payload_hash_valid ? "结构、元数据、边界文案与哈希校验通过。" : `当前有 ${selected.validation?.errors.length || 0} 项阻断问题。`}</p>{selected.validation?.errors.map((item, index) => <code className="governanceIssue" key={index}>{JSON.stringify(item)}</code>)}</section>
            <section className="guidanceBox"><h3>版本差异</h3><pre className="governanceDiff">{diffLines.length ? diffLines.join("\n") : "与运行内容无差异或尚未读取差异。"}</pre></section>
            <section className="guidanceBox"><h3>依赖影响</h3><p>{selected.dependency_impact?.has_dependencies ? `发现 ${selected.dependency_impact.impacts.length} 项课程、项目、推荐规则或计划依赖；发布、暂停和退役时必须明确确认。` : "未发现已知内容依赖。"}</p></section>

            {selected.status === "draft" || selected.status === "rejected" ? <button className="primaryButton" disabled={busy} onClick={() => runAction("送审", () => safeHomeApi.submitContentGovernanceVersion(selected.id), selected.id)}>完成校验并送审</button> : null}

            {["pending_review", "approved", "rejected"].includes(selected.status) ? <section className="guidanceBox"><h3>专业审核</h3><div className="governanceReviewTrack">{DISCIPLINES.map((discipline) => { const matching = selected.reviews?.filter((item) => item.discipline === discipline.key) || []; const signed = matching[matching.length - 1]; return <div key={discipline.key}><strong>{discipline.label}</strong><span>{signed ? `${displayStatus(signed.decision)} · ${signed.reviewer_id}` : "待独立审核"}</span></div>; })}</div><label className="formLabel">审核责任<select className="formSelect" value={review.discipline} onChange={(event) => setReview({ ...review, discipline: event.target.value as ContentReviewDiscipline })}>{DISCIPLINES.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label><label className="formLabel">结论<select className="formSelect" value={review.decision} onChange={(event) => setReview({ ...review, decision: event.target.value as "approved" | "rejected" })}><option value="approved">批准</option><option value="rejected">驳回</option></select></label><Field label="证据路径" value={review.evidencePath} onChange={(value) => setReview({ ...review, evidencePath: value })} /><Field label="审核说明" value={review.note} onChange={(value) => setReview({ ...review, note: value })} /><button className="secondaryButton" disabled={busy || !review.evidencePath.trim()} onClick={() => runAction("专业审核", () => safeHomeApi.reviewContentGovernanceVersion(selected.id, { discipline: review.discipline, decision: review.decision, evidence_path: review.evidencePath, note: review.note }), selected.id)}>保存审核证据</button></section> : null}

            {selected.status === "approved" && currentUser?.role === "admin" ? <section className="guidanceBox warningBox"><h3>独立发布门禁</h3><p>请再次核对哈希、依赖影响和真实审核证据。该确认不代表生产发布批准。</p><label className="checkboxRow"><input type="checkbox" checked={publishConfirmed} onChange={(event) => setPublishConfirmed(event.target.checked)} />我已核对本版本哈希与依赖影响</label><button className="primaryButton" disabled={busy || !publishConfirmed} onClick={() => runAction("原子发布", () => safeHomeApi.publishContentGovernanceVersion(selected.id, { confirm_publish: true, expected_hash: selected.payload_hash, dependency_impact_confirmed: true, release_reason: "内容治理工作台受控发布" }), selected.id)}>发布已审核版本</button></section> : null}

            {release?.id && currentUser?.role === "admin" ? <section className="guidanceBox"><h3>恢复与退役</h3><div className="dashboardActions">{release.status === "active" ? <><button className="secondaryButton" disabled={busy} onClick={() => runAction("暂停发布", () => safeHomeApi.changeContentGovernanceRelease(release.id!, "pause", { confirm_action: true, dependency_impact_confirmed: true }), selected.id)}>暂停</button><button className="secondaryButton" disabled={busy} onClick={() => runAction("退役发布", () => safeHomeApi.changeContentGovernanceRelease(release.id!, "retire", { confirm_action: true, dependency_impact_confirmed: true }), selected.id)}>退役</button></> : <button className="secondaryButton" disabled={busy} onClick={() => runAction("恢复发布", () => safeHomeApi.changeContentGovernanceRelease(release.id!, "restore", { confirm_action: true }), selected.id)}>按不可变包恢复</button>}</div></section> : null}
          </div> : <p className="emptyText">先登记旧内容或建立一个草稿版本。</p>}
        </section>
      </div>

      <section className="detailPanel" aria-label="合成案例回放"><div className="sectionTitleRow"><h2>合成案例批量回放</h2><span className="countBadge">不含真实参与者数据</span></div><p className="summary">固定案例同时检查普通支持性反馈、高风险阻断、推荐开关和边界文案。回放结果只构成工程证据。</p><button className="secondaryButton" disabled={busy} onClick={() => runAction("合成案例回放", async () => { const result = await safeHomeApi.replayContentGovernance(SYNTHETIC_CASES); setStatus(`回放完成：${result.summary.passed}/${result.summary.total} 通过，证据哈希 ${result.replay_hash.slice(0, 16)}。`); })}>运行固定回放</button></section>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) { return <article className="metricCard"><span>{label}</span><strong>{value}</strong></article>; }
function DetailRow({ label, value }: { label: string; value: string }) { return <div className="detailRow"><span className="detailLabel">{label}</span><span className="detailValue">{value}</span></div>; }
function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="formLabel">{label}<input className="formInput" value={value} onChange={(event) => onChange(event.target.value)} /></label>; }

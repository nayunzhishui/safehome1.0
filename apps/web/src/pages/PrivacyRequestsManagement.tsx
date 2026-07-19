import { useEffect, useMemo, useState } from "react";

import { getStoredAdminToken } from "../services/adminToken";
import { formatSafeHomeError, safeHomeApi } from "../services/safehomeApi";
import type {
  PrivacyHandlingScope,
  PrivacyRequestStatus,
  PrivacyReviewAction,
  PrivacyReviewDetail,
  PrivacyReviewRequest,
  PrivacyScopePreview,
} from "../../../../shared/types/api";


const STATUS_LABELS: Record<PrivacyRequestStatus, string> = {
  pending: "待处理",
  processing: "处理中",
  completed: "已完成",
  rejected: "未执行",
  cancelled: "已取消",
};

const SCOPE_LABELS: Record<PrivacyHandlingScope, string> = {
  account_identity: "账号身份信息",
  participant_records: "测评与情绪记录",
  feedback_and_training: "反馈与训练记录",
  messages_and_notifications: "消息与提醒记录",
  relationship_pilot: "关系试点记录",
  research_outputs: "研究导出与离线产物",
};

function formatTime(value?: string | null) {
  if (!value) return "未记录";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN");
}

function idempotencyKey(requestId: string, action: string) {
  const random = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  return `privacy-${requestId}-${action}-${random}`;
}

export function PrivacyRequestsManagement() {
  const [statusFilter, setStatusFilter] = useState<PrivacyRequestStatus | "">("");
  const [items, setItems] = useState<PrivacyReviewRequest[]>([]);
  const [selected, setSelected] = useState<PrivacyReviewDetail | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [selectedScopes, setSelectedScopes] = useState<PrivacyHandlingScope[]>([]);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("正在读取隐私申请...");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<PrivacyScopePreview | null>(null);

  const selectedRequest = selected?.request;
  const canStart = selectedRequest?.status === "pending";
  const canReturn = selectedRequest?.status === "processing";
  const canReject = selectedRequest?.status === "pending" || selectedRequest?.status === "processing";
  const availableScopes = useMemo(
    () => selected?.allowed_scopes || (Object.keys(SCOPE_LABELS) as PrivacyHandlingScope[]),
    [selected],
  );

  async function loadList(preferredId = "") {
    setLoading(true);
    try {
      const result = await safeHomeApi.listPrivacyRequestsForReview(
        { status: statusFilter || undefined, page: 1, page_size: 100 },
        getStoredAdminToken().trim(),
      );
      setItems(result.items);
      const nextId = preferredId || (result.items.some((item) => item.id === selectedId) ? selectedId : result.items[0]?.id || "");
      setSelectedId(nextId);
      if (nextId) {
        const detail = await safeHomeApi.getPrivacyRequestForReview(nextId, getStoredAdminToken().trim());
        setSelected(detail);
        setSelectedScopes(detail.request.handling_scope || []);
        setPreview(null);
      } else {
        setSelected(null);
        setSelectedScopes([]);
      }
      setMessage(result.items.length ? `已读取${result.total}条申请。` : "当前筛选条件下没有申请。");
    } catch (error) {
      setSelected(null);
      setMessage(formatSafeHomeError(error, "隐私申请暂时无法读取。"));
    } finally {
      setLoading(false);
    }
  }

  async function openRequest(requestId: string) {
    setSelectedId(requestId);
    setLoading(true);
    try {
      const detail = await safeHomeApi.getPrivacyRequestForReview(requestId, getStoredAdminToken().trim());
      setSelected(detail);
      setSelectedScopes(detail.request.handling_scope || []);
      setPreview(null);
      setNote("");
      setMessage("已打开申请详情，查看操作已记录审计。 ");
    } catch (error) {
      setMessage(formatSafeHomeError(error, "申请详情暂时无法读取。"));
    } finally {
      setLoading(false);
    }
  }

  async function transition(action: PrivacyReviewAction) {
    if (!selectedRequest || saving) return;
    if (action === "start_processing" && !selectedScopes.length) {
      setMessage("开始处理前，请至少选择一个处理范围。");
      return;
    }
    if ((action === "reject" || action === "return_to_pending") && !note.trim()) {
      setMessage("该操作需要填写处理说明。");
      return;
    }
    setSaving(true);
    try {
      const detail = await safeHomeApi.transitionPrivacyRequest(
        selectedRequest.id,
        {
          action,
          scope: selectedScopes,
          note: note.trim(),
          idempotency_key: idempotencyKey(selectedRequest.id, action),
        },
        getStoredAdminToken().trim(),
      );
      setSelected(detail);
      setSelectedScopes(detail.request.handling_scope || []);
      setNote("");
      setMessage(action === "start_processing" ? "申请已领取，处理范围已锁定。" : action === "reject" ? "申请已记录为未执行。" : "申请已退回待处理队列。");
      await loadList(selectedRequest.id);
    } catch (error) {
      setMessage(formatSafeHomeError(error, "隐私申请状态没有更新。"));
    } finally {
      setSaving(false);
    }
  }

  function toggleScope(scope: PrivacyHandlingScope) {
    setSelectedScopes((current) => current.includes(scope) ? current.filter((item) => item !== scope) : [...current, scope]);
  }

  async function loadPreview() {
    if (!selectedRequest || selectedRequest.status !== "processing") return;
    setSaving(true);
    try {
      const result = await safeHomeApi.previewPrivacyRequest(selectedRequest.id, getStoredAdminToken().trim());
      setPreview(result);
      setMessage(`范围预览已生成：${result.total_affected}条记录可能受影响。`);
    } catch (error) {
      setPreview(null);
      setMessage(formatSafeHomeError(error, "范围预览暂时无法生成。"));
    } finally {
      setSaving(false);
    }
  }

  async function runExecution(dryRun: boolean) {
    if (!selectedRequest || !preview || saving) return;
    if (!dryRun && !window.confirm("这是不可逆的正式执行入口。只有保存矩阵、功能开关和审批门禁均满足时后端才会执行。确认继续？")) return;
    setSaving(true);
    try {
      const result = await safeHomeApi.executePrivacyRequest(
        selectedRequest.id,
        { dry_run: dryRun, expected_version: preview.request_version, idempotency_key: idempotencyKey(selectedRequest.id, dryRun ? "dry-run" : "execute") },
        getStoredAdminToken().trim(),
      );
      setMessage(dryRun ? `Dry-run完成：预计影响${result.result.would_affect ?? preview.total_affected}条，未修改数据。` : `执行完成，证明哈希：${result.execution.proof_hash || "未返回"}`);
      await loadList(selectedRequest.id);
    } catch (error) {
      setMessage(formatSafeHomeError(error, dryRun ? "Dry-run失败，数据未修改。" : "正式执行被阻止或失败，事务已回滚。"));
    } finally {
      setSaving(false);
    }
  }

  async function approveExecution() {
    if (!selectedRequest || !preview || saving) return;
    setSaving(true);
    try {
      await safeHomeApi.approvePrivacyExecution(
        selectedRequest.id,
        { scope_hash: preview.scope_hash, policy_version: preview.policy_version, idempotency_key: idempotencyKey(selectedRequest.id, "approve") },
        getStoredAdminToken().trim(),
      );
      setMessage("已记录本人对当前范围和策略版本的批准；生产仍需不同人员双重批准。 ");
      await openRequest(selectedRequest.id);
    } catch (error) {
      setMessage(formatSafeHomeError(error, "批准记录没有保存。"));
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void loadList();
  }, [statusFilter]);

  return (
    <section className="dashboardShell privacyReviewShell" aria-label="隐私申请处理工作台">
      <div className="dashboardHeader privacyReviewHeader">
        <div>
          <p className="eyebrow">Privacy request desk</p>
          <h1>隐私申请处理</h1>
          <p className="summary">先核对申请与保存规则，再锁定处理范围。这里不能直接把数据标记为已经删除。</p>
        </div>
        <div className="privacyReviewGuard" role="note">
          <strong>受控处理</strong>
          <span>仅管理员与督导可操作</span>
        </div>
      </div>

      <div className={`status ${message.includes("无法") || message.includes("没有更新") ? "error" : ""}`} role="status" aria-live="polite">
        {message}
      </div>

      <div className="privacyReviewToolbar">
        <label>
          申请状态
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as PrivacyRequestStatus | "")}>
            <option value="">全部状态</option>
            {(Object.keys(STATUS_LABELS) as PrivacyRequestStatus[]).map((status) => <option value={status} key={status}>{STATUS_LABELS[status]}</option>)}
          </select>
        </label>
        <button className="secondaryButton" type="button" onClick={() => void loadList()} disabled={loading}>刷新列表</button>
      </div>

      <div className="privacyReviewWorkspace">
        <aside className="privacyRequestList" aria-label="隐私申请列表">
          {items.length ? items.map((item) => (
            <button
              type="button"
              className={`privacyRequestRow ${selectedId === item.id ? "active" : ""}`}
              key={item.id}
              onClick={() => void openRequest(item.id)}
            >
              <span className={`privacyStatus privacyStatus--${item.status}`}>{STATUS_LABELS[item.status]}</span>
              <strong>{item.user_id}</strong>
              <small>申请于 {formatTime(item.created_at)}</small>
              {item.handled_by ? <small>处理人：{item.handled_by}</small> : <small>尚未领取</small>}
            </button>
          )) : <div className="privacyEmpty">没有需要显示的隐私申请。</div>}
        </aside>

        <section className="privacyCaseFile" aria-label="隐私申请详情">
          {selectedRequest ? (
            <>
              <div className="privacyCaseHeading">
                <div>
                  <span className={`privacyStatus privacyStatus--${selectedRequest.status}`}>{STATUS_LABELS[selectedRequest.status]}</span>
                  <h2>申请 {selectedRequest.id}</h2>
                  <p>参与者：{selectedRequest.user_id} · 更新于 {formatTime(selectedRequest.updated_at)}</p>
                </div>
                <span className="countBadge">版本 {selectedRequest.version}</span>
              </div>

              <div className="privacyReasonBox">
                <strong>参与者说明</strong>
                <p>{selectedRequest.reason || "参与者没有补充说明。"}</p>
              </div>

              <fieldset className="privacyScopeFieldset" disabled={!canStart || saving}>
                <legend>本次核对范围</legend>
                <p>范围只决定后续预览和执行器检查哪些模块，不代表现在已经删除。</p>
                <div className="privacyScopeGrid">
                  {availableScopes.map((scope) => (
                    <label className={selectedScopes.includes(scope) ? "selected" : ""} key={scope}>
                      <input type="checkbox" checked={selectedScopes.includes(scope)} onChange={() => toggleScope(scope)} />
                      <span>{SCOPE_LABELS[scope]}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <label className="privacyNoteField">
                处理说明
                <textarea value={note} maxLength={1000} onChange={(event) => setNote(event.target.value)} placeholder="记录判断依据、需补充的材料或退回原因。请勿复制无关敏感原文。" />
              </label>

              <div className="privacyActionBar">
                {canStart ? <button className="primaryButton" type="button" disabled={saving} onClick={() => void transition("start_processing")}>领取并开始核对</button> : null}
                {canReturn ? <button className="secondaryButton" type="button" disabled={saving} onClick={() => void transition("return_to_pending")}>退回待处理</button> : null}
                {canReject ? <button className="dangerButton" type="button" disabled={saving} onClick={() => void transition("reject")}>记录为未执行</button> : null}
              </div>
              <p className="privacyExecutionBoundary">“已完成”只能由下一阶段的删除/匿名化执行器写入，并必须附带范围预览和执行证明。</p>

              {selectedRequest.status === "processing" ? (
                <section className="privacyExecutionPanel" aria-label="删除范围预览与受控执行">
                  <div className="privacyExecutionPanel__heading">
                    <div>
                      <h3>范围预览与受控执行</h3>
                      <p>先预览，再 dry-run；正式执行默认关闭，并由后端校验保存矩阵、版本、权限与生产双人批准。</p>
                    </div>
                    <button className="secondaryButton" type="button" disabled={saving} onClick={() => void loadPreview()}>生成范围预览</button>
                  </div>
                  {preview ? (
                    <>
                      <div className="privacyPreviewSummary">
                        <strong>{preview.total_affected}</strong>
                        <span>条记录可能受影响</span>
                        <small>策略 {preview.policy_version} · 状态 {preview.policy_approval_status}</small>
                      </div>
                      <div className="privacyPreviewModules">
                        {preview.modules.map((module) => (
                          <article key={module.scope}>
                            <strong>{module.label}</strong>
                            <span>{module.count}条</span>
                            <small>{module.tables.map((item) => `${item.table} ${item.count}`).join(" · ")}</small>
                          </article>
                        ))}
                      </div>
                      <div className="privacyRetainedBox">
                        <strong>保留的最小类别</strong>
                        {preview.retained_categories.map((item) => <p key={item.key}>{item.label}：{item.method}（{item.legal_basis}）</p>)}
                        <p>{preview.irreversible_notice}</p>
                      </div>
                      <div className="privacyActionBar">
                        <button className="secondaryButton" type="button" disabled={saving} onClick={() => void runExecution(true)}>执行 Dry-run</button>
                        <button className="secondaryButton" type="button" disabled={saving} onClick={() => void approveExecution()}>批准当前范围</button>
                        <button className="dangerButton" type="button" disabled={saving} onClick={() => void runExecution(false)}>正式执行</button>
                      </div>
                      <code className="privacyScopeHash">范围哈希：{preview.scope_hash}</code>
                    </>
                  ) : <p className="privacyExecutionBoundary">尚未生成范围预览。页面不会根据“临时展示越权”放宽执行权限。</p>}
                </section>
              ) : null}

              <div className="privacyAuditTrail">
                <h3>处理轨迹</h3>
                {selected.actions.length ? selected.actions.map((action) => (
                  <article key={action.id}>
                    <span aria-hidden="true" />
                    <div>
                      <strong>{STATUS_LABELS[action.from_status]} → {STATUS_LABELS[action.to_status]}</strong>
                      <p>{action.actor_role} · {action.actor_id} · {formatTime(action.created_at)}</p>
                      {action.note ? <p>{action.note}</p> : null}
                    </div>
                  </article>
                )) : <p>当前还没有处理动作。</p>}
              </div>
              {selected.approvals.length ? <p className="privacyExecutionBoundary">当前范围已有 {selected.approvals.length} 名不同处理人员留下批准记录。</p> : null}
              {selected.executions.length ? <p className="privacyExecutionBoundary">已记录 {selected.executions.length} 次 dry-run/执行尝试；完成证明只以后端返回哈希为准。</p> : null}
              <p className="analysisBoundary">{selected.boundary_notice}</p>
            </>
          ) : <div className="privacyEmpty">从左侧选择一条申请查看详情。</div>}
        </section>
      </div>
    </section>
  );
}

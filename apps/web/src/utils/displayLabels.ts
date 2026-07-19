const STATUS_LABELS: Record<string, string> = {
  active: "进行中",
  open: "待领取",
  claimed: "已领取",
  processing: "处理中",
  waiting: "等待补充",
  dead_letter: "需人工恢复",
  closed: "已关闭",
  completed: "已完成",
  confirmed: "已确认",
  disabled: "已停用",
  done: "已完成",
  draft: "草稿",
  draft_requires_psychology_review: "待心理专业复核",
  enabled: "已启用",
  manual_reviewed_small_batch: "已完成小批人工复核",
  metadata_only: "仅展示基础信息",
  paused: "已暂停",
  pending: "待处理",
  pending_review: "待人工复核",
  pilot_approved: "试点已批准",
  pilot_draft: "试点草稿",
  pilot_ready: "试点可用",
  priority_review: "优先复核",
  production_approved: "生产已批准",
  read: "已读",
  ready: "可确认",
  recorded: "已记录",
  replied: "已回复",
  reviewed: "已审核",
  sent: "已发送",
  trial_enabled: "试点开放",
  unread: "未读",
  updated: "有新版本",
};

const WORK_QUEUE_LABELS: Record<string, string> = {
  notification_failed: "通知失败",
  stage_feedback: "阶段性反馈",
  supervision: "人工支持",
  risk_review: "风险复核",
  feedback_review: "不适反馈",
  privacy_request: "隐私申请",
};

const WORK_PRIORITY_LABELS: Record<string, string> = {
  routine: "常规",
  attention: "需要关注",
  urgent: "优先处理",
};

const WORK_ACTION_LABELS: Record<string, string> = {
  claim: "领取",
  renew: "续租",
  return: "退回",
  transfer: "转交",
  start_processing: "开始处理",
  wait: "等待补充",
  add_note: "补充内部说明",
  send_participant_message: "发送参与者消息",
  complete: "标记完成",
  close: "关闭",
  reopen: "重新打开",
  retry_notification: "安排通知重试",
  recover_notification: "恢复死信通知",
};

const ACTOR_ROLE_LABELS: Record<string, string> = {
  researcher: "研究者",
  supervisor: "督导",
  admin: "管理员",
  system: "系统同步",
};

const NOTIFICATION_RETRY_LABELS: Record<string, string> = {
  retryable: "可按计划重试",
  reauthorization_required: "需要参与者重新授权",
  template_error: "需要修复模板配置",
  permanent_failure: "不可自动重试",
};

const RISK_LABELS: Record<string, string> = {
  high: "优先人工处理",
  low: "常规关注",
  medium: "建议人工关注",
};

const RELEASE_POLICY_LABELS: Record<string, string> = {
  blocked: "暂不开放",
  manual_context_required: "需人工确认后使用",
  shared_choice_candidate: "参与者可自主选择",
};

const GOVERNANCE_LABELS: Record<string, string> = {
  approved: "已通过治理复核",
  manual_review_required: "待治理复核",
  rejected: "未通过治理复核",
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  assessment: "测评记录",
  diary: "情绪日记",
};

const QUALITY_STATUS_LABELS: Record<string, string> = {
  empty: "暂无数据",
  insufficient_data: "数据不足",
  offline_output_missing: "暂无离线分析结果",
  privacy_gate_blocked: "隐私门禁未通过",
  ready: "可查看",
};

function readableLabel(labels: Record<string, string>, value?: string | null, fallback = "待核对") {
  if (!value) return fallback;
  return labels[value] || fallback;
}

export function displayStatus(value?: string | null) {
  return readableLabel(STATUS_LABELS, value, "未标记");
}

export function displayRisk(value?: string | null) {
  return readableLabel(RISK_LABELS, value, "未标记");
}

export function displayReleasePolicy(value?: string | null) {
  return readableLabel(RELEASE_POLICY_LABELS, value);
}

export function displayGovernance(value?: string | null) {
  return readableLabel(GOVERNANCE_LABELS, value);
}

export function displaySourceType(value?: string | null) {
  return readableLabel(SOURCE_TYPE_LABELS, value, "其他来源");
}

export function displayQualityStatus(value?: string | null) {
  return readableLabel(QUALITY_STATUS_LABELS, value, "待核对");
}

export function displayWorkQueue(value?: string | null) {
  return readableLabel(WORK_QUEUE_LABELS, value, "运营工作项");
}

export function displayWorkPriority(value?: string | null) {
  return readableLabel(WORK_PRIORITY_LABELS, value, "常规");
}

export function displayWorkAction(value?: string | null) {
  return readableLabel(WORK_ACTION_LABELS, value, "状态更新");
}

export function displayActorRole(value?: string | null) {
  return readableLabel(ACTOR_ROLE_LABELS, value, "处理人员");
}

export function displayNotificationRetry(value?: string | null) {
  return readableLabel(NOTIFICATION_RETRY_LABELS, value, "待核对失败原因");
}

const { createSafeHomeApi } = require("../services/api");
const { getAuthUser, requireLogin } = require("./authGuard");
const { createResilientForm } = require("./resilientForm");

const api = createSafeHomeApi();

const STEPS = [
  "boundary",
  "issue",
  "recent_event",
  "resources",
  "sharing",
  "summary",
  "feedback_check",
  "action_review",
];

const CONFIG = {
  boundary: {
    title: "先了解边界",
    description: "这是一段可以暂停、修改和撤回的协作过程。你决定写什么、分享什么，也可以选择现在不开始。",
    prompt: "你现在愿意继续吗？",
    mode: "choice",
    nextLabel: "按我的选择继续",
    options: [
      { value: "continue", label: "我已了解，继续", description: "进入下一步写下自己的议题。" },
      { value: "not_now", label: "现在先不开始", description: "退出本流程，之后仍可回来。" },
    ],
  },
  issue: {
    title: "我的议题",
    description: "从你真正想理解的问题开始，不要求先给关系或自己下结论。",
    prompt: "这次你最想共同理解什么？",
    mode: "text",
    nextLabel: "建立议题并继续",
  },
  recent_event: {
    title: "最近一次事件",
    description: "只记录一次具体片段：发生了什么、当时有什么反应。先不解释深层原因。",
    prompt: "写下最近一次与议题有关的具体片段",
    mode: "text",
    nextLabel: "保存这个片段",
  },
  resources: {
    title: "例外与资源",
    description: "也看看没有那么困难的时刻，以及当时有什么人、做法或环境在帮忙。",
    prompt: "哪些时刻有所不同？什么曾经帮到你？",
    mode: "text",
    nextLabel: "保存例外与资源",
  },
  sharing: {
    title: "资料与共享",
    description: "账号关联不等于自动互看。这里只决定本轮共享范围，之后仍可逐条修改或撤回。",
    prompt: "本轮你愿意共享到什么范围？",
    mode: "choice",
    nextLabel: "保存共享决定",
    options: [
      { value: "question_only", label: "只共享我的议题", description: "不自动带入最近事件原文。" },
      { value: "question_and_event", label: "议题和最近事件", description: "仅供本轮人工协作查看。" },
      { value: "pause_sharing", label: "暂不扩大共享", description: "保留当前最小范围，稍后再决定。" },
    ],
  },
  summary: {
    title: "提交前摘要",
    description: "你的原话不会被系统整理覆盖。请并排核对，再决定是否继续。",
    prompt: "核对这两个版本",
    mode: "summary",
    nextLabel: "保留原话并继续",
  },
  feedback_check: {
    title: "反馈核对",
    description: "反馈是可讨论的版本。不同意不会被记成确认，也不会影响你继续使用其它功能。",
    prompt: "这份反馈和你的体验有多接近？",
    mode: "feedback",
    nextLabel: "保存我的核对",
    options: [
      { value: "like", label: "比较像", description: "大体贴近我的体验。" },
      { value: "partly_like", label: "部分像", description: "有些贴近，也有需要修订的地方。" },
      { value: "not_like", label: "不像", description: "请在下方写下不一致之处。" },
      { value: "need_time", label: "需要想想", description: "先保留，不把沉默当作认可。" },
    ],
  },
  action_review: {
    title: "一个小行动与回看",
    description: "只选择低压力、可停止、由你愿意尝试的一小步。完成次数不代表疗效。",
    prompt: "如果你愿意，下一步想尝试什么？",
    mode: "action",
    nextLabel: "记录并返回总览",
  },
};

function key(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function route(stepId, caseId) {
  const suffix = caseId ? `?caseId=${encodeURIComponent(caseId)}` : "";
  return `/pages/therapeutic-assessment-${stepId.replace(/_/g, "-")}/index${suffix}`;
}

function nextStep(stepId) {
  return STEPS[STEPS.indexOf(stepId) + 1] || "";
}

function previousStep(stepId) {
  return STEPS[STEPS.indexOf(stepId) - 1] || "";
}

function registerTherapeuticAssessmentStepPage(stepId) {
  const config = CONFIG[stepId];
  if (!config) throw new Error(`Unknown therapeutic assessment step: ${stepId}`);

  Page({
    data: {
      ...config,
      stepId,
      stepNumber: STEPS.indexOf(stepId) + 1,
      stepTotal: STEPS.length,
      value: "",
      selected: "",
      actionPlan: {
        purposeText: "",
        plannedDate: "",
        reminderMode: "none",
        stopCondition: "如果感到明显不适、冲突升级或我不再愿意，就先停下来。",
        setbackPlan: "只记录当时发生了什么和阻碍，不责备自己，再决定是否调整。",
        confirmed: false,
      },
      createdActionId: "",
      caseId: "",
      activeCase: null,
      originalText: "",
      systemText: "",
      feedbackTitle: "",
      feedbackContent: "",
      feedbackLayerLabel: "",
      loading: true,
      saving: false,
      offline: false,
      stateKind: "",
      stateTitle: "",
      stateDescription: "",
      saveStatus: "尚未填写",
      remoteVersion: 0,
      canContinue: true,
    },

    onLoad(options) {
      const caseId = decodeURIComponent(options.caseId || "");
      if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {
        this.setData({ loading: false });
        return;
      }
      this.setData({ caseId });
      this.draftController = createResilientForm({
        storageKey: `safehome:resilientDraft:therapeutic:${caseId || "new"}:${stepId}`,
        fields: ["value", "selected", "actionPlan"],
        submissionPrefix: `ta-${stepId}`,
        hasContent: (values) => Boolean(String(values.value || "").trim() || values.selected),
      });
      const local = this.draftController.restore();
      if (local) this.setData({ ...local.values, saveStatus: local.saveStatus });
      this.networkListener = (status) => this.setData({ offline: !status.isConnected });
      if (wx.onNetworkStatusChange) wx.onNetworkStatusChange(this.networkListener);
      this.loadStep();
    },

    onHide() {
      this.flushLocal();
    },

    onUnload() {
      this.flushLocal();
      if (this.networkListener && wx.offNetworkStatusChange) wx.offNetworkStatusChange(this.networkListener);
    },

    flushLocal() {
      if (!this.draftController || this.data.saving) return;
      this.setData(this.draftController.flush({ value: this.data.value, selected: this.data.selected, actionPlan: this.data.actionPlan }));
    },

    async loadStep() {
      this.setData({ loading: true, stateKind: "", stateTitle: "", stateDescription: "" });
      try {
        const safetyStatus = await api.getTherapeuticAssessmentSafetyStatus();
        if (!safetyStatus.ordinary_flow_enabled) {
          this.setData({
            loading: false,
            stateKind: "error",
            stateTitle: "普通流程暂时暂停",
            stateDescription: safetyStatus.participant_message,
            canContinue: false,
          });
          return;
        }
        if (stepId === "boundary" && !this.data.caseId) {
          this.setData({ loading: false });
          return;
        }
        const result = await api.listTherapeuticAssessmentCases();
        const activeCase = (result.items || []).find((item) => item.id === this.data.caseId) || null;
        if (!activeCase && stepId !== "issue") {
          this.setData({
            loading: false,
            stateKind: "empty",
            stateTitle: "还没有本次议题",
            stateDescription: "请先从“我的议题”开始。",
            canContinue: false,
          });
          return;
        }
        if (activeCase && (activeCase.status === "withdrawn" || activeCase.consent_status === "withdrawn")) {
          this.setData({
            activeCase,
            loading: false,
            stateKind: "withdrawn",
            stateTitle: "本次协作已撤回",
            stateDescription: "历史审计按隐私规则保留，但不会继续同步或生成普通反馈。",
            canContinue: false,
          });
          return;
        }
        const latestFeedback = activeCase
          ? (activeCase.feedback_versions || []).filter((item) => item.status === "sent").slice(-1)[0] || null
          : null;
        this.setData({
          activeCase,
          originalText: activeCase ? activeCase.assessment_question : this.data.value,
          systemText: activeCase ? activeCase.working_question : "",
          feedbackTitle: latestFeedback ? latestFeedback.letter_title : "",
          feedbackContent: latestFeedback ? latestFeedback.participant_content : "",
          feedbackLayerLabel: latestFeedback
            ? (latestFeedback.feedback_layer === "layer_2" ? "可讨论的新连接" : "与当前理解一致")
            : "",
          canContinue: stepId !== "action_review" || Boolean(latestFeedback),
        });
        if (stepId === "feedback_check" && !latestFeedback) {
          this.setData({
            stateKind: "empty",
            stateTitle: "还没有可核对的反馈",
            stateDescription: "未经人工复核的草稿不会提前展示。你可以稍后再回来。",
          });
        }
        if (stepId === "action_review" && !latestFeedback) {
          this.setData({
            stateKind: "empty",
            stateTitle: "暂时不用选择行动",
            stateDescription: "收到经人工复核的反馈后，再决定是否尝试下一小步。",
          });
        }
        if (activeCase) {
          const remote = await api.getTherapeuticAssessmentParticipantDraft(activeCase.id, stepId);
          if (remote.version > 0) {
            this.setData({
              value: String(remote.payload.value || ""),
              selected: String(remote.payload.selected || ""),
              actionPlan: remote.payload.actionPlan || this.data.actionPlan,
              remoteVersion: remote.version,
              saveStatus: `已从云端恢复 · ${String(remote.updated_at || "").slice(11, 16) || "刚刚"}`,
            });
          }
        }
      } catch (error) {
        this.applyError(error);
      } finally {
        this.setData({ loading: false });
      }
    },

    applyError(error) {
      const code = String(error.code || "");
      this.setData({
        stateKind: code === "expired" ? "expired" : code === "withdrawn" ? "withdrawn" : "error",
        stateTitle: code === "expired" ? "本次协作已过期" : code === "withdrawn" ? "本次协作已撤回" : "内容暂时没有读取成功",
        stateDescription: error.message || "请检查网络后再试。",
      });
    },

    onValueChange(event) {
      const plan = this.data.actionPlan;
      const canContinue = stepId !== "action_review" || Boolean(
        event.detail.value.trim()
        && plan.purposeText.trim()
        && plan.stopCondition.trim()
        && plan.setbackPlan.trim()
        && plan.confirmed
      );
      this.setData({ value: event.detail.value, canContinue, stateKind: "", saveStatus: "正在保存草稿…" });
      this.draftController.schedule(
        { value: event.detail.value, selected: this.data.selected, actionPlan: this.data.actionPlan },
        (status) => this.setData(status),
      );
    },

    onOptionChange(event) {
      this.setData({ selected: event.detail.value, stateKind: "", saveStatus: "正在保存草稿…" });
      this.draftController.schedule(
        { value: this.data.value, selected: event.detail.value, actionPlan: this.data.actionPlan },
        (status) => this.setData(status),
      );
    },

    onActionChange(event) {
      const actionPlan = { ...this.data.actionPlan, [event.detail.field]: event.detail.value };
      const canContinue = Boolean(
        this.data.value.trim()
        && actionPlan.purposeText.trim()
        && actionPlan.stopCondition.trim()
        && actionPlan.setbackPlan.trim()
        && actionPlan.confirmed
      );
      this.setData({ actionPlan, canContinue, stateKind: "", saveStatus: "正在保存草稿…" });
      this.draftController.schedule(
        { value: this.data.value, selected: this.data.selected, actionPlan },
        (status) => this.setData(status),
      );
    },

    async syncDraft(status = "active") {
      if (!this.data.caseId || this.data.offline) {
        this.flushLocal();
        return null;
      }
      const result = await api.saveTherapeuticAssessmentParticipantDraft(
        this.data.caseId,
        stepId,
        {
          payload: { value: this.data.value, selected: this.data.selected, actionPlan: this.data.actionPlan },
          expected_version: this.data.remoteVersion,
          status,
          client_updated_at: new Date().toISOString(),
        },
        key(`mini-ta-draft-${stepId}`),
      );
      this.setData({ remoteVersion: result.version, saveStatus: "已同步到云端" });
      return result;
    },

    validate() {
      if (config.mode === "choice" && !this.data.selected) return "请选择一项后再继续。";
      if (config.mode === "feedback" && !this.data.selected) return "请先选择反馈与你体验的接近程度。";
      if (config.mode === "feedback" && this.data.selected === "not_like" && !this.data.value.trim()) return "请简要写下不一致的地方。";
      if (stepId === "issue" && !this.data.value.trim()) return "请写下本次最想共同理解的问题。";
      if (stepId === "action_review") {
        const plan = this.data.actionPlan;
        if (!this.data.value.trim() || !plan.purposeText.trim()) return "请写下行动和你想尝试它的原因。";
        if (!plan.stopCondition.trim() || !plan.setbackPlan.trim()) return "请补充停止条件和没做到时的记录方式。";
        if (!plan.confirmed) return "请确认这是你自愿选择、可以停止的一小步。";
      }
      return "";
    },

    async onContinue() {
      const validation = this.validate();
      if (validation) {
        this.setData({ stateKind: "error", stateTitle: "还差一点", stateDescription: validation });
        return;
      }
      if (stepId === "boundary" && this.data.selected === "not_now") {
        wx.navigateBack();
        return;
      }
      this.setData({ saving: true, stateKind: "" });
      try {
        if (stepId === "issue" && !this.data.caseId) {
          const created = await api.createTherapeuticAssessmentCase(
            { assessment_question: this.data.value.trim(), shared_scope: ["question"], consent: true },
            this.draftController.getSubmissionId(),
          );
          this.setData({ caseId: created.id, activeCase: created, originalText: created.assessment_question, systemText: created.working_question });
        }
        await this.syncDraft("completed");
        await this.commitStepContent();
        this.draftController.clear();
        const next = nextStep(stepId);
        if (this.data.createdActionId) {
          wx.redirectTo({
            url: `/pages/therapeutic-assessment-action-followup/index?caseId=${encodeURIComponent(this.data.caseId)}&actionId=${encodeURIComponent(this.data.createdActionId)}`,
          });
        } else if (next) wx.redirectTo({ url: route(next, this.data.caseId) });
        else wx.redirectTo({ url: "/pages/therapeutic-assessment/index" });
      } catch (error) {
        this.applyError(error);
      } finally {
        this.setData({ saving: false });
      }
    },

    async commitStepContent() {
      const activeCase = this.data.activeCase;
      const actor = getAuthUser() || {};
      if (!activeCase) return;
      if (stepId === "recent_event" && this.data.value.trim()) {
        await api.createTherapeuticAssessmentEvidence(activeCase.id, {
          kind: "O",
          content: this.data.value.trim(),
          source_origin: "human",
          source_ref: `participant-flow:${activeCase.id}:recent_event`,
          provider_id: actor.id,
          observed_at: new Date().toISOString(),
          context: "参与者在协作式阶段性评估中记录的最近一次事件",
          visibility_scope: ["participant", "research_team"],
        }, key("mini-ta-recent-event"));
      }
      if (stepId === "resources" && this.data.value.trim()) {
        await api.createTherapeuticAssessmentEvidence(activeCase.id, {
          kind: "O",
          content: this.data.value.trim(),
          source_origin: "human",
          source_ref: `participant-flow:${activeCase.id}:resources`,
          provider_id: actor.id,
          observed_at: new Date().toISOString(),
          context: "参与者主动补充的例外与资源",
          visibility_scope: ["participant", "research_team"],
        }, key("mini-ta-resources"));
      }
      if (stepId === "sharing") {
        const scope = this.data.selected === "question_and_event" ? ["question", "recent_record"] : ["question"];
        const updated = await api.updateTherapeuticAssessmentScope(
          activeCase.id,
          { shared_scope: scope, expected_version: activeCase.version },
          key("mini-ta-sharing"),
        );
        this.setData({ activeCase: updated });
      }
      if (stepId === "feedback_check") {
        const latestFeedback = (activeCase.feedback_versions || []).filter((item) => item.status === "sent").slice(-1)[0];
        if (!latestFeedback) return;
        await api.respondToTherapeuticAssessmentFeedback(
          latestFeedback.id,
          {
            recognition: this.data.selected,
            disagreement_note: this.data.value.trim() || undefined,
          },
          key("mini-ta-feedback-response"),
        );
      }
      if (stepId === "action_review" && this.data.value.trim()) {
        const latestFeedback = (activeCase.feedback_versions || []).filter((item) => item.status === "sent").slice(-1)[0];
        if (latestFeedback) {
          const plan = this.data.actionPlan;
          const action = await api.createTherapeuticAssessmentAction(
            activeCase.id,
            {
              feedback_version_id: latestFeedback.id,
              action_text: this.data.value.trim(),
              purpose_text: plan.purposeText.trim(),
              planned_date: plan.plannedDate || undefined,
              reminder_mode: plan.reminderMode,
              reminder_privacy: "generic_preview",
              stop_conditions: [plan.stopCondition.trim()],
              setback_plan: plan.setbackPlan.trim(),
              voluntary_confirmed: true,
              reversible_confirmed: true,
              stoppable_confirmed: true,
            },
            key("mini-ta-action-review"),
          );
          this.setData({ createdActionId: action.id });
        }
      }
    },

    onRetry() {
      this.loadStep();
    },

    onBack() {
      const previous = previousStep(stepId);
      if (previous) wx.redirectTo({ url: route(previous, this.data.caseId) });
      else wx.navigateBack();
    },
  });
}

module.exports = { registerTherapeuticAssessmentStepPage, STEPS, CONFIG };

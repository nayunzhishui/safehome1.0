const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function submissionKey(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

const WORKFLOW_LABELS = {
  submitted: "已提交",
  pending_human_review: "待人工复核",
  needs_more_info: "待补充资料",
  feedback_ready: "可整理反馈",
  feedback_draft: "反馈草稿",
  professional_review: "待专业复核",
  participant_check: "待你核对",
  revision_requested: "待修订",
  action_selected: "已选择小行动",
  followup: "随访中",
  safety_path: "人工安全支持",
  not_applicable: "本轮不适用",
  archived: "已归档",
  withdrawn: "已撤回",
};

Page({
  data: {
    loading: true,
    saving: false,
    cases: [],
    activeCase: null,
    question: "",
    shareQuestion: true,
    shareRecentRecord: false,
    actionText: "",
    notice: "",
    errorMessage: "",
    evidenceItems: [],
    productionContract: null,
    adultLaunchScope: null,
    childPolicy: null,
    multiPartyPolicy: null,
    aiAssistPolicy: null,
    launchScreening: null,
    defaultServiceLevel: {
      id: "L0",
      display_name: "支持性评估准备",
      short_name: "自助准备",
    },
  },

  onShow() {
    this.loadCases();
  },

  startParticipantFlow() {
    wx.navigateTo({ url: "/pages/therapeutic-assessment-boundary/index" });
  },

  continueParticipantFlow() {
    const caseId = this.data.activeCase && this.data.activeCase.id;
    if (!caseId) {
      this.startParticipantFlow();
      return;
    }
    wx.navigateTo({
      url: `/pages/therapeutic-assessment-boundary/index?caseId=${encodeURIComponent(caseId)}`,
    });
  },

  openQualityRecord() {
    const caseId = this.data.activeCase && this.data.activeCase.id;
    wx.navigateTo({
      url: `/pages/therapeutic-assessment-quality/index${caseId ? `?caseId=${encodeURIComponent(caseId)}` : ""}`,
    });
  },

  async loadCases() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const [result, levelStatus, productionContract, adultLaunchScope, childPolicy, multiPartyPolicy, aiAssistPolicy] = await Promise.all([
        api.listTherapeuticAssessmentCases(),
        api.getTherapeuticAssessmentServiceLevels(),
        api.getTherapeuticAssessmentProductionContract(),
        api.getTherapeuticAssessmentAdultLaunchScope(),
        api.getTherapeuticAssessmentChildPolicy(),
        api.getTherapeuticAssessmentMultiPartyPolicy(),
        api.getTherapeuticAssessmentAiAssistPolicy(),
      ]);
      const cases = (result.items || []).map((item) => ({
        ...item,
        workflowLabel: WORKFLOW_LABELS[item.workflow_state] || item.workflow_state,
        latestFeedback: (item.feedback_versions || []).filter((version) => version.status === "sent").slice(-1)[0] || null,
      }));
      this.setData({
        cases,
        activeCase: cases[0] || null,
        defaultServiceLevel: levelStatus.current_default || this.data.defaultServiceLevel,
        productionContract,
        adultLaunchScope,
        childPolicy,
        multiPartyPolicy,
        aiAssistPolicy,
      });
      if (cases[0]) {
        const [evidence, launchScreening] = await Promise.all([
          api.listTherapeuticAssessmentEvidence(cases[0].id),
          api.getTherapeuticAssessmentLaunchScreening(cases[0].id),
        ]);
        this.setData({ evidenceItems: evidence.items || [], launchScreening });
      } else {
        this.setData({ evidenceItems: [], launchScreening: null });
      }
    } catch (error) {
      this.setData({ errorMessage: error.message || "协作记录暂时无法读取。" });
    } finally {
      this.setData({ loading: false });
    }
  },

  async confirmAdultLaunchScope() {
    const activeCase = this.data.activeCase;
    const scope = this.data.adultLaunchScope;
    if (!activeCase || !scope) return;
    this.setData({ saving: true, errorMessage: "", notice: "" });
    try {
      const launchScreening = await api.submitTherapeuticAssessmentLaunchScreening(
        activeCase.id,
        {
          requested_level: "L1",
          age_band: "adult",
          voluntary_participation: true,
          data_scope: "single_person",
          urgency: "non_urgent",
          concern_scope: "ordinary_relationship_stress",
          excluded_signals: [],
          acknowledged_notices: scope.required_notices,
          expected_case_version: activeCase.version,
        },
        submissionKey("mini-ta-launch"),
      );
      this.setData({
        launchScreening,
        notice: "首发范围信息已记录；正式服务仍需真人与发布门禁确认。",
      });
    } catch (error) {
      this.setData({ errorMessage: error.message || "首发范围暂时没有记录成功。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  onQuestionInput(event) {
    this.setData({ question: event.detail.value });
  },

  onActionInput(event) {
    this.setData({ actionText: event.detail.value });
  },

  onScopeChange(event) {
    const values = event.detail.value || [];
    this.setData({
      shareQuestion: values.includes("question"),
      shareRecentRecord: values.includes("recent_record"),
    });
  },

  async createCase() {
    const question = this.data.question.trim();
    const sharedScope = [];
    if (this.data.shareQuestion) sharedScope.push("question");
    if (this.data.shareRecentRecord) sharedScope.push("recent_record");
    if (!question || !sharedScope.length) {
      this.setData({ errorMessage: "请写下想共同理解的问题，并至少选择一项共享范围。" });
      return;
    }
    this.setData({ saving: true, errorMessage: "", notice: "" });
    try {
      await api.createTherapeuticAssessmentCase(
        { assessment_question: question, shared_scope: sharedScope, consent: true },
        submissionKey("mini-ta-case"),
      );
      this.setData({ question: "", notice: "问题已提交。你仍可修改共享范围、表达不同意见或撤回。" });
      await this.loadCases();
    } catch (error) {
      this.setData({ errorMessage: error.message || "问题暂时没有提交成功。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  async chooseAction() {
    const activeCase = this.data.activeCase;
    const actionText = this.data.actionText.trim();
    if (!activeCase || !activeCase.latestFeedback || !actionText) {
      this.setData({ errorMessage: "收到经人工复核的反馈后，再写下一个愿意尝试的小行动。" });
      return;
    }
    this.setData({ saving: true, errorMessage: "", notice: "" });
    try {
      await api.createTherapeuticAssessmentAction(
        activeCase.id,
        { feedback_version_id: activeCase.latestFeedback.id, action_text: actionText },
        submissionKey("mini-ta-action"),
      );
      this.setData({ actionText: "", notice: "已记录你选择的下一小步。" });
      await this.loadCases();
    } catch (error) {
      this.setData({ errorMessage: error.message || "下一小步暂时没有保存成功。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  async updateQuestionAction(event) {
    const activeCase = this.data.activeCase;
    const action = event.currentTarget.dataset.action;
    if (!activeCase || !action) return;
    this.setData({ saving: true, errorMessage: "" });
    try {
      await api.updateTherapeuticAssessmentQuestion(
        activeCase.id,
        { action, expected_version: activeCase.version },
        submissionKey(`mini-ta-question-${action}`),
      );
      this.setData({ notice: action === "pause" ? "已暂停，你可以稍后继续。" : "问题候选状态已更新。" });
      await this.loadCases();
    } catch (error) {
      this.setData({ errorMessage: error.message || "问题状态暂时没有更新成功。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  disagree() {
    const activeCase = this.data.activeCase;
    if (!activeCase) return;
    wx.showModal({
      title: "表达不同意见",
      editable: true,
      placeholderText: "哪些地方与你的体验不一致？",
      success: async (result) => {
        if (!result.confirm || !String(result.content || "").trim()) return;
        try {
          await api.transitionTherapeuticAssessment(activeCase.id, "disagree", { note: result.content }, submissionKey("mini-ta-disagree"));
          this.setData({ notice: "不同意见已记录，研究者会在下一版本中看到。" });
          await this.loadCases();
        } catch (error) {
          this.setData({ errorMessage: error.message || "不同意见暂时没有保存成功。" });
        }
      },
    });
  },

  withdraw() {
    const activeCase = this.data.activeCase;
    if (!activeCase) return;
    wx.showModal({
      title: "确认撤回本次协作？",
      content: "撤回后不会继续发送新的普通反馈，历史审计按隐私规则保留。",
      success: async (result) => {
        if (!result.confirm) return;
        try {
          await api.transitionTherapeuticAssessment(activeCase.id, "withdraw", { note: "参与者主动撤回" }, submissionKey("mini-ta-withdraw"));
          this.setData({ notice: "本次协作已撤回。" });
          await this.loadCases();
        } catch (error) {
          this.setData({ errorMessage: error.message || "撤回暂时没有完成。" });
        }
      },
    });
  },
});

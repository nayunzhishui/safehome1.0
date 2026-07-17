const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function draftKey(programId, sessionNo) {
  return `safehome:programDraft:${programId}:${sessionNo}`;
}

function markActiveSessions(sessions, selectedSession) {
  const selectedNo = selectedSession ? Number(selectedSession.session_no) : null;
  return (sessions || []).map((session) => ({
    ...session,
    isActive: Number(session.session_no) === selectedNo,
  }));
}

function formatProgram(program) {
  const measurementPlan = program.measurement_plan || null;
  return {
    ...program,
    previewLabel: program.showcase_open ? "临时展示开放" : program.review_status === "pilot_approved" ? "已批准试点" : "开发预览，尚未正式开放",
    doseText: program.minimum_dose
      ? `计划 ${program.minimum_dose.planned_sessions} 节，至少完成 ${program.minimum_dose.minimum_completed_sessions} 节；建议间隔 ${program.minimum_dose.session_interval_days}`
      : "",
    measurementPlan: measurementPlan
      ? {
          ...measurementPlan,
          statusLabel: measurementPlan.status === "pilot_approved" ? "试点已确认" : "待研究负责人确认",
        }
      : null,
  };
}

Page({
  data: {
    programId: "",
    previewMode: false,
    program: null,
    sessions: [],
    selectedSession: null,
    draftText: "",
    reflectionAnswers: {},
    submittedEntries: [],
    analysisConsent: false,
    distressBefore: 5,
    distressAfter: 5,
    adverseResponse: false,
    submitting: false,
    successMessage: "",
    loading: true,
    errorMessage: "",
  },

  onLoad(query) {
    const programId = decodeURIComponent(query.id || "");
    const previewMode = query.preview === "1";
    this.setData({ programId, previewMode });
    this.loadProgram(programId);
  },

  loadProgram(programId) {
    if (!programId) {
      this.setData({ loading: false, errorMessage: "缺少项目 ID，请返回后重新打开。" });
      return;
    }
    this.setData({ loading: true, errorMessage: "" });
    api
      .getProgram(programId, this.data.previewMode ? { include_drafts: true } : {})
      .then((data) => {
        const program = formatProgram(data.program);
        const rawSessions = program.sessions || [];
        const selectedSession = rawSessions[0] || null;
        const sessions = markActiveSessions(rawSessions, selectedSession);
        this.setData(
          {
            program,
            sessions,
            selectedSession,
            loading: false,
          },
          () => {
            this.loadDraft();
            if (!this.data.previewMode) this.loadSubmittedEntries();
          },
        );
      })
      .catch((error) => {
        this.setData({
          loading: false,
          errorMessage: error.message || "项目内容暂时没能读取，请检查网络后再试一次。",
        });
        wx.showToast({ title: error.message || "读取失败", icon: "none" });
      });
  },

  retryLoad() {
    this.loadProgram(this.data.programId);
  },

  selectSession(event) {
    const sessionNo = Number(event.currentTarget.dataset.sessionNo);
    const selectedSession = (this.data.sessions || []).find((item) => Number(item.session_no) === sessionNo);
    if (!selectedSession) {
      return;
    }
    this.setData({ selectedSession, sessions: markActiveSessions(this.data.sessions, selectedSession), draftText: "", reflectionAnswers: {} }, () => this.loadDraft());
  },

  loadDraft() {
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      return;
    }
    const stored = wx.getStorageSync(draftKey(this.data.programId, session.session_no));
    if (stored && typeof stored === "object") {
      this.setData({
        draftText: stored.draftText || "",
        reflectionAnswers: stored.reflectionAnswers || {},
      });
      return;
    }
    this.setData({ draftText: stored || "", reflectionAnswers: {} });
  },

  onDraftInput(event) {
    this.setData({ draftText: event.detail.value, successMessage: "", errorMessage: "" });
  },

  onReflectionInput(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.setData({
      [`reflectionAnswers.${index}`]: event.detail.value,
      successMessage: "",
      errorMessage: "",
    });
  },

  onAnalysisConsentChange(event) {
    this.setData({ analysisConsent: !!event.detail.value.length });
  },

  onDistressBeforeChange(event) {
    this.setData({ distressBefore: Number(event.detail.value) });
  },

  onDistressAfterChange(event) {
    this.setData({ distressAfter: Number(event.detail.value) });
  },

  onAdverseResponseChange(event) {
    this.setData({ adverseResponse: !!event.detail.value.length });
  },

  saveDraft() {
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      return;
    }
    wx.setStorageSync(draftKey(this.data.programId, session.session_no), {
      draftText: this.data.draftText || "",
      reflectionAnswers: this.data.reflectionAnswers || {},
    });
    wx.showToast({ title: "已保存在本机", icon: "success" });
  },

  async loadSubmittedEntries() {
    try {
      const payload = await api.listProgramEntries(this.data.programId);
      this.setData({
        submittedEntries: (payload.items || []).map((item) => ({
          ...item,
          createdAtText: String(item.created_at || "").slice(0, 16).replace("T", " "),
          sessionText: `第 ${item.session_no} 节`,
        })),
      });
    } catch (error) {
      if (error.code !== "auth_required") console.warn("[program entries]", error);
    }
  },

  async submitEntry() {
    const session = this.data.selectedSession;
    const draftText = (this.data.draftText || "").trim();
    const reflectionAnswers = (session.reflection_questions || []).map((question, index) => ({
      question,
      answer: String((this.data.reflectionAnswers || {})[index] || "").trim(),
    }));
    const answeredReflections = reflectionAnswers.filter((item) => item.answer);
    if (!this.data.programId || !session) {
      this.setData({ errorMessage: "缺少项目信息，请返回重新打开。" });
      return;
    }
    if (!draftText && !answeredReflections.length) {
      this.setData({ errorMessage: "请先填写书写内容或至少一个反思问题。" });
      return;
    }
    this.setData({ submitting: true, successMessage: "", errorMessage: "" });
    try {
      await api.createProgramEntry(this.data.programId, {
        session_no: session.session_no,
        answers: {
          writing_prompt: session.writing_prompt || "",
          draft_text: draftText,
          reflection_answers: reflectionAnswers,
        },
        reflection: draftText || answeredReflections.map((item) => `${item.question}：${item.answer}`).join("\n"),
        analysis_consent: this.data.analysisConsent,
        participation_status: "completed",
        recommendation_source: "user_choice",
        distress_before: this.data.distressBefore,
        distress_after: this.data.distressAfter,
        adverse_response: this.data.adverseResponse,
        boundary_notice: this.data.program ? this.data.program.boundary_notice : "",
      });
      wx.removeStorageSync(draftKey(this.data.programId, session.session_no));
      this.setData({
        draftText: "",
        reflectionAnswers: {},
        successMessage: "已提交。它只用于本工具内复盘、训练建议和必要的人工补充反馈。",
      });
      await this.loadSubmittedEntries();
    } catch (error) {
      this.setData({
        errorMessage: error.message || "暂时没能提交，请登录后再试一次。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },
});

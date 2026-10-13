const { captureAuthSession, getAuthUser, isCurrentAuthSession } = require("../../utils/authGuard");
const { createSafeHomeApi } = require("../../services/api");
const { beginServiceEntry, finishServiceConsent } = require("../../utils/serviceConsent");

const api = createSafeHomeApi();

const RESEARCH_ROLES = ["researcher", "supervisor", "admin"];
const HELP_RESOURCES_URL = "/pages/emergency-resources/index";
const PARTICIPATION_OPTIONS = [
  { value: "completed", label: "完成了这一节" },
  { value: "skipped", label: "这一节先跳过" },
  { value: "paused", label: "先暂停这个项目" },
];
const PARTICIPATION_TEXT = { completed: "已完成", skipped: "已跳过", paused: "已暂停", withdrawn: "已退出" };
const SUBMITTED_TEXT = {
  completed: "已提交。它只用于本工具内复盘、训练建议和必要的人工补充反馈。",
  skipped: "已记录：这一节先跳过。想回来写的时候随时可以。",
  paused: "已记录暂停。休息好了再回来；需要时可以查看求助资源。",
};
const REVIEW_TEXT = {
  pilot_approved: "研究、心理、伦理三方已批准",
  production_approved: "项目负责人决定开放，研究、心理、伦理审核待完成",
  pilot_draft: "草案，待研究、心理、伦理审核",
};

function draftKey(programId, sessionNo, ownerId) {
  return `safehome:programDraft:${programId}:${sessionNo}:user:${encodeURIComponent(ownerId)}`;
}

function markActiveSessions(sessions, selectedSession, completedNos = []) {
  const selectedNo = selectedSession ? Number(selectedSession.session_no) : null;
  return (sessions || []).map((session) => ({
    ...session,
    isActive: Number(session.session_no) === selectedNo,
    isDone: completedNos.includes(Number(session.session_no)),
  }));
}

function completedSessionNos(entries) {
  return [...new Set((entries || [])
    .filter((item) => (item.participation_status || "completed") === "completed")
    .map((item) => Number(item.session_no)))];
}

// Rough, non-clinical cue to pause: a high rating after writing, or a clear rise from the start.
function distressNoticeText(before, after) {
  if (after >= 8) return "现在的不适程度比较高。可以先停在这里，不用继续写；如果需要，请联系身边可信任的人，或查看求助资源。";
  if (after - before >= 3) return "写完后比开始时更难受了。可以先停一停，做点让自己放松的事；如果需要，请联系身边可信任的人，或查看求助资源。";
  return "";
}

function minutesText(sessions) {
  const minutes = (sessions || []).map((session) => Number(session.duration_minutes)).filter((value) => value > 0);
  if (!minutes.length) return "";
  const low = Math.min(...minutes);
  const high = Math.max(...minutes);
  return low === high ? `${low}` : `${low}–${high}`;
}

// 已提交记录按“10月8日”显示（Figma 666:2991）；解析失败时退回原始日期。
function shortDateText(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value || ""));
  if (!match) return String(value || "").slice(0, 10);
  return `${Number(match[2])}月${Number(match[3])}日`;
}

function formatProgram(program) {
  const measurementPlan = program.measurement_plan || null;
  const sessions = program.sessions || [];
  const minutes = minutesText(sessions);
  return {
    ...program,
    previewLabel: program.showcase_open ? "临时展示开放" : program.review_status === "pilot_approved" ? "已批准试点" : program.review_status === "production_approved" ? "已开放" : "开发预览，尚未正式开放",
    sessionCountText: sessions.length ? `共 ${sessions.length} 节${minutes ? `，每节约 ${minutes} 分钟` : ""}` : "",
    reviewText: REVIEW_TEXT[program.review_status] || program.review_status || "",
    evidence: (program.evidence_basis || []).filter((item) => item && item.finding),
    constructText: (program.target_constructs || []).join(" · "),
    doseText: program.minimum_dose
      ? `计划 ${program.minimum_dose.planned_sessions} 节，至少完成 ${program.minimum_dose.minimum_completed_sessions} 节；建议间隔 ${program.minimum_dose.session_interval_days}`
      : "",
    measurementPlan: measurementPlan
      ? {
          ...measurementPlan,
          statusLabel: measurementPlan.status === "pilot_approved" ? "试点已确认" : "待研究负责人确认",
          outcomeText: (measurementPlan.primary_outcomes || []).join(" · "),
        }
      : null,
  };
}

Page({
  isDraftOwner() { return !!this._draftOwner && String((wx.getStorageSync("auth_user") || {}).id || "") === this._draftOwner; },
  onUnload() { this._consentDisposed = true; finishServiceConsent(this, false); },
  retryServiceEntry() { return this.onLoad(this._entryOptions || {}); },
  returnToPrivacyHome() { wx.switchTab({ url: "/pages/home/index" }); },
  data: {
    serviceReady: false,
    programId: "",
    requestedSessionNo: null,
    previewMode: false,
    program: null,
    sessions: [],
    selectedSession: null,
    draftText: "",
    reflectionAnswers: {},
    submittedEntries: [],
    completedNos: [],
    progressText: "",
    showResearchInfo: false,
    participationOptions: PARTICIPATION_OPTIONS,
    participationStatus: "completed",
    statusNote: "",
    analysisConsent: false,
    distressBefore: 5,
    distressAfter: 5,
    distressNotice: "",
    adverseResponse: false,
    submitting: false,
    successMessage: "",
    safetyMessage: "",
    loading: true,
    errorMessage: "",
  },

  onLoad(query = {}) {
    this._entryOptions = query;
    if (query.preview === "1") { this.setData({ serviceReady: true }); return this.loadAfterConsent(query); }
    return beginServiceEntry(this, api, "program", query, "/pages/program-detail/index");
  },
  onShow() {
    this._hidden = false;
    if (this._readSession && !isCurrentAuthSession(this._readSession)) {
      this.setData({ submittedEntries: [], completedNos: [], progressText: "", draftText: "", reflectionAnswers: {}, participationStatus: "completed", statusNote: "", analysisConsent: false, distressBefore: 5, distressAfter: 5, distressNotice: "", adverseResponse: false, successMessage: "", safetyMessage: "", serviceReady: false, submitting: false });
      return this.onLoad(this._entryOptions || {});
    }
    if (this.data.loading && this.data.programId) this.loadProgram(this.data.programId);
  },
  onHide() { this._hidden = true; },

  loadAfterConsent(query) {
    this._draftOwner = String((wx.getStorageSync("auth_user") || {}).id || "");
    const programId = decodeURIComponent(query.id || "");
    const previewMode = query.preview === "1";
    const requestedSessionNo = query.session ? Number(query.session) : null;
    const showResearchInfo = previewMode || RESEARCH_ROLES.includes(String((getAuthUser() || {}).role || ""));
    this.setData({ programId, previewMode, requestedSessionNo, showResearchInfo });
    this.loadProgram(programId);
  },

  loadProgram(programId) {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._programRequestId = (this._programRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._programRequestId && isCurrentAuthSession(session);
    if (!programId) {
      this.setData({ loading: false, errorMessage: "缺少项目 ID，请返回后重新打开。" });
      return;
    }
    this.setData({ loading: true, errorMessage: "" });
    api
      .getProgram(programId, this.data.previewMode ? { include_drafts: true } : {})
      .then((data) => {
        if (!isCurrent()) return;
        const program = formatProgram(data.program);
        const rawSessions = program.sessions || [];
        const selectedSession = rawSessions.find(
          (item) => Number(item.session_no) === Number(this.data.requestedSessionNo),
        ) || rawSessions[0] || null;
        const sessions = markActiveSessions(rawSessions, selectedSession, this.data.completedNos);
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
        if (!isCurrent()) return;
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
    this.setData({
      selectedSession,
      sessions: markActiveSessions(this.data.sessions, selectedSession, this.data.completedNos),
      draftText: "",
      reflectionAnswers: {},
      participationStatus: "completed",
      statusNote: "",
      successMessage: "",
      safetyMessage: "",
      errorMessage: "",
    }, () => this.loadDraft());
  },

  openHelpResources() {
    wx.navigateTo({ url: HELP_RESOURCES_URL });
  },

  loadDraft() {
    if (this.data.previewMode || !this.isDraftOwner()) return;
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      return;
    }
    const stored = wx.getStorageSync(draftKey(this.data.programId, session.session_no, this._draftOwner));
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

  onParticipationChange(event) {
    this.setData({ participationStatus: event.detail.value || "completed", successMessage: "", errorMessage: "" });
  },

  pickParticipation(event) {
    this.onParticipationChange({ detail: { value: event.currentTarget.dataset.value } });
  },

  onStatusNoteInput(event) {
    this.setData({ statusNote: event.detail.value });
  },

  onDistressBeforeChange(event) {
    const distressBefore = Number(event.detail.value);
    this.setData({ distressBefore, distressNotice: distressNoticeText(distressBefore, this.data.distressAfter) });
  },

  onDistressAfterChange(event) {
    const distressAfter = Number(event.detail.value);
    this.setData({ distressAfter, distressNotice: distressNoticeText(this.data.distressBefore, distressAfter) });
  },

  onAdverseResponseChange(event) {
    this.setData({ adverseResponse: !!event.detail.value.length });
  },

  // 点勾选框旁的文字也能切换，和登录页协议勾选一致。
  flipAdverseResponse() {
    this.setData({ adverseResponse: !this.data.adverseResponse });
  },

  flipAnalysisConsent() {
    this.setData({ analysisConsent: !this.data.analysisConsent });
  },

  saveDraft() {
    if (this.data.previewMode || !this.isDraftOwner()) return;
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      return;
    }
    wx.setStorageSync(draftKey(this.data.programId, session.session_no, this._draftOwner), {
      draftText: this.data.draftText || "",
      reflectionAnswers: this.data.reflectionAnswers || {},
    });
    wx.showToast({ title: "已保存在本机", icon: "success" });
  },

  async loadSubmittedEntries() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._entriesRequestId = (this._entriesRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._entriesRequestId && isCurrentAuthSession(session);
    try {
      const payload = await api.listProgramEntries(this.data.programId);
      if (!isCurrent()) return;
      const items = payload.items || [];
      const completedNos = completedSessionNos(items);
      const total = (this.data.sessions || []).length;
      this.setData({
        submittedEntries: items.map((item) => ({
          ...item,
          createdAtText: shortDateText(item.created_at),
          sessionText: `第 ${item.session_no} 节`,
          statusText: PARTICIPATION_TEXT[item.participation_status] || "已提交",
        })),
        completedNos,
        sessions: markActiveSessions(this.data.sessions, this.data.selectedSession, completedNos),
        progressText: completedNos.length && total ? `已完成 ${completedNos.length} / ${total} 节` : "",
      });
    } catch (error) {
      if (!isCurrent()) return;
      if (error.code !== "auth_required") console.warn("[program entries]", error);
    }
  },

  async submitEntry() {
    if (this.data.previewMode || this.data.submitting || this._hidden || this._consentDisposed || !this.isDraftOwner() || !isCurrentAuthSession(this._readSession)) return;
    const authSession = captureAuthSession();
    const isCurrent = () => !this._hidden && !this._consentDisposed && this.isDraftOwner() && isCurrentAuthSession(authSession);
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      this.setData({ errorMessage: "缺少项目信息，请返回重新打开。" });
      return;
    }
    const draftText = (this.data.draftText || "").trim();
    const reflectionAnswers = (session.reflection_questions || []).map((question, index) => ({
      question,
      answer: String((this.data.reflectionAnswers || {})[index] || "").trim(),
    }));
    const answeredReflections = reflectionAnswers.filter((item) => item.answer);
    const participationStatus = this.data.participationStatus || "completed";
    const statusNote = String(this.data.statusNote || "").trim();
    if (participationStatus === "completed" && !draftText && !answeredReflections.length) {
      this.setData({ errorMessage: "请先填写书写内容或至少一个反思问题；不想写的话，可以选择“这一节先跳过”。" });
      return;
    }
    this.setData({ submitting: true, successMessage: "", safetyMessage: "", errorMessage: "" });
    try {
      const result = await api.createProgramEntry(this.data.programId, {
        session_no: session.session_no,
        answers: {
          writing_prompt: session.writing_prompt || "",
          draft_text: draftText,
          reflection_answers: reflectionAnswers,
          participation_note: statusNote,
        },
        reflection: draftText || answeredReflections.map((item) => `${item.question}：${item.answer}`).join("\n") || statusNote,
        analysis_consent: this.data.analysisConsent,
        participation_status: participationStatus,
        recommendation_source: "user_choice",
        distress_before: this.data.distressBefore,
        distress_after: this.data.distressAfter,
        adverse_response: this.data.adverseResponse,
        boundary_notice: this.data.program ? this.data.program.boundary_notice : "",
      });
      if (!isCurrent()) return;
      if (this.isDraftOwner()) wx.removeStorageSync(draftKey(this.data.programId, session.session_no, this._draftOwner));
      this.setData({
        draftText: "",
        reflectionAnswers: {},
        participationStatus: "completed",
        statusNote: "",
        successMessage: SUBMITTED_TEXT[participationStatus] || SUBMITTED_TEXT.completed,
        safetyMessage: result && result.requires_review ? result.risk_safe_response || "" : "",
      });
      await this.loadSubmittedEntries();
    } catch (error) {
      if (!isCurrent()) return;
      this.setData({
        errorMessage: error.message || "暂时没能提交，请登录后再试一次。",
      });
    } finally {
      if (isCurrentAuthSession(authSession) && !this._consentDisposed) this.setData({ submitting: false });
    }
  },
});

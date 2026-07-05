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

Page({
  data: {
    programId: "",
    program: null,
    sessions: [],
    selectedSession: null,
    draftText: "",
    loading: true,
    errorMessage: "",
  },

  onLoad(query) {
    const programId = decodeURIComponent(query.id || "");
    this.setData({ programId });
    this.loadProgram(programId);
  },

  loadProgram(programId) {
    if (!programId) {
      this.setData({ loading: false, errorMessage: "缺少项目 ID，请返回后重新打开。" });
      return;
    }
    this.setData({ loading: true, errorMessage: "" });
    api
      .getProgram(programId)
      .then((data) => {
        const program = data.program;
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
          () => this.loadDraft(),
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
    this.setData({ selectedSession, sessions: markActiveSessions(this.data.sessions, selectedSession), draftText: "" }, () => this.loadDraft());
  },

  loadDraft() {
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      return;
    }
    this.setData({
      draftText: wx.getStorageSync(draftKey(this.data.programId, session.session_no)) || "",
    });
  },

  onDraftInput(event) {
    this.setData({ draftText: event.detail.value });
  },

  saveDraft() {
    const session = this.data.selectedSession;
    if (!this.data.programId || !session) {
      return;
    }
    wx.setStorageSync(draftKey(this.data.programId, session.session_no), this.data.draftText || "");
    wx.showToast({ title: "已保存在本机", icon: "success" });
  },
});

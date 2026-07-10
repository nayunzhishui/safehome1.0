const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const CONTEXTS = ["表白", "争吵", "冷战", "靠近", "边界表达", "被拒绝", "真实表达"];
const DRAFT_VERSION = 1;

function cloneStrokes(strokes) {
  return (strokes || []).map((stroke) => stroke.map((point) => ({ x: point.x, y: point.y })));
}

function contextItemsFromAnswers(answers = {}) {
  return CONTEXTS.map((key, index) => {
    const value = String(answers[key] || "");
    return {
      key,
      label: key,
      value,
      count: value.length,
      answered: Boolean(value.trim()),
      expanded: index === 0 || Boolean(value.trim()),
    };
  });
}

function createIdempotencyKey(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

Page({
  data: {
    enrollmentId: "",
    taskType: "relationship_drawing",
    isDrawing: true,
    contextItems: contextItemsFromAnswers(),
    answers: {},
    narration: "",
    narrationCount: 0,
    consent: false,
    saving: false,
    saveStatus: "尚未填写",
    draftRestored: false,
    hasLocalDraft: false,
    canUndo: false,
    canRedo: false,
  },
  strokes: [],
  currentStroke: null,
  strokeSnapshot: null,
  history: [],
  future: [],
  draftKey: "",
  draftTimer: null,
  submissionKey: "",

  onLoad(options) {
    const taskType = decodeURIComponent(options.type || "relationship_drawing");
    const enrollmentId = decodeURIComponent(options.enrollment_id || "");
    this.draftKey = `relationship_task_draft:${enrollmentId}:${taskType}`;
    this.submissionKey = createIdempotencyKey("relationship-task");
    this.setData(
      {
        enrollmentId,
        taskType,
        isDrawing: taskType === "relationship_drawing",
      },
      () => this.restoreDraft(),
    );
  },

  onReady() {
    if (this.data.isDrawing && this.strokes.length) {
      this.redrawCanvas();
    }
  },

  onHide() {
    this.persistDraftNow();
  },

  onUnload() {
    if (this.draftTimer) clearTimeout(this.draftTimer);
  },

  restoreDraft() {
    let draft = null;
    try {
      draft = wx.getStorageSync(this.draftKey);
    } catch (error) {
      draft = null;
    }
    if (!draft || draft.version !== DRAFT_VERSION) return;

    const answers = draft.answers && typeof draft.answers === "object" ? draft.answers : {};
    this.strokes = cloneStrokes(draft.strokes || []);
    this.submissionKey = draft.submissionKey || this.submissionKey;
    this.history = this.strokes.length ? [[]] : [];
    this.future = [];
    this.setData(
      {
        answers,
        contextItems: contextItemsFromAnswers(answers),
        narration: String(draft.narration || ""),
        narrationCount: String(draft.narration || "").length,
        consent: Boolean(draft.consent),
        saveStatus: "已恢复本机草稿",
        draftRestored: true,
        hasLocalDraft: true,
        canUndo: this.history.length > 0,
        canRedo: false,
      },
      () => {
        this.updateUnloadGuard(true);
        if (this.data.isDrawing && this.strokes.length) setTimeout(() => this.redrawCanvas(), 30);
      },
    );
  },

  hasDraftContent() {
    const hasAnswers = Object.values(this.data.answers || {}).some((value) => String(value || "").trim());
    return Boolean(this.strokes.length || this.data.narration.trim() || hasAnswers);
  },

  scheduleDraftSave() {
    if (this.draftTimer) clearTimeout(this.draftTimer);
    this.setData({ saveStatus: "正在保存到本机..." });
    this.draftTimer = setTimeout(() => this.persistDraftNow(), 220);
  },

  persistDraftNow() {
    if (!this.draftKey || this.data.saving) return;
    if (this.draftTimer) {
      clearTimeout(this.draftTimer);
      this.draftTimer = null;
    }
    const hasContent = this.hasDraftContent();
    try {
      if (!hasContent) {
        wx.removeStorageSync(this.draftKey);
        this.setData({ saveStatus: "尚未填写", hasLocalDraft: false, draftRestored: false });
        this.updateUnloadGuard(false);
        return;
      }
      wx.setStorageSync(this.draftKey, {
        version: DRAFT_VERSION,
        taskType: this.data.taskType,
        strokes: cloneStrokes(this.strokes),
        narration: this.data.narration,
        answers: this.data.answers,
        consent: this.data.consent,
        submissionKey: this.submissionKey,
        updatedAt: new Date().toISOString(),
      });
      this.setData({ saveStatus: "草稿已保存在本机", hasLocalDraft: true });
      this.updateUnloadGuard(true);
    } catch (error) {
      this.setData({ saveStatus: "本机草稿保存失败，请先不要退出" });
    }
  },

  updateUnloadGuard(enabled) {
    if (enabled && wx.enableAlertBeforeUnload) {
      wx.enableAlertBeforeUnload({ message: "内容已保存在本机，但还没有提交。确定先离开吗？" });
      return;
    }
    if (!enabled && wx.disableAlertBeforeUnload) wx.disableAlertBeforeUnload();
  },

  startStroke(event) {
    if (!this.data.isDrawing || this.data.saving) return;
    const touch = event.touches[0];
    this.strokeSnapshot = cloneStrokes(this.strokes);
    this.currentStroke = [{ x: touch.x, y: touch.y }];
  },

  moveStroke(event) {
    if (!this.currentStroke) return;
    const touch = event.touches[0];
    const previous = this.currentStroke[this.currentStroke.length - 1];
    this.currentStroke.push({ x: touch.x, y: touch.y });
    const ctx = wx.createCanvasContext("relationshipCanvas", this);
    ctx.setStrokeStyle("#4f7c6b");
    ctx.setLineWidth(3);
    ctx.setLineCap("round");
    ctx.beginPath();
    ctx.moveTo(previous.x, previous.y);
    ctx.lineTo(touch.x, touch.y);
    ctx.stroke();
    ctx.draw(true);
  },

  endStroke() {
    if (this.currentStroke && this.currentStroke.length > 1) {
      this.history.push(this.strokeSnapshot || cloneStrokes(this.strokes));
      if (this.history.length > 30) this.history.shift();
      this.strokes.push(this.currentStroke);
      this.future = [];
      this.syncDrawingHistory();
      this.scheduleDraftSave();
    }
    this.currentStroke = null;
    this.strokeSnapshot = null;
  },

  syncDrawingHistory() {
    this.setData({ canUndo: this.history.length > 0, canRedo: this.future.length > 0 });
  },

  redrawCanvas() {
    const ctx = wx.createCanvasContext("relationshipCanvas", this);
    ctx.clearRect(0, 0, 1000, 1000);
    ctx.setStrokeStyle("#4f7c6b");
    ctx.setLineWidth(3);
    ctx.setLineCap("round");
    this.strokes.forEach((stroke) => {
      if (!stroke || stroke.length < 2) return;
      ctx.beginPath();
      ctx.moveTo(stroke[0].x, stroke[0].y);
      stroke.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
      ctx.stroke();
    });
    ctx.draw();
  },

  undoStroke() {
    if (!this.history.length || this.data.saving) return;
    this.future.push(cloneStrokes(this.strokes));
    this.strokes = this.history.pop();
    this.redrawCanvas();
    this.syncDrawingHistory();
    this.scheduleDraftSave();
  },

  redoStroke() {
    if (!this.future.length || this.data.saving) return;
    this.history.push(cloneStrokes(this.strokes));
    this.strokes = this.future.pop();
    this.redrawCanvas();
    this.syncDrawingHistory();
    this.scheduleDraftSave();
  },

  clearCanvas() {
    if (!this.strokes.length || this.data.saving) return;
    wx.showModal({
      title: "清空画布？",
      content: "清空后仍可使用“撤销”恢复。",
      confirmText: "清空",
      confirmColor: "#a84232",
      success: (result) => {
        if (!result.confirm) return;
        this.history.push(cloneStrokes(this.strokes));
        this.strokes = [];
        this.future = [];
        this.redrawCanvas();
        this.syncDrawingHistory();
        this.scheduleDraftSave();
      },
    });
  },

  onNarrationInput(event) {
    const narration = event.detail.value;
    this.setData({ narration, narrationCount: narration.length });
    this.scheduleDraftSave();
  },

  toggleContext(event) {
    const key = event.currentTarget.dataset.key;
    const contextItems = this.data.contextItems.map((item) => (
      item.key === key ? { ...item, expanded: !item.expanded } : item
    ));
    this.setData({ contextItems });
  },

  onSentenceInput(event) {
    const key = event.currentTarget.dataset.key;
    const value = event.detail.value;
    const answers = { ...this.data.answers, [key]: value };
    const contextItems = this.data.contextItems.map((item) => (
      item.key === key
        ? { ...item, value, count: value.length, answered: Boolean(value.trim()) }
        : item
    ));
    this.setData({ answers, contextItems });
    this.scheduleDraftSave();
  },

  toggleConsent(event) {
    this.setData({ consent: (event.detail.value || []).includes("agree") });
    this.scheduleDraftSave();
  },

  getCanvasSize() {
    return new Promise((resolve) => {
      wx.createSelectorQuery().in(this).select(".drawing-canvas").boundingClientRect((rect) => {
        resolve({ width: rect && rect.width ? rect.width : 320, height: rect && rect.height ? rect.height : 260 });
      }).exec();
    });
  },

  async saveTask() {
    if (!this.data.consent) {
      wx.showToast({ title: "请先确认材料授权", icon: "none" });
      return;
    }
    const answers = Object.fromEntries(Object.entries(this.data.answers).filter(([, value]) => String(value || "").trim()));
    if (this.data.isDrawing && (!this.strokes.length || !this.data.narration.trim())) {
      wx.showToast({ title: "请画一些线条并写一句画外音", icon: "none" });
      return;
    }
    if (!this.data.isDrawing && !Object.keys(answers).length) {
      wx.showToast({ title: "请至少完成一个愿意回答的句子", icon: "none" });
      return;
    }
    this.setData({ saving: true, saveStatus: "正在提交..." });
    try {
      const canvasSize = this.data.isDrawing ? await this.getCanvasSize() : {};
      const saved = await api.createRelationshipTask(this.data.enrollmentId, {
        task_type: this.data.taskType,
        drawing_data: this.data.isDrawing
          ? { strokes: this.strokes, canvas_width: canvasSize.width, canvas_height: canvasSize.height }
          : {},
        narration: this.data.narration,
        answers,
        material_consent: true,
        idempotency_key: this.submissionKey,
      });
      api.trackProductEvent("relationship_step_completed", {
        action: "task_submitted",
        stage: "exploration",
        status: "success",
        source: "task_form",
      }).catch(() => {});
      wx.removeStorageSync(this.draftKey);
      this.updateUnloadGuard(false);
      this.submissionKey = createIdempotencyKey("relationship-task");
      this.setData({ saving: false, saveStatus: "已提交", hasLocalDraft: false, draftRestored: false });
      if (saved && (saved.risk_level === "medium" || saved.risk_level === "high")) {
        wx.showModal({
          title: "已转交人工关注",
          content: "这份内容不会生成普通自动解释。若你或他人正面临现实安全风险，请优先联系可信的人或当地紧急支持。",
          showCancel: false,
          confirmText: "我知道了",
          success: () => wx.navigateBack(),
        });
        return;
      }
      wx.showToast({ title: "已保存", icon: "success" });
      setTimeout(() => wx.navigateBack(), 500);
    } catch (error) {
      api.trackProductEvent("relationship_task_save_failed", {
        action: "task_submit",
        stage: "exploration",
        status: "failed",
        retryable: Boolean(error && error.retryable),
        source: "task_form",
      }).catch(() => {});
      this.setData({ saving: false, saveStatus: "提交未完成，草稿已保存在本机" });
      this.persistDraftNow();
      wx.showToast({ title: error.message || "暂时没能提交，草稿还在", icon: "none" });
      return;
    }
    this.setData({ saving: false });
  },
});

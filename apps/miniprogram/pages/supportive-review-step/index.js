const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");
const {
  FLOW_STEPS,
  STEP_TITLES,
  backToHub,
  formatDay,
  nextStepAfter,
  progressFor,
  stepUrl,
} = require("../../utils/supportiveReview");

const api = createSafeHomeApi();
const OPTIONAL_STEPS = ["guess", "episode", "exceptions", "scales", "inquiry"];
const RECENT_DAYS = 30;
const SECTION_BY_STEP = { followup: "followup" };

function localDay(timestamp) {
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return "";
  const pad = (value) => String(value).padStart(2, "0");
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}`;
}

function textOf(value) {
  return typeof value === "string" ? value : "";
}

function initialValues(step, review, fields) {
  const source = !review ? {} : {
    question: { question: review.question, question_history: review.question_history },
    guess: { guess: review.guess, hoped_change: review.hoped_change },
    episode: review.episode || {},
    exceptions: review.exceptions || {},
    experiment: review.experiment || {},
    followup: review.followup || {},
  }[step] || {};
  return fields.reduce((values, field) => ({
    ...values,
    [field.key]: textOf(source[field.key]) || (step === "experiment" ? textOf(field.defaultValue) : ""),
  }), {});
}

Page({
  data: {
    step: "question",
    stepTitle: "",
    prompt: "",
    note: "",
    progress: [],
    stepNumber: 1,
    stepTotal: FLOW_STEPS.length,
    loading: true,
    saving: false,
    loadError: "",
    errorMessage: "",
    saveStatus: "",
    reviewId: "",
    review: null,
    risk: null,
    fields: [],
    values: {},
    topics: [],
    topicId: "",
    topicExamples: [],
    starters: [],
    rewrites: [],
    rewritesOpen: false,
    intensityItems: [],
    intensity: null,
    intensityMinLabel: "",
    intensityMaxLabel: "",
    scaleRows: [],
    scaleEmpty: false,
    selectedResultIds: [],
    maxResults: 3,
    inquiryRows: [],
    cardOptions: [],
    cardId: "",
    plannedDate: "",
    todayDate: "",
    questionNowOptions: [],
    nextOptions: [],
    questionNow: "",
    nextChoice: "",
    stepDone: false,
    canSkip: false,
    primaryLabel: "保存并继续",
  },

  onLoad(options = {}) {
    const step = String(options.step || "question");
    const reviewId = decodeURIComponent(options.id || "");
    this.setData({
      step,
      reviewId,
      stepTitle: STEP_TITLES[step] || "自助整理",
      progress: progressFor(step),
      stepNumber: Math.max(1, FLOW_STEPS.indexOf(step) + 1),
      todayDate: localDay(Date.now()),
      primaryLabel: step === "experiment" ? "记下这个实验" : step === "followup" ? "保存回看" : "保存并继续",
    });
    if (!requireLogin({ redirectUrl: stepUrl(reviewId, step), message: "请先登录后再开始自助整理。" })) {
      this.setData({ loading: false, loadError: "需要先登录。" });
      return;
    }
    this.draftController = createResilientForm({
      storageKey: `safehome:resilientDraft:supportive:${reviewId || "new"}:${step}`,
      fields: ["values", "topicId", "intensity", "selectedResultIds", "inquiryRows", "cardId", "plannedDate", "questionNow", "nextChoice"],
      submissionPrefix: "supportive-review",
      hasContent: (values) => Object.keys(values.values || {}).some((key) => String(values.values[key] || "").trim())
        || (values.inquiryRows || []).some((row) => String(row.stood_out || row.fit || "").trim()),
    });
    this.load();
  },

  onShow() {
    if (this.loadedOnce && this.data.step === "scales" && !this.data.loading) this.loadScales();
  },

  onHide() {
    this.flushDraft();
  },

  onUnload() {
    this.flushDraft();
  },

  flushDraft() {
    if (!this.draftController || this.data.saving || this.data.loading) return;
    const status = this.draftController.flush(this.data);
    if (status.savedAt) this.setData({ saveStatus: status.saveStatus });
  },

  scheduleDraft() {
    if (!this.draftController) return;
    this.draftController.schedule(this.data, (status) => this.setData({ saveStatus: status.saveStatus }));
  },

  async load() {
    const { step, reviewId } = this.data;
    this.setData({ loading: true, loadError: "", errorMessage: "" });
    try {
      const [guide, review] = await Promise.all([
        api.getSupportiveReviewGuide(),
        reviewId ? api.getSupportiveReview(reviewId) : Promise.resolve(null),
      ]);
      if (!review && step !== "question") throw new Error("没有找到这次整理，请回到目录重新开始。");
      this.guide = guide;
      const config = (guide.steps || []).find((item) => item.id === step) || {};
      const fields = (config.fields || []).map((field) => ({
        key: field.key,
        label: field.label,
        placeholder: field.placeholder || "",
        maxLength: field.max_length || 300,
        required: Boolean(field.required),
        defaultValue: field.default || "",
      }));
      const stepDone = Boolean(review && (review.steps_done || []).includes(step));
      this.setData({
        review,
        risk: review ? review.risk : null,
        prompt: config.prompt || "",
        note: config.note || "",
        fields,
        values: initialValues(step, review, fields),
        stepDone,
        maxResults: config.max_results || 3,
      });
      this.setupStep(guide, config, review);
      if (step === "scales") await this.loadScales();
      this.restoreDraft();
      this.refreshSkip();
      this.loadedOnce = true;
    } catch (error) {
      this.setData({ loadError: error.message || "请检查网络后再试。" });
    } finally {
      this.setData({ loading: false });
    }
  },

  setupStep(guide, config, review) {
    const step = this.data.step;
    if (step === "question") {
      const topicId = review ? review.topic_id : "";
      const topics = guide.topics || [];
      const topic = topics.find((item) => item.id === topicId);
      this.setData({
        topics,
        topicId,
        topicExamples: topic ? topic.examples || [] : [],
        starters: (guide.question_guide || {}).starters || [],
        rewrites: (guide.question_guide || {}).rewrites || [],
      });
    }
    if (step === "episode") {
      const scale = config.intensity || {};
      const intensity = review && review.episode && typeof review.episode.intensity === "number" ? review.episode.intensity : null;
      this.setData({
        intensity,
        intensityMinLabel: scale.min_label || "",
        intensityMaxLabel: scale.max_label || "",
        intensityItems: this.intensityItems(intensity),
      });
    }
    if (step === "inquiry") {
      const inquiry = (review && review.inquiry) || {};
      this.setData({
        inquiryRows: ((review && review.linked_results) || []).map((result) => ({
          resultId: result.id,
          title: result.worksheet_title || "问卷",
          day: formatDay(result.created_on),
          stood_out: textOf((inquiry[result.id] || {}).stood_out),
          fit: textOf((inquiry[result.id] || {}).fit),
        })),
      });
    }
    if (step === "experiment") {
      const experiment = (review && review.experiment) || {};
      this.setData({
        cardOptions: ((review && review.card_options) || []).map((card) => ({
          ...card,
          durationText: card.duration_minutes ? `约 ${card.duration_minutes} 分钟` : "",
        })),
        cardId: experiment.card_id || "",
        plannedDate: experiment.planned_date || "",
      });
    }
    if (step === "followup") {
      const choices = config.choices || {};
      const followup = (review && review.followup) || {};
      this.setData({
        questionNowOptions: choices.question_now || [],
        nextOptions: choices.next || [],
        questionNow: followup.question_now || "",
        nextChoice: followup.next || "",
        note: review && review.experiment && review.experiment.own_idea ? `你的实验：${review.experiment.own_idea}` : this.data.note,
      });
    }
  },

  restoreDraft() {
    const local = this.draftController && this.draftController.restore();
    if (!local) return;
    const values = local.values || {};
    const patch = { saveStatus: "已恢复本机草稿" };
    if (values.values) patch.values = { ...this.data.values, ...values.values };
    if (this.data.step === "question" && values.topicId) {
      const topic = (this.data.topics || []).find((item) => item.id === values.topicId);
      patch.topicId = values.topicId;
      patch.topicExamples = topic ? topic.examples || [] : [];
    }
    if (this.data.step === "episode" && values.intensity !== undefined) {
      patch.intensity = values.intensity;
      patch.intensityItems = this.intensityItems(values.intensity);
    }
    if (this.data.step === "inquiry" && Array.isArray(values.inquiryRows)) {
      const saved = new Map(values.inquiryRows.map((row) => [row.resultId, row]));
      patch.inquiryRows = this.data.inquiryRows.map((row) => ({ ...row, ...(saved.get(row.resultId) || {}) }));
    }
    if (this.data.step === "experiment") {
      if (values.cardId !== undefined) patch.cardId = values.cardId;
      if (values.plannedDate !== undefined) patch.plannedDate = values.plannedDate;
    }
    if (this.data.step === "followup") {
      if (values.questionNow) patch.questionNow = values.questionNow;
      if (values.nextChoice) patch.nextChoice = values.nextChoice;
    }
    this.setData(patch);
  },

  hasTypedContent() {
    const values = this.data.values || {};
    return Object.keys(values).some((key) => String(values[key] || "").trim())
      || (this.data.inquiryRows || []).some((row) => String(row.stood_out || row.fit || "").trim())
      || (this.data.step === "episode" && this.data.intensity !== null)
      || (this.data.step === "scales" && this.data.selectedResultIds.length > 0);
  },

  refreshSkip() {
    const canSkip = OPTIONAL_STEPS.includes(this.data.step) && !this.data.stepDone && !this.hasTypedContent();
    this.setData({ canSkip });
  },

  intensityItems(selected) {
    return Array.from({ length: 11 }, (_, value) => ({ value, selected: value === selected }));
  },

  async loadScales() {
    const review = this.data.review;
    const topic = ((this.guide && this.guide.topics) || []).find((item) => item.id === (review && review.topic_id));
    try {
      const [catalog, results] = await Promise.all([
        api.listAssessments(),
        api.listAssessmentResults({ page_size: 50 }),
      ]);
      const available = new Map((catalog.items || []).map((item) => [item.id, item]));
      const order = topic ? topic.worksheet_ids || [] : [];
      const recommended = order.filter((id) => available.has(id));
      const fallback = recommended.length ? [] : Array.from(available.keys()).slice(0, 6);
      const cutoff = Date.now() - RECENT_DAYS * 24 * 60 * 60 * 1000;
      const latest = {};
      (results.items || []).forEach((item) => {
        const createdAt = Date.parse(item.created_at);
        if (Number.isNaN(createdAt) || createdAt < cutoff || latest[item.worksheet_id]) return;
        latest[item.worksheet_id] = item;
      });
      const linked = ((review && review.linked_results) || []).map((item) => item.id);
      let selected = this.data.selectedResultIds.length ? this.data.selectedResultIds : linked;
      const startedOn = review ? review.created_on : "";
      const worksheetIds = recommended.concat(fallback);
      ((review && review.linked_results) || []).forEach((item) => {
        if (!worksheetIds.includes(item.worksheet_id)) worksheetIds.push(item.worksheet_id);
      });
      const rows = worksheetIds.map((worksheetId) => {
        const worksheet = available.get(worksheetId) || {};
        const linkedResult = ((review && review.linked_results) || []).find((item) => item.worksheet_id === worksheetId);
        const result = latest[worksheetId] || (linkedResult ? { id: linkedResult.id, created_at: linkedResult.created_on } : null);
        return {
          worksheetId,
          title: worksheet.display_title || (linkedResult && linkedResult.worksheet_title) || "问卷",
          questionCount: worksheet.question_count || 0,
          available: available.has(worksheetId),
          resultId: result ? result.id : "",
          resultDay: result ? formatDay(localDay(result.created_at) || result.created_at) : "",
          fresh: Boolean(result && startedOn && localDay(result.created_at) >= startedOn),
        };
      });
      if (!this.data.selectedResultIds.length && !linked.length) {
        selected = rows.filter((row) => row.fresh && row.resultId).map((row) => row.resultId).slice(0, this.data.maxResults);
      }
      this.setData({
        scaleRows: rows.map((row) => ({ ...row, selected: selected.includes(row.resultId) })),
        selectedResultIds: selected,
        scaleEmpty: rows.length === 0,
      });
      this.refreshSkip();
    } catch (error) {
      this.setData({ errorMessage: error.message || "问卷列表暂时没有读取成功。" });
    }
  },

  onFieldInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [`values.${key}`]: event.detail.value, errorMessage: "" });
    this.refreshSkip();
    this.scheduleDraft();
  },

  onTopicTap(event) {
    const id = event.currentTarget.dataset.id;
    const topicId = this.data.topicId === id ? "" : id;
    const topic = this.data.topics.find((item) => item.id === topicId);
    this.setData({ topicId, topicExamples: topic ? topic.examples || [] : [] });
    this.scheduleDraft();
  },

  useExample(event) {
    if (String(this.data.values.question || "").trim()) {
      wx.showToast({ title: "已有内容，可直接修改", icon: "none" });
      return;
    }
    this.setData({ "values.question": event.currentTarget.dataset.text });
    this.scheduleDraft();
  },

  toggleRewrites() {
    this.setData({ rewritesOpen: !this.data.rewritesOpen });
  },

  onIntensityTap(event) {
    const value = Number(event.currentTarget.dataset.value);
    const intensity = this.data.intensity === value ? null : value;
    this.setData({ intensity, intensityItems: this.intensityItems(intensity) });
    this.refreshSkip();
    this.scheduleDraft();
  },

  onScaleTap(event) {
    const row = this.data.scaleRows[Number(event.currentTarget.dataset.index)];
    if (!row || !row.resultId) return;
    let selected = this.data.selectedResultIds.slice();
    if (selected.includes(row.resultId)) {
      selected = selected.filter((id) => id !== row.resultId);
    } else if (selected.length >= this.data.maxResults) {
      this.setData({ errorMessage: `最多加入 ${this.data.maxResults} 份问卷结果。` });
      return;
    } else {
      selected.push(row.resultId);
    }
    this.setData({
      selectedResultIds: selected,
      scaleRows: this.data.scaleRows.map((item) => ({ ...item, selected: selected.includes(item.resultId) })),
      errorMessage: "",
    });
    this.refreshSkip();
    this.scheduleDraft();
  },

  openAssessment(event) {
    const id = event.currentTarget.dataset.id;
    this.flushDraft();
    wx.navigateTo({ url: `/pages/assessment-detail/index?id=${encodeURIComponent(id)}` });
  },

  onInquiryInput(event) {
    const { index, key } = event.currentTarget.dataset;
    this.setData({ [`inquiryRows[${index}].${key}`]: event.detail.value, errorMessage: "" });
    this.refreshSkip();
    this.scheduleDraft();
  },

  onCardTap(event) {
    const id = event.currentTarget.dataset.id;
    this.setData({ cardId: this.data.cardId === id ? "" : id });
    this.scheduleDraft();
  },

  onDateChange(event) {
    this.setData({ plannedDate: event.detail.value });
    this.scheduleDraft();
  },

  clearDate() {
    this.setData({ plannedDate: "" });
    this.scheduleDraft();
  },

  onChoiceTap(event) {
    const { group, value } = event.currentTarget.dataset;
    this.setData({ [group]: value, errorMessage: "" });
    this.scheduleDraft();
  },

  openEmergencyResources() {
    wx.navigateTo({ url: "/pages/emergency-resources/index" });
  },

  goHub() {
    backToHub();
  },

  validate() {
    const { step, values } = this.data;
    const missing = this.data.fields.find((field) => field.required && !String(values[field.key] || "").trim());
    if (missing) return `请先填写“${missing.label}”。`;
    if (step === "followup" && (!this.data.questionNow || !this.data.nextChoice)) return "请先选择问题现在的情况和接下来的打算。";
    return "";
  },

  sectionPayload(empty = false) {
    const { step, values } = this.data;
    const text = (key) => (empty ? "" : String(values[key] || "").trim());
    if (step === "question") return { question: text("question"), question_history: text("question_history"), topic_id: this.data.topicId };
    if (step === "guess") return { guess: text("guess"), hoped_change: text("hoped_change") };
    if (step === "episode") {
      return {
        situation: text("situation"),
        body_feeling: text("body_feeling"),
        thought: text("thought"),
        action: text("action"),
        after: text("after"),
        intensity: empty ? null : this.data.intensity,
      };
    }
    if (step === "exceptions") return { exception: text("exception"), resources: text("resources") };
    if (step === "scales") return { result_ids: empty ? [] : this.data.selectedResultIds };
    if (step === "inquiry") {
      const entries = {};
      if (!empty) {
        this.data.inquiryRows.forEach((row) => {
          entries[row.resultId] = { stood_out: String(row.stood_out || "").trim(), fit: String(row.fit || "").trim() };
        });
      }
      return { entries };
    }
    if (step === "experiment") {
      return {
        own_idea: text("own_idea"),
        obstacle: text("obstacle"),
        plan_b: text("plan_b"),
        stop_condition: text("stop_condition"),
        card_id: this.data.cardId,
        planned_date: this.data.plannedDate,
      };
    }
    return {
      question_now: this.data.questionNow,
      next: this.data.nextChoice,
      noticed: text("noticed"),
      learned: text("learned"),
    };
  },

  async submit(empty) {
    const { step, reviewId } = this.data;
    this.setData({ saving: true, errorMessage: "" });
    try {
      let review;
      if (step === "question" && !reviewId) {
        review = await api.createSupportiveReview(this.sectionPayload(false), this.draftController.getSubmissionId());
      } else {
        review = await api.updateSupportiveReview(reviewId, {
          section: SECTION_BY_STEP[step] || step,
          data: this.sectionPayload(empty),
          expected_version: this.data.review.version,
        });
      }
      this.draftController.clear();
      this.afterSave(review);
    } catch (error) {
      if (error.code === "version_conflict") {
        this.setData({ errorMessage: "这次整理在别处更新过，已为你重新读取，请再保存一次。" });
        this.load();
        return;
      }
      this.setData({ errorMessage: error.message || "暂时没有保存成功，内容还在，请稍后再试。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  afterSave(review) {
    const step = this.data.step;
    if (review.risk && review.risk.level === "high") {
      wx.redirectTo({ url: stepUrl(review.id, "letter") });
      return;
    }
    if (step === "experiment" || step === "followup") {
      wx.showToast({ title: step === "experiment" ? "已记下实验" : "回看已保存", icon: "success" });
      setTimeout(() => backToHub(), 600);
      return;
    }
    const next = nextStepAfter(step, review);
    wx.redirectTo({ url: stepUrl(review.id, next || "letter") });
  },

  onSave() {
    const message = this.validate();
    if (message) {
      this.setData({ errorMessage: message });
      return;
    }
    this.submit(false);
  },

  onSkip() {
    if (!this.data.canSkip) return;
    this.submit(true);
  },
});

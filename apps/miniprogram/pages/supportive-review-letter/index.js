const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");
const { backToHub, stepUrl } = require("../../utils/supportiveReview");

const api = createSafeHomeApi();
const RESPONDABLE = { clue: true, prompt: true };

function decorate(sections, checks) {
  return (sections || []).map((section) => ({
    ...section,
    items: (section.items || []).map((item) => {
      const saved = checks[item.id] || {};
      return {
        ...item,
        respondable: Boolean(RESPONDABLE[item.kind] && (item.kind !== "clue" || item.checkable)),
        fit: saved.fit || "",
        note: saved.note || "",
        noteOpen: Boolean(saved.note),
      };
    }),
  }));
}

Page({
  data: {
    loading: true,
    loadError: "",
    saving: false,
    errorMessage: "",
    saveStatus: "",
    reviewId: "",
    review: null,
    letter: null,
    sections: [],
    checkOptions: [],
    anglesOpen: false,
    safetyOnly: false,
    risk: null,
    draftChecks: {},
    primaryLabel: "保存，选一个小实验",
  },

  onLoad(options = {}) {
    const reviewId = decodeURIComponent(options.id || "");
    this.setData({ reviewId });
    if (!requireLogin({ redirectUrl: stepUrl(reviewId, "letter"), message: "请先登录后再查看回看信。" })) {
      this.setData({ loading: false, loadError: "需要先登录。" });
      return;
    }
    this.draftController = createResilientForm({
      storageKey: `safehome:resilientDraft:supportive:${reviewId}:letter`,
      fields: ["draftChecks"],
      submissionPrefix: "supportive-letter",
      hasContent: (values) => Object.keys(values.draftChecks || {}).length > 0,
    });
    this.load();
  },

  onHide() {
    this.flushDraft();
  },

  onUnload() {
    this.flushDraft();
  },

  flushDraft() {
    if (this.draftController && !this.data.saving && !this.data.loading) this.draftController.flush(this.data);
  },

  async load() {
    this.setData({ loading: true, loadError: "", errorMessage: "" });
    try {
      const review = await api.getSupportiveReview(this.data.reviewId);
      const letter = review.letter || {};
      let checks = review.letter_checks || {};
      const local = this.draftController && this.draftController.restore();
      if (local && local.values && local.values.draftChecks) {
        checks = { ...checks, ...local.values.draftChecks };
      }
      const hasExperiment = Boolean(review.experiment && review.experiment.own_idea);
      this.setData({
        review,
        letter,
        risk: review.risk,
        safetyOnly: Boolean(letter.safety_only),
        checkOptions: letter.check_options || [],
        sections: decorate(letter.sections, checks),
        draftChecks: local && local.values ? local.values.draftChecks || {} : {},
        saveStatus: local ? "已恢复本机草稿" : "",
        primaryLabel: hasExperiment ? "保存我的核对" : "保存，选一个小实验",
      });
    } catch (error) {
      this.setData({ loadError: error.message || "请检查网络后再试。" });
    } finally {
      this.setData({ loading: false });
    }
  },

  remember(sectionIndex, itemIndex) {
    const item = this.data.sections[sectionIndex].items[itemIndex];
    const draftChecks = { ...this.data.draftChecks, [item.id]: { fit: item.fit, note: item.note } };
    this.setData({ draftChecks });
    this.draftController.schedule(this.data, (status) => this.setData({ saveStatus: status.saveStatus }));
  },

  onFit(event) {
    const { section, item, value } = event.currentTarget.dataset;
    const current = this.data.sections[section].items[item].fit;
    this.setData({ [`sections[${section}].items[${item}].fit`]: current === value ? "" : value, errorMessage: "" });
    this.remember(section, item);
  },

  openNote(event) {
    const { section, item } = event.currentTarget.dataset;
    this.setData({ [`sections[${section}].items[${item}].noteOpen`]: true });
  },

  onNoteInput(event) {
    const { section, item } = event.currentTarget.dataset;
    this.setData({ [`sections[${section}].items[${item}].note`]: event.detail.value });
    this.remember(section, item);
  },

  toggleAngles() {
    this.setData({ anglesOpen: !this.data.anglesOpen });
  },

  collectChecks() {
    const checks = {};
    this.data.sections.forEach((section) => {
      section.items.forEach((item) => {
        if (!item.respondable) return;
        const note = String(item.note || "").trim();
        if (item.fit || note) checks[item.id] = item.kind === "clue" ? { fit: item.fit, note } : { note };
      });
    });
    return checks;
  },

  async onSave() {
    const review = this.data.review;
    if (!review) return;
    this.setData({ saving: true, errorMessage: "" });
    try {
      const updated = await api.updateSupportiveReview(review.id, {
        section: "letter_checks",
        data: { checks: this.collectChecks() },
        expected_version: review.version,
      });
      this.draftController.clear();
      if (updated.experiment && updated.experiment.own_idea) {
        wx.showToast({ title: "已保存", icon: "success" });
        setTimeout(() => backToHub(), 600);
        return;
      }
      wx.redirectTo({ url: stepUrl(updated.id, "experiment") });
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

  openEmergencyResources() {
    wx.navigateTo({ url: "/pages/emergency-resources/index" });
  },

  goHub() {
    this.flushDraft();
    backToHub();
  },
});

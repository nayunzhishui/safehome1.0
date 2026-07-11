const { createSafeHomeApi } = require("../../services/api");
const { isLoggedIn, requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

function formatCourse(course) {
  return {
    ...course,
    durationText: course.duration_minutes ? `${course.duration_minutes} 分钟` : "一小节",
    relationText: (course.relation_to_cards_or_programs || []).join("、"),
    knowledgeChecks: (course.knowledge_checks || []).map((check) => ({ ...check, selectedValue: "", feedback: "" })),
    boosterText: course.booster_plan ? `${course.booster_plan.review_after_days} 天后：${course.booster_plan.prompt}` : "",
  };
}

Page({
  data: {
    courseId: "",
    course: null,
    loading: true,
    errorMessage: "",
    progressMessage: "",
    savingProgress: false,
  },

  onLoad(options) {
    const courseId = decodeURIComponent(options.id || "");
    this.setData({ courseId });
    this.loadCourse(courseId);
  },

  async loadCourse(courseId) {
    if (!courseId) {
      this.setData({ loading: false, errorMessage: "缺少课程 ID。" });
      return;
    }
    this.setData({ loading: true, errorMessage: "" });
    try {
      const payload = await api.getCourse(courseId);
      this.setData({
        course: formatCourse(payload.course || {}),
        loading: false,
      }, () => {
        if (isLoggedIn()) this.loadProgress();
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "课程详情暂时没能加载，请稍后再试。",
      });
    }
  },

  retryLoadCourse() {
    this.loadCourse(this.data.courseId);
  },

  chooseKnowledgeAnswer(event) {
    const checkId = event.currentTarget.dataset.checkId || "";
    const value = event.currentTarget.dataset.value || "";
    const course = this.data.course;
    if (!course || !checkId) return;
    const knowledgeChecks = (course.knowledgeChecks || []).map((check) => {
      if (check.id !== checkId) return check;
      const correct = value === check.correct_value;
      return {
        ...check,
        selectedValue: value,
        feedback: correct ? check.feedback_correct : check.feedback_incorrect,
      };
    });
    this.setData({ "course.knowledgeChecks": knowledgeChecks });
  },

  async loadProgress() {
    try {
      const payload = await api.getCourseProgress(this.data.courseId);
      const progress = payload.progress;
      if (progress) {
        this.setData({ progressMessage: progress.status === "completed" ? "这门课已记录完成，可以按巩固提示继续回看。" : "已恢复上次课程进度。" });
      }
    } catch (_error) {
      this.setData({ progressMessage: "课程内容可继续阅读，进度暂时没有同步。" });
    }
  },

  async markCourseComplete() {
    if (!requireLogin({ redirectUrl: `/pages/course-detail/index?id=${encodeURIComponent(this.data.courseId)}`, message: "请先登录后再保存课程进度。" })) return;
    const course = this.data.course;
    if (!course) return;
    const attemptedCheckIds = (course.knowledgeChecks || []).filter((item) => item.selectedValue).map((item) => item.id);
    if (attemptedCheckIds.length < (course.knowledgeChecks || []).length) {
      this.setData({ progressMessage: "请先完成理解检查，再记录课程完成。" });
      return;
    }
    this.setData({ savingProgress: true, progressMessage: "" });
    try {
      await api.saveCourseProgress(this.data.courseId, {
        status: "completed",
        completed_section_count: (course.sections || []).length,
        knowledge_check_completed_ids: attemptedCheckIds,
        transfer_task_status: "planned",
        linked_card_id: course.guided_practice && course.guided_practice.card_id,
      });
      this.setData({ progressMessage: "已记录课程完成。完成只表示学过并尝试，不代表心理状态评价。" });
    } catch (error) {
      this.setData({ progressMessage: error.message || "课程进度暂时没有保存，请稍后重试。" });
    } finally {
      this.setData({ savingProgress: false });
    }
  },

  goTraining() {
    wx.switchTab({ url: "/pages/training/index" });
  },
});

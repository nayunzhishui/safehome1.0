const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function formatCourse(course) {
  return {
    ...course,
    durationText: course.duration_minutes ? `${course.duration_minutes} 分钟` : "一小节",
    relationText: (course.relation_to_cards_or_programs || []).join("、"),
  };
}

Page({
  data: {
    courseId: "",
    course: null,
    loading: true,
    errorMessage: "",
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

  goTraining() {
    wx.switchTab({ url: "/pages/training/index" });
  },
});

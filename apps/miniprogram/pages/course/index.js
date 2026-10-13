const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function sizeText(course) {
  const parts = [`${course.lessonCount} 小节`];
  if (course.duration_minutes) parts.push(`约 ${course.duration_minutes} 分钟`);
  return parts.join(" · ");
}

function formatCourse(course) {
  const formatted = {
    ...course,
    category: course.theme || "陪伴练习",
    scene: course.scene || "选一小节慢慢看。",
    lessonCount: course.section_count || 1,
  };
  formatted.sizeText = sizeText(formatted);
  formatted.metaText = `${formatted.category} · ${formatted.sizeText}`;
  return formatted;
}

Page({
  data: {
    activeCategory: "全部",
    categories: ["全部"],
    courses: [],
    focusCourse: null,
    otherCourses: [],
    loading: true,
    errorMessage: "",
    boundaryNotice: "",
  },

  onLoad() {
    this.loadCourses();
  },

  async loadCourses() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const payload = await api.listCourses();
      const courses = (payload.items || []).map(formatCourse);
      const themes = Array.from(new Set(courses.map((item) => item.category).filter(Boolean)));
      const activeCategory = themes.includes(this.data.activeCategory) ? this.data.activeCategory : "全部";
      this.setData({
        courses,
        categories: ["全部"].concat(themes),
        boundaryNotice: payload.boundary_notice || "",
        loading: false,
      });
      this.filterCourses(activeCategory);
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "课程内容暂时没能加载，请检查网络后再试一次。",
      });
    }
  },

  selectCategory(event) {
    const category = event.currentTarget.dataset.category || "全部";
    this.filterCourses(category);
  },

  // “从这一节开始”取当前主题的第一门，其余排在下面的课程行里。
  filterCourses(category) {
    const visibleCourses = category === "全部"
      ? this.data.courses
      : this.data.courses.filter((course) => course.category === category);
    this.setData({
      activeCategory: category,
      focusCourse: visibleCourses[0] || null,
      otherCourses: visibleCourses.slice(1),
    });
  },

  openCourse(event) {
    const courseId = (event.detail && event.detail.id) || event.currentTarget.dataset.id;
    if (!courseId) {
      wx.showToast({ title: "课程信息暂时不完整", icon: "none" });
      return;
    }
    wx.navigateTo({
      url: `/pages/course-detail/index?id=${encodeURIComponent(courseId)}`,
    });
  },

  retryLoadCourses() {
    this.loadCourses();
  },
});

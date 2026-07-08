const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function formatCourse(course) {
  return {
    ...course,
    category: course.theme || "陪伴练习",
    description: course.scene || "选一小节慢慢看。",
    lessonCount: course.section_count || 1,
    progress: 0,
  };
}

Page({
  data: {
    activeCategory: "全部",
    categories: ["全部"],
    weeklyProgress: {
      learnedLessons: 0,
      suggestion: "本周可以先看一节内容，再配合一张训练卡做一次小练习。",
    },
    courses: [],
    visibleCourses: [],
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
      this.setData({
        courses,
        categories: ["全部"].concat(themes),
        boundaryNotice: payload.boundary_notice || "",
        loading: false,
      });
      this.filterCourses(this.data.activeCategory);
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

  filterCourses(category) {
    const visibleCourses = category === "全部"
      ? this.data.courses
      : this.data.courses.filter((course) => course.category === category);
    this.setData({
      activeCategory: category,
      visibleCourses,
    });
  },

  openCourse(event) {
    const courseId = event.detail && event.detail.id;
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

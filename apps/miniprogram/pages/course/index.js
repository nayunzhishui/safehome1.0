Page({
  data: {
    activeCategory: "全部",
    categories: ["全部", "情绪管理", "亲子沟通", "家庭关系", "压力应对", "青春期陪伴"],
    weeklyProgress: {
      learnedLessons: 3,
      suggestion: "本周可以继续学习一节亲子沟通课程，并配合一次 UP 训练。",
    },
    courses: [
      {
        title: "理解孩子的情绪",
        description: "学会看见孩子行为背后的情绪需求。",
        category: "情绪管理",
        lessonCount: 12,
        progress: 30,
      },
      {
        title: "家长情绪调节入门",
        description: "先稳定自己，才能更稳地回应孩子。",
        category: "情绪管理",
        lessonCount: 10,
        progress: 60,
      },
      {
        title: "非评判陪伴方法",
        description: "练习先接住情绪，再讨论具体问题。",
        category: "亲子沟通",
        lessonCount: 8,
        progress: 20,
      },
      {
        title: "冲突后的关系修复",
        description: "在争吵后重新建立一点连接和安全感。",
        category: "家庭关系",
        lessonCount: 9,
        progress: 0,
      },
      {
        title: "考试压力下的亲子沟通",
        description: "在成绩和升学压力下减少指责与对抗。",
        category: "压力应对",
        lessonCount: 7,
        progress: 60,
      },
    ],
    visibleCourses: [],
  },

  onLoad() {
    this.filterCourses("全部");
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

  openCourse() {
    wx.showToast({
      title: "课程详情后续接入",
      icon: "none",
    });
  },
});

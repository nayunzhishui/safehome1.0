Component({
  properties: {
    courseId: {
      type: String,
      value: "",
    },
    title: {
      type: String,
      value: "",
    },
    description: {
      type: String,
      value: "",
    },
    category: {
      type: String,
      value: "",
    },
    lessonCount: {
      type: Number,
      value: 0,
    },
    progress: {
      type: Number,
      value: 0,
    },
    buttonText: {
      type: String,
      value: "开始学习",
    },
  },
  methods: {
    handleTap() {
      this.triggerEvent("tapcard", { id: this.properties.courseId });
    },
  },
});

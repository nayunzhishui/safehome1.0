const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    status: "idle",
    message: "请先启动 backend，再点击按钮进行最小联调。",
    diary: null,
    feedback: null,
    cards: [],
  },

  async runSmokeTest() {
    this.setData({
      status: "running",
      message: "正在创建情绪事件记录...",
      diary: null,
      feedback: null,
      cards: [],
    });

    try {
      const diary = await api.createDiary({
        scene: "作业拖延",
        event_description: "孩子一直不开始写作业，我忍不住催了很多次。",
        parent_emotion: "着急",
        parent_emotion_intensity: 8,
        automatic_thought: "他就是故意拖。",
        behavior: "反复催促。",
      });

      this.setData({
        message: "正在生成即时反馈...",
        diary,
      });

      const feedback = await api.generateFeedback({ diary_id: diary.id });

      this.setData({
        message: "正在获取训练卡推荐...",
        feedback,
      });

      const cardsResult = await api.recommendCards({ tags: feedback.tags });

      this.setData({
        status: "success",
        message: "联调通过：已完成记录、反馈、训练卡推荐三步。",
        cards: cardsResult.items || [],
      });
    } catch (error) {
      this.setData({
        status: "error",
        message: error.message || "联调失败，请确认 backend 是否已启动。",
      });
    }
  },
});

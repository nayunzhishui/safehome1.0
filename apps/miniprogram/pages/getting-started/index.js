Page({
  data: {
    steps: [
      {
        title: "1. 记录一个具体事件",
        text: "先写清楚发生了什么、当时自己和孩子可能有哪些情绪，以及自己做了什么回应。",
      },
      {
        title: "2. 查看支持性反馈",
        text: "系统只做非诊断、非评判的线索提示，帮助你看见情绪、想法、身体反应和行为之间的连接。",
      },
      {
        title: "3. 选择一个小练习",
        text: "从推荐训练卡里选一个今天能完成的小动作，练完后打卡，方便后续复盘。",
      },
    ],
    boundaries: [
      "这里不会给孩子或家长下诊断结论。",
      "高风险内容需要优先寻求人工支持或专业帮助。",
      "每次只完成一个小步骤，也算是在练习陪伴能力。",
    ],
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openTraining() {
    wx.switchTab({ url: "/pages/training/index" });
  },
});

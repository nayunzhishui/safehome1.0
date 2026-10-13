// 三步开始（Figma 645:910）：只做导航说明，不读写存储、不提交同意记录。
// 七个位置七节竹，越往后颜色越深。
const ARC_LABELS = [
  "诱因／应激源",
  "反应（想法·身体感觉·行为）",
  "觉察",
  "接纳",
  "转化",
  "应对（适应性策略与行为）",
  "结果（适应与发展）",
];

Page({
  data: {
    arcNodes: ARC_LABELS.map((label, index) => ({ label, opacity: (0.35 + index * 0.1).toFixed(2) })),
    eventReasons: [
      "具体事件更容易看清当时发生了什么，而不是把一天都归成“很糟”。",
      "记录具体场景后，反馈才能只围绕这次互动，不评价家长或孩子。",
      "越具体，越容易找到下一次可以轻轻调整的一小步。",
    ],
    exerciseSteps: [
      {
        kicker: "01 · 写一个片段",
        title: "谁在场、发生了什么、我的反应",
        text: "只写刚才发生的一小段：谁在场、发生了什么、自己最明显的反应是什么。表单里只有“发生了什么”必须写，其他可以先空着；第一次记录需要先登录，并确认这项功能的数据用途。",
      },
      {
        kicker: "02 · 标一个位置",
        title: "在反射弧里找最容易先调整的一处",
        text: "看完反馈，在反射弧里标出最容易先调整的位置，例如暂停 3 秒、换一句说法或先命名情绪。",
      },
      {
        kicker: "03 · 做一个动作",
        title: "从训练卡里选一个今天能完成的",
        text: "完成后记录感受，方便后续复盘：记录一次 → 查看反馈线索 → 练一个小动作。训练中心里还有三个分节书写的练习项目，适合想多练几次的时候。",
      },
    ],
    boundaries: [
      "这里不会给孩子或家长下诊断结论。",
      "高风险内容需要优先寻求人工支持或专业帮助。",
      "每次只完成一个小步骤，也算是在练习陪伴能力。",
    ],
  },

  openAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openTraining() {
    wx.switchTab({ url: "/pages/training/index" });
  },
});

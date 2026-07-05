Page({
  data: {
    resources: [
      {
        title: "身边可信赖的人",
        text: "先联系能马上回应你的人，比如家人、朋友、老师或同事。",
      },
      {
        title: "当地紧急服务",
        text: "如存在即时安全风险，请拨打当地紧急电话或前往线下医疗机构。",
      },
      {
        title: "学校或社区支持",
        text: "涉及孩子安全时，可以联系学校老师、辅导员、社区或当地未成年人保护相关机构。",
      },
      {
        title: "专业心理或医疗机构",
        text: "如果风险持续存在，请尽快联系线下专业机构进行面对面评估和支持。",
      },
    ],
  },

  goGuide() {
    wx.navigateTo({ url: "/pages/emergency-guide/index" });
  },
});

const NOTICE_MAP = {
  consent: {
    kicker: "知情与边界",
    title: "先知道这个工具能做什么",
    subtitle: "使用前先确认边界，再开始记录和练习。",
    sections: [
      {
        title: "本工具的用途",
        items: [
          "帮助你记录具体情绪事件。",
          "整理互动线索，生成支持性反馈和训练建议。",
          "把测评、训练和复盘整理成阶段性观察。",
        ],
      },
      {
        title: "本工具不做什么",
        items: [
          "不做诊断、不做治疗、不处理紧急危机。",
          "不评价家长、孩子或家庭好坏。",
          "不把量表结果写成固定人格标签。",
        ],
      },
      {
        title: "高风险情况",
        items: [
          "高风险内容可能进入人工关注，但紧急情况仍应优先联系现实中的可靠人员或当地紧急资源。",
        ],
      },
    ],
  },
  privacy: {
    kicker: "隐私说明",
    title: "记录只用于复盘和必要支持",
    subtitle: "这里是小程序端精简说明，正式文本以 content/privacy.md 为准。",
    sections: [
      {
        title: "记录用途",
        items: [
          "记录会用于你的复盘、训练建议和必要的人工补充反馈。",
          "研究分析默认使用脱敏或聚合数据，不默认展示自由文本原文。",
        ],
      },
      {
        title: "账号与数据",
        items: [
          "登录后，系统优先用登录账号识别记录归属。",
          "退出登录只清除本机登录态，不等于删除服务器记录。",
        ],
      },
      {
        title: "人工补充反馈",
        items: [
          "你主动提交人工督导时，相关记录会供老师补充理解。",
          "请不要填写身份证号、详细住址、电话等不必要的个人敏感信息。",
        ],
      },
    ],
  },
  boundary: {
    kicker: "工具边界",
    title: "支持性工具，不替代现实帮助",
    subtitle: "安心陪伴只提供记录、复盘和练习建议。",
    sections: [
      {
        title: "非诊断边界",
        items: [
          "测评结果只作为自我观察和练习参考。",
          "阶段性画像只说明“当前更接近某类线索”，不是人格或疾病判断。",
        ],
      },
      {
        title: "紧急情况",
        items: [
          "如果你或孩子正在经历自伤、自杀、暴力、失控或其他安全风险，请先联系身边可信赖的人、当地紧急服务或线下专业机构。",
        ],
      },
    ],
  },
  about: {
    kicker: "关于",
    title: "安心陪伴",
    subtitle: "基于 UP 跨诊断情绪调节框架的家长非评判陪伴训练系统。",
    sections: [
      {
        title: "当前版本",
        items: [
          "当前为试点测试版，仍需人工验收量表、计分、边界文案和真机页面。",
        ],
      },
    ],
  },
};

Page({
  data: {
    notice: NOTICE_MAP.boundary,
  },

  onLoad(options = {}) {
    const type = options.type || "boundary";
    this.setData({
      notice: NOTICE_MAP[type] || NOTICE_MAP.boundary,
    });
  },

  goBack() {
    wx.navigateBack({ delta: 1 });
  },
});

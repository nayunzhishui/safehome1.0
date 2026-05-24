const topics = [
  {
    id: "exam-setback",
    title: "孩子考试失利后，家长第一句话怎么说？",
    tag: "考试压力",
    readTime: "4分钟阅读",
    summary: "成绩不理想时，第一句话常常决定后面对话能不能继续。这个案例提供一个更稳的开场方式。",
    situation: "孩子拿到不理想的成绩，家长看到后很着急，也担心孩子后面更难跟上。",
    usualResponse: "常见反应是马上分析原因、指出问题，或者把一次成绩和未来联系得很重。",
    supportiveResponse: "可以先回应孩子可能有的失落，再约定晚一点一起看下一步怎么补。",
    practiceCard: {
      title: "情绪觉察",
      subtitle: "先把感受说清楚，再进入讨论",
      tag: "新手",
      duration: "3-5 分钟",
      scenario: "考试失利、情绪低落",
      tags: "emotion_awareness,exam_stress",
    },
  },
  {
    id: "emotion-outburst",
    title: "孩子发脾气时，为什么讲道理没用？",
    tag: "情绪爆发",
    readTime: "4分钟阅读",
    summary: "孩子情绪升高时，大脑很难立刻接收道理。这个案例帮助家长先稳定现场，再慢慢进入问题讨论。",
    situation: "孩子因为作业或规则突然发脾气，家长越解释，孩子声音越大，双方都更难停下来。",
    usualResponse: "常见反应是马上讲道理、要求孩子冷静，或者用更大的声音压住现场。",
    supportiveResponse: "可以先降低语言密度，用一句情绪确认和一个短暂停顿，让双方都有一点缓冲。",
    practiceCard: {
      title: "暂停训练",
      subtitle: "在继续回应前，先给自己一个停顿",
      tag: "推荐",
      duration: "3-5 分钟",
      scenario: "情绪爆发、声音升高前",
      tags: "high_emotion_intensity,emotional_behavior",
    },
  },
  {
    id: "communication-stuck",
    title: "如何用非评判的方式陪伴孩子？",
    tag: "亲子沟通",
    readTime: "5分钟阅读",
    summary: "当孩子沉默、顶嘴或不回应时，家长可以先换一种更容易被听见的表达，而不是马上追问原因。",
    situation: "家长想了解孩子发生了什么，但孩子不愿意说。家长越追问，孩子越回避。",
    usualResponse: "常见反应是不断追问、解释自己是为孩子好，或者把沉默理解成不尊重。",
    supportiveResponse: "可以先降低问题强度，用一句观察和一个可选择的问题开始。",
    practiceCard: {
      title: "非评判陪伴",
      subtitle: "先接住情绪，再讨论问题",
      tag: "推荐",
      duration: "5-10 分钟",
      scenario: "沟通卡住、冲突后",
      tags: "judgmental_language,validation",
    },
  },
  {
    id: "repair-after-conflict",
    title: "亲子冲突后，如何重新连接？",
    tag: "关系修复",
    readTime: "5分钟阅读",
    summary: "冲突后不需要马上讲清所有道理，可以先做一个小的修复动作，让关系重新有一点空间。",
    situation: "双方都说了重话，后来家长有点后悔，但又不知道怎么重新开口。",
    usualResponse: "常见反应是装作没发生，或者再次强调自己当时为什么生气。",
    supportiveResponse: "可以先用一句简短的话承认刚才不容易，再邀请孩子晚一点继续说。",
    practiceCard: {
      title: "关系修复",
      subtitle: "冲突后重新连接",
      tag: "适合",
      duration: "5-10 分钟",
      scenario: "争吵后、冷场后",
      tags: "repair,conflict",
    },
  },
  {
    id: "homework-delay",
    title: "写作业拖延时，家长如何减少指责？",
    tag: "亲子沟通",
    readTime: "3分钟阅读",
    summary: "当孩子迟迟没有开始写作业时，家长很容易从提醒变成催促。这个案例帮助你先看见情绪，再选择一个更小的回应动作。",
    situation: "孩子说马上写，但过了一会儿还没有开始。家长提醒几次后，声音慢慢变大，孩子也开始不耐烦。",
    usualResponse: "常见反应是继续催促、反复讲道理，或者把这件事升级成态度问题。",
    supportiveResponse: "可以先把任务放小一点，先说出看到的状态，再和孩子约定一个很短的开始动作。",
    practiceCard: {
      title: "暂停训练",
      subtitle: "在继续提醒前，先给自己一个停顿",
      tag: "推荐",
      duration: "3-5 分钟",
      scenario: "作业拖延、反复催促前",
      tags: "emotional_behavior,repeated_urging",
    },
  },
  {
    id: "adolescent-distance",
    title: "青春期孩子越来越少说话，家长可以怎么靠近？",
    tag: "青春期",
    readTime: "5分钟阅读",
    summary: "青春期的沉默不一定代表拒绝家长。这个案例帮助家长减少追问，用更低压力的方式保持连接。",
    situation: "孩子回家后不太说话，家长想了解近况，但问得越多，孩子越简单回答。",
    usualResponse: "常见反应是连续追问、要求孩子必须说清楚，或者把沉默理解成不尊重。",
    supportiveResponse: "可以把问题变小，先表达愿意陪在旁边，再给孩子选择什么时候说。",
    practiceCard: {
      title: "非评判陪伴",
      subtitle: "先接住孩子的状态，再等待合适时机",
      tag: "适合",
      duration: "5-10 分钟",
      scenario: "青春期沟通、孩子沉默",
      tags: "judgmental_language,validation",
    },
  },
];

Page({
  data: {
    activeTag: "全部",
    tags: ["全部", "考试压力", "情绪爆发", "亲子沟通", "关系修复", "青春期"],
    topics,
    visibleTopics: topics,
    selectedTopic: topics[0],
  },

  onLoad(options) {
    const selected = topics.find((topic) => topic.id === options.id) || topics[0];
    this.setData({
      selectedTopic: selected,
      activeTag: selected.tag,
      visibleTopics: topics.filter((topic) => topic.tag === selected.tag),
    });
  },

  selectTag(event) {
    const tag = event.currentTarget.dataset.tag;
    const visibleTopics = tag === "全部" ? topics : topics.filter((topic) => topic.tag === tag);
    this.setData({
      activeTag: tag,
      visibleTopics,
      selectedTopic: visibleTopics[0] || topics[0],
    });
  },

  selectTopic(event) {
    const id = event.currentTarget.dataset.id;
    const selectedTopic = topics.find((topic) => topic.id === id);
    if (!selectedTopic) return;
    this.setData({
      selectedTopic,
    });
  },

  openPractice() {
    const tags = this.data.selectedTopic.practiceCard.tags;
    wx.navigateTo({
      url: `/pages/training-card/index?tags=${encodeURIComponent(tags)}`,
    });
  },

  goHome() {
    wx.switchTab({ url: "/pages/home/index" });
  },
});

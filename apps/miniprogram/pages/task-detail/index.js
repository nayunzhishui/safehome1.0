const TASKS = {
  emotion_education: {
    id: "emotion_education",
    cardId: "emotion_naming",
    title: "情绪教育",
    subtitle: "理解情绪，不急着压下去",
    scenario: "孩子突然激动、家长还没理解发生了什么时",
    duration: "5 分钟",
    goal: "先把情绪当成信号，而不是需要立刻压下去的问题。",
    steps: ["停下来，先不急着纠正。", "在心里说出这可能是一种情绪反应。", "先描述看到的事实，再询问孩子的感受。"],
    scripts: ["我看到你现在很难受。", "这件事对你来说可能不容易。", "我们先弄清楚发生了什么。"],
    tagsText: "emotion_awareness",
  },
  emotion_awareness: {
    id: "emotion_awareness",
    cardId: "emotion_naming",
    title: "情绪觉察",
    subtitle: "看见自己的情绪变化",
    scenario: "自己语速变快、胸口发紧或想立刻批评时",
    duration: "3-5 分钟",
    goal: "在回应孩子前，先识别自己的情绪和身体信号。",
    steps: ["停下来，感受身体哪里最紧。", "给自己的情绪命名。", "用一句观察句替代第一句批评。"],
    scripts: ["我现在有点着急，我先慢一点说。", "我看到作业还没有开始。", "我们先看第一步可以做什么。"],
    tagsText: "emotion_awareness,high_emotion_intensity",
  },
  body_regulation: {
    id: "body_regulation",
    cardId: "three_second_pause",
    title: "身体调节",
    subtitle: "通过呼吸和放松稳定身体",
    scenario: "准备提高音量、身体紧绷或反复催促时",
    duration: "5-8 分钟",
    goal: "先让身体反应降一点，再进入沟通。",
    steps: ["双脚踩稳，肩膀放松。", "慢慢吸气，再慢慢呼气。", "等语速降下来后，只说一个具体请求。"],
    scripts: ["我先停一下，慢一点说。", "我们先把今天第一项找出来。", "这一步做完后再看下一步。"],
    tagsText: "high_emotion_intensity,emotional_behavior",
  },
  pause_training: {
    id: "pause_training",
    cardId: "three_second_pause",
    title: "暂停训练",
    subtitle: "在冲突前先停一停",
    scenario: "亲子冲突前、催促前、情绪升高前",
    duration: "3-5 分钟",
    goal: "在自动反应出现前，给自己一个缓冲。",
    steps: ["停下来，先不急着纠正。", "说出你观察到的情绪。", "用一句接纳性话语回应。"],
    scripts: ["我看到你现在很委屈。", "这件事对你来说确实不容易。", "我们可以先缓一缓，等你准备好了再说。"],
    tagsText: "high_demand_language,emotional_behavior",
  },
  cognitive_adjustment: {
    id: "cognitive_adjustment",
    cardId: "cognitive_flexibility",
    title: "认知调整",
    subtitle: "换一个角度理解事件",
    scenario: "觉得孩子就是故意拖延或不配合时",
    duration: "5-8 分钟",
    goal: "从单一解释转向更灵活的理解。",
    steps: ["写下脑中第一个解释。", "问自己是否还有第二种可能。", "基于新的解释给出一个小帮助。"],
    scripts: ["也许他不是故意拖，而是不知道从哪里开始。", "我们先选最容易开始的一题。", "我愿意先听你说说卡在哪里。"],
    tagsText: "negative_attribution,catastrophic_prediction",
  },
  alternative_thought: {
    id: "alternative_thought",
    cardId: "cognitive_flexibility",
    title: "替代想法",
    subtitle: "找到更有帮助的想法",
    scenario: "脑中反复出现责备、担心或最坏结果时",
    duration: "5 分钟",
    goal: "找到一句更能帮助自己行动的想法。",
    steps: ["把自动想法写成一句话。", "删掉绝对化词语。", "换成一句更具体、更可执行的想法。"],
    scripts: ["这次只是一个困难时刻，不代表一直都会这样。", "我可以先帮他开始第一步。", "先处理眼前这一件事。"],
    tagsText: "negative_attribution,cognitive_flexibility",
  },
  communication_expression: {
    id: "communication_expression",
    cardId: "alternative_behavior",
    title: "沟通表达",
    subtitle: "把感受说清楚",
    scenario: "想表达要求但担心变成指责时",
    duration: "5-10 分钟",
    goal: "把高压表达换成事实、感受和一个具体请求。",
    steps: ["先说事实，不评价。", "再说自己的感受。", "最后提出一个小请求。"],
    scripts: ["我看到作业还没开始，我有点着急。", "我们先一起看今天第一项。", "你可以选先做语文还是数学。"],
    tagsText: "high_demand_language,judgmental_language",
  },
  nonjudgmental_company: {
    id: "nonjudgmental_company",
    cardId: "nonjudgmental_response",
    title: "非评判陪伴",
    subtitle: "先接住孩子的情绪",
    scenario: "孩子委屈、生气、崩溃或不愿说话时",
    duration: "5-10 分钟",
    goal: "先连接情绪，再讨论问题。",
    steps: ["停下来，先不急着纠正。", "说出你观察到的情绪。", "用一句接纳性话语回应。"],
    scripts: ["我看到你现在很委屈。", "这件事对你来说确实不容易。", "我们可以先缓一缓，等你准备好了再说。"],
    tagsText: "judgmental_language,parent_child_conflict",
  },
  relationship_repair: {
    id: "relationship_repair",
    cardId: "nonjudgmental_response",
    title: "关系修复",
    subtitle: "冲突后重新连接",
    scenario: "刚发生争吵、冷处理或双方都很受伤时",
    duration: "8-10 分钟",
    goal: "在问题讨论前，先恢复一点安全感和连接。",
    steps: ["承认刚才沟通不容易。", "说出自己愿意重新开始。", "邀请孩子选择什么时候再谈。"],
    scripts: ["刚才我们都很着急。", "我想重新好好说一次。", "你愿意现在说，还是等一会儿再说？"],
    tagsText: "parent_child_conflict,emotional_behavior",
  },
  positive_interaction: {
    id: "positive_interaction",
    cardId: "alternative_behavior",
    title: "积极互动",
    subtitle: "增加家庭中的正向时刻",
    scenario: "想减少指责、增加合作和亲近时",
    duration: "5 分钟",
    goal: "主动增加一个小的正向互动时刻。",
    steps: ["找到孩子刚完成的一个小动作。", "只描述这个具体动作。", "给出一句真实、简短的肯定。"],
    scripts: ["我看到你刚才自己开始了第一题。", "谢谢你愿意试一下。", "我们先把这个小进步记下来。"],
    tagsText: "behavior_substitution,nonjudgmental_response",
  },
};

Page({
  data: {
    task: null,
    reflection: "",
    emotionLevel: 5,
  },

  onLoad(options) {
    const id = decodeURIComponent(options.id || "nonjudgmental_company");
    const task = TASKS[id] || TASKS.nonjudgmental_company;
    this.setData({ task });
  },

  goBack() {
    wx.navigateBack();
  },

  onReflectionInput(event) {
    this.setData({ reflection: event.detail.value });
  },

  onEmotionLevelChange(event) {
    this.setData({ emotionLevel: Number(event.detail.value) });
  },

  startPractice() {
    wx.showToast({
      title: "可以从第一步开始",
      icon: "none",
    });
  },

  finishPractice() {
    const task = this.data.task;
    if (!task) return;
    wx.navigateTo({
      url: `/pages/checkin/index?card_id=${encodeURIComponent(task.cardId)}&card_title=${encodeURIComponent(task.title)}`,
    });
  },

  recordFeeling() {
    wx.showToast({
      title: this.data.reflection.trim() ? "已暂存在本页" : "可以先写一句感受",
      icon: "none",
    });
  },
});

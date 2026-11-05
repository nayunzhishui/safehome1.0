// B1 急救卡浮层：选分数 → 听着做 → 再选分数 → 看前后分数。见 docs/11_商业化开发/开发框架.md 第 3 节。
// 骨架：状态和事件已定，播放、保存都是 TODO。
// 卡片正文从 GET /api/cards 取，不要写死在这里（test_rc0810_f20 会检查）。
const SCORES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const UNSET = -1;

Component({
  properties: {
    show: { type: Boolean, value: false },
    group: { type: String, value: "heat" },
    // [{ id, title, duration_minutes, audio_file_id }]，来自 GET /api/cards/quick
    cards: { type: Array, value: [] },
    // { [card_id]: { steps: [...] } }，来自 GET /api/cards，可能晚几秒才到
    cardTexts: { type: Object, value: {} },
    loggedIn: { type: Boolean, value: false },
  },
  data: {
    scores: SCORES,
    phase: "before", // before → playing → after → done
    index: 0,
    emotionBefore: UNSET, // 不给默认值，必须点选
    emotionAfter: UNSET,
    audioFailed: false,
  },
  lifetimes: {
    detached() {
      // TODO(B1-前端): 销毁 InnerAudioContext
    },
  },
  methods: {
    onPickBefore(event) {
      this.setData({ emotionBefore: Number(event.currentTarget.dataset.score) });
    },
    onStart() {
      if (this.data.emotionBefore === UNSET) return;
      // TODO(B1-前端): 第二次点击。wx.createInnerAudioContext()，src 用 cards[index].audio_file_id；
      // 播放失败时 audioFailed = true，显示文字步骤，练习照常继续
      this.setData({ phase: "playing" });
    },
    onFinishPractice() {
      this.setData({ phase: "after" });
    },
    onPickAfter(event) {
      this.setData({ emotionAfter: Number(event.currentTarget.dataset.score) });
    },
    onSubmit() {
      if (this.data.emotionAfter === UNSET) return;
      const card = this.data.cards[this.data.index] || {};
      // TODO(B1-前端): 没登录 → utils/quickCardStore.addPending；已登录 → api.createCheckin
      this.setData({ phase: "done" });
      this.triggerEvent("completed", {
        card_id: card.id,
        emotion_before: this.data.emotionBefore,
        emotion_after: this.data.emotionAfter,
        completed: 1,
      });
    },
    onSwitchCard() {
      // TODO(B1-前端): 换同组的下一张，回到 before
    },
    onClose() {
      this.triggerEvent("close");
    },
    onOpenEmergency() {
      wx.navigateTo({ url: "/pages/emergency-guide/index" });
    },
  },
});

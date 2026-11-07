// B1 急救卡浮层：点一个分数就开始 → 照着做（有语音就播放）→ 再点一个分数 → 看前后分数。
// 见 docs/11_商业化开发/开发框架.md 第 3 节。卡片正文由页面从 GET /api/cards 取来传进来，不写死在这里（test_rc0810_f20 会检查）。
// 不打分也能做：没点分数就不记分（负责人 11-05 定）。保存由页面负责，这里只发 completed 事件。
const SCORES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const UNSET = -1;

Component({
  properties: {
    show: { type: Boolean, value: false },
    group: { type: String, value: "heat" },
    // [{ id, title, duration_minutes, steps, example, stopRule, audio_file_id }]
    cards: { type: Array, value: [] },
    loggedIn: { type: Boolean, value: false },
    saveMessage: { type: String, value: "" },
  },
  data: {
    scores: SCORES,
    phase: "before", // before → playing → after → done
    index: 0,
    emotionBefore: UNSET,
    emotionAfter: UNSET,
    hasAudio: false,
    audioFailed: false,
  },
  observers: {
    show(show) {
      this.stopAudio();
      if (show) this.setData({ phase: "before", index: 0, emotionBefore: UNSET, emotionAfter: UNSET, audioFailed: false });
    },
  },
  lifetimes: {
    detached() {
      this.stopAudio();
    },
  },
  methods: {
    currentCard() {
      return this.data.cards[this.data.index] || {};
    },
    // 有语音文件就播放；没有或播放失败时只看文字步骤，练习照常继续
    playAudio() {
      this.stopAudio();
      const src = this.currentCard().audio_file_id;
      if (!src || !wx.createInnerAudioContext) {
        this.setData({ hasAudio: false });
        return;
      }
      const audio = wx.createInnerAudioContext();
      audio.src = src;
      audio.onError(() => this.setData({ audioFailed: true }));
      audio.play();
      this._audio = audio;
      this.setData({ hasAudio: true, audioFailed: false });
    },
    stopAudio() {
      if (!this._audio) return;
      try {
        this._audio.stop();
        this._audio.destroy();
      } catch (error) {
        // 已经销毁的就算了
      }
      this._audio = null;
    },
    start(score) {
      this.setData({ emotionBefore: score, phase: "playing" });
      this.playAudio();
      this.triggerEvent("started", { card_id: this.currentCard().id, group: this.data.group });
    },
    onPickBefore(event) {
      this.start(Number(event.currentTarget.dataset.score));
    },
    onStartWithoutScore() {
      this.start(UNSET);
    },
    onSwitchCard() {
      if (this.data.cards.length < 2) return;
      this.setData({ index: (this.data.index + 1) % this.data.cards.length });
      this.playAudio();
    },
    onFinishPractice() {
      this.stopAudio();
      this.setData({ phase: "after" });
    },
    finish(score) {
      this.setData({ emotionAfter: score, phase: "done" });
      this.triggerEvent("completed", {
        card_id: this.currentCard().id,
        group: this.data.group,
        completed: true,
        emotion_before: this.data.emotionBefore >= 0 ? this.data.emotionBefore : undefined,
        emotion_after: score >= 0 ? score : undefined,
      });
    },
    onPickAfter(event) {
      this.finish(Number(event.currentTarget.dataset.score));
    },
    onFinishWithoutScore() {
      this.finish(UNSET);
    },
    onLogin() {
      this.triggerEvent("login");
    },
    onClose() {
      this.stopAudio();
      this.triggerEvent("close");
    },
    onOpenEmergency() {
      this.stopAudio();
      wx.navigateTo({ url: "/pages/emergency-guide/index" });
    },
  },
});

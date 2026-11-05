// B3 练习前后分数：“练之前 7 分，练完 5 分”。分数没降也照实显示。见 docs/11_商业化开发/开发框架.md 第 5 节。
Component({
  properties: {
    before: { type: Number, value: -1 },
    after: { type: Number, value: -1 },
  },
  data: { text: "" },
  observers: {
    "before, after"(before, after) {
      const ready = before >= 0 && after >= 0;
      this.setData({ text: ready ? `练之前 ${before} 分，练完 ${after} 分` : "" });
    },
  },
});

// B3 个人基线：参照物是她自己，不和别人比。见 docs/11_商业化开发/开发框架.md 第 5 节。
Component({
  properties: {
    baseline: { type: Object, value: null }, // GET /api/insights/baseline 的返回
  },
  data: { waitingText: "" },
  observers: {
    baseline(value) {
      if (!value || value.available) {
        this.setData({ waitingText: "" });
        return;
      }
      // TODO(B3-前端): need_records 或 need_days 为 0 时只说另一半
      this.setData({ waitingText: `再记 ${value.need_records} 次、再过 ${value.need_days} 天，就能看到你自己的基线` });
    },
  },
});

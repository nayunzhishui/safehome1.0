// TimelineItem（Figma 642:422）：竹节时间线条目。current 实心竹节＋青瓷色小标题；done 淡化实心竹节；upcoming 空心竹节。
Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    state: { type: String, value: "current" },
    kicker: { type: String, value: "" },
    title: { type: String, value: "" },
    body: { type: String, value: "" },
    showLine: { type: Boolean, value: true },
  },
});

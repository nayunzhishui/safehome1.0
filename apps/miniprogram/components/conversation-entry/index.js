// 回答按空行或换行分段显示，段间留 8 的间距（Figma 671:3155）。
function splitParagraphs(content) {
  return String(content || "").split(/\n+/).map((line) => line.trim()).filter(Boolean);
}

Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    message: { type: Object, value: {} },
  },
  data: { paragraphs: [] },
  lifetimes: {
    attached() {
      this.setData({ paragraphs: splitParagraphs((this.data.message || {}).content) });
    },
  },
  observers: {
    "message.content"(value) {
      this.setData({ paragraphs: splitParagraphs(value) });
    },
  },
});

// B4 深度报告：按快照分节显示，不够门槛的节不显示；顶部固定风险提示和求助入口。见 docs/11_商业化开发/开发框架.md 第 6 节。
// 文字只写“练完平均降了几分（几次）”，不写“最有效”。
Component({
  properties: {
    preview: { type: Object, value: null }, // GET /api/deep-report/preview
    report: { type: Object, value: null }, // 快照，结构见开发框架第 6.3 节
  },
  methods: {
    onPurchase() {
      this.triggerEvent("purchase", { source: "deep_report" });
    },
    onExportImage() {
      // TODO(B4-前端): 用 utils/longImage.js（从 pages/relationship-report 抽出来）导出长图
      this.triggerEvent("exportimage");
    },
    onOpenSupport() {
      wx.navigateTo({ url: "/pages/emergency-guide/index" });
    },
  },
});

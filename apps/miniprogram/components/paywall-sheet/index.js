// B5 付费面板。只挂在三处：深度报告预览、4 周方案入口、完整短课入口。见 docs/11_商业化开发/开发框架.md 第 7.6 节。
// 紧急安全指引、紧急求助资源、人工支持这些页面，以及所有风险提示，都不能挂这个组件。
const { canPurchase } = require("../../utils/commerce");

Component({
  properties: {
    show: { type: Boolean, value: false },
    skus: { type: Array, value: [] }, // GET /api/commerce/skus 的 items
    platform: { type: String, value: "" },
    source: { type: String, value: "" }, // deep_report / four_week_plan / full_courses
  },
  data: { purchasable: false },
  observers: {
    platform(platform) {
      this.setData({ purchasable: canPurchase(platform) });
    },
  },
  methods: {
    onBuy(event) {
      const { sku } = event.currentTarget.dataset;
      // TODO(B5-前端): utils/commerce.purchase(api, sku)，成功后 triggerEvent("purchased")
      this.triggerEvent("buy", { sku_id: sku, source: this.data.source });
    },
    onClose() {
      this.triggerEvent("close");
    },
  },
});

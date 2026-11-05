// B6 下一步：一篇文章、一支视频、一门课或一个故事之后，接一张训练卡或一份问卷。见 docs/11_商业化开发/开发框架.md 第 8 节。
// 高风险时页面不显示这个组件，改为显示求助入口。
const { pathFor } = require("../../utils/contentRoute");

Component({
  properties: {
    items: { type: Array, value: [] }, // GET /api/content-map/next-step 返回的 next
  },
  methods: {
    onOpen(event) {
      const { id } = event.currentTarget.dataset;
      const url = pathFor(id);
      if (url) wx.navigateTo({ url });
      this.triggerEvent("open", { id });
    },
  },
});

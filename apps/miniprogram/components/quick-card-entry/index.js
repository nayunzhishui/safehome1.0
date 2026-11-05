// B1 急救卡入口：首页上的两个按钮。见 docs/11_商业化开发/开发框架.md 第 3 节。
// 骨架：属性和事件已定，还没有挂到页面上。
const DEFAULT_GROUPS = [
  { key: "heat", label: "我现在很火" },
  { key: "after", label: "刚吵完" },
];

Component({
  properties: {
    groups: { type: Array, value: DEFAULT_GROUPS },
  },
  methods: {
    onTapGroup(event) {
      const { key } = event.currentTarget.dataset;
      // 第一次点击：首页监听 open 事件，打开 quick-card-player 浮层
      this.triggerEvent("open", { group: key });
    },
  },
});

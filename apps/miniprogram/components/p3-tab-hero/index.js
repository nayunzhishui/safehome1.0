// TabHero（Figma 642:448）：训练、课程、我的三个标签页顶部。自定义导航，竹林插画随胶囊位置下移。
const { navMetrics, FIGMA_NAV_BOTTOM } = require("../../utils/nav-metrics");

// Figma 中标题距导航底 8px、副标题距导航底 54px，整块高 186px（导航底 88）。
const TITLE_GAP = 8;
const SUBTITLE_GAP = 54;
const HERO_HEIGHT = 186;

function layout() {
  const nav = navMetrics();
  return {
    offset: Math.max(0, Math.round(nav.offset)),
    titleTop: Math.round(nav.navBottom + TITLE_GAP),
    subtitleTop: Math.round(nav.navBottom + SUBTITLE_GAP),
    height: Math.round(nav.navBottom + HERO_HEIGHT - FIGMA_NAV_BOTTOM),
  };
}

Component({
  options: { styleIsolation: "apply-shared", multipleSlots: true },
  properties: {
    title: { type: String, value: "" },
    subtitle: { type: String, value: "" },
  },
  data: {
    hero: { offset: 0, titleTop: 96, subtitleTop: 142, height: HERO_HEIGHT },
  },
  lifetimes: {
    attached() {
      this.setData({ hero: layout() });
    },
  },
});

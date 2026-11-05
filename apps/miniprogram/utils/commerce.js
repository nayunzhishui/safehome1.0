// B5 付费的前端工具。见 docs/11_商业化开发/开发框架.md 第 7 节。
// 只有安卓显示购买按钮；iOS 和电脑端不显示，也不写引导去别处付款的话。
function getPlatform() {
  try {
    const info = typeof wx.getDeviceInfo === "function" ? wx.getDeviceInfo() : wx.getSystemInfoSync();
    return String(info.platform || "").toLowerCase();
  } catch (error) {
    return "";
  }
}

function canPurchase(platform) {
  return platform === "android";
}

function purchase(api, skuId) {
  // TODO(B5-前端): 建单 → 调起支付（mock 或 wx.requestVirtualPayment）→ 轮询订单最多 5 次 → 返回订单
  return Promise.reject(new Error("B5-前端尚未实现"));
}

module.exports = { getPlatform, canPurchase, purchase };

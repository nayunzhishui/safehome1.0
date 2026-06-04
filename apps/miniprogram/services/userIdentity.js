const STORAGE_KEY = "safehome_anonymous_user_id";

function generateAnonymousUserId() {
  return `wx_user_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function getAnonymousUserId() {
  if (typeof wx === "undefined" || !wx.getStorageSync || !wx.setStorageSync) {
    return generateAnonymousUserId();
  }

  const existing = wx.getStorageSync(STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const generated = generateAnonymousUserId();
  wx.setStorageSync(STORAGE_KEY, generated);
  return generated;
}

module.exports = {
  STORAGE_KEY,
  getAnonymousUserId,
};

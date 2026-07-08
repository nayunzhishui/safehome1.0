function getAuthToken() {
  return wx.getStorageSync("auth_token") || "";
}

function getAuthUser() {
  return wx.getStorageSync("auth_user") || null;
}

function isLoggedIn() {
  return !!getAuthToken();
}

function requireLogin(options = {}) {
  if (isLoggedIn()) {
    return true;
  }
  const redirectUrl = options.redirectUrl || "";
  const message = options.message || "请先登录，这样系统才能保存你的记录并生成后续复盘。";
  wx.showToast({
    title: message,
    icon: "none",
    duration: 1800,
  });
  const query = redirectUrl ? `?redirect=${encodeURIComponent(redirectUrl)}` : "";
  setTimeout(() => {
    wx.navigateTo({ url: `/pages/login/index${query}` });
  }, 300);
  return false;
}

function logout() {
  wx.removeStorageSync("auth_token");
  wx.removeStorageSync("auth_user");
  try {
    const app = getApp();
    if (app && app.logout) {
      app.logout();
    }
  } catch (error) {
    // getApp may be unavailable in isolated utility tests.
  }
}

module.exports = {
  getAuthToken,
  getAuthUser,
  isLoggedIn,
  requireLogin,
  logout,
};

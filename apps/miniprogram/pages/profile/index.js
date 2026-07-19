const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, isLoggedIn, logout, requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

Page({
  data: {
    user: {
      nickname: "温暖的家长",
      loginState: "当前为试点体验模式",
      streakText: "连续记录 0 天",
      growthLevel: "本周待记录",
      roleText: "",
    },
    loggedIn: false,
    recordEntries: [
      {
        title: "周报入口",
        subtitle: "查看本周变化",
        url: "/pages/weekly-report/index",
        private: true,
      },
      {
        title: "历次反馈",
        subtitle: "查看消息和补充反馈",
        url: "/pages/messages/index",
        private: true,
      },
      {
        title: "训练记录",
        subtitle: "查看已完成的训练卡记录",
        url: "/pages/training-history/index",
        private: true,
      },
      {
        title: "测评记录",
        subtitle: "查看全部支持性测评记录",
        url: "/pages/assessment-history/index",
        private: true,
      },
      {
        title: "我的成长仪表盘",
        subtitle: "分开查看记录、测评、关系探索与人工反馈",
        url: "/pages/growth-dashboard/index",
        private: true,
      },
    ],
    supportEntries: [
      {
        title: "人工督导",
        subtitle: "获得专业补充反馈",
        url: "/pages/supervision/index",
        private: true,
      },
      {
        title: "专业资源说明",
        subtitle: "了解线下支持边界",
        url: "/pages/emergency-resources/index",
      },
    ],
    safetyEntries: [
      {
        title: "紧急安全指引",
        subtitle: "出现安全风险时先找现实帮助",
        url: "/pages/emergency-guide/index",
      },
      {
        title: "紧急帮助说明",
        subtitle: "了解可用现实资源",
        url: "/pages/emergency-resources/index",
      },
    ],
    settingsEntries: [
      {
        title: "知情与边界",
        subtitle: "了解本工具能做什么",
        url: "/pages/settings-detail/index?type=consent",
      },
      {
        title: "隐私说明",
        subtitle: "了解记录和研究数据如何使用",
        url: "/pages/settings-detail/index?type=privacy",
      },
      {
        title: "工具边界",
        subtitle: "不做诊断、不替代紧急帮助",
        url: "/pages/settings-detail/index?type=boundary",
      },
    ],
    stats: null,
    isResearcher: false,
    showcaseAccess: false,
    dataClaim: null,
    claimBusy: false,
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const storedUser = getAuthUser();
    const loggedIn = isLoggedIn();
    const canClaim = loggedIn && storedUser && ["parent", "student", "user"].includes(storedUser.role);
    const [showcase, claimPreview] = await Promise.all([
      api.getShowcaseAccess().catch(() => ({ enabled: false })),
      canClaim ? api.getDataClaimPreview().catch(() => null) : Promise.resolve(null),
    ]);
    const dismissedClaimId = wx.getStorageSync("safehome_dismissed_data_claim_id") || "";
    const dataClaim = claimPreview && claimPreview.available && claimPreview.claim_id !== dismissedClaimId
      ? claimPreview
      : null;
    try {
      const stats = await api.getProfileStats();
      this.setData({
        stats,
        loggedIn,
        user: {
          nickname: storedUser && storedUser.nickname ? storedUser.nickname : "温暖的家长",
          loginState: storedUser ? "已登录，可同步记录" : "当前为试点体验模式",
          streakText: `连续记录 ${stats.streak_days || 0} 天`,
          growthLevel: stats.weekly_record_count > 0 ? "本周有记录" : "本周待记录",
          roleText: storedUser && storedUser.role ? this.formatRole(storedUser.role) : "",
        },
        isResearcher: !!showcase.enabled || !!(storedUser && ["researcher", "admin", "supervisor"].includes(storedUser.role)),
        showcaseAccess: !!showcase.enabled,
        dataClaim,
      });
    } catch (error) {
      this.setData({
        loggedIn,
        user: {
          ...this.data.user,
          nickname: storedUser && storedUser.nickname ? storedUser.nickname : "温暖的家长",
          loginState: storedUser ? "已登录，本次暂时离线" : "未登录，先登录后查看记录",
          roleText: storedUser && storedUser.role ? this.formatRole(storedUser.role) : "",
        },
        dataClaim,
      });
    }
  },

  formatRole(role) {
    const map = {
      parent: "家长账号",
      student: "学生账号",
      researcher: "研究账号",
      supervisor: "督导账号",
      admin: "管理员",
    };
    return map[role] || role;
  },

  openEntry(event) {
    const group = event.currentTarget.dataset.group || "recordEntries";
    const index = event.currentTarget.dataset.index;
    const list = this.data[group] || [];
    const entry = list[index];
    if (!entry) return;
    if (entry.private && !requireLogin({
      redirectUrl: entry.tab ? "/pages/profile/index" : entry.url,
      message: "请先登录，这样系统才能保存你的记录并生成后续复盘。",
    })) {
      return;
    }
    if (!entry.url) {
      wx.showToast({
        title: "后续会补充更完整说明",
        icon: "none",
      });
      return;
    }
    if (entry.tab) {
      wx.switchTab({ url: entry.url });
      return;
    }
    wx.navigateTo({ url: entry.url });
  },

  goLogin() {
    wx.navigateTo({ url: "/pages/login/index?redirect=%2Fpages%2Fprofile%2Findex" });
  },

  goRegister() {
    wx.navigateTo({ url: "/pages/register/index?redirect=%2Fpages%2Fprofile%2Findex" });
  },

  goResearcher() {
    const storedUser = getAuthUser();
    if (storedUser && (this.data.showcaseAccess || ["researcher", "admin", "supervisor"].includes(storedUser.role))) {
      wx.navigateTo({ url: "/pages/researcher-dashboard/index" });
      return;
    }
    wx.navigateTo({ url: "/pages/login/index?redirect=%2Fpages%2Fresearcher-dashboard%2Findex" });
  },

  dismissDataClaim() {
    if (this.data.dataClaim && this.data.dataClaim.claim_id) {
      wx.setStorageSync("safehome_dismissed_data_claim_id", this.data.dataClaim.claim_id);
    }
    this.setData({ dataClaim: null });
  },

  async confirmDataClaim() {
    const claim = this.data.dataClaim;
    if (!claim || !claim.claim_id || this.data.claimBusy) return;
    this.setData({ claimBusy: true });
    try {
      const result = await api.claimAnonymousData(claim.claim_id);
      wx.removeStorageSync("safehome_dismissed_data_claim_id");
      this.setData({ dataClaim: null, claimBusy: false });
      wx.showToast({ title: `已合并 ${result.total_records || 0} 条记录`, icon: "success" });
      await this.loadProfile();
    } catch (error) {
      this.setData({ claimBusy: false });
      wx.showToast({ title: error.message || "暂时未能合并，请稍后再试", icon: "none" });
    }
  },

  doLogout() {
    logout();
    wx.showToast({ title: "已退出", icon: "success" });
    this.loadProfile();
  },
});

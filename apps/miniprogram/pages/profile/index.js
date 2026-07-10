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
        subtitle: "回到训练中心继续练习",
        url: "/pages/training/index",
        tab: true,
      },
      {
        title: "测评记录",
        subtitle: "回顾支持性测评",
        url: "/pages/assessment/index",
        private: true,
      },
      {
        title: "关系探索成长仪表盘",
        subtitle: "查看多次测评、任务、事件和变化记录",
        url: "/pages/relationship-growth/index",
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
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const storedUser = getAuthUser();
    const loggedIn = isLoggedIn();
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
        isResearcher: !!(storedUser && ["researcher", "admin", "supervisor"].includes(storedUser.role)),
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
    if (storedUser && ["researcher", "admin", "supervisor"].includes(storedUser.role)) {
      wx.navigateTo({ url: "/pages/researcher-dashboard/index" });
      return;
    }
    wx.navigateTo({ url: "/pages/login/index?redirect=%2Fpages%2Fresearcher-dashboard%2Findex" });
  },

  doLogout() {
    logout();
    wx.showToast({ title: "已退出", icon: "success" });
    this.loadProfile();
  },
});

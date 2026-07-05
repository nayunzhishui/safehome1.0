const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    user: {
      nickname: "温暖的家长",
      loginState: "当前为试点体验模式",
      streakText: "连续记录 0 天",
      growthLevel: "本周待记录",
    },
    recordEntries: [
      {
        title: "周报入口",
        subtitle: "查看本周变化",
        url: "/pages/weekly-report/index",
      },
      {
        title: "历次反馈",
        subtitle: "查看消息和补充反馈",
        url: "/pages/messages/index",
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
      },
    ],
    supportEntries: [
      {
        title: "人工督导",
        subtitle: "获得专业补充反馈",
        url: "/pages/supervision/index",
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
        url: "",
      },
      {
        title: "隐私说明",
        subtitle: "后续接入隐私文本",
        url: "",
      },
    ],
    stats: null,
  },

  onShow() {
    this.loadProfile();
  },

  async loadProfile() {
    const storedUser = wx.getStorageSync("auth_user") || null;
    try {
      const stats = await api.getProfileStats();
      this.setData({
        stats,
        user: {
          nickname: storedUser && storedUser.nickname ? storedUser.nickname : "温暖的家长",
          loginState: storedUser ? "已登录，可同步记录" : "当前为试点体验模式",
          streakText: `连续记录 ${stats.streak_days || 0} 天`,
          growthLevel: stats.weekly_record_count > 0 ? "本周有记录" : "本周待记录",
        },
      });
    } catch (error) {
      this.setData({
        user: {
          ...this.data.user,
          nickname: storedUser && storedUser.nickname ? storedUser.nickname : "温暖的家长",
          loginState: "离线时显示本地入口",
        },
      });
    }
  },

  openEntry(event) {
    const group = event.currentTarget.dataset.group || "recordEntries";
    const index = event.currentTarget.dataset.index;
    const list = this.data[group] || [];
    const entry = list[index];
    if (!entry) return;
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
});

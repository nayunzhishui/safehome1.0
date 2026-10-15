const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, isLoggedIn, logout, requireLogin, captureAuthSession, isCurrentAuthSession } = require("../../utils/authGuard");
const { navMetrics, FIGMA_NAV_BOTTOM } = require("../../utils/nav-metrics");
const { localDisplayIdentity } = require("../../utils/wechatProfile");

const api = createSafeHomeApi();

// 入口分组来自页面配置（Figma 643:932 GroupRow）；说明文字在“专业支持”和紧急分组里显示，其余只作读屏补充。
const RECORD_ENTRIES = [
  { title: "本周复盘", subtitle: "查看本周变化", icon: "calendar", iconTone: "ink", url: "/pages/weekly-report/index", private: true },
  { title: "历次反馈", subtitle: "查看消息和补充反馈", icon: "message", url: "/pages/messages/index", private: true },
  { title: "训练记录", subtitle: "查看已完成的训练卡记录", icon: "leaf", url: "/pages/training-history/index", private: true },
  { title: "测评记录", subtitle: "查看全部支持性测评记录", icon: "check", url: "/pages/assessment-history/index", private: true },
  { title: "我的成长仪表盘", subtitle: "分开查看记录、测评、关系探索与人工反馈", icon: "chart", url: "/pages/growth-dashboard/index", private: true },
];

const SAFETY_ENTRIES = [
  { title: "紧急安全指引", subtitle: "出现安全风险时先找现实帮助", icon: "alert", url: "/pages/emergency-guide/index" },
  { title: "紧急帮助说明", subtitle: "可用的现实资源", icon: "phone", url: "/pages/emergency-resources/index" },
];

const SETTINGS_ENTRIES = [
  { title: "参与者保护", subtitle: "年龄确认、家长绑定与未满14周岁保护", icon: "shield", url: "/pages/settings-detail/index?type=protection", private: true },
  { title: "知情与边界", subtitle: "了解本工具能做什么", icon: "info", url: "/pages/settings-detail/index?type=consent" },
  { title: "隐私说明", subtitle: "了解记录和研究数据如何使用", icon: "lock", url: "/pages/settings-detail/index?type=privacy" },
  { title: "工具边界", subtitle: "不做诊断、不替代紧急帮助", icon: "slash", url: "/pages/settings-detail/index?type=boundary" },
];

const BASE_SUPPORT_ENTRIES = [
  {
    title: "支持性评估",
    subtitle: "自助整理一个想弄清楚的问题",
    icon: "compass",
    url: "/pages/therapeutic-assessment/index",
    private: true,
  },
  {
    title: "人工支持",
    subtitle: "提交补充理解请求",
    icon: "person",
    url: "/pages/supervision/index",
    private: true,
  },
  {
    title: "专业资源说明",
    subtitle: "",
    icon: "book",
    url: "/pages/emergency-resources/index",
  },
];

function buildSupportEntries(participantEntryVisible, capability = null) {
  if (!participantEntryVisible) return BASE_SUPPORT_ENTRIES;
  const simulated = capability && capability.response_origin === "synthetic_simulation";
  const label = simulated ? "合成问答演示" : "支持性问答";
  return [
    BASE_SUPPORT_ENTRIES[0],
    {
      title: label,
      subtitle: simulated
        ? "仅用于本地合成数据演示，不代表真实供应商回答"
        : "根据已审核内容整理一个可暂停的小步骤",
      icon: "message",
      url: "/pages/support-assistant/index?focus=ai",
      private: true,
    },
    {
      title: simulated ? "合成知识检索演示" : "知识库问答",
      subtitle: "从已审核项目内容检索并显示参考来源",
      icon: "info",
      url: "/pages/support-assistant/index?focus=rag",
      private: true,
    },
    ...BASE_SUPPORT_ENTRIES.slice(1),
  ];
}

function buildEntryGroups(supportEntries) {
  return [
    { key: "recordEntries", title: "我的记录", entries: RECORD_ENTRIES },
    { key: "supportEntries", title: "专业支持", entries: supportEntries, showSubtitles: true },
    {
      key: "safetyEntries",
      title: "紧急时先找现实帮助",
      subtitle: "本小程序不能提供实时危机干预，请先联系身边可信赖的人或当地紧急支持。",
      entries: SAFETY_ENTRIES,
      tone: "warm",
      showSubtitles: true,
    },
    { key: "settingsEntries", title: "设置与说明", entries: SETTINGS_ENTRIES },
  ];
}

// 自定义导航：头像距导航底 8px，整块高 196px（Figma 导航底 88）。
function heroLayout() {
  const nav = navMetrics();
  return {
    offset: Math.max(0, Math.round(nav.offset)),
    top: Math.round(nav.navBottom + 8),
    height: Math.round(nav.navBottom + 196 - FIGMA_NAV_BOTTOM),
  };
}

const DEFAULT_USER = {
  nickname: "温暖的家长",
  avatarPath: "",
  metaText: "试点体验 · 连续记录 0 天",
  growthLevel: "本周待记录",
};

Page({
  data: {
    hero: { offset: 0, top: 96, height: 196 },
    user: DEFAULT_USER,
    loggedIn: false,
    entryGroups: buildEntryGroups(buildSupportEntries(false)),
    stats: null,
    isResearcher: false,
    showcaseAccess: false,
    dataClaim: null,
    claimBusy: false,
    identityStatus: null,
    identityBusy: false,
    logoutBusy: false,
    profileSheetVisible: false,
    profileSheetUserId: "",
  },

  onLoad() {
    this.setData({ hero: heroLayout() });
  },

  onShow() {
    this._hidden = false;
    if (this._readSession && !isCurrentAuthSession(this._readSession)) this.setData({ stats: null, dataClaim: null, identityStatus: null, user: DEFAULT_USER, loggedIn: false, logoutBusy: false });
    this.loadProfile();
  },

  onHide() { this._hidden = true; },
  onUnload() { this._consentDisposed = true; this._hidden = true; },

  async loadProfile() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._profileRequestId = (this._profileRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._profileRequestId && isCurrentAuthSession(session);
    const storedUser = getAuthUser();
    const loggedIn = isLoggedIn();
    const canClaim = loggedIn && storedUser && ["parent", "student", "user"].includes(storedUser.role);
    const [showcase, claimPreview, identityStatus, aiConfig] = await Promise.all([
      api.getShowcaseAccess().catch(() => ({ enabled: false })),
      canClaim ? api.getDataClaimPreview().catch(() => null) : Promise.resolve(null),
      canClaim ? api.getIdentityStatus().catch(() => null) : Promise.resolve(null),
      api.getAiQaConfig().catch(() => null),
    ]);
      if (!isCurrent()) return;
    const supportEntries = buildSupportEntries(
      Boolean(aiConfig && aiConfig.participant_entry_visible),
      aiConfig && aiConfig.capability,
    );
    const dismissedClaimId = wx.getStorageSync("safehome_dismissed_data_claim_id") || "";
    const dataClaim = claimPreview && claimPreview.available && claimPreview.claim_id !== dismissedClaimId
      ? claimPreview
      : null;
    try {
      const stats = await api.getProfileStats();
      if (!isCurrent()) return;
      const roleText = storedUser && storedUser.role ? this.formatRole(storedUser.role) : "";
      this.setData({
        stats,
        loggedIn,
        user: {
          ...localDisplayIdentity(storedUser, DEFAULT_USER.nickname),
          metaText: `${roleText || "试点体验"} · 连续记录 ${stats.streak_days || 0} 天`,
          growthLevel: stats.weekly_record_count > 0 ? "本周有记录" : "本周待记录",
        },
        isResearcher: !!showcase.enabled || !!(storedUser && ["researcher", "admin", "supervisor"].includes(storedUser.role)),
        showcaseAccess: !!showcase.enabled,
        dataClaim,
        identityStatus,
        entryGroups: buildEntryGroups(supportEntries),
      });
    } catch (error) {
      if (!isCurrent()) return;
      const roleText = storedUser && storedUser.role ? this.formatRole(storedUser.role) : "";
      this.setData({
        loggedIn,
        user: {
          ...this.data.user,
          ...localDisplayIdentity(storedUser, DEFAULT_USER.nickname),
          metaText: storedUser ? `${roleText || "已登录"} · 本次暂时离线` : "试点体验 · 登录后查看记录",
        },
        dataClaim,
        identityStatus,
        entryGroups: buildEntryGroups(supportEntries),
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
    const key = event.currentTarget.dataset.group || "recordEntries";
    const index = event.currentTarget.dataset.index;
    const group = this.data.entryGroups.find((item) => item.key === key);
    const entry = group ? group.entries[index] : null;
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

  openProfileSheet() {
    const storedUser = getAuthUser();
    if (!storedUser || !storedUser.id) return;
    this.setData({ profileSheetVisible: true, profileSheetUserId: String(storedUser.id) });
  },

  onProfileSheetDone(event) {
    const storedUser = getAuthUser();
    const update = { profileSheetVisible: false };
    if (event.detail && event.detail.saved && storedUser && String(storedUser.id) === this.data.profileSheetUserId) {
      const identity = localDisplayIdentity(storedUser, DEFAULT_USER.nickname);
      update["user.nickname"] = identity.nickname;
      update["user.avatarPath"] = identity.avatarPath;
    }
    this.setData(update);
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
      const result = await api.claimAnonymousData(claim.claim_id, claim.version || 0);
      wx.removeStorageSync("safehome_dismissed_data_claim_id");
      this.setData({ dataClaim: null, claimBusy: false });
      wx.showToast({ title: `已合并 ${result.total_records || 0} 条记录`, icon: "success" });
      await this.loadProfile();
    } catch (error) {
      this.setData({ claimBusy: false });
      wx.showToast({ title: error.message || "暂时未能合并，请稍后再试", icon: "none" });
    }
  },

  requestIdentityUnbind(event) {
    const identityType = event.currentTarget.dataset.identity;
    const status = this.data.identityStatus;
    const descriptor = status && status.identities ? status.identities[identityType] : null;
    if (!descriptor || !descriptor.can_unbind || this.data.identityBusy) return;
    const label = identityType === "wechat" ? "微信登录" : "手机号登录";
    wx.showModal({
      title: `撤销${label}`,
      content: "撤销后会退出所有设备，但不会删除日记、测评或训练记录。确认继续吗？",
      confirmText: "确认撤销",
      confirmColor: "#9B4137",
      success: async (modalResult) => {
        if (!modalResult.confirm) return;
        this.setData({ identityBusy: true });
        try {
          await api.unbindIdentity(identityType, status.auth_epoch);
          logout();
          wx.showToast({ title: "绑定已撤销，请重新登录", icon: "none" });
          setTimeout(() => {
            wx.redirectTo({ url: "/pages/login/index?redirect=%2Fpages%2Fprofile%2Findex" });
          }, 500);
        } catch (error) {
          this.setData({ identityBusy: false });
          wx.showToast({ title: error.message || "状态已更新，请刷新后重试", icon: "none" });
        }
      },
    });
  },

  async doLogout() {
    if (this.data.logoutBusy) return;
    this.setData({ logoutBusy: true });
    const result = await api.logout();
    if (result.session_changed) return;
    this.setData({ logoutBusy: false });
    wx.showToast({
      title: result.pending_logout ? "已退出，联网后将撤销旧会话" : "已退出",
      icon: "none",
    });
    await this.loadProfile();
  },
});

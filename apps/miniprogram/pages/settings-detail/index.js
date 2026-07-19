const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

const NOTICE_MAP = {
  consent: {
    kicker: "知情与边界",
    title: "先知道这个工具能做什么",
    subtitle: "使用前先确认边界，再开始记录和练习。",
    sections: [
      {
        title: "本工具的用途",
        items: [
          "帮助你记录具体情绪事件。",
          "整理互动线索，生成支持性反馈和训练建议。",
          "把测评、训练和复盘整理成阶段性观察。",
        ],
      },
      {
        title: "本工具不做什么",
        items: [
          "不做诊断、不做治疗、不处理紧急危机。",
          "不评价家长、孩子或家庭好坏。",
          "不把量表结果写成固定人格标签。",
        ],
      },
      {
        title: "高风险情况",
        items: [
          "高风险内容可能进入人工关注，但紧急情况仍应优先联系现实中的可靠人员或当地紧急资源。",
        ],
      },
    ],
  },
  privacy: {
    kicker: "隐私说明",
    title: "记录只用于复盘和必要支持",
    subtitle: "这里是小程序端精简说明，正式文本以 content/privacy.md 为准。",
    sections: [
      {
        title: "记录用途",
        items: [
          "记录会用于你的复盘、训练建议和必要的人工补充反馈。",
          "研究分析默认使用脱敏或聚合数据，不默认展示自由文本原文。",
        ],
      },
      {
        title: "账号与数据",
        items: [
          "登录后，系统优先用登录账号识别记录归属。",
          "退出登录只清除本机登录态，不等于删除服务器记录。",
        ],
      },
      {
        title: "人工补充反馈",
        items: [
          "你主动提交人工督导时，相关记录会供老师补充理解。",
          "请不要填写身份证号、详细住址、电话等不必要的个人敏感信息。",
        ],
      },
    ],
  },
  boundary: {
    kicker: "工具边界",
    title: "支持性工具，不替代现实帮助",
    subtitle: "安心陪伴只提供记录、复盘和练习建议。",
    sections: [
      {
        title: "非诊断边界",
        items: [
          "测评结果只作为自我观察和练习参考。",
          "阶段性画像只说明“当前更接近某类线索”，不是人格或疾病判断。",
        ],
      },
      {
        title: "紧急情况",
        items: [
          "如果你或孩子正在经历自伤、自杀、暴力、失控或其他安全风险，请先联系身边可信赖的人、当地紧急服务或线下专业机构。",
        ],
      },
    ],
  },
  about: {
    kicker: "关于",
    title: "安心陪伴",
    subtitle: "基于 UP 跨诊断情绪调节框架的家长非评判陪伴训练系统。",
    sections: [
      {
        title: "当前版本",
        items: [
          "当前为试点测试版，仍需人工验收量表、计分、边界文案和真机页面。",
        ],
      },
    ],
  },
};

const PRIVACY_STATUS_LABELS = {
  pending: "待处理",
  processing: "处理中",
  completed: "已完成",
  rejected: "未执行",
  cancelled: "已取消",
};

Page({
  data: {
    notice: NOTICE_MAP.boundary,
    noticeType: "boundary",
    privacyLoading: false,
    privacyError: "",
    privacyNeedsLogin: false,
    privacyRequests: [],
    privacySubmitting: false,
  },

  onLoad(options = {}) {
    const type = options.type || "boundary";
    this.setData({
      notice: NOTICE_MAP[type] || NOTICE_MAP.boundary,
      noticeType: type,
    });
  },

  onShow() {
    if (this.data.noticeType === "privacy") {
      this.loadPrivacyRequests();
    }
  },

  async loadPrivacyRequests() {
    this.setData({ privacyLoading: true, privacyError: "", privacyNeedsLogin: false });
    try {
      const result = await api.listPrivacyRequests({ page: 1, page_size: 50 });
      const items = (result.items || []).map((item) => ({
        ...item,
        statusLabel: PRIVACY_STATUS_LABELS[item.status] || item.status,
        canCancel: item.status === "pending",
        canAppeal: item.status === "rejected",
        createdDate: String(item.created_at || "").slice(0, 10),
        updatedDate: String(item.updated_at || "").slice(0, 10),
      }));
      this.setData({ privacyLoading: false, privacyRequests: items });
    } catch (error) {
      const privacyNeedsLogin = Boolean(error && (error.statusCode === 401 || error.status === 401 || error.code === "unauthorized" || error.code === "auth_required"));
      this.setData({
        privacyLoading: false,
        privacyNeedsLogin,
        privacyError: privacyNeedsLogin ? "登录后才能查看和管理自己的删除申请。" : (error.message || "删除申请暂时没有读取成功。"),
      });
    }
  },

  submitPrivacyDeleteRequest() {
    if (this.data.privacySubmitting) return;
    wx.showModal({
      title: "提交删除申请",
      content: "申请提交后不会立即删除数据，管理员或督导会先核对范围与保存规则。",
      editable: true,
      placeholderText: "可选：简要说明原因",
      confirmText: "提交申请",
      success: async (result) => {
        if (!result.confirm) return;
        this.setData({ privacySubmitting: true, privacyError: "" });
        try {
          const response = await api.createPrivacyDeleteRequest({ reason: String(result.content || "").trim() });
          wx.showToast({ title: response.already_active ? "已有申请处理中" : "申请已提交", icon: "none" });
          await this.loadPrivacyRequests();
        } catch (error) {
          this.setData({ privacyError: error.message || "申请没有提交成功，请稍后重试。" });
        } finally {
          this.setData({ privacySubmitting: false });
        }
      },
    });
  },

  cancelPrivacyRequest(event) {
    const requestId = event.currentTarget.dataset.id;
    if (!requestId || this.data.privacySubmitting) return;
    wx.showModal({
      title: "取消删除申请",
      content: "只可取消尚未开始处理的申请。",
      confirmText: "确认取消",
      success: async (result) => {
        if (!result.confirm) return;
        const idempotencyKey = `privacy-cancel-${requestId}-${Date.now()}`;
        this.setData({ privacySubmitting: true, privacyError: "" });
        try {
          await api.cancelPrivacyRequest(requestId, { reason: "参与者主动取消" }, idempotencyKey);
          wx.showToast({ title: "申请已取消", icon: "success" });
          await this.loadPrivacyRequests();
        } catch (error) {
          this.setData({ privacyError: error.message || "申请状态没有改变，请刷新后重试。" });
        } finally {
          this.setData({ privacySubmitting: false });
        }
      },
    });
  },

  appealPrivacyRequest(event) {
    const requestId = event.currentTarget.dataset.id;
    if (!requestId || this.data.privacySubmitting) return;
    wx.showModal({
      title: "补充说明后重新提交",
      content: "请说明希望继续核对的内容。内部处理备注不会在这里展示。",
      editable: true,
      placeholderText: "必填，不超过500字",
      confirmText: "重新提交",
      success: async (result) => {
        if (!result.confirm) return;
        const reason = String(result.content || "").trim();
        if (!reason) {
          this.setData({ privacyError: "请先填写补充说明。" });
          return;
        }
        this.setData({ privacySubmitting: true, privacyError: "" });
        try {
          await api.appealPrivacyRequest(requestId, { reason }, `privacy-appeal-${requestId}-${Date.now()}`);
          wx.showToast({ title: "已重新提交", icon: "success" });
          await this.loadPrivacyRequests();
        } catch (error) {
          this.setData({ privacyError: error.message || "暂时无法重新提交，请刷新后重试。" });
        } finally {
          this.setData({ privacySubmitting: false });
        }
      },
    });
  },

  handlePrivacyStateAction() {
    if (this.data.privacyNeedsLogin) {
      wx.navigateTo({ url: "/pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprivacy" });
      return;
    }
    this.loadPrivacyRequests();
  },

  goBack() {
    wx.navigateBack({ delta: 1 });
  },
});

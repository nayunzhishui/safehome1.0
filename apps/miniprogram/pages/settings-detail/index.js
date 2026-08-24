const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, isLoggedIn } = require("../../utils/authGuard");
const {
  bindStudent,
  confirmAge,
  createFamilyBindCode,
  getMinorSafeguardStatus,
  listFamilyMembers,
  updateChildAssent,
  updateGuardianConsent,
} = require("../../services/minorSafeguardsApi");

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
  protection: {
    kicker: "参与者保护",
    title: "年龄与监护人保护设置",
    subtitle: "学生先确认年龄范围；未满14周岁时，再分别完成监护人同意和学生本人确认。",
    sections: [
      {
        title: "最少收集",
        items: [
          "只记录“未满14周岁 / 已满14周岁”的年龄范围，不要求填写生日。",
          "年龄信息只用于保护门禁，不用于诊断、能力判断或人格标签。",
        ],
      },
      {
        title: "未满14周岁",
        items: [
          "先绑定家长账号，再由家长确认是否同意受保护的数据处理。",
          "监护人同意不能替代学生本人意愿；学生仍可拒绝或撤回。",
          "绑定关系本身不等于监护人已经同意敏感数据处理。",
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

function protectionStatusLabel(status) {
  const map = {
    age_verification_required: "待确认年龄",
    age_verified: "年龄已确认",
    guardian_link_required: "待绑定监护人",
    guardian_consent_required: "待监护人同意",
    child_assent_required: "待学生本人确认",
    active: "保护设置已完成",
    blocked_withdrawn_or_refused: "受保护功能已暂停",
    not_applicable: "无需此项保护",
  };
  return map[status] || status || "待确认";
}

Page({
  data: {
    notice: NOTICE_MAP.boundary,
    noticeType: "boundary",
    privacyLoading: false,
    privacyError: "",
    privacyNeedsLogin: false,
    privacyRequests: [],
    privacySubmitting: false,
    protectionLoading: false,
    protectionError: "",
    protectionNeedsLogin: false,
    protectionBusy: false,
    protectionRole: "",
    protectionStatus: null,
    guardianChildren: [],
    bindCodeInput: "",
    generatedBindCode: "",
    generatedBindExpiresAt: "",
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
    if (this.data.noticeType === "protection") {
      this.loadProtectionStatus();
    }
  },

  async loadProtectionStatus() {
    if (!isLoggedIn()) {
      this.setData({
        protectionLoading: false,
        protectionNeedsLogin: true,
        protectionError: "登录后才能确认年龄或管理未成年人保护设置。",
        protectionRole: "",
        protectionStatus: null,
        guardianChildren: [],
      });
      return;
    }
    const user = getAuthUser() || {};
    const role = user.role || "";
    this.setData({ protectionLoading: true, protectionNeedsLogin: false, protectionError: "", protectionRole: role });
    try {
      if (role === "student") {
        const status = await getMinorSafeguardStatus();
        this.setData({
          protectionLoading: false,
          protectionStatus: { ...status, statusLabel: protectionStatusLabel(status.status) },
          guardianChildren: [],
        });
        return;
      }
      if (role === "parent") {
        const family = await listFamilyMembers();
        const activeLinks = (family.items || []).filter((item) => item.status === "consumed" && item.student_user_id);
        const children = await Promise.all(
          activeLinks.map(async (link) => {
            try {
              const status = await getMinorSafeguardStatus(link.student_user_id);
              return {
                ...link,
                safeguard: { ...status, statusLabel: protectionStatusLabel(status.status) },
              };
            } catch (error) {
              return {
                ...link,
                safeguard: {
                  status: "unavailable",
                  statusLabel: "状态暂不可用",
                  errorMessage: error.message || "请稍后重试",
                },
              };
            }
          }),
        );
        this.setData({ protectionLoading: false, guardianChildren: children, protectionStatus: null });
        return;
      }
      this.setData({
        protectionLoading: false,
        protectionStatus: { status: "not_applicable", statusLabel: "当前后台角色不使用参与者保护设置" },
        guardianChildren: [],
      });
    } catch (error) {
      this.setData({ protectionLoading: false, protectionError: error.message || "参与者保护状态暂时没有读取成功。" });
    }
  },

  chooseAge(event) {
    if (this.data.protectionBusy) return;
    const ageBand = event.currentTarget.dataset.age;
    if (!ageBand) return;
    this.setData({ protectionBusy: true, protectionError: "" });
    confirmAge(ageBand)
      .then(() => this.loadProtectionStatus())
      .catch((error) => this.setData({ protectionError: error.message || "年龄确认没有完成。" }))
      .finally(() => this.setData({ protectionBusy: false }));
  },

  onBindCodeInput(event) {
    this.setData({ bindCodeInput: String(event.detail.value || "").replace(/\D/g, "").slice(0, 10) });
  },

  submitStudentBinding() {
    const bindCode = String(this.data.bindCodeInput || "").trim();
    if (bindCode.length !== 10 || this.data.protectionBusy) {
      this.setData({ protectionError: "请输入家长提供的10位绑定码。" });
      return;
    }
    this.setData({ protectionBusy: true, protectionError: "" });
    bindStudent(bindCode)
      .then(() => {
        this.setData({ bindCodeInput: "" });
        wx.showToast({ title: "已完成绑定", icon: "success" });
        return this.loadProtectionStatus();
      })
      .catch((error) => this.setData({ protectionError: error.message || "绑定没有完成，请检查绑定码。" }))
      .finally(() => this.setData({ protectionBusy: false }));
  },

  createGuardianBindCode() {
    if (this.data.protectionBusy) return;
    this.setData({ protectionBusy: true, protectionError: "" });
    createFamilyBindCode("家长")
      .then((result) => {
        this.setData({
          generatedBindCode: result.bind_code || "",
          generatedBindExpiresAt: result.expires_at || "",
        });
      })
      .catch((error) => this.setData({ protectionError: error.message || "绑定码暂时没有生成成功。" }))
      .finally(() => this.setData({ protectionBusy: false }));
  },

  updateGuardianDecision(event) {
    if (this.data.protectionBusy) return;
    const childUserId = event.currentTarget.dataset.child;
    const agreed = String(event.currentTarget.dataset.agreed) === "true";
    if (!childUserId) return;
    const actionText = agreed ? "同意" : "撤回同意";
    wx.showModal({
      title: `${actionText}受保护功能`,
      content: agreed
        ? "确认后，仍需要学生本人确认愿意继续；你的同意不能替代学生本人选择。"
        : "撤回后，测评、研究参与、自由文本和画像等受保护功能将停止。",
      confirmText: actionText,
      success: (result) => {
        if (!result.confirm) return;
        this.setData({ protectionBusy: true, protectionError: "" });
        updateGuardianConsent(childUserId, agreed)
          .then(() => this.loadProtectionStatus())
          .catch((error) => this.setData({ protectionError: error.message || "监护人确认没有完成。" }))
          .finally(() => this.setData({ protectionBusy: false }));
      },
    });
  },

  updateChildDecision(event) {
    if (this.data.protectionBusy) return;
    const assented = String(event.currentTarget.dataset.assented) === "true";
    wx.showModal({
      title: assented ? "确认继续" : "确认暂不继续",
      content: assented
        ? "确认后可以继续当前账号允许的受保护功能。"
        : "选择暂不继续后，测评、研究参与和画像等受保护功能会停止。",
      confirmText: assented ? "我愿意继续" : "暂不继续",
      success: (result) => {
        if (!result.confirm) return;
        this.setData({ protectionBusy: true, protectionError: "" });
        updateChildAssent(assented)
          .then(() => this.loadProtectionStatus())
          .catch((error) => this.setData({ protectionError: error.message || "本人确认没有完成。" }))
          .finally(() => this.setData({ protectionBusy: false }));
      },
    });
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

  goProtectionLogin() {
    wx.navigateTo({ url: "/pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprotection" });
  },

  goBack() {
    wx.navigateBack({ delta: 1 });
  },
});

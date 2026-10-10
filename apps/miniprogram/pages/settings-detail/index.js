const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, isLoggedIn, captureAuthSession, isCurrentAuthSession } = require("../../utils/authGuard");
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
    "kicker": "隐私说明",
    "title": "安心陪伴隐私政策",
    "version": "2026.10-privacy-v5",
    "status": "operator_details_required",
    "subtitle": "说明我们如何收集、使用和保护你的个人信息。",
    "sections": [
      {
        "title": "一、我们是谁、如何联系我们",
        "items": [
          "运营者：【上线前请填写：与小程序备案主体一致的全称】",
          "联系方式：【上线前请填写：可接收个人信息相关请求的邮箱或电话】",
          "我们安排专人负责个人信息保护事务。你可以通过上述方式提出查阅、复制、更正、删除、撤回同意等请求，我们会在核验身份后的15个工作日内答复。"
        ]
      },
      {
        "title": "二、本服务做什么、不做什么",
        "items": [
          "安心陪伴帮助家长记录具体的亲子互动事件，回看自己的感受，并获得支持性反馈和小练习；部分页面提供用于自我观察的测评。",
          "本服务不提供医疗诊断、心理治疗或危机干预。测评和反馈只供自我观察，不应用于诊断、人员筛选或给他人贴标签。",
          "人工支持不是实时服务。遇到紧急情况，请立即联系当地紧急服务（如110、120）或身边可信任的人。"
        ]
      },
      {
        "title": "三、我们收集哪些信息、为什么收集",
        "items": [
          "微信登录：用于识别你的账号。我们获取微信提供的用户标识，不会要求你提供微信密码。",
          "手机号快捷登录（可选）：只在你点击并同意微信授权后获取手机号，并且只保存用于识别账号的手机号摘要，不保存完整手机号。拒绝授权不影响其他登录方式。",
          "账号密码登录：我们只保存经过加密处理的密码校验信息，不保存密码原文。请不要在记录或说明中填写密码。",
          "你主动填写的内容：目标、亲子互动记录（场景、经过、情绪及强度、想法和做法等）、测评作答及结果、练习打卡、阶段复盘和人工支持说明。这些内容可能反映你和孩子的心理状况，属于敏感个人信息。我们会在你首次提交前单独征求同意，只用于保存和回看、生成支持性反馈与练习建议，以及在出现安全提示时由负责人员进行人工关注。",
          "人工支持中的联系方式（可选）：你自愿填写时，只用于负责人员处理该请求时与你联系；一般列表中只显示部分号码。请不要填写他人的联系方式。",
          "本机草稿：部分表单在你同意后，会把尚未提交的内容暂存在你的手机上，提交前不会上传；草稿按账号区分，提交成功后自动清除，你也可以在微信中清除本小程序的缓存来删除它们。",
          "运行与安全日志：为保障账号安全和排查故障，我们记录登录状态、请求时间、请求编号、错误码和同意版本等必要信息，不记录你填写的正文。",
          "剪切板：只有在你点击“复制”按钮时，我们才把页面上的错误编号写入剪切板；我们不会读取你的剪切板。",
          "订阅消息（可选）：只有在你同意某个提醒后，我们才会按该提醒发送微信通知；是否订阅不影响其他功能。",
          "请不要填写不必要的他人真实姓名、身份证号、学校班级、详细住址或联系方式，也不要未经同意提交他人的材料。"
        ]
      },
      {
        "title": "四、需要你另行同意的用途",
        "items": [
          "匿名研究、模型训练、关系分析和辅助分析等用途，需要你分别单独同意，默认不勾选。不同意不影响记录、反馈和练习等基础功能。",
          "你可以在“我的→隐私说明”中查看这些授权并随时撤回；撤回后不再按该授权处理新的数据，但不影响撤回前已经进行的处理。"
        ]
      },
      {
        "title": "五、我们如何委托处理和共享",
        "items": [
          "我们不会出售你的个人信息，也不会把你的记录用于广告营销。",
          "为提供服务，以下服务方会在必要范围内处理你的信息：",
          "腾讯云（微信云托管及云数据库）：服务运行和数据存储；",
          "微信（深圳市腾讯计算机系统有限公司）：微信登录、手机号授权和订阅消息。",
          "本服务目前没有接入任何外部人工智能模型服务。将来如需接入，我们会在使用前更新本政策并征求你的同意。",
          "除法律法规规定或有权机关依法要求外，我们不会向其他第三方提供你的个人信息。"
        ]
      },
      {
        "title": "六、保存期限与删除",
        "items": [
          "我们只在实现上述目的所必需的期间保存你的信息。在你使用本服务期间，记录会一直保存，便于你回看。",
          "你可以在“我的→隐私说明”中提交删除申请并查看处理状态。核验后，我们会删除或匿名化你的个人信息，法律法规要求保留的最少记录除外，例如依据《网络安全法》留存不少于六个月的安全日志。",
          "删除后，备份中的数据会在备份周期结束后被覆盖，在此期间不会用于任何业务。",
          "退出登录、清除小程序缓存和删除服务器上的数据是三件不同的事，请按需要分别操作。"
        ]
      },
      {
        "title": "七、未成年人保护",
        "items": [
          "本服务主要面向家长，部分学生功能面向在校学生。",
          "不满14周岁的学生，需要监护人关联账号并同意后才能使用受保护的功能；孩子本人可以拒绝或随时撤回，监护人的同意不能代替孩子的拒绝。",
          "我们只保存执行年龄保护所需的年龄区间，不收集出生日期。监护人可以通过第一部分的联系方式查阅、更正或删除孩子的信息。"
        ]
      },
      {
        "title": "八、我们如何保护你的信息",
        "items": [
          "我们采取身份验证、按角色和记录范围授权、操作审计和数据备份等措施；后台查看和研究导出受权限和用途限制，导出默认去除可识别信息。",
          "小程序与服务之间的通信经由微信云托管提供的通道传输。",
          "任何安全措施都不能保证绝对安全。如果发生个人信息安全事件，我们会按法律要求及时告知你并采取补救措施。"
        ]
      },
      {
        "title": "九、你的权利",
        "items": [
          "查阅和复制：你可以在小程序中查看自己的记录；需要副本时请通过第一部分的联系方式申请。",
          "更正：发现信息有误时，可以通过第一部分的联系方式申请更正。",
          "撤回同意：在“我的→隐私说明”中撤回可选用途的授权。",
          "删除与注销：在“我的→隐私说明”中提交删除申请；注销账号请通过第一部分的联系方式申请。"
        ]
      },
      {
        "title": "十、本政策的更新",
        "items": [
          "本政策更新时，我们会在小程序内提示。涉及收集范围、使用目的或共享对象的重要变化，我们会再次征求你的同意。"
        ]
      }
    ]
  },
  agreement: {
    "kicker": "用户协议",
    "title": "安心陪伴用户服务协议",
    "subtitle": "请在使用前阅读；勾选同意后再登录或注册。",
    "sections": [
      {
        "title": "一、协议双方",
        "items": [
          "本协议是你与安心陪伴运营者之间关于使用本小程序的约定。运营者的名称和联系方式见《隐私政策》第一部分。",
          "你在登录或注册时勾选同意，即表示已阅读并同意本协议和《隐私政策》。"
        ]
      },
      {
        "title": "二、服务内容",
        "items": [
          "本服务帮助家长记录亲子互动事件、回看感受，并提供支持性反馈、练习建议和用于自我观察的测评。具体功能以页面实际开放为准。",
          "本服务不提供医疗诊断、心理治疗或危机干预，测评和反馈结果不能代替专业意见。",
          "人工支持不是实时服务，不承诺即时回复。"
        ]
      },
      {
        "title": "三、账号",
        "items": [
          "你可以使用微信、手机号或账号密码登录。请妥善保管账号和密码，不要转借他人使用。",
          "不满14周岁的学生需要在监护人同意后使用受保护的功能。",
          "发现账号被他人使用时，请及时通过《隐私政策》中的联系方式告知我们。"
        ]
      },
      {
        "title": "四、你的内容",
        "items": [
          "你填写的记录和作答归你所有。你授权我们在提供本服务所必需的范围内保存和处理这些内容，具体规则见《隐私政策》。",
          "请只填写与你和孩子有关、并且你有权提供的内容；不要发布违法、侵权、侮辱他人或泄露他人隐私的内容。"
        ]
      },
      {
        "title": "五、安全提示",
        "items": [
          "当你或他人可能面临伤害时，请立即联系当地紧急服务（如110、120）或身边可信任的人，不要只依赖本小程序。",
          "系统可能对出现安全提示的内容进行人工关注，但这不是紧急救助服务。"
        ]
      },
      {
        "title": "六、内容与知识产权",
        "items": [
          "小程序中的训练卡、课程和说明文字的权利归运营者或原权利人所有，仅供你个人学习使用，未经许可不得复制或用于商业用途。"
        ]
      },
      {
        "title": "七、责任说明",
        "items": [
          "我们会尽力保证服务稳定，但服务可能因维护、网络或不可抗力暂时中断。",
          "测评、反馈和练习建议只供自我观察参考，请结合实际情况判断，必要时寻求专业帮助。"
        ]
      },
      {
        "title": "八、协议的变更与终止",
        "items": [
          "本协议更新时，我们会在小程序内提示；重要变化会请你重新确认。",
          "你可以随时停止使用本服务，并按《隐私政策》申请删除个人信息或注销账号。",
          "违反本协议或法律法规的，我们可以限制或停止提供相应服务。"
        ]
      },
      {
        "title": "九、其他",
        "items": [
          "本协议适用中华人民共和国法律。"
        ]
      }
    ]
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
          "年龄信息只用于未成年人保护，不用于诊断、能力判断或人格标签。",
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
    subtitle: "参考情绪调节统一方案（UP）设计的家长陪伴练习工具。",
    sections: [
      {
        title: "当前版本",
        items: [
          "当前为试点版本，我们会根据使用反馈持续改进。",
        ],
      },
    ],
  },
};

const OPTIONAL_CONSENT_LABELS = {
  research_authorization: "研究用途", anonymous_research: "去标识化研究",
  quality_evaluation: "质量评估", model_training: "模型训练", ai_assistance: "AI辅助",
  relationship_analysis: "关系分析", secondary_research: "后续研究",
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
    consentDecisions: [],
    consentLoading: false,
    consentError: "",
    consentBusy: false,
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
    this._hidden = false;
    if (this._readSession && !isCurrentAuthSession(this._readSession)) this.setData({ consentDecisions: [], privacyRequests: [], protectionStatus: null, guardianChildren: [], generatedBindCode: "", bindCodeInput: "" });
    if (this.data.noticeType === "privacy") {
      this.loadPrivacyRequests();
      this.loadConsentDecisions();
    }
    if (this.data.noticeType === "protection") {
      this.loadProtectionStatus();
    }
  },

  onHide() { this._hidden = true; },
  onUnload() { this._consentDisposed = true; this._hidden = true; },

  async loadProtectionStatus() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._protectionRequestId = (this._protectionRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._protectionRequestId && isCurrentAuthSession(session);
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
      if (!isCurrent()) return;
        this.setData({
          protectionLoading: false,
          protectionStatus: { ...status, statusLabel: protectionStatusLabel(status.status) },
          guardianChildren: [],
        });
        return;
      }
      if (role === "parent") {
        const family = await listFamilyMembers();
      if (!isCurrent()) return;
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
      if (!isCurrent()) return;
        this.setData({ protectionLoading: false, guardianChildren: children, protectionStatus: null });
        return;
      }
      this.setData({
        protectionLoading: false,
        protectionStatus: { status: "not_applicable", statusLabel: "当前后台角色不使用参与者保护设置" },
        guardianChildren: [],
      });
    } catch (error) {
      if (!isCurrent()) return;
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

  async loadConsentDecisions() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._consentRequestId = (this._consentRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._consentRequestId && isCurrentAuthSession(session);
    this.setData({ consentLoading: true, consentError: "", consentDecisions: [] });
    try {
      const result = await api.listConsentRecords();
      if (!isCurrent()) return;
      const latest = new Map();
      const ordered = (result.items || []).slice().sort((a, b) =>
        Number(b.event_version || 0) - Number(a.event_version || 0)
        || String(b.created_at || "").localeCompare(String(a.created_at || ""))
        || String(b.id || "").localeCompare(String(a.id || "")));
      ordered.forEach((item) => {
        if (OPTIONAL_CONSENT_LABELS[item.consent_type] && !latest.has(item.consent_type)) latest.set(item.consent_type, item);
      });
      const consentDecisions = Array.from(latest.values()).map((item) => ({
        ...item, label: OPTIONAL_CONSENT_LABELS[item.consent_type], agreed: item.agreed === true || item.agreed === 1,
      }));
      this.setData({ consentLoading: false, consentDecisions });
    } catch (error) {
      if (!isCurrent()) return;
      this.setData({ consentLoading: false, consentError: error.message || "用途决定暂时没有读取成功，请登录或重试。" });
    }
  },

  withdrawOptionalConsent(event) {
    if (this.data.consentBusy) return;
    const item = this.data.consentDecisions.find((entry) => entry.id === event.currentTarget.dataset.id);
    if (!item || !item.agreed) return;
    wx.showModal({
      title: `撤回${item.label}`,
      content: "这会记录你对这一用途的撤回决定，不等于立即删除全部历史数据。历史资料与衍生制品的处理可通过隐私请求跟进。",
      confirmText: "确认撤回",
      success: (result) => {
        if (!result.confirm) return;
        this.setData({ consentBusy: true, consentError: "" });
        api.createConsent({
          consent_type: item.consent_type, consent_version: item.consent_version,
          agreed: false, purpose: item.purpose || item.consent_type, processor: item.processor || "safehome",
          text_hash: item.text_hash || null, expected_latest_id: item.id,
        }).then(() => this.loadConsentDecisions())
          .catch((error) => this.setData({ consentError: error.message || "撤回没有完成，请刷新后重试。" }))
          .finally(() => this.setData({ consentBusy: false }));
      },
    });
  },

  async loadPrivacyRequests() {
    const session = captureAuthSession();
    this._readSession = session;
    const requestId = this._privacyRequestId = (this._privacyRequestId || 0) + 1;
    const isCurrent = () => !this._hidden && !this._consentDisposed && requestId === this._privacyRequestId && isCurrentAuthSession(session);
    this.setData({ privacyLoading: true, privacyError: "", privacyNeedsLogin: false });
    try {
      const result = await api.listPrivacyRequests({ page: 1, page_size: 50 });
      if (!isCurrent()) return;
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
      if (!isCurrent()) return;
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

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
  "version": "2026.10-privacy-v4-draft",
  "status": "draft",
  "sections": [
    {
      "title": "版本与适用范围",
      "items": [
        "版本：2026.10-privacy-v4-draft",
        "本稿已按实际功能整理；标为[待填写]的主体与期限信息须由负责人补齐核定后用于正式对外发布。"
      ]
    },
    {
      "title": "一、运营主体与联系",
      "items": [
        "运营主体：[待填写：与小程序登记主体一致的全称]",
        "隐私联系渠道：[待填写：实际可接收隐私申请的邮箱或电话]",
        "隐私事务负责角色：[待填写：实际负责团队或岗位]",
        "申请响应时限：[待填写：经负责人确认并能够履行的响应时限]",
        "小程序内隐私入口支持提交和查看删除申请；查阅、更正或其他隐私事务请使用上方联系渠道。联系渠道、处理主体发生变化时，将更新本政策并说明影响；不使用源码文件路径代替用户可阅读的政策。"
      ]
    },
    {
      "title": "二、适用范围与服务边界",
      "items": [
        "安心陪伴用于记录具体亲子互动事件、回看感受并提供支持性反馈与陪伴练习。测评、训练及项目以页面实际开放范围为准。",
        "临时开放不代表内容已完成版权、专业或伦理审核；不得把自我观察结果用于临床诊断、治疗、人员筛选或给他人贴标签。",
        "系统不提供紧急救助。人工支持请求不是实时服务，不承诺即时回应。",
        "研究、模型训练、关系分析和辅助模型处理须独立授权，不能由基础使用同意或浏览教程代替。"
      ]
    },
    {
      "title": "三、账号与登录信息",
      "items": [
        "微信登录用于识别账号，并把记录关联到本人。我们不要求你提供微信账号密码。",
        "手机号快捷登录只在你主动触发微信授权后进行。该登录/绑定流程在服务端保存用于账号识别的手机号摘要，不将完整手机号作为该流程的持久登录标识保存。",
        "你可以选择其他实际可用的登录方式；拒绝手机号授权不自动关闭其他登录方式。我们不会把手机号登录的授权扩展到联系、营销或研究用途。",
        "使用账号密码登录时，系统核验并安全保存密码校验信息；请勿在日记、草稿或人工支持说明中填写密码。"
      ]
    },
    {
      "title": "四、记录、测评与练习数据",
      "items": [
        "按你选择的功能，我们处理目标、具体事件、情绪与回应、测评作答和结果、练习及打卡、阶段复盘等内容，用于保存、回看及相应支持性反馈。按当前功能另行处理情绪温度计、目标、消息、项目材料及必要的同意、保护和访问审计记录。",
        "这些记录与账号关联，不属于完全匿名数据。后台查看、研究导出和人工复核受角色、对象范围及用途授权限制。",
        "请勿填写不必要的他人真实姓名、身份证号、学校班级、详细住址或联系方式。不要未经授权提交他人材料。"
      ]
    },
    {
      "title": "五、本机草稿",
      "items": [
        "部分表单会在说明用途并取得同意后，将未提交内容保存到当前设备，以便继续填写。提交前，本机草稿正文不会因草稿功能而自动发送服务器。",
        "草稿按账号区分。无法可靠确认所属账号的旧草稿不会自动恢复或自动归属给另一账号。",
        "退出登录不等于删除本机草稿或服务器数据。你可按微信提供的小程序缓存清理方式清除设备端数据；清理前应确认不再需要未提交内容。",
        "本机草稿保存规则：[待填写：设备端保留或主动清理规则及适用范围]"
      ]
    },
    {
      "title": "六、人工支持与联系方式",
      "items": [
        "你主动提交人工支持请求时，填写的说明及选择关联的记录将用于负责人员补充理解，并在授权范围内提供给他们。",
        "人工支持页面的联系方式字段为可选。若你主动填写，系统会另行保存该联系方式，并允许具有相应权限的负责人员在处理该请求时查看；普通列表仅展示掩码。",
        "这与“手机号登录只保存摘要”是两条不同的数据处理流程。请只填实际需要使用的联系渠道，不填他人的联系方式。",
        "人工支持信息与联系方式的保存期限：[待填写：期限、起算点及完成请求后的处理规则]"
      ]
    },
    {
      "title": "七、关系材料、研究与辅助分析",
      "items": [
        "关系项目、绘画、叙事和协作理解材料可能包含敏感信息。提交前须明确当前材料用途、授权对象和独立同意；他人的同意不能由你代替。",
        "可选研究、模型训练和辅助分析分别征求同意；拒绝可选用途不影响已经开放的基础功能。",
        "真实参与者原文不会因选择普通记录功能而自动进入通用模型训练。未开放外部模型服务时，不以隐私条款表示其已经开放；开放第三方处理前须核对实际处理者、用途和规则，并完成必要告知和授权。",
        "涉及未成年人的受保护功能仍遵守原有监护与本人意愿流程，临时开放开关不替代这些保护。"
      ]
    },
    {
      "title": "八、消息、日志与服务提供方",
      "items": [
        "站内消息用于服务内通知；微信订阅消息另由你按实际模板主动授权，不把订阅作为研究同意或以奖励强迫订阅。",
        "为身份核验、错误排查及安全审计，我们处理必要的登录状态、时间、请求标识、错误码和同意版本等元数据，不将原文或密钥写入普通诊断日志。",
        "后端采用微信云托管及相应云数据库基础设施。其他实际接入的处理者及其信息范围，应在使用前据实披露。",
        "第三方处理清单：[待填写：实际使用的处理者/服务、数据类型、目的及相应政策位置]"
      ]
    },
    {
      "title": "九、保存期限",
      "items": [
        "账号及业务记录：[待填写：具体期限或可执行的判定标准、起算条件]",
        "必要安全与审计记录：[待填写：具体期限及适用依据]",
        "备份数据：[待填写：备份保留周期及删除后备份处理方式]",
        "达到保存目的、期限届满或申请经核验应执行时，按实际批准规则处理；不能无限期以“研究需要”保留所有原文。",
        "依法确须保留的最少记录应与普通内容区分，并说明范围与依据。工程草案中的保留策略不是已生效的法律或研究批准。"
      ]
    },
    {
      "title": "十、查阅、更正、撤回与删除",
      "items": [
        "在“我的→隐私说明”中可以查看并撤回可选用途授权、提交和查看删除申请；查阅、更正及尚无直接页面入口的其他请求，请使用本政策列明的联系渠道。涉及监护同意与本人意愿的选择仍在保护设置中操作。处理前可能核验账号及范围，并提供处理状态。",
        "提交删除申请不等于立即删除完毕；部分完成、失败或需要补充信息时，会明确反馈，不把收到申请写成已完成。",
        "撤回某项可选授权后，不再按该授权继续处理后续数据；历史数据、未发布衍生材料及依法须保留的最少记录按相应规则处理。",
        "本机清缓存、退出账号和删除服务器数据不是同一操作。"
      ]
    },
    {
      "title": "十一、安全措施",
      "items": [
        "工程实现包含身份核验、权限控制、审计和备份恢复能力；真实部署链路、安全配置和演练证据须在发布前核对，不据此承诺绝对安全。",
        "数据库与网络链路的实际传输保护范围：[待填写：真实部署及已批准例外的范围和依据]。不将当前代码或历史部署记录写成所有链路均已验证。",
        "我们不公开密钥、内部地址或数据库账号密码。任何措施均不应被描述为绝对安全或永不泄露。"
      ]
    },
    {
      "title": "十二、政策更新",
      "items": [
        "收集范围、处理目的、接收方或其他重要事项变化时，将更新政策并按实际影响再次告知或征求同意。",
        "本政策版本、微信平台隐私指引、页面功能说明和真实程序行为应保持一致。负责人完成待填信息后，须同步正文与小程序展示内容，再更新正式发布包。"
      ]
    }
  ],
  "subtitle": "请阅读实际数据用途；待填写的信息尚未确认。"
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

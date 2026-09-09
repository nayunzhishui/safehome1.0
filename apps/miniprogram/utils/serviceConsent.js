const VERSION = "2026.09.08-service-notice-v1";
const LOCAL_NOTICE_KEY = "safehome:serviceNotice:v1";
const PURPOSES = {
  diary: { title: "情绪记录使用说明", purpose: "diary_record", text: "你填写的事件、感受、身体感觉和回应将与登录账号关联，用于保存记录、生成支持性反馈与练习建议。草稿可能保存在本机。请勿填写他人的真实姓名、学校班级、详细住址或联系方式。" },
  assessment: { title: "支持性测评知情说明", purpose: "supportive_assessment", text: "作答和结果将与登录账号关联，用于生成及回看本次支持性测评结果。结果仅提供阶段性观察线索，不作诊断、标签或排名。草稿可能保存在本机。具体适用范围请阅读当前测评说明。" },
  goal: { title: "目标记录知情说明", purpose: "practice_goal", text: "你的练习目标、场景与动机将保存到账号，用于练习追踪与回看；不要填写他人身份信息。" },
  checkin: { title: "练习打卡知情说明", purpose: "practice_checkin", text: "本次练习、完成情况和感受将保存到账号，用于练习追踪和阶段复盘，不用于诊断或排名。" },
  thermometer: { title: "情绪温度计知情说明", purpose: "emotion_thermometer", text: "你的情绪强度、记录时间与补充内容将保存到账号，用于回看自己的变化。这是自我观察记录，不是诊断结果。" },
  supervision: { title: "人工支持知情说明", purpose: "human_support_request", text: "你主动提交的说明及关联记录将用于人工补充理解，并按授权提供给负责人员。这里不是实时危机服务，请不要填写不必要的身份信息。" },
  relationship: { title: "关系项目参与知情说明", purpose: "relationship_participation", text: "报名与作答将按项目说明保存到账号，用于你选择的关系项目。仍须符合当前项目的年龄、同意与开放条件；本确认不替代监护同意、项目研究同意或其他人的授权。" },
  program: { title: "项目记录知情说明", purpose: "program_entry", text: "你提交的书写、反思和练习感受将保存到当前项目，用于过程复盘、训练建议及必要的人工支持。项目有单独参与条件时，仍需完成原有确认。" },
};
const BOUNDARY = "研究、模型训练、AI辅助和关系分析须另行授权，不因点击本按钮一并同意；拒绝可选授权不影响已开放的基础功能。可在隐私中心查看授权、撤回与删除申请。系统不替代诊断、治疗或紧急救助。";
function hasLocalNotice() { return wx.getStorageSync(LOCAL_NOTICE_KEY) === VERSION; }
function acceptLocalNotice() { wx.setStorageSync(LOCAL_NOTICE_KEY, VERSION); }
function latest(items, type) {
  return items.filter(item => item.consent_type === type).sort((a, b) => Number(b.event_version || 0) - Number(a.event_version || 0) || String(b.created_at || "").localeCompare(String(a.created_at || "")))[0];
}
function agreed(item) { return !!item && (item.agreed === true || item.agreed === 1); }
async function ensureServiceConsent(page, api, feature, native = false) {
  const notice = PURPOSES[feature];
  if (!hasLocalNotice()) throw new Error("请先返回首页阅读并同意隐私与基础使用说明，再使用本功能。");
  if (!notice) throw new Error("缺少对应功能的知情说明。");
  if (page._consentPending) throw new Error("请先完成当前知情确认。");
  const userId = (wx.getStorageSync("auth_user") || {}).id;
  if (!userId) throw new Error("请先登录，再确认本人的知情选择。");
  const ensureSameUser = () => {
    if (page._consentDisposed) throw new Error("页面已关闭，请重新进入后确认。");
    if (typeof getCurrentPages === "function") {
      const pages = getCurrentPages();
      if (pages.length && pages[pages.length - 1] !== page) throw new Error("页面已切换，请回到原页面重新确认。");
    }
    if ((wx.getStorageSync("auth_user") || {}).id !== userId) throw new Error("账号已变化，请重新打开页面确认。");
  };
  page._consentPending = true;
  try {
    // A local acknowledgement cannot stand in for the current WeChat decision.
    await new Promise((resolve, reject) => {
      if (!wx.getPrivacySetting) { reject(new Error("当前微信版本无法确认隐私状态，请更新微信后返回首页重试。")); return; }
      wx.getPrivacySetting({
        success: result => result.needAuthorization
          ? reject(new Error("请先返回首页完成微信隐私授权，再使用本功能。"))
          : resolve(),
        fail: () => reject(new Error("微信隐私状态暂时无法确认，请稍后重试。")),
      });
    });
    ensureSameUser();
    const payload = await api.listConsentRecords(); ensureSameUser();
    const items = payload.items || [];
    const current = latest(items, "service_data");
    // A new feature gets a separate explicit event. A newer withdrawal must
    // never be bypassed by an older local acknowledgement or another account.
    const withdrawal = Math.max(0, ...items.filter(item => item.consent_type === "service_data" && !agreed(item)).map(item => Number(item.event_version || 0)));
    const matching = items.find(item => item.consent_type === "service_data" && agreed(item) && item.consent_version === VERSION && item.purpose === notice.purpose && Number(item.event_version || 0) > withdrawal);
    if (agreed(current) && matching) return true;
    const accepted = await new Promise(resolve => {
      page._resolveServiceConsent = resolve;
      if (native) {
        wx.showModal({ title: notice.title, content: notice.text + "\n\n" + BOUNDARY, confirmText: "同意继续", cancelText: "暂不同意", success: result => resolve(result.confirm === true), fail: () => resolve(false) });
      } else {
        page.setData({ serviceConsent: { ...notice, boundary: BOUNDARY } });
      }
    });
    ensureSameUser();
    if (!accepted) return false;
    await api.createConsent({ consent_type: "service_data", agreed: true, consent_version: VERSION, purpose: notice.purpose, reason: notice.title, expected_latest_id: current ? current.id : undefined });
    ensureSameUser();
    return true;
  } finally { page._consentPending = false; page._resolveServiceConsent = null; }
}
function finishServiceConsent(page, accepted) {
  const resolve = page._resolveServiceConsent;
  page.setData({ serviceConsent: null });
  if (resolve) resolve(accepted);
}
module.exports = { VERSION, BOUNDARY, hasLocalNotice, acceptLocalNotice, latest, agreed, ensureServiceConsent, finishServiceConsent };

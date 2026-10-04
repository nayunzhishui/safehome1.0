// Targeted frontend regression checks; no live API calls or user data.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '../../../..');
const MINI = path.join(ROOT, 'apps/miniprogram');
const read = (file) => fs.readFileSync(path.join(MINI, file), 'utf8');

function pageHarness(route, api = {}) {
  let definition;
  const writes = [];
  const removed = [];
  const storage = new Map();
  const navigation = [];
  const directory = path.join(MINI, 'pages', route);
  const context = {
    cloudConfig: { useLocalHttp: false },
    Page(value) { definition = value; },
    require(name) {
      if (name === '../../services/api') return { createSafeHomeApi: () => api };
      if (name === '../../services/cloudConfig') return { getCloudConfig: () => context.cloudConfig };
      if (name === '../../utils/authGuard') {
        const mod = { exports: {} };
        vm.runInNewContext(read('utils/authGuard.js'), { module: mod, wx: context.wx, setTimeout: context.setTimeout });
        return { ...mod.exports, requireLogin: () => true };
      }
      return require(path.resolve(directory, name));
    },
    wx: {
      setStorageSync: (key, value) => { writes.push({ key, value }); storage.set(key, value); },
      removeStorageSync: (key) => { removed.push(key); storage.delete(key); },
      getStorageSync: (key) => storage.get(key),
      showToast() {},
      navigateTo: (value) => navigation.push(value),
      switchTab: (value) => navigation.push(value),
      navigateBack: (value) => navigation.push(value),
    },
    setTimeout: () => 1,
    clearTimeout() {},
    console,
  };
  vm.runInNewContext(read(`pages/${route}/index.js`), context);
  const page = { ...definition, data: JSON.parse(JSON.stringify(definition.data)) };
  page.setData = function setData(patch, callback) {
    for (const [key, value] of Object.entries(patch)) {
      const parts = key.replace(/\[(\d+)\]/g, '.$1').split('.');
      let owner = this.data;
      for (const part of parts.slice(0, -1)) owner = owner[part];
      owner[parts.at(-1)] = value;
    }
    if (callback) callback();
  };
  return { page, writes, removed, storage, navigation, context };
}

function resultHarness(scores, category = '量表') {
  const api = {
    getAssessmentResult: async () => ({ id: 'synthetic-result', category, scores_json: JSON.stringify(scores) }),
    getAssessment: async () => ({
      id: 'synthetic-worksheet',
      training_recommendation_rules: [{ recommended_card_ids: ['synthetic-card'], today_suggestion: '暂停片刻', long_term_suggestion: '回看记录' }],
    }),
    listCards: async () => ({ items: [{ id: 'synthetic-card', title: '合成练习', purpose: '测试推荐分支' }] }),
    getAssessmentExploratoryAnalysis: async () => null,
    getAssessmentProfilePosition: async () => null,
  };
  const harness = pageHarness('assessment-result', api);
  harness.page.data.resultId = 'synthetic-result';
  harness.page.data.worksheetId = 'synthetic-worksheet';
  harness.page.drawProfilePositionCharts = () => {};
  harness.page.drawScaleDimensionChart = () => {};
  return harness;
}

test('登录按后端CloudBase身份模式请求，不额外依赖wx.login', async () => {
  const sent = []; let completed = 0;
  const h = pageHarness('login', {
    getAuthCapabilities: async () => ({ wechat_login: { available: true, mode: 'cloudbase_identity' }, phone_login: { available: false } }),
    wechatLogin: async data => { sent.push(data); return { token: 'synthetic', user: { role: 'parent' } }; },
  });
  h.page.completeLogin = () => { completed += 1; };
  h.page.loadAuthCapabilities(); await Promise.resolve();
  h.page.submitWechatLogin(); await new Promise(setImmediate);
  assert.equal(sent.length, 1); assert.deepEqual(JSON.parse(JSON.stringify(sent[0])), {});
  assert.equal(completed, 1); assert.equal(h.page.data.wechatLoading, false);
});

test('登录在本地HTTP仍使用微信code兑换', async () => {
  let received;
  const h = pageHarness('login', { wechatLogin: async data => { received = data; return {}; } });
  h.context.cloudConfig.useLocalHttp = true;
  h.page.data.wechatMode = 'cloudbase_identity';
  h.context.wx.login = options => options.success({ code: 'synthetic-code' });
  h.page.completeLogin = () => {};
  h.page.submitWechatLogin(); await new Promise(setImmediate);
  assert.equal(received.code, 'synthetic-code');
});

test('登录请求进行中忽略重复及其他方式的登录事件', () => {
  let accountRequests = 0; let wechatRequests = 0; let phoneRequests = 0;
  const h = pageHarness('login', {
    login: () => { accountRequests += 1; return new Promise(() => {}); },
    phoneLogin: () => { phoneRequests += 1; return Promise.resolve({}); },
  });
  h.context.wx.login = () => { wechatRequests += 1; };
  h.page.data.username = 'synthetic'; h.page.data.password = 'synthetic-not-a-secret';
  h.page.submitLogin(); h.page.submitLogin(); h.page.submitWechatLogin();
  h.page.handlePhoneLogin({ detail: { code: 'synthetic-code' } });
  assert.equal(accountRequests, 1); assert.equal(wechatRequests, 0); assert.equal(phoneRequests, 0);
});

test('登录手机号说明区分登录摘要与人工支持联系方式', () => {
  const text = read('pages/login/index.wxml');
  assert.ok(text.includes('该授权流程')); assert.ok(text.includes('人工支持'));
  assert.ok(!text.includes('不可逆摘要'));
});

for (const [name, scores, category] of [
  ['普通量表高风险', { risk: { risk_level: 'high' } }, '量表'],
  ['学生画像高风险且旧数据允许自动反馈', { risk_level: 'high', allow_auto_feedback: true }, '学生画像'],
  ['学生画像明确禁止自动反馈', { risk_level: 'low', allow_auto_feedback: false }, '学生画像'],
]) {
  test(`${name}不展示、不缓存普通推荐，也不跳转普通训练`, async () => {
    const h = resultHarness(scores, category);
    h.storage.set('safehome:latestTrainingRecommendation', { sourceType: 'diary', cardIds: ['old-card'] });
    h.storage.set('safehome:threeDayLightPlan', { days: [{ cardId: 'old-card' }] });
    h.storage.set('safehome:resilientDraft:diary:general', { text: '保留原始草稿' });
    await h.page.loadResult();
    assert.equal(h.page.data.errorMessage, '');
    assert.equal(h.page.data.trainingRecommendation, null);
    assert.equal(h.writes.length, 0);
    assert.equal(h.storage.has('safehome:latestTrainingRecommendation'), false);
    assert.equal(h.storage.has('safehome:threeDayLightPlan'), false);
    assert.equal(h.storage.has('safehome:resilientDraft:diary:general'), true);
    h.page.openRecommendedCards();
    assert.equal(h.navigation.length, 0);
  });
}

test('普通低风险结果保留已有推荐缓存与训练跳转', async () => {
  const h = resultHarness({ risk: { risk_level: 'low' } });
  await h.page.loadResult();
  assert.equal(h.page.data.errorMessage, '');
  assert.equal(h.page.data.trainingRecommendation.cardIds[0], 'synthetic-card');
  assert.ok(h.writes.some((item) => item.key === 'safehome:latestTrainingRecommendation'));
  h.page.openRecommendedCards();
  assert.match(h.navigation[0].url, /card_ids=synthetic-card/);
});

test('日记历史区分强度0与未填写，不改变原记录', () => {
  const { context } = pageHarness('diary-history');
  for (const value of [0, '0', 5, 10]) {
    context.sample = { id: 'synthetic', parent_emotion_intensity: value };
    const formatted = vm.runInNewContext('formatRecord(sample)', context);
    assert.equal(formatted.intensityText, `强度 ${Number(value)}/10`);
    assert.equal(formatted.intensityMarks.filter((item) => item.active).length, Number(value));
    assert.equal(context.sample.parent_emotion_intensity, value);
  }
  for (const value of [null, undefined, '', 'not-a-number']) {
    context.sample = { parent_emotion_intensity: value };
    assert.equal(vm.runInNewContext('formatRecord(sample).intensityText', context), '强度待补充');
  }
});

test('真实九级题目选择保留value、score和题目顺序', () => {
  const source = JSON.parse(fs.readFileSync(path.join(ROOT, 'content/assessment_worksheets.json'), 'utf8'));
  const worksheet = source.worksheets.find((item) => item.questions.some((q) => q.options?.length === 9));
  const { page, context } = pageHarness('assessment-detail');
  context.worksheetFixture = worksheet;
  page.data.worksheet = vm.runInNewContext('withAnswerState(worksheetFixture)', context);
  const qi = worksheet.questions.findIndex((q) => q.options?.length === 9);
  for (const option of worksheet.questions[qi].options) {
    page.selectOption({ currentTarget: { dataset: { index: qi, value: option.value, score: option.score } } });
    const answer = page.buildAnswers()[qi];
    assert.equal(answer.question_id, worksheet.questions[qi].id);
    assert.equal(answer.value, String(option.value));
    assert.equal(answer.score, option.score);
  }
});

test('测评历史加载更多使用真实页码而不是重新读取第一页', async () => {
  const requests = [];
  const { page } = pageHarness('assessment-history', {
    listAssessmentResults: async (params) => {
      requests.push(params);
      return { items: [{ id: 'synthetic-next', worksheet_title: '合成记录' }], page: 2, total: 2, has_more: false };
    },
  });
  page.data.items = [{ id: 'synthetic-first' }];
  page.data.hasMore = true;
  await page.loadPage(2);
  assert.equal(requests[0].page, 2);
  assert.equal(page.data.items.length, 2);
  assert.equal(page.data.hasMore, false);
});

test('新手说明入口只做导航，暂不使用不提交同意记录', () => {
  const guide = read('pages/getting-started/index.wxml');
  for (const type of ['consent', 'privacy', 'protection']) {
    assert.ok(guide.includes(`/pages/settings-detail/index?type=${type}`));
  }
  assert.ok(guide.includes('查看说明不会自动记录同意'));
  const boundary = read('components/boundary-note/index.wxml');
  assert.match(boundary, /<navigator wx:if="{{!consented && !sending}}"[^>]*open-type="navigateBack"[^>]*>暂不使用，返回<\/navigator>/);
  assert.doesNotMatch(read('pages/getting-started/index.js'), /createConsent/);
});

test('结果页保留来源与高风险入口条件；空表登录恢复可达', () => {
  const result = read('pages/assessment-result/index.wxml');
  assert.ok(result.includes('sourceNotice.content'));
  assert.ok(result.includes("(!riskSummary || riskSummary.riskLevel !== 'high')"));
  const form = read('pages/assessment-detail/index.wxml');
  assert.match(form, /<view wx:else class="state-box error">[\s\S]*?wx:if="{{needsLogin}}"[\s\S]*?bindtap="goLogin"/);
});

test('高风险即时反馈先展示现实支持，不展示普通互动练习位置', () => {
  const markup = read('pages/feedback-result/index.wxml');
  assert.ok(markup.indexOf('wx:if="{{isHighRisk}}"') < markup.indexOf('<feedback-rating'));
  assert.match(markup, /<view wx:if="{{!isHighRisk}}" class="safe-section">\s*<section-title title="互动线索"/);
  assert.ok(markup.includes('wx:if="{{canShowTraining}}"'));
});

test('读取测评遇到401时显示登录恢复，普通网络错误不误判为登录过期', async () => {
  for (const error of [
    { statusCode: 401, message: '登录已失效' },
    { status: 401, message: '登录已失效' },
    { code: 'auth_required', message: '请登录' },
    { code: 'unauthorized', message: '请登录' },
    { code: 'network_error', message: '网络暂不可用' },
  ]) {
    const { page } = pageHarness('assessment-detail', { getAssessment: async () => { throw error; } });
    await page.loadWorksheet('synthetic-sheet');
    assert.equal(page.data.loading, false);
    assert.equal(page.data.needsLogin, error.code !== 'network_error');
    assert.equal(page.data.errorMessage, error.message);
  }
});

function supervisionApi() {
  return {
    listDiaries: async () => ({ items: [{ id: 'diary-a', scene: '合成场景', event_description: '合成记录' }] }),
    listAssessmentResults: async () => ({ items: [{ id: 'assessment-a', worksheet_title: '合成测评' }] }),
  };
}

test('人工支持默认选择URL带入日记，不被默认不关联抢占', async () => {
  const { page } = pageHarness('supervision', supervisionApi());
  await page.loadSourceOptions('diary-a');
  assert.equal(page.data.selectedSource.id, 'diary-a');
  assert.equal(page.data.selectedSource.type, 'diary');
  assert.equal(page.data.sourceOptions.filter((item) => item.selected).length, 1);
});

test('人工支持尊重草稿中的不关联或测评选择', async () => {
  for (const selectedSource of [{ type: '', id: '' }, { type: 'assessment', id: 'assessment-a' }]) {
    const { page } = pageHarness('supervision', supervisionApi());
    page.data.draftRestored = true;
    page.data.selectedSource = selectedSource;
    await page.loadSourceOptions('diary-a');
    assert.equal(page.data.selectedSource.id, selectedSource.id);
    assert.equal(page.data.selectedSource.type, selectedSource.type);
  }
});

test('关联列表读取失败可重试，重试成功后清除错误且保留请求正文', async () => {
  const api = supervisionApi();
  const working = api.listDiaries;
  api.listDiaries = async () => { throw { message: '合成网络故障' }; };
  const { page } = pageHarness('supervision', api);
  page.data.diaryId = 'diary-a';
  page.data.message = '仍需保留的请求正文';
  await page.loadSourceOptions('diary-a');
  assert.equal(page.data.sourceError, '合成网络故障');
  assert.equal(page.data.loadingSources, false);
  api.listDiaries = working;
  await page.retrySources();
  assert.equal(page.data.sourceError, '');
  assert.equal(page.data.selectedSource.id, 'diary-a');
  assert.equal(page.data.message, '仍需保留的请求正文');
});

test('人工支持仅显式提交时调用API，传递原有来源字段', async () => {
  const submitted = [];
  const { page } = pageHarness('supervision', {
    ...supervisionApi(),
    createSupervision: async (payload) => submitted.push(payload),
  });
  await page.loadSourceOptions('diary-a');
  assert.equal(submitted.length, 0);
  page.data.message = ' 请一起看看这次记录 ';
  await page.submitSupervision();
  assert.equal(submitted.length, 1);
  assert.equal(submitted[0].source_type, 'diary');
  assert.equal(submitted[0].source_id, 'diary-a');
  assert.equal(submitted[0].message, '请一起看看这次记录');
});

test('任务卡状态提示不假写缓存，进入打卡保留卡ID与日记ID', async () => {
  const h = pageHarness('task-detail', { listCards: async () => ({ items: [{ id: 'synthetic-card', title: '合成练习', steps: ['暂停片刻'] }] }) });
  h.storage.set('auth_user', { id: 'synthetic-user' });
  h.storage.set('auth_token', 'synthetic-token');
  h.page.onLoad({ card_id: 'synthetic-card', diary_id: 'diary-a' });
  await h.page.onShow();
  h.page.data.serviceReady = true;
  h.page.data.reflection = '本页感受';
  h.page.recordFeeling();
  assert.equal(h.writes.length, 0);
  await h.page.finishPractice();
  assert.match(h.navigation[0].url, /card_id=synthetic-card/);
  assert.match(h.navigation[0].url, /diary_id=diary-a/);
  assert.doesNotMatch(h.navigation[0].url, /reflection=/);
  assert.ok(read('pages/task-detail/index.wxml').includes('打卡页需要另行填写'));
});

test('开发页声明写入后果，两个长期测试入口继续保留', () => {
  const debug = read('pages/debug/index.wxml');
  const integration = read('pages/integration-test/index.wxml');
  assert.ok(debug.includes('开发专用'));
  assert.ok(debug.includes('profile 测试会创建测试记录'));
  assert.ok(integration.includes('运行后会创建测试情绪记录'));
  assert.ok(integration.includes('bindtap="runSmokeTest"'));
  assert.ok(debug.includes('bindtap="testProfile"'));
});

test('关联读取失败后主动不关联，重试成功及提交仍保持不关联', async () => {
  const api = supervisionApi();
  const working = api.listDiaries;
  const submitted = [];
  api.listDiaries = async () => { throw { message: '合成网络故障' }; };
  api.createSupervision = async (payload) => submitted.push(payload);
  const { page } = pageHarness('supervision', api);
  page.data.diaryId = 'diary-a';
  await page.loadSourceOptions('diary-a');
  page.selectSource({ currentTarget: { dataset: { type: '', id: '' } } });
  page.data.message = '只提交这段请求，不关联记录';
  api.listDiaries = working;
  await page.retrySources();
  assert.equal(page.data.selectedSource.id, '');
  assert.equal(page.data.draftRestored, false);
  await page.submitSupervision();
  assert.equal(submitted.length, 1);
  assert.equal(submitted[0].source_id, undefined);
  assert.equal(submitted[0].source_type, undefined);
});

test('草稿不跨账号恢复、覆盖或清除，旧无归属草稿不自动迁入', () => {
  const storage = new Map([['auth_user', { id: 'synthetic-a' }], ['draft', { version: 1, values: { text: 'legacy' } }]]);
  const context = { module: { exports: {} }, wx: {
    getStorageSync: key => storage.get(key),
    setStorageSync: (key, value) => storage.set(key, value),
    removeStorageSync: key => storage.delete(key),
  }, setTimeout, clearTimeout };
  vm.runInNewContext(read('utils/resilientForm.js'), context);
  const create = () => context.module.exports.createResilientForm({ storageKey: 'draft', fields: ['text'], submissionPrefix: 'synthetic', hasContent: value => !!value.text });
  const first = create();
  assert.equal(first.restore(), null);
  first.flush({ text: 'account-a' });
  assert.equal(create().restore().values.text, 'account-a');
  storage.set('auth_user', { id: 'synthetic-b' });
  assert.equal(create().restore(), null);
  first.flush({ text: 'must-not-overwrite' });
  first.clear();
  assert.equal(storage.get('draft:user:synthetic-a').values.text, 'account-a');
  assert.throws(() => first.getSubmissionId(), /账号已变化/);
  storage.delete('auth_user');
  create().flush({ text: 'no-account' });
  assert.equal(storage.has('draft:user:'), false);
  assert.equal(storage.get('draft').values.text, 'legacy');
});

test('云SDK启动不启用用户访问遥测', () => {
  assert.match(read('app.js'), /traceUser: false/);
});

test('first privacy reminder records reading only, without creating any purpose consent', () => {
  let consentWrites = 0;
  const { page, writes } = pageHarness('home', { createConsent() { consentWrites += 1; } });
  page.refreshHomeData = () => {};
  page.onShow();
  assert.equal(page.data.privacyNoticeVisible, true);
  page.acknowledgePrivacyNotice();
  page.onShow();
  assert.equal(page.data.privacyNoticeVisible, false);
  assert.equal(consentWrites, 0);
  assert.equal(writes.length, 1);
  assert.equal(writes[0].key, 'safehome_privacy_notice_seen');
});

test('optional-purpose withdrawal uses the latest self decision and needs explicit confirmation', async () => {
  const submitted = [];
  const records = [
    { id: 'old-research', consent_type: 'research_authorization', event_version: 1, agreed: 1, consent_version: 'v1' },
    { id: 'new-research', consent_type: 'research_authorization', event_version: 2, agreed: 0, consent_version: 'v1' },
    { id: 'training-current', consent_type: 'model_training', event_version: 3, agreed: 1, consent_version: 'v2', purpose: 'model_training', processor: 'safehome' },
  ];
  const { page, context } = pageHarness('settings-detail', {
    listConsentRecords: async () => ({ items: records }),
    createConsent: async (payload) => { submitted.push(payload); return { ...payload }; },
  });
  await page.loadConsentDecisions();
  assert.equal(page.data.consentDecisions.find(item => item.consent_type === 'research_authorization').agreed, false);
  assert.equal(submitted.length, 0);
  context.wx.showModal = ({ success }) => success({ confirm: false });
  page.withdrawOptionalConsent({ currentTarget: { dataset: { id: 'training-current' } } });
  assert.equal(submitted.length, 0);
  context.wx.showModal = ({ success }) => success({ confirm: true });
  page.withdrawOptionalConsent({ currentTarget: { dataset: { id: 'training-current' } } });
  await new Promise(setImmediate);
  assert.equal(submitted.length, 1);
  assert.equal(submitted[0].agreed, false);
  assert.equal(submitted[0].expected_latest_id, 'training-current');
  assert.equal(submitted[0].consent_version, 'v2');
});

function serviceConsentHarness({ records = [], accept = true, needPrivacy = false, privacyAccept = true, changeAccount = false } = {}) {
  const storage = new Map([['auth_user', { id: 'synthetic-a' }], ['safehome_privacy_notice_seen', '2026.10-privacy-notice-v1']]);
  const submitted = [], modals = [];
  const page = { setData() {} };
  const context = { module: { exports: {} }, getCurrentPages: () => [page], wx: {
    getStorageSync: key => storage.get(key),
    setStorageSync: (key, value) => storage.set(key, value),
    getPrivacySetting: ({ success }) => success({ needAuthorization: needPrivacy }),
    requirePrivacyAuthorize: ({ success, fail }) => privacyAccept ? success() : fail(),
    showModal: options => { modals.push(options); if (changeAccount) storage.set('auth_user', { id: 'synthetic-b' }); options.success({ confirm: accept }); },
  } };
  vm.runInNewContext(read('utils/serviceConsent.js'), context);
  const api = { listConsentRecords: async () => ({ items: records }), createConsent: async value => submitted.push(value) };
  return { helper: context.module.exports, api, page, submitted, modals, storage };
}

test('拒绝基础功能说明不写任何用途同意，确认后仅写该功能用途', async () => {
  const denied = serviceConsentHarness({ accept: false });
  assert.equal(await denied.helper.ensureServiceConsent(denied.page, denied.api, 'diary'), false);
  assert.equal(denied.submitted.length, 0);
  const accepted = serviceConsentHarness();
  assert.equal(await accepted.helper.ensureServiceConsent(accepted.page, accepted.api, 'diary'), true);
  assert.equal(accepted.submitted.length, 1);
  assert.equal(accepted.submitted[0].consent_type, 'service_data');
  assert.equal(accepted.submitted[0].purpose, 'diary_record');
  assert.equal(accepted.submitted[0].consent_version, accepted.helper.VERSION);
  assert.ok(accepted.modals[0].content.includes('须另行授权'));
});

test('最新撤回不能被旧同意或首页阅读状态绕过', async () => {
  const h = serviceConsentHarness();
  h.api.listConsentRecords = async () => ({ items: [
    { id: 'old', consent_type: 'service_data', consent_version: h.helper.VERSION, purpose: 'diary_record', event_version: 1, agreed: 1 },
    { id: 'withdrawn', consent_type: 'service_data', event_version: 2, agreed: 0 },
  ] });
  await h.helper.ensureServiceConsent(h.page, h.api, 'diary');
  assert.equal(h.modals.length, 1);
  assert.equal(h.submitted[0].expected_latest_id, 'withdrawn');
});

test('微信隐私拒绝或账号切换均阻断用途写入', async () => {
  const denied = serviceConsentHarness({ needPrivacy: true, privacyAccept: false });
  await assert.rejects(denied.helper.ensureServiceConsent(denied.page, denied.api, 'assessment'), /微信隐私授权/);
  assert.equal(denied.modals.length, 0);
  assert.equal(denied.submitted.length, 0);
  const switched = serviceConsentHarness({ changeAccount: true });
  await assert.rejects(switched.helper.ensureServiceConsent(switched.page, switched.api, 'assessment'), /账号已变化/);
  assert.equal(switched.submitted.length, 0);
});

test('已有同版同用途决定可复用，新增用途须重新确认', async () => {
  const h = serviceConsentHarness();
  h.api.listConsentRecords = async () => ({ items: [
    { id: 'diary-only', consent_type: 'service_data', consent_version: h.helper.VERSION, purpose: 'diary_record', event_version: 1, agreed: 1 },
  ] });
  await h.helper.ensureServiceConsent(h.page, h.api, 'diary');
  assert.equal(h.modals.length, 0);
  await h.helper.ensureServiceConsent(h.page, h.api, 'supervision');
  assert.equal(h.modals.length, 1);
  assert.equal(h.submitted[0].purpose, 'human_support_request');
});

test('小程序可阅读的隐私正文与本地正文一致，保留未确认字段', () => {
  const { context } = pageHarness('settings-detail');
  const policy = vm.runInNewContext('NOTICE_MAP.privacy', context);
  const local = fs.readFileSync(path.join(ROOT, 'content/privacy.md'), 'utf8');
  for (const section of policy.sections) for (const item of section.items) assert.ok(local.includes(item), section.title);
  assert.equal(policy.status, 'draft');
  assert.ok(local.includes('[待填写：'));
  assert.doesNotMatch(read('pages/settings-detail/index.js'), /正式文本以 content\/privacy\.md/);
});

test('未开放训练卡不回退到硬编码内容，旧缓存不能继续打卡', async () => {
  const h = pageHarness('task-detail', { listCards: async () => ({ items: [] }) });
  h.storage.set('auth_user', { id: 'synthetic' }); h.storage.set('auth_token', 'synthetic');
  h.storage.set('safehome:selectedTrainingCard', { id: 'closed-card', title: 'old', stepsList: [{ text: 'old step' }] });
  h.page.onLoad({ card_id: 'closed-card' });
  await h.page.onShow(); await h.page.finishPractice();
  assert.equal(h.page.data.task, null);
  assert.match(h.page.data.errorMessage, /未开放/);
  assert.equal(h.navigation.length, 0);
});


function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
function switchAccount(h, id) {
  h.storage.set('auth_user', { id }); h.storage.set('auth_token', `synthetic-${id}`);
}

function homeApi(overrides = {}) {
  return {
    listDiaries: async () => ({ items: [] }), getProfileStats: async () => ({}),
    getEmotionThermometerDay: async () => ({}), getProgressSummary: async () => null,
    getTodayJourney: async () => ({ state: 'ready', primary_action: { type: 'practice_due', title: '合成服务端行动', url: '/pages/training/index' } }),
    trackProductEvent: async () => ({}), ...overrides,
  };
}

function homeWithRealApi() {
  const api = {};
  const h = pageHarness('home', api);
  const requests = [];
  h.context.wx.request = options => requests.push(options);
  const mod = { exports: {} };
  vm.runInNewContext(read('services/api.js'), {
    module: mod, wx: h.context.wx, console,
    require(name) {
      if (name === './userIdentity') return { getAnonymousUserId: () => 'synthetic-anonymous' };
      if (name === './cloudConfig') return {
        DEFAULT_CLOUD_CONFIG: {},
        getCloudConfig: () => ({ useLocalHttp: true, localHttpBaseUrl: 'http://synthetic.invalid' }),
      };
      throw new Error(name);
    },
  });
  Object.assign(api, mod.exports.createSafeHomeApi());
  return { ...h, requests };
}

test('首页登录态：未登录不显示摘要错误或读取个人数据，行动可进入登录', async () => {
  const h = homeWithRealApi();
  await h.page.refreshHomeData();
  await h.page.loadTodayJourney();
  assert.equal(h.requests.length, 0);
  assert.equal(h.page.data.homeOverviewError, '');
  assert.equal(h.page.data.latestRecordError, '');
  assert.equal(h.page.data.progressSummaryError, '');
  assert.equal(h.page.data.homeLoginRequired, true);
  assert.equal(h.page.data.latestRecordReady, true);
  assert.equal(h.page.data.progressSummaryReady, true);
  h.page.openTodayAction();
  assert.equal(h.navigation[0].url, '/pages/login/index');
  assert.equal(h.requests.length, 0);
});

test('首页登录态：当前会话401后清旧摘要、结束等待并显示登录入口，保留草稿', async () => {
  const h = homeWithRealApi(); switchAccount(h, 'A');
  h.storage.set('safehome:programDraft:own-program:1:user:A', { draftText: 'synthetic-draft' });
  h.page.data.latestRecord = { mood: 'old-private' };
  h.page.data.progressSummary = { summaryText: 'old-private' };
  const run = h.page.refreshHomeData();
  assert.equal(h.requests.length, 6);
  for (const request of h.requests) {
    request.success({ statusCode: 401, data: { error: { code: 'unauthorized' } } });
  }
  await run; await new Promise(setImmediate);
  assert.equal(h.storage.has('auth_token'), false);
  assert.equal(h.page.data.latestRecord, null);
  assert.equal(h.page.data.progressSummary, null);
  assert.equal(h.page.data.todayJourneyLoading, false);
  assert.equal(h.page.data.homeLoginRequired, true);
  assert.equal(h.page.data.todayJourney.type, 'login_required');
  assert.equal(h.page.data.homeOverviewError, '');
  assert.equal(h.storage.has('safehome:programDraft:own-program:1:user:A'), true);
});

test('首页登录态：登录后恢复个人读取，普通网络错误仍允许重试', async () => {
  const h = homeWithRealApi();
  await h.page.refreshHomeData();
  switchAccount(h, 'A');
  const run = h.page.refreshHomeData();
  assert.equal(h.requests.length, 6);
  for (const request of h.requests) {
    request.fail({ errMsg: 'synthetic network failure' });
  }
  await run; await new Promise(setImmediate);
  assert.equal(h.page.data.homeLoginRequired, false);
  assert.equal(h.storage.get('auth_token'), 'synthetic-A');
  assert.ok(h.page.data.homeOverviewError);
  assert.ok(h.page.data.latestRecordError);
  assert.ok(h.page.data.progressSummaryError);
  assert.ok(h.page.data.todayJourneyError);
  const requestCount = h.requests.length;
  h.page.retryHomeData();
  assert.equal(h.requests.length, requestCount + 6);
  for (const request of h.requests.slice(requestCount)) {
    request.success({ statusCode: 200, data: { ok: true, data: { items: [] } } });
  }
  await new Promise(setImmediate);
  assert.equal(h.page.data.homeOverviewError, '');
  assert.equal(h.page.data.latestRecordError, '');
  assert.equal(h.page.data.progressSummaryError, '');
});

test('首页登录态：最近记录和阶段反馈未登录分支先于读取、错误和空记录', () => {
  const template = read('pages/home/index.wxml');
  for (const [heading, loginTitle] of [
    ['最近记录', '登录后查看最近记录'], ['阶段性反馈', '登录后查看阶段性反馈'],
  ]) {
    const section = template.split(`<section-heading title="${heading}" />`)[1].split('</view>')[0];
    assert.match(section, new RegExp(`wx:if="\\{\\{homeLoginRequired\\}\\}" kind="empty" title="${loginTitle}"`));
    assert.ok(section.indexOf('homeLoginRequired') < section.indexOf('kind="loading"'));
    assert.match(section, /wx:elif="\{\{![a-zA-Z]+Ready/);
  }
});

test('首页不展示其他账号或无归属草稿的继续入口', async () => {
  const h = pageHarness('home', homeApi()); switchAccount(h, 'A');
  h.storage.set('safehome:programDraft:other-program:1:user:B', { draftText: 'other-owner' });
  h.storage.set('safehome:programDraft:legacy-program:1', { draftText: 'legacy-ownerless' });
  h.context.wx.getStorageInfoSync = () => ({ keys: [...h.storage.keys()] });
  await h.page.loadTodayJourney();
  assert.equal(h.page.data.todayJourney.type, 'practice_due');
  h.storage.set('safehome:programDraft:own-program:1:user:A', { draftText: 'own' });
  await h.page.loadTodayJourney();
  assert.equal(h.page.data.todayJourney.type, 'continue_program_draft');
  assert.ok(h.page.data.todayJourney.url.includes('own-program'));
});

test('首页识别当前账号关系画布或答案草稿', async () => {
  const h = pageHarness('home', homeApi()); switchAccount(h, 'A');
  h.storage.set('relationship_task_draft:own-enrollment:drawing:user:A', { strokes: [[{ x: 1, y: 2 }]], answers: { q1: 'synthetic' } });
  h.context.wx.getStorageInfoSync = () => ({ keys: [...h.storage.keys()] });
  await h.page.loadTodayJourney();
  assert.equal(h.page.data.todayJourney.type, 'continue_relationship_draft');
});

test('首页并行摘要等待中切换账号不回填旧日记', async () => {
  const waiting = deferred();
  const h = pageHarness('home', homeApi({
    listDiaries: async () => ({ items: [{ parent_emotion: 'old-owner', scene: 'old-scene' }] }),
    getProgressSummary: () => waiting.promise,
  })); switchAccount(h, 'A');
  const running = h.page.refreshHomeData(); await Promise.resolve();
  switchAccount(h, 'B'); waiting.resolve(null); await running;
  assert.equal(h.page.data.latestRecord, null);
});

test('首页返回新账号时立即清旧摘要，隐藏后的旅程不回填', async () => {
  const waiting = deferred();
  const h = pageHarness('home', homeApi({ getTodayJourney: () => waiting.promise }));
  switchAccount(h, 'A'); h.page.onShow();
  h.page.data.latestRecord = { mood: 'old-owner' }; h.page.data.unreadMessageCount = 8;
  h.page.onHide(); switchAccount(h, 'B'); h.page.onShow();
  assert.equal(h.page.data.latestRecord, null); assert.equal(h.page.data.unreadMessageCount, 0);
  h.page.onHide();
  waiting.resolve({ state: 'ready', primary_action: { type: 'read_feedback', title: 'late', url: '/pages/feedback-result/index' } });
  await new Promise(setImmediate);
  assert.equal(h.page.data.todayJourney, null);
});

for (const [route, field] of [['assessment-result', 'result'], ['assessment-history', 'items'], ['program-detail', 'submittedEntries']]) {
  test(`${route}返回页面时清除旧账号已显示内容`, () => {
    const h = pageHarness(route);
    switchAccount(h, 'A'); h.page._readSession = { userId: 'A', token: 'synthetic-A' };
    h.page.data[field] = field === 'result' ? { id: 'private-A' } : [{ id: 'private-A' }];
    h.page.data.loading = false;
    h.page.loadResult = h.page.loadPage = h.page.onLoad = () => {};
    h.page.onHide(); switchAccount(h, 'B'); h.page.onShow();
    assert.ok(h.page.data[field] === null || h.page.data[field].length === 0);
  });
}

test('日记读取隐藏后不回填，重新显示会恢复读取', async () => {
  const waiting = deferred(); let calls = 0;
  const h = pageHarness('diary-history', { listDiaries: () => ++calls === 1 ? waiting.promise : Promise.resolve({ items: [{ id: 'current-B', raw_text: 'synthetic' }] }) });
  switchAccount(h, 'B'); h.page._authorized = true;
  const run = h.page.loadRecords(); h.page.onHide();
  waiting.resolve({ items: [{ id: 'hidden-result' }] }); await run;
  assert.equal(h.page.data.records.length, 0);
  h.page.onShow(); await new Promise(setImmediate);
  assert.equal(calls, 2); assert.equal(h.page.data.records[0].id, 'current-B');
  assert.equal(h.page.data.loading, false);
});

test('关系任务返回页面时清除旧账号画布和正文', () => {
  const h = pageHarness('relationship-task'); switchAccount(h, 'A');
  h.page._formSession = { userId: 'A', token: 'synthetic-A' }; h.page._draftOwner = 'A';
  h.page.data.narration = 'private-A'; h.page.data.answers = { 争吵: 'private-A' }; h.page.strokes = [[{ x: 1, y: 2 }]];
  h.page.redrawCanvas = () => {}; h.page.onLoad = () => {};
  h.page.onHide(); switchAccount(h, 'B'); h.page.onShow();
  assert.equal(h.page.data.narration, ''); assert.equal(Object.keys(h.page.data.answers).length, 0);
  assert.equal(h.page.strokes.length, 0); assert.equal(h.page.data.consent, false);
});

for (const [code, statusCode, expected] of [
  ['wechat_phone_exchange_failed', 400, '手机号验证未完成，请稍后重新授权或使用其他登录方式。'],
  ['wechat_phone_permission_denied', 503, '手机号登录暂不可用，请使用其他登录方式；平台权限需要项目负责人确认。'],
]) {
  test(`手机号错误${code}经过真实请求层仍显示对应提示`, async () => {
    let pending;
    const mod = { exports: {} };
    const wx = { getStorageSync: () => undefined, removeStorageSync() {}, request: options => { pending = options; } };
    vm.runInNewContext(read('services/api.js'), { module: mod, wx, console, require(name) {
      if (name === './userIdentity') return { getAnonymousUserId: () => 'synthetic-anonymous' };
      if (name === './cloudConfig') return { DEFAULT_CLOUD_CONFIG: {}, getCloudConfig: () => ({ useLocalHttp: true, localHttpBaseUrl: 'http://synthetic.invalid' }) };
      throw new Error(name);
    } });
    const run = mod.exports.createSafeHomeApi().phoneLogin({ code: 'synthetic' });
    pending.success({ statusCode, data: { error: { code, message: 'backend-message' } } });
    await assert.rejects(run, error => error.code === code && error.message === expected);
  });
}

test('旧401不能清除新的登录，当前会话401仍清理', async () => {
  const storage = new Map([['auth_token', 'synthetic-A'], ['auth_user', { id: 'A' }]]);
  let pending;
  const mod = { exports: {} };
  const wx = { getStorageSync: key => storage.get(key), setStorageSync: (key, value) => storage.set(key, value), removeStorageSync: key => storage.delete(key), request: options => { pending = options; } };
  vm.runInNewContext(read('services/api.js'), { module: mod, wx, console, require(name) {
    if (name === './userIdentity') return { getAnonymousUserId: () => 'synthetic-anonymous' };
    if (name === './cloudConfig') return { DEFAULT_CLOUD_CONFIG: {}, getCloudConfig: () => ({ useLocalHttp: true, localHttpBaseUrl: 'http://synthetic.invalid' }) };
    throw new Error(name);
  } });
  const api = mod.exports.createSafeHomeApi();
  const old = api.listProgramEntries('synthetic-program');
  storage.set('auth_token', 'synthetic-B'); storage.set('auth_user', { id: 'B' });
  pending.success({ statusCode: 401, data: { error: { code: 'unauthorized' } } });
  await assert.rejects(old);
  assert.equal(storage.get('auth_token'), 'synthetic-B');
  const current = api.listProgramEntries('synthetic-program');
  pending.success({ statusCode: 401, data: { error: { code: 'unauthorized' } } });
  await assert.rejects(current);
  assert.equal(storage.has('auth_token'), false);
});

for (const transport of ['api', 'minorSafeguardsApi']) {
  test(`${transport}迟到200或401不回填或清理新会话`, async () => {
    const storage = new Map([['auth_token', 'synthetic-A'], ['auth_user', { id: 'A' }]]); let pending;
    const mod = { exports: {} };
    const wx = { getStorageSync: key => storage.get(key), setStorageSync: (key, value) => storage.set(key, value), removeStorageSync: key => storage.delete(key), request: options => { pending = options; } };
    vm.runInNewContext(read(`services/${transport}.js`), { module: mod, wx, console, require(name) {
      if (name === './userIdentity') return { getAnonymousUserId: () => 'synthetic-anonymous' };
      if (name === './cloudConfig') return { DEFAULT_CLOUD_CONFIG: {}, getCloudConfig: () => ({ useLocalHttp: true, localHttpBaseUrl: 'http://synthetic.invalid' }) };
      throw new Error(name);
    } });
    const api = transport === 'api' ? mod.exports.createSafeHomeApi() : mod.exports;
    const request = () => transport === 'api' ? api.listProgramEntries('synthetic') : api.getMinorSafeguardStatus();
    for (const statusCode of [200, 401]) {
      storage.set('auth_token', 'synthetic-A'); storage.set('auth_user', { id: 'A' });
      const run = request(); storage.set('auth_token', 'synthetic-B'); storage.set('auth_user', { id: 'B' });
      pending.success({ statusCode, data: { ok: statusCode === 200, data: { private: 'A' } } });
      await assert.rejects(run, error => error.code === 'auth_session_changed');
      assert.equal(storage.get('auth_token'), 'synthetic-B');
    }
    if (transport === 'api') {
      storage.set('auth_token', 'synthetic-A'); storage.set('auth_user', { id: 'A' });
      const run = api.logout(); storage.set('auth_token', 'synthetic-B'); storage.set('auth_user', { id: 'B' });
      pending.success({ statusCode: 200, data: { ok: true, data: { tokens_revoked: true } } });
      assert.equal((await run).session_changed, true);
      assert.equal(storage.get('auth_token'), 'synthetic-B');
    }
  });
}

for (const [route, method, apiMethod, payload, field] of [
  ['program-detail', 'loadSubmittedEntries', 'listProgramEntries', { items: [{ id: 'synthetic-A-entry' }] }, 'submittedEntries'],
  ['assessment-detail', 'loadWorksheet', 'getAssessment', { id: 'synthetic-scale', questions: [] }, 'worksheet'],
  ['settings-detail', 'loadConsentDecisions', 'listConsentRecords', { items: [{ id: 'synthetic-A-consent', consent_type: 'research_authorization', agreed: 1 }] }, 'consentDecisions'],
  ['assessment-history', 'loadPage', 'listAssessmentResults', { items: [{ id: 'synthetic-A-result' }] }, 'items'],
  ['diary-history', 'loadRecords', 'listDiaries', { items: [{ id: 'synthetic-A-diary', raw_text: 'synthetic-private-A' }] }, 'records'],
]) {
  test(`${route}拒绝账号切换后的迟到个人响应`, async () => {
    const waiting = deferred();
    const h = pageHarness(route, { [apiMethod]: () => waiting.promise });
    switchAccount(h, 'A');
    const before = JSON.stringify(h.page.data[field]);
    const run = h.page[method](method === 'loadPage' ? 1 : 'synthetic');
    switchAccount(h, 'B'); waiting.resolve(payload);
    await run;
    assert.equal(JSON.stringify(h.page.data[field]), before);
    assert.equal(h.writes.length, 0);
  });
}

test('测评结果等待第二个请求时切换账号也不写推荐缓存', async () => {
  const waiting = deferred();
  const api = {
    getAssessmentResult: async () => ({ id: 'synthetic-A', scores_json: '{}' }),
    getAssessment: async () => ({ id: 'synthetic', questions: [] }),
    listCards: async () => ({ items: [] }),
    getAssessmentExploratoryAnalysis: async () => null,
    getAssessmentProfilePosition: () => waiting.promise,
  };
  const result = pageHarness('assessment-result', api);
  result.page.data.resultId = 'synthetic-A'; result.page.data.worksheetId = 'synthetic';
  switchAccount(result, 'A');
  const running = result.page.loadResult();
  await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
  switchAccount(result, 'B'); waiting.resolve(null); await running;
  assert.equal(result.page.data.result, null);
  assert.equal(result.writes.length, 0);
});

test('高风险日记反馈清理旧普通建议，迟到普通响应不再回填', async () => {
  const waiting = deferred(); let calls = 0;
  const h = pageHarness('feedback-result', {
    generateFeedback: () => ++calls === 1 ? waiting.promise : Promise.resolve({ risk_level: 'high' }),
    listCards: async () => ({ items: [] }),
  });
  switchAccount(h, 'A');
  h.storage.set('safehome:latestTrainingRecommendation', { cardIds: ['old'] });
  h.storage.set('safehome:threeDayLightPlan', { days: ['old'] });
  const old = h.page.loadFeedback('synthetic-old');
  await h.page.loadFeedback('synthetic-high');
  waiting.resolve({ risk_level: 'low', recommended_card_ids: ['old'] }); await old;
  assert.equal(h.page.data.isHighRisk, true);
  assert.equal(h.storage.has('safehome:latestTrainingRecommendation'), false);
  assert.equal(h.storage.has('safehome:threeDayLightPlan'), false);
});

test('画布等待时切换账号，不提交或删除草稿', async () => {
  const waiting = deferred(); let sent = 0;
  const h = pageHarness('relationship-task', { createRelationshipTask: async () => { sent++; }, trackProductEvent: async () => {} });
  switchAccount(h, 'A'); h.page._draftOwner = 'A';
  h.page.data.consent = true; h.page.data.narration = 'synthetic narration'; h.page.strokes = [[{ x: 1, y: 2 }]];
  h.page.getCanvasSize = () => waiting.promise;
  const running = h.page.saveTask();
  switchAccount(h, 'B'); waiting.resolve({ width: 320, height: 260 }); await running;
  assert.equal(sent, 0); assert.equal(h.removed.length, 0);
});

test('周报保留有效0，缺失才使用占位', () => {
  const { page } = pageHarness('weekly-report');
  assert.equal(page.formatThermometerDetail({ count: 1, avg_intensity: 0, avg_valence: 0, avg_arousal: 0, avg_control: 0 }), '平均强度 0 · 愉悦 0 · 唤起 0 · 可控 0');
  assert.equal(page.formatThermometerDetail({ count: 1, avg_intensity: null }), '平均强度 -');
});

test('三个Web测评草稿键按账号隔离，旧无归属键不恢复', () => {
  const ts = require('../../node_modules/typescript');
  const source = ts.transpileModule(fs.readFileSync(path.join(ROOT, 'apps/web/src/hooks/useResilientDraft.ts'), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  const storage = new Map(); let owner = 'A'; let token = 'synthetic-A';
  const window = { localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) }, setTimeout: () => 1, clearTimeout() {}, addEventListener() {}, removeEventListener() {} };
  const mod = { exports: {} };
  vm.runInNewContext(source, { module: mod, exports: mod.exports, window, require(name) {
    if (name === 'react') return { useEffect: fn => fn(), useMemo: fn => fn(), useRef: value => ({ current: value }), useState: value => [value, () => {}] };
    if (name === '../services/authState') return { getStoredAuthToken: () => token, getStoredAuthUser: () => ({ id: owner }) };
    throw new Error(name);
  } });
  for (const key of ['student-assessment', 'parent-assessment', 'relationship-assessment']) {
    const storageKey = `safehome:draft:${key}`; let restored = null;
    const use = () => mod.exports.useResilientDraft({ storageKey, submissionPrefix: 'synthetic', value: { answer: '' }, restore: values => { restored = values; }, hasContent: values => !!values.answer });
    owner = 'A'; token = 'synthetic-A'; const a = use(); a.flush({ answer: 'synthetic-A-answer' });
    storage.set(storageKey, JSON.stringify({ version: 1, values: { answer: 'ownerless legacy' } }));
    owner = 'B'; token = 'synthetic-B'; restored = null; const b = use();
    assert.equal(restored, null); a.flush({ answer: 'late-A' });
    b.flush({ answer: 'synthetic-B-answer' });
    assert.equal(JSON.parse(storage.get(`${storageKey}:user:A`)).values.answer, 'synthetic-A-answer');
    assert.equal(JSON.parse(storage.get(`${storageKey}:user:B`)).values.answer, 'synthetic-B-answer');
    owner = 'A'; token = 'synthetic-A'; restored = null; use();
    assert.equal(restored.answer, 'synthetic-A-answer');
  }
});

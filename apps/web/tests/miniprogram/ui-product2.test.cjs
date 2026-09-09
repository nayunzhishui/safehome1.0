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
    Page(value) { definition = value; },
    require(name) {
      if (name === '../../services/api') return { createSafeHomeApi: () => api };
      if (name === '../../utils/authGuard') return { requireLogin: () => true, isLoggedIn: () => true };
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

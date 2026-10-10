// Home greeting follows local time of day and date; synthetic dates only.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '../../../..');
const { buildGreeting, greetingFor, dateLabel, LATE_NIGHT } = require(path.join(ROOT, 'apps/miniprogram/utils/greeting.js'));

const at = (hours, minutes = 0) => new Date(2026, 9, 10, hours, minutes);

test('greeting changes at each time-of-day boundary', () => {
  assert.equal(greetingFor(at(4, 59)), LATE_NIGHT);
  assert.equal(greetingFor(at(5, 0)), '早上好');
  assert.equal(greetingFor(at(8, 59)), '早上好');
  assert.equal(greetingFor(at(9, 0)), '上午好');
  assert.equal(greetingFor(at(11, 29)), '上午好');
  assert.equal(greetingFor(at(11, 30)), '中午好');
  assert.equal(greetingFor(at(13, 29)), '中午好');
  assert.equal(greetingFor(at(13, 30)), '下午好');
  assert.equal(greetingFor(at(17, 59)), '下午好');
  assert.equal(greetingFor(at(18, 0)), '晚上好');
  assert.equal(greetingFor(at(22, 59)), '晚上好');
  assert.equal(greetingFor(at(23, 0)), LATE_NIGHT);
  assert.equal(greetingFor(at(0, 30)), LATE_NIGHT);
});

test('date label uses month, day and weekday without zero padding', () => {
  assert.equal(dateLabel(at(20)), '10月10日 周六');
  assert.equal(dateLabel(new Date(2026, 0, 4, 9)), '1月4日 周日');
  assert.equal(dateLabel(new Date(2026, 11, 31, 9)), '12月31日 周四');
});

test('buildGreeting combines both parts and falls back to now for invalid input', () => {
  assert.deepEqual(buildGreeting(at(20, 15)), { greeting: '晚上好', dateText: '10月10日 周六' });
  const fallback = buildGreeting(new Date('not a date'));
  assert.equal(typeof fallback.greeting, 'string');
  assert.match(fallback.dateText, /^\d{1,2}月\d{1,2}日 周[日一二三四五六]$/);
});

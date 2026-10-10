// Home greeting: follows the device's local time of day and date. Pure function, no storage or network.

const WEEKDAYS = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

// Minutes since local midnight; each slot covers [from, to). Anything outside these slots is late night.
const SLOTS = [
  { from: 5 * 60, to: 9 * 60, greeting: "早上好" },
  { from: 9 * 60, to: 11 * 60 + 30, greeting: "上午好" },
  { from: 11 * 60 + 30, to: 13 * 60 + 30, greeting: "中午好" },
  { from: 13 * 60 + 30, to: 18 * 60, greeting: "下午好" },
  { from: 18 * 60, to: 23 * 60, greeting: "晚上好" },
];
const LATE_NIGHT = "夜深了";

function validDate(value) {
  return value instanceof Date && !Number.isNaN(value.getTime()) ? value : new Date();
}

function greetingFor(value) {
  const date = validDate(value);
  const minutes = date.getHours() * 60 + date.getMinutes();
  const slot = SLOTS.find((item) => minutes >= item.from && minutes < item.to);
  return slot ? slot.greeting : LATE_NIGHT;
}

function dateLabel(value) {
  const date = validDate(value);
  return `${date.getMonth() + 1}月${date.getDate()}日 ${WEEKDAYS[date.getDay()]}`;
}

function buildGreeting(value) {
  const date = validDate(value);
  return { greeting: greetingFor(date), dateText: dateLabel(date) };
}

module.exports = { buildGreeting, greetingFor, dateLabel, LATE_NIGHT };

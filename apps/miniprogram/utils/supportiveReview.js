const HUB_ROUTE = "pages/therapeutic-assessment/index";

// The letter is its own page; follow-up is reached from the hub once an experiment exists.
const FLOW_STEPS = ["question", "guess", "episode", "exceptions", "scales", "inquiry", "letter", "experiment"];

const STEP_TITLES = {
  question: "我想弄清楚的问题",
  guess: "我现在的猜测",
  episode: "一次具体经历",
  exceptions: "不一样的时候",
  scales: "选择问卷",
  inquiry: "做完问卷后的回看",
  letter: "回看信",
  experiment: "一个小实验",
  followup: "一两周后的回看",
};

function stepUrl(reviewId, step) {
  const id = encodeURIComponent(reviewId || "");
  if (step === "letter" || step === "done") return `/pages/supportive-review-letter/index?id=${id}`;
  return `/pages/supportive-review-step/index?step=${step}${reviewId ? `&id=${id}` : ""}`;
}

function nextStepAfter(step, review) {
  if (step === "scales") return review && review.linked_results && review.linked_results.length ? "inquiry" : "letter";
  const index = FLOW_STEPS.indexOf(step);
  return index >= 0 && index < FLOW_STEPS.length - 1 ? FLOW_STEPS[index + 1] : "";
}

function progressFor(step) {
  const index = FLOW_STEPS.indexOf(step);
  return FLOW_STEPS.map((id, position) => ({
    id,
    state: index < 0 ? "done" : position < index ? "done" : position === index ? "current" : "todo",
  }));
}

function formatDay(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value || ""));
  if (!match) return "";
  return `${Number(match[2])}月${Number(match[3])}日`;
}

function statusText(item) {
  if (!item) return "";
  if (item.status === "completed") return "已完成回看";
  if (item.status === "followup_due") return "可以回看小实验了";
  if (item.next_step === "followup") return item.followup_due_on ? `${formatDay(item.followup_due_on)}起可以回看` : "试过后再回来回看";
  return `下一步：${STEP_TITLES[item.next_step] || "继续整理"}`;
}

function entryUrl(item) {
  if (!item) return stepUrl("", "question");
  if (item.status === "followup_due") return stepUrl(item.id, "followup");
  if (item.next_step === "followup" || item.next_step === "done") return stepUrl(item.id, "letter");
  return stepUrl(item.id, item.next_step);
}

function backToHub() {
  const pages = getCurrentPages();
  for (let index = pages.length - 2; index >= 0; index -= 1) {
    if (pages[index].route === HUB_ROUTE) {
      wx.navigateBack({ delta: pages.length - 1 - index });
      return;
    }
  }
  wx.redirectTo({ url: `/${HUB_ROUTE}` });
}

function submissionKey(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

module.exports = {
  FLOW_STEPS,
  STEP_TITLES,
  backToHub,
  entryUrl,
  formatDay,
  nextStepAfter,
  progressFor,
  statusText,
  stepUrl,
  submissionKey,
};

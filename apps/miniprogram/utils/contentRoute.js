// B6 统一内容编号“类型:id”到页面路径。见 docs/11_商业化开发/开发框架.md 第 8 节。
const ROUTES = {
  card: (id) => `/pages/checkin/index?card_id=${encodeURIComponent(id)}`,
  course: (id) => `/pages/course-detail/index?id=${encodeURIComponent(id)}`,
  worksheet: (id) => `/pages/assessment-detail/index?id=${encodeURIComponent(id)}`,
  // TODO(B6-前端): story 指向 pages/hot-topics 的哪个参数；video 用 channel-video 放在哪里；article 怎么打开
};

function parseContentId(contentId) {
  const text = String(contentId || "");
  const index = text.indexOf(":");
  if (index <= 0) return null;
  return { type: text.slice(0, index), id: text.slice(index + 1) };
}

function pathFor(contentId) {
  const parsed = parseContentId(contentId);
  if (!parsed || !ROUTES[parsed.type]) return "";
  return ROUTES[parsed.type](parsed.id);
}

module.exports = { parseContentId, pathFor };

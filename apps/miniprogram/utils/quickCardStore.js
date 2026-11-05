// B1 急救卡本地暂存：没登录时把练习结果存在手机上，登录后逐条上传，成功一条删一条。
// 见 docs/11_商业化开发/开发框架.md 第 3 节。上传时间就是记录时间，练习的实际时间不保留。
const STORAGE_KEY = "safehome.quickCard.pending";
const MAX_PENDING = 20;

function listPending() {
  // TODO(B1-前端)
  return [];
}

function addPending(record) {
  // TODO(B1-前端): record = { client_submission_id, card_id, emotion_before, emotion_after, completed }；
  // 超过 MAX_PENDING 条时丢掉最早的
}

function uploadPending(api) {
  // TODO(B1-前端): 逐条 api.createCheckin(record)，成功一条删一条；返回上传成功的条数
  return Promise.resolve(0);
}

module.exports = { STORAGE_KEY, MAX_PENDING, listPending, addPending, uploadPending };

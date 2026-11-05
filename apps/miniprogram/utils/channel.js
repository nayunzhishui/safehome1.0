// A3 渠道标记：解析进入参数里的 ch，记住第一次的渠道，登录后补报一次 app_entry。
// 见 docs/11_商业化开发/开发框架.md 第 2 节。
const STORAGE_KEY = "safehome.channel";
const CHANNELS = ["gzh", "sph", "group", "interview", "other"];

function parseChannel(options = {}) {
  const query = options.query || {};
  let ch = query.ch || "";
  if (!ch && query.scene) {
    // 小程序码的 scene 形如 "ch=sph"
    const match = /(?:^|&)ch=([a-z]+)/.exec(decodeURIComponent(query.scene));
    ch = match ? match[1] : "";
  }
  return CHANNELS.includes(ch) ? ch : "";
}

function rememberChannel(ch) {
  // TODO(A3-前端): 只记第一次的渠道和时间；本地存储的读写都用 try/catch 包住
}

function flushChannelEvent(api) {
  // TODO(A3-前端): 登录后用 services/api.js 里提交产品事件的方法补报：
  // event_name "app_entry"，client_event_id `app_entry:${ch}:${北京日期}`，metadata { channel: ch }
  return Promise.resolve(false);
}

module.exports = { STORAGE_KEY, CHANNELS, parseChannel, rememberChannel, flushChannelEvent };

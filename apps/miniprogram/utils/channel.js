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

function readSaved() {
  try {
    const saved = wx.getStorageSync(STORAGE_KEY);
    return saved && saved.ch ? saved : null;
  } catch (error) {
    return null;
  }
}

function writeSaved(saved) {
  try {
    wx.setStorageSync(STORAGE_KEY, saved);
  } catch (error) {
    // 存不进去就算了，渠道统计少一条，不影响使用。
  }
}

// 北京日期 YYYY-MM-DD，用来拼 client_event_id。
function beijingDate(iso) {
  const time = new Date(iso).getTime();
  const shifted = new Date((Number.isNaN(time) ? Date.now() : time) + 8 * 3600 * 1000);
  return shifted.toISOString().slice(0, 10);
}

function rememberChannel(ch) {
  if (!ch || readSaved()) return; // 只记第一次的渠道
  writeSaved({ ch, firstSeenAt: new Date().toISOString(), reported: false });
}

// 登录后补报一次 app_entry；后端还没放行这个事件时会失败，下次启动再试。
function flushChannelEvent(api) {
  const saved = readSaved();
  if (!saved || saved.reported || !api || !api.trackProductEvent) return Promise.resolve(false);
  const clientEventId = `app_entry:${saved.ch}:${beijingDate(saved.firstSeenAt)}`;
  return api.trackProductEvent("app_entry", { channel: saved.ch }, clientEventId)
    .then(() => {
      writeSaved({ ...saved, reported: true });
      return true;
    })
    .catch(() => false);
}

module.exports = { STORAGE_KEY, CHANNELS, parseChannel, rememberChannel, flushChannelEvent };

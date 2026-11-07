// B1 急救卡本地暂存：没登录时把练习结果存在手机上，登录后逐条上传，成功一条删一条。
// 见 docs/11_商业化开发/开发框架.md 第 3 节。上传时间就是记录时间，练习的实际时间不保留。
const STORAGE_KEY = "safehome.quickCard.pending";
const MAX_PENDING = 20;

function read() {
  try {
    const list = wx.getStorageSync(STORAGE_KEY);
    return Array.isArray(list) ? list : [];
  } catch (error) {
    return [];
  }
}

function write(list) {
  try {
    wx.setStorageSync(STORAGE_KEY, list);
  } catch (error) {
    // 存不进去就丢掉这条，不影响练习本身
  }
}

function listPending() {
  return read();
}

// record = { client_submission_id, card_id, emotion_before, emotion_after, completed }
function addPending(record) {
  const list = read();
  list.push(record);
  while (list.length > MAX_PENDING) list.shift(); // 超过上限丢掉最早的
  write(list);
}

// 逐条上传，遇到失败就停，下次再试；返回上传成功的条数
async function uploadPending(api) {
  if (!api || !api.createCheckin) return 0;
  let uploaded = 0;
  for (const record of read()) {
    try {
      await api.createCheckin(record);
    } catch (error) {
      break;
    }
    uploaded += 1;
    write(read().filter((item) => item.client_submission_id !== record.client_submission_id));
  }
  return uploaded;
}

module.exports = { STORAGE_KEY, MAX_PENDING, listPending, addPending, uploadPending };

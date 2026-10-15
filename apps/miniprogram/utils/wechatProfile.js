// 头像和昵称只存在这台手机上，按账号分开，不上传服务器：生产库 avatar_url 只有 191 个字符，
// 研究者工作台也会显示服务器上的昵称。登录后的填写卡片和“我的”页共用这里的读写。
const KEY_PREFIX = "safehome:wechatProfile:";
const NICKNAME_MAX_LENGTH = 20;

function storageKey(userId) {
  return `${KEY_PREFIX}${userId}`;
}

function readLocalProfile(userId) {
  if (!userId) return null;
  try {
    const value = wx.getStorageSync(storageKey(userId));
    return value && typeof value === "object" ? value : null;
  } catch (error) {
    return null;
  }
}

function writeLocalProfile(userId, profile) {
  wx.setStorageSync(storageKey(userId), profile);
}

// 设置过或点过“跳过”的账号，登录后不再询问；之后可以在“我的”页点头像修改。
function shouldOfferLocalProfile(userId) {
  if (!userId) return false;
  const profile = readLocalProfile(userId);
  return !(profile && (profile.nickname || profile.avatarPath || profile.skipped));
}

function skipLocalProfile(userId) {
  if (!userId) return;
  writeLocalProfile(userId, { ...(readLocalProfile(userId) || {}), skipped: true });
}

function normalizeNickname(value) {
  return Array.from(String(value || "").replace(/\s+/g, " ").trim()).slice(0, NICKNAME_MAX_LENGTH).join("");
}

function removeLocalFile(path) {
  const root = wx.env && wx.env.USER_DATA_PATH;
  if (!root || typeof path !== "string" || !path.startsWith(`${root}/`)) return;
  try {
    wx.getFileSystemManager().unlink({ filePath: path, fail() {} });
  } catch (error) {
    // 旧头像文件已经不在，不影响新设置。
  }
}

// chooseAvatar 给的是临时文件（开发者工具 http://tmp/…，真机 wxfile://tmp_…），另存后才不会被微信清掉。
function persistAvatar(userId, tempPath) {
  if (/^https:\/\//.test(tempPath)) return Promise.resolve(tempPath);
  const match = /\.(jpe?g|png|webp)$/i.exec(tempPath);
  const extension = match ? match[1].toLowerCase() : "jpg";
  const safeId = String(userId).replace(/[^A-Za-z0-9_-]/g, "");
  const filePath = `${wx.env.USER_DATA_PATH}/safehome-avatar-${safeId}-${Date.now()}.${extension}`;
  return new Promise((resolve, reject) => {
    wx.getFileSystemManager().saveFile({
      tempFilePath: tempPath,
      filePath,
      success: (result) => resolve(result.savedFilePath || filePath),
      fail: () => reject(new Error("头像没有保存成功，请再选一次。")),
    });
  });
}

async function saveLocalProfile(userId, { nickname, avatarTempPath }) {
  if (!userId) throw new Error("请先登录，再设置头像和昵称。");
  const previous = readLocalProfile(userId) || {};
  let avatarPath = previous.avatarPath || "";
  if (avatarTempPath && avatarTempPath !== avatarPath) {
    avatarPath = await persistAvatar(userId, avatarTempPath);
    if (previous.avatarPath && previous.avatarPath !== avatarPath) removeLocalFile(previous.avatarPath);
  }
  const savedNickname = normalizeNickname(nickname);
  const profile = { nickname: savedNickname, avatarPath, skipped: !savedNickname && !avatarPath, updatedAt: Date.now() };
  writeLocalProfile(userId, profile);
  return profile;
}

function clearLocalProfile(userId) {
  if (!userId) return;
  const previous = readLocalProfile(userId) || {};
  removeLocalFile(previous.avatarPath);
  writeLocalProfile(userId, { nickname: "", avatarPath: "", skipped: true, updatedAt: Date.now() });
}

// “我的”页显示：本机设置的头像昵称优先，其次是账号里的昵称（注册时可选填），最后是默认称呼。
function localDisplayIdentity(user, fallbackNickname) {
  const profile = user && user.id ? readLocalProfile(user.id) : null;
  return {
    nickname: (profile && profile.nickname) || (user && user.nickname) || fallbackNickname,
    avatarPath: (profile && profile.avatarPath) || "",
  };
}

module.exports = {
  NICKNAME_MAX_LENGTH,
  readLocalProfile,
  shouldOfferLocalProfile,
  skipLocalProfile,
  saveLocalProfile,
  clearLocalProfile,
  normalizeNickname,
  localDisplayIdentity,
};

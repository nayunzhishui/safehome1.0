// 昵称保存到账号（换手机登录也在，研究者工作台也能看到）；头像只存在这台手机上，按账号分开，
// 因为生产库 avatar_url 只有 191 个字符，放不下图片。登录后的填写卡片和“我的”页共用这里的读写。
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

// 在这台手机上保存过或点过“跳过”，登录后就不再询问；之后可以在“我的”页点头像修改。
// 早先只存本机的版本留下的 nickname/skipped 记录也算问过。
function shouldOfferLocalProfile(userId) {
  if (!userId) return false;
  const profile = readLocalProfile(userId);
  return !(profile && (profile.answered || profile.skipped || profile.avatarPath || profile.nickname));
}

function skipLocalProfile(userId) {
  if (!userId) return;
  writeLocalProfile(userId, { ...(readLocalProfile(userId) || {}), answered: true });
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

// 只处理本机头像；昵称由调用方先保存到账号。
async function saveLocalAvatar(userId, avatarTempPath) {
  if (!userId) throw new Error("请先登录，再设置头像和昵称。");
  const previous = readLocalProfile(userId) || {};
  let avatarPath = previous.avatarPath || "";
  if (avatarTempPath && avatarTempPath !== avatarPath) {
    avatarPath = await persistAvatar(userId, avatarTempPath);
    if (previous.avatarPath && previous.avatarPath !== avatarPath) removeLocalFile(previous.avatarPath);
  }
  const profile = { avatarPath, answered: true, updatedAt: Date.now() };
  writeLocalProfile(userId, profile);
  return profile;
}

function clearLocalAvatar(userId) {
  if (!userId) return;
  const previous = readLocalProfile(userId) || {};
  removeLocalFile(previous.avatarPath);
  writeLocalProfile(userId, { avatarPath: "", answered: true, updatedAt: Date.now() });
}

// 昵称：账号里的优先，其次是早先版本只存本机的昵称，最后是默认称呼；头像只看本机。
function localDisplayIdentity(user, fallbackNickname) {
  const profile = user && user.id ? readLocalProfile(user.id) : null;
  return {
    nickname: (user && user.nickname) || (profile && profile.nickname) || fallbackNickname,
    avatarPath: (profile && profile.avatarPath) || "",
  };
}

module.exports = {
  NICKNAME_MAX_LENGTH,
  readLocalProfile,
  shouldOfferLocalProfile,
  skipLocalProfile,
  saveLocalAvatar,
  clearLocalAvatar,
  normalizeNickname,
  localDisplayIdentity,
};

const DRAFT_VERSION = 1;

function createSubmissionId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function formatSavedAt(timestamp) {
  if (!timestamp) return "尚未保存草稿";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "草稿已保存在本机";
  return `草稿已于 ${`${date.getHours()}`.padStart(2, "0")}:${`${date.getMinutes()}`.padStart(2, "0")} 保存在本机`;
}

function createResilientForm({ storageKey, fields, submissionPrefix, hasContent }) {
  let timer = null;
  let currentSubmissionId = createSubmissionId(submissionPrefix);

  function pick(data) {
    return fields.reduce((result, key) => ({ ...result, [key]: data[key] }), {});
  }

  function restore() {
    try {
      const stored = wx.getStorageSync(storageKey);
      if (!stored || stored.version !== DRAFT_VERSION || !stored.values) return null;
      currentSubmissionId = stored.clientSubmissionId || currentSubmissionId;
      return {
        values: stored.values,
        clientSubmissionId: currentSubmissionId,
        savedAt: stored.savedAt || "",
        saveStatus: formatSavedAt(stored.savedAt),
      };
    } catch (error) {
      return null;
    }
  }

  function save(data) {
    const values = pick(data);
    if (!hasContent(values)) {
      clear(true);
      return { savedAt: "", saveStatus: "尚未填写" };
    }
    const savedAt = new Date().toISOString();
    try {
      wx.setStorageSync(storageKey, { version: DRAFT_VERSION, values, savedAt, clientSubmissionId: currentSubmissionId });
    } catch (error) {
      return { savedAt: "", saveStatus: "本机空间不足，暂时无法保存草稿" };
    }
    try {
      if (wx.enableAlertBeforeUnload) wx.enableAlertBeforeUnload({ message: "这份记录还没有提交，草稿已保存在本机。" });
    } catch (error) { /* older runtimes do not support leave prompts */ }
    return { savedAt, saveStatus: formatSavedAt(savedAt) };
  }

  function schedule(data, callback) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      callback(save(data));
    }, 260);
  }

  function flush(data) {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    return save(data);
  }

  function clear(removeStored = true) {
    if (timer) clearTimeout(timer);
    timer = null;
    if (removeStored) {
      try { wx.removeStorageSync(storageKey); } catch (error) { /* best effort */ }
    }
    try { if (wx.disableAlertBeforeUnload) wx.disableAlertBeforeUnload(); } catch (error) { /* best effort */ }
    currentSubmissionId = createSubmissionId(submissionPrefix);
  }

  return { restore, schedule, flush, clear, getSubmissionId: () => currentSubmissionId };
}

module.exports = { createResilientForm, formatSavedAt };

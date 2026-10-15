const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser } = require("../../utils/authGuard");
const {
  NICKNAME_MAX_LENGTH,
  readLocalProfile,
  saveLocalAvatar,
  skipLocalProfile,
  clearLocalAvatar,
  normalizeNickname,
} = require("../../utils/wechatProfile");

const api = createSafeHomeApi();

// 卡片打开后如果换了账号，不能把昵称写到另一个账号上。
function currentUser(userId) {
  const user = getAuthUser();
  return user && userId && String(user.id || "") === String(userId) ? user : null;
}

// 微信不再直接给出头像昵称（2022-10 起），只能由本人点“用微信头像”、在昵称框点微信昵称。
// 昵称保存到账号，头像只存这台手机。
// after_login：登录后询问一次，“跳过”会记住；edit：从“我的”页修改，可取消或清除。
Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    visible: { type: Boolean, value: false },
    userId: { type: String, value: "" },
    context: { type: String, value: "after_login" },
  },
  data: {
    avatarPreview: "",
    chosenAvatar: "",
    nickname: "",
    hasSaved: false,
    saving: false,
    message: "",
    maxLength: NICKNAME_MAX_LENGTH,
  },
  observers: {
    "visible, userId"(visible, userId) {
      if (!visible) return;
      const profile = readLocalProfile(userId) || {};
      const user = currentUser(userId) || {};
      const nickname = user.nickname || profile.nickname || "";
      this.setData({
        avatarPreview: profile.avatarPath || "",
        chosenAvatar: "",
        nickname,
        hasSaved: !!(profile.avatarPath || nickname),
        saving: false,
        message: "",
      });
      this.ensurePrivacyAuthorization();
    },
  },
  methods: {
    stop() {},

    // 没同意微信隐私保护指引时，昵称框只是普通输入框，不会出现微信昵称；先请微信弹出它的授权。
    ensurePrivacyAuthorization() {
      if (!wx.getPrivacySetting || !wx.requirePrivacyAuthorize) return;
      wx.getPrivacySetting({
        success: (result) => {
          if (result.needAuthorization) wx.requirePrivacyAuthorize({ fail() {} });
        },
      });
    },

    onChooseAvatar(event) {
      const avatarUrl = (event.detail && event.detail.avatarUrl) || "";
      if (!avatarUrl) return;
      this.setData({ avatarPreview: avatarUrl, chosenAvatar: avatarUrl, message: "" });
    },

    onNicknameReview(event) {
      if (event.detail && event.detail.pass === false) {
        this.setData({ message: "这个昵称没有通过微信的安全检查，请换一个。" });
      }
    },

    // 选微信昵称不一定触发 input 事件，按微信建议从表单提交里取值。
    submit(event) {
      if (this.data.saving) return;
      const user = currentUser(this.data.userId);
      if (!user) {
        this.setData({ message: "登录状态已经变了，请重新打开后再设置。" });
        return;
      }
      const nickname = normalizeNickname(((event.detail && event.detail.value) || {}).nickname);
      if (!nickname && !this.data.avatarPreview) {
        this.setData({
          message: this.data.context === "edit"
            ? "还没有选头像，也没有填昵称。"
            : "还没有选头像，也没有填昵称；不想设置可以点“跳过”。",
        });
        return;
      }
      this.setData({ saving: true, message: "" });
      const nicknameSaved = nickname === (user.nickname || "") ? Promise.resolve() : api.updateMyNickname(nickname);
      nicknameSaved
        .then(() => saveLocalAvatar(this.data.userId, this.data.chosenAvatar))
        .then(() => {
          this.setData({ saving: false });
          this.triggerEvent("done", { saved: true });
        })
        .catch((error) => {
          this.setData({ saving: false, message: error.message || "没有保存成功，请检查网络后再试一次。" });
        });
    },

    dismiss() {
      if (this.data.saving) return;
      if (this.data.context !== "edit") skipLocalProfile(this.data.userId);
      this.triggerEvent("done", { saved: false });
    },

    // 清除账号里的昵称和这台手机上的头像。
    clear() {
      if (this.data.saving) return;
      const user = currentUser(this.data.userId);
      if (!user) {
        this.setData({ message: "登录状态已经变了，请重新打开后再设置。" });
        return;
      }
      this.setData({ saving: true, message: "" });
      const nicknameCleared = user.nickname ? api.updateMyNickname("") : Promise.resolve();
      nicknameCleared
        .then(() => {
          clearLocalAvatar(this.data.userId);
          this.setData({ saving: false });
          this.triggerEvent("done", { saved: true });
        })
        .catch((error) => {
          this.setData({ saving: false, message: error.message || "没有清除成功，请检查网络后再试一次。" });
        });
    },
  },
});

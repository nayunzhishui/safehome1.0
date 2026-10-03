const assert = require("node:assert/strict");
const automator = require("miniprogram-automator");

const port = Number(process.env.WECHAT_DEVTOOLS_AUTO_PORT || 9420);

async function main() {
  const miniProgram = await automator.connect({ wsEndpoint: `ws://127.0.0.1:${port}` });
  try {
    // This is a synthetic UI check, never a production service probe.
    await miniProgram.mockWxMethod("getStorageSync", "");
    await miniProgram.evaluate(() => {
      const app = getApp();
      app.globalData.token = "";
      app.globalData.user = null;
      const respond = (options) => {
        const path = options.path || options.url || "";
        const data = path.includes("/api/auth/capabilities")
          ? { wechat_login: { available: false, mode: "" }, phone_login: { available: false } }
          : path.includes("/api/assessments")
            ? { items: [], boundary_notice: "合成空列表，仅用于界面核验" }
            : null;
        const result = data === null
          ? { statusCode: 503, data: { ok: false, error: { code: "synthetic_unavailable" } } }
          : { statusCode: 200, data: { ok: true, data } };
        if (options.success) options.success(result);
        return Promise.resolve(result);
      };
      wx.request = respond;
      wx.cloud = wx.cloud || {};
      wx.cloud.callContainer = respond;
    });
    const loginPage = await miniProgram.reLaunch("/pages/login/index");
    await loginPage.waitFor(() => !getCurrentPages().slice(-1)[0].data.wechatAvailable);
    assert.equal(loginPage.path, "pages/login/index");
    assert.equal(await loginPage.$(".wechat-action"), null, "未配置微信登录时不得显示可点击按钮");
    assert.equal(await loginPage.$(".phone-action"), null, "未配置手机号登录时不得显示授权按钮");
    assert.equal((await loginPage.$$(".auth-unavailable")).length, 2);
    await (await loginPage.$(".primary-action")).tap();
    assert.equal(await loginPage.data("message"), "请填写用户名和密码");
    await loginPage.setData({ wechatAvailable: true, phoneAvailable: true });
    await loginPage.waitFor(".wechat-action");
    assert.ok(await loginPage.$(".wechat-action"), "可用态微信按钮缺失");
    assert.ok(await loginPage.$(".phone-action"), "可用态手机号按钮缺失");

    const assessmentPage = await miniProgram.reLaunch("/pages/assessment/index");
    await assessmentPage.waitFor(() => !getCurrentPages().slice(-1)[0].data.loading);
    assert.equal(assessmentPage.path, "pages/assessment/index");
    assert.ok(await assessmentPage.$(".empty-section-card"), "空列表提示缺失");
    await assessmentPage.setData({ errorMessage: "合成网络失败" });
    await assessmentPage.waitFor(".error-action");
    const retry = await assessmentPage.$(".error-action");
    assert.ok(retry, "网络失败缺少重试入口");
    await retry.tap();
    await assessmentPage.waitFor(() => !getCurrentPages().slice(-1)[0].data.loading);
    assert.equal(await assessmentPage.data("errorMessage"), "");

    const intro = await miniProgram.reLaunch("/pages/getting-started/index");
    assert.equal(intro.path, "pages/getting-started/index");
    assert.equal((await intro.$$(".before-start-link")).length, 3);
    assert.match(await (await intro.$(".before-start-copy")).text(), /不会自动记录同意/);
    const emergency = await miniProgram.reLaunch("/pages/emergency-guide/index");
    assert.equal(emergency.path, "pages/emergency-guide/index");
    assert.match(await (await emergency.$(".safety-intro")).text(), /当地紧急服务/);
    process.stdout.write("微信开发者工具合成界面检查通过；不代表平台能力、真机或正式发布通过。\n");
  } finally {
    await miniProgram.disconnect();
  }
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message || error}\n`);
  process.exitCode = 1;
});

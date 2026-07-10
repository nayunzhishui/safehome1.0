const assert = require("node:assert/strict");
const automator = require("miniprogram-automator");

const port = Number(process.env.WECHAT_DEVTOOLS_AUTO_PORT || 9420);

async function main() {
  const miniProgram = await automator.connect({ wsEndpoint: `ws://127.0.0.1:${port}` });
  try {
    const loginPage = await miniProgram.reLaunch("/pages/login/index");
    await loginPage.waitFor(500);
    assert.equal(loginPage.path, "pages/login/index");
    assert.ok(await loginPage.$(".wechat-action"), "微信登录按钮缺失");
    assert.ok(await loginPage.$(".phone-action"), "手机号登录按钮缺失");

    const assessmentPage = await miniProgram.reLaunch("/pages/assessment/index");
    await assessmentPage.waitFor(500);
    assert.equal(assessmentPage.path, "pages/assessment/index");

    const integrationPage = await miniProgram.reLaunch("/pages/integration-test/index");
    await integrationPage.waitFor(500);
    assert.equal(integrationPage.path, "pages/integration-test/index");
    process.stdout.write("微信开发者工具自动化冒烟检查通过。\n");
  } finally {
    await miniProgram.disconnect();
  }
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message || error}\n`);
  process.exitCode = 1;
});

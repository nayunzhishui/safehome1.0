import { expect, test } from "@playwright/test";


async function expectNoHorizontalOverflow(page: import("@playwright/test").Page) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}


test("login and register expose keyboard focus, status and stable mobile width", async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "登录" })).toBeVisible();

  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "跳到主要内容" })).toBeFocused();
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByRole("alert")).toContainText("请填写用户名和密码");
  await expectNoHorizontalOverflow(page);

  await page.screenshot({ path: testInfo.outputPath("login.png"), fullPage: true });
  await page.goto("/register");
  await expect(page.getByRole("heading", { name: "注册" })).toBeVisible();
  await expect(page.getByRole("button", { name: "注册" })).toHaveCSS("min-height", "44px");
  await expectNoHorizontalOverflow(page);
});


test("family and access denied pages keep actions and explanations readable", async ({ page }, testInfo) => {
  await page.route("**/api/showcase-access", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data: { enabled: false, read_only_role_bypass: false } }) }));
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { user: { id: "parent-e2e", role: "parent", nickname: "测试家长" } } }),
    });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "test-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "parent-e2e", role: "parent", nickname: "测试家长" }));
  });

  await page.goto("/family");
  await expect(page.getByRole("heading", { name: "家庭绑定" })).toBeVisible();
  await expect(page.getByRole("button", { name: "生成绑定码" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "后台页面暂缓" })).toHaveCount(0);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: testInfo.outputPath("family.png"), fullPage: true });

  await page.goto("/content/scales");
  await expect(page.getByRole("heading", { name: "当前账号不能访问此页面" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("未向当前账号开放");
  await expect(page.getByRole("link", { name: "切换账号" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});


test("server identity overrides a forged researcher role", async ({ page }) => {
  await page.route("**/api/showcase-access", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data: { enabled: false, read_only_role_bypass: false } }) }));
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { user: { id: "parent-e2e", role: "parent", nickname: "真实家长" } } }),
    });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "test-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "forged", role: "researcher", nickname: "伪造研究者" }));
  });

  await page.goto("/content/scales");
  await expect(page.getByRole("heading", { name: "当前账号不能访问此页面" })).toBeVisible();
  const storedRole = await page.evaluate(() => JSON.parse(localStorage.getItem("safehome_auth_user") || "{}").role);
  expect(storedRole).toBe("parent");
});


test("invalid token is cleared before protected content renders", async ({ page }) => {
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ ok: false, error: { code: "unauthorized", message: "登录令牌无效" } }),
    });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "invalid-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "forged", role: "admin" }));
  });

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "当前账号不能访问此页面" })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("safehome_auth_token"))).toBeNull();
});

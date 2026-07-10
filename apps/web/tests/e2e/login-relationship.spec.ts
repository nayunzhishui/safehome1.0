import { expect, test } from "@playwright/test";


test("学生注册登录后可浏览关系探索量表", async ({ page }) => {
  const suffix = Date.now().toString(36);
  const username = `student_${suffix}`;
  const password = "student-password-123";

  await page.goto("/register");
  await page.getByLabel("用户名").fill(username);
  await page.getByLabel("密码").fill(password);
  await page.getByLabel("角色").selectOption("student");
  await page.getByRole("button", { name: "注册" }).click();
  await expect(page).toHaveURL(/\/student$/);
  await expect(page.getByRole("heading", { name: "学生阶段性压力反应画像" })).toBeVisible();

  await page.evaluate(() => localStorage.clear());
  await page.goto("/login");
  await page.getByLabel("用户名").fill(username);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page).toHaveURL(/\/student$/);

  await page.goto("/relationship-assessment");
  await expect(page.getByRole("heading", { name: "大学生关系探索测评" })).toBeVisible();
  await expect(page.getByLabel("选择量表")).toContainText("题");
  await expect(page.locator("fieldset").first()).toBeVisible();
});

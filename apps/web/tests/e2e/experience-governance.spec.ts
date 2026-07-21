import { expect, test } from "@playwright/test";


const registry = {
  version: "2026.07-task33-v1",
  status: "engineering_complete_local_external_validation_pending",
  participant_information_architecture: ["记录", "练习", "了解自己", "人工支持"],
  researcher_information_architecture: ["待处理", "参与者", "内容", "研究/导出", "系统状态"],
  home_layout_guard: { preserve_existing_blocks: true, today_step_after: "测一测/情绪日记", today_step_before: "三步开始" },
  design_tokens: { color: ["canvas", "surface", "ink"], patterns: ["form", "table", "timeline"] },
  automated_gates: ["touch_target", "contrast", "focus_visible", "accessible_name", "heading_order", "form_association", "horizontal_overflow", "reduced_motion"],
  form_resilience: ["draft_timestamp", "save_status", "duplicate_submit_guard", "leave_prompt", "restore_entry", "slow_loading_state", "retry_without_reentry"],
  pages: [
    ...Array.from({ length: 40 }, (_, index) => ({ platform: "miniprogram", path: `pages/p${index}/index`, title: `小程序页面${index}`, workspace: "记录", goal: "完成任务", primary_action: "继续", data_source: "api", states: ["loading", "empty", "error", "retry", "success", "permission_denied"], roles: ["parent"], sensitivity: index < 20 ? "high" : "low", owner: "participant_experience", draft_required: index < 10 })),
    ...Array.from({ length: 35 }, (_, index) => ({ platform: "web", path: `/route-${index}`, title: `Web路由${index}`, workspace: "系统状态", goal: "完成任务", primary_action: "查看", data_source: "api", states: ["loading", "empty", "error", "retry", "success", "permission_denied"], roles: ["admin"], sensitivity: index < 12 ? "high" : "low", owner: "research_operations", draft_required: index < 4 })),
  ],
  external_gates: ["large_text", "screen_reader", "wechat_embedded_browser", "android_ios", "formative_cognitive_interviews"].map((gate) => ({ gate, status: "pending_human_device_evidence" })),
  boundary_notice: "自动检查不能替代真人验收。",
};

test("体验工作台保持五工作区、四入口和外部门禁", async ({ page }, testInfo) => {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "admin-t33", role: "admin", nickname: "体验管理员" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path === "/api/ux-governance/workbench") data = { registry, audit_runs: [], evidence_packages: [], external_gates: registry.external_gates, human_device_acceptance_approved: false, formative_research_approved: false, release_approved: false };
    else if (path === "/api/ux-governance/evidence-packages") data = { id: "ux-pkg-1", status: "draft_for_human_ux_review", release_approved: false };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t33" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-t33-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-t33", role: "admin", nickname: "体验管理员" }));
  });

  await page.goto("/system/experience", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "体验与无障碍" })).toBeVisible({ timeout: 15_000 });
  for (const name of ["记录", "练习", "了解自己", "人工支持"]) await expect(page.getByText(name, { exact: true }).last()).toBeVisible();
  const navToggle = page.getByRole("button", { name: "打开导航" });
  if (await navToggle.isVisible()) await navToggle.click();
  for (const name of ["待处理", "参与者", "内容", "研究/导出", "系统状态"]) await expect(page.locator(".adminNavGroup").filter({ hasText: name })).toBeVisible();
  await expect(page.getByText("外部体验验收待完成")).toBeVisible();
  await expect(page.getByRole("button", { name: /通过验收|签字|批准发布/ })).toHaveCount(0);

  const semantics = await page.evaluate(() => {
    const headings = Array.from(document.querySelectorAll("h1,h2,h3,h4,h5,h6")).map((node) => Number(node.tagName.slice(1)));
    const headingSkips = headings.slice(1).filter((level, index) => level - headings[index] > 1);
    const unnamed = Array.from(document.querySelectorAll("button,a,input,select,textarea")).filter((node) => {
      const element = node as HTMLElement;
      if (element.offsetParent === null) return false;
      return !(element.innerText || element.getAttribute("aria-label") || element.getAttribute("title") || (element as HTMLInputElement).value || node.getAttribute("name"));
    }).length;
    const smallTargets = Array.from(document.querySelectorAll("button,.adminNav a")).filter((node) => {
      const element = node as HTMLElement;
      if (element.offsetParent === null) return false;
      const rect = element.getBoundingClientRect();
      return rect.width < 44 || rect.height < 44;
    }).length;
    return { headingSkips: headingSkips.length, unnamed, smallTargets, width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth };
  });
  expect(semantics.headingSkips).toBe(0);
  expect(semantics.unnamed).toBe(0);
  expect(semantics.smallTargets).toBe(0);
  expect(semantics.scroll).toBeLessThanOrEqual(semantics.width + 1);

  const packageButton = page.getByRole("button", { name: "生成待人工核对证据包" });
  if (testInfo.project.name === "desktop-chrome") {
    await packageButton.focus();
    const outline = await packageButton.evaluate((node) => getComputedStyle(node).outlineStyle);
    expect(outline).not.toBe("none");
  }
  await packageButton.click();
  await expect(page.getByRole("status")).toContainText("本地工程覆盖已更新");

  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  const enlarged = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(enlarged.scroll).toBeLessThanOrEqual(enlarged.width + 1);
  await page.emulateMedia({ reducedMotion: "reduce" });
  const motion = await packageButton.evaluate((node) => getComputedStyle(node).transitionDuration);
  expect(motion.split(",").every((value) => Number.parseFloat(value) <= 0.01)).toBeTruthy();
  await page.screenshot({ path: testInfo.outputPath("experience-governance-large-text.png"), fullPage: true });
});

test("关系测评草稿可恢复并复用同一提交标识", async ({ page }) => {
  let submittedKey = "";
  const worksheet = {
    id: "relationship_initiation_intention_action",
    display_title: "关系中的行动方式问卷",
    instructions: "请按近期体验填写。",
    result_disclaimer: "仅用于阶段性观察，不构成诊断。",
    questions: [{ id: "q1", prompt: "我愿意尝试一次主动表达", required: true, options: [{ value: "1", label: "很不符合" }, { value: "9", label: "很符合" }] }],
  };
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "student-t33", role: "student", nickname: "合成学生" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path === "/api/assessments") data = { items: [{ id: worksheet.id }] };
    else if (path === `/api/assessments/${worksheet.id}`) data = worksheet;
    else if (path === "/api/assessment-results") {
      submittedKey = route.request().headers()["idempotency-key"] || "";
      data = { id: "assessment-t33", worksheet_id: worksheet.id };
    } else if (path.endsWith("/profile-position")) data = { available: false, explanation: "当前只保留阶段位置参考。", boundary_notice: "不构成诊断。" };
    await route.fulfill({ status: path === "/api/assessment-results" ? 201 : 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t33-draft" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "student-t33-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "student-t33", role: "student", nickname: "合成学生" }));
  });
  await page.goto("/relationship-assessment", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "关系中的行动方式问卷" })).toBeVisible();
  await page.getByLabel("很符合").check();
  await page.waitForTimeout(450);
  const storedBeforeReload = await page.evaluate(() => localStorage.getItem("safehome:draft:relationship-assessment"));
  expect(storedBeforeReload).toContain("clientSubmissionId");
  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.getByLabel("很符合")).toBeChecked();
  await expect(page.getByText(/已恢复：草稿已于/)).toBeVisible();
  await page.getByRole("button", { name: "提交并查看阶段性画像" }).click();
  await expect.poll(() => submittedKey).toMatch(/^relationship-assessment-/);
  await expect.poll(async () => page.evaluate(() => localStorage.getItem("safehome:draft:relationship-assessment"))).toBeNull();
});

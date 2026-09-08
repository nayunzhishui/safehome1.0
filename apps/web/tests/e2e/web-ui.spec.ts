import { expect, test, type Page } from "@playwright/test";

const routes = ["/", "/login", "/register", "/student", "/about-study", "/assessment", "/student/assessment", "/relationship-assessment", "/assessment/report/ui-preview", "/student/report/ui-preview", "/privacy", "/dashboard", "/goals", "/diaries", "/diaries/ui-preview", "/feedback", "/checkins", "/reports", "/profiles", "/profiles/ui-preview", "/reviews", "/privacy-requests", "/supervision", "/supervision/ui-preview", "/content/review", "/content/scales", "/content/worksheets", "/content/cards", "/content/rules", "/export", "/integration-test", "/family", "/ai-sandbox", "/research/benchmarks", "/research/methodology", "/research/analysis", "/research/therapeutic-assessment", "/research/therapeutic-assessment/quality", "/security/privacy", "/reliability/release", "/system/experience", "/system/operations-governance"];

async function identity(page: Page, role = "admin") {
  await page.addInitScript(({ role }) => {
    sessionStorage.setItem("safehome_auth_token", "web-ui-fixture");
    sessionStorage.setItem("safehome_auth_user", JSON.stringify({ id: "web-ui-fixture", role }));
  }, { role });
  await page.route("**/api/**", route => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/showcase-access") return route.fulfill({ json: { ok: true, data: { enabled: false } } });
    if (pathname === "/api/auth/me") return route.fulfill({ json: { ok: true, data: { user: { id: "web-ui-fixture", role, nickname: "界面合成测试" } } } });
    return route.fulfill({ status: 503, json: { ok: false, error: { code: "service_unavailable", message: "当前连接暂不可用，请稍后重试。" } } });
  });
}

async function stableWidth(page: Page) {
  const size = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(size.scroll).toBeLessThanOrEqual(size.width + 1);
}

for (const route of routes) {
  test(`UI route and network failure: ${route}`, async ({ page }) => {
    await identity(page);
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(route);
    await expect(page.locator("h1").first()).toBeVisible();
    await page.waitForLoadState("networkidle");
    await stableWidth(page);
    expect(errors).toEqual([]);
    await expect(page.locator(".fatalErrorPage")).toHaveCount(0);
    if (route !== "/login" && route !== "/register" && !["/", "/student", "/about-study"].includes(route)) {
      await expect(page.getByRole("link", { name: /^安心陪伴(首页|工作台)$/ }).first()).toBeVisible();
    }
  });
}

test("home has working scene examples, FAQ, anchor links and narrow navigation", async ({ page }, testInfo) => {
  await identity(page);
  await page.goto("/");
  const homeTitle = page.getByRole("heading", { level: 1 });
  await expect(homeTitle).toContainText("陪伴孩子");
  const fontSize = await homeTitle.evaluate(el => parseFloat(getComputedStyle(el).fontSize));
  expect(fontSize).toBeGreaterThanOrEqual(testInfo.project.name.includes("mobile") ? 28 : 48);
  const switcher = page.getByRole("group", { name: "选择演示场景" });
  await switcher.getByRole("button", { name: "手机使用" }).click();
  await expect(page.locator(".previewDiary")).toContainText("约好的手机使用时间到了");
  await expect(switcher.getByRole("button", { name: "手机使用" })).toHaveAttribute("aria-pressed", "true");
  await switcher.getByRole("button", { name: "亲子沟通" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".previewDiary")).toContainText("今天过得怎么样");
  const faq = page.locator(".companionFaq details").nth(1);
  await faq.locator("summary").click();
  await expect(faq).toHaveAttribute("open", "");
  await expect(faq.locator("p")).toBeVisible();
  await faq.locator("summary").click();
  await expect(faq.locator("p")).toBeHidden();
  if ((page.viewportSize()?.width || 0) < 821) {
    await page.getByLabel("展开网站导航").click();
    await expect(page.getByRole("navigation", { name: "移动网站导航" }).getByRole("link", { name: "学生画像", exact: true })).toBeVisible();
  }
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("home.png"), fullPage: true });
});

test("populated goal list keeps selection, details and long content reachable", async ({ page }) => {
  await identity(page);
  const goals = [0, 1].map(i => ({ id: `goal-${i}`, user_id: "ui-parent", scene: i ? "手机使用冲突" : "孩子写作业拖延", smart_goal: i ? "先询问孩子想从哪一步开始。" : "先留意自己的感受，再慢慢表达一个具体请求。".repeat(8), motivation: "合成界面用例", status: "active", start_date: "2026-09-08", created_at: "2026-09-08T09:00:00+08:00" }));
  await page.route("**/api/goals**", route => route.fulfill({ json: { ok: true, data: { items: goals, count: goals.length } } }));
  await page.goto("/goals");
  await expect(page.getByRole("heading", { name: "目标管理", exact: true })).toBeVisible();
  await page.getByRole("button", { name: /手机使用冲突/ }).click();
  await expect(page.locator(".detailPanel")).toContainText("先询问孩子想从哪一步开始");
  await page.getByRole("button", { name: /孩子写作业拖延/ }).click();
  await expect(page.locator(".detailPanel")).toContainText(goals[0].smart_goal);
  await stableWidth(page);
});

test("overview section navigation and optional directory remain available", async ({ page }) => {
  await identity(page);
  await page.goto("/dashboard");
  await expect(page.getByRole("navigation", { name: "总览页内导航" })).toBeVisible();
  await page.getByRole("link", { name: "参与者档案", exact: true }).click();
  await expect(page).toHaveURL(/#overview-participants$/);
  const directory = page.locator(".webPageDirectory");
  await expect(directory.locator(".dashboardGrid")).toBeHidden();
  await directory.locator("summary").click();
  await expect(directory.getByRole("heading", { name: "已完成页面", exact: true })).toBeVisible();
  await stableWidth(page);
});

test("server role restriction is unchanged with session-scoped storage", async ({ page }) => {
  await identity(page, "parent");
  await page.goto("/content/scales");
  await expect(page.getByRole("heading", { name: "当前账号不能访问此页面" })).toBeVisible();
  await expect(page.getByRole("link", { name: "切换账号" })).toBeVisible();
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem("safehome_auth_user") || "{}").role)).toBe("parent");
  await stableWidth(page);
});

test("large training directory remains keyboard-scrollable and exposes details nearby", async ({ page }, testInfo) => {
  await identity(page);
  await page.goto("/content/cards");
  const list = page.locator(".listPanel > .recordList");
  await expect(list).toBeVisible();
  const items = list.getByRole("button");
  expect(await items.count()).toBeGreaterThan(10);
  const last = items.last();
  const title = await last.locator(".recordScene").innerText();
  await last.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".detailPanel")).toContainText(title);
  const dimensions = await list.evaluate(el => ({ height: el.clientHeight, scrollHeight: el.scrollHeight, top: el.scrollTop }));
  expect(dimensions.height).toBeLessThanOrEqual((page.viewportSize()?.width || 0) <= 820 ? 340 : 640);
  expect(dimensions.scrollHeight).toBeGreaterThan(dimensions.height);
  expect(dimensions.top).toBeGreaterThan(0);
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("catalog-selection.png"), fullPage: true });
});

test("detail chapters preserve all training content and safety fields", async ({ page }) => {
  await identity(page);
  await page.goto("/content/cards");
  await expect(page.getByRole("region", { name: "主要内容", exact: true })).toContainText("练习步骤");
  await expect(page.getByRole("region", { name: "适用边界与安全", exact: true })).toContainText("停止规则");
  await expect(page.getByRole("region", { name: "审核、来源与记录信息", exact: true })).toContainText("审核状态");
  await expect(page.locator(".webPageIdentity .summary")).toHaveCount(0);
  await expect(page.locator(".webPageContext")).toContainText("只读查看");
  await stableWidth(page);
});

test("research section navigation resolves to existing focusable content", async ({ page }) => {
  await identity(page);
  for (const path of ["/ai-sandbox", "/research/benchmarks", "/research/methodology", "/research/analysis", "/system/operations-governance", "/security/privacy", "/reliability/release", "/system/experience", "/content/review", "/privacy", "/reports"]) {
    await page.goto(path);
    const nav = page.getByRole("navigation", { name: "本页分区导航" });
    await expect(nav).toBeVisible();
    const hrefs = await nav.locator("a").evaluateAll(links => links.map(link => link.getAttribute("href") || ""));
    for (const href of hrefs) await expect(page.locator(href)).toHaveCount(1);
    await nav.locator("a").last().click();
    await expect(page).toHaveURL(new RegExp(hrefs[hrefs.length - 1] + "$"));
    await stableWidth(page);
  }
});

test("worksheet editor groups retain edits and send the original hidden-entry payload", async ({ page }, testInfo) => {
  await identity(page);
  const worksheet = { id: "ui-sheet", display_title: "合成测评入口", source_title: "合成来源", source_file: "fixture.json", category: "支持性测评", audience_class: "student_support", reflex_node: "", profile_model_id: null, review_status: "pilot_review_required", enabled_for_user: false, boundary_notice: "合成示例，不用于诊断。", result_disclaimer: "支持性参考。", instructions: "", scoring: "", source_version: "fixture", source_type: "database_admin", pages: 1, sections: [], questions: [], recommended_card_ids: [] };
  let payload: Record<string, unknown> | undefined;
  await page.route("**/api/admin/worksheets**", route => {
    if (route.request().method() === "PATCH" || route.request().method() === "PUT") {
      payload = route.request().postDataJSON();
      return route.fulfill({ json: { ok: true, data: { ...worksheet, ...payload } } });
    }
    return route.fulfill({ json: { ok: true, data: { items: [worksheet], count: 1 } } });
  });
  await page.goto("/content/worksheets");
  await expect(page.getByRole("region", { name: "入口与来源" })).toBeVisible();
  await expect(page.getByLabel("量表 ID", { exact: true })).toBeDisabled();
  await page.getByLabel("量表名称", { exact: true }).fill("修改后的合成标题");
  await page.getByRole("textbox", { name: "边界说明", exact: true }).fill("保留非诊断边界");
  await page.getByRole("button", { name: "保存配置", exact: true }).click();
  await expect.poll(() => payload?.display_title).toBe("修改后的合成标题");
  expect(payload?.boundary_notice).toBe("保留非诊断边界");
  expect(payload?.enabled_for_user).toBe(false);
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("worksheet-editor.png"), fullPage: true });
});

test("review summary keeps risk visible and review saving remains internal", async ({ page }, testInfo) => {
  await identity(page);
  let posted: Record<string, unknown> | undefined;
  const profile = { id: "ui-profile", anonymous_id: "synthetic-01", profile_name: "合成画像复核", confidence: 0.4, risk_level: "high", requires_review: true, boundary_notice: "仅用于界面验证的合成数据，不构成诊断。", created_at: "2026-09-08T09:00:00+08:00" };
  await page.route("**/api/profile-results**", route => {
    if (route.request().method() === "POST") { posted = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, data: { id: "ui-review" } } }); }
    return route.fulfill({ json: { ok: true, data: { items: [profile], count: 1 } } });
  });
  await page.goto("/reviews");
  await expect(page.locator(".reviewCaseSummary")).toContainText("高风险");
  await page.getByLabel("人工备注", { exact: true }).fill("只在后台保留的合成复核记录");
  await page.getByRole("button", { name: "保存复核", exact: true }).click();
  await expect.poll(() => posted?.note).toBe("只在后台保留的合成复核记录");
  expect(posted?.visible_to_student).toBe(false);
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("review-case.png"), fullPage: true });
});

test("student report shows interpretation before charts and keeps followup submission", async ({ page }, testInfo) => {
  await identity(page, "student");
  let posted: Record<string, unknown> | undefined;
  const profile = { id: "ui-report", profile_name: "合成阶段性反馈", dimensions: [], boundary_notice: "仅为合成界面示例，不构成诊断。", report: { metrics: [], mechanism: "先看自己的感受，再选择一个小练习。", first_task: "尝试暂停一下。", integrative_path: {}, next_questions: [], sandplay_task: { symbols: [], reflection_questions: [] } } };
  await page.route("**/api/profile-results/**", route => {
    if (route.request().method() === "POST") { posted = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, data: { saved: true } } }); }
    const data = new URL(route.request().url()).pathname.endsWith("/visuals") ? { radar: [], trends: [], keywords: [] } : profile;
    return route.fulfill({ json: { ok: true, data } });
  });
  await page.goto("/student/report/ui-report");
  const interpretation = page.getByRole("heading", { name: "理解本次阶段性线索", exact: true });
  await expect(interpretation).toBeVisible();
  const positions = await page.evaluate(() => { const h = [...document.querySelectorAll('h2')]; return [h.findIndex(x => x.textContent === '理解本次阶段性线索'), h.findIndex(x => x.textContent === '维度雷达图')]; });
  expect(positions[0]).toBeLessThan(positions[1]);
  await page.getByLabel("这一轮的变化或困难", { exact: true }).fill("合成复盘");
  await page.getByRole("button", { name: "保存这一轮", exact: true }).click();
  await expect.poll(() => posted?.text).toBe("合成复盘");
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("student-report.png"), fullPage: true });
});

test("parent report foregrounds response without losing action and print controls", async ({ page }, testInfo) => {
  await identity(page, "parent");
  const report = { role: "合成家长支持性报告", summary: "本次反馈只用于自我观察。", boundary_notice: "合成示例，不用于诊断。", metrics: [], empathy: "看见自己的感受，也留意孩子的回应。", strength: "愿意尝试新的回应。", action_title: "先停一下", action: "先命名自己的情绪。", course: "后续研究意向", scale_report: {} };
  await page.route("**/api/parent-assessments/**", route => route.fulfill({ json: { ok: true, data: { id: "ui-parent-report", report } } }));
  await page.goto("/assessment/report/ui-parent-report");
  await expect(page.getByRole("heading", { name: "结果说明", exact: true })).toBeVisible();
  const titles = await page.locator(".reportPage h2").allTextContents();
  expect(titles.indexOf("结果说明")).toBeLessThan(titles.indexOf("支持性反馈，不作诊断"));
  await expect(page.getByRole("button", { name: "保存或打印报告", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "我愿意了解后续研究", exact: true })).toBeVisible();
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("parent-report.png"), fullPage: true });
});

test("assessment progress remains accessible and back navigation preserves answers", async ({ page }, testInfo) => {
  await identity(page, "student");
  const scale = { scale_code: "fixture", short_name: "合成体验量表", name: "合成体验量表", score_direction: "仅为界面测试", items: [{ item_code: "fixture-1", display_order: 1, text: "这是一道合成题目，用来检查题干与选项的布局。" }] };
  await page.route("**/api/student-assessment", route => route.fulfill({ json: { ok: true, data: { scales: [scale], open_questions: [], boundary_notice: "合成测评，不作诊断。" } } }));
  await page.goto("/student/assessment");
  await expect(page.getByRole("progressbar", { name: "步骤进度" })).toBeVisible();
  await page.getByLabel("我了解本测评用于自我理解和研究反馈，不构成临床诊断。").check();
  await page.getByRole("button", { name: "下一步", exact: true }).click();
  await page.getByLabel("基本符合", { exact: true }).check();
  await page.getByRole("button", { name: "上一步", exact: true }).click();
  await page.getByRole("button", { name: "下一步", exact: true }).click();
  await expect(page.getByLabel("基本符合", { exact: true })).toBeChecked();
  await stableWidth(page);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: testInfo.outputPath("assessment-question.png"), fullPage: true });
});


test("compact website and workspace menus restore keyboard focus and close after navigation", async ({ page }) => {
  await identity(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const toggle = page.getByLabel("展开网站导航");
  await toggle.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".siteMobileNav")).toHaveAttribute("open", "");
  const menu = page.getByRole("navigation", { name: "移动网站导航" });
  await menu.getByRole("link", { name: "核心流程", exact: true }).focus();
  await page.keyboard.press("Escape");
  await expect(menu).toBeHidden();
  await expect(toggle).toBeFocused();
  await toggle.click();
  await menu.getByRole("link", { name: "核心流程", exact: true }).click();
  await expect(page).toHaveURL(/#flow$/);
  await expect(menu).toBeHidden();
  await page.goto("/dashboard");
  await expect(page.getByRole("link", { name: "安心陪伴工作台", exact: true })).toHaveAttribute("href", "/dashboard");
  const workspaceToggle = page.getByRole("button", { name: /打开导航/ });
  await workspaceToggle.click();
  await page.getByRole("navigation", { name: "后台功能导航" }).getByRole("link", { name: "用户与记录", exact: true }).focus();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("navigation", { name: "后台功能导航" })).toBeHidden();
  await expect(workspaceToggle).toBeFocused();
  await expect(workspaceToggle).toHaveAttribute("aria-expanded", "false");
});

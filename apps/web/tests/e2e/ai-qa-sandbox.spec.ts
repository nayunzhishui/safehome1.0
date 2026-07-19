import { expect, test } from "@playwright/test";


test("AI 合成沙盒展示参与者门禁、来源与工程评测边界", async ({ page }, testInfo) => {
  let sessionCreated = false;
  let evaluationCreated = false;
  const session = {
    id: "aiqs-e2e",
    user_id: "researcher-e2e",
    mode: "research_sandbox",
    status: "active",
    synthetic_data: 1,
    context_policy: "current_session_only",
    research_use_allowed: 0,
    created_at: "2026-07-20T00:00:00Z",
    updated_at: "2026-07-20T00:00:00Z",
    messages: [],
  };
  const run = {
    id: "aiqeval-e2e",
    suite_version: "task28-suite-v1",
    provider_version: "fake-safehome-v1",
    knowledge_snapshot_hash: "a".repeat(64),
    metrics: { total: 24, passed: 24, failed: 0, route_accuracy: 1, critical_failures: 0, citation_coverage: 1, diagnostic_violations: 0, human_escalation_rate: 0.16 },
    thresholds: { critical_failures_max: 0 },
    results: [],
    status: "engineering_threshold_passed",
    created_by: "researcher-e2e",
    created_at: "2026-07-20T00:00:00Z",
  };

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const fulfill = (data: unknown) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data }) });
    if (path === "/api/showcase-access") return fulfill({ enabled: false });
    if (path === "/api/auth/me") return fulfill({ user: { id: "researcher-e2e", role: "researcher", nickname: "沙盒研究者" } });
    if (path === "/api/ai-qa/config") return fulfill({
      service_name: "支持性内容助手", participant_enabled: false, sandbox_enabled: true, provider: "fake", stage: "synthetic_research_sandbox",
      governance_status: "blocked_human_review", participant_eligible: false,
      gate_decisions: { provider: { proposed: "undecided", status: "owner_security_review_required" }, human_on_call: { proposed: "undecided", status: "operations_owner_required" } },
      runtime_control: { killed: 0 }, data_policy: { cross_session_memory: false, provider_training: false, real_participant_data: false, write_tools: false },
      boundary_notice: "不构成负责人或生产批准。",
    });
    if (path === "/api/ai-qa/review/evidence") return fulfill({ runs: evaluationCreated ? [run] : [], reviews: [], safety_events: [], provider_events: [], raw_prompts_included: false, actor_scope: "own" });
    if (path === "/api/ai-qa/sessions" && route.request().method() === "GET") return fulfill({ items: sessionCreated ? [session] : [] });
    if (path === "/api/ai-qa/sessions" && route.request().method() === "POST") { sessionCreated = true; return fulfill(session); }
    if (path === "/api/ai-qa/sessions/aiqs-e2e" && route.request().method() === "GET") return fulfill(session);
    if (path === "/api/ai-qa/sessions/aiqs-e2e/messages") return fulfill({
      route: "answered", fixed_response: false, human_escalation: false, boundary_notice: "只基于已发布内容。",
      message: { id: "aiqm-e2e", session_id: "aiqs-e2e", user_id: "researcher-e2e", role: "assistant", content: "可以从训练中心查看已批准训练卡。", citations: [{ content_type: "training_card", content_id: "pause", title: "先暂停一下", version_id: "v-e2e", content_version: "v1", release_id: "r-e2e", payload_hash: "b".repeat(64), excerpt: "情绪升高时先暂停。", governance_status: "published" }], model: { provider: "fake" }, safety: { route: "answered" }, prompt_version: "v1", knowledge_version: "k1", token_estimate: 10, cost_micros: 0, created_at: "2026-07-20T00:00:00Z" },
    });
    if (path === "/api/ai-qa/evaluation/run") { evaluationCreated = true; return fulfill(run); }
    return fulfill({});
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "researcher-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "researcher-e2e", role: "researcher", nickname: "沙盒研究者" }));
  });

  await page.goto("/ai-sandbox");
  await expect(page.getByRole("heading", { name: "支持性内容助手研究沙盒" })).toBeVisible();
  await expect(page.getByText("参与者入口关闭")).toBeVisible();
  await page.getByRole("button", { name: "新建会话" }).click();
  await page.getByRole("button", { name: "运行问答链路" }).click();
  await expect(page.getByText("可以从训练中心查看已批准训练卡。")).toBeVisible();
  await expect(page.getByText("先暂停一下", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "运行评测" }).click();
  await expect(page.getByText("engineering_threshold_passed")).toBeVisible();
  await expect(page.getByText("工程阈值通过不等于心理、伦理、隐私、安全或生产批准。")).toBeVisible();
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("ai-qa-sandbox.png"), fullPage: true });
});

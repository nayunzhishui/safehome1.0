import { expect, test } from "@playwright/test";


test("可靠性工作台呈现三段证据路径且不越过人工门禁", async ({ page }, testInfo) => {
  const registry = {
    version: "2026-07-20-t32-reliability-v1",
    status: "engineering_controls_ready_external_release_gates_pending",
    journeys: [
      ["authentication", "登录"], ["diary_submission", "记录提交"], ["feedback_generation", "反馈生成"],
      ["training_plan", "训练计划"], ["messages", "消息"], ["research_queue", "研究队列"], ["ai_sandbox", "AI合成沙盒"],
    ].map(([journey_id, label]) => ({ journey_id, label, paths: ["/api/example"] })),
    trace_fields: ["request_id", "actor_scope", "module", "journey", "outcome", "error_code", "latency_ms", "retry_count", "recovered"],
    sensitive_fields_forbidden: ["token", "participant_text"],
    job_adapters: [], feature_flags: [],
    fault_scenarios: [{ scenario: "provider_failure", expected: "backoff_or_safe_degradation" }],
    production_slo: { status: "pending_test_cloud_observation", thresholds: null },
    external_gates: ["test_cloud_observation", "wechat_devtools", "on_call_owner"],
    production_release: { approved: false, automatic_signature_allowed: false, temporary_showcase_exception_accepted: false },
  };
  let snapshots: unknown[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "admin-t32", role: "admin", nickname: "可靠性管理员" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path === "/api/reliability/slo-snapshots") {
      data = { id: "slo-1", environment: "local_synthetic", window_minutes: 60, metrics: {}, status: "local_evidence_only", production_slo_frozen: false, created_at: "2026-07-20" };
      snapshots = [data];
    } else if (path === "/api/reliability/drills") data = { id: "drill-1", status: "passed" };
    else if (path === "/api/reliability/evidence-packages") data = { id: "pkg-1", status: "draft_external_gates_pending" };
    else if (path === "/api/reliability/workbench") data = {
      registry, recent_events: [], jobs: [{ id: "job-1", job_type: "notification_delivery", source_type: "notification_delivery", source_id: "synthetic", idempotency_key: "e2e", status: "dead_letter", attempt_count: 2, max_attempts: 2, available_at: "2026-07-20", updated_at: "2026-07-20" }],
      feature_flags: [{ id: "flag-1", flag_name: "participant_journey", version: 1, enabled: true, role_scope: ["parent", "student"], rollout_percent: 100, reason_code: "registry_default", changed_at: "2026-07-20" }],
      slo_snapshots: snapshots, drill_runs: [], evidence_packages: [], production_slo_frozen: false, gradual_release_enabled: false,
    };
    else if (path.endsWith("/recover")) data = { id: "job-1", status: "pending" };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t32" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-t32-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-t32", role: "admin", nickname: "可靠性管理员" }));
  });

  await page.goto("/reliability/release", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "可靠性与发布证据" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("测试云阈值尚未冻结")).toBeVisible();
  await expect(page.getByText("本地机器证据")).toBeVisible();
  await expect(page.getByText("测试云观察", { exact: true })).toBeVisible();
  await expect(page.getByText("人工上线门禁")).toBeVisible();
  await page.getByRole("button", { name: "生成快照" }).click();
  await expect(page.getByRole("status")).toContainText("工程证据已更新");
  await expect(page.getByRole("button", { name: /确认上线|伦理签署|关闭临时越权/ })).toHaveCount(0);
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("reliability-release-workbench.png"), fullPage: true });
});

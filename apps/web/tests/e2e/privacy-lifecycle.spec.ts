import { expect, test } from "@playwright/test";


test("privacy lifecycle desk renders preview and dry-run without overflow", async ({ page }, testInfo) => {
  await page.route("**/api/showcase-access", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, data: { enabled: false } }),
  }));
  await page.route("**/api/auth/me", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, data: { user: { id: "admin-e2e", role: "admin", nickname: "隐私管理员" } } }),
  }));
  await page.route("**/api/privacy/admin/requests/**/preview", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, data: {
      request_id: "privacy-e2e", request_version: 1, policy_version: "privacy-lifecycle-v1-draft-20260720",
      policy_approval_status: "owner_confirmation_required", scope_hash: "a".repeat(64), scope: ["participant_records"],
      modules: [{ scope: "participant_records", label: "参与者记录与支持性测评", method: "delete_or_anonymize_by_whitelist", count: 3, tables: [{ table: "emotion_diaries", count: 3 }] }],
      total_affected: 3,
      retained_categories: [{ key: "audit_minimum", label: "最小审计证据", method: "移除原文并替换标识", legal_basis: "待负责人确认" }],
      external_surfaces: [{ surface: "backups", status: "retention_confirmation_required" }],
      irreversible_notice: "正式执行不可逆。",
    } }),
  }));
  await page.route("**/api/privacy/admin/requests/**/execute", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, data: {
      execution: { id: "execution-e2e", actor_id: "admin-e2e", environment: "test", mode: "dry_run", policy_version: "privacy-lifecycle-v1-draft-20260720", scope_hash: "a".repeat(64), status: "completed", started_at: "2026-07-20T00:00:00Z", completed_at: "2026-07-20T00:00:01Z" },
      result: { mode: "dry_run", deleted: {}, total_deleted: 0, would_affect: 3, external_surfaces: [] }, already_processed: false,
    } }),
  }));
  await page.route("**/api/privacy/admin/requests/privacy-e2e", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, data: {
      request: { id: "privacy-e2e", user_id: "participant-e2e", request_type: "delete_my_data", status: "processing", created_at: "2026-07-20T00:00:00Z", updated_at: "2026-07-20T00:01:00Z", version: 1, handling_scope: ["participant_records"], reason: "停止使用", handled_by: "admin-e2e" },
      actions: [], approvals: [], executions: [], allowed_scopes: ["participant_records"], boundary_notice: "受控处理，不复制敏感原文。",
    } }),
  }));
  await page.route("**/api/privacy/admin/requests**", (route) => {
    if (new URL(route.request().url()).pathname !== "/api/privacy/admin/requests") return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { items: [{ id: "privacy-e2e", user_id: "participant-e2e", request_type: "delete_my_data", status: "processing", handled_by: "admin-e2e", version: 1, created_at: "2026-07-20T00:00:00Z", updated_at: "2026-07-20T00:01:00Z" }], page: 1, page_size: 100, total: 1, has_more: false, boundary_notice: "不返回原文" } }),
    });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-e2e", role: "admin", nickname: "隐私管理员" }));
  });

  await page.goto("/privacy-requests");
  await expect(page.getByRole("heading", { name: "隐私申请处理" })).toBeVisible();
  await page.getByRole("button", { name: "生成范围预览" }).click();
  await expect(page.getByRole("status")).toContainText("3条记录可能受影响");
  await page.getByRole("button", { name: "执行 Dry-run" }).click();
  await expect(page.getByRole("status")).toContainText("Dry-run完成");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("privacy-lifecycle.png"), fullPage: true });
});

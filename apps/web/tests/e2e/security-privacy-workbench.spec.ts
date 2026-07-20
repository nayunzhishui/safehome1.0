import { expect, test } from "@playwright/test";


test("安全隐私工作台呈现正式门禁、对象矩阵与脱敏扫描", async ({ page }, testInfo) => {
  const registry = {
    version: "2026-07-20-t31-security-v1",
    status: "engineering_controls_ready_formal_acceptance_blocked",
    asset_inventory: [
      { asset_id: "identity", location: "users", sensitivity: "high", processor: "auth", authorization_basis: "service", deletion_or_withdrawal: "anonymize" },
      { asset_id: "diary", location: "emotion_diaries", sensitivity: "high", processor: "owner", authorization_basis: "service", deletion_or_withdrawal: "delete" },
    ],
    authorization_matrix: [
      { operation_id: "security.workbench.get", method: "GET", path: "/api/security/workbench", object_type: "security_controls", action: "read", object_scope: "internal_redacted", allowed_roles: ["researcher", "supervisor", "admin"], denied_roles: ["parent", "student"], legacy_admin_token: true, showcase_read_bypass: false, idempotency: { supported: false, required: false } },
      { operation_id: "messages.send.post", method: "POST", path: "/api/messages", object_type: "messages", action: "send", object_scope: "assigned", allowed_roles: ["researcher", "supervisor", "admin"], denied_roles: ["parent", "student"], legacy_admin_token: true, showcase_read_bypass: false, idempotency: { supported: true, required: false } },
    ],
    authorization_summary: { operation_count: 186, showcase_bypass_operation_count: 5, formal_permission_acceptance_passed: false, reason: "展示例外" },
    web_miniprogram_threats: [{ id: "idor", mitigation: "服务端对象授权", detection: "403测试", owner: "backend_owner", residual_risk: "展示例外" }],
    ai_threats: [{ id: "prompt_injection", mitigation: "fake provider", detection: "合成红队", owner: "ai_safety_owner", residual_risk: "真人审核待完成" }],
    identity_controls: {}, privacy_deletion_proof: {},
    temporary_showcase_exception: { enabled: true, risk_id: "T31-F07", scope: ["showcase"], stop_condition: "正式试点或生产发布前必须停用并重跑权限矩阵。", accepted_for_formal_permission_testing: false },
    automated_scans: ["tracked_secret_pattern_scan", "container_non_root_check"],
    external_gates: ["测试云", "真机", "真人签字"],
  };
  let runs: unknown[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "admin-e2e", role: "admin", nickname: "安全管理员" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path === "/api/security/scans") {
      data = { id: "scan-1", mode: "local_static_redacted", hard_checks_passed: true, blockers: [], warnings: ["network_dependency_advisories"], checks: [{ id: "container_non_root", status: "passed", severity: "blocker" }], artifact_hash: "hash", secret_values_returned: false, production_approval_inferred: false };
      runs = [{ id: "scan-1", status: "passed", summary: data }];
    } else if (path === "/api/security/workbench") data = { registry, registry_hash: "registry-hash", runs, events: [{ id: "event-1", event_type: "login_failed", severity: "medium", status: "open", created_at: "2026-07-20" }], deletion_verifications: [{ id: "proof-1", status: "verified" }], scan_execution_enabled: true, formal_permission_acceptance_passed: false };
    else if (path === "/api/security/events/event-1/resolve") data = { id: "event-1", status: "resolved" };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t31" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-e2e", role: "admin", nickname: "安全管理员" }));
  });

  await page.goto("/security/privacy", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "安全、隐私与滥用防护" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("正式权限验收未通过")).toBeVisible();
  await expect(page.getByText("临时展示越权继续保留")).toBeVisible();
  await expect(page.getByText("186")).toBeVisible();
  const scan = page.getByRole("button", { name: "运行本地扫描" });
  await scan.focus();
  await expect(scan).toBeFocused();
  await scan.click();
  await expect(page.getByRole("status")).toContainText("工程证据已更新");
  await page.getByPlaceholder("例如 privacy / researcher").fill("messages");
  await expect(page.getByText("/api/messages")).toBeVisible();
  await expect(page.getByRole("button", { name: /正式批准|安全签字|关闭展示越权/ })).toHaveCount(0);
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("security-privacy-workbench.png"), fullPage: true });
});

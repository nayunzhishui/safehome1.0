import { expect, test } from "@playwright/test";


const capabilities = [
  { id: "capability.ai_qa", title: "受控支持性问答沙盒", intended_use: "只在固定合成环境验证支持性问答边界，不用于诊断或自动治疗决定。", owner: { accountable_role: "engineering_owner", named_owner_status: "pending_human_assignment" }, dependencies: ["api-contract"], data: { object_scopes: ["internal_synthetic"], sensitivity: "moderate_or_low", participant_text_allowed_in_governance_records: false }, open_roles: ["researcher", "supervisor", "admin"], feature_flags: ["AI_QA_ENABLED"], version: "2026-07-21.2", tests: ["fixed replay"], rollback: "关闭开关", governance_status: "synthetic_sandbox_only_participant_release_blocked", technical_implementation_complete: true, production_release_approved: false, operation_ids: ["ai.config"] },
  { id: "capability.privacy", title: "隐私生命周期", intended_use: "受控处理访问、撤回和删除申请，不扩大对象权限。", owner: { accountable_role: "security_privacy_owner", named_owner_status: "pending_human_assignment" }, dependencies: ["api-contract"], data: { object_scopes: ["self"], sensitivity: "high", participant_text_allowed_in_governance_records: false }, open_roles: ["parent", "student", "supervisor", "admin"], feature_flags: [], version: "2026-07-21.2", tests: ["privacy tests"], rollback: "关闭执行开关", governance_status: "engineering_registered_release_approval_pending", technical_implementation_complete: true, production_release_approved: false, operation_ids: ["privacy.list"] },
];

const workbench = {
  registry: { version: "2026-07-21-t34-v1", status: "engineering_registry_complete_release_approval_pending", operation_count: 222, capability_count: capabilities.length, capabilities, external_gates: ["ethics", "test_cloud", "android_ios"], temporary_showcase_exception: { retained: true, formal_permission_acceptance: false, production_release_blocker: true }, treatment_assessment: { synthetic_l0_allowed: true, real_participant_release_allowed: false, blocked_by: ["D01-D26"] }, production_release_approved: false, boundary_notice: "工程完成不等于发布批准。" },
  asset_cards: { cards: [{ id: "risk_keywords", card_type: "rule", current_status: "human_review_pending" }, { id: "profile_model", card_type: "model", current_status: "formal_admission_pending" }, { id: "synthetic_data", card_type: "dataset", current_status: "synthetic_only" }] },
  packages: [{ id: "pkg-1", package_version: "ops-v1", risk_level: "high", target_environment: "local_synthetic", capability_ids: capabilities.map((item) => item.id), manifest_hash: "a".repeat(64), artifact_count: 24, status: "under_review", proposed_by: "researcher-a", production_release_approved: false, reviews: [], approvals: [], replay_runs: [{ id: "run-1", package_id: "pkg-1", suite_version: "fixed-v1", metrics: { total: 27, passed: 27, failed: 0, high_severity_regressions: 0, wording_diff_count: 0 }, snapshot_hash: "b".repeat(64), status: "engineering_replay_passed_human_review_pending", high_severity_regressions: 0, wording_diff_count: 0, contains_real_data: false, created_at: "2026-07-21T00:00:00Z" }] }],
  runtime_controls: [],
  monitor_snapshots: [{ id: "monitor-1", environment: "local_synthetic", window_days: 30, metrics: {}, thresholds: {}, drift_signals: [{ metric: "coverage_rate", direction: "below", value: 0.5, threshold: 0.8, action: "human_review_required" }], review_required: true, automatic_participant_or_family_judgment: false, contains_participant_text: false, created_at: "2026-07-21T00:00:00Z" }],
  incidents: [{ id: "incident-1", capability_id: "capability.ai_qa", incident_type: "ai_safety_failure", severity: "critical", status: "contained_disabled_notifications_queued", summary_code: "synthetic", evidence_hold_hash: "c".repeat(64), capability_disabled: true, notifications: [{ id: "n1", recipient_role: "security_owner", status: "queued", attempt_count: 0, created_at: "2026-07-21T00:00:00Z" }], reported_at: "2026-07-21T00:00:00Z" }],
  evidence_packages: [],
  production_release_approved: false,
};

test("运营治理工作台呈现能力、发布回放、漂移复核和事件停用，不提供生产批准", async ({ page }, testInfo) => {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "admin-t34", role: "admin", nickname: "运营管理员" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path === "/api/operations-governance/workbench") data = workbench;
    else if (path === "/api/operations-governance/monitoring/snapshots") data = workbench.monitor_snapshots[0];
    else if (path === "/api/operations-governance/evidence-packages") data = { id: "evidence-1", status: "draft_for_external_governance_review", production_release_approved: false };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t34" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-t34-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-t34", role: "admin", nickname: "运营管理员" }));
  });

  await page.goto("/system/operations-governance", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "内容、数据与模型运营治理" })).toBeVisible({ timeout: 15_000 });
  for (const label of ["能力与开放边界", "不可变发布包", "固定合成回放", "漂移复核", "事件与停用"]) await expect(page.getByText(label, { exact: true }).first()).toBeVisible();
  await expect(page.getByText("生产发布未批准")).toBeVisible();
  await expect(page.getByRole("button", { name: /批准生产|生产发布批准|代签/ })).toHaveCount(0);
  await expect(page.getByText(/不判断参与者或家庭变差/)).toBeVisible();
  await expect(page.getByText(/能力保持停用/)).toBeVisible();

  await page.getByRole("button", { name: "生成聚合快照" }).click();
  await expect(page.getByRole("status")).toContainText("本地运营工程证据已更新");
  await page.getByRole("button", { name: "生成待人工核对证据包" }).click();
  await expect(page.getByRole("status")).toContainText("人工、伦理、云、真机和生产批准仍未签署");

  const geometry = await page.evaluate(() => ({
    width: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
    small: Array.from(document.querySelectorAll("button,input,select,a")).flatMap((node) => {
      const element = node as HTMLElement;
      if (element.offsetParent === null) return [];
      const rect = element.getBoundingClientRect();
      return rect.height < 44 || rect.width < 44 ? [{ tag: element.tagName, text: element.innerText || element.getAttribute("aria-label") || "", className: element.className, width: rect.width, height: rect.height }] : [];
    }),
  }));
  expect(geometry.scroll).toBeLessThanOrEqual(geometry.width + 1);
  expect(geometry.small).toEqual([]);

  if (testInfo.project.name === "desktop-chrome") {
    await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
    const enlarged = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
    expect(enlarged.scroll).toBeLessThanOrEqual(enlarged.width + 1);
    await page.screenshot({ path: testInfo.outputPath("operations-governance-large-text.png"), fullPage: true });
  }
});

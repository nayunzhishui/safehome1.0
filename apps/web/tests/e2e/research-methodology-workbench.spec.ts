import { expect, test } from "@playwright/test";


test("研究方法工作台区分机器证据与真人冻结并保持窄屏可用", async ({ page }, testInfo) => {
  const registry = {
    version: "2026-07-20-t30-methodology-v1",
    status: "draft_before_freeze",
    real_outcome_data_accessed: false,
    formal_freeze_allowed: false,
    confirmatory_analysis_allowed: false,
    product_lines: [
      { id: "journey", primary_question: "参与者能否完成唯一下一步？", prohibited_interpretation: "完成更多不等于心理改善。" },
      { id: "training", primary_question: "推荐训练能否被理解和替换？", prohibited_interpretation: "完成率不等于疗效。" },
    ],
    participant_flow_states: ["eligible", "completed", "technical_failure"],
    measures: [
      { measure_id: "regulatory_focus_relationship_18", display_name: "关系中的行动方式问卷", item_count: 18, review_status: "approved", freeze_status: "draft_before_freeze", score_separation: { raw_scale: { min: 1, max: 9 }, model_input_scale: { min: 1, max: 5 } } },
      { measure_id: "student_profile_v1", display_name: "学生支持性画像", item_count: 12, review_status: "pilot_ready", freeze_status: "draft_before_freeze" },
    ],
    metrics: [], missingness_plan: {}, longitudinal_plan: {}, analysis_sequence: {}, simulation_plan: {},
    reporting_standards: [{ id: "APA_JARS_QUANT", status: "applicable", official_url: "https://example.invalid/jars", accessed_on: "2026-07-20" }],
    signature_requirements: [{ role: "research_lead", status: "pending_human_signature", evidence_required: "primary" }],
    unresolved_blockers: ["unique_primary_outcome", "sample_size_basis"],
    boundary_notice: "不读取主要真实结果，不构成伦理批准或负责人签字。",
  };
  const version = { id: "rmv-1", version: registry.version, status: registry.status, registry_hash: "1234567890abcdef1234", formal_freeze_allowed: 0, real_outcome_data_accessed: 0, registry, created_by: "admin-e2e", created_at: "2026-07-20" };
  let checks: unknown[] = [];
  let simulations: unknown[] = [];
  let packages: unknown[] = [];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "admin-e2e", role: "admin", nickname: "方法管理员" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path === "/api/research/methodology/config") data = { status: registry.status, formal_freeze_recorded: false, confirmatory_analysis_allowed: false, real_outcome_data_accessed: false, workbench_enabled: true, boundary_notice: registry.boundary_notice, registry_version: registry.version, measure_count: 2, product_line_count: 2, unresolved_blocker_count: 2, runtime_control: { disabled: 0 } };
    else if (path === "/api/research/methodology/registry") data = registry;
    else if (path === "/api/research/methodology/versions" && route.request().method() === "GET") data = { items: [version] };
    else if (path === "/api/research/methodology/versions/sync") data = version;
    else if (path === "/api/research/methodology/checks/run") { data = { id: "rmc-1", version_id: "rmv-1", artifact_hash: "checkhash", hard_checks: { all_registered: true }, hard_check_passed: true, formal_freeze_ready: false, formal_freeze_recorded: false, real_outcome_rows_read: 0, status: "machine_structure_complete_human_freeze_pending" }; checks = [data]; }
    else if (path === "/api/research/methodology/simulations/run") { data = { id: "rms-1", version_id: "rmv-1", artifact_hash: "simhash", parameters: { seed: 20260720 }, metrics: { contains_real_data: false, confirmatory_power_claim: false }, status: "engineering_feasibility_only_human_design_freeze_pending" }; simulations = [data]; }
    else if (path === "/api/research/methodology/evidence-packages") { data = { id: "rmep-1", status: "draft_for_human_signature", formal_freeze_recorded: false }; packages = [data]; }
    else if (path === "/api/research/methodology/evidence") data = { checks, simulations, packages };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t30" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-e2e", role: "admin", nickname: "方法管理员" }));
  });

  await page.goto("/research/methodology", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "心理测量与研究方法工作台" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("人工签字待完成")).toBeVisible();
  await expect(page.getByText("0 行")).toBeVisible();
  await expect(page.getByText("九点原分")).toBeVisible();
  await expect(page.getByText("1–5 · transformed_scores_json")).toBeVisible();
  await expect(page.getByRole("button", { name: /正式冻结|负责人签字|伦理批准/ })).toHaveCount(0);
  const runCheck = page.getByRole("button", { name: "运行结构检查" });
  await runCheck.focus();
  await expect(runCheck).toBeFocused();
  await runCheck.click();
  await page.getByRole("button", { name: "运行合成仿真" }).click();
  await page.getByRole("button", { name: "生成证据包" }).click();
  await expect(page.getByRole("status")).toContainText("仅形成工程证据");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("research-methodology-workbench.png"), fullPage: true });
});

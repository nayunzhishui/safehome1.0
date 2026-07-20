import { expect, test } from "@playwright/test";


test("离线基准工作台呈现许可门禁、合成运行和盲标边界", async ({ page }, testInfo) => {
  const cards = [
    { id: "safehome_synthetic_affect_240_v1", name: "安心陪伴合成中文情绪事件240例", source_url: "project://synthetic", source_version: "v1", language: "zh-CN", platform: "synthetic", population: "synthetic_no_people", context: "合成", license: "project-owned-synthetic", content_rights_status: "approved_internal_synthetic", sensitivity: "none_synthetic", allowed_uses: ["engineering_test"], prohibited_uses: ["production_training"], artifact_sha256: "hash", local_path: "content/synthetic.json", ingest_status: "local_synthetic_ready", deletion_method: "rebuild", review_note: "不含真实参与者。", registry_version: "v1", created_at: "2026-07-20", updated_at: "2026-07-20" },
    { id: "goemotions", name: "GoEmotions", source_url: "https://example.invalid", source_version: "reviewed", language: "en", platform: "Reddit-derived", population: "unknown", context: "social", license: "CC-BY-4.0 notice", content_rights_status: "human_review_required", sensitivity: "public_user_generated_text", allowed_uses: ["metadata_review_only"], prohibited_uses: ["download_before_approval"], artifact_sha256: null, local_path: null, ingest_status: "blocked_rights_review", deletion_method: "remove", review_note: "当前只登记链接。", registry_version: "v1", created_at: "2026-07-20", updated_at: "2026-07-20" },
  ];
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path === "/api/auth/me") data = { user: { id: "admin-e2e", role: "admin", nickname: "方法管理员" } };
    else if (path === "/api/showcase-access") data = { enabled: false };
    else if (path.endsWith("/config")) data = { enabled: true, external_ingest_enabled: false, production_replacement_allowed: false, registry_version: "v1", registry_status: "engineering_registry_ready_human_rights_review_pending", annotation_status: "draft_human_annotation_pending", synthetic_case_count: 240, runtime_control: { disabled: 0 }, boundary_notice: "公开不等于可训练。" };
    else if (path.endsWith("/dataset-cards")) data = { items: cards };
    else if (path.endsWith("/dataset-cards/sync")) data = { registry_version: "v1", card_count: 2, external_downloaded: false };
    else if (path.endsWith("/runs/network")) data = { id: "run-1" };
    else if (path.endsWith("/runs")) data = { items: [] };
    else if (path.endsWith("/cases")) data = { items: [{ id: "syn-affect-001", text: "我感到担心。", synthetic: true, already_annotated: false }], offset: 0, limit: 12, total: 240, blind: true, generator_labels_included: false };
    else if (path.endsWith("/agreement")) data = { complete_double_annotated_cases: 0, required_cases: 200, distinct_annotators: 0, emotion_cohen_kappa: null, mean_valence_gap: null, mean_arousal_gap: null, human_gold_release_eligible: false, human_gold_released: false, boundary_notice: "未发布" };
    else if (path.endsWith("/annotations")) data = { saved: true, generator_label_visible: false };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-t29" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-e2e", role: "admin", nickname: "方法管理员" }));
  });

  await page.goto("/research/benchmarks", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "公开数据与算法基准" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("生产替换关闭")).toBeVisible();
  await expect(page.getByText("当前只登记链接。")).toBeVisible();
  await expect(page.getByText("不是人工金标准")).toBeVisible();
  await page.getByRole("button", { name: "网络算法基准" }).focus();
  await expect(page.getByRole("button", { name: "网络算法基准" })).toBeFocused();
  await page.getByRole("button", { name: "保存当前标注" }).click();
  await expect(page.getByRole("status")).toContainText("保存盲标完成");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("offline-benchmark-workbench.png"), fullPage: true });
});

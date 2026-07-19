import { expect, test } from "@playwright/test";

const version = {
  id: "cgv-e2e",
  content_type: "training_card",
  item_id: "emotion_naming",
  version: "e2e-v2",
  payload_hash: "a".repeat(64),
  payload: { id: "emotion_naming", title: "给情绪一个名字" },
  metadata: { source: "项目自研", source_version: "v2", copyright_status: "owned", age_scope: "12岁以上", audience: "student,parent", change_summary: "合成验收草稿" },
  status: "pending_review",
  created_by: "admin-e2e",
  created_at: "2026-07-20T00:00:00Z",
  updated_at: "2026-07-20T00:00:00Z",
  reviews: [],
  releases: [],
  validation: { ok: true, errors: [], warnings: [], payload_hash_valid: true },
  dependency_impact: { has_dependencies: true, impacts: [{ dependency_type: "recommendation_rule" }] },
};

test("内容治理工作台呈现草稿、diff、审核门禁与合成回放", async ({ page }) => {
  test.setTimeout(120_000);
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    let data: unknown = {};
    if (url.pathname === "/api/auth/me") data = { user: { id: "admin-e2e", role: "admin", nickname: "内容管理员" } };
    else if (url.pathname === "/api/showcase-access") data = { enabled: true };
    else if (url.pathname === "/api/content-review/inventory") data = { items: [{ content_type: "training_card", item_id: "emotion_naming", source_file: "training_cards.json", source_version: "v1", active_hash: "b".repeat(64), governed_version: { id: version.id, version: version.version, status: version.status, payload_hash: version.payload_hash } }], missing_sources: ["faq.json"], import_policy: "register_only_never_auto_approve" };
    else if (url.pathname === "/api/content-review/versions") data = { items: [version] };
    else if (url.pathname.endsWith("/diff")) data = { version_id: version.id, baseline: "active_content", changed: true, diff: ["-旧标题", "+给情绪一个名字"], truncated: false };
    else if (url.pathname === `/api/content-review/versions/${version.id}`) data = version;
    else if (url.pathname === "/api/content-review/replay") data = { summary: { total: 2, passed: 2, failed: 0 }, replay_hash: "c".repeat(64), evidence_level: "synthetic_only", contains_real_data: false, results: [] };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data, request_id: "e2e-request" }) });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-e2e", role: "admin", nickname: "内容管理员" }));
  });

  await page.goto("/content/review", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "内容治理工作台" })).toBeVisible();
  await expect(page.getByText("不可变哈希", { exact: false })).toBeVisible();
  await expect(page.getByText("+给情绪一个名字", { exact: false })).toBeVisible();
  await expect(page.getByRole("strong").filter({ hasText: "研究方法" })).toBeVisible();
  await expect(page.getByRole("strong").filter({ hasText: "心理专业" })).toBeVisible();
  await expect(page.getByRole("button", { name: "运行固定回放" })).toBeVisible();
  await page.getByRole("button", { name: "新建草稿" }).click();
  await expect(page.getByRole("heading", { name: "新建不可变草稿" })).toBeVisible();
});

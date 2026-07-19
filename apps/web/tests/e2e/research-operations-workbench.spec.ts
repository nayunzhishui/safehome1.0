import { expect, test } from "@playwright/test";


test("research operations workbench supports narrow screens, keyboard focus and claim recovery", async ({ page }, testInfo) => {
  let version = 0;
  let status = "open";
  const workItem = () => ({
    id: "work-item-e2e",
    queue_type: "supervision",
    source_type: "supervision_requests",
    source_id: "supervision-e2e",
    user_id: "participant-e2e",
    priority: "attention",
    status,
    assignee_id: status === "claimed" ? "admin-e2e" : null,
    lease_expires_at: status === "claimed" ? "2026-07-20T01:00:00Z" : null,
    due_at: null,
    version,
    resolution_code: null,
    closed_at: null,
    last_action_at: null,
    created_at: "2026-07-20T00:00:00Z",
    updated_at: "2026-07-20T00:00:00Z",
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const fulfill = (data: unknown) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, data }) });
    if (path === "/api/showcase-access") return fulfill({ enabled: false, read_only_role_bypass: false });
    if (path === "/api/auth/me") return fulfill({ user: { id: "admin-e2e", role: "admin", nickname: "运营管理员" } });
    if (path === "/api/research/operations") return fulfill({
      scope: "all_participants", generated_at: "2026-07-20T00:00:00Z",
      notification_preferences: { accepted: 1, rejected: 0, consumed: 0, unknown: 0 },
      notification_deliveries: { pending: 0, sending: 0, sent: 1, failed: 0, retry_queue: 0, exhausted: 0, overdue: 0 },
      failure_reasons: [], backlog: { stage_feedback: 0, supervision: 1, risk_review: 0, privacy_requests: 0 },
      privacy_management_available: true, boundary_notice: "只显示必要运营信息。",
    });
    if (path === "/api/research/queues") return fulfill({
      queue: "supervision",
      items: [{ ...workItem(), work_item_id: "work-item-e2e", title: "人工支持待处理", wait_minutes: 12 }],
      page: 1, page_size: 20, total: 1, has_more: false, scope: "all_participants", boundary_notice: "不返回参与者原文。",
    });
    if (path === "/api/research/work-items/metrics") return fulfill({
      scope: "all_participants", generated_at: "2026-07-20T00:00:00Z", window_days: 7,
      totals: { open: status === "open" ? 1 : 0, claimed: status === "claimed" ? 1 : 0, processing: 0, waiting: 0, completed: 0, closed: 0, dead_letter: 0 },
      sla: { overdue: 0, expired_leases: 0 }, close_reasons: [], workload: [], trend: [{ day: "2026-07-20", opened: 1, closed: 0 }],
      quality_boundary: "工作量不用于评价心理支持质量。",
    });
    if (path === "/api/research/work-items/work-item-e2e/actions") {
      version += 1;
      status = "claimed";
      return fulfill({ work_item: workItem(), already_processed: false });
    }
    if (path === "/api/research/work-items/work-item-e2e") return fulfill({
      work_item: workItem(),
      source: { source_type: "supervision_requests", source_id: "supervision-e2e", user_id: "participant-e2e", read_only: true },
      notes: [], actions: status === "claimed" ? [{ id: "action-e2e", actor_id: "admin-e2e", actor_role: "admin", action: "claim", from_status: "open", to_status: "claimed", created_at: "2026-07-20T00:01:00Z" }] : [],
      boundary_notice: "原始参与者内容保持只读。",
    });
    if (path === "/api/research/participants") return fulfill({ items: [], count: 0, scope: "all_participants", boundary_notice: "授权范围" });
    if (path === "/api/text-analysis/summary") return fulfill({ items: {}, raw_text_included: false, boundary_notice: "聚合" });
    if (path === "/api/relationship-pilot/researcher/dashboard") return fulfill({ items: [], count: 0 });
    return fulfill({ items: [], count: 0, total: 0, page: 1, page_size: 50, has_more: false });
  });
  await page.addInitScript(() => {
    localStorage.setItem("safehome_auth_token", "admin-e2e-token");
    localStorage.setItem("safehome_auth_user", JSON.stringify({ id: "admin-e2e", role: "admin", nickname: "运营管理员" }));
  });

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "提醒与人工工作水位" })).toBeVisible();
  await page.getByRole("button", { name: "查看人工支持" }).focus();
  await expect(page.getByRole("button", { name: "查看人工支持" })).toBeFocused();
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: /人工支持待处理/ }).click();
  await expect(page.getByText("原始参与者内容保持只读。")).toBeVisible();
  await page.getByRole("button", { name: "领取", exact: true }).click();
  await expect(page.locator(".workItemDetail .countBadge")).toHaveText("已领取");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
  await page.screenshot({ path: testInfo.outputPath("research-operations-workbench.png"), fullPage: true });
});

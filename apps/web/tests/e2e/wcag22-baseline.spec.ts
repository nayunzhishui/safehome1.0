import { expect, test } from "@playwright/test";

const publicPages = ["/login", "/register", "/privacy"];

async function accessibleName(locator: import("@playwright/test").Locator): Promise<string> {
  return locator.evaluate((element) => {
    const ariaLabel = element.getAttribute("aria-label")?.trim();
    if (ariaLabel) return ariaLabel;
    const labelledBy = element.getAttribute("aria-labelledby")?.trim();
    if (labelledBy) {
      const text = labelledBy
        .split(/\s+/)
        .map((id) => document.getElementById(id)?.textContent?.trim() || "")
        .filter(Boolean)
        .join(" ");
      if (text) return text;
    }
    if (element instanceof HTMLInputElement || element instanceof HTMLSelectElement || element instanceof HTMLTextAreaElement) {
      const labels = Array.from(element.labels || [])
        .map((label) => label.textContent?.trim() || "")
        .filter(Boolean)
        .join(" ");
      if (labels) return labels;
      const placeholder = element.getAttribute("placeholder")?.trim();
      if (placeholder) return placeholder;
    }
    return element.textContent?.trim() || element.getAttribute("title")?.trim() || "";
  });
}

for (const path of publicPages) {
  test(`${path} has named form controls and actionable buttons`, async ({ page }) => {
    await page.goto(path);
    const controls = page.locator("input:not([type=hidden]), select, textarea, button");
    const count = await controls.count();
    for (let index = 0; index < count; index += 1) {
      const control = controls.nth(index);
      if (!(await control.isVisible())) continue;
      expect((await accessibleName(control)).length, `${path} control ${index} needs an accessible name`).toBeGreaterThan(0);
    }
  });

  test(`${path} primary controls satisfy WCAG 2.2 minimum target size`, async ({ page }) => {
    await page.goto(path);
    const controls = page.locator("button, input:not([type=hidden]), select, textarea");
    const count = await controls.count();
    for (let index = 0; index < count; index += 1) {
      const control = controls.nth(index);
      if (!(await control.isVisible())) continue;
      const box = await control.boundingBox();
      if (!box) continue;
      expect(box.width, `${path} control ${index} width`).toBeGreaterThanOrEqual(24);
      expect(box.height, `${path} control ${index} height`).toBeGreaterThanOrEqual(24);
    }
  });

  test(`${path} does not skip visible heading levels`, async ({ page }) => {
    await page.goto(path);
    const levels = await page.locator("h1, h2, h3, h4, h5, h6").evaluateAll((elements) =>
      elements
        .filter((element) => {
          const style = window.getComputedStyle(element);
          return style.display !== "none" && style.visibility !== "hidden";
        })
        .map((element) => Number(element.tagName.slice(1))),
    );
    for (let index = 1; index < levels.length; index += 1) {
      expect(levels[index] - levels[index - 1], `${path} heading ${index}`).toBeLessThanOrEqual(1);
    }
  });

  test(`${path} keyboard focus remains visibly indicated`, async ({ page }) => {
    await page.goto(path);
    const target = page.locator("button, input:not([type=hidden]), select, textarea, a[href]").filter({ visible: true }).first();
    if ((await target.count()) === 0) return;
    await target.focus();
    const visibleFocus = await target.evaluate((element) => {
      const style = window.getComputedStyle(element);
      const outlineVisible = style.outlineStyle !== "none" && Number.parseFloat(style.outlineWidth || "0") > 0;
      const shadowVisible = style.boxShadow !== "none";
      return outlineVisible || shadowVisible;
    });
    expect(visibleFocus, `${path} first interactive control should show focus`).toBe(true);
  });
}

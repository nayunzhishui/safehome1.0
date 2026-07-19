import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromWeb = createRequire(path.join(ROOT, "apps", "web", "package.json"));
const { chromium } = requireFromWeb("playwright");
const VIEWPORTS = [375, 430, 768, 1440];


function rpxToPx(source) {
  return source.replace(/(-?\d+(?:\.\d+)?)rpx/g, (_, raw) => `${Number(raw) / 2}px`);
}


async function componentCss() {
  const paths = [
    "apps/miniprogram/app.wxss",
    "apps/miniprogram/components/page-state/index.wxss",
    "apps/miniprogram/components/status-pill/index.wxss",
    "apps/miniprogram/components/journey-action-card/index.wxss",
    "apps/miniprogram/components/feedback-rating/index.wxss",
  ];
  const sources = await Promise.all(paths.map((item) => fs.readFile(path.join(ROOT, item), "utf8")));
  return rpxToPx(sources.join("\n").replace("page {", ":root {"));
}


async function previewHtml() {
  const css = await componentCss();
  return `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>T23 participant visual audit</title>
<style>${css}
*{box-sizing:border-box}body{margin:0;background:var(--safe-bg);color:var(--safe-title);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}main{width:min(100%,1080px);margin:0 auto;padding:24px 20px 48px}h1{margin:0 0 6px;font-size:28px;line-height:1.25}.qa-intro{margin:0 0 24px;color:var(--safe-muted);font-size:15px;line-height:1.6}.qa-grid{display:grid;grid-template-columns:1fr;gap:20px}.qa-panel{min-width:0;display:grid;align-content:start;gap:12px}.qa-label{margin:0;color:var(--safe-primary-deep);font-size:14px;font-weight:800}.page-state__loader text{display:block}.feedback-rating-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.feedback-rating-option{width:100%}@media(min-width:700px){.qa-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}</style></head>
<body><main><h1>参与者关键状态</h1><p class="qa-intro">核对主行动、状态恢复、反馈评价和触控尺寸。这里不展示诊断或成长总分。</p><div class="qa-grid">
<section class="qa-panel"><p class="qa-label">主任务 · 可继续</p><div class="journey-action journey-action--ready" role="region" aria-label="今天的一小步"><div class="journey-action__head"><div class="journey-action__marker" aria-hidden="true">1</div><span class="journey-action__kicker">今天的一小步</span><span class="status-pill status-pill--success" role="status" aria-label="状态：可以继续">可以继续</span></div><div class="journey-action__content"><span class="journey-action__title">记录一件刚发生的小事</span><span class="journey-action__description">只写清谁在场、发生了什么和自己最明显的反应。</span><span class="journey-action__meta">约 2 分钟</span><button class="journey-action__button" aria-label="开始记录一件刚发生的小事">开始记录</button><span class="journey-action__boundary">这只是一个可选建议，可按自己的节奏决定是否继续。</span></div></div></section>
<section class="qa-panel"><p class="qa-label">主任务 · 读取失败</p><div class="journey-action journey-action--error" role="region" aria-label="今天的一小步"><div class="journey-action__head"><div class="journey-action__marker" aria-hidden="true">1</div><span class="journey-action__kicker">今天的一小步</span></div><div class="journey-action__content" role="status"><span class="journey-action__title">暂时没有读取到下一步</span><span class="journey-action__description">请检查网络后重新读取，原有入口仍可使用。</span><button class="journey-action__button journey-action__button--secondary" aria-label="重新读取今天的一小步">重新读取</button></div></div></section>
<section class="qa-panel"><p class="qa-label">加载、空态与错误</p><div class="page-state page-state--loading" role="status" aria-live="polite"><div class="page-state__loader" aria-hidden="true"><text></text><text></text><text></text></div><div class="page-state__copy"><span class="page-state__title">正在整理已保存的线索</span><span class="page-state__description">四类信息会分别读取，不会合并成总分。</span></div></div><div class="page-state page-state--empty" role="status" aria-live="polite"><div class="page-state__mark" aria-hidden="true">·</div><div class="page-state__copy"><span class="page-state__title">还没有记录或练习</span><span class="page-state__description">可以先留下一件具体小事。</span></div></div><div class="page-state page-state--error" role="status" aria-live="polite"><div class="page-state__mark" aria-hidden="true">!</div><div class="page-state__copy"><span class="page-state__title">内容暂时没有读取成功</span><span class="page-state__description">网络恢复后可重新读取。</span></div><button class="page-state__action" aria-label="重新读取内容">重新读取</button></div></section>
<section class="qa-panel"><p class="qa-label">共同核对</p><div class="feedback-rating"><span class="feedback-rating-prompt">这段内容与你的实际情况相符吗？</span><div class="feedback-rating-options"><button class="feedback-rating-option feedback-rating-option--active" aria-label="评价为符合" aria-pressed="true">符合</button><button class="feedback-rating-option" aria-label="评价为部分符合" aria-pressed="false">部分符合</button><button class="feedback-rating-option" aria-label="评价为不符合" aria-pressed="false">不符合</button><button class="feedback-rating-option feedback-rating-option--care" aria-label="评价为让我不舒服" aria-pressed="false">让我不舒服</button></div><span class="feedback-rating-note" role="status">已记录你的核对，可以随时调整。</span></div></section>
</div></main></body></html>`;
}


async function run() {
  const outputArg = process.argv.find((item) => item.startsWith("--output-dir="));
  const outputDir = path.resolve(outputArg ? outputArg.slice("--output-dir=".length) : path.join(ROOT, ".codex_tmp", "task23-05-visual-audit"));
  await fs.mkdir(outputDir, { recursive: true });
  const htmlPath = path.join(outputDir, "preview.html");
  await fs.writeFile(htmlPath, await previewHtml(), "utf8");

  const browser = await chromium.launch({ headless: true, channel: "chrome" });
  for (const width of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(pathToFileURL(htmlPath).href);
    await page.waitForLoadState("networkidle");
    const dimensions = await page.evaluate(() => ({ clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth }));
    if (dimensions.scrollWidth > dimensions.clientWidth + 1) throw new Error(`horizontal overflow at ${width}px: ${JSON.stringify(dimensions)}`);

    const buttons = page.locator("button");
    for (let index = 0; index < await buttons.count(); index += 1) {
      const button = buttons.nth(index);
      const box = await button.boundingBox();
      const name = ((await button.getAttribute("aria-label")) || (await button.innerText())).trim();
      if (!name) throw new Error(`button ${index} has no accessible name at ${width}px`);
      if (!box || box.height < 44) throw new Error(`button ${name} is below 44px at ${width}px: ${JSON.stringify(box)}`);
    }

    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => ({ tag: document.activeElement?.tagName, name: document.activeElement?.getAttribute("aria-label") || document.activeElement?.textContent?.trim() }));
    if (focused.tag !== "BUTTON" || !focused.name) throw new Error(`keyboard focus did not reach a named action at ${width}px: ${JSON.stringify(focused)}`);
    await page.screenshot({ path: path.join(outputDir, `viewport-${width}.png`), fullPage: true });
    await page.close();
  }
  await browser.close();
  console.log(`T23 visual audit passed: ${VIEWPORTS.join(", ")}`);
  console.log(`Evidence: ${outputDir}`);
}


run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

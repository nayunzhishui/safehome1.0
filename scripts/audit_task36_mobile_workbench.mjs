import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const requireFromWeb = createRequire(path.join(ROOT, "apps", "web", "package.json"));
const { chromium } = requireFromWeb("playwright");
const VIEWPORTS = [360, 375, 430, 768];


function rpxToPx(source) {
  return source.replace(/(-?\d+(?:\.\d+)?)rpx/g, (_, raw) => `${Number(raw) / 2}px`);
}


async function previewHtml() {
  const appCss = await fs.readFile(path.join(ROOT, "apps/miniprogram/app.wxss"), "utf8");
  const pageCss = await fs.readFile(path.join(ROOT, "apps/miniprogram/pages/researcher-dashboard/index.wxss"), "utf8");
  const css = rpxToPx(`${appCss}\n${pageCss}`.replace("page {", ":root {"));
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>T36移动工作台视觉验收</title><style>${css}
  *{box-sizing:border-box}body{margin:0;background:var(--safe-bg);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}.safe-page{width:100%;padding:18px 16px 42px}.large-text{font-size:125%}.large-text .dashboard-copy,.large-text .state-copy,.large-text .participant-meta{font-size:18px}.workspace-tabs{display:flex;overflow-x:auto}.workspace-tab{flex:none}.safe-card{padding:18px;background:#fff;border:1px solid var(--safe-border)}button{font:inherit}</style></head>
  <body><main class="safe-page researcher-dashboard-page">
    <section class="workbench-hero"><div><span class="dashboard-kicker">研究者移动工作台</span><span class="dashboard-title">先处理重要的一小步</span><span class="dashboard-copy">移动端用于查看摘要、处理提醒和进入试点；完整研究配置与批量工作仍在 Web 完成。</span></div><button class="sync-chip" aria-label="刷新当前工作区"><span class="sync-label">最近同步</span><span class="sync-time">21:30</span></button></section>
    <section class="state-banner state-banner--partial"><span class="state-title">部分摘要暂未同步</span><span class="state-copy">其余工作区仍可使用，可重试未完成同步。</span><button class="inline-retry">重新同步</button></section>
    <nav class="workspace-tabs" aria-label="研究者工作区导航">${["待处理","参与者","反馈与消息","试点项目","我的工作"].map((label,index)=>`<button class="workspace-tab ${index===0?"active":""}">${label}</button>`).join("")}</nav>
    <section class="summary-grid"><div class="summary-card summary-card--primary"><span class="summary-value">12</span><span class="summary-label">待处理摘要</span></div><div class="summary-card summary-card--urgent"><span class="summary-value">2</span><span class="summary-label">优先处理</span></div><div class="summary-card"><span class="summary-value">1</span><span class="summary-label">消息待恢复</span></div></section>
    <section class="safe-card workspace-card"><div class="section-heading"><div><span class="section-eyebrow">授权范围内</span><span class="section-title">查找参与者</span></div><button class="icon-refresh">刷新</button></div><div class="search-box"><span class="search-icon">⌕</span><input aria-label="搜索参与者" placeholder="输入昵称或用户 ID"></div></section>
    <section class="participant-list"><article class="safe-card participant-card"><div class="participant-avatar">长</div><div class="participant-main"><span class="participant-name">一位昵称非常非常长但不能造成页面横向溢出的参与者以及需要继续验证超长名称省略策略</span><span class="participant-meta">128 条活动摘要 · 3 个关系试点</span></div><span class="participant-count">9 未读</span></article></section>
    <section class="safe-card error-card"><span class="error-title">试点项目暂时没有读取成功</span><span class="error-copy">已有列表会保留，可以重新加载。</span><span class="diagnostic-copy">请求编号：request-example</span><div class="error-actions"><button class="safe-primary-button">重新加载</button><button class="safe-outline-button">复制诊断信息</button></div></section>
  </main></body></html>`;
}


async function verifyPage(page, width, mode) {
  const dimensions = await page.evaluate(() => ({ clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth }));
  if (dimensions.scrollWidth > dimensions.clientWidth + 1) throw new Error(`horizontal overflow at ${width}px/${mode}: ${JSON.stringify(dimensions)}`);
  const buttons = page.locator("button");
  const buttonCount = await buttons.count();
  for (let index = 0; index < buttonCount; index += 1) {
    const button = buttons.nth(index);
    const box = await button.boundingBox();
    const name = ((await button.getAttribute("aria-label")) || (await button.innerText())).trim();
    if (!name) throw new Error(`unnamed button ${index} at ${width}px/${mode}`);
    if (!box || box.height < 44) throw new Error(`touch target below 44px: ${name} at ${width}px/${mode}`);
  }
  const longName = page.locator(".participant-name");
  const overflow = await longName.evaluate((element) => ({ clientWidth: element.clientWidth, scrollWidth: element.scrollWidth, textOverflow: getComputedStyle(element).textOverflow }));
  if (overflow.textOverflow !== "ellipsis" || overflow.clientWidth >= overflow.scrollWidth) throw new Error(`long nickname fixture did not exercise ellipsis at ${width}px/${mode}`);
}


async function run() {
  const outputArg = process.argv.find((item) => item.startsWith("--output-dir="));
  const outputDir = path.resolve(outputArg ? outputArg.slice("--output-dir=".length) : path.join(ROOT, ".codex_tmp", "task36-f04-visual-audit"));
  await fs.mkdir(outputDir, { recursive: true });
  const htmlPath = path.join(outputDir, "preview.html");
  await fs.writeFile(htmlPath, await previewHtml(), "utf8");
  for (const width of VIEWPORTS) {
    const browser = await chromium.launch({ headless: true, channel: "msedge" });
    try {
      const page = await browser.newPage({ viewport: { width, height: 960 } });
      page.setDefaultTimeout(10_000);
      for (const mode of ["normal", "large-text"]) {
        console.log(`Checking ${width}px/${mode}`);
        await page.goto(pathToFileURL(htmlPath).href);
        if (mode === "large-text") await page.locator("body").evaluate((body) => body.classList.add("large-text"));
        await verifyPage(page, width, mode);
        await page.screenshot({ path: path.join(outputDir, `viewport-${width}-${mode}.png`), fullPage: true });
      }
      await page.close();
    } finally {
      await browser.close();
    }
  }
  console.log(`T36 F04 visual audit passed: ${VIEWPORTS.join(", ")} px; normal + large-text`);
  console.log(`Evidence: ${outputDir}`);
}


run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

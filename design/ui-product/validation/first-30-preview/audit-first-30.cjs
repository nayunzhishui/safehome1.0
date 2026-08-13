const fs = require("node:fs");
const path = require("node:path");
const automator = require(path.resolve(__dirname, "../../../../apps/web/node_modules/miniprogram-automator"));

const routes = [
  "pages/home/index", "pages/login/index", "pages/register/index", "pages/messages/index",
  "pages/support-assistant/index", "pages/message-detail/index", "pages/emergency-guide/index",
  "pages/emergency-resources/index", "pages/getting-started/index", "pages/thermometer/index",
  "pages/training/index", "pages/training-history/index", "pages/personalized-plan/index",
  "pages/program-list/index", "pages/program-detail/index", "pages/relationship-pilot/index",
  "pages/relationship-report/index", "pages/relationship-task/index", "pages/relationship-growth/index",
  "pages/therapeutic-assessment/index", "pages/therapeutic-assessment-boundary/index",
  "pages/therapeutic-assessment-issue/index", "pages/therapeutic-assessment-recent-event/index",
  "pages/therapeutic-assessment-resources/index", "pages/therapeutic-assessment-sharing/index",
  "pages/therapeutic-assessment-summary/index", "pages/therapeutic-assessment-feedback-check/index",
  "pages/therapeutic-assessment-action-review/index", "pages/therapeutic-assessment-action-followup/index",
  "pages/therapeutic-assessment-quality/index",
];

async function main() {
  const endpoint = process.env.WECHAT_DEVTOOLS_ENDPOINT || "ws://127.0.0.1:9420";
  const outDir = path.resolve(__dirname, "screenshots");
  fs.mkdirSync(outDir, { recursive: true });
  const mini = process.env.AUTOMATOR_LAUNCH === "1"
    ? await automator.launch({
        cliPath: path.resolve(__dirname, "wechat-cli.bat"),
        projectPath: path.resolve(__dirname, "../../../../apps/miniprogram"),
        trustProject: true,
        timeout: 60000,
      })
    : await automator.connect({ wsEndpoint: endpoint });
  const consoleErrors = [];
  const exceptions = [];
  mini.on("console", (event) => {
    const level = String(event.level || event.type || "").toLowerCase();
    if (level === "error") consoleErrors.push(event);
  });
  mini.on("exception", (event) => exceptions.push(event));
  const results = [];
  try {
    const start = Math.max(0, Number(process.env.AUDIT_START || 1) - 1);
    const end = Math.min(routes.length, Number(process.env.AUDIT_END || routes.length));
    for (let index = start; index < end; index += 1) {
      const route = routes[index];
      process.stdout.write(`START ${index + 1} ${route}\n`);
      const beforeConsole = consoleErrors.length;
      const beforeExceptions = exceptions.length;
      const page = await mini.reLaunch(`/${route}`);
      await page.waitFor(650);
      const routeOk = page.path === route || page.path === "pages/login/index";
      const root = await page.$(".safe-page, .taf-page, .page-shell");
      const heading = await page.$(".home-title, .auth-title, .page-title, .intro-title, .hero-title, .program-title, .pilot-title, .report-title, .task-heading, .growth-title, .ta-title, .safe-h1, .quality-title");
      const screenshot = path.join(outDir, `${String(index + 1).padStart(2, "0")}-${route.split("/")[1]}.png`);
      const shouldCapture = process.env.SKIP_SCREENSHOT !== "1" && (!fs.existsSync(screenshot) || process.env.FORCE_SCREENSHOT === "1");
      if (shouldCapture) await mini.screenshot({ path: screenshot });
      results.push({
        index: index + 1,
        requested: route,
        actual: page.path,
        routeOk,
        rootFound: !!root,
        headingFound: !!heading,
        consoleErrors: consoleErrors.length - beforeConsole,
        exceptions: exceptions.length - beforeExceptions,
        screenshot,
      });
      fs.writeFileSync(path.resolve(__dirname, `audit-first-30-${start + 1}-${end}.json`), JSON.stringify({ endpoint, checked: results.length, results, consoleErrors, exceptions }, null, 2));
      process.stdout.write(`DONE ${index + 1} ${page.path}\n`);
    }
  } finally {
    if (process.env.AUTOMATOR_LAUNCH === "1") await mini.close();
    else mini.disconnect();
  }
  const report = { endpoint, checked: results.length, results, consoleErrors, exceptions };
  fs.writeFileSync(path.resolve(__dirname, "audit-first-30.json"), JSON.stringify(report, null, 2));
  const failures = results.filter((item) => !item.routeOk || !item.rootFound || item.consoleErrors || item.exceptions);
  process.stdout.write(JSON.stringify({ checked: results.length, failures, exceptionCount: exceptions.length, consoleErrorCount: consoleErrors.length }, null, 2));
  if (failures.length || exceptions.length || consoleErrors.length) process.exitCode = 1;
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});

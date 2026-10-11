#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const automator = require("miniprogram-automator");

const ROOT = path.resolve(__dirname, "../..");
const PROJECT_PATH = path.join(ROOT, "apps", "miniprogram");
const APP_JSON = JSON.parse(fs.readFileSync(path.join(PROJECT_PATH, "app.json"), "utf8"));
const SCENARIOS = JSON.parse(fs.readFileSync(path.join(__dirname, "scenarios.json"), "utf8"));
const MODE = process.argv[2] || "all";
const CLI_PATH = process.env.WECHAT_DEVTOOLS_CLI || "";
const LOCAL_BASE_URL = process.env.SAFEHOME_ACCEPTANCE_BASE_URL || "http://127.0.0.1:5000";
const ALLOW_EXTERNAL = process.env.SAFEHOME_ACCEPTANCE_ALLOW_EXTERNAL_READS === "1";
const ALLOW_TEST_WRITES = process.env.SAFEHOME_ACCEPTANCE_ALLOW_TEST_WRITES === "1";
const RUN_ID = new Date().toISOString().replace(/[:.]/g, "-");
const OUTPUT_DIR = path.resolve(
  process.env.SAFEHOME_ACCEPTANCE_OUTPUT || path.join(ROOT, "artifacts", "miniprogram-acceptance", RUN_ID),
);
const SCREENSHOT_DIR = path.join(OUTPUT_DIR, "screenshots");

const SECRET_KEY_PATTERN = /(token|password|secret|code|openid|unionid|phone|mobile|contact|authorization|cookie)/i;

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function redact(value, key = "") {
  if (SECRET_KEY_PATTERN.test(String(key))) return "[REDACTED]";
  if (Array.isArray(value)) return value.map((item) => redact(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, redact(v, k)]));
  }
  if (typeof value === "string" && /Bearer\s+[A-Za-z0-9._-]+/i.test(value)) return "[REDACTED]";
  return value;
}

function isLoopback(urlValue) {
  try {
    const parsed = new URL(urlValue);
    return ["127.0.0.1", "localhost", "::1"].includes(parsed.hostname);
  } catch (error) {
    return false;
  }
}

function scenario(id) {
  return SCENARIOS.automated_scenarios.find((item) => item.id === id);
}

async function safeReset(miniProgram) {
  if (!isLoopback(LOCAL_BASE_URL) && !ALLOW_EXTERNAL) {
    throw new Error(
      `Refusing non-loopback acceptance base URL (${LOCAL_BASE_URL}). ` +
      "Set SAFEHOME_ACCEPTANCE_ALLOW_EXTERNAL_READS=1 only for an approved test environment.",
    );
  }

  await miniProgram.callWxMethod("clearStorageSync");
  await miniProgram.callWxMethod("setStorageSync", "safehome_cloud_config", {
    cloudEnvId: "acceptance-local",
    containerService: "acceptance-local",
    httpBaseUrl: LOCAL_BASE_URL,
    localHttpBaseUrl: LOCAL_BASE_URL,
    useLocalHttp: true,
  });
}

async function capture(miniProgram, page, name) {
  const safeName = name.replace(/[^A-Za-z0-9._-]+/g, "-");
  const screenshotPath = path.join(SCREENSHOT_DIR, `${safeName}.png`);
  let data = null;
  try {
    data = redact(await page.data());
  } catch (error) {
    data = { capture_error: error.message };
  }
  await miniProgram.screenshot({ path: screenshotPath });
  return { screenshot: path.relative(ROOT, screenshotPath), data };
}

async function routeSweep(miniProgram, pages = APP_JSON.pages) {
  const results = [];
  for (const pagePath of pages) {
    const startedAt = Date.now();
    try {
      const page = await miniProgram.reLaunch(`/${pagePath}`);
      await page.waitFor(650);
      const evidence = await capture(miniProgram, page, pagePath);
      results.push({
        id: `route:${pagePath}`,
        page: pagePath,
        status: "passed",
        duration_ms: Date.now() - startedAt,
        ...evidence,
      });
    } catch (error) {
      results.push({
        id: `route:${pagePath}`,
        page: pagePath,
        status: "failed",
        duration_ms: Date.now() - startedAt,
        error: redact(error && (error.stack || error.message || String(error))),
      });
    }
  }
  return results;
}

async function authSurface(miniProgram) {
  const spec = scenario("AC-AUTH-01");
  const startedAt = Date.now();
  const page = await miniProgram.reLaunch(`/${spec.page}`);
  await page.waitFor(650);

  const checks = [];
  for (const selector of spec.required_selectors || []) {
    const element = await page.$(selector);
    checks.push({ selector, passed: Boolean(element) });
  }

  let anyPassed = true;
  if (spec.required_selectors_any && spec.required_selectors_any.length) {
    const states = [];
    for (const selector of spec.required_selectors_any) {
      const element = await page.$(selector);
      states.push({ selector, present: Boolean(element) });
    }
    anyPassed = states.some((item) => item.present);
    checks.push({ any_of: states, passed: anyPassed });
  }

  const evidence = await capture(miniProgram, page, "auth-surface");
  return [{
    id: spec.id,
    page: spec.page,
    status: checks.every((item) => item.passed) && anyPassed ? "passed" : "failed",
    duration_ms: Date.now() - startedAt,
    checks,
    ...evidence,
  }];
}

async function integrationSmoke(miniProgram) {
  const spec = scenario("AC-INTEGRATION-01");
  if (!ALLOW_TEST_WRITES) {
    return [{
      id: spec.id,
      page: spec.page,
      status: "skipped",
      reason: "SAFEHOME_ACCEPTANCE_ALLOW_TEST_WRITES=1 is required; test writes remain disabled by default.",
    }];
  }

  const startedAt = Date.now();
  const page = await miniProgram.reLaunch(`/${spec.page}`);
  await page.waitFor(500);
  const trigger = await page.$(spec.trigger_selector);
  if (!trigger) {
    return [{
      id: spec.id,
      page: spec.page,
      status: "failed",
      error: `Missing trigger selector: ${spec.trigger_selector}`,
    }];
  }

  await trigger.tap();
  let data = {};
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    await page.waitFor(500);
    data = await page.data();
    if (["success", "error"].includes(data.status)) break;
  }

  const evidence = await capture(miniProgram, page, "integration-smoke");
  const expectedStatus = spec.expected_data && spec.expected_data.status;
  return [{
    id: spec.id,
    page: spec.page,
    status: data.status === expectedStatus ? "passed" : "failed",
    duration_ms: Date.now() - startedAt,
    observed_status: data.status || "unknown",
    observed_message: redact(data.message || ""),
    ...evidence,
  }];
}

function writeSummary(report) {
  const counts = report.results.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {});
  const lines = [
    "# SafeHome 小程序准真机验收结果",
    "",
    `- run_id: ${report.run_id}`,
    `- mode: ${report.mode}`,
    `- transport: local-http (${report.base_url})`,
    `- passed: ${counts.passed || 0}`,
    `- failed: ${counts.failed || 0}`,
    `- skipped: ${counts.skipped || 0}`,
    "",
    "## 结果",
    "",
    "| ID | 页面 | 状态 | 耗时(ms) |",
    "|---|---|---|---:|",
    ...report.results.map((item) => `| ${item.id} | ${item.page || "-"} | ${item.status} | ${item.duration_ms || 0} |`),
    "",
    "## 判定边界",
    "",
    "本报告属于微信开发者工具/本地测试环境的准真机证据，不自动等同 Android/iOS 物理真机 UAT 或正式上线批准。",
  ];
  fs.writeFileSync(path.join(OUTPUT_DIR, "summary.md"), lines.join("\n"), "utf8");
}

async function main() {
  if (!CLI_PATH) {
    throw new Error(
      "WECHAT_DEVTOOLS_CLI is required. Point it to the WeChat DevTools CLI executable and enable the DevTools service port.",
    );
  }
  if (!["routes", "auth", "smoke", "all"].includes(MODE)) {
    throw new Error(`Unknown mode: ${MODE}`);
  }

  ensureDir(SCREENSHOT_DIR);
  const report = {
    schema: "safehome.miniprogram.acceptance.result.v1",
    run_id: RUN_ID,
    mode: MODE,
    base_url: LOCAL_BASE_URL,
    writes_enabled: ALLOW_TEST_WRITES,
    results: [],
  };

  let miniProgram;
  try {
    miniProgram = await automator.launch({
      cliPath: CLI_PATH,
      projectPath: PROJECT_PATH,
    });
    await safeReset(miniProgram);

    if (MODE === "routes" || MODE === "all") {
      report.results.push(...await routeSweep(miniProgram));
    }
    if (MODE === "auth" || MODE === "all") {
      report.results.push(...await authSurface(miniProgram));
    }
    if (MODE === "smoke" || MODE === "all") {
      report.results.push(...await integrationSmoke(miniProgram));
    }
  } finally {
    if (miniProgram) await miniProgram.close();
  }

  fs.writeFileSync(
    path.join(OUTPUT_DIR, "results.json"),
    JSON.stringify(redact(report), null, 2),
    "utf8",
  );
  writeSummary(report);

  const failures = report.results.filter((item) => item.status === "failed");
  console.log(JSON.stringify(redact(report), null, 2));
  process.exitCode = failures.length ? 1 : 0;
}

main().catch((error) => {
  console.error(`[SafeHome acceptance] ${error.stack || error.message || error}`);
  process.exitCode = 1;
});

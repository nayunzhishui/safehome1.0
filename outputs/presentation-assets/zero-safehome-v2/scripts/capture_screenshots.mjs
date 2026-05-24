import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "file:///C:/Users/32257/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const OUT_DIR = "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function writeMetadata(items) {
  await fs.writeFile(
    path.join(OUT_DIR, "screenshots.json"),
    `${JSON.stringify(items, null, 2)}\n`,
    "utf8",
  );
}

async function gotoStable(page, url) {
  await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(900);
}

async function shot(page, name, title, note, options = {}) {
  const file = path.join(OUT_DIR, `${name}.png`);
  await page.screenshot({ path: file, fullPage: options.fullPage ?? false });
  return { name, title, note, file };
}

async function scrollToText(page, text) {
  try {
    const loc = page.getByText(text, { exact: false }).first();
    await loc.scrollIntoViewIfNeeded({ timeout: 5000 });
    await page.waitForTimeout(600);
  } catch {
    await page.evaluate((amount) => window.scrollBy(0, amount), 520);
    await page.waitForTimeout(600);
  }
}

async function captureZeroWeb(browser, items) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    locale: "zh-CN",
  });
  const page = await context.newPage();
  const base = "http://127.0.0.1:5056";

  const pages = [
    ["zero_home", "/", "0版网页首页与导航", "一个站点内保留安心家入口、双量表测评、学生画像测评、研究说明和研究者入口。"],
    ["zero_parent_assessment", "/assessment", "双量表测评页", "自我关怀量表与不确定性不耐受量表用于基础研究测评。"],
    ["zero_parent_report", "/report/11", "双量表反馈报告", "展示非诊断性反馈、维度分数和研究反馈说明。"],
    ["zero_student_entry", "/student", "学生画像入口", "学生端从考试焦虑画像测评进入，强调非诊断和支持性反馈。"],
    ["zero_student_assessment", "/student/assessment", "学生画像测评页", "整合考试焦虑、IU、ERF、自我关怀和结构化文本问题。"],
  ];

  for (const [name, route, title, note] of pages) {
    await gotoStable(page, `${base}${route}`);
    items.push(await shot(page, name, title, note));
  }

  await gotoStable(page, `${base}/student/report/7`);
  items.push(await shot(page, "zero_student_report_top", "学生报告总览", "报告顶部呈现画像名称、置信度、关键分数和首轮建议。"));
  await scrollToText(page, "维度雷达图");
  items.push(await shot(page, "zero_student_report_visuals", "雷达图与PCA分类图", "用维度雷达图和二维分类图解释学生落在哪一类画像。"));
  await scrollToText(page, "轮次状态变化");
  items.push(await shot(page, "zero_student_report_followup", "轮次变化与文本关键词", "后续复测后显示量表分数趋势、访谈文本关键词和改善线索。"));
  await scrollToText(page, "沙盘");
  items.push(await shot(page, "zero_student_report_sandplay", "沙盘式表达任务", "学生用象征物、空间位置和一句说明表达考试压力场景。"));

  await gotoStable(page, `${base}/admin/login`);
  await page.locator("input[type='password']").fill("admin123");
  await page.locator("button, input[type='submit']").first().click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(900);
  items.push(await shot(page, "zero_admin", "研究者后台", "后台合并双量表研究和学生画像研究，支持概览和分模块导出。"));

  await context.close();
}

async function captureSafehomeWeb(browser, items) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    locale: "zh-CN",
  });
  const page = await context.newPage();
  const base = "http://127.0.0.1:5173";

  const pages = [
    ["home_landing", "/", "安心家网页首页", "展示安心家作为家长情绪管理支持系统的入口、理念和主要路径。"],
    ["home_dashboard", "/dashboard", "研究看板", "研究者从网页后台查看目标、记录、反馈、训练、周报和督导概览。"],
    ["home_goals", "/goals", "目标管理", "家长先设定亲子互动中的具体小目标，形成练习方向。"],
    ["home_diaries", "/diaries", "情绪事件记录", "记录场景、情绪、自动想法、身体感受和行为反应。"],
    ["home_feedback", "/feedback", "非诊断反馈结果", "基于规则识别互动模式，给出支持性反馈和替代回应。"],
    ["home_checkins", "/checkins", "训练打卡", "记录训练卡完成情况、情绪前后变化和练习反思。"],
    ["home_reports", "/reports", "周度报告", "汇总一周场景、情绪、模式、训练卡和下周建议。"],
    ["home_supervision", "/supervision", "人工督导请求", "在需要时提交人工督导或进一步支持请求。"],
    ["home_cards", "/content/cards", "训练卡内容库", "UP训练卡作为干预内容，可承接0版网页的任务脚本。"],
    ["home_rules", "/content/rules", "反馈规则库", "非诊断反馈规则支持模式识别和解释生成。"],
    ["home_export", "/export", "研究数据导出", "后台导出支持论文和用户研究的数据整理。"],
    ["home_integration", "/integration-test", "联调测试入口", "验证创建记录、生成反馈、推荐训练卡三步闭环。"],
  ];

  for (const [name, route, title, note] of pages) {
    await gotoStable(page, `${base}${route}`);
    items.push(await shot(page, name, title, note));
  }
  await context.close();
}

function miniHtml(page) {
  const chips = page.chips.map((item) => `<span>${item}</span>`).join("");
  const cards = page.cards.map((item) => `
    <section class="card">
      <b>${item.title}</b>
      <p>${item.body}</p>
    </section>
  `).join("");
  return `<!doctype html>
  <html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <style>
      body { margin: 0; background: #dfe8e2; font-family: "Microsoft YaHei", Arial, sans-serif; }
      .phone { width: 390px; min-height: 844px; margin: 0 auto; background: #f7faf7; color: #1d2b22; overflow: hidden; }
      .nav { background: #2f7d45; color: white; padding: 18px 22px 16px; font-size: 20px; font-weight: 700; }
      .hero { padding: 22px; background: linear-gradient(135deg, #eaf6ee, #ffffff); }
      .eyebrow { color: #4caf7d; font-size: 13px; font-weight: 700; margin-bottom: 8px; }
      h1 { margin: 0; font-size: 26px; line-height: 1.18; }
      .subtitle { margin: 10px 0 0; color: #6b756d; font-size: 14px; line-height: 1.5; }
      .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
      .chips span { background: #ffffff; border: 1px solid #dce7df; border-radius: 999px; padding: 7px 10px; font-size: 12px; color: #31563b; }
      .content { padding: 16px; }
      .card { background: #fff; border: 1px solid #e3ebe5; border-radius: 14px; padding: 15px; margin-bottom: 12px; box-shadow: 0 8px 18px rgba(48, 80, 58, 0.06); }
      .card b { display: block; font-size: 16px; margin-bottom: 7px; }
      .card p { margin: 0; color: #68746a; font-size: 13px; line-height: 1.5; }
      .tabbar { position: fixed; left: calc(50% - 195px); bottom: 0; width: 390px; height: 62px; background: #fff; border-top: 1px solid #e3ebe5; display: grid; grid-template-columns: repeat(4, 1fr); color: #7c897f; font-size: 12px; text-align: center; align-items: center; }
      .tabbar b { color: #4caf7d; font-weight: 700; }
    </style>
  </head>
  <body>
    <div class="phone">
      <div class="nav">安心陪伴</div>
      <div class="hero">
        <div class="eyebrow">${page.eyebrow}</div>
        <h1>${page.title}</h1>
        <p class="subtitle">${page.subtitle}</p>
        <div class="chips">${chips}</div>
      </div>
      <div class="content">${cards}</div>
      <div class="tabbar"><b>首页</b><span>训练</span><span>课程</span><span>我的</span></div>
    </div>
  </body>
  </html>`;
}

async function captureMiniProgram(browser, items) {
  const context = await browser.newContext({
    viewport: { width: 430, height: 900 },
    deviceScaleFactor: 1,
    locale: "zh-CN",
  });
  const page = await context.newPage();
  const pages = [
    {
      name: "mini_home",
      title: "小程序首页",
      eyebrow: "家长支持入口",
      subtitle: "从目标、记录、训练和周报进入家长端陪伴闭环。",
      chips: ["目标", "记录", "反馈", "训练"],
      cards: [
        { title: "今天先做一件小事", body: "用一句观察句替代催促，降低亲子互动中的即时冲突。" },
        { title: "继续上次目标", body: "围绕作业拖延、考试压力或沟通冲突进行小步练习。" },
      ],
      note: "小程序首页承接家长端低负担入口。",
    },
    {
      name: "mini_training",
      title: "训练页",
      eyebrow: "UP训练卡",
      subtitle: "把情绪觉察、暂停、替代回应转为可执行练习。",
      chips: ["情绪命名", "三秒暂停", "替代回应"],
      cards: [
        { title: "三秒暂停", body: "先停下、命名情绪，再用非评判句回应孩子。" },
        { title: "共同解决", body: "从对抗转向一起找下一步可以完成的小目标。" },
      ],
      note: "训练页对应安心家的内容干预模块。",
    },
    {
      name: "mini_assessment",
      title: "测一测",
      eyebrow: "评估工作表",
      subtitle: "家长可完成简短工作表，结果用于自我观察和练习记录。",
      chips: ["非诊断", "自我观察", "练习建议"],
      cards: [
        { title: "情绪觉察工作表", body: "帮助家长识别触发场景、自动想法和身体反应。" },
        { title: "亲子互动反思", body: "记录一次冲突中的双方情绪和可替代回应。" },
      ],
      note: "测评页是0版网页评估能力未来进入安心家的接口。",
    },
    {
      name: "mini_assessment_detail",
      title: "测评详情",
      eyebrow: "逐题填写",
      subtitle: "题目以简短语言呈现，降低家长填写负担。",
      chips: ["选择题", "简答", "自动保存"],
      cards: [
        { title: "题目示例", body: "当孩子没有按计划行动时，我能先觉察自己的情绪。" },
        { title: "结果说明", body: "得分只用于支持性反馈，不构成诊断。" },
      ],
      note: "测评详情页体现轻量、非诊断的测评交互。",
    },
    {
      name: "mini_diary",
      title: "情绪记录",
      eyebrow: "事件记录",
      subtitle: "记录真实亲子互动中的场景、情绪、想法和行为。",
      chips: ["场景", "情绪强度", "自动想法"],
      cards: [
        { title: "作业拖延", body: "孩子迟迟不开始作业，家长感到着急并反复催促。" },
        { title: "身体信号", body: "胸口发紧、声音变快，是进入自动反应前的重要线索。" },
      ],
      note: "情绪记录页是安心家数据闭环的起点。",
    },
    {
      name: "mini_feedback",
      title: "反馈结果",
      eyebrow: "非诊断反馈",
      subtitle: "系统识别互动模式，提供支持性解释和替代回应。",
      chips: ["触发点", "互动模式", "替代句"],
      cards: [
        { title: "模式提示", body: "可能从担心孩子落后，快速进入催促和控制。" },
        { title: "替代回应", body: "我看到你现在很烦，我们先把第一步写下来。" },
      ],
      note: "反馈结果页体现安心家的支持性表达风格。",
    },
    {
      name: "mini_checkin",
      title: "练习打卡",
      eyebrow: "任务复盘",
      subtitle: "记录训练卡是否完成，以及情绪前后变化。",
      chips: ["完成", "情绪前后", "反思"],
      cards: [
        { title: "今日完成", body: "使用三秒暂停后，家长情绪强度从8降到5。" },
        { title: "下次调整", body: "先观察孩子状态，再提出一个具体小步骤。" },
      ],
      note: "打卡页把内容干预转化为可追踪数据。",
    },
    {
      name: "mini_weekly_report",
      title: "周度报告",
      eyebrow: "一周回顾",
      subtitle: "汇总常见场景、情绪模式、训练完成和下周建议。",
      chips: ["高频场景", "训练卡", "建议"],
      cards: [
        { title: "本周常见场景", body: "作业拖延、考试复习和睡前沟通是主要触发点。" },
        { title: "下周建议", body: "继续练习观察句，减少直接评价和催促。" },
      ],
      note: "周报页对应安心家的阶段性反馈能力。",
    },
    {
      name: "mini_supervision",
      title: "人工督导",
      eyebrow: "支持升级",
      subtitle: "当家长需要进一步建议时，可以提交人工督导请求。",
      chips: ["人工建议", "风险提示", "转介"],
      cards: [
        { title: "提交问题", body: "想请老师看看这次回应还可以怎么调整。" },
        { title: "边界提示", body: "高风险情况建议联系专业人员或可信支持系统。" },
      ],
      note: "督导页提供从自动反馈到人工支持的通道。",
    },
    {
      name: "mini_profile",
      title: "我的",
      eyebrow: "个人中心",
      subtitle: "查看目标、训练记录、测评结果和隐私说明。",
      chips: ["记录", "隐私", "设置"],
      cards: [
        { title: "我的练习", body: "查看近期目标、已完成训练卡和周度报告。" },
        { title: "隐私与同意", body: "说明数据用途、研究授权和退出方式。" },
      ],
      note: "个人中心承接隐私、记录和持续使用。",
    },
  ];

  for (const p of pages) {
    await page.setContent(miniHtml(p), { waitUntil: "load" });
    await page.waitForTimeout(300);
    const file = path.join(OUT_DIR, `${p.name}.png`);
    await page.screenshot({ path: file, fullPage: false });
    items.push({ name: p.name, title: p.title, note: p.note, file });
  }
  await context.close();
}

async function captureStatic(browser, items) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "zh-CN" });
  const page = await context.newPage();
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    body{margin:0;background:#f4f7fb;font-family:"Microsoft YaHei",Arial;color:#102033}
    .wrap{padding:54px 72px}
    h1{font-size:42px;margin:0 0 10px}
    p{color:#5b677a;font-size:20px;margin:0 0 30px}
    .grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px}
    .card{background:white;border:1px solid #d9e2ef;border-radius:16px;padding:24px;min-height:170px}
    b{display:block;color:#168a86;font-size:22px;margin-bottom:14px}
    code{display:block;background:#f7fafc;border:1px solid #e1e8f0;border-radius:10px;padding:10px;margin:8px 0;font-size:15px}
  </style></head><body><div class="wrap">
    <h1>0版网页数据与模型文件</h1>
    <p>当前原型把机器学习模型、画像解释、沙盘任务和统一数据库保存在项目内，便于复现与继续开发。</p>
    <div class="grid">
      <div class="card"><b>机器学习模型</b><code>content/ml_model.json</code><code>ml_outputs/student_profile_assignments.csv</code><code>ml_outputs/student_profile_dashboard.html</code></div>
      <div class="card"><b>画像与干预规则</b><code>content/profile_rules.json</code><code>content/sandplay_tasks.json</code><code>docs/profile_convergence_plan.md</code></div>
      <div class="card"><b>统一数据与代码</b><code>unified_assessment.sqlite3</code><code>app.py</code><code>templates/student_report.html</code><code>static/profile_visuals.js</code></div>
    </div>
  </div></body></html>`;
  await page.setContent(html, { waitUntil: "load" });
  const file = path.join(OUT_DIR, "zero_files_model.png");
  await page.screenshot({ path: file, fullPage: false });
  items.push({ name: "zero_files_model", title: "0版网页数据与模型文件", note: "说明模型、规则、沙盘任务和统一数据库的保存位置。", file });
  await context.close();
}

async function main() {
  await ensureDir(OUT_DIR);
  const browser = await chromium.launch({
    executablePath: EDGE,
    headless: true,
  });
  const items = [];
  await captureZeroWeb(browser, items);
  await captureSafehomeWeb(browser, items);
  await captureMiniProgram(browser, items);
  await captureStatic(browser, items);
  await browser.close();
  await writeMetadata(items);
  console.log(JSON.stringify({ count: items.length, outDir: OUT_DIR }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});

import fs from "node:fs/promises";
import path from "node:path";

const SLIDES_DIR = "D:/codex/workspace/safehome1.0/outputs/presentations/safehome-readfeedback-report/slides";
const IMG = "D:/codex/workspace/safehome1.0/outputs/presentation-assets/zero-safehome-v2/screenshots";

function p(name) {
  return `${IMG}/${name}.png`;
}

function esc(value) {
  return JSON.stringify(value);
}

const imports = `import { C, arrow, bullets, callout, footer, header, image, line, metric, rect, sectionPill, setBackground, tag, text } from "./shared.mjs";\n\n`;

function moduleSource(index, body) {
  return `${imports}export default async function slide${String(index).padStart(2, "0")}(presentation) {\n  const slide = presentation.slides.add();\n  setBackground(slide);\n${body}\n  footer(slide);\n  return slide;\n}\n`;
}

function titleSlide({ kicker, title, subtitle, chips }) {
  return `  rect(slide, 0, 0, 1280, 720, { fill: "#F5F8FC", line: false, radius: "rounded-sm" });
  rect(slide, 820, 0, 460, 720, { fill: "#E8F3F2", line: false, radius: "rounded-sm" });
  rect(slide, 866, 100, 300, 320, { fill: "#FFFFFF", lineFill: "#D3E5E3", radius: "rounded-lg" });
  text(slide, "评估", 926, 150, 180, 44, { size: 34, bold: true, color: C.blue, align: "center" });
  line(slide, 960, 210, 112, 5, C.teal);
  text(slide, "画像\\n反馈\\n追踪\\n合并", 927, 250, 180, 130, { size: 24, bold: true, color: C.ink, align: "center", lineSpacing: 1.35 });
  tag(slide, ${esc(kicker)}, 86, 74, 150, C.teal);
  text(slide, ${esc(title)}, 84, 142, 680, 128, { size: 42, bold: true, color: C.ink, lineSpacing: 1.15 });
  text(slide, ${esc(subtitle)}, 88, 330, 710, 90, { size: 21, color: C.muted, lineSpacing: 1.3 });
  ${chips.map((c, i) => `metric(slide, ${88 + i * 214}, 498, 190, ${esc(c[0])}, ${esc(c[1])}, ${c[2]});`).join("\n  ")}`;
}

function imageSlide({ section, title, subtitle, img, bullets: items, caption, page }) {
  return `  header(slide, ${esc(section)}, ${esc(title)}, ${esc(subtitle)}, ${esc(page)});
  rect(slide, 72, 210, 360, 430, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  bullets(slide, ${esc(items)}, 100, 240, 305, 210, { size: 19, lineSpacing: 1.34 });
  callout(slide, ${esc(caption)}, 92, 466, 320, 136, C.teal);
  image(slide, ${esc(img)}, 486, 216, 660, 372, { alt: ${esc(title)} });`;
}

function twoImageSlide({ section, title, subtitle, leftImg, rightImg, leftTitle, rightTitle, note, page }) {
  return `  header(slide, ${esc(section)}, ${esc(title)}, ${esc(subtitle)}, ${esc(page)});
  image(slide, ${esc(leftImg)}, 80, 220, 520, 320, { alt: ${esc(leftTitle)} });
  image(slide, ${esc(rightImg)}, 680, 220, 520, 320, { alt: ${esc(rightTitle)} });
  tag(slide, ${esc(leftTitle)}, 104, 560, 210, C.blue);
  tag(slide, ${esc(rightTitle)}, 704, 560, 210, C.teal);
  text(slide, ${esc(note)}, 160, 612, 960, 42, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2, align: "center" });`;
}

function flowSlide({ section, title, subtitle, steps, note, page }) {
  const stepCode = steps.map((s, i) => {
    const x = 82 + i * 228;
    return `rect(slide, ${x}, 250, 172, 142, { fill: "#FFFFFF", lineFill: "#D9E2EF" });
  tag(slide, ${esc(s[0])}, ${x + 20}, 274, 90, ${s[2]});
  text(slide, ${esc(s[1])}, ${x + 20}, 318, 126, 54, { size: 20, bold: true, color: C.ink, align: "center", lineSpacing: 1.12 });
  ${i < steps.length - 1 ? `arrow(slide, ${x + 176}, 306, 42);` : ""}`;
  }).join("\n  ");
  return `  header(slide, ${esc(section)}, ${esc(title)}, ${esc(subtitle)}, ${esc(page)});
  ${stepCode}
  rect(slide, 128, 470, 1024, 94, { fill: "#FFFFFF", lineFill: "#D9E2EF", label: ${esc(note)}, size: 22, bold: true, color: C.blue, align: "center", pad: 18 });`;
}

function miniGridSlide({ section, title, subtitle, images, labels, note, page }) {
  if (images.length > 3) {
    return `  header(slide, ${esc(section)}, ${esc(title)}, ${esc(subtitle)}, ${esc(page)});
  ${images.map((img, i) => {
    const x = 70 + i * 236;
    return `image(slide, ${esc(img)}, ${x}, 214, 148, 300, { alt: ${esc(labels[i])} });
  tag(slide, ${esc(labels[i])}, ${x}, 536, 138, ${i % 2 ? "C.teal" : "C.blue"});`;
  }).join("\n  ")}
  text(slide, ${esc(note)}, 110, 604, 820, 44, { size: 20, bold: true, color: C.ink, lineSpacing: 1.2 });
  callout(slide, "小程序截图为基于现有 WXML/WXSS 内容生成的移动端预览，用于汇报页面逻辑。", 955, 560, 240, 110, C.amber);`;
  }
  return `  header(slide, ${esc(section)}, ${esc(title)}, ${esc(subtitle)}, ${esc(page)});
  ${images.map((img, i) => {
    const x = 82 + i * 220;
    return `image(slide, ${esc(img)}, ${x}, 220, 168, 338, { alt: ${esc(labels[i])} });
  tag(slide, ${esc(labels[i])}, ${x}, 580, 150, ${i % 2 ? "C.teal" : "C.blue"});`;
  }).join("\n  ")}
  text(slide, ${esc(note)}, 780, 272, 340, 170, { size: 24, bold: true, color: C.ink, lineSpacing: 1.35 });
  callout(slide, "小程序截图为基于现有 WXML/WXSS 内容生成的移动端预览，用于汇报页面逻辑。", 760, 490, 400, 80, C.amber);`;
}

const slides = [
  titleSlide({
    kicker: "导师阶段汇报",
    title: "0版网页与安心家合并工作汇报",
    subtitle: "先完整汇报0版网页的设计、理念、功能和截图，再说明与安心家的合并方式，最后汇报安心家项目的整体工作思路。",
    chips: [["46页", "详细汇报", "C.teal"], ["0版网页", "功能截图", "C.blue"], ["安心家", "工作思路", "C.amber"]],
  }),
  flowSlide({
    section: "01 | 汇报主线",
    title: "本次汇报先讲0版网页，再讲安心家",
    subtitle: "把0版网页作为已经可演示的研究原型，把安心家作为后续长期平台。",
    page: "02",
    steps: [["第一部分", "0版网页", "C.teal"], ["第二部分", "合并方案", "C.blue"], ["第三部分", "安心家理念", "C.green"], ["第四部分", "页面设计", "C.amber"], ["第五部分", "下一阶段", "C.lavender"]],
    note: "汇报重点从“做了什么页面”转向“这些页面如何形成评估、反馈、追踪、研究导出的工作流”。",
  }),
  flowSlide({
    section: "02 | 总体结论",
    title: "0版网页是评估反馈原型，安心家是长期陪伴平台",
    subtitle: "两者不是两个互相竞争的网站，而是同一项目的两个层级。",
    page: "03",
    steps: [["0版网页", "测评画像", "C.teal"], ["报告页", "解释反馈", "C.blue"], ["轮次任务", "追踪变化", "C.green"], ["研究后台", "导出分析", "C.amber"], ["安心家", "长期陪伴", "C.lavender"]],
    note: "建议定位：0版网页沉淀为安心家的“治疗性评估与反馈报告模块”。",
  }),
  imageSlide({ section: "03 | 0版网页定位", title: "0版网页是治疗性评估与反馈报告原型", subtitle: "不是普通问卷网页，而是把测评结果转化为解释、任务和追踪。", page: "04", img: p("zero_home"), bullets: ["面向学生、家长/研究参与者、研究者和咨询/督导者", "保留安心家视觉入口，同时加入学生画像模块", "输出非诊断反馈、可视化图表和研究数据", "所有功能围绕“评估-反馈-追踪”组织"], caption: "先把可演示原型讲清楚，再谈并入安心家。" }),
  imageSlide({ section: "04 | 首页/导航", title: "首页承担统一入口：旧版研究与学生画像并存", subtitle: "一个站点内同时呈现双量表测评、学生画像测评、研究说明和后台入口。", page: "05", img: p("zero_home"), bullets: ["首页保留安心家视觉风格", "导航区连接双量表、学生测评、研究说明和后台", "用户一进入即可选择研究路径", "后续可迁入安心家统一导航"], caption: "首页是0版网页的信息入口和合并雏形。" }),
  flowSlide({ section: "05 | 0版网页工作流", title: "工作流程：测评进入，报告反馈，轮次收束", subtitle: "学生端与研究者端围绕同一条数据链路运转。", page: "06", steps: [["填写", "量表/文本", "C.blue"], ["分类", "机器学习", "C.teal"], ["报告", "可视化", "C.green"], ["任务", "小步干预", "C.amber"], ["复测", "收束画像", "C.lavender"]], note: "每一次填写都不只生成分数，还进入后续任务、复测、文本关键词和研究导出。" }),
  imageSlide({ section: "06 | 双量表测评", title: "双量表测评页：自我关怀与不确定性不耐受", subtitle: "旧版研究模块仍然保留，为家长/研究参与者提供基础测评。", page: "07", img: p("zero_parent_assessment"), bullets: ["自我关怀量表用于理解自我支持资源", "不确定性不耐受用于理解焦虑相关认知倾向", "页面保留知情同意和研究授权", "提交后进入非诊断反馈报告"], caption: "这是0版网页最早的测评研究基础。" }),
  imageSlide({ section: "07 | 双量表报告", title: "双量表报告页：非诊断反馈与研究说明", subtitle: "报告将量表得分转化为可理解的解释和支持性提示。", page: "08", img: p("zero_parent_report"), bullets: ["展示维度得分与解释", "强调非诊断、非医疗判断", "保留研究反馈和后续使用说明", "可作为安心家家长端测评模块来源"], caption: "报告页是从“得分”走向“反馈”的关键。" }),
  imageSlide({ section: "08 | 学生入口", title: "学生画像入口：考试焦虑支持性测评", subtitle: "学生端入口明确说明边界：用于理解状态和获得建议，不用于贴标签。", page: "09", img: p("zero_student_entry"), bullets: ["入口文案面向学生，降低测评压力", "强调考试焦虑画像和阶段性建议", "把学生端与家长端在同一站点分开", "后续可独立进入安心家的学生测评路径"], caption: "学生入口决定了系统不是单纯家长端工具。" }),
  imageSlide({ section: "09 | 学生测评", title: "学生画像测评页：多维度收集考试焦虑相关信息", subtitle: "量表和结构化文本共同支持画像分类与后续访谈。", page: "10", img: p("zero_student_assessment"), bullets: ["考试焦虑：识别考试情境中的紧张和回避", "IU：识别对不确定结果的放大反应", "ERF：识别情绪调节灵活性", "自我关怀：识别自我支持与自责倾向"], caption: "学生画像依赖多维度，而不是单一焦虑总分。" }),
  imageSlide({ section: "10 | 模型文件", title: "模型与规则文件：保证可复现和可迭代", subtitle: "0版网页把机器学习模型、画像规则和任务脚本保存为轻量文件。", page: "11", img: p("zero_files_model"), bullets: ["ml_model.json 保存聚类中心、标准化参数和PCA参数", "profile_rules.json 保存画像解释和首轮建议", "sandplay_tasks.json 保存沙盘式任务脚本", "SQLite 保存提交、轮次和沙盘记录"], caption: "轻量文件结构便于之后迁移到安心家。" }),
  imageSlide({ section: "11 | 学生报告总览", title: "学生报告顶部：先回答“我属于哪一类”", subtitle: "报告顶部呈现画像名称、置信度、关键分数和初步解释。", page: "12", img: p("zero_student_report_top"), bullets: ["显示画像名称和一句话解释", "展示画像置信度和关键维度", "给出不是诊断的边界说明", "为下方图表和任务做铺垫"], caption: "报告第一屏要让学生快速理解结果。" }),
  imageSlide({ section: "12 | 画像卡片", title: "画像卡片：把机器学习分类转成心理学语言", subtitle: "系统不只显示组别编号，而是解释画像含义和主要依据。", page: "13", img: p("zero_student_report_top"), bullets: ["画像名称避免病理化", "置信度体现模型判断的不确定性", "维度分数帮助学生理解原因", "最近两类距离可用于人工复核"], caption: "模型结果必须被翻译成可理解的反馈。" }),
  imageSlide({ section: "13 | 可视化图表", title: "雷达图与PCA分类图：解释“为什么是这一类”", subtitle: "量表维度和训练样本分布共同帮助研究者和学生理解分类。", page: "14", img: p("zero_student_report_visuals"), bullets: ["雷达图显示IU、ERF、自我关怀和考试焦虑", "PCA图展示个体点与训练样本群落", "可视化降低机器学习黑箱感", "后续可用于和导师讨论模型合理性"], caption: "这是机器学习结果进入网页的核心展示。" }),
  imageSlide({ section: "14 | 轮次变化", title: "轮次状态变化：从一次测评走向持续追踪", subtitle: "复测后显示状态分数变化，帮助判断画像是否收束。", page: "15", img: p("zero_student_report_followup"), bullets: ["保存第1/2/3轮反馈", "记录任务完成和当前状态评分", "趋势图体现小步干预后的变化", "误差不降时建议调整路径或人工复核"], caption: "轮次设计让评估成为过程，而不是一次性标签。" }),
  imageSlide({ section: "15 | 文本关键词", title: "文本关键词：从访谈/日记中观察压力词和资源词", subtitle: "结构化文本用于辅助判断改善程度，不直接决定诊断。", page: "16", img: p("zero_student_report_followup"), bullets: ["提取压力词、资源词和改善词", "用于访谈线索和研究编码", "和量表分数一起观察变化", "不把自然语言处理作为硬性判定"], caption: "文本分析服务于理解，不服务于贴标签。" }),
  imageSlide({ section: "16 | 整合治疗任务", title: "报告任务：标本同治、整合治疗取向", subtitle: "每个画像只给一个首轮任务，避免学生被报告压垮。", page: "17", img: p("zero_student_report_full"), bullets: ["CBT：自动想法和证据检验", "ACT：接纳不确定性与价值行动", "焦点解决：例外经验和资源追踪", "人本/动力学：非评判理解与关系线索"], caption: "任务设计体现心理学整合，而不是单一技术。" }),
  imageSlide({ section: "17 | 沙盘式表达", title: "沙盘式表达任务：把考试压力转成可讨论材料", subtitle: "学生用象征物、空间位置和文字反思表达内在场景。", page: "18", img: p("zero_student_report_sandplay"), bullets: ["象征物：山、门、桥、时钟、书本、眼睛、家等", "沙盘板：拖放位置和空间关系", "反思问题：学生用自己的语言解释场景", "摘要指标只作为访谈线索，不自动诊断"], caption: "这是0版网页最有研究特色的表达任务。" }),
  imageSlide({ section: "18 | 研究者后台", title: "研究者后台：双量表研究与学生画像研究合并管理", subtitle: "后台支持查看概览、研究记录和分模块导出。", page: "19", img: p("zero_admin"), bullets: ["同一个后台管理旧版和新版数据", "双量表提交、学生提交、轮次和沙盘记录分区", "导出字段便于论文和用户研究分析", "管理员登录保护后台入口"], caption: "后台是从网页原型走向研究工具的基础。" }),
  imageSlide({ section: "19 | 数据导出", title: "数据与导出：保留研究可用字段", subtitle: "研究者可以分别导出量表、画像、轮次、关键词和沙盘记录。", page: "20", img: p("zero_admin"), bullets: ["旧版：宽表、长表、计分表、数据字典", "新版：画像分数、置信度、轮次追踪", "沙盘：象征物坐标、反思文本、摘要指标", "研究授权字段控制导出范围"], caption: "导出能力决定后续论文数据整理效率。" }),
  twoImageSlide({ section: "20 | 0版网页小结", title: "0版网页已经形成“评估-反馈-追踪-导出”闭环", subtitle: "每个功能都有明确的研究和用户价值。", page: "21", leftImg: p("zero_student_report_visuals"), rightImg: p("zero_admin"), leftTitle: "学生报告", rightTitle: "研究后台", note: "前台帮助学生理解自己，后台帮助研究者整理数据。" }),
  flowSlide({ section: "21 | 合并定位", title: "合并不是拼页面，而是明确层级", subtitle: "0版网页成为安心家的评估反馈模块，安心家承接长期陪伴。", page: "22", steps: [["安心家", "主平台", "C.blue"], ["0版网页", "评估模块", "C.teal"], ["内容库", "训练任务", "C.green"], ["数据库", "统一记录", "C.amber"], ["后台", "研究导出", "C.lavender"]], note: "合并后对外可统一叫安心家，内部保留0版网页作为评估反馈引擎。" }),
  twoImageSlide({ section: "22 | 合并依据", title: "两个系统共享同一条支持性反馈逻辑", subtitle: "0版网页强在评估报告，安心家强在长期训练和陪伴。", page: "23", leftImg: p("zero_home"), rightImg: p("home_landing"), leftTitle: "0版网页", rightTitle: "安心家", note: "共同边界是非诊断、支持性、可追踪。" }),
  flowSlide({ section: "23 | 合并后的分工", title: "安心家做陪伴，0版网页做评估", subtitle: "分工清楚才能避免两个项目重复建设。", page: "24", steps: [["测评", "0版网页", "C.teal"], ["报告", "0版网页", "C.teal"], ["训练", "安心家", "C.blue"], ["打卡", "安心家", "C.blue"], ["督导", "安心家", "C.blue"]], note: "学生画像结果可以进入安心家的评估结果表，任务脚本可以沉淀为训练卡。" }),
  flowSlide({ section: "24 | 迁移路线", title: "迁移顺序：内容先行，API第二，前端最后", subtitle: "降低风险，保留原型可回退。", page: "25", steps: [["第1步", "内容迁移", "C.green"], ["第2步", "模型服务", "C.teal"], ["第3步", "数据表扩展", "C.blue"], ["第4步", "页面迁移", "C.amber"], ["第5步", "统一后台", "C.lavender"]], note: "不直接覆盖原0版网页；先把可复用内容和模型逻辑搬入安心家。" }),
  twoImageSlide({ section: "25 | 内容合并", title: "0版网页任务脚本可进入安心家训练卡体系", subtitle: "CBT、ACT、沙盘式表达任务可以变成安心家的训练内容。", page: "26", leftImg: p("zero_files_model"), rightImg: p("home_cards"), leftTitle: "任务脚本", rightTitle: "训练卡库", note: "这样既保留研究原型，又接入家长/学生的持续练习场景。" }),
  twoImageSlide({ section: "26 | 数据合并", title: "研究数据进入统一后台，但保留模块字段", subtitle: "避免强行合成一张表，减少数据含义混乱。", page: "27", leftImg: p("zero_admin"), rightImg: p("home_export"), leftTitle: "0版导出", rightTitle: "安心家导出", note: "建议按模块导出：家长端、学生画像、轮次追踪、沙盘记录。" }),
  flowSlide({ section: "27 | 合并边界", title: "合并后仍然坚持非诊断和人工复核边界", subtitle: "这是向导师汇报时需要主动说明的伦理线。", page: "28", steps: [["非诊断", "不贴病理标签", "C.red"], ["最小数据", "不存人脸音视频", "C.teal"], ["知情同意", "研究授权", "C.blue"], ["模型透明", "解释置信度", "C.amber"], ["人工复核", "高风险转介", "C.lavender"]], note: "沙盘内容只作为表达和访谈线索，不解释为潜意识诊断。" }),
  imageSlide({ section: "28 | 安心家理念", title: "安心家：面向家长的情绪管理与亲子支持系统", subtitle: "基于UP跨诊断情绪调节框架，强调记录、识别、反馈、练习、追踪、支持。", page: "29", img: p("home_landing"), bullets: ["服务对象：亲子冲突中的家长", "目标：形成更支持性的回应方式", "方法：非诊断反馈与训练卡练习", "边界：不替代咨询、诊断或医疗服务"], caption: "安心家是长期陪伴主平台。" }),
  flowSlide({ section: "29 | 安心家流程", title: "核心流程：目标设定到人工督导", subtitle: "安心家的产品逻辑是一条持续陪伴闭环。", page: "30", steps: [["目标", "设定方向", "C.green"], ["记录", "情绪事件", "C.teal"], ["反馈", "模式识别", "C.blue"], ["训练", "卡片练习", "C.amber"], ["支持", "周报督导", "C.lavender"]], note: "目标设定 → 情绪事件记录 → 模式识别 → 非诊断反馈 → 训练卡 → 打卡 → 周报 → 人工督导。" }),
  imageSlide({ section: "30 | 板块架构", title: "安心家项目板块：后端、内容库、网页端、小程序端、共享类型", subtitle: "当前项目路径为 D:\\codex\\workspace\\safehome1.0。", page: "31", img: p("home_dashboard"), bullets: ["backend：Flask + SQLite API", "content：训练卡、反馈规则、评估工作表", "apps/web：研究后台和网页端", "apps/miniprogram：家长小程序端", "shared：两端共用类型和常量"], caption: "安心家比0版网页更像长期产品工程。" }),
  imageSlide({ section: "31 | 网页首页", title: "网页首页设计：支持性、清晰、低压", subtitle: "页面视觉以绿色支持感为主，不做营销式大页面。", page: "32", img: p("home_landing"), bullets: ["突出安心陪伴和家长支持", "入口连接研究后台和功能模块", "文案强调非评判和小步练习", "适合后续承接0版网页评估入口"], caption: "首页负责解释项目定位。" }),
  imageSlide({ section: "32 | 研究看板", title: "研究看板：把分散记录汇总到后台", subtitle: "研究者可从这里了解目标、记录、反馈、训练、周报和督导。", page: "33", img: p("home_dashboard"), bullets: ["展示核心数据概览", "连接各管理页面", "适合导师快速了解项目进度", "后续可加入0版网页学生画像统计"], caption: "看板是安心家的研究者视角。" }),
  imageSlide({ section: "33 | 目标管理", title: "目标管理：先确定家长要练习的具体场景", subtitle: "安心家的干预不是泛泛建议，而是围绕一个小目标持续练习。", page: "34", img: p("home_goals"), bullets: ["目标围绕具体亲子互动场景", "SMART目标帮助降低模糊性", "和后续情绪记录、训练卡关联", "适合形成个案追踪材料"], caption: "目标管理是家长端闭环起点。" }),
  imageSlide({ section: "34 | 情绪记录", title: "情绪事件记录：捕捉触发点、自动想法和行为反应", subtitle: "数据结构服务于UP情绪调节框架。", page: "35", img: p("home_diaries"), bullets: ["记录场景和事件描述", "记录家长与孩子的情绪强度", "记录自动想法和身体感受", "记录行为与原始文本"], caption: "这是生成反馈和训练建议的原始材料。" }),
  imageSlide({ section: "35 | 非诊断反馈", title: "反馈结果：从记录中识别互动模式", subtitle: "系统输出支持性解释和替代回应，而不是评价家长。", page: "36", img: p("home_feedback"), bullets: ["识别触发点和常见模式", "输出支持性反馈", "给出替代回应句", "推荐训练卡"], caption: "安心家的语言风格必须保持非评判。" }),
  imageSlide({ section: "36 | 训练卡", title: "训练卡内容库：把建议变成可练习任务", subtitle: "训练卡是安心家承接0版网页任务脚本的最佳位置。", page: "37", img: p("home_cards"), bullets: ["情绪命名、三秒暂停、替代回应等卡片", "每张卡包含目的、步骤、示例和标签", "适合后续加入CBT/ACT/沙盘式表达任务", "内容库可版本化和研究化"], caption: "训练卡让反馈进入行动。" }),
  imageSlide({ section: "37 | 打卡记录", title: "打卡记录：把练习转成可追踪变化", subtitle: "家长完成训练卡后记录情绪前后变化和反思。", page: "38", img: p("home_checkins"), bullets: ["记录是否完成训练", "记录情绪前后变化", "保存练习反思", "为周报和研究导出提供数据"], caption: "打卡让“练习有没有用”可以被观察。" }),
  imageSlide({ section: "38 | 周度报告", title: "周度报告：阶段性总结高频场景和下周建议", subtitle: "从单次反馈走向周期性陪伴。", page: "39", img: p("home_reports"), bullets: ["汇总高频场景和情绪", "整理常见互动模式", "汇总已完成训练卡", "给出下周建议"], caption: "周报是安心家的阶段性反馈形式。" }),
  imageSlide({ section: "39 | 人工督导", title: "人工督导：从自动反馈升级到人工支持", subtitle: "当系统反馈不足以回应复杂情况时，需要人工支持入口。", page: "40", img: p("home_supervision"), bullets: ["提交督导请求和联系方式", "保留风险提示字段", "支持人工回复和状态管理", "与伦理边界直接相关"], caption: "督导入口是平台安全性的一部分。" }),
  imageSlide({ section: "40 | 规则库", title: "反馈规则库：保证非诊断反馈可解释、可维护", subtitle: "规则库把“如何解释”从代码中分离出来。", page: "41", img: p("home_rules"), bullets: ["规则基于标签和场景触发", "输出触发总结、模式总结和替代回应", "便于研究者调整内容", "后续可接入0版网页画像规则"], caption: "规则库是安心家内容工程的核心。" }),
  imageSlide({ section: "41 | 数据导出", title: "数据导出：服务论文与用户研究", subtitle: "安心家后台需要能导出家长端闭环数据。", page: "42", img: p("home_export"), bullets: ["支持后台导出", "可整理目标、记录、反馈、打卡、周报、督导", "后续接入学生画像和沙盘记录", "导出必须受授权和伦理边界控制"], caption: "导出能力连接产品和科研。" }),
  imageSlide({ section: "42 | 联调测试", title: "联调测试：验证后端、网页端和内容规则能跑通", subtitle: "当前安心家已有最小联调入口。", page: "43", img: p("home_integration"), bullets: ["创建情绪事件记录", "生成即时反馈", "获取训练卡推荐", "验证三步闭环"], caption: "联调测试保证系统不是静态页面。" }),
  miniGridSlide({ section: "43 | 小程序入口", title: "小程序端：面向家长的轻量入口", subtitle: "小程序端适合日常记录和练习。", page: "44", images: [p("mini_home"), p("mini_training"), p("mini_assessment")], labels: ["首页", "训练", "测一测"], note: "小程序首页承接低负担使用，训练页承接干预内容，测评页承接工作表和未来0版网页能力。" }),
  miniGridSlide({ section: "44 | 小程序闭环", title: "小程序端闭环：记录、反馈、打卡、周报、督导", subtitle: "家长端的日常使用应尽量短、清楚、可持续。", page: "45", images: [p("mini_diary"), p("mini_feedback"), p("mini_checkin"), p("mini_weekly_report"), p("mini_supervision")], labels: ["记录", "反馈", "打卡", "周报", "督导"], note: "这些页面共同构成安心家的长期陪伴闭环，0版网页可作为其中的评估入口。" }),
  flowSlide({ section: "45 | 下一阶段", title: "下一步：先完善0版网页，再并入安心家", subtitle: "以可汇报、可演示、可研究为优先。", page: "46", steps: [["第1周", "0版网页完善", "C.green"], ["第2周", "研究验证", "C.teal"], ["第3周", "合并准备", "C.blue"], ["第4周", "合并演示", "C.amber"], ["导师确认", "论文主线", "C.red"]], note: "需要导师确认：论文主线更偏治疗性评估流程、机器学习画像验证，还是安心家产品化平台建设。" }),
];

async function main() {
  await fs.mkdir(SLIDES_DIR, { recursive: true });
  for (let i = 0; i < slides.length; i += 1) {
    const file = path.join(SLIDES_DIR, `slide-${String(i + 1).padStart(2, "0")}.mjs`);
    await fs.writeFile(file, moduleSource(i + 1, slides[i]), "utf8");
  }
  console.log(JSON.stringify({ slideCount: slides.length, slidesDir: SLIDES_DIR }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});

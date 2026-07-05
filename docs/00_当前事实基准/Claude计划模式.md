# Claude 计划模式：量表录入 · 聚类画像 · 前端重构

> 适用仓库：`nayunzhishui/safehome1.0`
> 本文件位置：`docs/00_当前事实基准/Claude计划模式.md`（创建于 2026-06-29，来源：Claude Code 计划模式 · Claude Opus 4.8）
> 双执行体：**Claude Code** 与 **Codex**。颗粒度对齐 `docs/08_已完成整改记录/6.5已完成增强问题逐步开发清单.md`。
> 核心原则：**先判断是否已完成，再决定是否修改；已完成不重复开发，未完成才最小改动；代码优雅、干净、整洁、简洁、高效。codex在任何前端设计方面参考skills库中的设计库，优先调用skills进行前端设计**

---

## 0. Context（为什么做）

SafeHome 已有完整「测一测」引擎（量表 API / 通用计分 / DB / 三页前端 / 风险护栏），但三处价值未释放：①夏老师 168 份量表已完成内容梳理，但 `scales_catalog.json`（13 台账）/`scale_item_drafts.json`（题项草稿）→ 用户端唯一数据源 `assessment_worksheets.json`（仅 3 份）之间**搬运链路断裂**，且用户无法按分类自由选择；②既往 9 组 SPSS 数据**未转化为聚类画像**，用户看不到自己在群体中的位置；③小程序视觉偏「AI 味」，需全站重构。
**预期结果**：用户在小程序按「三大类 + 情绪反射弧节点 + 搜索」自由选量表 → 填写 → 提交后获计分与（有画像的量表）**散点落点 + 雷达 + 客观特征/支持建议** → 全站视觉统一重构。

## 1. 技术栈结论（评估后：不更换）

| 端 | 栈 | 结论 |
|---|---|---|
| 后端 | Flask 2.2 + 手写 SQL（SQLite/MySQL 双后端）+ pytest（115 测试） | 保留 |
| Web | React 19 + TS 5.8 + Vite 7（无 UI 库、手写路由） | 保留（本计划基本不动） |
| 小程序 | 原生 JS + CloudBase `callContainer` | 保留（任务3 在其上重构） |
| 跨端 | `shared/`（`types/api.ts` + `constants/api.ts`）+ `{ok,data}` 协议 | 保留并强制同步 |

唯一新增技术面：任务2 离线聚类依赖（pandas/scikit-learn/pyreadstat），**隔离在 `analysis/profiling/`**，不进后端运行时。

## 2. 全局规则（Claude 与 Codex 共同遵守）

**2.1 执行前必读**：`docs/10Claude协作/{协作交接.md,代码审查.md,Claude使用记录.md}`、`docs/00_当前事实基准/项目进度统一口径.md`、D:\codex\workspace\safehome1.0\docs\00_当前事实基准\项目进度统一口径.md，本文件对应任务章节。
**2.2 Claude/Codex 差异约定**：差异处用「**【Codex 在本处如何操作】**」标注。通用差异：①解析二进制量表（docx/pdf/sav）——Claude 跑一次性 Python（python-docx/pdfplumber/pyreadstat）；Codex 同理，缺库则标 `pending_extraction` 并把待补清单交用户。②figma——Claude 无 figma skill，走「设计规范+手写」；Codex 若接入 figma MCP 可改为拉 token。③装依赖/长任务——Claude 直接在 `analysis/profiling/` 建 venv 跑；Codex 按 `requirements-analysis.txt` 执行。
**2.3 禁止**：`git add .`/`commit`/`push`（除非用户要求）、删业务文件、重构整体架构、改真实 `.env`、提交 DB/backups/node_modules/dist、提交真实 token、**提交既往 .sav 原始/逐行隐私数据**、**擅改量表题项原文与计分规则**（录入=如实搬运）、把草稿标 `fully_approved`、新增 AI 自由咨询/临床诊断/医疗级危机干预。
**2.4 允许修改**：`backend/** content/** docs/** apps/web/** apps/miniprogram/** shared/** backend/tests/** scripts/** analysis/**`；以下仅对应子任务明确要求时改：`backend/models.py backend/database.py apps/web/src/services/safehomeApi.ts apps/miniprogram/services/api.js content/risk_keywords.json content/readfeedback/**`。
**2.5 留痕**：任务2 设计留痕 → `safehome1.0其他内容/画像系统设计_Claude_20260628/`（补 02/03/04）；最终报告 → `safehome1.0其他内容/画像系统聚类结果报告_Claude_<日期>.md`；每子任务完成向 `docs/10Claude协作/Claude使用记录.md` 第 4 节按模板追加一条；重要进度同步 `docs/00_当前事实基准/{开发日志.md,开发说明.md}`。
**2.6 基础检查命令**：
```powershell
cd D:\codex\workspace\safehome1.0; python backend\scripts\validate_content.py
cd D:\codex\workspace\safehome1.0\backend; python -m pytest tests -q
cd D:\codex\workspace\safehome1.0\apps\web; npm run build
cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram -Recurse -Filter *.js  | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

---

## 3. 精确事实基准（执行者必读 · 改之前先核对行号是否漂移）

**3.1 数据库**（`backend/models.py` / `backend/database.py`）
- `assessment_results`（models.py:153-164）：`id,user_id,worksheet_id,worksheet_title,category,answers_json,scores_json,total_score,result_summary,created_at`（**无 updated_at**）。学生画像也写此表（worksheet_id=`student_profile_v1`，category=`学生画像`，total_score=None，结构化结果塞 scores_json）。
- `student_profiles`（models.py:167-200）：已含 `cluster_id(INT),pc1(REAL),pc2(REAL),nearest_distance,second_distance,dimensions_json,visuals_json,report_json,profile_code,profile_name,confidence,scores_json,...` —— **任务2 可参考其字段语义**，但该表语义属"学生画像"。
- 加列：`ensure_column(conn, table, column, definition)`（database.py:413）→ 在 `ensure_schema_columns()`（database.py:477）对应表 dict 加一行；`init_db()` 启动幂等执行。`CURRENT_SCHEMA_VERSION="2026_06_04_001"`（database.py:25），改 schema 时**同步升版本**。
- MySQL 适配：加**长文本 TEXT 列不要**进 `MYSQL_VARCHAR_COLUMNS`（database.py:27）；`*_json` 自动 LONGTEXT；仅"要进索引的短列"才登记白名单。
- 工具：`new_id(prefix)`、`now_iso()`、`json_dumps/json_loads`、`load_content_json(filename)`、`row_to_dict/rows_to_dicts`、`ensure_user`、`write_audit_log`。

**3.2 shared 契约**（`shared/types/api.ts` / `shared/constants/api.ts`，小程序 `apps/miniprogram/services/api.js` 有第二份端点表，**两处同步**）
- `AssessmentQuestion`（api.ts:206-212）当前仅 `type:"text"|"scale"`，**无 dimension/reverse_scored**（仅存在于内容 JSON）→ 若前端要用须扩展类型。
- 已有 `ProfileVisuals`（api.ts:350-359）：`{ radar[]; pca:{user,points,clusters}; trends[]; keywords? }` —— **任务2 落点可视化直接复用此契约**。
- 端点：`assessments=/api/assessments`、`assessmentResults=/api/assessment-results`、`profile=/api/profile`、`profileResults=/api/profile-results`、`modelInfo=/api/model/info` 等。

**3.3 量表 API 与计分**（`backend/routes/assessments.py`）
- `GET /api/assessments`（:151，支持 `?category=`）→ `_summarize_worksheet`（:34-50）固定字段。`GET /api/assessments/<id>`（:161，返回整份 worksheet + `training_recommendation_rules`）。`POST /api/assessment-results`（:176-232）。`GET /api/assessment-results`（:235，仅返回当前 worksheet id 内记录）。
- **通用计分引擎**`_score_answers`（:70-121）已支持：`dimension_score_method` 取 `sum`/`mean`；反向 `_effective_score`（:60-67）按 `low+high-score`；`len(dimensions)>1` 才写 `scores.dimensions`。**结论：新量表（含 7 点+反向+多维如 PRFQ）只配 JSON，零计分代码改动。**
- assessments.py **当前未导入** `check_text_risk`/`create_risk_review_record`（任务1 自由文本题需新增导入）。

**3.4 画像引擎**（`backend/services/student_profile_model_service.py` + `backend/routes/profile.py`）
- 匹配算法（service:231-275）：z 标准化 → 到各 `cluster.center`（z 空间）欧氏距离 → 最近簇 → 置信度 `(second-nearest)/(second)` → PCA 2D `pc=Σ z·pca_components`（**无 pca_mean**，隐含以 feature_means 为中心）。
- `content/readfeedback/student_profile_model.json` 结构：`features[],feature_means{},feature_stds{},chosen_k,model_selection[],pca_components[2×N],pca_explained_ratio,clusters[]{cluster_id,profile_id,profile_name,n,percent,mean_scores,z_profile,center[],center_pc[2],first_task},training_points[]{cluster_id,profile_id,pc1,pc2},scoring_notes` → **任务2 每组产出同构模型**。
- `build_student_visuals`（service:349）已生成 radar+pca散点+trends；接口 `GET /api/profile-results/<id>/visuals` 已存在。
- 家长计分 `score_parent_scale_answers`（parent_assessment_service.py:52）**硬编码 1-5 + `6-raw`**，**PRFQ 7点禁用此函数**（PRFQ 走通用 worksheet 引擎，见 3.3）。

**3.5 风险接入**（`backend/services/risk_service.py` / `risk_review_service.py`）
- `check_text_risk(text|list, source)` → `{risk_level,matched_categories,requires_review,allow_auto_feedback,...}`。
- `create_risk_review_record(conn,user_id,source_type,source_id,risk_result)` 仅 medium/high 落库。范式见 `routes/feedback.py:94-136`、`routes/profile.py:277-278`。

**3.6 前端三页与资产**（`apps/miniprogram/`）
- 列表页 `pages/assessment/index.js`：现有前端关键词硬分组 `GROUP_DEFINITIONS`（student/parent/adult），`getGroupKey` 返回 `"pending"` 会**静默丢卡（bug，须修）**；`listAssessments()` 无参；**无 Tab/无搜索**。
- 详情页 `pages/assessment-detail/index.js`：`withAnswerState` 注入答题态；scale→option-row、text→textarea；提交分叉（`isStudentProfile`→`createProfile`，否则 `createAssessmentResult`）；`buildProfilePayload` 按固定 key 取值。
- 结果页 `pages/assessment-result/index.js`：**无任何 canvas/图表**；维度纯文字卡；有训练卡推荐区；画像分支靠 `category==='学生画像'`。
- **全局无 canvas/chart 代码**（任务2 自建）。组件 7 个（alert-card/section-title/welcome-card/course-card/training-task-card/function-entry-card/bottom-tip-card）。
- **design token 已存在**（app.wxss:1-47）：`--safe-primary:#578b5f`、`--safe-bg:#fff8ee`、`--safe-card:#fffdf8`、`--safe-radius-*`、`--safe-shadow-*`、公共类 `.safe-page/.safe-card/.safe-h1...`。tabBar：home/training/course/profile。
- 现有 3 worksheet 真实 id：`student_profile_v1`（特殊，6 题 4scale+2text、无 dimensions、category=学生画像、走 /api/profile，**导入脚本不可破坏**）、`emotion_regulation_erq`（2维 sum 7点）、`parent_reflective_functioning_prfq`（3维 mean 7点 + PRFQ11/18 reverse_scored，**已验证通用引擎计分正确**）。
- Web `apps/web/src/pages/ScalesReview.tsx`：静态 import `scales_catalog.json`，**纯只读、无写、无画像**。

**3.7 validate_content.py 排除逻辑**（要改的点）：`EXCLUDED_SCALE_KEYWORDS`（:28-49）+ `is_excluded_scale`（:330）+ `validate_scales_catalog_exclusions`（:343-364）当前把焦虑/抑郁/睡眠/人格类**硬钉** `enabled=false/excluded_from_user_flow=true`。

---

# 任务一：量表按分类录入并打通全链路

**目标**：量表按「情绪反射弧 / 家长自助 / 学生自助」三大类（情绪反射弧内再按 诱因→反应→觉知→接纳→转化→应对→结果 节点）录入，用户端**分类 + 搜索**自由选填，API/后端/前端/DB 全链路打通。
**用户授权决策（务必如实记录）**：诊断/筛查类量表（GAD-7/PHQ-9/DASS/ISI/PSQI/EPQ/大五等）**全部开放**；突破原「筛查类不开放」红线，由用户明确授权；实现上**强制保留非诊断免责声明**作为最低防护。

### T1-01 内容模型扩展（分类字段 + schema）
**改动**：worksheet 与 catalog scale 统一新增：
```text
audience_class : "emotion_reflex" | "parent_self" | "student_self"
reflex_node    : "trigger|reaction|awareness|acceptance|transformation|coping|outcome" | null
search_keywords: string[]   # 别名/英文缩写(ERQ/PRFQ/SCS)/主题词
sensitive_category : bool    # 诊断/筛查/人格化量表为 true（驱动免责强校验）
result_disclaimer  : string  # 结果页免责（敏感类必填，普通类可继承 boundary_notice）
```
保留旧 `category`（结果页/导出/旧画像分支仍用）；新字段为分类树权威源。节点取值与情绪反射弧框架链条一致。`content/schemas/` 增 `assessment_worksheets.schema.json`（若无）并补字段；`scales_catalog.schema.json` 同步。
**【Codex 在本处如何操作】**：仅改 schema 定义；worksheet 实例字段由 T1-04 脚本回填，不手工逐条编辑。
**允许修改**：`content/schemas/**`、`content/scales_catalog.json`（人工区字段）。**完成标准**：schema 含新字段且 `validate_content.py` 通过。

### T1-02 改 validate_content.py（放开诊断类 + 必备边界）
**改动**：把"硬排除"改为"软标注 + 必备边界"：
- 移除/改造 `validate_scales_catalog_exclusions` 对 `enabled/excluded_from_user_flow/review_status` 的强制；保留 `is_excluded_scale` 仅用于**自动给该量表打 `sensitive_category=true`** 的校验提示（不再拦截开放）。
- 新增：对 `sensitive_category=true` 的量表与 worksheet，强校验 `boundary_notice` 含 `BOUNDARY_TERMS`（不构成诊断/不替代心理咨询/不替代危机干预）之一，且 `result_disclaimer` 非空——缺失则报错。
- 保留 `FORBIDDEN_TERMS` 全局禁用语、worksheet 旧前缀拦截（`worksheet_`/`appendix_b_examples_`）。
**必须更新测试**`backend/tests/test_content_validation.py`：将"诊断量表必须 disabled"用例改为"诊断量表 `enabled=true` 但缺 boundary/disclaimer→报错；补齐→通过"。
**允许修改**：`backend/scripts/validate_content.py`、`backend/tests/test_content_validation.py`、`content/schemas/**`。**完成标准**：诊断类可 `enabled=true` 且校验通过；缺免责则失败。

### T1-03 题项录入
**改动**：按"D:\codex\workspace\safehome1.0其他内容\量表内容报告_20260628.md"优先，把这些量表都录入进去，把可解析题项如实补入 `content/scale_item_drafts.json`（结构同现有 PRFQ draft：`likert[]/dimensions[]{code,label,item_codes,reverse_item_codes}/items[]{item_code,display_order,text,dimension,reverse_scored}`）。
**Claude 做法**：对 docx（python-docx）/pdf（pdfplumber）/xlsx（openpyxl）写一次性解析脚本抽题→逐条人工核对题面与反向题→更新 catalog `item_status/scoring_status`；解析不出的（caj/sav/老 doc）写入 `docs/量表待人工录入清单.md` **交用户录入**。**严禁臆造题项与计分**。
**【Codex 在本处如何操作】**：同写解析脚本；缺库或解析失败则该量表标 `item_status:pending_extraction` 并入待补清单交用户。
**允许修改**：`content/scale_item_drafts.json`、`content/scales_catalog.json`、`docs/量表待人工录入清单.md`。**完成标准**：每个拟 `enabled=true` 量表题项+计分完整且经核对。

### T1-04 导入脚本 build_worksheets.py（drafts+catalog→worksheets，幂等·零回归）
**新增**`backend/scripts/build_worksheets.py`：
```text
输入 scale_item_drafts.json + scales_catalog.json；对每个 enabled 量表生成 worksheet：
  items[]→questions[]（item_code→id, text→prompt, type=scale, dimension, reverse_scored）
  likert[]→每题 options[]（value/label/score）
  dimensions[] 透传；dimension_score_method（PRFQ=mean，单维/未声明=sum）
  audience_class/reflex_node/search_keywords/sensitive_category/result_disclaimer 来自 catalog
  enabled_for_user=scale.enabled；recommended_card_ids 透传；boundary_notice 注入（敏感类必填）
零回归：worksheet.id==scale.id；**手工保留清单**（不被覆盖）：student_profile_v1 整条、
  各 worksheet 的 sections 文案、source_file/source_title、人工润色字段——用 worksheet 上
  `_generated:true` 标记区分"脚本生成区"与"人工区"；脚本只覆盖生成区，人工区做深合并保留。
  student_profile_v1 直接跳过（它由 /api/profile 链路维护，不在 drafts 中）。
幂等：再次运行无意外 diff；打印 新增/更新/跳过/保留 统计。
```
**必须新增测试**`backend/tests/test_build_worksheets.py`：PRFQ 7点+反向→options/method=mean 正确；student_profile_v1 原样保留；二次运行幂等。
**允许修改**：`backend/scripts/build_worksheets.py`、`content/assessment_worksheets.json`、`backend/tests/**`。**完成标准**：脚本产物过 `validate_content.py`，幂等，现有 3 worksheet 零回归。

### T1-05 后端 API（分类/搜索/groups + 自由文本风险接入）
**改动**`backend/routes/assessments.py`：
- `_summarize_worksheet` 增返回 `audience_class/reflex_node/search_keywords/sensitive_category/enabled_for_user`。
- `list_assessments` 支持 query：`audience_class`、`reflex_node`、`q`（模糊匹配 display_title+search_keywords）；响应增 `groups`（按大类/节点聚合计数树，供前端直接渲染）。
- `get_assessment` 透传 `result_disclaimer`。
- **自由文本风险**：`create_assessment_result` 内对 `answers` 中 `type=="text"` 的值 `check_text_risk(text, source="assessment")`；high 时按 feedback 范式不返回普通推荐、置 `risk_level`；`conn.commit()` 前 `create_risk_review_record(conn,user_id,"assessment",result_id,risk_result)`。新增两处 import。
**必须新增测试**`backend/tests/test_assessments_route.py`：按 `audience_class/reflex_node/q` 过滤、`groups` 计数、含敏感词 text 题→生成 risk_review_record。
**允许修改**：`backend/routes/assessments.py`、`backend/tests/test_assessments_route.py`。**完成标准**：分类/搜索/风险接入正确，旧提交/历史接口不回归。

### T1-06 shared 契约同步（防两端漂移）
**改动**：`shared/types/api.ts` 扩展 `AssessmentListItem`/`AssessmentWorksheet`（加 `audience_class/reflex_node/search_keywords/sensitive_category/result_disclaimer`）、`AssessmentQuestion`（加可选 `dimension?/reverse_scored?`）、新增 `AssessmentGroupNode` 类型；`shared/constants/api.ts` 如需新端点则加。`apps/miniprogram/services/api.js` 的 `API_ENDPOINTS` 与 `listAssessments(params)` 同步（透传分类/搜索参数）。
**允许修改**：`shared/**`、`apps/miniprogram/services/api.js`。**完成标准**：Web `npm run build` 通过；小程序 JS 检查通过；两份端点表一致。

### T1-07 小程序列表页（三大类 Tab + 节点分组 + 搜索 + 修 bug）
**改动**`pages/assessment/`：
- `data` 增 `activeClass`（默认 emotion_reflex）、`keyword`、`groupsTree`。
- 改 `loadAssessments` 调 `api.listAssessments({audience_class, q})`，直接用后端 `groups`/`items` 渲染，**弃用前端关键词硬分组**（修 `getGroupKey` 的 "pending" 丢卡 bug：未归类量表归入"其他"可见分组，不静默丢弃）。
- 顶部三大类 Tab（纯 view 实现，无第三方组件）；情绪反射弧大类下渲染 7 节点二级分组；顶部搜索框 `<input bindinput>` 防抖调 `q`。空分组隐藏。
- 卡片展示 `sensitive_category` 提示标签；点击导航沿用现有 `openAssessmentEntry`。
**允许修改**：`pages/assessment/index.{js,wxml,wxss,json}`。**完成标准**：三大类+节点+搜索可用；无量表被静默丢弃；JS/JSON 检查通过。

### T1-08 小程序详情页（通用渲染适配 + 边界）
**改动**`pages/assessment-detail/`：复用现有 scale/text 渲染（已支持任意 likert，含 7 点）；展示 `instructions`、`boundary_notice`；`sensitive_category` 量表在题首显著展示免责。**保留** student_profile_v1 的 `createProfile` 分叉不动。
**允许修改**：`pages/assessment-detail/index.{js,wxml,wxss}`。**完成标准**：任意量表可填可交；JS 检查通过。

### T1-09 小程序结果页（维度展示 + 免责 + 画像入口预留）
**改动**`pages/assessment-result/`：维度沿用现有 `scaleDimensions` 文字卡（"不相加、不比高低"）；底部固定 `result_disclaimer`；**为任务2 预留画像区占位**：worksheet 含 `profile_model_id` 时显示"查看我的画像位置"入口（T2-09 接入）。
**允许修改**：`pages/assessment-result/index.{js,wxml,wxss}`。**完成标准**：维度/免责正确；有画像量表显示入口占位。

### T1-10 数据字典与文档登记
**改动**：`docs/03_技术真相/数据字典.md`（与 `数据库字段说明.md`）登记 worksheet/catalog 新字段；`docs/10Claude协作/Claude使用记录.md` 追加记录。
**允许修改**：`docs/**`。

### T1-11 任务一验收
```text
python backend\scripts\build_worksheets.py（幂等）→ validate_content.py 通过 → backend pytest 通过
→ Web npm run build 通过 → 小程序 JS/JSON 检查通过
→ 人工走查：三大类/节点/搜索选量表 → 填写（含 7 点/反向）→ 结果维度+免责 → 现有 3 量表零回归
```

### 附录A：量表→三大类/节点 归属 + 第一批开放清单
分类总表（32 条目，节选关键，完整随 T1-03 落 `docs/量表分类映射表.md`）：PRFQ→家长自助；父母养育倦怠/家庭亲密度/父母自主支持→家长自助；ERQ→情绪反射弧·转化；正念MAAS/FMI→觉知；AAQ→接纳；CD-RISC/认知灵活性→转化；SCS→接纳/转化；领悟社会支持→结果；学习投入/认知好奇/情绪弹性/情绪智力/回避融合/心理韧性RSCA→学生自助；GAD-7/PHQ-9/DASS/ISI-PSQI/GHQ-12/EPQ/大五→情绪反射弧·反应（敏感类，按授权开放但 `sensitive_category=true`）。
**第一批开放（题项+计分就绪）**：A1 PRFQ（家长自助，18题草稿已就绪）、A2 ERQ（转化，已就绪）、A3 SCS（接纳）、B1 CD-RISC-10（转化）、B2 青少年情绪弹性（学生自助）、B3 学习投入（学生自助）、B4 MAAS（觉知）。

---

# 任务二：既往数据聚类画像 + 可视化落点

**目标**：对既往数据**每组每量表单独聚类**（绝不跨组合并；一表多量表则拆开），产出画像模型与「客观特征+支持建议」解释；用户填完对应量表后看到**散点落点 + 雷达**。落点端到端先打通有产品量表的组（PRFQ 优先）。

### T2-01 独立分析环境
**新增**`analysis/profiling/`：`requirements-analysis.txt`（pandas,scikit-learn,pyreadstat,numpy,scipy,matplotlib）、`config.py`（既往数据根路径=项目外、输出路径、`RANDOM_SEED=42`）、`README.md`（数据不入仓声明）、`.gitignore`（忽略中间数据/venv）。
**【Codex 在本处如何操作】**：如果已有分析功能，不需要额外添加依赖，先看一下本机有没有对应依赖，按 `requirements-analysis.txt` 装依赖；缺 pyreadstat 则改用既往盘点 CSV 中可用数值列并在报告标注"未读原始 .sav"。**约束**：原始 .sav/逐行数据严禁入仓，仅聚合画像模型 JSON 入仓。

### T2-02 数据拆组与计分（依据附录B）
**新增**`analysis/profiling/01_extract_groups.py`：按「研究组×量表」拆分（字段范围见附录B）；每组：选题→反向计分（按各量表点数，如 PRFQ `8-raw`）→维度分/总分→缺失值处理（缺失比阈值剔除/均值填补，记录策略）→z 标准化。输出每组特征矩阵到项目外中间目录（含 features 列名/均值/标准差/样本量）。留痕至 `画像系统设计_Claude_20260628/02_分组聚类设计.md`。
**完成标准**：每组干净特征矩阵+计分口径文档；PRFQ 组与产品 worksheet 口径一致（7点/`8-raw`/维度均值）。

### T2-03 每组聚类+降维（产出模型 JSON）
**新增**`analysis/profiling/02_cluster.py`，对**每组独立**：KMeans k∈[2..6]（`random_state=RANDOM_SEED`），用 silhouette+肘部+最小簇样本量选 k；PCA 前 2 主成分做 2D 投影。产出**对齐 `student_profile_model.json` 的同构模型**（见 3.4），文件含 `source_group`、`clusters[]{cluster_id,size,center[],centroid_2d,mean_scores,dimension_means}`、`pca_components`、`training_points`（脱敏，仅 cluster_id+pc1+pc2，**不含任何可回溯个体的原值**）。
**约束**：每组一个模型文件，绝不混合；样本<~120 的组（附录B 标注）降 k 或仅出描述、标注"样本偏小"。
**完成标准**：每组模型可复算用户落点；PRFQ 组 silhouette/簇规模合理并记录。

### T2-04 画像定义与解释（客观特征 + 支持建议）
**改动**：为每组每簇写解释入模型 JSON `clusters[].profile`：`title`（中性非诊断画像名）、`objective_desc`（基于 center 的各维相对高低，客观）、`support_advice`（成长方向，非治疗承诺）、`disclaimer`（不构成诊断/不替代咨询）。口径=**客观特征+支持建议**。留痕 `03_画像定义与匹配算法.md`。
**完成标准**：每簇四段齐全；过 `FORBIDDEN_TERMS`，无人格/诊断定性。

### T2-05 画像模型落地 content + schema
**改动**：模型 JSON → `content/profiles/<group_id>_profile_model.json`（脱敏聚合，入仓）；worksheet 增 `profile_model_id` 关联（仅有画像的量表，经 T1-04 脚本/人工）；新增 `content/schemas/profile_model.schema.json` 并纳入 `validate_content.py`（校验 features/clusters/pca 完整性 + 解释非空 + 禁用语）。
**允许修改**：`content/profiles/**`、`content/schemas/**`、`content/assessment_worksheets.json`、`backend/scripts/validate_content.py`。

### T2-06 后端匹配服务 + 接口（实时计算，复用可视化契约）
**新增**`backend/services/profile_match_service.py` + 路由 `GET /api/assessment-results/<id>/profile`：
```text
读 assessment_result.scores_json + worksheet.profile_model_id → 载入 content/profiles 模型
→ 按 feature_means/stds z 标准化 → 投影 pca_components 得 point_2d
→ 到各 cluster.center 欧氏距离取最近簇 + 置信度（复用 student_profile_model_service 同款算法，抽公共函数）
→ 返回（复用 ProfileVisuals 契约，api.ts:350-359 结构）:
   { point_2d, nearest_cluster_id, clusters:[{cluster_id,centroid_2d,size,profile}],
     radar:{ axes, user_values, cluster_values }, confidence, disclaimer }
```
**设计选择**：落点**实时计算不落表**（给定分数+模型可复算，保持简洁；scores 已存 assessment_results）。鉴权沿用 `require_admin_or_owner`（owner=匿名 user_id）。**禁用** `score_parent_scale_answers`（3.4）。
**必须新增测试**`backend/tests/test_profile_match_route.py`：已知分数→落点/最近簇稳定；无 profile_model_id 量表→404 友好；非 owner→401。
**允许修改**：新增 service/route、`backend/routes/assessments.py`（或新 blueprint）、`backend/tests/**`。

### T2-07 shared 契约同步
**改动**：`shared/types/api.ts` 新增 `ProfilePosition`（point_2d/nearest_cluster_id/clusters/radar/confidence/disclaimer）；`shared/constants/api.ts` 加端点；`apps/miniprogram/services/api.js` 加 `getAssessmentProfile(resultId)`。
**完成标准**：Web build + 小程序 JS 通过。

### T2-08 小程序 canvas 可视化（从零自建，零图库）
**新增**`apps/miniprogram/utils/chart.js`（纯函数绘制）+ 组件 `components/profile-scatter/` 与 `components/profile-radar/`：
```text
散点：Canvas 2D；坐标变换（数据域→画布，留边距）；绘簇心+簇着色+用户落点高亮"您在这里"+图例；
     自适应 rpx→px（wx.getSystemInfo dpr）；training_points 作浅色底图。
雷达：N 轴（维度）；归一化到统一量纲（按各维 min/max 或 0..max）；绘用户多边形 + 最近簇轮廓对比 + 轴标签。
性能：单次绘制、无动画循环；离屏数据由接口给好，前端不算聚类。
```
**【Codex 在本处如何操作】**：优先调用skills，同用原生 Canvas 2D；若选用 ec-canvas 需先评估包体，默认不引第三方。
**完成标准**：散点/雷达正确渲染；JS/JSON 检查通过。

### T2-09 结果页接入画像区
**改动**`pages/assessment-result/`：worksheet 有 `profile_model_id` 时，调 `getAssessmentProfile(resultId)` → 渲染散点+雷达组件 + `nearest.title/objective_desc/support_advice/disclaimer`。无模型量表不显示该区。
**完成标准**：填完 PRFQ→结果页见散点落点+雷达+解释。

### T2-10 留痕文档与报告
补全 `画像系统设计_Claude_20260628/{02_分组聚类设计.md,03_画像定义与匹配算法.md,04_量表补齐与落地路线.md}`；输出 `safehome1.0其他内容/画像系统聚类结果报告_Claude_<日期>.md`（覆盖组、每组 k/样本/簇画像、端到端落点的组、待补量表的组与原因）。

### T2-11 任务二验收
```text
analysis 脚本可复现（同种子同结果）→ content/profiles/*.json 过 validate_content.py
→ backend pytest（profile_match）通过 → 小程序可视化走查（PRFQ）→ 留痕 02/03/04 + 报告齐全
```

### 附录B：既往数据 9 组 × 量表 拆分清单（聚类拆组依据）
| 组 | 人群 | 主样本量 | 量表单元（字段） | 可独立聚类 | 端到端对接 |
|---|---|---|---|---|---|
| 2 李霞庆 | 初中生+家长 | PRFQ 家长自评 400+（126+336…） | **PRFQ FS1-18(FS11/18反)**、RFQ T1-8、自主支持 Z1-12(青少年报告)、亲子 F/M | ✅ | **✅ PRFQ 唯一闭环** |
| 1 王季璇 | 初中生 | 634 | 亲子沟通 F1-14+M1-14、学业浮力、情绪弹性 | ✅ | ⚠️需产品新建量表 |
| 3a 夏媛媛初测 | 高一 | 652 | SCS（Q10/12/13/16/19/22/23/26/29 反） | ✅ | ⚠️学生引擎不重训→成人参照 |
| 5 牛至旭 | 中年女性 | 209 | SWLS、WHO-5、SCS | ✅ | ⚠️人群异→成人参照 |
| 6 高鸣聪 | 大学生 | 309 | HPLP(27)、目标感、SCS | ✅ | ✗ 成人参照 |
| 3b 夏媛媛暑期 | 混杂 | 100 | SCS | ⚠️偏小+混杂 | ✗ |
| 4 蒋鑫悦 | 大学生 | 159 | 调节聚焦、学业拖延（题面缺失） | ⚠️需先补题 | ✗ |
| 7 孙天娇 | 大学生 | 706 | 不健康体重控制（敏感主题） | ⚠️越边界 | ✗ |
| 8 李欣珊 | 大学生 | 341 | 学业压力/PSQI/心理灵活性（仅汇总分） | ⚠️无逐题 | ✗ |
| 9 疫情 | 混杂 | 数千 | GHQ-12/RISC/疫苗意向…（多主题混） | ⚠️需再拆 | ✗ |
**硬约束**：9 组各自独立聚类、绝不合并；首批画像聚焦组2 PRFQ（端到端）+ 组1/3a/5/6（画像库/常模，落点待产品量表）。

### 附录C：PRFQ 口径 + 桥强弱 + 需人工核对点
PRFQ：18题3维（PM:1/4/7/10/13/16；CM:2/5/8/11反/14/17；IC:3/6/9/12/15/18反），7点，反向 `8-raw`，维度均值；产品侧已配置正确，历史侧家长自评。桥强弱：PRFQ★★★★★（唯一闭环）＞亲子沟通★★★（产品须新建）＞自主支持★★☆（需补题+报告人对齐）＞SCS★★★☆（学生已闭环不重训）；IUS/ERQ/TA 无历史常模。
**执行期需人工核对（不阻塞计划）**：①PRFQ 历史 .sav 实际点数（确认 7 点以对齐 `8-raw`）；②父母自主支持报告人方向（青少年报告 vs 家长自评）二选一；③catalog 13 条 vs 报告 32 条 vs 运行层粒度不一致，录入以"运行层+草稿层"为准。

---

# 任务三：前端全站视觉重构（小程序用户端为主）

**目标**：小程序用户端**全站视觉重构**，风格「简洁高效 / 干净清爽 / 优雅温暖」、去 AI 味、尽量不用插图。在任务一、二之后做。

### T3-01 设计 token 演进 + 设计规范
**改动**：基于现有 `app.wxss:1-47` 的 `--safe-*` 变量**演进**（非从零）：收敛为「柔和中性底 + 单一温暖主色（沿用/微调 `--safe-primary`）+ 克制语义色」；统一字号/行高阶梯、8 倍数间距、圆角、克制阴影；去高饱和渐变/拟物/emoji 堆砌。沉淀 `docs/10Claude协作/前端设计规范_Claude.md`（色值、组件规范、Do/Don't）。
**【Codex 在本处如何操作】**：若接入 figma MCP，从 figma 拉 token 写入变量；否则按本规范实现。

### T3-02 公共样式与组件重构
**改动**：重构 7 个组件（alert-card/section-title/welcome-card/course-card/training-task-card/function-entry-card/bottom-tip-card）统一到 token；抽公共 class 去重；`welcome-card` 的 CSS 插画按"少插图"原则简化。**完成标准**：组件视觉统一、无样式回归。

### T3-03 逐页重构（清单）
按 tabBar 主线 + 任务1/2 新页逐页套 token：`home`、`training`、`course`、`profile(我的)`、`assessment(选择)`、`assessment-detail(填写)`、`assessment-result(结果+画像)`、`diary-form`、`checkin`、`weekly-report`、`goal-setting`、`feedback-result`、`training-card`、`supervision`、`task-detail`。每页：信息层级梳理、留白、去插图、统一卡片/按钮/列表。**约束**：只改样式与呈现，不改业务数据流与接口。
**完成标准**：全站风格一致、功能不回归、JS/JSON 检查通过。

### T3-04 去 AI 味文案
**改动**：扫描 `apps/miniprogram/**/*.{wxml,js}` 文案，按 6.5 P2-02 词表（治愈/重塑/改变人生/专业诊断/人格/异常/立即改善…）替换为具体、克制、支持性表达；合法边界文案（"不构成诊断"）不误改。留痕 `docs/05_伦理试用/文案低AI味与伦理表达检查.md`。

### T3-05 figma / Codex 差异说明
figma 设计稿对接：用户配置 figma MCP 后，Claude/Codex 可拉取设计稿比对实现；未配置则以 T3-01 规范为准。本任务**不阻塞**于 figma。

### T3-06 任务三验收
```text
小程序 JS/JSON 检查通过 → 设计规范文档齐全 → 走查 5 条主路径视觉与文案 →（可选）figma 比对
```

---

## 4. 收尾 · 归档 · 顺序 · 验证

**4.1 归档**：本计划已写入 `docs/00_当前事实基准/Claude计划模式.md`，并同步更新 `docs/00_当前事实基准/项目进度统一口径.md` 第 8 节「文档分类索引」。
**4.2 使用记录**：每子任务完成向 `Claude使用记录.md` 第 4 节按模板追加一条。
**4.3 执行顺序**：任务一（T1-01→11）→ 任务二（T2-01→11，依赖任务一 worksheet/计分口径）→ 任务三（T3-01→06）。任务一/二有交叉：要让亲子沟通/自主支持组端到端，需在任务一录入对应产品量表。
**4.4 端到端验证（总）**：
```text
后端：validate_content.py && (cd backend && pytest tests -q)
Web ：cd apps\web && npm run build
小程序：node --check 全量 *.js + ConvertFrom-Json 全量 *.json
分析：analysis/profiling 可复现，content/profiles/*.json 校验通过
人工：分类选量表→填写(含7点/反向/text风险)→结果维度+免责→(PRFQ)散点+雷达+解释→全站视觉走查
```
**4.5 最终汇报**：按 6.5 清单「最终汇报格式」输出（执行概况/修改文件/各任务状态表/测试结果/安全检查/下一步≤3 条）。
**4.6 Codex 一句话口令**：「请按 `docs/00_当前事实基准/Claude计划模式.md` 执行：任务一→二→三→四；每步先判断状态（已完成不重复开发），未完成才最小改动；每步跑对应测试并向 `docs/10Claude协作/Claude使用记录.md` 追加记录；遇 Claude/Codex 差异处按【Codex 在本处如何操作】执行。」

---

# 任务四：量表入库 · 云托管部署 · Web 可视化 · 认证打通

**目标**：① 量表定义与作答结果全部可见于数据库（DB 为唯一事实源）；② 后端部署至腾讯云云托管 + MySQL；③ Web 管理端增聚类散点/雷达可视化；④ 用户注册/登录认证打通前后端。
**执行时机**：任务一（T1-04 build_worksheets.py）完成后方可执行 T4-01；任务二（T2-06 profile_match_service）完成后方可执行 T4-03；T4-02/T4-04 可与任务一/二并行。

---

### T4-00 切换腾讯云 MySQL（轻量配置，不涉及部署）

**背景**：现在用本地 SQLite，用户希望数据存到腾讯云 MySQL。`config.py` 与 `database.py` 的双后端切换已完整实现（`DB_PROVIDER=mysql`），Dockerfile 也存在，**本步骤只做连接配置和验证，不改代码**。

**改动**：

**1. 复制并填写环境变量** — 以 `.env.example` 为模板，在项目根创建 `.env`（已在 `.gitignore` 中）：
```text
APP_ENV=production
DB_PROVIDER=mysql
MYSQL_HOST=<腾讯云 MySQL 内网/外网地址>
MYSQL_PORT=3306
MYSQL_USER=<用户名>
MYSQL_PASSWORD=<密码>
MYSQL_DATABASE=safehome
SECRET_KEY=<≥32位随机字符串>
ADMIN_EXPORT_TOKEN=<随机令牌>
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
CONTENT_DIR=content
```

**2. 安装 PyMySQL**（仅首次）：
```bash
pip install pymysql cryptography
```
或加入 `backend/requirements.txt`（若未在其中）。

**3. 初始化远程库** — 启动后端，`init_db()` 自动在 MySQL 上建表（幂等）：
```bash
APP_ENV=production DB_PROVIDER=mysql ... python backend/app.py
# 或直接调
python -c "from backend.database import init_db; init_db()"
```

**4. 验证** — 调 `GET /healthz/deep`，返回 `database.ok=true` + `database.provider=mysql` 即通过。

**完成标准**：`healthz/deep` 中 `database.ok=true`，`provider=mysql`；本地 SQLite 降级路径不破坏（`.env` 改回 `DB_PROVIDER=sqlite` 仍可启动）。**严禁**：把真实密码/host 提交到 git。

---

### T4-01 量表定义入库（assessment_worksheets 表 + 迁移 + API 切换）

**背景**：量表定义（worksheet）目前存 `content/assessment_worksheets.json`；作答结果（`assessment_results`）已在 DB。用户需量表定义也可在 DB 查询/管理。

**改动**：

**1. 新增表** — 在 `backend/models.py` `SCHEMA_SQL` 追加：
```sql
CREATE TABLE IF NOT EXISTS assessment_worksheets (
    id TEXT PRIMARY KEY,
    display_title TEXT NOT NULL,
    source_title TEXT,
    source_file TEXT,
    category TEXT,
    audience_class TEXT,
    reflex_node TEXT,
    questions_json TEXT NOT NULL DEFAULT '[]',
    dimensions_json TEXT NOT NULL DEFAULT '[]',
    dimension_score_method TEXT NOT NULL DEFAULT 'sum',
    scoring_notes_json TEXT NOT NULL DEFAULT '{}',
    search_keywords_json TEXT NOT NULL DEFAULT '[]',
    boundary_notice TEXT,
    result_disclaimer TEXT,
    instructions TEXT,
    sensitive_category INTEGER NOT NULL DEFAULT 0,
    profile_model_id TEXT,
    enabled_for_user INTEGER NOT NULL DEFAULT 1,
    review_status TEXT NOT NULL DEFAULT 'approved',
    review_note TEXT,
    source_version TEXT,
    source_type TEXT,
    audience TEXT,
    audience_class_detail TEXT,
    recommended_card_ids_json TEXT NOT NULL DEFAULT '[]',
    _meta_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```
索引：`CREATE INDEX IF NOT EXISTS idx_assessment_worksheets_audience_enabled ON assessment_worksheets(audience_class, enabled_for_user)`。将以上同步写入 `INDEX_SQL`。`MYSQL_VARCHAR_COLUMNS` 增 `audience_class/reflex_node/review_status/profile_model_id/dimension_score_method/source_version/source_type/audience`。

**2. 迁移脚本** — 新增 `backend/scripts/import_worksheets_to_db.py`：
```text
读 content/assessment_worksheets.json → 逐条 UPSERT 到 assessment_worksheets 表
（ON CONFLICT(id) DO UPDATE 覆盖非人工区字段）
student_profile_v1 特殊项不跳过，照常入库（只是标注 category='学生画像'）
幂等：二次运行仅更新 updated_at
打印 新增/跳过/更新 统计
```

**3. 后端 API 切换** — 修改 `backend/routes/assessments.py` 的三个 `_load_payload`/`_worksheets`/`_find_worksheet` 辅助函数：优先从 DB 读（`SELECT * FROM assessment_worksheets WHERE enabled_for_user=1` 或不过滤），JSON 文件降级为 `content/` 初始化时一次性来源（已入库后不再依赖）。具体：
```python
def _worksheets_from_db(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM assessment_worksheets ORDER BY display_title").fetchall()
    return [_db_row_to_worksheet(row) for row in rows]

def _db_row_to_worksheet(row: dict) -> dict:
    # 展开 *_json 字段并还原完整 worksheet 结构
    ...
```
**保留 `load_content_json` 降级路径**（DB 空时从文件读，便于本地冷启动）。

**4. Admin CRUD 接口** — 在 `backend/routes/admin.py` 增：
```text
GET  /api/admin/worksheets          → 全量列表（含 disabled），需 X-Admin-Token
POST /api/admin/worksheets          → 新增，需 X-Admin-Token + require_admin_token
PUT  /api/admin/worksheets/<id>     → 更新，字段白名单保护（禁改 id/created_at）
```

**5. DB health check** — `check_database_health()` 在 `REQUIRED_HEALTH_TABLES` 加 `assessment_worksheets`；`training_cards_sync_ok` 类比增 `worksheets_sync_ok`（DB 条数 ≥ JSON 条数）。

**必须更新/新增测试**：`backend/tests/test_assessments_route.py` 增 DB 路径下分类/搜索/提交计分用例；`backend/tests/test_import_worksheets.py` 验证迁移幂等 + student_profile_v1 完整保留 + PRFQ 题项/计分正确。

**CURRENT_SCHEMA_VERSION** 升版至 `"2026_07_01_001"` 并同步 `CURRENT_SCHEMA_NAME`。

**允许修改**：`backend/models.py`、`backend/database.py`、`backend/routes/assessments.py`、`backend/routes/admin.py`、`backend/scripts/import_worksheets_to_db.py`（新增）、`backend/tests/**`。

**完成标准**：迁移脚本幂等；`GET /api/assessments` 数据与 JSON 文件一致；pytest 通过；`healthz/deep` 中 `worksheets_sync_ok=true`。

---

### T4-03 聚类落点写入 DB + Web 端可视化（ResearchDashboard）

**背景**：`assessment_profile_service.py` 已完整实现落点匹配（z 标准化 → PCA 投影 → 最近簇），API `GET /api/assessment-results/<id>/profile-position` 已存在，`content/profiles/` 已有 PRFQ 等多个模型 JSON。**缺失**：计算结果没有持久化到 DB（`assessment_results` 无 pc1/pc2 字段；无独立落点缓存表）；Web 端无可视化界面。

**改动**：

**1. 落点结果写入 DB** — 用最轻方案：在 `assessment_results` 表加三列（不新建表）：
```sql
-- 在 ensure_schema_columns() 的 assessment_results dict 中追加：
"profile_model_id":   "TEXT"
"profile_cluster_id": "TEXT"
"profile_pc1":        "REAL"
"profile_pc2":        "REAL"
"profile_confidence": "REAL"
```
在 `routes/assessments.py` 的 `create_assessment_result` 末尾，提交 `assessment_results` 后**异步写落点**：
```python
# 若 worksheet 有匹配模型，实时计算落点并回写
try:
    position = build_assessment_profile_position(result_row, worksheet)
    conn.execute(
        """UPDATE assessment_results SET
           profile_model_id=?, profile_cluster_id=?, profile_pc1=?, profile_pc2=?, profile_confidence=?
           WHERE id=?""",
        (position["model_id"], position["position"]["cluster_id"],
         position["position"]["pc1"], position["position"]["pc2"],
         position["position"]["confidence"], result_id)
    )
    conn.commit()
except ProfilePositionUnavailable:
    pass  # 无模型的量表静默跳过，不影响提交
```
`MYSQL_VARCHAR_COLUMNS` 增 `profile_model_id/profile_cluster_id`。

**2. 安装 ECharts** — `apps/web` 内：
```bash
npm install echarts@^5 --save-exact
```

**3. 新增可视化组件** — `apps/web/src/components/ProfileScatterChart.tsx` + `ProfileRadarChart.tsx`：
```tsx
// ProfileScatterChart: 接收 position（含 pc1/pc2）+ clusters（含 pca_centroid），
//   渲染簇着色散点底图 + 用户落点「您在这里」高亮
// ProfileRadarChart: 接收 feature_profile（z_score 归一化）+ clusters 轮廓，
//   渲染双多边形对比（用户 vs 最近簇均值）
```

**4. ResearchDashboard 接入** — `apps/web/src/pages/ResearchDashboard.tsx`：
- 增 assessment_results 列表 → 选一条有 `profile_pc1` 的记录 → 调 `GET /api/assessment-results/<id>/profile-position` → 渲染两个组件。
- 无模型量表显示"暂无画像数据"，不崩溃。

**5. shared 类型同步** — `shared/types/api.ts` 新增 `AssessmentProfilePosition` 类型（`position/{pc1,pc2,cluster_id,profile_name,confidence}/clusters[]/feature_profile[]`，与 `assessment_profile_service` 返回结构对齐）；`shared/constants/api.ts` 加端点 `assessmentProfilePosition`。

**允许修改**：`backend/database.py`（`ensure_schema_columns`）、`backend/routes/assessments.py`、`apps/web/src/components/ProfileScatterChart.tsx`（新增）、`apps/web/src/components/ProfileRadarChart.tsx`（新增）、`apps/web/src/pages/ResearchDashboard.tsx`、`apps/web/package.json`、`shared/types/api.ts`、`shared/constants/api.ts`。

**完成标准**：填完 PRFQ → `assessment_results` 中 `profile_pc1/pc2` 有值；ResearchDashboard 散点+雷达可渲染；`npm run build` 通过。

---

### T4-04 用户认证打通前端（Web + 小程序，匿名数据丢弃）

**背景**：后端 `/api/auth/register` + `/api/auth/login` 已实现（werkzeug hash + JWT），`users` 表有 `username/password_hash/role/status` 字段，`generate_auth_token` 在 `routes/auth_utils.py`。Web 端 `LoginPage.tsx`/`RegisterPage.tsx` 已存在但未接 API；小程序未接。**匿名用户数据不迁移，注册后视为新用户**。

**改动**：

**1. 后端 auth_utils 补全** — 先确认 `routes/auth_utils.py` 中有：
- `generate_auth_token(user: dict) -> str`：生成含 `user_id/role/exp` 的 JWT
- `require_login` 装饰器：解析 `Authorization: Bearer <token>` header，注入 `g.current_user`
若缺 JWT 解码部分则补全；`PyJWT` 若不在 `requirements.txt` 则加入。

**2. safehomeApi 增认证方法** — `apps/web/src/services/safehomeApi.ts` 增：
```typescript
login(creds: {username: string; password: string}): Promise<{token: string; user: UserInfo}>
register(creds: {username: string; password: string; role?: string; nickname?: string}): Promise<{token: string; user: UserInfo}>
```
`requestRaw` 的默认 headers 增：`Authorization: Bearer <token>`（`authState.getToken()` 读；无 token 时不带）。

**3. authState 完善** — `apps/web/src/services/authState.ts` 确认有 `login/logout/getToken/getUser/isLoggedIn`（localStorage 持久化）；不完整则补全。

**4. LoginPage + RegisterPage 接 API** — 表单提交 → 调对应方法 → 成功后 `authState.login(token, user)` → 跳转主页；失败显示后端返回的 `error.message`。**登录成功后丢弃之前的匿名 `user_id`**（`userIdentity.ts` 中 `clearAnonymousUserId()` 若无则新增）。

**5. 小程序认证** — `apps/miniprogram/app.js` 增：
```javascript
// globalData 增 token/user 字段
// login(username, password): callContainer('/api/auth/login') → wx.setStorageSync('auth_token')
// logout(): wx.removeStorageSync('auth_token')
// 启动时 onLaunch 读缓存恢复登录态
```
`apps/miniprogram/services/api.js` 的请求 headers 增 `Authorization: Bearer ${wx.getStorageSync('auth_token') || ''}`。**同样不迁移匿名数据**（旧 `user_id` 直接丢弃）。

**6. 小程序登录/注册页** — 若无则新增 `pages/login/` 与 `pages/register/`（最小实现：用户名+密码表单，调 api.js 对应方法，成功后 navigateBack 或跳首页）。

**必须新增/确认测试**：`backend/tests/test_auth_route.py` 覆盖：注册→登录→token 有效→重复用户名 400→密码错 401→状态非 active → 403。

**允许修改**：`backend/routes/auth_utils.py`、`backend/requirements.txt`、`apps/web/src/services/authState.ts`、`apps/web/src/services/safehomeApi.ts`、`apps/web/src/services/userIdentity.ts`、`apps/web/src/pages/LoginPage.tsx`、`apps/web/src/pages/RegisterPage.tsx`、`apps/miniprogram/app.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/pages/login/**`（新增）、`apps/miniprogram/pages/register/**`（新增）、`backend/tests/test_auth_route.py`。

**完成标准**：Web 注册/登录/登出正常，token 随请求发送，登录后匿名 id 丢弃；小程序同；pytest 通过；小程序 JS/JSON 检查通过。

---

### T4-05 任务四验收
```text
云 MySQL ：healthz/deep → database.ok=true + provider=mysql；本地 sqlite 降级不破坏
量表入库 ：python backend/scripts/import_worksheets_to_db.py（幂等）→ GET /api/assessments 数据一致
           → healthz/deep: worksheets_sync_ok=true → pytest 通过
落点写 DB ：填完 PRFQ → assessment_results.profile_pc1/pc2 有值 → GET profile-position 返回正确
Web 可视化：npm run build 通过 → ResearchDashboard 散点+雷达可渲染 → 无画像量表不崩溃
认证      ：Web 注册→登录→登出→token 随请求→匿名 id 丢弃；小程序同；pytest 通过；小程序 JS/JSON 检查通过
```

---

# 任务五：训练卡内容升级 + 推荐算法完善

**目标**：① 训练卡内容达到循证心理学实操水准（UP/CBT 框架，家长 10 张 + 学生 10 张，针对量表核心构念）；② 修复量表维度分→卡推荐的断链；③ 画像簇→卡映射；④ 修复前后端代码逻辑缺陷。
**执行时机**：T5-01/T5-05 无前置依赖，可立刻执行；T5-03 依赖 T1-04（量表题项就绪）；T5-04 依赖 T2-x（画像模型就绪）。

---

### T5-01 训练卡内容重写（20 张，UP/CBT 精准版）

**背景**：现有 12 张卡语言偏模板化，目标达到"循证心理干预实操手册"水准——措辞精准、温暖、去 AI 味，聚焦可执行小动作，每张卡对应量表中的一个核心构念。

**内容框架（保持 UP/CBT，不引入新框架）**：

家长 10 张（对应 PRFQ 三维 + ERQ + 亲子沟通）：
| 卡 ID | 对应构念 | 核心技能 |
|---|---|---|
| `prfq_pm_awareness` | PRFQ-PM（前心智化）| 识别自动反应模式，暂停前先觉察 |
| `prfq_cm_tolerance` | PRFQ-CM（确定心理状态）| 容忍不确定：孩子内心状态不总是可读 |
| `prfq_ic_curiosity` | PRFQ-IC（兴趣好奇）| 用好奇替代解释，开放式问话练习 |
| `erq_reappraisal_parent` | ERQ 认知重评 | 对情境换一个解释，找第二种可能 |
| `erq_suppression_release` | ERQ 表达抑制 | 识别压抑信号，低风险表达一个感受 |
| `repair_after_rupture` | 关系修复 | 冲突后重建连接的具体话术步骤 |
| `validation_before_advice` | 非评判回应 | 先确认后建议，不急着解决 |
| `parent_body_grounding` | 身体信号 | 身体感觉作为情绪信号的落地练习 |
| `specific_request_replace_threat` | 行为替代 | 把威胁/催促换成一个5分钟可执行的小请求 |
| `one_open_question` | 亲子沟通 | 一次只问一个开放式问题，不叠问 |

学生 10 张（对应 SCS + ERQ + RSCA + student_profile）：
| 卡 ID | 对应构念 | 核心技能 |
|---|---|---|
| `scs_self_kindness` | SCS 自我善意 | 把自责改为朋友式支持句 |
| `scs_common_humanity` | SCS 共同人性 | 这种困难不只我一个人有 |
| `scs_mindful_moment` | SCS 正念觉察 | 不放大也不压制：观察情绪一分钟 |
| `erq_reappraisal_student` | ERQ 认知重评 | 找压力情境的第二种解读 |
| `erq_expression_gentle` | ERQ 表达抑制 | 写下一个还没说出口的感受 |
| `rsca_emotion_regulation` | RSCA 情绪调节 | 三步稳定情绪：命名-呼吸-小动作 |
| `rsca_positive_cognition` | RSCA 积极认知 | 找一个今天做到了的小事实 |
| `exam_micro_start` | 考试压力 | 把任务拆到"10分钟可开始"的颗粒度 |
| `auto_thought_rewrite` | CBT 自动想法 | 写下→找证据→改写一句更平衡的话 |
| `body_scan_before_study` | 身体意识 | 开始学习前60秒身体扫描落地 |

**每张卡写作标准**（与现有结构字段对齐，提升内容深度）：
- `steps[]`：3-4 步，每步一句短句，行动动词开头，无"尝试""可以"等软化词，具体到"说什么/做什么"
- `example`：1-2 句真实对话/独白，不用引号嵌套引号，不抽象
- `reflection_questions[]`：3 题，锚定当次练习中的具体行为（"我刚才命名的是哪一个词"而非"有什么感受"）
- `suitable_for[]` / `not_suitable_for[]`：实际临床适应症描述，不泛化
- `purpose`：一句话说明练习的**行为机制**，不说效果承诺

**允许修改**：`content/training_cards.json`。**严禁**：修改卡的 id（已被 `assessment_training_map` 和 `diary_training_map` 引用的旧卡 id）；删除现有卡（只能新增或原地升级文字）。

**完成标准**：20 张卡内容通过 `validate_content.py`；FORBIDDEN_TERMS 无命中；每张卡 steps≥3、example 非空、reflection_questions≥2。

---

### T5-02 推荐算法断链修复（维度分评估引擎）

**背景**：`assessment_training_map.json` 规则有 `trigger_condition.dimension` + `trigger_condition.level`（如 PRFQ_IC "needs_support"），但 `_training_rules_for_worksheet()`（assessments.py:146-159）只按 `worksheet_id/scale_id` 过滤，从不评估维度分。用户填完量表后，规则返回给前端但**从不选择卡**。

**改动**：

**1. 阈值评估逻辑** — 新增 `backend/services/training_recommendation_service.py`：
```python
def evaluate_training_rules(worksheet_id: str, scores_json: str) -> list[dict]:
    """
    从 assessment_training_map.json 中选出满足维度条件的规则。
    阈值策略（按优先级）：
    1. 有对应 content/profiles/ 模型 → 用 feature.mean 作基准，z < -0.5 → "needs_support"
    2. 无模型 → 用量表 score_min/score_max 中点，低于中点 → "needs_support"，高于 → "high"
    """
    rules = _load_all_rules()  # 读 assessment_training_map.json
    scores = json_loads(scores_json, {})
    dim_map = {d["key"]: d["score"] for d in scores.get("dimensions", [])}
    model = _find_profile_model(worksheet_id)  # 从 content/profiles/ 找同 worksheet_id 的模型
    result = []
    for rule in rules:
        if not _matches_worksheet(rule, worksheet_id):
            continue
        if _evaluate_condition(rule["trigger_condition"], dim_map, model):
            result.append(rule)
    return result

def _evaluate_condition(condition, dim_map, model) -> bool:
    dimension = condition.get("dimension")
    level = condition.get("level")
    if not dimension:          # 无维度条件 → 直接匹配
        return True
    score = dim_map.get(dimension)
    if score is None:
        return False
    threshold = _get_threshold(dimension, model)  # 返回 {"support_below": x, "high_above": y}
    return _check_level(level, score, threshold)
```

**2. 接入 create_assessment_result** — 在 `routes/assessments.py` 的 `create_assessment_result` 末尾（写 DB 后）：
```python
from services.training_recommendation_service import evaluate_training_rules
training_rules = evaluate_training_rules(worksheet["id"], json_dumps(scores))
result["training_recommendation_rules"] = training_rules
result["recommended_card_ids"] = _flatten_card_ids(training_rules) or result.get("recommended_card_ids", [])
```

**3. 升级 card_service.py `recommend_cards` fallback** — 无 tag 匹配时改为按类型多样化采样（每种 type 取1张）而非顺序前 N：
```python
if not matched:
    types = {}
    for card in cards:
        types.setdefault(card.get("type", ""), []).append(card)
    return [cards[0] for cards in types.values()][:limit]
```

**4. 更新 assessment_training_map.json** — 为 PRFQ 三个维度（PM/CM/IC）、ERQ 两个维度（CR/ES）、RSCA、SCS 各补充规则，覆盖 `needs_support`/`high` 两种触发条件，每条规则 `recommended_card_ids` 指向 T5-01 新卡。

**必须新增测试** `backend/tests/test_training_recommendation.py`：PRFQ 低 IC 分 → 触发 `prfq_ic_curiosity` 等卡；无维度条件规则直接命中；无模型量表用中点阈值；高风险 → 空列表。

**允许修改**：`backend/services/training_recommendation_service.py`（新增）、`backend/routes/assessments.py`、`backend/services/card_service.py`、`content/assessment_training_map.json`、`backend/tests/**`。

**完成标准**：填完 PRFQ 后 API 返回 `recommended_card_ids` 非空且与维度分对应；pytest 通过。

---

### T5-03 日记→训练卡规则补全

**背景**：`diary_training_map.json` 现有 4 条规则（对应 4 个 feedback_rule_id）；`feedback_rules.json` 中可能有更多规则 id 未覆盖；`_match_diary_training_rules()` 硬限 `[:1]`。

**改动**：
- 检查 `content/feedback_rules.json` 所有 rule id，为未覆盖的补充 `diary_training_map.json` 规则（指向 T5-01 新卡）
- 将 `_match_diary_training_rules()` 的 `[:1]` 改为返回最多 2 条（今日练习 + 备用），前端只展示第一条，第二条作为"还可以做"备选
- 规则补全优先：高强度情绪、自责/自我批评、关系冲突三类场景各至少1条新规则

**允许修改**：`content/diary_training_map.json`、`backend/routes/feedback.py`（`[:1]`→`[:2]`）。**完成标准**：`feedback_rules.json` 中每个 rule id 至少有一条对应日记训练规则；validate_content.py 通过。

---

### T5-04 画像簇→训练卡映射建议

**背景**：`content/profiles/*.json` 每个簇有 `objective_desc`/`support_advice`/`dimension_means`，但无 `recommended_card_ids`。算法用 C 方案：基于簇特征自动建议映射，用户审核。

**改动**：

**1. 生成建议** — 新增 `analysis/profiling/suggest_cluster_card_map.py`（离线脚本）：
读每个 profile JSON → 对每个簇：检查 `dimension_means` 中最低的2-3个维度 → 在 `training_cards.json` 中找 `target_skill` 最匹配的卡 → 输出建议映射到 `docs/10Claude协作/画像簇训练卡映射建议.md`（供人工审核）。

**2. 审核后落地** — 人工审核建议映射 → 修改对应 `content/profiles/*.json`，为每个 `clusters[i]` 加：
```json
"recommended_card_ids": ["card_id_1", "card_id_2"],
"card_reason": "PM 维度偏低，优先识别自动反应"
```

**3. 接入落点接口** — `assessment_profile_service.py` 的 `build_assessment_profile_position` 返回值中，在 `clusters[i]` 里透传 `recommended_card_ids`；前端结果页可直接展示"与你最近的群体通常练习的卡"。

**允许修改**：`analysis/profiling/suggest_cluster_card_map.py`（新增）、`content/profiles/**`（人工审核后）、`backend/services/assessment_profile_service.py`。**完成标准**：PRFQ 每个簇有 `recommended_card_ids`；接口返回中含簇推荐卡；建议文档已产出供审核。

---

### T5-05 代码逻辑缺陷修复清单

**已知问题与修复方案**：

| 文件 | 问题 | 修复 |
|---|---|---|
| `task-detail/index.js` | 硬编码 `TASKS` 字典（10个任务）与 API 卡数据完全独立，新增卡永远 fallback 到 `nonjudgmental_company`，**这是最高优先级 bug** | 当前保留不改（T3 视觉重构时彻底重构），**在文件顶部加注释标记 `// TODO T3: REFACTOR - hardcoded, disconnect from API`** |
| `training-card/index.js:36` | `cardIds.length > 0` 时调 `api.listCards()` 拉全量再过滤，浪费 | 改为直接用传入的 cardIds 匹配已获取到的卡列表；或新增 `GET /api/cards/:id` 端点 |
| `training-card/index.js:formatCard` | `todayGoal`/`reflectionPrompt` 是固定字符串，与卡无关 | 改为读卡的 `reflection_questions[0]` 和 `suitable_for[0]`；字段不存在时才用默认值 |
| `feedback-result/index.js:buildEmotionOverview` | 情绪词硬编码（`"着急 / 生气 / 委屈"`），与实际 tag 无关 | 改为用 `feedback.labels` 数组直接组合；无 labels 时显示触发摘要 |
| `card_service.py:recommend_cards` | 无匹配时按顺序返回前N（T5-02 已修） | 见 T5-02 |
| `feedback.py:_match_diary_training_rules` | `[:1]` 限制最多1条规则 | 见 T5-03 |

**允许修改**：`apps/miniprogram/pages/training-card/index.js`、`apps/miniprogram/pages/feedback-result/index.js`、`apps/miniprogram/pages/task-detail/index.js`（只加注释）、`backend/services/card_service.py`。

**完成标准**：小程序 JS/JSON 检查通过；`training-card` 页的 `todayGoal` 随卡变化；`buildEmotionOverview` 不再硬编码情绪词。

---

### T5-06 任务五验收
```text
内容    ：validate_content.py 通过；20 张卡 steps≥3、example 非空；FORBIDDEN_TERMS 无命中
算法    ：填完 PRFQ（IC 维度低分）→ API 返回对应卡 ID → pytest test_training_recommendation 通过
日记链路：日记提交 → feedback-result 显示训练卡推荐 → 最多2条规则可见
画像映射：PRFQ 各簇有 recommended_card_ids；建议文档已产出
代码修复：小程序 JS/JSON 检查通过；todayGoal/emotionOverview 不再使用硬编码字符串
task-detail bug：文件顶部已加 TODO 注释，等待 T3 重构
```

# 任务六：前端改造（小程序端）

> 创建时间：2026-06-30
> 负责人：Claude（方向把握+技术安排）+ Codex（技术实现）
> 改造范围：`apps/miniprogram/pages/*`（暂不动 `apps/web/*`）

---

## ⚠️ 执行前必读 · 全章订正总表（Claude 核实修订 2026-07-01）

> 本任务六初稿大量"原代码"标注了"(推测)"，经逐文件核实，部分行号/字段名/API 名/"已完成代码"与真实代码**不符甚至虚构**。Codex 执行时**以下表与各节内的【Claude订正】块为准**，原文保留仅作对照。**凡与本表冲突，一律以本表为准。**

### A. 全局 API 方法名（最高频错误，按计划调用一律 `TypeError`）

| 计划写的（错） | 真实方法（`apps/miniprogram/services/api.js`） | 返回 |
|---|---|---|
| `api.getAssessments()` | `api.listAssessments(params)`（:360） | `{ worksheets / items }` |
| `api.getDiaries(params)` | `api.listDiaries(params)`（:277） | `{ items: [...] }`（非裸数组） |
| `api.getTrainingCards()` | `api.listCards()`（:347）/ `api.recommendCards(params)`（:351） | `{ cards }` / 推荐卡 |
| `api.getWeeklyReport()` | ✅ 存在（:394），此名正确 | 周报对象 |

### B. 后端约定（T6-01 等）

| 主题 | 计划写的（错） | 真实约定 |
|---|---|---|
| 建表容器 | `SCHEMA` 列表 | **`SCHEMA_SQL`**（`models.py:28`）；索引加 `INDEX_SQL`（:399） |
| 按天统计 SQL | `WHERE DATE(created_at)=DATE('now')` | **禁用**。MySQL 下 `DATE('now')` 解析为 NULL→统计恒为 0。统一用 `substr(created_at,1,10)=?`，日期串在 **Python 端**用 `date.today().isoformat()` 算好再传参（见 `report_service.py:26`） |
| `parse_int` | `parse_int(x, default=20, min_val=1, max_val=100)` | **只有 `default` 参数**，无 min/max → 写了会 `TypeError`。范围校验自己写 `if`（`routes/utils.py:70`） |
| 工具签名 | — | `fail(code, message, status=400)`、`ensure_user(conn, user_id, nickname=None)`、`new_id(prefix)` 必传 prefix；蓝图变量名统一 `bp`，`app.py` 用 `from routes.X import bp as X_bp` |

### C. 周报字段（T6-04/T6-05）

- 周报对象**没有** `diaries_count / emotions_count / checkins_count / profiles_count`（计划所谓"原代码用这些"是**虚构**）。
- 真实字段（`report_service.py:85-101`）：`frequent_scenes`、`frequent_emotions`、`common_patterns` 均为 **`[[名称, 次数], ...]` 元组列表**（不是纯字符串数组）；`completed_cards` 是字符串数组；`profile_trend.profile_count`；`next_week_suggestion`。
- `profile_trend` **不落库**（`weekly_reports` 表无此列），只在 HTTP 响应透出。
- 前端 `weekly-report/index.js` 已有 `formatPairs([[名,次]])→{name,count}`，4 格已正确绑 `frequentScenes.length` 等——**不要按"原代码 diaries_count"去改**。

### D. 训练卡（T6-06）

- 实际 **34 张**（全 enabled）。文档里"20 张/12 张"作废，统一 **34**。
- 字段名：计划的 `theory_background`→真实 **`theory_source`**；`target_competency`→真实 **`target_skill`**；`practice_tips` **不存在**（最近似 `reflection_questions`）。**改文案时复用现有字段名，不要新造同义字段并存。**
- 硬约束（`validate_content.py` + `schemas/training_cards.schema.json`）：`theory_source`/`target_skill`/`reflection_questions`/`not_suitable_for` 为 required，**不可删**；`reflection_questions` ≥2 条；每卡 `not_suitable_for` 必须含"高风险/危机/安全/现实支持"之一。好消息：脚本不拦额外字段，"前额叶/杏仁核/认知加工"等不在禁用词（禁用词仅 8 个）。

### E. 量表 worksheet（T6-02）

- **无任何 demo 量表**（数据全走 `api.listAssessments()`）→ 计划"删除所有 demo 量表"**无对象可删**，该子目标取消。
- 启用数核对无误：**16 个（学生5 / 家长1 / 成人10）**。
- `audience_class` 真实取值 **`student / parent / adult`**（英文）；标题字段是 **`display_title`**（非 `title`）。
- **分组维度（用户决策 2026-07-01）：保留现有"Tab=人群 + section=反射弧节点(`reflex_node`)"双层结构**，**不改为按 audience 分组**（否则与 Tab 重复且丢节点维度）。T6-02 只做：修选项截断 bug + 接真实搜索/分类，不动分组维度。
- 真实函数名：`refreshVisibleAssessments`（非 applyFilters）、`buildAssessmentSections`（非 buildCategorySections）。

### F. 方法名 / 其它（T6-04）

- home 页统计方法是 **`refreshTodayRecordCount`**（非 `loadTodayRecordCount`）。
- `created_at` 是 **UTC**（`now_iso()`）；前端 `new Date(created_at)` 按本地时区解析，"今天/昨天"判断会偏移——T6-04 时间格式化需按 UTC 处理或后端返回本地化字段。
- 字段名 `scene / event_description / parent_emotion` 前后端一致（✅）；`feedback-result` 接收 `diary_id`（✅）。

### G. T6-08 全节为"从零实现"（不是对接已有）

> T6-08 声称"Claude 已提供/已完成"的 **后端 7 项 + 前端 4 页面 + home 消息入口 + profile 改造，经核实全部不存在**（`messages` 表/路由、`/api/auth/wechat-login`、`/api/profile/stats`、`calculate_consecutive_days`、`users.wechat_openid/avatar_url`、supervision 回复建消息、`pages/messages|message-detail|emergency-guide|emergency-resources/`、`loadUnreadCount/openMessages` 均无）。**整节按"从零新建"执行，详见 T6-08 节内【Claude订正】重写规格。**

### 各节状态速览

| 节 | 状态 | 关键动作 |
|---|---|---|
| T6-01 | 方向OK，3处技术坑 | 见节内订正：SCHEMA_SQL / 日期SQL / parse_int |
| T6-02 | 部分订正 | 保留节点分组；删"删demo"；选项截断改 `keep-all`；API/函数名 |
| T6-03 | ✅ 行号精确，可照做 | 无需订正 |
| T6-04 | 部分订正 | `listDiaries` / `refreshTodayRecordCount` / UTC时区 |
| T6-05 | 部分订正 | 删虚构 `diaries_count` 叙述；对齐元组字段 |
| T6-06 | 多处订正 | `theory_source`/`target_skill`；34张；`listCards/recommendCards`；required不可删 |
| T6-07 | 保留GitHub+补防护 | 微信合法域名 + 版权/内容审核/伦理免责 |
| T6-08 | 整节重写 | 从零实现规格 |

---

## T6-01：情绪温度计功能开发（后端+前端）

### 一、任务目标

将首页"情绪天气"功能改造为"情绪温度计"功能，支持用户快速记录即时情绪波动和简短事件。

**核心变更：**
1. 首页卡片文案：`情绪天气` → `情绪温度计`，`今天已记录 X 次` → `即时情绪记录`
2. 新增独立的情绪温度计记录页面（非情绪日记）
3. 新增后端 API 和数据表支持温度计记录

---

### 二、后端代码审核结论

**现有相关代码：**
- `backend/models.py:90-107` - `emotion_diaries` 表（详细日记）
- `backend/routes/diaries.py` - 日记 CRUD 接口
- `backend/database.py:413` - `ensure_column` 动态加列
- `shared/types/api.ts` - 前后端类型定义
- `shared/constants/api.ts:1-41` - API 端点常量

**审核结论：**
- ✅ 数据库设计：新建独立表 `emotion_thermometer`（不与日记混用）
- ✅ API 设计：新建 `/api/emotion-thermometer` 端点
- ✅ 类型定义：需在 `shared/types/api.ts` 新增接口
- ✅ 常量定义：需在 `shared/constants/api.ts` 新增端点
- ✅ 风险等级：仅 low/medium/high 三级（无 critical）

---

### 三、详细实现方案

#### 3.1 后端实现

##### 3.1.1 数据库表设计

**文件：`backend/models.py`**

在 `SCHEMA` 列表末尾（约第 600 行附近）追加：

> **【Claude订正】** 真实变量名是 **`SCHEMA_SQL`**（`backend/models.py:28`，一个 list，元素为 CREATE TABLE 字符串），不是 `SCHEMA`。请追加到 `SCHEMA_SQL`。`init_db()`（`database.py:270`）遍历 `SCHEMA_SQL` 建表，幂等。本表无强索引需求；如需按 `user_id` 查询加速，把 `CREATE INDEX ...` 追加进 `INDEX_SQL`（`models.py:399`）。`emotion_thermometer` 经核实为全新表（content/schema/代码层均无既有定义）。

```python
"""
CREATE TABLE IF NOT EXISTS emotion_thermometer (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    intensity_level INTEGER NOT NULL,
    brief_text TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""",
```

**字段说明：**
- `id`: 主键，格式 `thermo_<uuid>`
- `user_id`: 用户ID
- `intensity_level`: 情绪波动强度，1-10（1-3=低波动，4-7=中等波动，8-10=高波动）
- `brief_text`: 一句话内容（事件+感受+想法）
- `created_at`: 创建时间（ISO 8601格式）

##### 3.1.2 API 路由实现

**新建文件：`backend/routes/emotion_thermometer.py`**

```python
"""Emotion thermometer endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import (
    fail,
    ok,
    parse_int,
    require_fields,
    require_user_id,
)

bp = Blueprint("emotion_thermometer", __name__, url_prefix="/api/emotion-thermometer")


@bp.post("")
def create_thermometer_record():
    """创建情绪温度计记录"""
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["intensity_level", "brief_text"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    intensity_level = payload.get("intensity_level")
    brief_text = payload.get("brief_text", "").strip()

    # 验证 intensity_level 范围
    if not isinstance(intensity_level, int) or not (1 <= intensity_level <= 10):
        return fail("validation_error", "intensity_level 必须是 1-10 之间的整数")

    # 验证 brief_text 长度
    if not brief_text:
        return fail("validation_error", "brief_text 不能为空")
    if len(brief_text) > 500:
        return fail("validation_error", "brief_text 不能超过 500 字符")

    timestamp = now_iso()
    record_id = new_id("thermo")

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO emotion_thermometer (
                id, user_id, intensity_level, brief_text, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (record_id, user_id, intensity_level, brief_text, timestamp),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM emotion_thermometer WHERE id = ?", (record_id,)
        ).fetchone()

    return ok(row_to_dict(row))


@bp.get("")
def list_thermometer_records():
    """获取情绪温度计记录列表"""
    user_id = request.args.get("user_id", "demo-parent")
    limit = parse_int(request.args.get("limit"), default=20, min_val=1, max_val=100)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM emotion_thermometer
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        # 统计今日记录数
        today_count_row = conn.execute(
            """
            SELECT COUNT(*) as count FROM emotion_thermometer
            WHERE user_id = ? AND DATE(created_at) = DATE('now')
            """,
            (user_id,),
        ).fetchone()

    today_count = today_count_row["count"] if today_count_row else 0

    return ok({"items": rows_to_dicts(rows), "total": len(rows), "today_count": today_count})
```

> **【Claude订正 · 上方 `list_thermometer_records` 有两处会出错，必改】**
>
> **(1) `parse_int` 没有 `min_val`/`max_val` 参数**（`routes/utils.py:70` 只有 `default`）。写 `parse_int(..., min_val=1, max_val=100)` 会 `TypeError`。改为：
> ```python
> limit = parse_int(request.args.get("limit"), default=20)
> limit = max(1, min(limit or 20, 100))  # 范围裁剪手动写
> ```
>
> **(2) 禁用 `DATE(created_at) = DATE('now')`** —— 这是双后端兼容坑：MySQL 把字符串 `'now'` 当日期解析得 `NULL`，`WHERE ... = NULL` 恒为假，`today_count` 在 MySQL 永远是 0（仅 SQLite 正常）；方言层 `_mysqlize_query` 只换占位符/引号，不会翻译该函数。改用项目唯一约定（Python 端算日期串 + `substr`，见 `report_service.py:26`）：
> ```python
> from datetime import date
> today_str = date.today().isoformat()  # 'YYYY-MM-DD'
> today_count_row = conn.execute(
>     "SELECT COUNT(*) AS count FROM emotion_thermometer "
>     "WHERE user_id = ? AND substr(created_at, 1, 10) = ?",
>     (user_id, today_str),
> ).fetchone()
> ```
> 注：`created_at` 由 `now_iso()` 写为 **UTC** ISO，`substr(...,1,10)` 取日期前缀，两后端一致。本期按 UTC 自然日统计；若要严格"用户本地自然日"需另定时区策略（与 T6-04 时间显示同源问题）。
>
> **(3) import 与蓝图写法（3.1.2/3.1.3）经核实正确**：`from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts` 与 `from routes.utils import fail, ok, parse_int, require_fields, require_user_id` 均可用；蓝图变量名 `bp`、`app.py` 用 `from routes.emotion_thermometer import bp as emotion_thermometer_bp` + `app.register_blueprint(...)` 均符合现有约定，照做即可。

##### 3.1.3 注册蓝图

**文件：`backend/app.py`**

在文件顶部导入区（约第 18 行附近）添加：

```python
from routes.emotion_thermometer import bp as emotion_thermometer_bp
```

在蓝图注册区（约第 75 行附近）添加：

```python
app.register_blueprint(emotion_thermometer_bp)
```

##### 3.1.4 类型定义（shared）

**文件：`shared/types/api.ts`**

在文件末尾（约第 400 行附近）添加：

```typescript
export interface EmotionThermometerRecord {
  id: ID;
  user_id: ID;
  intensity_level: number; // 1-10
  brief_text: string;
  created_at: ISODateTime;
}

export interface EmotionThermometerInput {
  user_id?: ID;
  nickname?: string;
  intensity_level: number;
  brief_text: string;
}

export interface EmotionThermometerListResponse {
  items: EmotionThermometerRecord[];
  total: number;
  today_count: number;
}
```

##### 3.1.5 API 常量定义

**文件：`shared/constants/api.ts`**

在 `API_ENDPOINTS` 对象中（约第 40 行附近）添加：

```typescript
emotionThermometer: "/api/emotion-thermometer",
```

#### 3.2 前端实现

##### 3.2.1 小程序 API 服务

**文件：`apps/miniprogram/services/api.js`**

在 `API_ENDPOINTS` 对象中（约第 27 行附近）添加：

```javascript
emotionThermometer: "/api/emotion-thermometer",
```

在文件末尾（约第 200 行附近）的 `return` 对象中添加：

```javascript
// 情绪温度计
createThermometerRecord(input) {
  return request("POST", API_ENDPOINTS.emotionThermometer, input);
},
getThermometerRecords(params = {}) {
  return request("GET", API_ENDPOINTS.emotionThermometer + queryString(params));
},
```

##### 3.2.2 首页卡片改造

**文件：`apps/miniprogram/pages/home/index.wxml`**

**修改位置：第 14-22 行**

**原代码：**
```xml
<!-- 情绪天气：紧凑横条 -->
<button class="mood-strip" bindtap="startDiary">
  <view class="mood-strip-left">
    <text class="mood-strip-label">情绪天气</text>
    <text class="mood-strip-sub">今天已记录 {{todayRecordCount}} 次{{todayRecordCountReady ? '' : '，联网后更新'}}</text>
  </view>
  <text class="mood-strip-face">☺</text>
  <text class="mood-strip-action">记录 ›</text>
</button>
```

**修改为：**
```xml
<!-- 情绪温度计：紧凑横条 -->
<button class="mood-strip" bindtap="startThermometer">
  <view class="mood-strip-left">
    <text class="mood-strip-label">情绪温度计</text>
    <text class="mood-strip-sub">即时情绪记录</text>
  </view>
  <text class="mood-strip-face">🌡</text>
  <text class="mood-strip-action">记录 ›</text>
</button>
```

**文件：`apps/miniprogram/pages/home/index.js`**

**修改位置：约第 110 行附近**

**原方法：**
```javascript
startDiary() {
  wx.navigateTo({ url: "/pages/diary-form/index" });
},
```

**修改为：**
```javascript
startThermometer() {
  wx.navigateTo({ url: "/pages/thermometer/index" });
},
```

同时保留原有的 `startDiary` 方法（用于其他入口）。

删除 `todayRecordCount` 和 `todayRecordCountReady` 相关逻辑：
- 删除 `data` 中的这两个字段（第 26-27 行）
- 删除 `onShow` 中的 `loadTodayRecordCount` 调用（第 117 行附近）
- 删除 `loadTodayRecordCount` 方法（第 120-145 行附近）

##### 3.2.3 新建情绪温度计页面

**新建目录：`apps/miniprogram/pages/thermometer/`**

**新建文件：`apps/miniprogram/pages/thermometer/index.wxml`**

```xml
<view class="safe-page thermometer-page">
  
  <!-- 页面标题 -->
  <view class="safe-section">
    <text class="safe-h1">情绪温度计</text>
    <text class="safe-caption">记录此刻的情绪波动</text>
  </view>

  <!-- 温度计标尺 -->
  <view class="safe-section">
    <text class="thermometer-label">当前情绪波动程度</text>
    <view class="thermometer-scale">
      <view class="thermometer-bar">
        <view class="thermometer-fill" style="height: {{intensity * 10}}%;"></view>
      </view>
      <view class="thermometer-marks">
        <text class="thermometer-mark" wx:for="{{[10,9,8,7,6,5,4,3,2,1]}}" wx:key="*this">{{item}}</text>
      </view>
    </view>
    <slider 
      class="thermometer-slider" 
      min="1" 
      max="10" 
      step="1" 
      value="{{intensity}}" 
      bindchange="onIntensityChange" 
      activeColor="var(--safe-primary)"
      backgroundColor="var(--safe-border)"
    />
    <view class="thermometer-level-hint">
      <text class="safe-caption">{{intensityHint}}</text>
    </view>
  </view>

  <!-- 一句话输入 -->
  <view class="safe-section">
    <text class="thermometer-label">刚才发生了什么？</text>
    <textarea 
      class="thermometer-textarea" 
      placeholder="用一句话记录：发生的事件、你的感受和想法"
      maxlength="500"
      value="{{briefText}}"
      bindinput="onBriefTextInput"
      auto-height
    />
    <text class="safe-caption">{{briefText.length}}/500</text>
  </view>

  <!-- 提交按钮 -->
  <view class="safe-section">
    <button 
      class="safe-primary-button" 
      bindtap="submitRecord"
      disabled="{{!canSubmit}}"
    >
      保存记录
    </button>
  </view>

  <!-- 非诊断边界说明 -->
  <view class="safe-section">
    <view class="alert-card alert-card--info">
      <text class="safe-caption">本功能仅用于自我觉察和情绪记录，不构成诊断或评估。</text>
    </view>
  </view>

</view>
```

**新建文件：`apps/miniprogram/pages/thermometer/index.js`**

```javascript
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

const INTENSITY_HINTS = {
  1: "很平静",
  2: "略有波动",
  3: "轻微波动",
  4: "有些波动",
  5: "中等波动",
  6: "明显波动",
  7: "较强波动",
  8: "强烈波动",
  9: "非常强烈",
  10: "极度波动",
};

Page({
  data: {
    intensity: 5,
    intensityHint: "中等波动",
    briefText: "",
    canSubmit: false,
  },

  onLoad() {
    this.updateIntensityHint();
  },

  onIntensityChange(e) {
    const intensity = parseInt(e.detail.value, 10);
    this.setData({ intensity }, () => {
      this.updateIntensityHint();
      this.checkCanSubmit();
    });
  },

  onBriefTextInput(e) {
    this.setData({ briefText: e.detail.value }, () => {
      this.checkCanSubmit();
    });
  },

  updateIntensityHint() {
    const hint = INTENSITY_HINTS[this.data.intensity] || "中等波动";
    this.setData({ intensityHint: hint });
  },

  checkCanSubmit() {
    const canSubmit = this.data.briefText.trim().length > 0;
    this.setData({ canSubmit });
  },

  async submitRecord() {
    if (!this.data.canSubmit) {
      return;
    }

    wx.showLoading({ title: "保存中..." });

    try {
      const result = await api.createThermometerRecord({
        intensity_level: this.data.intensity,
        brief_text: this.data.briefText.trim(),
      });

      wx.hideLoading();

      if (result.ok) {
        wx.showToast({
          title: "记录成功",
          icon: "success",
          duration: 2000,
        });

        setTimeout(() => {
          wx.navigateBack();
        }, 2000);
      } else {
        wx.showToast({
          title: result.error?.message || "保存失败",
          icon: "none",
          duration: 3000,
        });
      }
    } catch (err) {
      wx.hideLoading();
      wx.showToast({
        title: "网络错误，请重试",
        icon: "none",
        duration: 3000,
      });
      console.error("submitRecord error:", err);
    }
  },
});
```

**新建文件：`apps/miniprogram/pages/thermometer/index.wxss`**

```css
.thermometer-page {
  padding-bottom: 120rpx;
}

.thermometer-label {
  display: block;
  color: var(--safe-title);
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 24rpx;
}

.thermometer-scale {
  display: flex;
  align-items: stretch;
  gap: 24rpx;
  margin-bottom: 32rpx;
}

.thermometer-bar {
  width: 80rpx;
  height: 600rpx;
  background: var(--safe-bg-soft);
  border: 2rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  position: relative;
  overflow: hidden;
}

.thermometer-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, var(--safe-primary), var(--safe-primary-soft));
  transition: height 0.3s ease;
}

.thermometer-marks {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12rpx 0;
}

.thermometer-mark {
  display: block;
  color: var(--safe-muted);
  font-size: 24rpx;
  line-height: 1;
}

.thermometer-slider {
  width: 100%;
  margin-bottom: 16rpx;
}

.thermometer-level-hint {
  text-align: center;
  padding: 16rpx;
  background: var(--safe-primary-pale);
  border-radius: var(--safe-radius-sm);
}

.thermometer-textarea {
  width: 100%;
  min-height: 200rpx;
  padding: 24rpx;
  background: var(--safe-card);
  border: 2rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  font-size: 28rpx;
  line-height: 1.6;
  color: var(--safe-text);
  margin-bottom: 16rpx;
}
```

**新建文件：`apps/miniprogram/pages/thermometer/index.json`**

```json
{
  "navigationBarTitleText": "情绪温度计",
  "usingComponents": {
    "section-title": "/components/section-title/index",
    "alert-card": "/components/alert-card/index"
  }
}
```

##### 3.2.4 注册页面路由

**文件：`apps/miniprogram/app.json`**

在 `pages` 数组中（约第 12 行附近）添加：

```json
"pages/thermometer/index",
```

---

### 四、验收标准

#### 4.1 后端验收

**运行测试：**
```bash
cd D:\codex\workspace\safehome1.0\backend
python -m pytest tests -q
```

**手动测试 API：**

1. **创建记录：**
```bash
curl -X POST http://127.0.0.1:5000/api/emotion-thermometer \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-parent",
    "intensity_level": 7,
    "brief_text": "孩子写作业磨蹭，我有点着急"
  }'
```

预期响应：
```json
{
  "ok": true,
  "data": {
    "id": "thermo_xxx",
    "user_id": "demo-parent",
    "intensity_level": 7,
    "brief_text": "孩子写作业磨蹭，我有点着急",
    "created_at": "2026-06-30T..."
  }
}
```

2. **获取列表：**
```bash
curl http://127.0.0.1:5000/api/emotion-thermometer?user_id=demo-parent
```

预期响应：
```json
{
  "ok": true,
  "data": {
    "items": [...],
    "total": 1,
    "today_count": 1
  }
}
```

#### 4.2 前端验收

**在微信开发者工具中测试：**

1. 启动小程序，进入首页
2. 确认首页卡片显示"情绪温度计"+"即时情绪记录"
3. 点击卡片，跳转到情绪温度计页面
4. 拖动滑块，确认：
   - 温度计填充高度变化
   - 底部提示文案跟随变化（1=很平静，10=极度波动）
5. 输入一句话内容（至少1个字符）
6. 确认"保存记录"按钮可点击
7. 点击提交，确认：
   - 显示"保存中..."加载提示
   - 成功后显示"记录成功"
   - 2秒后自动返回首页
8. 返回首页，再次点击"情绪温度计"，确认能再次记录

#### 4.3 边界验收

**必须符合：**
- ✅ 非诊断文案：页面底部显示"不构成诊断或评估"
- ✅ API 不变：不破坏现有 `/api/diaries` 接口
- ✅ 核心链路：情绪日记功能保持可用
- ✅ 风险等级：无风险判断逻辑（温度计纯记录功能）
- ✅ 代码检查：小程序 JS/JSON 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

---

### 五、完成后更新文档

**1. 更新 API 文档：**
文件：`docs/03_技术真相/API接口文档.md`

在"已实现接口"章节末尾添加：

```markdown
### POST /api/emotion-thermometer
创建情绪温度计记录。

Request:
{
  "user_id": "demo-parent",
  "intensity_level": 7,
  "brief_text": "孩子写作业磨蹭，我有点着急"
}

Response:
{
  "ok": true,
  "data": {
    "id": "thermo_xxx",
    "user_id": "demo-parent",
    "intensity_level": 7,
    "brief_text": "...",
    "created_at": "2026-06-30T..."
  }
}

### GET /api/emotion-thermometer
获取情绪温度计记录列表。

Query: ?user_id=demo-parent&limit=20

Response:
{
  "ok": true,
  "data": {
    "items": [...],
    "total": 5,
    "today_count": 2
  }
}
```

**2. 更新数据库文档：**
文件：`docs/03_技术真相/数据库字段说明.md`

在表清单中添加：

```markdown
### emotion_thermometer（情绪温度计记录）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT | 主键，格式 thermo_<uuid> |
| user_id | TEXT | 用户ID |
| intensity_level | INTEGER | 情绪波动强度 1-10 |
| brief_text | TEXT | 一句话内容 |
| created_at | TEXT | 创建时间 ISO 8601 |
```

**3. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 新增情绪温度计功能（T6-01）
  - 后端：新增 `/api/emotion-thermometer` 接口和 `emotion_thermometer` 表
  - 前端：首页"情绪天气"改为"情绪温度计"，新增 `/pages/thermometer` 记录页
  - 设计：1-10 档标尺，一句话快速记录
```

**4. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-01 情绪温度计功能开发
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：情绪温度计后端API + 小程序页面 + 首页入口改造
- 关键决策：独立表设计，1-10档标尺，与情绪日记功能解耦
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的设计图片（如有）
- [ ] 3. 在 `backend/models.py` 添加 `emotion_thermometer` 表定义
- [ ] 4. 创建 `backend/routes/emotion_thermometer.py` 文件
- [ ] 5. 在 `backend/app.py` 注册蓝图
- [ ] 6. 在 `shared/types/api.ts` 添加类型定义
- [ ] 7. 在 `shared/constants/api.ts` 添加端点常量
- [ ] 8. 在 `apps/miniprogram/services/api.js` 添加 API 方法
- [ ] 9. 修改 `apps/miniprogram/pages/home/index.wxml` 卡片文案
- [ ] 10. 修改 `apps/miniprogram/pages/home/index.js` 事件处理
- [ ] 11. 创建 `apps/miniprogram/pages/thermometer/` 目录及 4 个文件
- [ ] 12. 在 `apps/miniprogram/app.json` 注册页面路由
- [ ] 13. 启动后端，测试 API（curl 或 Postman）
- [ ] 14. 在微信开发者工具中测试小程序页面
- [ ] 15. 运行代码检查命令（JS/JSON 语法）
- [ ] 16. 更新 4 个文档（API、数据库、开发日志、Claude记录）
- [ ] 17. 截图验收结果，提交给用户确认

---

### 七、注意事项

1. **不要删除情绪日记功能**：温度计和日记是独立功能，保留所有日记相关代码
2. **参考设计 skills**：Codex 在实现时优先调用 `C:\Users\32257\.codex\skills\frontend-design` 等本地 skills
3. **遵守伦理边界**：页面必须显示"不构成诊断"等非诊断文案
4. **代码风格**：保持与现有代码一致（缩进、命名、注释）
5. **错误处理**：API 调用失败时显示友好提示，不暴露技术细节

---

**任务状态：** 待执行
**预计工时：** 2-3 小时（后端1h + 前端1.5h + 测试0.5h）
**优先级：** P0（首页核心功能改造）

---

## T6-02：测一测页面改造（量表列表+搜索+学生画像详情修复）

### 一、任务目标

改造"测一测"页面，实现：
1. **删除所有 demo 测试量表**，只展示后端已启用的正式量表
2. **修复学生支持性画像测评详情页**选项显示不完整问题
3. **实现搜索功能**：支持标题和关键词搜索
4. **分类展示**：按"学生自助/家长自助/成人自助"正确分类

**核心变更：**
- 前端不再使用硬编码的 demo 量表数据
- 从后端 API `/api/assessments` 动态获取启用量表
- 修复选项按钮样式的文字断行问题
- 实现分类和搜索的正确逻辑

---

### 二、后端代码审核结论

**现有后端代码：**
- `backend/routes/assessments.py` - 量表 API 路由
- `content/assessment_worksheets.json` - 量表数据源（27个量表）
- API `/api/assessments` 返回所有 `enabled_for_user=True` 的量表

**审核结论：**
- ✅ 后端数据完整：27个量表，16个已启用
- ✅ 后端 API 正常：返回正确的量表列表
- ✅ 数据编码正确：UTF-8 格式，中文显示正常
- ✅ 分类字段存在：`audience_class` 字段（student/parent/adult）
- ✅ 搜索字段存在：`search_keywords` 数组字段

**启用量表统计：**
- 学生自助（student）：5个量表
- 家长自助（parent）：1个量表
- 成人自助（adult）：10个量表
- 总计：16个启用量表

> **【Claude订正】** 启用数核对**无误**（27 个 worksheet，启用 16 = 学生5/家长1/成人10）。但 **`content/assessment_worksheets.json` 里没有任何 demo/示例量表**（无"工作表1.1"之类），数据全部经 `api.listAssessments()` 取得——**故本任务"删除所有 demo 测试量表"无对象可删，该子目标取消**，前端也无硬编码量表数组。`audience_class` 真实取值是英文 `student/parent/adult`；标题字段是 `display_title`（不是 `title`，`title` 为空）。

**问题诊断：**
- 前端选项显示问题：`.option-button` 样式中 `word-break: break-all` 导致中文被强制断开
- 示例："1 很少" 被断成 "1 很 少"，导致显示为乱码形式

---

### 三、详细实现方案

#### 3.1 前端修复：学生画像详情页选项显示

**文件：`apps/miniprogram/pages/assessment-detail/index.wxss`**

**修改位置：约第 115-126 行**

**原代码：**
```css
.option-button {
  min-height: var(--safe-touch);
  padding: 0 18rpx;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
  color: var(--safe-text);
  font-size: 25rpx;
  line-height: 1.5;
  transition: all 120ms ease;
  word-break: break-all;
  font-weight: 800;
}
```

**修改为：**
```css
.option-button {
  min-height: var(--safe-touch);
  padding: 0 18rpx;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
  color: var(--safe-text);
  font-size: 25rpx;
  line-height: 1.5;
  transition: all 120ms ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 800;
}
```

**改动说明：**
- 删除 `word-break: break-all;`（导致中文断开）
- 添加 `white-space: nowrap;`（不换行）
- 添加 `overflow: hidden;`（超出隐藏）
- 添加 `text-overflow: ellipsis;`（超长显示省略号）

> **【Claude订正 · 此修复方向会引入新 bug，改用下面的版本】**
> 选项是 **grid 多列窄格**（`assessment-detail/index.wxss` 选项容器 `repeat(auto-fill, minmax(0,1fr))`，按钮 `font-size:20rpx`、可两行），"5 几乎总是"这类 5–6 字标签**靠换行**才能完整显示。改成 `white-space:nowrap; text-overflow:ellipsis` 后，窄格单行放不下会被截成 **"5 几…"**，用户分不清"几乎总是 / 几乎从不"——**直接损坏量表作答语义**。
> 正确做法：把 `break-all` 换成 `keep-all`（中文按词/标点断、不拆字），并**保留可换行**（不要 nowrap/ellipsis）：
> ```css
> .option-button {
>   /* ...其余不变... */
>   word-break: keep-all;   /* 替换 break-all */
>   white-space: normal;    /* 允许换行 */
>   font-weight: 800;
> }
> ```
> （`.option-button` 真实位置 `index.wxss:106-120`，`word-break: break-all` 在 :119，核实无误。选项 label 形如 "5 几乎总是" 由后端 `build_worksheets.py:39` 拼接。）

#### 3.2 前端改造：测一测列表页

**文件：`apps/miniprogram/pages/assessment/index.js`**

> **【Claude订正 · 本节 3.2 整体方向调整，以下为准，原各子节按此取舍】**
> 1. **API 名**：用 `api.listAssessments(params)`（`services/api.js:360`），**不是 `api.getAssessments()`**（不存在，会 `TypeError` 致测一测页白屏）。
> 2. **真实函数名**：筛选用 `refreshVisibleAssessments()`（**非** `applyFilters`）；分组用模块级 `buildAssessmentSections(items, activeAudience, query)`（**非** `buildCategorySections`）。**改这两个真实函数**，不要新建同名函数（否则成孤儿函数、改了不生效）。
> 3. **无 demo 数据**：3.2.2"删除 demo 数据逻辑"无对象，跳过（页面本就无硬编码量表）。
> 4. **分组维度——保留现状（用户决策 2026-07-01）**：当前是「顶部 Tab = 学生/家长/成人（按 `audience_class` 过滤）+ 页内 section 按**反射弧节点 `reflex_node`** 分组（标题取 `NODE_LABELS`）」。**👉 3.2.4『改为按 audience_class 分组』作废**——那会与 Tab 重复、并丢掉反射弧节点维度（量表体系核心分类）。section 继续按 `reflex_node` 分组，**不改**。
> 5. **本节真正要做的只有 3 件**：① 搜索接好（在 `refreshVisibleAssessments` 内按 `display_title` + `search_keywords` 过滤）；② 确认 Tab 用 `audience_class ∈ {student,parent,adult}` 过滤；③ 修详情页选项截断（见 3.1 的【Claude订正】，用 `keep-all` 不用 ellipsis）。其余"删 demo / 换分组维度"描述忽略。

##### 3.2.1 修改分类标签

**修改位置：第 5-10 行**

**原代码：**
```javascript
const AUDIENCE_TABS = [
  { key: "all", label: "全部", description: "查看当前可填写内容" },
  { key: "student", label: "学生自助", description: "学习、压力和支持画像" },
  { key: "parent", label: "家长自助", description: "亲子理解和陪伴练习" },
  { key: "adult", label: "成人自助", description: "情绪、觉察和自我支持" },
];
```

**保持不变**（已经是正确的分类）

##### 3.2.2 删除 demo 数据逻辑

**修改位置：第 161-243 行**

在 `Page({})` 中找到 `onLoad` 方法，删除所有硬编码的 demo 量表数据。

**原代码：**
```javascript
onLoad() {
  this.setData({
    activeAudience: this.getDefaultAudience(),
  });
  this.loadAssessments();
},
```

**保持不变**（逻辑正确）

**但需要检查 `loadAssessments` 方法，确保没有混入 demo 数据。**

**修改位置：约第 176-200 行**

找到 `loadAssessments` 方法，**确认是否有硬编码的 demo 数据混入**。

**期望的正确代码：**
```javascript
async loadAssessments() {
  this.setData({ loading: true, errorMessage: "" });

  try {
    const result = await api.getAssessments();

    if (!result.ok) {
      this.setData({
        loading: false,
        errorMessage: result.error?.message || "读取失败",
      });
      return;
    }

    const worksheets = result.data.worksheets || [];
    
    // 只保留启用的量表
    const enabledWorksheets = worksheets.filter(
      (w) => w.enabled_for_user !== false
    );

    this.setData({
      loading: false,
      allAssessments: enabledWorksheets,
      boundaryNotice: result.data.boundary_notice || "",
    });

    this.applyFilters();
  } catch (err) {
    this.setData({
      loading: false,
      errorMessage: "网络错误，请重试",
    });
    console.error("loadAssessments error:", err);
  }
},
```

**如果发现有硬编码的 demo 数据（如 `const demoWorksheets = [...]`），全部删除。**

##### 3.2.3 修改搜索逻辑

**修改位置：约第 230-250 行**

找到 `applyFilters` 方法，确保搜索逻辑正确匹配**标题和关键词**。

**期望的正确代码：**
```javascript
applyFilters() {
  const { allAssessments, activeAudience, searchKeyword } = this.data;
  const keyword = (searchKeyword || "").trim().toLowerCase();

  // 按分类过滤
  let filtered = allAssessments;
  if (activeAudience !== "all") {
    filtered = filtered.filter(
      (item) => item.audience_class === activeAudience
    );
  }

  // 按搜索关键词过滤（搜索标题 + search_keywords）
  if (keyword) {
    filtered = filtered.filter((item) => {
      const title = (item.display_title || "").toLowerCase();
      const keywords = (item.search_keywords || [])
        .map((k) => String(k).toLowerCase())
        .join(" ");
      return title.includes(keyword) || keywords.includes(keyword);
    });
  }

  const categories = buildCategorySections(filtered);
  this.setData({ categories });
},
```

##### 3.2.4 检查分组逻辑

> **【Claude订正 · 本子节作废】** 分组维度**保留按反射弧节点 `reflex_node` 分组**（用户决策 2026-07-01），**不**改为 `audience_class`。真实分组函数名是 `buildAssessmentSections`（非 `buildCategorySections`）。以下"按 audience_class 分组"的代码**不要执行**。

**修改位置：约第 100-138 行**

找到 `buildCategorySections` 函数，**确认分组逻辑是否正确**。

根据你的要求，分类应该是"学生自助/家长自助/成人自助"，而不是按 `reflex_node` 分组。

**修改后的正确代码：**
```javascript
function buildCategorySections(filtered) {
  if (!filtered.length) {
    return [
      {
        key: "empty",
        title: "没有匹配内容",
        subtitle: "换一个分类或关键词再看",
        emptyText: "当前条件下没有可显示的测评内容。",
        items: [],
      },
    ];
  }

  // 按 audience_class 分组
  const audienceMap = {
    student: {
      key: "student",
      title: "学生自助",
      subtitle: "学习、压力和支持画像",
      items: [],
    },
    parent: {
      key: "parent",
      title: "家长自助",
      subtitle: "亲子理解和陪伴练习",
      items: [],
    },
    adult: {
      key: "adult",
      title: "成人自助",
      subtitle: "情绪、觉察和自我支持",
      items: [],
    },
  };

  filtered.forEach((item) => {
    const audienceClass = item.audience_class || "adult";
    if (audienceMap[audienceClass]) {
      audienceMap[audienceClass].items.push(item);
    }
  });

  // 只返回有内容的分组
  const sections = Object.values(audienceMap).filter(
    (section) => section.items.length > 0
  );

  return sections;
}
```

**改动说明：**
- 删除原有的 `reflex_node` 分组逻辑
- 改为按 `audience_class` 分组
- 分组标签使用固定的"学生自助/家长自助/成人自助"

#### 3.3 前端样式优化

**文件：`apps/miniprogram/pages/assessment/index.wxss`**

**无需修改**，当前样式已适配分类展示。

---

### 四、验收标准

#### 4.1 学生画像详情页验收

**在微信开发者工具中测试：**

1. 进入"测一测"页面
2. 点击"学生支持性画像测评"
3. 确认选项按钮显示正确：
   - ✅ "1 很少" 显示为完整文字，不被断开
   - ✅ "2 偶尔" 显示为完整文字
   - ✅ "3 有时" 显示为完整文字
   - ✅ "4 经常" 显示为完整文字
   - ✅ "5 几乎总是" 显示为完整文字
4. 确认题目和选项布局清晰，无乱码

#### 4.2 测一测列表页验收

**在微信开发者工具中测试：**

1. 进入"测一测"页面
2. 确认默认显示"家长自助"分类
3. 确认页面展示的量表数量：
   - **全部**：约16个量表
   - **学生自助**：约5个量表
   - **家长自助**：约1个量表
   - **成人自助**：约10个量表
4. 确认**没有 demo 测试量表**（如"工作表1.1"等）
5. 确认分组标题正确：
   - 学生自助分组显示"学生自助"标题
   - 家长自助分组显示"家长自助"标题
   - 成人自助分组显示"成人自助"标题

#### 4.3 搜索功能验收

**在微信开发者工具中测试：**

1. 在搜索框输入"情绪"
   - 确认显示所有标题或关键词包含"情绪"的量表
2. 在搜索框输入"学生"
   - 确认显示"学生支持性画像测评"等相关量表
3. 在搜索框输入"压力"
   - 确认显示所有与压力相关的量表
4. 点击"清除"按钮
   - 确认搜索框清空，列表恢复默认显示
5. 搜索"不存在的关键词"
   - 确认显示"没有匹配内容"提示

#### 4.4 边界验收

**必须符合：**
- ✅ 非诊断文案：页面保留"不构成诊断或贴标签"等边界说明
- ✅ API 不变：不破坏后端 `/api/assessments` 接口
- ✅ 数据来源：前端只从后端 API 获取量表，不使用硬编码数据
- ✅ 代码检查：小程序 JS/JSON/WXSS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram\pages\assessment -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram\pages\assessment-detail -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 测一测页面改造（T6-02）
  - 删除所有 demo 测试量表，改为从后端 API 动态获取
  - 修复学生画像测评详情页选项显示问题（word-break 导致断行）
  - 实现搜索功能（标题+关键词）
  - 按"学生自助/家长自助/成人自助"正确分类展示
  - 启用量表：学生5个、家长1个、成人10个，共16个
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"测一测"章节更新：

```markdown
### 测一测页面

**验收结果：**
- ✅ 量表列表从后端动态获取，无硬编码 demo 数据
- ✅ 搜索功能正常（标题+关键词）
- ✅ 分类展示正确（学生/家长/成人自助）
- ✅ 学生画像测评选项显示完整，无断行乱码
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-02 测一测页面改造
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：删除 demo 量表 + 修复学生画像详情页显示 + 搜索功能 + 分类展示
- 关键决策：前端完全依赖后端 API，不使用硬编码数据；修复 word-break 导致的中文断行问题
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的设计图片（两张截图）
- [ ] 3. 修改 `apps/miniprogram/pages/assessment-detail/index.wxss` 第 115-126 行（选项按钮样式）
- [ ] 4. 审查 `apps/miniprogram/pages/assessment/index.js` 的 `loadAssessments` 方法
- [ ] 5. 删除任何硬编码的 demo 量表数据
- [ ] 6. 修改 `buildCategorySections` 函数（改为按 audience_class 分组）
- [ ] 7. 检查 `applyFilters` 方法的搜索逻辑（确保搜索标题+关键词）
- [ ] 8. 在微信开发者工具中测试学生画像详情页（选项显示）
- [ ] 9. 在微信开发者工具中测试量表列表页（分类+数量）
- [ ] 10. 测试搜索功能（输入"情绪""学生""压力"等关键词）
- [ ] 11. 确认无 demo 量表残留
- [ ] 12. 运行代码检查命令（JS 语法）
- [ ] 13. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 14. 截图验收结果（列表页+详情页+搜索结果），提交给用户确认

---

### 七、注意事项

1. **保留学生画像测评**：不要删除 `student_profile_v1`，这是核心功能
2. **删除所有 demo**：检查代码中是否有 `const demoWorksheets = [...]` 等硬编码数据，全部删除
3. **参考设计 skills**：Codex 在实现时优先调用本地 `frontend-design` 等 skills
4. **遵守伦理边界**：页面必须保留"不构成诊断"等非诊断文案
5. **代码风格**：保持与现有代码一致（缩进、命名、注释）
6. **测试完整性**：必须在微信开发者工具中实际测试，不能只改代码不验证

---

**任务状态：** 待执行
**预计工时：** 2-3 小时（前端修复1h + 列表改造1h + 测试验收1h）
**优先级：** P0（核心测评功能改造）

---

## T6-03：三步开始页面优化（文案+视觉）

> **【Claude订正 · 本节可信，按原文执行即可】** 经逐行核实，T6-03 引用的行号/文案/字段**全部精确命中**（intro-text 在 `index.wxml:5`、steps/boundaries 在 `index.js`、按钮在 `index.wxml:24-25`、step 结构 `index.wxml:8-13`、`.step-title` 在 `index.wxss:62-66`）。是任务六里最可靠的一节。唯一提醒：`steps`/`boundaries` 是 `index.js` 里的 data（不在 wxml）。

### 一、任务目标

优化"三步开始"页面，提升新手理解度和视觉吸引力：
1. **优化文案**：去除专业术语，改为生活化表达
2. **添加视觉元素**：步骤卡片增加数字标签，提升层次感
3. **统一按钮文案**：保持温和一致的表达风格

**核心变更：**
- 将"情绪反射弧"等专业术语改为通俗表达
- 简化新手说明文案，降低认知负担
- 为三个步骤卡片添加数字标签（1/2/3）
- 统一按钮文案风格

---

### 二、前端代码审核结论

**现有文件：**
- `apps/miniprogram/pages/getting-started/index.wxml` - 页面结构
- `apps/miniprogram/pages/getting-started/index.js` - 数据和逻辑
- `apps/miniprogram/pages/getting-started/index.wxss` - 样式

**审核结论：**
- ✅ 信息层级清晰：新手说明 → 三步流程 → 使用边界 → 行动按钮
- ✅ 视觉设计符合规范：色彩、圆角、阴影、间距正确
- ✅ 伦理边界明确：底部说明"不下诊断结论"
- ⚠️ 文案过于专业化："情绪反射弧""链路"等术语不够通俗
- ⚠️ 缺少视觉辅助：纯文字卡片略显单调

---

### 三、详细实现方案

#### 3.1 文案优化

**文件：`apps/miniprogram/pages/getting-started/index.js`**

##### 3.1.1 优化新手说明文案

**修改位置：data 对象外（需要新增常量）**

在 `Page({})` 之前添加常量定义：

```javascript
const INTRO_TEXT = "当和孩子出现冲突或情绪时，先记录下来：发生了什么、你有什么感受、你做了什么。记下这些线索，下次就更容易找到可以调整的地方。";
```

**文件：`apps/miniprogram/pages/getting-started/index.wxml`**

**修改位置：第 5 行**

**原代码：**
```xml
<text class="intro-text">当亲子互动里出现压力时，可以先把它当作一次"情绪反射弧"：事件出现后，我们会有情绪、想法、身体反应和行为。把这条链路写下来，才更容易找到下一次可以轻轻调整的位置。</text>
```

**修改为：**
```xml
<text class="intro-text">当和孩子出现冲突或情绪时，先记录下来：发生了什么、你有什么感受、你做了什么。记下这些线索，下次就更容易找到可以调整的地方。</text>
```

##### 3.1.2 优化步骤2文案

**文件：`apps/miniprogram/pages/getting-started/index.js`**

**修改位置：data.steps 数组第2项（第 8-11 行）**

**原代码：**
```javascript
{
  title: "2. 查看支持性反馈",
  text: "系统只做非诊断、非评判的线索提示，帮助你看见情绪、想法、身体反应和行为之间的连接。",
},
```

**修改为：**
```javascript
{
  title: "2. 查看支持性反馈",
  text: "系统会给你一些支持性反馈，帮你理解当时的情绪和反应模式，不做诊断或评判。",
},
```

##### 3.1.3 优化使用边界文案

**文件：`apps/miniprogram/pages/getting-started/index.js`**

**修改位置：data.boundaries 数组第2项（第 19 行）**

**原代码：**
```javascript
"高风险内容需要优先寻求人工支持或专业帮助。",
```

**修改为：**
```javascript
"如遇严重安全问题，请优先寻求专业帮助或人工支持。",
```

##### 3.1.4 优化按钮文案

**文件：`apps/miniprogram/pages/getting-started/index.wxml`**

**修改位置：第 24-25 行**

**原代码：**
```xml
<button class="primary-action" bindtap="startDiary">记录一次</button>
<button class="secondary-action" bindtap="openTraining">去训练中心</button>
```

**修改为：**
```xml
<button class="primary-action" bindtap="startDiary">开始记录</button>
<button class="secondary-action" bindtap="openTraining">看看训练卡</button>
```

#### 3.2 视觉优化：添加步骤数字标签

##### 3.2.1 修改页面结构

**文件：`apps/miniprogram/pages/getting-started/index.wxml`**

**修改位置：第 8-13 行**

**原代码：**
```xml
<view class="step-list">
  <view wx:for="{{steps}}" wx:key="title" class="step-card">
    <text class="step-title">{{item.title}}</text>
    <text class="step-text">{{item.text}}</text>
  </view>
</view>
```

**修改为：**
```xml
<view class="step-list">
  <view wx:for="{{steps}}" wx:key="title" class="step-card">
    <view class="step-header">
      <view class="step-number">{{index + 1}}</view>
      <text class="step-title">{{item.title}}</text>
    </view>
    <text class="step-text">{{item.text}}</text>
  </view>
</view>
```

##### 3.2.2 添加数字标签样式

**文件：`apps/miniprogram/pages/getting-started/index.wxss`**

**修改位置：在 `.step-card` 样式后（约第 60 行附近）添加**

```css
.step-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

.step-number {
  width: 56rpx;
  height: 56rpx;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--safe-primary);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
}

.step-title {
  flex: 1;
  color: var(--safe-title);
  font-size: 29rpx;
  font-weight: 850;
  line-height: 1.35;
}
```

**同时删除原有的独立 `.step-title` 样式（约第 68-72 行）：**

**删除这段：**
```css
.step-title {
  color: var(--safe-title);
  font-size: 29rpx;
  font-weight: 850;
}
```

---

### 四、验收标准

#### 4.1 文案验收

**在微信开发者工具中测试：**

1. 进入"三步开始"页面
2. 确认新手说明文案：
   - ✅ 没有"情绪反射弧"等专业术语
   - ✅ 使用"冲突或情绪""线索"等通俗表达
3. 确认步骤2文案：
   - ✅ "支持性反馈"清晰易懂
   - ✅ 没有"线索提示""连接"等抽象词
4. 确认使用边界文案：
   - ✅ "严重安全问题"比"高风险内容"更温和
5. 确认按钮文案：
   - ✅ "开始记录"+"看看训练卡"长度接近
   - ✅ 风格一致，都是温和表达

#### 4.2 视觉验收

**在微信开发者工具中测试：**

1. 确认步骤卡片结构：
   - ✅ 每个步骤卡片左侧显示圆形数字标签（1/2/3）
   - ✅ 数字标签为绿色底白字
   - ✅ 标题在数字标签右侧，与数字水平对齐
2. 确认布局美观：
   - ✅ 数字标签和标题之间间距适中（16rpx）
   - ✅ 标题和正文之间间距合理（12rpx）
   - ✅ 整体视觉层次清晰

#### 4.3 交互验收

**在微信开发者工具中测试：**

1. 点击"开始记录"按钮
   - ✅ 跳转到情绪日记表单页面
2. 点击"看看训练卡"按钮
   - ✅ 跳转到训练中心页面（tabBar）

#### 4.4 边界验收

**必须符合：**
- ✅ 伦理边界说明保持清晰："不下诊断结论"
- ✅ 文案保持非评判、支持性表达
- ✅ 没有诊断化、标签化表达
- ✅ 代码检查：JS/WXML/WXSS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
node --check apps\miniprogram\pages\getting-started\index.js
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 三步开始页面优化（T6-03）
  - 文案优化：去除"情绪反射弧"等专业术语，改为生活化表达
  - 视觉优化：步骤卡片增加数字标签（1/2/3），提升层次感
  - 按钮文案统一：改为"开始记录"+"看看训练卡"
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"三步开始"章节更新：

```markdown
### 三步开始页面

**验收结果：**
- ✅ 文案通俗易懂，无专业术语
- ✅ 步骤卡片有数字标签，视觉层次清晰
- ✅ 按钮文案温和一致
- ✅ 伦理边界说明清楚
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-03 三步开始页面优化
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：文案优化（去除专业术语）+ 视觉优化（数字标签）
- 关键决策：降低新手理解门槛，提升视觉吸引力
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的截图（三步开始页面）
- [ ] 3. 修改 `apps/miniprogram/pages/getting-started/index.wxml` 第5行（新手说明文案）
- [ ] 4. 修改 `apps/miniprogram/pages/getting-started/index.js` data.steps 第2项（步骤2文案）
- [ ] 5. 修改 `apps/miniprogram/pages/getting-started/index.js` data.boundaries 第2项（边界文案）
- [ ] 6. 修改 `apps/miniprogram/pages/getting-started/index.wxml` 第24-25行（按钮文案）
- [ ] 7. 修改 `apps/miniprogram/pages/getting-started/index.wxml` 第8-13行（添加数字标签结构）
- [ ] 8. 在 `apps/miniprogram/pages/getting-started/index.wxss` 添加数字标签样式
- [ ] 9. 删除 `index.wxss` 中原有的独立 `.step-title` 样式
- [ ] 10. 在微信开发者工具中测试页面显示
- [ ] 11. 确认文案通俗易懂，无专业术语
- [ ] 12. 确认数字标签显示正确（1/2/3圆形绿底白字）
- [ ] 13. 测试按钮跳转（开始记录→日记表单，看看训练卡→训练中心）
- [ ] 14. 运行代码检查命令（JS 语法）
- [ ] 15. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 16. 截图验收结果（优化前后对比），提交给用户确认

---

### 七、注意事项

1. **保持伦理边界**：不删除"使用边界"卡片，只优化表达
2. **保持色彩规范**：数字标签使用 `var(--safe-primary)`，不使用其他颜色
3. **保持简洁风格**：不添加过多装饰，保持克制的设计
4. **参考设计 skills**：Codex 在实现时优先调用本地 `frontend-design` 等 skills
5. **代码风格**：保持与现有代码一致（缩进、命名、注释）
6. **测试完整性**：必须在微信开发者工具中实际测试，不能只改代码不验证

---

### 八、设计参考（视觉效果）

**数字标签预期效果：**

```
┌──────────────────────────────┐
│  ⊙   1. 记录一个具体事件      │
│  1                            │
│                               │
│  先写清楚发生了什么、当时...  │
└──────────────────────────────┘
```

**数字标签样式：**
- 直径：56rpx
- 背景：绿色（`--safe-primary`）
- 文字：白色，28rpx，粗体
- 与标题间距：16rpx

---

**任务状态：** 待执行
**预计工时：** 1-1.5 小时（文案修改0.5h + 视觉优化0.5h + 测试验收0.5h）
**优先级：** P2（体验优化，非核心功能）

---

## T6-04：首页支持性反馈和最近记录改造

> **【Claude订正 · 本节 API名/方法名/时区，以下为准】**
> 1. **`api.getDiaries` 不存在 → 改用 `api.listDiaries(params)`**（`services/api.js:277`，GET `/api/diaries`）。本节 3.1.2 代码块里 `api.getDiaries({limit:1})` 全部改成 `api.listDiaries({limit:1})`；列表取 `result.data.items`（沿用本计划统一的 `{ok,data}` 包装）。
> 2. **`onShow` 的统计方法真名是 `refreshTodayRecordCount`（非 `loadTodayRecordCount`）**——3.1.3"原代码"写错了。只需在 `onShow` 里**新增** `this.loadLatestRecord()`，别去找不存在的 `loadTodayRecordCount`。
> 3. **时区**：`created_at` 是 `now_iso()` 写入的 **UTC** ISO 串。`new Date(created_at)` 在小程序按设备本地时区解析，会让"今天/昨天"判断偏移（跨零点误判）。建议后端补一个本地化展示字段，或前端按 `+08:00` 显式校正；本期至少在验收里注明此偏移已知。
> 4. 字段 `scene/event_description/parent_emotion` 前后端一致（✅）；`latestRecord` 硬编码属实可放心替换；`feedback-result` 收 `diary_id`（✅）。

### 一、任务目标

改造首页的"支持性反馈"入口和"最近记录"模块，实现动态数据展示和正确的跳转逻辑：
1. **删除硬编码数据**：最近记录从后端 API 动态获取
2. **修复跳转逻辑**：点击记录卡片跳转到该次反馈详情，而非本周复盘
3. **优化文案**："查看全部"改为"本周复盘"
4. **优化支持性反馈入口**：根据是否有记录，跳转到最近一次反馈或引导记录

**核心变更：**
- 删除 `latestRecord` 硬编码数据
- 调用 API 获取最近一条情绪日记记录
- 记录卡片点击跳转到对应的反馈详情页
- "查看全部"改为"本周复盘"

---

### 二、前端代码审核结论

**现有代码：**
- `apps/miniprogram/pages/home/index.js` - 首页逻辑
- `apps/miniprogram/pages/home/index.wxml` - 首页结构

**审核结论：**
- ❌ **问题1**：最近记录是硬编码（第 105-110 行）
  ```javascript
  latestRecord: {
    mood: "有点烦",
    time: "昨天 21:30",
    trigger: "孩子写作业磨蹭",
    status: "支持性反馈已完成",
  }
  ```
- ❌ **问题2**：记录卡片点击跳转到 `openWeeklyReport`（本周复盘），应该跳转到反馈详情
- ❌ **问题3**："查看全部"文案不清晰，应改为"本周复盘"
- ❌ **问题4**："支持性反馈"入口当前只是提示记录，未展示上次互动线索

---

### 三、详细实现方案

#### 3.1 删除硬编码数据，改为动态获取

**文件：`apps/miniprogram/pages/home/index.js`**

##### 3.1.1 修改 data 定义

**修改位置：第 105-110 行**

**原代码：**
```javascript
latestRecord: {
  mood: "有点烦",
  time: "昨天 21:30",
  trigger: "孩子写作业磨蹭",
  status: "支持性反馈已完成",
},
```

**修改为：**
```javascript
latestRecord: null,
latestRecordReady: false,
```

##### 3.1.2 添加加载最近记录的方法

**修改位置：在 `onShow()` 方法后添加（约第 120 行附近）**

```javascript
async loadLatestRecord() {
  try {
    const result = await api.getDiaries({ limit: 1 });
    
    if (!result.ok || !result.data.items || result.data.items.length === 0) {
      this.setData({
        latestRecord: null,
        latestRecordReady: true,
      });
      return;
    }

    const diary = result.data.items[0];
    
    // 格式化时间
    const createdAt = new Date(diary.created_at);
    const now = new Date();
    const diffMs = now - createdAt;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    let timeLabel = "";
    if (diffDays === 0) {
      const hours = createdAt.getHours();
      const minutes = createdAt.getMinutes();
      timeLabel = `今天 ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    } else if (diffDays === 1) {
      const hours = createdAt.getHours();
      const minutes = createdAt.getMinutes();
      timeLabel = `昨天 ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    } else if (diffDays < 7) {
      timeLabel = `${diffDays}天前`;
    } else {
      const month = createdAt.getMonth() + 1;
      const day = createdAt.getDate();
      timeLabel = `${month}月${day}日`;
    }

    this.setData({
      latestRecord: {
        id: diary.id,
        mood: diary.parent_emotion || "情绪记录",
        time: timeLabel,
        trigger: diary.scene || diary.event_description?.slice(0, 15) || "具体事件",
        status: "支持性反馈已完成",
      },
      latestRecordReady: true,
    });
  } catch (err) {
    console.error("loadLatestRecord error:", err);
    this.setData({
      latestRecord: null,
      latestRecordReady: true,
    });
  }
},
```

> **【Claude订正】** 上方 `api.getDiaries({ limit: 1 })` → **`api.listDiaries({ limit: 1 })`**；`new Date(diary.created_at)` 的 `created_at` 是 **UTC**（见本节节首订正第 3 点，"今天/昨天"判断需按 UTC 或 `+08:00` 处理，否则跨零点会误判）。

##### 3.1.3 在 onShow 中调用

**修改位置：第 114-118 行**

**原代码：**
```javascript
onShow() {
  this.loadTodayRecordCount();
  this.checkDevEntry();
},
```

**修改为：**
```javascript
onShow() {
  this.loadTodayRecordCount();
  this.loadLatestRecord();
  this.checkDevEntry();
},
```

#### 3.2 修复跳转逻辑

##### 3.2.1 修改记录卡片点击事件

**文件：`apps/miniprogram/pages/home/index.wxml`**

**修改位置：第 78-84 行**

**原代码：**
```xml
<button class="recent-record-card" bindtap="openWeeklyReport">
  <view class="recent-copy">
    <text class="recent-time">{{latestRecord.time}}</text>
    <text class="recent-title">{{latestRecord.mood}}，{{latestRecord.trigger}}</text>
  </view>
  <text class="recent-status">{{latestRecord.status}} ›</text>
</button>
```

**修改为：**
```xml
<button wx:if="{{latestRecord}}" class="recent-record-card" bindtap="openLatestRecordFeedback">
  <view class="recent-copy">
    <text class="recent-time">{{latestRecord.time}}</text>
    <text class="recent-title">{{latestRecord.mood}}，{{latestRecord.trigger}}</text>
  </view>
  <text class="recent-status">{{latestRecord.status}} ›</text>
</button>
<view wx:else class="recent-empty">
  <text class="recent-empty-text">还没有记录，先去记录一次吧</text>
</view>
```

##### 3.2.2 添加跳转方法

**文件：`apps/miniprogram/pages/home/index.js`**

**修改位置：在 `openWeeklyReport()` 方法后添加（约第 167 行附近）**

```javascript
openLatestRecordFeedback() {
  if (!this.data.latestRecord || !this.data.latestRecord.id) {
    wx.showToast({
      title: "没有找到记录",
      icon: "none",
    });
    return;
  }
  
  // 跳转到反馈结果页
  wx.navigateTo({
    url: `/pages/feedback-result/index?diary_id=${encodeURIComponent(this.data.latestRecord.id)}`,
  });
},
```

#### 3.3 优化文案

##### 3.3.1 "查看全部"改为"本周复盘"

**文件：`apps/miniprogram/pages/home/index.wxml`**

**修改位置：第 77 行**

**原代码：**
```xml
<section-title title="最近记录" subtitle="方便继续查看与跟进" more-text="查看全部" bind:more="openWeeklyReport" />
```

**修改为：**
```xml
<section-title title="最近记录" subtitle="方便继续查看与跟进" more-text="本周复盘" bind:more="openWeeklyReport" />
```

#### 3.4 优化支持性反馈入口

##### 3.4.1 修改跳转逻辑

**文件：`apps/miniprogram/pages/home/index.js`**

**修改位置：第 200-207 行**

**原代码：**
```javascript
if (key === "feedback") {
  wx.showToast({
    title: "请先记录一次事件",
    icon: "none",
  });
  wx.navigateTo({ url: "/pages/diary-form/index" });
  return;
}
```

**修改为：**
```javascript
if (key === "feedback") {
  if (this.data.latestRecord && this.data.latestRecord.id) {
    // 有最近记录，跳转到最近一次反馈
    wx.navigateTo({
      url: `/pages/feedback-result/index?diary_id=${encodeURIComponent(this.data.latestRecord.id)}`,
    });
  } else {
    // 没有记录，引导先记录
    wx.showToast({
      title: "请先记录一次事件",
      icon: "none",
    });
    wx.navigateTo({ url: "/pages/diary-form/index" });
  }
  return;
}
```

#### 3.5 添加空状态样式

**文件：`apps/miniprogram/pages/home/index.wxss`**

**在文件末尾添加（约第 200 行附近）：**

```css
.recent-empty {
  padding: 40rpx 24rpx;
  text-align: center;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-bg);
}

.recent-empty-text {
  color: var(--safe-muted);
  font-size: 26rpx;
  line-height: 1.6;
}
```

---

### 四、验收标准

#### 4.1 动态数据验收

**在微信开发者工具中测试：**

1. **首次进入（无记录）：**
   - ✅ "最近记录"显示"还没有记录，先去记录一次吧"
   - ✅ 点击"支持性反馈"提示"请先记录一次事件"，跳转到日记表单

2. **记录一次后：**
   - ✅ 返回首页，"最近记录"显示真实数据（时间+情绪+场景）
   - ✅ 时间格式正确（今天 17:09、昨天 21:30、3天前、6月30日）
   - ✅ 情绪和场景取自真实记录

3. **点击记录卡片：**
   - ✅ 跳转到该次记录的反馈详情页（`/pages/feedback-result/index?diary_id=xxx`）
   - ✅ 显示该次记录对应的反馈和推荐训练卡

4. **点击"本周复盘"：**
   - ✅ 跳转到本周复盘页面（`/pages/weekly-report/index`）

5. **点击"支持性反馈"入口：**
   - ✅ 有记录时跳转到最近一次反馈详情
   - ✅ 无记录时提示先记录

#### 4.2 数据格式验收

**确认以下字段映射正确：**
- `diary.id` → `latestRecord.id` ✅
- `diary.parent_emotion` → `latestRecord.mood` ✅
- `diary.scene` 或 `diary.event_description` → `latestRecord.trigger` ✅
- `diary.created_at` → `latestRecord.time`（格式化后）✅

#### 4.3 边界验收

**必须符合：**
- ✅ 无硬编码数据，所有内容从 API 获取
- ✅ API 调用失败时显示空状态，不影响其他功能
- ✅ 时间格式友好（今天/昨天/X天前/X月X日）
- ✅ 代码检查：JS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
node --check apps\miniprogram\pages\home\index.js
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 首页支持性反馈和最近记录改造（T6-04）
  - 删除硬编码数据，改为从 API 动态获取最近一条记录
  - 修复跳转逻辑：记录卡片跳转到反馈详情，"本周复盘"跳转到周报
  - 优化支持性反馈入口：根据是否有记录智能跳转
  - 添加空状态提示
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"首页"章节更新：

```markdown
### 首页

**验收结果：**
- ✅ 最近记录从 API 动态获取，无硬编码
- ✅ 记录卡片点击跳转到反馈详情
- ✅ "本周复盘"跳转正确
- ✅ 支持性反馈入口智能跳转（有记录→反馈详情，无记录→引导记录）
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-04 首页支持性反馈和最近记录改造
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：删除硬编码 + 动态数据 + 修复跳转逻辑 + 空状态
- 关键决策：记录卡片直接跳转反馈详情，支持性反馈入口智能判断
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的首页截图
- [ ] 3. 修改 `apps/miniprogram/pages/home/index.js` data 定义（删除硬编码）
- [ ] 4. 在 `index.js` 添加 `loadLatestRecord()` 方法
- [ ] 5. 修改 `index.js` 的 `onShow()` 方法（调用 loadLatestRecord）
- [ ] 6. 修改 `apps/miniprogram/pages/home/index.wxml` 记录卡片结构（添加空状态）
- [ ] 7. 在 `index.js` 添加 `openLatestRecordFeedback()` 方法
- [ ] 8. 修改 `index.wxml` 的 "查看全部" 文案为 "本周复盘"
- [ ] 9. 修改 `index.js` 的 `openCoreEntry()` 方法（优化支持性反馈逻辑）
- [ ] 10. 在 `apps/miniprogram/pages/home/index.wxss` 添加空状态样式
- [ ] 11. 在微信开发者工具中测试首次进入（无记录）
- [ ] 12. 记录一次情绪日记，返回首页查看动态数据
- [ ] 13. 点击记录卡片，确认跳转到反馈详情页
- [ ] 14. 点击"本周复盘"，确认跳转到周报页
- [ ] 15. 点击"支持性反馈"，确认智能跳转逻辑
- [ ] 16. 运行代码检查命令（JS 语法）
- [ ] 17. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 18. 截图验收结果（动态数据+跳转逻辑），提交给用户确认

---

### 七、注意事项

1. **时间格式友好**：使用"今天/昨天/X天前/X月X日"，不直接显示 ISO 时间
2. **空状态处理**：无记录时显示友好提示，不显示错误信息
3. **API 失败处理**：调用失败时设置 `latestRecord: null`，不影响其他功能
4. **代码风格**：保持与现有代码一致（缩进、命名、注释）
5. **测试完整性**：必须在微信开发者工具中实际测试完整流程

---

**任务状态：** 待执行
**预计工时：** 2-2.5 小时（删除硬编码1h + 修复逻辑1h + 测试验收0.5h）
**优先级：** P1（核心交互功能，影响用户体验）

---

## T6-05：本周复盘页面改造

> **【Claude订正 · 周报字段真相，以下为准】**
> 1. **API `api.getWeeklyReport()` 名正确**（`services/api.js:394`）。
> 2. **周报对象没有 `diaries_count/emotions_count/checkins_count/profiles_count`** —— 计划多处所谓"原代码用这些"是**虚构**。真实字段（`report_service.py:85-101`）：`frequent_scenes`、`frequent_emotions`、`common_patterns` 都是 **`[[名称,次数], ...]` 元组列表**；`completed_cards` 是字符串数组；`profile_trend.profile_count`；`next_week_suggestion`。
> 3. 前端 `weekly-report/index.js` 已有 `formatPairs([[名,次]]) → {name,count}`，结果存进 data 的 `frequentScenes/frequentEmotions/commonPatterns`。**高频场景显示场景名**直接用 `item.name`（已存在）——可行，照做。
> 4. **4 格数据绑定现状已正确**（已绑 data 的 `frequentScenes.length` 等）——见 3.2.1 订正：**只改样式、不改绑定**。
> 5. `profile_trend` **不落库**（`weekly_reports` 表无此列），仅 HTTP 响应透出；本期不要依赖它已持久化。
> 6. "下周可以继续的一小步"板块**确实存在**（`index.wxml:115-118`），可按计划删除。
> 7. tag 中文映射（3.4）可行，未命中映射表的回退原文不报错——照做。

### 一、任务目标

优化本周复盘页面，提升信息展示和视觉体验：
1. **删除冗长说明文案**：顶部说明过长，删除
2. **优化本周小变化卡片**：4个格子缩小，居中文字
3. **修复高频场景显示**：显示场景名称（不只是次数）
4. **修复互动线索显示**：`general_support` 改为中文"一般支持"
5. **删除"下周可以继续的一小步"板块**

**核心变更：**
- 删除顶部"这不是评分..."长文案
- 本周小变化4格：宽度缩小，内容居中
- 高频场景：显示场景名+次数（如"亲子沟通 3次"）
- 互动线索：tag 中文映射（`general_support` → "一般支持"）
- 删除最后的"下周可以继续的一小步"卡片

---

### 二、前端代码审核结论

**现有代码：**
- `apps/miniprogram/pages/weekly-report/index.wxml` - 页面结构
- `apps/miniprogram/pages/weekly-report/index.js` - 数据逻辑
- `backend/services/report_service.py` - 后端周报生成逻辑

**审核结论：**
- ❌ **问题1**：顶部说明文案过长（第6行）
  ```xml
  <text class="hero-summary">这不是评分，也不是判断。只是把记录和练习整理出来，帮你找到下周可以继续的一小步。</text>
  ```
  
- ❌ **问题2**：本周小变化4格太大，未居中（第44-63行）
  ```xml
  <view class="stat-grid">
    <view class="stat-card">
      <text class="stat-num">{{report.diaries_count || 0}}</text>
      <text class="stat-label">类常见场景</text>
    </view>
    ...
  </view>
  ```

- ❌ **问题3**：高频场景只显示次数，不显示场景名（第83-91行）
  ```xml
  <block wx:for="{{frequentScenes}}" wx:key="name">
    <view class="freq-row">
      <text class="row-num">{{item.count}}</text>
      <!-- 缺少场景名显示 -->
    </view>
  </block>
  ```

- ❌ **问题4**：互动线索显示英文 tag（第98-105行）
  ```xml
  <text class="row-name">{{item.name}}</text>
  <!-- item.name 是 "general_support"，未做中文映射 -->
  ```

- ❌ **问题5**：存在"下周可以继续的一小步"板块（第115-118行）
  ```xml
  <view class="next-step-card">
    <text class="next-title">下周可以继续的一小步</text>
    <text class="next-text">{{report.next_week_suggestion}}</text>
  </view>
  ```

**互动线索来源逻辑（已确认）：**
- 后端：`backend/services/report_service.py` 第64-67行
- 从 `feedback_results.tags_json` 统计最常见的5个 tag
- tag 是英文（如 `general_support`, `high_demand_language`）
- 前端直接显示，未做中文映射

---

### 三、详细实现方案

#### 3.1 删除顶部冗长说明

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第2-8行**

**原代码：**
```xml
<view class="weekly-hero safe-card safe-card--hero">
  <view class="hero-copy">
    <text class="hero-kicker">本周复盘</text>
    <text class="hero-title">看看这一周的小变化</text>
    <text class="hero-summary">这不是评分，也不是判断。只是把记录和练习整理出来，帮你找到下周可以继续的一小步。</text>
  </view>
</view>
```

**修改为：**
```xml
<view class="weekly-hero safe-card safe-card--hero">
  <view class="hero-copy">
    <text class="hero-kicker">本周复盘</text>
    <text class="hero-title">看看这一周的小变化</text>
  </view>
</view>
```

**删除：** `<text class="hero-summary">...</text>`

#### 3.2 优化本周小变化卡片

##### 3.2.1 修改卡片结构和样式

> **【Claude订正 · 只改样式，别改数据绑定】** 4 格现状**已正确**绑定 data 字段（`{{frequentScenes.length}}` / `{{frequentEmotions.length}}` / `{{commonPatterns.length}}` / `{{completedCardsText ? '已记' : '待记'}}`，均经 `formatPairs` 处理）。本子节"原代码 `report.diaries_count`"是虚构、"修改为 `report.frequent_scenes.length`"也不对（应是 data 里的 `frequentScenes`，不是 `report.frequent_scenes`）。**故下面的数据绑定改写不要做**（会把已正确的绑定改坏），只保留 `.stat-card` 缩小居中的**样式**改造。

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第44-63行**

**原代码：**
```xml
<view class="stat-grid">
  <view class="stat-card">
    <text class="stat-num">{{report.diaries_count || 0}}</text>
    <text class="stat-label">类常见场景</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.emotions_count || 0}}</text>
    <text class="stat-label">类常见情绪</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.checkins_count || 0}}</text>
    <text class="stat-label">条互动索引</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.profiles_count || '待记'}}</text>
    <text class="stat-label">{{report.profiles_count ? '次画像' : '续写测试'}}</text>
  </view>
</view>
```

**修改为：**
```xml
<view class="stat-grid">
  <view class="stat-card">
    <text class="stat-num">{{report.frequent_scenes.length || 0}}</text>
    <text class="stat-label">类常见场景</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.frequent_emotions.length || 0}}</text>
    <text class="stat-label">类常见情绪</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.completed_cards.length || 0}}</text>
    <text class="stat-label">条互动索引</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.profile_trend.profile_count || 0}}</text>
    <text class="stat-label">{{report.profile_trend.profile_count ? '次画像' : '续写测试'}}</text>
  </view>
</view>
```

**文件：`apps/miniprogram/pages/weekly-report/index.wxss`**

**查找 `.stat-card` 样式，修改宽度和对齐**

**原样式（需要查找）：**
```css
.stat-card {
  /* 当前样式 */
}
```

**修改为：**
```css
.stat-card {
  flex: 0 0 calc(50% - 12rpx);
  max-width: 200rpx;
  padding: 24rpx 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
}

.stat-num {
  display: block;
  color: var(--safe-primary);
  font-size: 48rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
}

.stat-label {
  display: block;
  margin-top: 12rpx;
  color: var(--safe-text);
  font-size: 24rpx;
  line-height: 1.4;
  text-align: center;
}
```

#### 3.3 修复高频场景显示

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第83-91行**

**原代码：**
```xml
<block wx:for="{{frequentScenes}}" wx:key="name">
  <view class="freq-row">
    <text class="row-num">{{item.count}}</text>
  </view>
</block>
```

**修改为：**
```xml
<block wx:for="{{frequentScenes}}" wx:key="name">
  <view class="freq-row">
    <text class="row-name">{{item.name}}</text>
    <text class="row-count">{{item.count}} 次</text>
  </view>
</block>
```

**改动说明：**
- 添加 `<text class="row-name">{{item.name}}</text>` 显示场景名
- `{{item.count}}` 改为 `{{item.count}} 次`

#### 3.4 修复互动线索中文映射

##### 3.4.1 添加 tag 中文映射

**文件：`apps/miniprogram/pages/weekly-report/index.js`**

**在文件开头添加常量（第3行附近）：**

```javascript
const TAG_LABELS = {
  general_support: "一般支持",
  high_demand_language: "高要求语言",
  emotional_behavior: "情绪与行为",
  cognitive_flexibility: "认知灵活性",
  acceptance_openness: "接纳与开放",
  mindful_awareness: "觉察当下",
  self_compassion: "自我关怀",
  parental_burnout: "家长耗竭",
  parent_child_interaction: "亲子互动",
  academic_pressure: "学业压力",
  emotion_regulation: "情绪调节",
  uncertainty_intolerance: "不确定性不耐受",
  fear_negative_evaluation: "害怕负面评价",
  test_anxiety: "考试焦虑",
};
```

##### 3.4.2 修改数据处理逻辑

**文件：`apps/miniprogram/pages/weekly-report/index.js`**

**修改位置：第5-10行**

**原代码：**
```javascript
function formatPairs(items = []) {
  return items.map((item) => ({
    name: item[0],
    count: item[1],
  }));
}
```

**修改为：**
```javascript
function formatPairs(items = [], useTagLabel = false) {
  return items.map((item) => ({
    name: useTagLabel ? (TAG_LABELS[item[0]] || item[0]) : item[0],
    count: item[1],
  }));
}
```

**修改位置：第36-37行**

**原代码：**
```javascript
commonPatterns: formatPairs(report.common_patterns || []),
```

**修改为：**
```javascript
commonPatterns: formatPairs(report.common_patterns || [], true),
```

#### 3.5 删除"下周可以继续的一小步"板块

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第115-118行**

**删除以下代码：**
```xml
<view class="next-step-card">
  <text class="next-title">下周可以继续的一小步</text>
  <text class="next-text">{{report.next_week_suggestion}}</text>
</view>
```

---

### 四、验收标准

#### 4.1 顶部说明验收

**在微信开发者工具中测试：**
1. 进入本周复盘页面
2. 确认顶部只有：
   - ✅ "本周复盘"（标签）
   - ✅ "看看这一周的小变化"（标题）
   - ❌ 没有长文案说明

#### 4.2 本周小变化卡片验收

**在微信开发者工具中测试：**
1. 确认4个格子：
   - ✅ 宽度缩小（约200rpx）
   - ✅ 数字和文字居中对齐
   - ✅ 布局为 2x2 网格
2. 确认内容正确：
   - ✅ 第1格：X 类常见场景（取自 `frequent_scenes.length`）
   - ✅ 第2格：X 类常见情绪（取自 `frequent_emotions.length`）
   - ✅ 第3格：X 条互动索引（取自 `completed_cards.length`）
   - ✅ 第4格：X 次画像（取自 `profile_trend.profile_count`）

#### 4.3 高频场景验收

**在微信开发者工具中测试：**
1. 确认每行显示：
   - ✅ 场景名称（如"亲子沟通"）
   - ✅ 出现次数（如"3 次"）
2. 确认排序：
   - ✅ 按次数从高到低

#### 4.4 互动线索验收

**在微信开发者工具中测试：**
1. 确认显示中文：
   - ✅ `general_support` 显示为"一般支持"
   - ✅ `high_demand_language` 显示为"高要求语言"
   - ✅ 其他 tag 显示为对应中文
2. 确认未映射的 tag：
   - ✅ 如果 tag 不在映射表，显示原始英文（不报错）

#### 4.5 板块删除验收

**在微信开发者工具中测试：**
1. 确认页面底部：
   - ✅ 没有"下周可以继续的一小步"卡片
   - ✅ 只有"刷新复盘"和"回到首页"按钮

#### 4.6 边界验收

**必须符合：**
- ✅ 无数据时显示友好提示
- ✅ 各板块数据正确对应后端 API 返回值
- ✅ 代码检查：JS/WXML/WXSS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
node --check apps\miniprogram\pages\weekly-report\index.js
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 本周复盘页面改造（T6-05）
  - 删除顶部冗长说明文案
  - 优化本周小变化4格：缩小宽度，居中文字
  - 修复高频场景显示：显示场景名+次数
  - 修复互动线索显示：tag 中文映射（general_support→一般支持）
  - 删除"下周可以继续的一小步"板块
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"本周复盘"章节更新：

```markdown
### 本周复盘页面

**验收结果：**
- ✅ 顶部说明简洁，无冗长文案
- ✅ 本周小变化4格缩小居中
- ✅ 高频场景显示场景名+次数
- ✅ 互动线索显示中文
- ✅ 已删除"下周一小步"板块
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-05 本周复盘页面改造
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：删除冗长文案 + 优化卡片 + 修复场景/线索显示 + 删除下周板块
- 关键决策：简化信息密度，提升可读性；tag 中文映射提升理解度
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的本周复盘页面截图
- [ ] 3. 修改 `apps/miniprogram/pages/weekly-report/index.wxml` 删除顶部长文案（第6行）
- [ ] 4. 修改 `index.wxml` 本周小变化4格的数据绑定（第44-63行）
- [ ] 5. 修改 `apps/miniprogram/pages/weekly-report/index.wxss` 的 `.stat-card` 样式（缩小居中）
- [ ] 6. 修改 `index.wxml` 高频场景显示逻辑（第83-91行，添加场景名）
- [ ] 7. 在 `apps/miniprogram/pages/weekly-report/index.js` 添加 `TAG_LABELS` 映射表
- [ ] 8. 修改 `index.js` 的 `formatPairs` 函数（添加 tag 映射参数）
- [ ] 9. 修改 `index.js` 的 `commonPatterns` 处理（第37行，传入 true）
- [ ] 10. 删除 `index.wxml` 的"下周一小步"板块（第115-118行）
- [ ] 11. 在微信开发者工具中测试本周复盘页面
- [ ] 12. 确认顶部简洁、4格缩小居中
- [ ] 13. 确认高频场景显示"场景名 X次"
- [ ] 14. 确认互动线索显示中文
- [ ] 15. 确认已删除"下周一小步"
- [ ] 16. 运行代码检查命令（JS 语法）
- [ ] 17. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 18. 截图验收结果（优化前后对比），提交给用户确认

---

### 七、注意事项

1. **tag 映射表完整性**：确保常见 tag 都有中文映射，未映射的显示原文不报错
2. **4格数据准确性**：使用后端返回的数组长度（`.length`），不使用可能不存在的 `_count` 字段
3. **高频场景格式**：显示为"场景名 X次"，不只显示数字
4. **代码风格**：保持与现有代码一致（缩进、命名、注释）
5. **测试完整性**：必须在微信开发者工具中实际测试，确认数据正确显示

---

**任务状态：** 待执行
**预计工时：** 2-2.5 小时（前端修改1.5h + 样式优化0.5h + 测试验收0.5h）
**优先级：** P1（核心功能页面，影响用户体验）

---

## T6-06：训练页面改造

> **【Claude订正 · 本节初稿多为"(推测)"，以下为准】**
> - **API**：`api.listCards()`（:347）/ `api.recommendCards()`（:351）；**无 `getTrainingCards`**（3.4 的 `loadAllCards` 内改成 `api.listCards()`）。
> - **训练卡共 34 张**（"20/12张"作废）；改文案聚焦核心 5 张即可。
> - **字段名**：`theory_background`→**`theory_source`**、`target_competency`→**`target_skill`**、`practice_tips` 不存在（用 `reflection_questions`）。3.5 的 JSON 示例按此替换；**别新造同义字段**。
> - **硬约束**：`theory_source/target_skill/reflection_questions/not_suitable_for` 为 required 不可删；`reflection_questions`≥2；`not_suitable_for` 须含"高风险/危机/安全/现实支持"之一。("前额叶/杏仁核"等不在禁用词，可用。)
> - **training 页是静态 `trainingStages`，不调 API**；候选卡在 `training-card`（`loadCards`→`listCards/recommendCards`）。`suitable_for[0]` 改多场景 join 可行。新手路径"图标"是文字 `<text class="starter-icon">先</text>`，删它即删该节点。

### 一、任务目标

优化训练页面，提升视觉层次和信息展示：
1. **顶部标题居中**："从先稳定自己开始"居中显示
2. **删除新手推荐路径图标**：左侧小图标去掉
3. **优化新手推荐3个板块**：缩小上下高度，内容居中，保持横向排列
4. **新增"其他训练卡"入口**：在阶段三下方，独立卡片区域，进入后显示所有训练卡列表
5. **优化训练卡详情页内容**：使用更结构化的专业表达
6. **优化"适用情境"展示**：显示多个场景，避免误解为只有一个

**核心变更：**
- 顶部文案居中对齐
- 新手推荐路径简化（去图标，缩小板块）
- 新增"其他训练卡"入口（34张卡片全展示）
- 训练卡详情页文案重构（更结构化）
- 适用情境改为多场景展示

---

### 二、前端代码审核结论

**现有代码：**
- `apps/miniprogram/pages/training/index.wxml` - 训练页面结构
- `apps/miniprogram/pages/training/index.wxss` - 训练页面样式
- `apps/miniprogram/pages/training-card/index.wxml` - 训练卡详情页
- `content/training_cards.json` - 训练卡数据（34张卡片）

**审核结论：**
- ✅ 后端有34张训练卡数据，全部启用
- ❌ 问题1：顶部标题左对齐（第4行）
- ❌ 问题2：新手推荐路径有图标（第52行附近）
- ❌ 问题3：新手推荐3个板块高度较大（需缩小）
- ❌ 问题4：缺少"其他训练卡"入口
- ❌ 问题5：训练卡详情页文案过于口语化
- ❌ 问题6：适用情境只显示一个（`suitable_for` 数组第一项）

---

### 三、详细实现方案

#### 3.1 顶部标题居中

**文件：`apps/miniprogram/pages/training/index.wxss`**

**查找 `.hero-title` 样式，添加居中：**

```css
.hero-title {
  color: var(--safe-title);
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center; /* 新增 */
}
```

同时确认 `.hero-copy` 也居中：

```css
.hero-copy {
  display: flex;
  flex-direction: column;
  align-items: center; /* 新增 */
  text-align: center; /* 新增 */
}
```

#### 3.2 删除新手推荐路径图标

**文件：`apps/miniprogram/pages/training/index.wxml`**

**修改位置：第51-62行（推测）**

**原代码（推测）：**
```xml
<view class="path-card">
  <view class="path-icon">图标</view>
  <text class="path-label">新手推荐路径</text>
  <text class="path-text">如果不知道从哪张卡开始，先按这三个小练习走一遍。</text>
</view>
```

**修改为：**
```xml
<view class="path-card">
  <text class="path-label">新手推荐路径</text>
  <text class="path-text">如果不知道从哪张卡开始，先按这三个小练习走一遍。</text>
</view>
```

**删除图标相关的样式（wxss）**

#### 3.3 优化新手推荐3个板块

**文件：`apps/miniprogram/pages/training/index.wxss`**

**修改板块样式（推测为 `.stage-preview-card` 或类似）：**

```css
.stage-preview-card {
  flex: 1;
  min-width: 180rpx;
  padding: 24rpx 16rpx; /* 原来可能是 32rpx 24rpx，缩小上下 */
  display: flex;
  flex-direction: column;
  align-items: center; /* 居中 */
  justify-content: center;
  text-align: center; /* 文字居中 */
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
}

.stage-preview-title {
  display: block;
  color: var(--safe-title);
  font-size: 28rpx;
  font-weight: 800;
  line-height: 1.3;
  text-align: center; /* 居中 */
  margin-bottom: 8rpx;
}

.stage-preview-text {
  display: block;
  color: var(--safe-text);
  font-size: 24rpx;
  line-height: 1.5;
  text-align: center; /* 居中 */
}
```

#### 3.4 新增"其他训练卡"入口

**文件：`apps/miniprogram/pages/training/index.wxml`**

**在阶段三区域后添加（约第120行附近）：**

```xml
<!-- 其他训练卡入口 -->
<view class="safe-section">
  <view class="other-cards-entry" bindtap="openAllCards">
    <view class="entry-copy">
      <text class="entry-title">查看更多训练卡</text>
      <text class="entry-subtitle">浏览全部 34 张训练卡，找到适合你的练习</text>
    </view>
    <text class="entry-arrow">›</text>
  </view>
</view>
```

**文件：`apps/miniprogram/pages/training/index.wxss`**

**添加样式：**

```css
.other-cards-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 24rpx;
  border: 2rpx solid var(--safe-primary);
  border-radius: var(--safe-radius-md);
  background: var(--safe-primary-pale);
}

.entry-copy {
  flex: 1;
}

.entry-title {
  display: block;
  color: var(--safe-primary-deep);
  font-size: 30rpx;
  font-weight: 850;
  line-height: 1.3;
  margin-bottom: 8rpx;
}

.entry-subtitle {
  display: block;
  color: var(--safe-text);
  font-size: 24rpx;
  line-height: 1.5;
}

.entry-arrow {
  flex: 0 0 auto;
  color: var(--safe-primary);
  font-size: 48rpx;
  font-weight: 300;
}
```

**文件：`apps/miniprogram/pages/training/index.js`**

**添加方法（约第200行附近）：**

```javascript
openAllCards() {
  wx.navigateTo({
    url: "/pages/training-card/index?showAll=true",
  });
},
```

**文件：`apps/miniprogram/pages/training-card/index.js`**

**修改 `onLoad` 方法，支持显示全部卡片：**

```javascript
onLoad(options) {
  const showAll = options.showAll === "true";
  if (showAll) {
    this.loadAllCards();
  } else {
    this.loadCards(options);
  }
},

async loadAllCards() {
  this.setData({ loading: true, errorMessage: "" });

  try {
    const result = await api.getTrainingCards();
    
    if (!result.ok) {
      this.setData({
        loading: false,
        errorMessage: "无法加载训练卡列表",
      });
      return;
    }

    const cards = (result.data.cards || []).map((card) => ({
      id: card.id,
      title: card.title,
      purpose: card.purpose,
      duration: card.duration_minutes,
      tagsText: (card.tags || []).join("、"),
      todayGoal: card.purpose, // 使用 purpose 作为目标
      suitableScenarios: (card.suitable_for || []).join("、"), // 多场景
    }));

    this.setData({
      loading: false,
      cards,
    });
  } catch (err) {
    this.setData({
      loading: false,
      errorMessage: "加载失败，请重试",
    });
  }
},
```

#### 3.5 优化训练卡详情页内容（更结构化表达）

**文件：`content/training_cards.json`**

**需要重写部分训练卡的字段，使其更结构化。以下是改写示例：**

**原数据（情绪识别卡）：**
```json
{
  "id": "emotion_naming",
  "title": "情绪识别卡：先命名情绪",
  "purpose": "帮助家长在回应孩子前，先识别自己和孩子的情绪。",
  "steps": [
    "暂停 3 秒，先不急着讲道理。",
    "在心里说出自己的情绪：我现在是着急、失望，还是害怕？",
    "再尝试命名孩子的情绪：孩子可能是委屈、害怕，还是挫败？",
    "用一句非评判的话开头：我看到你现在很难受。"
  ],
  "example": "我看到你这次数学没考好后很沮丧，我也有点着急。我们先把发生了什么说清楚。"
}
```

**改为（更结构化）：**
```json
{
  "id": "emotion_naming",
  "title": "情绪识别卡：先命名情绪",
  "purpose": "通过暂停反应、识别情绪的方式，帮助家长在高情绪强度情境下建立觉察窗口，为后续有效沟通创造条件。",
  "theory_background": "基于情绪调节理论（Emotion Regulation Theory），情绪命名是情绪觉察的第一步，能够激活前额叶皮层对情绪的认知加工，降低杏仁核的自动化反应。",
  "target_competency": "情绪觉察能力（Emotional Awareness）",
  "steps": [
    "【暂停】当注意到情绪激活信号时，暂停 3 秒，不立即做出言语或行为反应。",
    "【自我识别】在内心命名自己的情绪状态：着急、失望、愤怒、担忧或其他。",
    "【他人识别】尝试推测孩子当前的情绪：委屈、害怕、挫败、愤怒或其他。",
    "【非评判开场】用一句描述性、非评判的话开启对话，如'我看到你现在很难受'。"
  ],
  "example": "【情境】孩子数学考试成绩不理想。\n【应用】我看到你这次数学没考好后很沮丧（识别孩子情绪），我也有点着急（识别自己情绪）。我们先把发生了什么说清楚（非评判开场）。",
  "practice_tips": [
    "初次练习时，可以先在纸上写下情绪词，帮助具体化。",
    "情绪词汇表可参考：着急、失望、愤怒、担忧、无力、内疚、害怕等。",
    "如果无法准确命名，可以用'不舒服''有压力'等宽泛词汇替代。"
  ]
}
```

**需要Codex按此模式重写以下核心训练卡：**
1. `emotion_naming` - 情绪识别卡
2. `cognitive_flexibility` - 认知灵活化卡
3. `pause_3_seconds` - 3秒暂停卡
4. `body_awareness` - 身体觉察卡
5. `validation_first` - 先确认卡

**其他训练卡保持原样，优先级低。**

#### 3.6 优化"适用情境"展示（多场景）

**文件：`apps/miniprogram/pages/training-card/index.wxml`**

**修改位置：约第57行**

**原代码（推测）：**
```xml
<view class="scenario-box">
  <text class="scenario-label">适用情境：</text>
  <text class="scenario-text">{{card.suitableScenario}}</text>
</view>
```

**修改为：**
```xml
<view class="scenario-box">
  <text class="scenario-label">适用情境</text>
  <text class="scenario-text">{{card.suitableScenarios}}</text>
</view>
```

**文件：`apps/miniprogram/pages/training-card/index.js`**

**修改数据处理（约第40-50行附近）：**

**原代码（推测）：**
```javascript
suitableScenario: card.suitable_for[0] || "多种情境",
```

**修改为：**
```javascript
suitableScenarios: (card.suitable_for || []).join("、") || "多种亲子互动情境",
```

**样式优化（让多个情境换行显示）：**

```css
.scenario-box {
  padding: 20rpx;
  border-left: 4rpx solid var(--safe-primary);
  border-radius: var(--safe-radius-sm);
  background: var(--safe-primary-pale);
  margin-bottom: 24rpx;
}

.scenario-label {
  display: block;
  color: var(--safe-primary-deep);
  font-size: 24rpx;
  font-weight: 800;
  margin-bottom: 12rpx;
}

.scenario-text {
  display: block;
  color: var(--safe-text);
  font-size: 26rpx;
  line-height: 1.7;
  word-wrap: break-word; /* 支持长文本换行 */
}
```

---

### 四、验收标准

#### 4.1 顶部标题验收
- ✅ "从先稳定自己开始"居中显示

#### 4.2 新手推荐路径验收
- ✅ 左侧图标已删除
- ✅ 3个板块高度缩小（padding 减小）
- ✅ 板块内容（标题+文字）居中对齐

#### 4.3 其他训练卡入口验收
- ✅ 在阶段三下方显示独立卡片区域
- ✅ 显示"查看更多训练卡"+"浏览全部34张训练卡"
- ✅ 点击进入训练卡列表页，显示所有34张卡片

#### 4.4 训练卡详情页验收
- ✅ 核心5张卡片使用结构化表达（purpose/theory_background/target_competency/practice_tips）
- ✅ 文案专业化，使用心理学术语

#### 4.5 适用情境验收
- ✅ 显示多个场景，用"、"分隔
- ✅ 如"家长催促前、亲子冲突后、孩子情绪激动时"

---

### 五、完成后更新文档

**1. 更新开发日志**
**2. 更新 UI 验收清单**
**3. 更新 Claude 使用记录**

---

### 六、Codex 执行检查清单

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的训练页面截图
- [ ] 3. 修改 `.hero-title` 和 `.hero-copy` 样式（居中）
- [ ] 4. 删除新手推荐路径的图标元素
- [ ] 5. 修改新手推荐3个板块样式（缩小padding，居中）
- [ ] 6. 在阶段三后添加"其他训练卡"入口结构
- [ ] 7. 添加"其他训练卡"入口样式
- [ ] 8. 在 `training/index.js` 添加 `openAllCards` 方法
- [ ] 9. 在 `training-card/index.js` 添加 `loadAllCards` 方法
- [ ] 10. 重写 5 张核心训练卡的 JSON 数据（更结构化）
- [ ] 11. 修改适用情境数据处理（显示多场景）
- [ ] 12. 修改适用情境样式（支持换行）
- [ ] 13. 在微信开发者工具中测试训练页面
- [ ] 14. 测试"其他训练卡"入口跳转
- [ ] 15. 测试训练卡详情页新文案
- [ ] 16. 测试适用情境多场景显示
- [ ] 17. 更新 3 个文档
- [ ] 18. 截图验收结果

---

**任务状态：** 待执行
**预计工时：** 3-4 小时（文案重构1.5h + 前端修改1h + 样式优化0.5h + 测试1h）
**优先级：** P1（核心功能页面）

---

## T6-07：课程页面重新设计

> **【Claude订正 · 保留从 GitHub 拉取（用户决策 2026-07-01），但必须补以下防护】**
> - **微信合法域名**：外链封面/视频在真机/体验版需在「微信公众平台→开发管理→服务器域名」配置 `downloadFile` 合法域名，否则图片空白。开发者工具 `urlCheck:false` 能显示是假象、不代表真机可用。**建议把封面下载到本地 `assets/` 或转 Base64**，减少外链依赖。
> - **内容/版权/伦理**（心理健康产品红线）：GitHub 第三方课程须 ① 核对开源协议（标注来源/许可，避开不可商用或强传染协议）；② 人工过内容质量与边界（不得含诊断/治疗承诺，命中禁用词的删改）；③ 每门课加"内容来源 + 非诊断/非治疗"声明。**不可整包导入未审内容**。
> - **现状**：无 `content/courses.json`，`course/index.js` 是硬编码 5 门课、`openCourse` 仅弹 toast。本节实为"新建数据层 + 重写页面"，不是改已有 JSON。

### 一、任务目标

完全重新设计课程页面，打造吸引人的学习体验：
1. **全新视觉设计**：参考优秀的教育类 App 设计
2. **课程内容来源**：从 GitHub 开源社区搜索心理学、家庭教育相关课程数据
3. **支持分类**：按训练卡阶段分类（阶段一/阶段二/阶段三）
4. **支持搜索和筛选**：标题搜索、分类筛选、难度筛选
5. **课程详情页**：完整的课程信息展示
6. **学习进度跟踪**：标记已完成、学习中、未开始
7. **完成标记**：支持打卡完成

**核心变更：**
- 删除现有课程页面代码，完全重写
- 从 GitHub 获取开源课程数据
- 实现完整的课程学习系统

---

### 二、GitHub 课程数据搜索

**Codex 需要执行：**

1. 搜索 GitHub 上的开源课程项目：
   - 关键词：parenting psychology, family education, emotional intelligence, child development
   - 筛选条件：有结构化课程数据（JSON/Markdown）
   - 推荐仓库：psychology-courses, parenting-guides, family-education-resources

2. 提取课程数据结构：
   ```json
   {
     "id": "course_001",
     "title": "情绪管理基础课程",
     "category": "阶段一",
     "description": "帮助家长理解情绪的本质和调节方法",
     "duration": "30分钟",
     "difficulty": "入门",
     "instructor": "李明",
     "cover_image": "https://...",
     "lessons": [
       {
         "id": "lesson_001",
         "title": "什么是情绪",
         "duration": "10分钟",
         "content_type": "video",
         "content_url": "https://..."
       }
     ],
     "tags": ["情绪管理", "基础知识"],
     "status": "not_started"
   }
   ```

3. 整理成 `content/courses.json`

---

### 三、前端设计方案

#### 3.1 课程列表页设计

**参考设计风格：**
- 网易云课堂
- 得到 App
- Coursera

**布局结构：**
```
[搜索框]
[分类标签] 全部 | 阶段一 | 阶段二 | 阶段三
[筛选器] 难度 | 时长 | 讲师

[课程卡片]
- 封面图
- 标题
- 描述
- 时长 | 难度
- 学习进度条
- [开始学习] 按钮
```

**文件：`apps/miniprogram/pages/course/index.wxml`**

```xml
<view class="safe-page course-page">
  
  <!-- 搜索栏 -->
  <view class="search-bar">
    <input class="search-input" placeholder="搜索课程..." bindinput="onSearchInput" />
  </view>

  <!-- 分类标签 -->
  <view class="category-tabs">
    <button 
      wx:for="{{categories}}" 
      wx:key="key"
      class="category-tab {{activeCategory === item.key ? 'active' : ''}}"
      data-key="{{item.key}}"
      bindtap="switchCategory"
    >
      {{item.label}}
    </button>
  </view>

  <!-- 筛选器 -->
  <view class="filter-bar">
    <button class="filter-btn" bindtap="showDifficultyFilter">
      难度 {{difficultyFilter ? ': ' + difficultyFilter : ''}}
    </button>
    <button class="filter-btn" bindtap="showDurationFilter">
      时长 {{durationFilter ? ': ' + durationFilter : ''}}
    </button>
  </view>

  <!-- 课程列表 -->
  <view class="course-list">
    <view wx:for="{{courses}}" wx:key="id" class="course-card" bindtap="openCourse" data-id="{{item.id}}">
      <image class="course-cover" src="{{item.cover_image}}" mode="aspectFill" />
      <view class="course-info">
        <text class="course-title">{{item.title}}</text>
        <text class="course-desc">{{item.description}}</text>
        <view class="course-meta">
          <text class="course-duration">{{item.duration}}</text>
          <text class="course-difficulty">{{item.difficulty}}</text>
        </view>
        <progress class="course-progress" percent="{{item.progress}}" />
        <button class="course-action">
          {{item.status === 'completed' ? '已完成' : item.status === 'learning' ? '继续学习' : '开始学习'}}
        </button>
      </view>
    </view>
  </view>

</view>
```

#### 3.2 课程详情页设计

**文件：`apps/miniprogram/pages/course-detail/index.wxml`**

```xml
<view class="safe-page course-detail-page">
  
  <!-- 课程头部 -->
  <view class="course-header">
    <image class="course-banner" src="{{course.cover_image}}" mode="aspectFill" />
    <view class="course-header-info">
      <text class="course-title-large">{{course.title}}</text>
      <text class="course-instructor">讲师：{{course.instructor}}</text>
      <view class="course-stats">
        <text>{{course.duration}}</text>
        <text>{{course.difficulty}}</text>
        <text>{{course.lessons.length}} 课时</text>
      </view>
    </view>
  </view>

  <!-- 课程描述 -->
  <view class="course-section">
    <text class="section-title">课程介绍</text>
    <text class="course-description">{{course.description}}</text>
  </view>

  <!-- 课程目录 -->
  <view class="course-section">
    <text class="section-title">课程目录</text>
    <view wx:for="{{course.lessons}}" wx:key="id" class="lesson-item" bindtap="openLesson" data-id="{{item.id}}">
      <view class="lesson-number">{{index + 1}}</view>
      <view class="lesson-info">
        <text class="lesson-title">{{item.title}}</text>
        <text class="lesson-duration">{{item.duration}}</text>
      </view>
      <view class="lesson-status">
        {{item.completed ? '✓' : ''}}
      </view>
    </view>
  </view>

  <!-- 开始学习按钮 -->
  <view class="action-bar">
    <button class="primary-button" bindtap="startCourse">开始学习</button>
  </view>

</view>
```

---

### 四、验收标准

#### 4.1 课程数据验收
- ✅ 从 GitHub 获取至少 10 门课程数据
- ✅ 课程数据结构完整（包含所有必需字段）
- ✅ 按阶段一/阶段二/阶段三分类

#### 4.2 课程列表验收
- ✅ 搜索功能正常（标题搜索）
- ✅ 分类筛选正常（全部/阶段一/阶段二/阶段三）
- ✅ 难度筛选正常（入门/进阶/高级）
- ✅ 时长筛选正常（<15分钟/15-30分钟/>30分钟）
- ✅ 课程卡片美观，信息清晰

#### 4.3 课程详情验收
- ✅ 课程信息完整展示
- ✅ 课程目录可点击
- ✅ 支持标记完成

#### 4.4 学习进度验收
- ✅ 学习进度正确记录（本地存储）
- ✅ 进度条正确显示
- ✅ 已完成课程显示✓标记

---

### 五、Codex 执行检查清单

- [ ] 1. 搜索 GitHub 开源课程数据
- [ ] 2. 整理课程数据到 `content/courses.json`
- [ ] 3. 删除现有课程页面代码
- [ ] 4. 创建新的课程列表页（wxml/js/wxss/json）
- [ ] 5. 创建课程详情页（wxml/js/wxss/json）
- [ ] 6. 实现搜索功能
- [ ] 7. 实现分类筛选
- [ ] 8. 实现难度/时长筛选
- [ ] 9. 实现学习进度跟踪（本地存储）
- [ ] 10. 实现完成标记功能
- [ ] 11. 在微信开发者工具中测试
- [ ] 12. 更新文档
- [ ] 13. 截图验收

---

**任务状态：** 待执行
**预计工时：** 6-8 小时（数据搜索2h + 页面开发4h + 功能实现2h）
**优先级：** P2（新功能开发，非核心链路）

---

## T6-08："我的"页面全量改造

### 任务概述

**优先级：** P1  
**预计工时：** 8-10 小时  
**执行方式：** Codex 在 Claude 已提供的代码基础上继续完成

---

### 一、任务目标

全量改造"我的"页面，实现用户信息展示、消息系统、记录统计和安全支持：

1. **样式改造**：参考用户提供的第3张图片的简洁列表布局，保留现有配色
2. **用户信息动态化**：实现微信登录，显示微信头像和昵称
3. **统计数据真实化**：连续打卡天数、本周记录数从后端动态获取
4. **新增消息系统**：首页顶部消息入口 + 消息列表页 + 消息详情页
5. **人工督导反馈**：督导回复推送到消息列表
6. **删除冗余内容**：
   - 去掉绿框内容
   - 删除所有图案标签（"周""反""急""助"等）
   - 去掉"专业资源边界"前端入口
7. **紧急安全指引**：新增危机干预文字指引（200-300字，带步骤编号，包含蝴蝶拍等方法）

---

### 二、Claude 已提供的代码

#### 2.1 后端代码（已完成）

**以下代码 Codex 可以直接使用或参考修改：**

##### 微信登录接口
- 文件：`backend/routes/auth.py`
- 接口：`POST /api/auth/wechat-login`
- 功能：接收微信 code，换取 openid，创建或查询用户

##### 用户统计接口
- 文件：`backend/routes/profile.py`
- 接口：`GET /api/profile/stats`
- 功能：返回连续打卡天数和本周记录数
- 算法：`calculate_consecutive_days()` - 计算连续打卡天数

##### 消息系统接口
- 文件：`backend/routes/messages.py`（新建）
- 接口：
  - `POST /api/messages` - 创建消息
  - `GET /api/messages` - 获取消息列表（含未读数）
  - `GET /api/messages/<id>` - 获取消息详情并标记已读
  - `POST /api/messages/<id>/mark-read` - 标记已读

##### 数据库表
- `messages` 表结构已在 `backend/models.py` 中定义

##### 督导反馈推送
- 修改 `backend/routes/supervision.py`，督导回复时创建消息

#### 2.2 前端代码（已完成）

**以下代码 Codex 可以直接使用或参考修改：**

##### 首页顶部消息入口
- 文件：`apps/miniprogram/pages/home/index.wxml`
- 位置：顶部标题栏右侧
- 显示：🔔图标 + 未读数气泡
- 逻辑：`apps/miniprogram/pages/home/index.js` 中的 `loadUnreadCount()` 和 `openMessages()`

##### 消息列表页
- 目录：`apps/miniprogram/pages/messages/`
- 文件：`index.wxml`, `index.js`, `index.wxss`, `index.json`
- 功能：显示消息列表，未读消息高亮

##### 消息详情页
- 目录：`apps/miniprogram/pages/message-detail/`
- 文件：`index.wxml`, `index.js`, `index.wxss`, `index.json`
- 功能：显示完整消息内容

##### "我的"页面改造
- 文件：`apps/miniprogram/pages/profile/index.wxml`
- 样式：参考用户提供的第3张图片（简洁列表布局）
- 删除：所有图案标签（"周""反""急""助"等）

---

### 三、Codex 需要完成的部分

#### 3.1 紧急安全指引内容（未完成）

**文件：`apps/miniprogram/pages/emergency-guide/index.wxml`（新建）**

**内容要求：**
- 长度：200-300字简短版
- 格式：带步骤编号的指引
- 必须包含：蝴蝶拍技术、5-4-3-2-1接地法、深呼吸练习
- 必须包含：紧急联系方式（120、110、心理援助热线）

**建议内容结构：**

```xml
<view class="safe-page emergency-page">
  
  <view class="emergency-header">
    <text class="emergency-title">紧急安全指引</text>
    <text class="emergency-subtitle">在紧急情况下可以做些什么</text>
  </view>

  <view class="alert-card alert-important">
    <text class="alert-title">⚠️ 重要提醒</text>
    <text class="alert-text">本指引仅作为应急参考，不替代专业危机干预。如遇生命安全紧急情况，请立即拨打120或110。</text>
  </view>

  <view class="guide-section">
    <text class="guide-title">一、即时自我安抚方法</text>
    
    <view class="guide-item">
      <text class="guide-number">1. 蝴蝶拍技术</text>
      <text class="guide-text">双臂交叉放在胸前，左右手轮流轻拍对侧肩膀，每次约10-15下。这个动作可以帮助情绪降温。</text>
    </view>
    
    <view class="guide-item">
      <text class="guide-number">2. 5-4-3-2-1接地法</text>
      <text class="guide-text">说出5样你能看到的东西、4样你能触摸的、3样你能听到的、2样你能闻到的、1样你能尝到的。帮助你回到当下。</text>
    </view>
    
    <view class="guide-item">
      <text class="guide-number">3. 深呼吸练习</text>
      <text class="guide-text">吸气4秒，屏住7秒，呼气8秒。重复3-5次，帮助身体放松。</text>
    </view>
  </view>

  <view class="guide-section">
    <text class="guide-title">二、紧急联系方式</text>
    <view class="contact-list">
      <text class="contact-item">• 急救电话：120</text>
      <text class="contact-item">• 报警电话：110</text>
      <text class="contact-item">• 心理援助热线：400-161-9995（24小时）</text>
      <text class="contact-item">• 希望24热线：400-161-9995</text>
    </view>
  </view>

  <view class="guide-footer">
    <text class="guide-footer-text">如果您或孩子有自杀或自伤想法，请立即联系身边可信赖的人、学校老师或拨打上述热线。</text>
  </view>

</view>
```

**对应的样式和逻辑文件也需要创建。**

#### 3.2 紧急帮助说明页（未完成）

**文件：`apps/miniprogram/pages/emergency-resources/index.wxml`（新建）**

**内容：解释可用的现实资源**

#### 3.3 完善 API 调用

**文件：`apps/miniprogram/services/api.js`**

**需要添加的 API 方法：**

```javascript
// 微信登录
wechatLogin(code, nickname, avatarUrl) {
  return request("POST", API_ENDPOINTS.wechatLogin, {
    code,
    nickname,
    avatar_url: avatarUrl,
  });
},

// 获取用户统计
getUserStats(userId) {
  return request("GET", API_ENDPOINTS.userStats + queryString({ user_id: userId }));
},

// 消息相关
getMessages(params = {}) {
  return request("GET", API_ENDPOINTS.messages + queryString(params));
},

getMessage(messageId) {
  return request("GET", `${API_ENDPOINTS.messages}/${messageId}`);
},

markMessageRead(messageId) {
  return request("POST", `${API_ENDPOINTS.messages}/${messageId}/mark-read`);
},
```

**添加 API 端点常量：**

```javascript
// shared/constants/api.ts
wechatLogin: "/api/auth/wechat-login",
userStats: "/api/profile/stats",
messages: "/api/messages",
```

#### 3.4 "我的"页面逻辑完善

**文件：`apps/miniprogram/pages/profile/index.js`**

**需要实现的方法：**

```javascript
data: {
  userInfo: {},
  userStats: {},
  loading: true,
},

onLoad() {
  this.loadUserInfo();
  this.loadUserStats();
},

async loadUserInfo() {
  // 从本地存储获取用户信息
  // 或调用 API 获取
},

async loadUserStats() {
  try {
    const result = await api.getUserStats();
    if (result.ok) {
      this.setData({
        userStats: {
          check_in_days: result.data.check_in_days,
          weekly_record_count: result.data.weekly_record_count,
        },
      });
    }
  } catch (err) {
    console.error("loadUserStats error:", err);
  }
},

// 各个跳转方法
openWeeklyReport() {
  wx.navigateTo({ url: "/pages/weekly-report/index" });
},

openFeedbackHistory() {
  // 跳转到反馈历史页
},

openTrainingHistory() {
  // 跳转到训练记录页
},

openAssessmentHistory() {
  // 跳转到测评记录页
},

openSupervision() {
  wx.navigateTo({ url: "/pages/supervision/index" });
},

openSupervisionGuide() {
  // 跳转到专业资源说明页
},

openEmergencyGuide() {
  wx.navigateTo({ url: "/pages/emergency-guide/index" });
},

openEmergencyResources() {
  wx.navigateTo({ url: "/pages/emergency-resources/index" });
},

openBoundary() {
  // 跳转到知情与边界页
},

openPrivacy() {
  wx.navigateTo({ url: "/pages/privacy/index" });
},
```

#### 3.5 微信登录流程（前端部分）

**需要在小程序启动时或"我的"页面首次加载时触发：**

```javascript
// app.js 或 profile/index.js
async doWechatLogin() {
  try {
    // 获取微信登录凭证
    const loginRes = await wx.login();
    const code = loginRes.code;
    
    // 获取用户信息（需要用户授权）
    const userInfoRes = await wx.getUserProfile({
      desc: '用于完善用户资料'
    });
    
    const { nickName, avatarUrl } = userInfoRes.userInfo;
    
    // 发送到后端
    const result = await api.wechatLogin(code, nickName, avatarUrl);
    
    if (result.ok) {
      // 保存用户信息到本地
      wx.setStorageSync('user_id', result.data.user_id);
      wx.setStorageSync('user_info', {
        nickname: result.data.nickname,
        avatar_url: result.data.avatar_url,
      });
      
      this.setData({
        userInfo: {
          nickname: result.data.nickname,
          avatar_url: result.data.avatar_url,
        },
      });
    }
  } catch (err) {
    console.error("wechatLogin error:", err);
  }
}
```

#### 3.6 注册新页面路由

**文件：`apps/miniprogram/app.json`**

**在 `pages` 数组中添加：**

```json
"pages/messages/index",
"pages/message-detail/index",
"pages/emergency-guide/index",
"pages/emergency-resources/index"
```

#### 3.7 后端蓝图注册

**文件：`backend/app.py`**

**确保已注册：**

```python
from routes.messages import bp as messages_bp

app.register_blueprint(messages_bp)
```

#### 3.8 数据库表创建

**文件：`backend/models.py`**

**确保已添加 `messages` 表定义到 `SCHEMA` 列表。**

**确保 `users` 表有以下字段：**
- `wechat_openid`
- `avatar_url`

**使用 `ensure_column` 添加：**

```python
# backend/database.py 的 ensure_schema_columns() 中
"users": [
    ("wechat_openid", "TEXT"),
    ("avatar_url", "TEXT"),
],
"messages": [],  # 已在 SCHEMA 中定义完整
```

---

### 四、验收标准

#### 4.1 微信登录验收
- [ ] 用户首次进入可以授权登录
- [ ] 登录后显示微信昵称和头像
- [ ] 用户信息保存到本地存储和后端数据库

#### 4.2 用户统计验收
- [ ] "连续打卡X天"显示正确（情绪日记+训练打卡）
- [ ] "本周有X条记录"显示正确
- [ ] 数据从后端动态获取，非硬编码

#### 4.3 消息系统验收
- [ ] 首页顶部显示消息图标
- [ ] 有未读消息时显示红色数字气泡
- [ ] 点击进入消息列表页
- [ ] 消息列表显示正确，未读消息高亮
- [ ] 点击消息进入详情页
- [ ] 查看消息后自动标记已读

#### 4.4 督导反馈验收
- [ ] 督导回复后，消息推送到用户消息列表
- [ ] 用户收到"老师回复了您的补充内容"通知
- [ ] 点击消息可查看督导回复内容

#### 4.5 "我的"页面样式验收
- [ ] 页面布局参考第3张图片（简洁列表）
- [ ] 删除所有图案标签（"周""反""急""助"等）
- [ ] 删除绿框内容
- [ ] 删除"专业资源边界"入口
- [ ] 所有菜单项文字居中

#### 4.6 紧急安全指引验收
- [ ] 内容长度200-300字
- [ ] 包含蝴蝶拍技术说明
- [ ] 包含5-4-3-2-1接地法
- [ ] 包含深呼吸练习
- [ ] 包含紧急联系方式（120/110/热线）
- [ ] 带步骤编号，结构清晰

---

### 五、Codex 执行检查清单

**Codex 请按以下顺序执行：**

#### 阶段一：后端实现（3-4h）

- [ ] 1. 在 `backend/models.py` 添加 `messages` 表定义
- [ ] 2. 在 `backend/models.py` 确保 `users` 表有 `wechat_openid` 和 `avatar_url` 字段
- [ ] 3. 创建 `backend/routes/messages.py`，实现消息 CRUD 接口
- [ ] 4. 在 `backend/routes/auth.py` 实现微信登录接口
- [ ] 5. 在 `backend/routes/profile.py` 实现用户统计接口
- [ ] 6. 修改 `backend/routes/supervision.py`，督导回复时创建消息
- [ ] 7. 在 `backend/app.py` 注册 messages_bp 蓝图
- [ ] 8. 启动后端，测试 API 接口

#### 阶段二：前端实现（4-5h）

- [ ] 9. 在 `shared/constants/api.ts` 添加新端点常量
- [ ] 10. 在 `apps/miniprogram/services/api.js` 添加 API 方法
- [ ] 11. 修改 `apps/miniprogram/pages/home/index.wxml` 添加消息图标
- [ ] 12. 修改 `apps/miniprogram/pages/home/index.js` 实现 `loadUnreadCount` 和 `openMessages`
- [ ] 13. 创建消息列表页（`pages/messages/`）
- [ ] 14. 创建消息详情页（`pages/message-detail/`）
- [ ] 15. 改造"我的"页面（`pages/profile/`）- 样式参考第3张图
- [ ] 16. 实现"我的"页面逻辑（用户信息+统计数据）
- [ ] 17. 创建紧急安全指引页（`pages/emergency-guide/`）
- [ ] 18. 创建紧急帮助说明页（`pages/emergency-resources/`）
- [ ] 19. 在 `app.json` 注册新页面路由
- [ ] 20. 实现微信登录流程

#### 阶段三：测试验收（1-2h）

- [ ] 21. 测试微信登录（获取头像和昵称）
- [ ] 22. 测试用户统计数据显示
- [ ] 23. 测试消息系统（创建消息→列表显示→查看详情→标记已读）
- [ ] 24. 测试督导反馈推送
- [ ] 25. 测试"我的"页面所有跳转
- [ ] 26. 测试紧急安全指引内容完整性
- [ ] 27. 检查所有图案标签已删除
- [ ] 28. 检查样式符合第3张图布局
- [ ] 29. 运行代码检查（JS/WXML 语法）
- [ ] 30. 截图验收结果

---

### 六、注意事项

#### 6.1 微信登录配置

**需要配置环境变量：**

```bash
# .env 文件
WECHAT_APPID=你的小程序AppID
WECHAT_SECRET=你的小程序Secret
```

#### 6.2 连续打卡天数算法

**逻辑：**
- 从今天开始倒推
- 如果当天有记录（`emotion_diaries` 或 `checkins` 任一），计数+1
- 继续检查前一天
- 直到遇到某天没记录，停止

#### 6.3 本周记录数定义

**本周：** 从本周一到本周日  
**记录数：** `emotion_diaries` 表记录数 + `checkins` 表记录数

#### 6.4 消息类型

**当前只支持：** `supervision_feedback`（督导反馈）  
**未来可扩展：** 系统通知、训练提醒等

#### 6.5 图案标签删除

**需要删除的图案：**
- "周"（周报入口）
- "反"（历次反馈）
- "练"（训练记录）
- "测"（测评记录）
- "督"（人工督导）
- "询"（专业资源说明）
- "急"（紧急安全指引）
- "助"（紧急帮助说明）
- "知"（知情与边界）
- "隐"（隐私说明）

**改为：** 纯文字菜单项，文字居中

---

### 七、完成后更新文档

**1. 更新开发日志**

```markdown
## 2026-06-30
- "我的"页面全量改造（T6-08）
  - 实现微信登录，显示用户头像和昵称
  - 新增消息系统（列表+详情+未读提醒）
  - 用户统计动态化（连续打卡天数+本周记录数）
  - 督导反馈推送到消息列表
  - 样式改造：简洁列表布局，删除图案标签
  - 新增紧急安全指引（含蝴蝶拍等方法）
```

**2. 更新 API 文档**

添加新接口文档：
- `POST /api/auth/wechat-login`
- `GET /api/profile/stats`
- 消息相关接口

**3. 更新数据库文档**

添加 `messages` 表说明

**4. 更新 Claude 使用记录**

```markdown
### T6-08 "我的"页面全量改造
- 会话链接：（补充）
- 完成时间：2026-06-30
- 交付内容：微信登录+消息系统+用户统计+样式改造+安全指引
- 关键决策：Claude 提供代码框架，Codex 完成实现和集成
```

---

### 八、问题与支持

**如果 Codex 遇到以下问题：**

1. **微信登录接口调用失败**：检查 AppID 和 Secret 配置
2. **连续打卡天数计算不准**：检查日期格式和数据库查询逻辑
3. **消息未推送**：检查督导回复接口是否正确调用消息创建
4. **样式不符合第3张图**：参考图片的简洁列表布局，使用纯白背景+灰色分隔线

**可随时向 Claude 反馈问题，Claude 会协助调整。**

---

**任务状态：** 待执行  
**优先级：** P1  
**预计工时：** 8-10 小时

---

**Codex 可以在 Claude 提供的代码基础上开始执行了！** ✅

---

# 任务七：四层一致性审查与修复（API契约 / Flask后端 / React Web / SQLite·MySQL）

> 创建时间：2026-07-01｜来源：Claude 四路并行核实审查（Explore over `d:\codex\workspace\safehome1.0`）
> 基准（最新进度）：**量表录入**——2026-06-29 worksheet 构建/后端 API/shared/小程序链路已落地，已入库 `assessment_worksheets`（27 份，16 启用），后台 admin CRUD 后端已实现；**聚类画像**——2026-06-29~30 已生成 7 个产品候选模型 + 落点接口 `GET /api/assessment-results/<id>/profile-position` + 小程序 Canvas + Web ECharts。
> 性质：**对已实现部分做一致性修复与补齐**，不是从零开发。多条为两路 agent 交叉确认。
> 优先级：**P0**=数据损坏/画像不可用/后台缺功能；**P1**=契约不一致/健壮性；**P2**=清理与统一。

## 优先级总览

| 子任务 | 层 | 核心 | 优先级 |
|---|---|---|---|
| T7-01 | 后端+DB | 画像落点链路打通（cluster0空串 / scale_id兜底 / 回填 / 题号对齐 / 交叉校验） | **P0** |
| T7-02 | 契约+Web | 后台量表管理（admin worksheet CRUD 端点+类型+Web 页面） | **P0** |
| T7-03 | 契约+Web+小程序 | 画像落点字段补齐（strength_note / small_step / display_name） | P1 |
| T7-04 | 后端 | 落点接口健壮性（GET 回填 / 置信度阈值 / model 归属校验 / list 规范化） | P1 |
| T7-05 | DB | 索引 / REAL→DOUBLE / 健康检查 / 白名单 | P1 |
| T7-06 | 后端+小程序 | 遗留统一（学生画像去硬编码 / 端点漂移 / review_status / worksheet 下线） | P2 |
| T7-07 | — | 验收 | — |

---

## T7-01：聚类画像落点链路打通（P0｜后端 + DB）

落点链路 `scores → model → 落点 → 接口` 当前**端到端未真正打通**，7 个产品模型里约 4 个对用户恒不可用，且簇 0 落点静默损坏。

| # | 问题 | 文件:行 | 改法 |
|---|---|---|---|
| 1 | **`cluster_id=0` 写成空串**（簇从 0 编号的 PRFQ/SCS 高频命中；后端+DB 两路确认）。列将统一为 **INTEGER**（见 T7-05#5） | `backend/routes/assessments.py:386` | `cid=(position.get("position") or {}).get("cluster_id"); cluster_val = None if cid is None else int(cid)` —— None 安全、不再 `... or ""` 短路丢 0；存 int |
| 2 | `_choose_model` 自动兜底**只按 `worksheet_id` 匹配**，4/7 模型 `worksheet_id=None` 永远选不中 | `backend/services/assessment_profile_service.py:58-62` | 兜底候选改 `model.get("worksheet_id")==wid or model.get("scale_id")==wid`；hplp 有两个模型共享 scale_id，需指定保留哪个或给不同 worksheet_id |
| 3 | worksheet 普遍缺 `profile_model_id`、模型普遍缺 `worksheet_id`，build 脚本不回填 | `backend/scripts/build_worksheets.py:149` | build 阶段加载 `content/profiles`，按 scale_id/worksheet_id 反查回填 worksheet 的 `profile_model_id`（让链路在静态内容层即连通） |
| 4 | `rsca_adolescent_resilience` 模型 23 题号与 worksheet `questions[].id` **0/23 匹配**，即便选中也必抛"题项不足" | `content/profiles/*rsca*` 的 `features[].worksheet_question_id` vs `content/assessment_worksheets.json` rsca 题号；消费 `assessment_profile_service.py:225-227` | 对齐题号（重建该 worksheet 或修模型）；`regulatory_focus_general_18` 缺 1 题同理补齐 |
| 5 | `validate_content.py` **不校验 worksheet↔model 连通性**，放任 #2/#4 静默通过 | `backend/scripts/validate_content.py:194-196,383-433` | 新增交叉规则：模型声明 worksheet_id/scale_id 时校验对应 worksheet 存在且题号覆盖率 ≥ 运行时门槛（`assessment_profile_service.py:226`）；worksheet 声明 profile_model_id 时校验模型存在 |

**完成标准**：青少年情绪弹性/RFQ-8/RSCA/HPLP/一般调节聚焦/PRFQ/SCS 各自填完→落点接口 `available:true` 且簇 id 正确落库（含簇 0）；`validate_content.py` 能拦断链。

---

## T7-02：后台量表管理（P0｜契约 + Web）

后端 `GET/POST /api/admin/worksheets` + `PUT /api/admin/worksheets/<id>` 已实现（`backend/routes/admin.py:593-655`，鉴权 `require_role("admin", allow_legacy_admin=True)`），但 **shared / web / 小程序三端零声明**，后台无法查看/管理驱动真实测评+画像的 DB 量表（契约+Web 两路确认）。ScalesReview 读的是构建期静态 `scales_catalog.json`，与 `assessment_worksheets` 表不是同一份数据。

1. **shared**：`shared/constants/api.ts` 增 `adminWorksheets: "/api/admin/worksheets"`；`shared/types/api.ts` 定义 `AdminWorksheet`（字段对齐 `admin.py:72-100` 的 `_worksheet_from_row`）与 `AdminWorksheetInput`（对齐 `WORKSHEET_WRITABLE_FIELDS` `admin.py:33-62`）。
2. **web service**：`apps/web/src/services/safehomeApi.ts` 增 `listAdminWorksheets / createAdminWorksheet(input) / updateAdminWorksheet(id, input)`，复用现有 `adminHeaders(adminToken)` 模式。
3. **web 页面**：新增 `WorksheetsManagement.tsx`（挂 `/content/worksheets`，role 限 admin），在 `main.tsx:43-61` 注册路由+导航：列表（含 disabled）、详情（questions/dimensions/scoring_notes）、表单编辑白名单字段、`enabled_for_user` 开关、`profile_model_id` 绑定。ScalesReview 保留为"content 目录只读视图"但页面注明"不等于 DB 量表"。
4. **后端补全**：admin worksheet 缺 **DELETE/下线接口** → 补 `@bp.delete("/worksheets/<id>")`（软删：`enabled_for_user=0`+`review_status=disabled`+写 audit_log）。

**完成标准**：admin 在 Web 可查看/新增/编辑/启用停用 DB 量表，并能绑定 `profile_model_id`；`npm run build` 通过。

---

## T7-03：画像落点字段补齐（P1｜契约 + Web + 小程序已在用）

后端落点返回 `strength_note / small_step / position.display_name / clusters[].display_name / explanation`，**小程序已渲染**，但 **shared 类型缺这些字段 → web TS 取不到 → ResearchDashboard 不展示**（契约+Web 两路确认）。

1. **shared**（`shared/types/api.ts`）：`AssessmentProfilePosition` 顶层补 `strength_note?: string; small_step?: string;`；`.position` 补 `display_name?: string;`；`AssessmentProfileCluster` 补 `display_name?: string;`。
2. **Web 展示**（`apps/web/src/components/ProfileScatterChart.tsx:46`、`pages/ResearchDashboard.tsx:361`）：散点标签与标题优先用 `display_name`（回退 `profile_name`）；落点区块增展示 `explanation / strength_note / small_step / interpretation.message`。
3. 顺带补具名类型 `AssessmentGroupNode/AssessmentGroup`（替换 `AssessmentListResponse.groups` 的匿名内联类型，`api.ts:751-755`）；`AssessmentWorksheet` 补 `dimensions? / dimension_score_method? / scoring_notes?`（后端 `get_assessment` 已下发，内容库 25 份在用）。

**完成标准**：Web 研究看板画像区与小程序展示同源字段；TS 无 `as any`。

---

## T7-04：落点接口健壮性（P1｜后端）

| # | 问题 | 文件:行 | 改法 |
|---|---|---|---|
| 1 | POST 落点写 DB、GET 落点只实时算**不回填**；POST 时模型不可用被静默 pass 后，DB `profile_*` 永远空 | `backend/routes/assessments.py:372-396,441-479` | GET 计算成功后顺带 UPDATE `profile_*` 列（复用修正后的 cluster_id 逻辑） |
| 2 | 低置信度阈值 `0.05` 过低，护栏几乎不触发（与"不贴标签"边界冲突） | `assessment_profile_service.py:13,178-184` | 结合复核校准（如 0.15~0.2），设为可配置 + 补单测 |
| 3 | GET `?model_id=` 命中即用，**不校验该模型属于此 worksheet** | `assessment_profile_service.py:46-50` | 命中后校验 `model.worksheet_id/scale_id == worksheet.id`，不符则忽略或报不可用 |
| 4 | `list_assessment_results` 返回裸行，未解析 `answers_json/scores_json`、带出空串 cluster | `backend/routes/assessments.py:414-438` | 统一解析 JSON + 规范 cluster（修 T7-01#1 后自然一致） |
| 5 | ✅**新增 admin 全量测评结果列表**（研究看板跨用户，用户已确认做） | 新增 `GET /api/admin/assessment-results`（`require_role("admin")`，跨 user，支持 `worksheet_id/profile_model_id` 过滤+分页）+ shared 端点常量 + web `safehomeApi.listAdminAssessmentResults` + `ResearchDashboard` 有后台令牌时改调该接口 | 中 |

---

## T7-05：数据库层（P1｜双后端）

| # | 问题 | 文件:行 | 改法 | 优先 |
|---|---|---|---|---|
| 1 | `ensure_column` 后补的 `REAL` 列在 MySQL 不转 DOUBLE（落点 pc1/pc2/confidence、student_profiles 距离列均后补） | `backend/database.py:236-238` | 在 `mysqlize_column_definition` 对结果同样 `.replace("REAL","DOUBLE")` | 中 |
| 2 | `assessment_results` **无任何索引**，且不在 `REQUIRED_HEALTH_TABLES` | `models.py:399-411`、`database.py:14-25` | 加 `idx_assessment_results_user_created(user_id, created_at)`；把 `assessment_results` 加进必需表；可选加列存在性检查 | 中 |
| 3 | 白名单缺 `sensitive_category/source_file/source_title/display_title` 等短列（MySQL 落 TEXT，无法直接索引/等值） | `database.py:28-119` | 按需加入 `MYSQL_VARCHAR_COLUMNS` | 低中 |
| 4 | `review_status` 缺省 `approved` 与内容侧 `pilot_review_required` 相反（缺省即放行风险） | `models.py:173`、`database.py:775`、`admin.py:129` vs `build_worksheets.py:144` | DB 层缺省与内容侧统一（建议缺省 pilot/未审），并在 validator 校验 worksheet.review_status ∈ 枚举 | 低 |
| 5 | ✅**已定：统一改 INTEGER**（`profile_cluster_id` 对齐 `student_profiles.cluster_id`） | `database.py:533`列定义、`:60`白名单 | ①列定义 TEXT→INTEGER；②从 `MYSQL_VARCHAR_COLUMNS` **移除** `profile_cluster_id`；③写迁移：MySQL `ALTER ... MODIFY`、SQLite 重建/`ensure_column` 不改存量需单独迁移，空串→NULL；④升 `CURRENT_SCHEMA_VERSION`；⑤T7-01#1 写 int | 中（含存量迁移） |

---

## T7-06：遗留统一项（P2｜后端 + 小程序）

1. **学生画像去硬编码**：`student_profile_model_service.py` 是与 `assessment_profile_service` 重复的另一套 z/PCA/距离/置信度，且 `_validate_answers:102-108` 硬编码 `{"1".."5"}`、`score_student_answers:130` 硬编码 `6-raw`。抽公共工具两 service 共用；学生侧 1-5/反向改为从 likert 上下界推导。
2. **小程序端点漂移**：`apps/miniprogram/services/api.js:8-32` 自带一份 `API_ENDPOINTS`，比 shared 缺 ~14 键，`getAssessmentProfilePosition:379` 硬编码路径。最小补齐已用端点 + privacy/family 缺失方法；长期根治=构建期注入 shared 常量。
3. **review_status 枚举**三处取值域统一（见 T7-05#4）。
4. **契约纠偏**：`User` 类型补 `username?/anonymous_id?/status?`、`UserRole` 补 researcher/supervisor；`admin-create-account` 端点可补声明。
5. **401 文案**（`safehomeApi.ts:417-422`）：登录失败别显示"后台令牌无效"，优先用后端 `error.message`，仅 admin-token 接口用云托管提示。

---

## T7-07：任务七验收

```text
后端：validate_content.py（含新交叉校验）通过 → pytest 通过
画像：7 个候选模型各自填完 → profile-position available:true、簇 id 正确落库（含簇0）→ GET 回填 DB
契约：shared 补字段后 Web npm run build 通过；小程序 JS 检查通过；端点三端核对
Web ：/content/worksheets 量表 CRUD 可用；研究看板画像区展示 display_name/strength_note/small_step
DB  ：healthz/deep 含 assessment_results 必需表与 worksheets_sync；MySQL 下落点列为 DOUBLE
```

## 【已确认决策 · 用户 2026-07-01】

1. **研究看板跨用户画像** → ✅ **做**：新增后端 admin 全量测评结果列表端点（见 **T7-04#5**），研究看板改调该接口，看全部参与者落点。
2. **cluster_id 类型** → ✅ **统一改 INTEGER**（对齐 `student_profiles.cluster_id`）：见 **T7-05#5**（含存量迁移 + 升 schema 版本）；**T7-01#1** 落点写库相应存 int。
3. **微信登录** → ✅ **归 T6-08 从零实现**：`/api/auth/wechat-login` 在 T6-08 补齐；任务七不重复，仅做 **T7-06#4** 的 `User` 类型纠偏。

---

## T7-08：任务七补遗（对比 6.30 已交付的训练推荐层后核实，2026-07-01）

> 6.30 已交付训练推荐引擎（T5）与画像簇→训练卡映射，任务七初稿只审了「量表录入 + 聚类画像落点」，**漏审了训练推荐这一层**。已直接核实代码，结论与补充如下。

### 核实结论：训练推荐层基本已打通（**不是缺口，勿重复开发**）
- `evaluate_training_rules` 已接入 `create_assessment_result`（`backend/routes/assessments.py:401-406`），填完量表返回 `recommended_card_ids` ✓
- 日记侧 `_match_diary_training_rules` 已从 `[:1]` 改为 `[:2]`（`backend/routes/feedback.py:74`）✓
- 画像簇 `recommended_card_ids`/`card_reason` 已落地 **8 个** `content/profiles/*.json`，且 `build_assessment_profile_position` 已透传（`assessment_profile_service.py:290-291`）✓
- 小程序 `assessment-result`（wxml+js）已读取展示簇推荐卡 ✓

### 补充缺口（任务七需补做）

| # | 问题/缺口 | 文件:行 | 改法 | 优先级 |
|---|---|---|---|---|
| 1 | **Web 研究看板不展示簇推荐卡**（与 T7-03 同源：web 也没展示 display_name/strength_note） | `apps/web/src/pages/ResearchDashboard.tsx`（grep `recommended_card_ids` 0 命中） | 落点区补展示 `clusters[].recommended_card_ids` + `card_reason`（"与你最近群体常练的卡"）；并入 T7-03 一起做 | P1 |
| 2 | **卡 id 悬空引用未校验**：`assessment_training_map.json`/`diary_training_map.json`/`content/profiles/*.json` 的 `recommended_card_ids` 是否都存在于 `training_cards.json`（34 张） | `backend/scripts/validate_content.py` | 加交叉校验（与 T7-01#5 worksheet↔model 同批补） | P1 |
| 3 | `card_service.recommend_cards` 无 tag 命中时的 fallback 是否仍顺序前 N | `backend/services/card_service.py:14-28 之后` | 确认；若是，改按 card `type` 多样化采样（每型取 1） | P2 |
| 4 | **文档同步（任务七收尾必做）**：任务七新增 `GET /api/admin/assessment-results`、`cluster_id` 改 INTEGER、新增列/索引、shared 类型字段 | `docs/03_技术真相/{API接口文档.md, 数据库字段说明.md, 数据字典.md}` | 随代码同步更新（项目统一口径第 7 条强制）；T7-07 验收增一条"文档已同步" | P1 |
| 5 | 认证层：6.30 已接入登录/注册+token，属"需人工验收"项 | — | 任务七仅 T7-06 纠偏 User 类型/401 文案，**无新增代码缺口**（确认不漏审） | — |

### T7-07 验收补充
```text
+ 训练推荐：填完量表→recommended_card_ids 非空；簇推荐卡在小程序与 Web 落点区均可见
+ 卡引用：validate_content 校验 *_training_map/profiles 的 card id 均存在于 training_cards.json
+ 文档：API接口文档.md / 数据库字段说明.md / 数据字典.md 随新端点与 cluster_id 类型变更同步
```

---

# 任务八：温度计全天曲线 · 反射弧三步 · 训练中心分层与项目测试 · 情感计算与SNA雏形 · 跨层审查

> 创建 2026-07-01｜Claude｜接任务七后。来源：用户 4 项新需求 + 一轮跨层审查。
> **决策（用户 2026-07-01）**：训练中心=三块；项目内容=框架+首节完整样例+其余大纲；情感计算/SNA=离线雏形（`analysis/profiling/`，脱敏输出，不进后端运行时）。
> **前置**：T6-01 情绪温度计**尚未由 Codex 实现**（`emotion_thermometer` 表不在 models.py）。T8-01 是对 T6-01 的**增补**——执行时先落 T6-01 基础表/接口，再叠 T8-01。

## T8-01：情绪温度计——每日多次记录 + 全天情绪曲线（增补 T6-01）

**现状**：`emotion_thermometer`（T6-01 计划：id/user_id/intensity_level 1-10/brief_text/created_at）**每条一行、天然支持一天多次记录**，无需改表结构；缺的是"按日拉取 + 曲线展示"。

**后端**
- 新增按日查询 `GET /api/emotion-thermometer/day?user_id=&date=YYYY-MM-DD`（date 缺省=今天）→ 当日记录按 `created_at` 升序 + 汇总 `{min,max,avg,count}`。
- **日期过滤用双后端安全写法** `WHERE user_id=? AND substr(created_at,1,10)=?`，date 串 Python 端算好传参（**禁 `DATE('now')`**，见任务六总表 B）。
- 索引 `emotion_thermometer(user_id, created_at)` 进 INDEX_SQL。

**小程序**
- thermometer 页加"今日曲线"区（或独立 `pages/thermometer-day`）：Canvas 2D 折线图，x=当日时间、y=强度 1–10；每点可点看 `brief_text`+时间；空态"今天还没有记录"。
- 复用纯函数 `utils/chart.js`；rpx→px 适配 dpr；单次绘制无动画循环。
- 入口：记录成功后"查看今天波动"；首页温度计卡副标"今天已记录 N 次"。

**shared**：`EmotionThermometerDayResponse { date; items[]; summary{min,max,avg,count} }`；端点常量 `emotionThermometerDay`。
**验收**：一天多记录→曲线按时间连线正确；跨零点不串天（UTC 归日一致，与 T6-04 时区注意同源）。

## T8-02：三步开始——讲清情绪反射弧 + 记录必要性 + 逻辑链条 + 一次练习（修订 T6-03）

> **覆盖声明**：本项**推翻** T6-03 早前"去除情绪反射弧术语"的【Claude订正】。按用户新要求，getting-started 页**显式讲解**情绪反射弧。以 T8-02 为准。

**页面四段**（`apps/miniprogram/pages/getting-started/`）
1. **什么是情绪反射弧**：一句通俗定义（"一件事发生后，情绪、想法、身体、行为会像反射一样接连出现——看清它，就能找到可调整的点"）。
2. **为什么先记录一次具体事件**：泛泛说情绪难改，落到一件具体的事上才看得见链条、找得到抓手。
3. **逻辑链条可视化**：横向步骤条/箭头链呈现，每节点一句话。**权威链条已核实填死（勿自造、勿改序、勿增减节点）**——来源：情绪反射弧框架 + 前端 `NODE_LABELS` 用词对齐。

   **诱因/应激源 → 反应（想法·身体感觉·行为）→ 觉察 → 接纳 → 转化 → 应对（适应性策略与行为）→ 结果（适应与发展）**

   | 节点 | 用户向一句话 |
   |---|---|
   | 诱因/应激源 | 一件让你有情绪的事发生了 |
   | 反应 | 紧接着冒出的想法、身体感觉和行为 |
   | 觉察 | 先停一下，看见自己正在反应 |
   | 接纳 | 允许这些感受存在，不急着对抗 |
   | 转化 | 换个角度理解，给自己一点余地 |
   | 应对 | 选一个此刻能做的小行动 |
   | 结果 | 回看这次经历，带走一点成长 |

   ⚠️ **用词对齐**：用 **觉察**（非"觉知"，与前端 `NODE_LABELS` 一致）。**必须区分两套概念，勿混用**：① 上面 7 节点是**用户教育用的"概念弧"**（getting-started 展示）；② 测一测里的 `reflex_node`（reaction / reflection / acceptance / awareness / resource / fusion / transformation / behavior / motivation / outcome / integrated_profile…）是**量表分类标签**，粒度更细、用途不同——**不要把 reflex_node 的 10+ 个值当作这条教育弧来渲染**。
4. **一次练习**：引导用户就"最近一件小事"沿链条走一遍（最简：选诱因→写当时反应→做一次"觉知"微练习），或跳记录页带入链条提示。

**边界**：保留"不下诊断结论"；练习是自我觉察、非治疗。
**文件**：getting-started index.{wxml,js,wxss}。**验收**：四段齐全、链条与框架一致、练习可完成。

## T8-03：训练中心分层改造（三块）

**目标结构**（`apps/miniprogram/pages/training/`）
- **第一档·通用**：现有训练卡/`trainingStages` 保留为"通用训练"档。
- **入口二·个性化定制方案（=个性化治疗入口）**：进入后**基于测一测结果**生成定制训练卡方案。复用已有 `evaluate_training_rules`（维度分→卡）+ 画像簇 `recommended_card_ids`（profiles）。
  - 后端新增 `GET /api/training-plan?user_id=`：取该用户最近若干测评结果 → 汇总/去重 recommended_card_ids（按维度/簇归类）→ 返回 `{plan_items[]{source_worksheet, dimension|cluster, card_ids, reason}}`；无测评则引导"先去测一测"。
  - 前端新增 `pages/personalized-plan`：展示"根据你的测评，为你定制"，分组列卡，点击进训练卡页。
- **入口三·项目测试**：列出 3 个循证项目（T8-04），点击进项目详情/分节。
  - 前端新增 `pages/program-list` + `pages/program-detail`（分节 + 书写）。

**shared**：`TrainingPlan`、`Program`/`ProgramSession` 类型；端点 `trainingPlan/programs`。
**文件**：training/index 改为三入口；新增 personalized-plan、program-list、program-detail；app.json 注册；api.js 加方法。
**验收**：三块入口可达；个性化方案随测评变化；无测评优雅引导。

## T8-04：三个循证书写/管理项目（框架 + 首节完整样例 + 其余大纲）

**内容模型**（`content/programs.json` + `content/schemas/programs.schema.json`，纳入 `validate_content.py`）：
```text
program{ id, title, target_constructs[], theory_source, audience,
  sessions[]{ session_no, title, objective, steps[], writing_prompt?, reflection_questions[], duration_minutes, disclaimer },
  boundary_notice, review_status }
```
**伦理**：每项目 `boundary_notice` + 每节 `disclaimer`（非诊断/非治疗承诺）；过 FORBIDDEN_TERMS。**首节给完整可用内容，其余节给大纲，整包标 `review_status:"pilot_draft"` 待专业审核后扩写。**

### 项目 A：自我关怀书写·考试焦虑（提升情绪调节 + 降低不确定性不耐受 IUS）
- 构念：自我关怀(SCS)、情绪调节、不确定性不耐受(IUS)；理论：自我关怀写作 + UP/CBT。
- 6 节大纲：①认识考试焦虑与不确定 ②自我关怀三要素书写 ③把"最坏假设"写成"多种可能" ④对不确定的接纳练习 ⑤考前自我对话脚本 ⑥回顾与迁移。
- **第 1 节完整样例**：目标=看见考试焦虑里"对不确定的不耐受"；步骤（写下最近一次考试焦虑的具体情境／标出最让你不安的"不确定点"／用一句自我关怀的话回应自己）；书写提示（"如果好朋友有同样的担心，你会怎么对他说？把这句话写给自己"）；反思（我最担心的不确定是什么？／这句关怀话让身体有什么变化？）；时长 10–15 分钟；disclaimer（本练习用于自我觉察，不构成诊断或治疗）。

### 项目 B：自我关怀·亲密关系建立中的自我成长
- 构念：自我关怀、关系自我、边界；理论：自我关怀 + 关系成长。
- 6 节大纲：①关系里的自我觉察 ②自我关怀 vs 自我批评 ③需求与边界表达书写 ④冲突后的自我修复 ⑤从依赖到相互支持 ⑥回顾与迁移。
- **第 1 节完整样例**：目标=在关系里先看见自己的感受与需求；步骤（写一段近期关系中的具体互动／标出当时自己的感受与未说出口的需求／用自我关怀的一句话肯定这份需求的合理）；书写提示、反思、时长 10–15 分钟、disclaimer（结构同 A，主题为亲密关系）。

### 项目 C：缓解学业压力·健康促进睡眠管理
- 构念：学业压力、健康促进生活方式(HPLP)、睡眠卫生；理论：压力管理 + 睡眠卫生（**非临床失眠治疗**）。
- 6 节大纲：①学业压力盘点 ②压力-睡眠关系觉察 ③睡眠卫生小步计划 ④睡前放松(呼吸/身体扫描) ⑤白天节律与任务拆解 ⑥回顾与迁移。
- **第 1 节完整样例**：目标=看清压力来源与睡眠现状；步骤（记录一周作息与压力事件／找出 1 个最影响睡眠的因素／定 1 个今晚可做的小改变）；书写提示、反思、时长 10–15 分钟、disclaimer（如长期严重失眠请就医）。

**后端**：`GET /api/programs`、`GET /api/programs/<id>`；书写留存先本地缓存（仿 3 天计划），如需入库另立 `program_entries`(P2)。
**验收**：3 项目过 `validate_content`；首节完整、其余大纲齐、边界文案齐。

## T8-05：情感计算 + 社会网络分析雏形（离线，不进后端运行时）

**约束**：沿 `analysis/profiling/` 聚类同款——离线脚本、脱敏聚合输出、原始/逐行不入仓、不进后端运行时；依赖入 `requirements-analysis.txt`。

- **情感计算雏形** `analysis/profiling/affective_computing_prototype.py`：读 `emotion_diaries` 自由文本（`event_description/automatic_thought/raw_text`）+ 温度计 `brief_text`（离线导出或只读）；做中文情绪/情感倾向分析（**优先轻量词典法，避免重 ML**）；输出**脱敏聚合**（个体情绪走势/效价随时间、群体分布）→ 可视化数据 JSON。**只出"情绪倾向"描述，不产诊断标签**。
- **社会网络分析雏形** `analysis/profiling/social_network_prototype.py`：以 `family_links`（bind_code/relation_label）建家庭关系图；算基础指标（度、连通分量、简单中心性）；输出脱敏图摘要 + 可视化数据。**注明 family_links 多为试点/稀疏，仅雏形**。
- **可视化**：先离线出图/JSON；如上 Web，ResearchDashboard 加两个"雏形"面板读离线产物 JSON（只读、标注雏形、非诊断、researcher/admin 鉴权）。
- 留痕 → `画像系统设计_Claude_20260628/`。**验收**：两脚本可复现、输出脱敏、不改后端运行时依赖。

## T8-06：跨层审查修改意见（service / schema / 契约 / 类型 / 错误码 / 权限脱敏 / 前端服务层）

**✅ 现状良好（已核实）**：MySQL 连接 `charset=utf8mb4` + `DictCursor` + `autocommit=False`（`database.py:150-158`）——中文/emoji 安全、显式事务；**SQL 无注入**（f-string 只拼内部表/列/索引标识符，值一律 `?` 占位；admin 导出 base_sql 内部构造 + `LIMIT ?`）；`{ok,data}`/`{ok,error}` 协议三端一致；导出脱敏 + `require_role` 已在。

**🔧 修改意见**

| # | 主题 | 问题 | 改法 | 优先 |
|---|---|---|---|---|
| 1 | **事务安全** | `autocommit=False` + 单连接复用；请求在 execute 后、commit 前抛异常且无 rollback，下个复用该连接的请求可能续到脏事务 | `get_connection`/`MySQLConnection.__exit__` 异常路径补 `rollback()`（或每请求独立连接/失效重连） | 高 |
| 2 | **连接健壮性** | `pymysql.connect` 无 `connect_timeout/read_timeout`、无池、无重连，长驻易 `MySQL server has gone away` | 加超时 + `ping(reconnect=True)` 或 per-request 连接 | 中 |
| 3 | **标识符插值护栏** | `ensure_column`/索引/导出的 f-string DDL 拼表列名 | 固化"只接内部白名单、绝不接用户输入"（断言+注释），防未来变注入面 | 中 |
| 4 | **错误码体系** | `fail(code,message)` 的 code 是散串（validation_error/missing_fields…），前端易按 message 判分支 | 收敛为集中错误码枚举（shared 常量），前端按 code 判；API 文档补"错误码表" | 中 |
| 5 | **契约/类型单一源** | 小程序端点表仍漂移（T7-06#2 未做） | T8 新类型/端点**先落 shared 再两端用**；顺带把小程序端点表对齐 shared | 中 |
| 6 | **权限脱敏** | T8-05 情感/SNA 产物、T8-04 书写自由文本 | 上 Web 前脱敏聚合 + researcher/admin 鉴权；书写导出走既有白名单、默认不导原文 | 高 |
| 7 | **文档同步** | T8 新增 `emotion_thermometer`(按日索引)、`programs`、可能的 `program_entries`、多个新端点 | 同步 `docs/03_技术真相/{数据库字段说明.md, API接口文档.md, 数据字典.md}` | 中 |

## T8-07：任务八验收
```text
后端：validate_content(含 programs+新schema) 通过；pytest 通过；healthz/deep 绿
温度计：一天多记录→今日曲线正确；按日接口 substr 双后端一致
三步开始：反射弧四段+练习；链条节点与框架一致
训练中心：三块入口可达；个性化方案随测评生成；项目测试可进
项目内容：3 项目首节完整+其余大纲+边界文案；过 FORBIDDEN_TERMS
情感/SNA：analysis 脚本可复现、脱敏、不进后端运行时
审查：事务 rollback + 连接超时/重连已加；错误码表已补；字段/API 文档同步
```

# 任务九：代码审查与修改计划（小程序原生 / 数据库 / Flask / 项目结构 / 日志排错）

> 创建时间：2026-07-02  
> 来源：用户提供的 31 项代码审查事项。  
> 执行原则：任务九先做审查和问题定位，再按风险分批最小修复。每个小任务都要输出：审查范围、发现问题、建议修复、涉及文件、验证命令。涉及代码、文档、配置或内容库改动时，必须同步 `docs/00_当前事实基准/{开发日志.md,当前进度交接.md,开发说明.md}`。涉及 API、字段或数据库时，还必须同步 API 文档、数据库字段说明和 shared 契约。

## T9-01：小程序页面、组件、配置和请求层分工审查

审查微信小程序原生开发中页面、组件、配置文件和请求层之间的职责分工。

重点检查：

```text
1. api 封装是否集中在服务层。
2. 本地后端和云托管后端差异是否通过配置处理。
3. 身份 token 是否由统一请求层注入。
4. api.js 是否承担稳定业务入口，而不是让页面拼接接口。
5. page 层是否只处理 data、路由参数、用户事件和页面状态。
```

交付物：小程序分层审查记录。

## T9-02：小程序失败态、空态和用户可见错误审查

审查小程序页面是否只写成功态，导致接口失败时页面空白，或只 `console.log` 错误不给用户提示。

重点检查：

```text
1. loading、empty、error、success 状态是否完整。
2. 接口失败时是否有用户能看懂的提示。
3. 是否存在只在控制台打印错误、页面无反馈的问题。
4. 是否存在错误后按钮不可恢复、页面无法重试的问题。
```

交付物：页面失败态和空态清单。

## T9-03：小程序 page / component / service 职责边界审查

审查 component 中是否混入请求数据、身份校验和复杂错误处理，确认这些逻辑留在页面或服务层。

重点检查：

```text
1. page 放页面状态、路由参数、调用服务层、用户提示。
2. page 不放重复展示结构。
3. component 放局部 UI、展示逻辑、轻量交互事件。
4. service 放接口地址、请求头、错误转换、云托管分支。
5. 是否有多个页面重复写相同展示结构或请求逻辑。
```

交付物：page/component/service 职责边界表。

## T9-04：小程序服务层和请求封装审查

审查服务层是否统一处理 `baseURL`、云托管调用、token 注入和错误转换。

重点检查：

```text
1. 页面中不得硬编码本地或云托管地址。
2. 是否用配置开关区分 mock、本地后端和云托管后端。
3. 测试环境 token 不得带到生产环境。
4. 请求头、身份信息和环境分支是否集中维护。
5. 失败响应是否统一转换。
```

交付物：请求封装审查清单。

## T9-05：后端错误到小程序页面错误结构转换审查

审查后端错误是否转换成页面能理解的稳定结构，而不是页面直接解析各种 `res.statusCode` 和原始报错。

重点检查：

```text
1. 前端是否拿到 message、code、retryable 等稳定字段。
2. 用户可见错误是否统一。
3. 是否避免暴露数据库连接失败、权限校验细节、堆栈等内部信息。
4. 页面是否按 code 做稳定动作。
```

交付物：API 错误转换表。

## T9-06：小程序上线后普通用户可打开页面联调审查

审查页面在上线后是否能被普通用户打开，并且不会依赖开发者临时状态。

重点检查：

```text
1. 普通用户入口是否可达。
2. 页面是否依赖调试页、测试 token 或开发者缓存。
3. 缺少登录态、缺少数据、接口失败时是否能正常提示。
4. 微信开发者工具和真机环境表现是否一致。
```

交付物：普通用户可打开页面清单。

## T9-07：小程序身份、token、401/403/404/500 处理审查

审查小程序端身份和 token 保存边界，以及各类 HTTP 错误对应动作。

重点检查：

```text
1. 小程序端可以保存登录态或临时 token。
2. 不得把服务端秘钥、数据库密码、管理员 token 放到前端代码或缓存。
3. token 失效时服务层统一处理 401，清理登录态、跳转登录或提示重新授权。
4. 不允许每个页面各写一套 token 失效逻辑。
5. 401、403、404、500 是否对应正确页面动作。
```

交付物：身份和错误状态处理审查表。

## T9-08：小程序用户提示语义审查

审查用户提示是否能区分不同错误类型，并给出合适动作。

重点检查：

```text
1. 可自行处理的问题是否给出补充引导。
2. 需要稍后再试的问题是否提示重试。
3. 参数缺失是否提示用户补充信息。
4. 权限不足是否停止操作。
5. 网络失败是否提示检查网络或重试。
```

交付物：用户提示语义表。

## T9-09：小程序 api.js 业务入口命名与封装审查

审查 `api.js` 是否承担环境选择、路径拼接、身份注入、响应处理和错误转换。

重点检查：

```text
1. api.js 是否暴露稳定业务方法，而不是暴露页面自己拼接的请求。
2. 页面代码是否接近业务语言。
3. 入口函数命名是否稳定。
4. 页面调用的业务方法语义是否稳定。
5. 是否存在多个页面重复拼接同一接口的问题。
```

交付物：api.js 入口函数审查表。

## T9-10：小程序请求分支和环境定位审查

审查请求分支是否能清楚回答当前环境是什么、目标服务在哪、失败时如何定位。

重点检查：

```text
1. 当前运行环境是否可见或可诊断。
2. mock、本地后端、云托管后端分支是否清楚。
3. 失败日志是否能定位目标服务、接口路径和请求方式。
4. 是否有隐藏的默认环境导致联调混乱。
```

交付物：环境分支定位记录。

## T9-11：小程序响应处理统一性审查

审查响应处理是否把后端结构转换成页面可消费的数据。

重点检查：

```text
1. 成功时统一返回 data。
2. 失败时统一抛出 error。
3. 页面是否避免直接处理后端原始外形。
4. 数据缺省值和空数组是否由服务层或页面稳定处理。
```

交付物：响应处理一致性清单。

## T9-12：CloudBase 云托管调用链审查

审查小程序云托管调用链是否和后端接口一致。

重点检查：

```text
1. wx.cloud.init 的环境 ID 是否正确。
2. callContainer 的 path、method、header 是否与后端接口一致。
3. 云托管服务是否有健康检查接口。
4. 健康检查是否返回稳定 JSON。
5. 本地和云端调用差异是否集中配置。
```

交付物：CloudBase 调用链审查表。

## T9-13：数据库持久化边界和数据归属审查

审查需要保留的数据是否进入数据库，字段是否一致并支持查询。

重点检查：

```text
1. 需要长期保留的数据是否写入数据库。
2. 字段是否和 API、shared、文档一致。
3. 查询是否支持业务需要。
4. SQL 是否按路由层、服务层、数据库适配层拆分。
5. SQLite 与 MySQL 边界是否清楚。
```

交付物：数据库持久化边界表。

## T9-14：数据库字段稳定性和字段说明审查

审查数据库字段名是否稳定、含义单一，并在字段说明文档记录。

重点检查：

```text
1. 是否存在重复字段或含义重叠字段。
2. 前端、测试和数据库字段是否一致。
3. 表是否按实体拆分。
4. 每行是否保留主键，方便更新、追踪和关联。
5. 字段名是否可解释。
6. 字段说明文档是否记录含义。
```

交付物：字段检查表。

## T9-15：数据库主键、外键和关联关系审查

审查主键、外键和服务逻辑中的关联关系是否清楚。

重点检查：

```text
1. 每张表是否有稳定主键。
2. 需要关联的表是否有外键或服务层明确约束。
3. 字段命名是否能表达关联关系。
4. 服务逻辑是否避免误把不同用户或不同实体的数据关联在一起。
```

交付物：主外键和关联关系审查表。

## T9-16：数据库事务安全审查

审查事务能否保证一组操作全部成功或全部失败。

重点检查：

```text
1. 一次请求同时写入多张表时是否使用事务。
2. 失败时是否 rollback。
3. 是否存在半完成数据。
4. 测试是否覆盖写入失败场景。
```

交付物：事务安全审查记录。

## T9-17：SQLite 连接生命周期和参数化查询审查

审查 SQLite 是否使用上下文管理器，连接生命周期是否和一次操作绑定。

重点检查：

```text
1. 是否避免多个函数共享同一个全局连接。
2. 是否使用参数化查询。
3. 不得出现 f"select * from feedback where user_id = '{user_id}'" 这类拼接 SQL。
4. SQL 结构和值是否分离。
5. 异常时连接是否正确关闭。
```

交付物：SQLite 连接和 SQL 安全审查表。

## T9-18：schema 初始化脚本幂等性审查

审查 schema 初始化脚本是否可重复运行，并写清楚字段、默认值和必要索引。

重点检查：

```text
1. 初始化脚本是否幂等。
2. 每张表字段是否完整。
3. 默认值是否明确。
4. 必要索引是否存在。
5. 初始化失败时是否有清楚错误日志。
```

交付物：schema 初始化审查记录。

## T9-19：MySQL、编码、健康检查和备份策略审查

审查 MySQL 连接、字符集、云端部署前数据库可用性和备份策略。

重点检查：

```text
1. MySQL 是否能连接成功。
2. 字符集是否使用 utf8mb4。
3. 同时检查数据库字符集、表字符集、连接 charset 和前后端 JSON 编码。
4. 是否存在乱码、插入失败、emoji 报错、排序异常。
5. 云端部署前后端是否能连上数据库。
6. schema 是否已初始化。
7. 健康检查是否能区分服务可用和数据库可用。
8. 是否有备份策略、恢复演练和保存周期。
9. database 是否有连接函数、初始化 schema 函数。
10. 查询函数是否全部使用参数化写法。
11. 是否有统一异常处理和日志。
12. 需要输出索引表，即字段检查表。
```

交付物：MySQL/编码/备份/字段索引综合审查表。

## T9-20：审计日志、迁移留痕和端到端编码验证审查

审查是否有审计日志、迁移留痕，以及中文、英文、数字、标点和 emoji 的端到端编码验证。

重点检查：

```text
1. 是否记录必要摘要。
2. 后续迁移是否能记录变更原因、执行 SQL、影响表、验证方式和回滚策略。
3. 写一条同时包含中文、英文、数字、标点和 emoji 的记录。
4. 从接口写入数据库，再从数据库读回页面。
5. 验证写入、读出、接口返回、页面展示四步。
6. 能否定位编码问题出现在哪一层。
```

交付物：审计日志和端到端编码验证记录。

## T9-21：Flask 路由拆分、响应结构和中文 JSON 审查

审查 Flask 后端是否按业务域拆分路由，并形成稳定请求响应链路。

重点检查：

```text
1. 是否避免一个 app.py 承担所有职责。
2. 请求解析、业务调用、错误响应、跨域联调和测试验证是否稳定。
3. 成功响应、校验失败、权限失败和服务器错误是否有稳定外形。
4. JSON 对中文是否有 provider 控制序列化行为。
5. 接口调试和日志中中文是否可读。
6. 是否仍使用 utf8 和标准 JSON。
```

交付物：Flask 路由和响应结构审查表。

## T9-22：Flask 应用工厂和测试配置审查

审查 Flask 应用是否可配置、可测试、可拆分。

重点检查：

```text
1. 是否有 create_app。
2. 配置是否隔离开发、测试和生产。
3. create_app 是否允许传入 URL 或临时配置。
4. 接口测试是否能使用临时配置。
5. 测试是否避免依赖真实生产配置。
```

交付物：Flask 应用工厂审查记录。

## T9-23：Blueprint、service、database 分层审查

审查 blueprint、route、service、database 是否分别放置对应职责。

重点检查：

```text
1. route 放 URL、method、请求参数和响应结构。
2. service 放业务规则、数据组装和权限判断。
3. database 放连接、SQL、事务、索引相关查询。
4. 开发、测试和生产配置是否隔离。
5. 是否有跨层调用导致测试困难。
```

交付物：后端分层审查表。

## T9-24：CORS、healthz/readyz 和错误码稳定性审查

审查前端是否能调用后端，CORS、健康检查和错误码是否稳定。

重点检查：

```text
1. CORS 是否允许正确来源访问。
2. 是否存在长期允许所有来源加携带凭证的问题。
3. healthz 是否安全、稳定。
4. 是否拆分基础 healthz 和 readyz。
5. 不要把所有检查都堆进一个接口。
6. 错误响应是否使用稳定 code。
```

交付物：CORS 和健康检查审查表。

## T9-25：后端入口装配轻量化审查

审查入口装配分层是否混乱。

重点检查：

```text
1. 入口文件是否保持轻量。
2. 入口是否只负责装配，而不是承载所有业务。
3. 是否同时出现大量 SQL、复杂业务判断和页面文案。
4. 业务逻辑是否已下沉到 service。
5. 数据访问是否已下沉到 database。
```

交付物：后端入口轻量化审查记录。

## T9-26：argparse 脚本 main 函数边界审查

审查命令行脚本是否把 argparse 和业务函数边界分开。

重点检查：

```text
1. main 函数是否只处理命令行边界。
2. 测试是否可以直接测业务函数。
3. 测试是否可以单独测参数解析。
4. 脚本失败时是否返回清楚退出码和错误提示。
```

交付物：脚本 main 函数边界审查表。

## T9-27：项目结构、依赖方向和内容库组织审查

审查当前项目结构是否能减少混乱、降低协作成本，并让测试和部署有稳定入口。

重点检查：

```text
1. 当前分层是否清楚。
2. 入口、路由、服务、模型之间关系是否稳定。
3. 依赖方向是否清楚。
4. 当前脚本命名是否规范。
5. 内容库命名是否清晰、字段稳定、格式可校验。
6. 内容库是否有写死在路由里的问题。
7. 虚拟环境和本地运行产物是否避免进入仓库。
```

交付物：项目结构审查报告。

## T9-28：requirements 和依赖文件审查

审查依赖文件和运行命令是否对应。

重点检查：

```text
1. requirements 是否明确。
2. 后端依赖和分析依赖是否区分。
3. 前端依赖是否和 package 文件对应。
4. 文档中的安装命令是否可执行。
5. 是否有未记录但运行时必需的依赖。
```

交付物：依赖审查清单。

## T9-29：环境变量和敏感配置审查

审查 `.env`、配置文件、前端代码、文档和脚本中是否暴露敏感配置。

重点检查：

```text
1. 数据库密码、云服务秘钥、token、内部管理账号登录信息不得进入前端或仓库。
2. 生产环境不得使用默认 token 或弱 secret。
3. Web、小程序和后端对环境变量的读取路径是否清楚。
4. 示例配置是否脱敏。
5. 日志和错误提示是否避免打印密钥。
```

交付物：敏感配置扫描记录和整改建议。

## T9-30：logging 日志体系审查

审查项目是否有统一、可过滤、可定位的日志体系。

重点检查：

```text
1. 是否使用 logging 模块。
2. 同一条事件是否能输出到控制台、文件或平台日志，并按级别过滤。
3. 后端请求、数据库连接、脚本批处理和容器启动是否可追踪。
4. 日志是否描述事件，而不只是“这里执行了什么”。
5. 是否用 DEBUG、INFO、WARNING、ERROR 表达严重程度。
6. 是否有结构化上下文。
7. logger、level、handler、formatter 是否清楚。
8. 是否有随意创建不同名字 logger 的问题。
9. basicConfig 是否只在程序入口调用一次。
10. handler 输出位置是否清楚。
```

交付物：日志体系审查报告。

## T9-31：异常追踪、错误码和用户可见错误审查

审查异常与追踪信息是否能帮助协作者定位问题，同时避免向用户暴露内部细节。

重点检查：

```text
1. exception 日志是否保留堆栈信息。
2. 协作者是否能先看异常类型，再看项目代码行号，再回到函数输入条件。
3. 错误码是否成为日志、接口响应和测试之间的桥梁。
4. 用户看到提示，前端拿到 code，后端日志记录 code 加上下文。
5. 错误码是否使用稳定的大写枚举。
6. 用户可见错误是否简短可理解，不过度暴露内部细节。
7. 测试是否覆盖关键错误码和错误外形。
```

交付物：错误码和异常追踪审查表。

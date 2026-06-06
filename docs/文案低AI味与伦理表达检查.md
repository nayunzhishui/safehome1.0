# 文案低 AI 味与伦理表达检查

更新时间：2026-06-05

## 扫描范围

- `apps/miniprogram/**/*.wxml`
- `apps/miniprogram/**/*.js`
- `apps/web/src/**/*.tsx`
- `content/**/*.json`

扫描词：

```text
治愈、重塑、改变人生、专业诊断、人格、疾病、异常、立即改善、高危患者、潜意识说明
```

## 已处理

- Web 学生/家长报告页将“固定人格”改为“固定特征”。
- Web 报告边界文案将“医学或心理疾病诊断”改为“医学或心理诊断”。
- 候选家长训练卡将“判断孩子或家长人格”改为“判断孩子或家长固定特征”。

## 保留命中

| 文件 | 命中 | 处理 |
|---|---|---|
| `content/readfeedback/student_scales.json` | “异常心神不定” | 量表题项原文，禁止擅自修改 |
| `content/student_profile_rules.json` | “前端不得使用‘人格’字样” | 内部规则说明，不是用户端文案 |
| `content/enrichment/README.md` | “不承诺诊断、治疗、危机干预或立即改善” | 否定式边界说明，保留 |
| `content/enrichment/student_training_cards_candidates.json` | “不承诺立即改善” | 否定式边界说明，保留 |
| `apps/web/src/pages/ResearchDashboard.tsx` | “内容文件异常” | 工程状态语境，非心理标签 |

## 验证

```powershell
npm run build
Get-ChildItem -Path apps\miniprogram -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
```

结果：通过。

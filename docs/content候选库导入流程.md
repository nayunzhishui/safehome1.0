# content 候选库导入流程

更新时间：2026-06-05

`content/enrichment/` 只用于保存候选训练卡和候选反馈规则，不参与正式运行。

## 导入前必须确认

1. 心理学人工审核通过。
2. 文案非诊断、非标签化、非治疗承诺。
3. 高风险、危机和现实安全边界清楚。
4. 推荐训练卡 ID 已存在或同步新增。
5. 候选内容仍不得标记为 `fully_approved`，除非项目负责人明确审核通过。

## 最小导入步骤

1. 从候选库选择 1-3 条，不整批导入。
2. 复制到 `content/training_cards.json` 或 `content/feedback_rules.json`。
3. 更新版本号和 `review_status`。
4. 运行：

```powershell
python backend\scripts\validate_content.py
python -m pytest backend\tests -q
```

5. 回测小程序记录、反馈、训练卡和打卡主链路。

## 暂不导入

- 暴露/接近行动类内容；
- 涉及自伤、自杀、暴力、虐待、严重失眠的内容；
- 任何可能让用户理解成诊断、治疗或危机干预的内容。

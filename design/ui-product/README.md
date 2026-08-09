# UIproduct 自动逐页改造控制

本目录记录 `UIproduct` 分支上的全小程序 UI 改造状态。它解决“逐页、可恢复、不可跳关”，不替代 ImageGen、Figma、微信开发者工具和真机人工验收。

## 固定流程

每页严格按以下证据顺序推进：

`truth → freeze → imagegen → image_review → figma → figma_review → implementation → loop_visual → loop_ui → loop_ux → loop_states → loop_device → harness_visual → harness_component → harness_ux → harness_engineering → done`

任一阶段没有证据，`scripts/ui_product_loop.py record` 都不会允许进入下一阶段。

## 命令

```powershell
python scripts/ui_product_loop.py audit-truth
python scripts/ui_product_loop.py check-truth
python scripts/ui_product_loop.py status
python scripts/ui_product_loop.py harness
```

记录阶段证据示例：

```powershell
python scripts/ui_product_loop.py record --page pages/home/index --stage truth --evidence design/function-truth-table.md --note "当前代码、接口与状态已核对"
```

Figma 可使用文件或 Figma 链接作为证据。ImageGen、Figma 和真机结果必须先经过对应审查，不能直接记录为通过。

## 硬门禁

- 当前分支必须是 `UIproduct`。
- `main` 指针必须保持为创建分支时的提交。
- `backend/`、`content/`、`shared/` 不得在本 UI 任务中产生改动。
- 全部 `app.json` 页面必须出现在功能真值表中。
- WXML 事件必须能解析到页面处理器；页面 API 调用必须能解析到现有 API client。
- 页面源码变化后必须重新生成并复核功能真值证据。
- 未完成真机项必须记录为待人工验收，不得伪造通过。

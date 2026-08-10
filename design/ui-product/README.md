# UIproduct 自动逐页改造控制

本目录记录 `UIproduct` 分支上的全小程序 UI 改造状态。它解决“逐页、可恢复、不可跳关”，不替代 ImageGen、Figma、微信开发者工具和最终批次真机人工验收。

## 固定流程

第一阶段每页严格按以下证据顺序推进：

`truth → freeze → imagegen → image_review → figma → figma_review → implementation → loop_visual → loop_ui → loop_ux → loop_states → harness_visual → harness_component → harness_ux → harness_engineering → done`

任一阶段没有证据，`scripts/ui_product_loop.py record` 都不会允许进入下一阶段。

第二阶段仅在全部页面第一阶段均为 `complete` 后开放：用户统一进行 Android/iOS 真机验收，逐页记录 `pass` 或 `fix_required`。发现问题后修正并回归，全部页面均有 `pass` 证据才完成最终验收。

## 命令

```powershell
python scripts/ui_product_loop.py audit-truth
python scripts/ui_product_loop.py check-truth
python scripts/ui_product_loop.py status
python scripts/ui_product_loop.py harness
python scripts/ui_product_loop.py device-status
```

记录阶段证据示例：

```powershell
python scripts/ui_product_loop.py record --page pages/home/index --stage truth --evidence design/function-truth-table.md --note "当前代码、接口与状态已核对"
```

Figma 可使用文件或 Figma 链接作为证据。ImageGen 和 Figma 结果必须先经过对应审查，不能直接记录为通过。

全部页面本地完成后记录真机结果：

```powershell
python scripts/ui_product_loop.py device-record --page pages/home/index --result pass --evidence design/ui-product/device/home-android.png --note "Android 真机通过"
```

Figma 长流程状态单独保存在 `design/ui-product/figma-state.json`。每次 Figma 调用前先读取该文件；所有返回的 fileKey、Page ID、Component ID、Variable ID 和 Screen ID 必须立即写回，禁止猜测节点 ID。

## 硬门禁

- 当前分支必须是 `UIproduct`。
- `main_sha_at_start` 永久保存创建分支时的提交；Harness 比较 `main_sha_baseline`。只有用户明确要求在 UI worktree 合并并核对新的 `main` 后，才允许推进核准基线，同时把变更写入 `baseline_history`。
- `backend/`、`content/`、`shared/` 不得在本 UI 任务中产生改动。
- 全部 `app.json` 页面必须出现在功能真值表中。
- WXML 事件必须能解析到页面处理器；页面 API 调用必须能解析到现有 API client。
- 页面源码变化后必须重新生成并复核功能真值证据。
- 真机验收统一延期到全部页面本地完成后；在门禁开放前 `device-record` 会拒绝写入。
- 延期不等于通过；没有截图或录屏证据不得记录 `pass`。

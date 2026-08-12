# UIproduct 逐页改造与远端审查控制

本目录记录 `UIproduct` 分支上的全小程序 UI 改造状态。网页版 GPT 先完成 ImageGen、Figma 和代码复现，Codex 再根据精确远端证据独立审查；不可行时由 Codex 按 ImageGen → Figma → 代码顺序修正。完整交接规则见 `docs/07_UI设计/网页版GPT_UIproduct执行与Codex审查规则.md`。

## 固定流程

第一阶段每页严格按以下证据顺序推进：

`truth → freeze → imagegen → image_review → figma → figma_review → implementation → loop_visual → loop_ui → loop_ux → loop_states → harness_visual → harness_component → harness_ux → harness_engineering → done`

任一阶段没有证据，`scripts/ui_product_loop.py record` 都不会允许进入下一阶段。网页版 GPT 完成 `harness_engineering` 后必须推送 `UIproduct`，返回 ImageGen、带 `node-id` 的 Figma Frame、精确 commit 和验证结果。Codex 审查为 `可行` 后才记录 `done`；结论为 `需修正` 或 `阻断` 时，Codex 接管当前页修复并重新审查。

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

逐页本地自审仍必须执行“小字预算”门禁。全部页面本地完成后的统一用户验收中，出现小于 `24rpx`、连续三行及以上小字、重复免责声明、未经人类化的机器字段或 ISO 时间、关键操作或关键反馈使用 Caption 样式中的任一项，必须通过 `device-record --result fix_required` 登记并回修。完整规则见 `docs/07_UI设计/UI美术与UX改造总指导.md` 第 10.1 节；跨页截图审查证据见 `design/ui-product/small-copy-policy.md`。

全部页面本地完成后记录真机结果：

```powershell
python scripts/ui_product_loop.py device-record --page pages/home/index --result pass --evidence design/ui-product/device/home-android.png --note "Android 真机通过"
```

Figma 长流程状态单独保存在 `design/ui-product/figma-state.json`。每次 Figma 调用前先读取该文件；所有返回的 fileKey、Page ID、Component ID、Variable ID 和 Screen ID 必须立即写回，禁止猜测节点 ID。

## 硬门禁

- 当前分支必须是 `UIproduct`。
- 网页版 GPT 只提供分支首页不算交付；必须提供精确 commit 或 Pull Request 和带 `node-id` 的 Figma Frame。
- Codex 修复必须创建独立 `UIproduct` 提交，禁止与网页版 GPT 同时修改同一页面或同一 Figma Frame。
- `main_sha_at_start` 永久保存创建分支时的提交；Harness 比较 `main_sha_baseline`。只有用户明确要求在 UI worktree 合并并核对新的 `main` 后，才允许推进核准基线，同时把变更写入 `baseline_history`。
- 用户已于 2026-08-10 明确冻结“先完成全部 UI、再统一合并 main”：逐页阶段的范围 Harness 固定比较 `main_sha_baseline`，外部 main 继续推进只记录为待集成，不阻断 UI 页面生产，也不得提前修改、切换或合并主 worktree。
- 全部页面本地完成后，在 UIproduct worktree 一次性合并当时的 main；冲突必须同时保留 UI 记录与 main 记录。合并后更新核准基线，重跑全量真值与工程 Harness，再开放统一真机批次。
- `backend/`、`content/`、`shared/` 不得在本 UI 任务中产生改动。
- 全部 `app.json` 页面必须出现在功能真值表中。
- WXML 事件必须能解析到页面处理器；页面 API 调用必须能解析到现有 API client。
- 页面源码变化后必须重新生成并复核功能真值证据。
- 每页的 ImageGen 提示词、Figma 审查和 `code-review.md` 必须记录小字预算；不得用缩小字号解决信息密度。
- 每页完成 `harness_engineering` 后先执行远端 Codex 审查。只有 `可行` 才记录 `done`；不可行时完成 ImageGen、Figma、代码修复闭环后重新审查。
- 真机验收统一延期到全部页面本地完成后；在门禁开放前 `device-record` 会拒绝写入。
- 延期不等于通过；没有截图或录屏证据不得记录 `pass`。

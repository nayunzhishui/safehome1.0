---
title: 网页版 GPT UIproduct 交接包入口
contentType: How-to
status: canonical
updated: 2026-08-11
---

# 网页版 GPT UIproduct 交接包入口

这个压缩包用于让网页版 GPT 接手 SafeHome 微信小程序 UI。当前活动页是 `pages/getting-started/index`。该页已经完成功能真值、现状审查、方向比较和需求冻结；Figma 与前端尚未开始，已有 ImageGen 只作参考。

## 阅读顺序

1. `project/AGENTS.md`
2. `rules/UI美术与UX改造总指导.md`
3. `rules/网页版GPT_UIproduct执行与Codex审查规则.md`
4. `truth/function-truth-table.md` 中 `pages/getting-started/index` 章节
5. `design-system/experience-tokens.json`
6. `ui-product/README.md`
7. `ui-product/registry.json`
8. `ui-product/figma-state.json`
9. `ui-product/references/current-ui/README.md` 及 12 张截图
10. `ui-product/pages/10-getting-started/` 全部文件
11. `source/apps/miniprogram/pages/getting-started/` 源码

## 媒体证据边界

- 已收录对话中用于 UI 审查的 12 张现有界面截图，并在 `ui-product/references/current-ui/README.md` 中逐张标注用途、问题和功能边界。
- 历史真机录屏 `屏幕录制 2026-08-09 220512.mp4` 已不在对话中的原始本地路径，本包不伪造、不以其他素材替代该视频。
- 需要视频级动态审查时，由用户重新上传真机录屏；当前先以截图、功能真值表和页面源码为准。

## 当前任务

请逐页执行功能真值 → ImageGen → Figma → `UIproduct` 代码。不要修改 `main`、后端、数据库、API、CloudBase、认证、content 或 shared 业务语义。

完成当前页后返回：

- 采用的 ImageGen 证据
- 带 `node-id` 的 Figma Frame 链接
- 精确 GitHub commit 或 Pull Request 链接
- 修改文件
- 保持不变的事件、路由、API 和状态
- 验证命令、退出码、未执行项和已知差异

Codex 会独立审查。结论为 `需修正` 或 `阻断` 时，Codex 按 ImageGen → Figma → 代码顺序接管修复并提交新的 `UIproduct` 修复 commit。

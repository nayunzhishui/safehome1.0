# 历史工作副本留档

2026-10-11 清理本地工作副本前，把副本中从未提交、也未进入任何分支的内容转存到这里，避免丢失。

## safehome1.0-f06bug备份（原 safehome1.0-rc0810-f06 工作副本，约 2026-09-13）

- 基于分支 `codex/rc0810-f06`（f3f73e00，2026-08-12）。该分支的提交已全部在主线中。
- `f06bug备份_20260913_未提交改动.patch`：副本相对该分支的未提交改动（backend/routes/auth_utils.py、feedback.py、utils.py 与 services/research_access_service.py，约 +100 行），是 F06 对象授权的一次早期尝试。主线后来以另一种写法完成了 F06（routes/utils.py 中的 require_admin_or_owner 与越权拒绝审计，17 个 F06 测试），本补丁未应用。
- `f06bug备份_20260913_test_rc0810_f06.py`：当时未提交的测试，含两个主线测试名中没有的场景（研究者须有有效分配才能访问参与者日记目标；分配不能让研究者冒充参与者写入）。如需补到主线，需要按主线现有接口改写后再加入。

## safehome1.0-UIproduct（UIproduct 分支工作副本）

- 未提交的首页 HTML 原型、预览图、真机评审截图与设计文档修改已转存到 `design/ui-product/`，记录原文见 `design/ui-product/pages/01-home/首页HTML原型试行记录_20260827.md`。

## .codex_tmp/release-integration-20260921（GPT 登录、隐私与发布候选工作副本）

- 分支 `codex/release-integration-20260921` 已于 2026-10-11 合并进主线。
- `release-integration-20260921_未提交文档改动.patch`：副本中未提交的 4 份记录文档改动（共 6 行，如两次独立审查因账号额度耗尽失败、不能记为审查通过的状态说明），原样留档，未应用到主线。

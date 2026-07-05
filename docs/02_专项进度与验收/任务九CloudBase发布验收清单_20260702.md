# 任务九 CloudBase 发布验收清单

创建日期：2026-07-02

适用分支：`codex/task9-code-review`

适用场景：任务九本地自动审查、修复和验收已完成后，将当前分支发布到 CloudBase 云托管，并验证 `/readyz`、MySQL、content 和小程序联调。

## 1. 发布前确认

```text
1. 当前分支是 codex/task9-code-review。
2. 已运行 scripts/run_task9_review_checks.ps1 并通过。
3. 不提交 .env、数据库、node_modules、dist、backups、真实 token、真实用户数据。
4. 不删除 pages/integration-test/index。
5. 不把 MYSQL_PASSWORD、ADMIN_EXPORT_TOKEN、SECRET_KEY、WECHAT_SECRET 写入仓库。
```

发布前本地命令：

```powershell
git branch --show-current
powershell -ExecutionPolicy Bypass -File scripts/run_task9_review_checks.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_task9_external_checks.ps1 -SkipCloudBase
powershell -ExecutionPolicy Bypass -File scripts/build_task9_cloudbase_package.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify_task9_cloudbase_package.ps1
```

本地上传包说明：

```text
脚本会在 .codex_tmp/ 下生成 safehome-cloudbase-task9-*.zip。
同时生成 .codex_tmp/safehome-cloudbase-task9-latest.zip，供控制台上传时使用。
同时生成 .sha256 校验文件，用于确认上传包完整性。
上传包只包含 Dockerfile、.dockerignore、backend、content、shared 和 TASK9_PACKAGE_MANIFEST.txt。
脚本会排除 .env、数据库、日志、缓存、虚拟环境、node_modules、dist、backups、exports 等本地运行产物。
本脚本只打包，不自动发布 CloudBase。
verify 脚本会检查最新上传包是否包含必需文件，并拒绝 .env、数据库、日志、缓存、node_modules、dist、backups 等运行产物。
```

## 2. CloudBase 环境变量

CloudBase 云托管服务 `flask-gh3l` 至少需要确认：

| 变量 | 要求 |
|---|---|
| `APP_ENV` | `production` |
| `DB_PROVIDER` | `mysql` |
| `MYSQL_HOST` | 腾讯云 MySQL 内网地址 |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | 后端专用账号 |
| `MYSQL_PASSWORD` | 只填写在 CloudBase 环境变量中 |
| `MYSQL_DATABASE` | `safehome` |
| `CONTENT_DIR` | `/app/content` |
| `ADMIN_EXPORT_TOKEN` | 强随机后台令牌，不使用本地默认值 |
| `SECRET_KEY` | 强随机签名密钥，不少于 32 字符 |
| `ALLOWED_ORIGINS` | Web 站点白名单，逗号分隔 |

可选：

| 变量 | 要求 |
|---|---|
| `LOG_LEVEL` | 建议 `INFO` |
| `LOG_FILE` | 容器中建议留空，输出到平台日志 |
| `WECHAT_APPID` | 微信登录启用时填写 |
| `WECHAT_SECRET` | 只填写在 CloudBase 环境变量中 |

## 3. 发布后健康检查

发布当前分支后运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_task9_external_checks.ps1 -SkipSqliteBackupRestore
```

如果 CloudBase 冷启动或网络较慢，可以显式放宽超时：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_task9_external_checks.ps1 -SkipSqliteBackupRestore -HealthTimeoutSec 90
```

期望结果：

```text
/healthz：200
/readyz：200
/healthz/deep：200
database.provider=mysql
database.ok=true
content.ok=true
```

如果 `/healthz` 通过但 `/readyz` 返回 404：

```text
说明云端仍是旧版本，尚未发布包含任务九 /readyz 的代码。
需要重新确认 CloudBase 构建来源和发布版本。
```

如果 `/readyz` 返回 503：

```text
说明 Flask 已部署新代码，但数据库、schema 或 content 依赖未 ready。
优先查看 /healthz/deep 的 database 和 content 字段。
```

## 4. 小程序验收

微信开发者工具中打开：

```text
pages/debug/index
```

依次验证：

```text
1. 切回云托管。
2. 测试 healthz。
3. 测试 assessments。
4. 测试 risk/check。
5. 测试 profile 最小请求。
```

普通页面逐页打开：

```text
首页
测一测
测评详情
测评结果
情绪温度计
训练
个性化训练方案
项目测试
项目详情
目标设定
情绪记录
反馈结果
训练卡
打卡
周报
消息
督导
我的
```

重点观察：

```text
1. 页面能打开。
2. 接口失败时不是空白页。
3. 错误提示不暴露数据库、SQL、堆栈、密钥或内部服务细节。
4. 401 后需要重新登录或重新授权。
5. 高风险内容不生成普通训练卡建议。
```

## 5. 当前已知状态

2026-07-02 本地补查：

```text
/healthz：200，CloudBase Flask 可用。
/healthz/deep：200，database.provider=mysql，database.ok=true。
/readyz：404，说明云端还未发布任务九新增代码。
已生成并校验本地上传包：.codex_tmp/safehome-cloudbase-task9-latest.zip。
SHA256：E2FB72F9291CF70074A4D993EE7F71209901A7A6B0E7C5E7EA140B826751E333。
```

当前结论：

```text
任务九本地自动项已完成。
任务九外部闭环剩余：发布当前分支到 CloudBase，并用本清单完成 /readyz 和小程序真机验收。
```

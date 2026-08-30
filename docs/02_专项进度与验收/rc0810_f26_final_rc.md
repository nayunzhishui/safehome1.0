# RC0810-F26 最终 RC 收口与发布建议

结论：**NO-GO**。本报告完成工程材料收口，不代表 RC 已形成、平台已批准、已发布或已稳定运行。

## 候选基线

- commit：`56b6a949ab8790f9eb5c6534dd08ebd403f646cf`
- tree：`251b74a0d04d39d5a2a6e5b9b4b12d3896e1e3bf`
- 打包方式：隔离 Git archive；未从脏工作区直接打包
- production 小程序 ZIP：`1a67a1c368d9151e80f05e7646dbc67a5584cea25c87e46bbdea38d50be52fc6`
- 后端镜像：`ghcr.io/nayunzhishui/safehome-rc0810@sha256:a4280975e3a838dbb42f52dc1b5bfc34a146b2eb61b421e5963543af78bf8e04`；Trivy CycloneDX SBOM 已绑定，扫描仍有 Critical/High 阻断，签名证明待外部核验

## 阻断原因

- official_required_ci_not_verified_for_candidate
- image_security_findings_and_signed_attestation_pending
- registry_raw_evidence_actions_artifact_pending
- wechat_platform_real_device_and_human_evidence_missing
- product_platform_engineering_professional_go_incomplete
- 72h_candidate_observation_not_executed
- wave_c_independent_review_pending

## 四方 GO

- product: pending_external（approved=false）
- platform: blocked_external（approved=false）
- engineering: blocked_required_ci_image_security（approved=false）
- professional: pending_external（approved=false）

## 阶段事实

- 工程材料完成：是
- RC 形成：否
- 平台审核通过：否
- 正式发布：否
- 稳定运行验证：否

## 发布演练

仅形成计划，未执行生产动作。候选观察窗口为 72 小时；回滚顺序为停止流量、代码、数据库、内容、数据核对。消息、外部 AI、导出和风险任务必须分别对账并执行补偿或通知。

## 下一动作

波次 C 先由固定 reviewer 独立审查累计 diff 与本证据包。之后仍须完成 required CI、关闭镜像安全发现并核验签名证明、微信平台与真机证据、四方签署和候选观察，才能重新判定 GO。

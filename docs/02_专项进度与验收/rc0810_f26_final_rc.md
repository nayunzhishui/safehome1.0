# RC0810-F26 最终 RC 收口与发布建议

结论：**NO-GO**。本报告完成工程材料收口，不代表 RC 已形成、平台已批准、已发布或已稳定运行。

## 候选基线

- commit：`8d1629b9af0f6bba4fff6b379374b124fbb991fa`
- tree：`cfb23353683be2112f5cfadeabde5af5f63e83ee`
- 打包方式：隔离 Git archive；未从脏工作区直接打包
- production 小程序 ZIP：`0726465e5a23b4a75fd308be7ba6c338595612eaa0dfb9791e11f67a9a47c78e`
- 后端镜像：`ghcr.io/nayunzhishui/safehome-rc0810@sha256:b9f1fd7bc19e81bc84dbf1d84f1edb889443470995284a5b4ee74c55dd16c20a`；Trivy CycloneDX SBOM 已绑定，扫描仍有 Critical/High 阻断，签名证明待外部核验

## 阻断原因

- official_required_ci_not_verified_for_candidate
- image_security_findings_and_signed_attestation_pending
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

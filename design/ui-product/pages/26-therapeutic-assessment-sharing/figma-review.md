# 资料与共享页 Figma 审查

- Figma 页面：`266:6`
- 默认态：`266:7`
- 只共享议题：`266:63`
- 议题和最近事件：`266:91`
- 暂不扩大共享：`266:124`
- 状态板：`266:162`

## 结果

- 页面只呈现本轮共享范围选择，没有暴露 scope、版本号、接口字段或虚构权限等级。
- 三条选项说明分别解释是否带入最近事件、人工查看范围及最小共享范围，均属于真实操作后果，予以保留。
- 未增加装饰性小字、重复免责声明、机器字段翻译或对界面显而易见内容的复述。
- 复用 `TherapeuticChoiceOption`、Button 与 PageState；Default、三种选中态、Saving、Offline、Error、SafetyPaused、LongContent 已覆盖。
- 五个根节点只使用 Noto Sans SC Regular/Medium；未绑定填充 0、未绑定描边 0、占位符 0。

结论：Figma 通过，可复用现有选择步骤组件实现。

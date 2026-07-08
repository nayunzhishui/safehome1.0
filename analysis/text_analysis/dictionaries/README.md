# 文本分析词典说明

本目录只用于离线、聚合、脱敏文本分析。

- `emotion_terms.json` 当前包含一个小样本 DLUT 风格情感本体字段：`word/category/polarity/intensity/arousal_weight/reflex_node`。
- 完整大连理工情感词汇本体或 BosonNLP 词库需由用户按原许可证自行获取并转换后放置，不能把未经确认授权的完整原始词库直接提交入仓。
- `scene_terms.json`、`person_terms.json`、`behavior_terms.json` 用于共现网络和情绪反射弧节点聚合。
- `stopwords.json` 用于 jieba 分词后的停用词过滤。

所有输出只能包含计数、均值、中心性和链条聚合，不输出原始自由文本。

// 内容浏览（研究者工作台“管理”页）：按类型看训练卡、量表、规则等内容的当前版本和审核状态。
// 只能看：改内容要走三方专业审核，生产环境的发布开关也锁着，不在手机上代填审核。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const PAGE = 20;
const TYPE_LABELS = {
  training_card: "训练卡",
  scale: "量表",
  worksheet: "测评表",
  course: "课程",
  program: "项目",
  feedback_rule: "反馈规则",
  diary_training_rule: "日记与练习对应规则",
  assessment_training_rule: "测评与练习对应规则",
  therapeutic_method: "评估方法",
  student_profile_rule: "学生画像规则",
  consent_text: "知情同意说明",
  privacy_text: "隐私说明",
  ai_safety_text: "AI 安全说明",
};
const STATUS_LABELS = {
  engineering_complete_expert_review_pending: "工程完成，待专业审核",
  approved: "已审核",
  draft: "草稿",
};

Component({
  data: {
    types: [],
    type: "training_card",
    items: [],
    shown: [],
    error: "",
    loading: false,
  },

  lifetimes: {
    attached() {
      this.load();
    },
  },

  methods: {
    async load() {
      this.setData({ loading: true, error: "" });
      try {
        const inventory = await api.getContentInventory();
        this.allItems = (inventory.items || []).map((item) => {
          const meta = item.source_metadata || {};
          const status = meta.governance_status || "";
          return {
            key: `${item.content_type}:${item.item_id}`,
            contentType: item.content_type,
            title: item.item_id,
            meta: [item.source_version, STATUS_LABELS[status] || status, item.governed_version ? `审核版 ${item.governed_version}` : ""]
              .filter(Boolean)
              .join(" · "),
            summary: meta.change_summary || "",
          };
        });
        const counts = {};
        this.allItems.forEach((item) => { counts[item.contentType] = (counts[item.contentType] || 0) + 1; });
        const types = Object.keys(counts)
          .sort((a, b) => counts[b] - counts[a])
          .map((id) => ({ id, label: `${TYPE_LABELS[id] || id} ${counts[id]}` }));
        const type = counts[this.data.type] ? this.data.type : (types[0] && types[0].id) || "";
        this.setData({ types, loading: false });
        this.showType(type);
      } catch (error) {
        this.setData({ loading: false, error: error.message || "内容清单暂时读不出来。" });
      }
    },

    showType(type) {
      const items = (this.allItems || []).filter((item) => item.contentType === type);
      this.setData({ type, items, shown: items.slice(0, PAGE) });
    },

    pickType(event) {
      this.showType(event.currentTarget.dataset.id);
    },

    showMore() {
      this.setData({ shown: this.data.items.slice(0, this.data.shown.length + PAGE) });
    },
  },
});

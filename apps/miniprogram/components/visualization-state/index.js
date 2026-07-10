const { visualizationState } = require("../../utils/relationshipStatus.generated");

Component({
  properties: {
    state: { type: String, value: "insufficient" },
    message: { type: String, value: "" },
  },
  data: {
    label: "数据不足",
    tone: "neutral",
    description: "",
  },
  observers: {
    "state,message": function syncState(state, message) {
      const value = visualizationState(state);
      this.setData({
        label: value.label,
        tone: value.tone,
        description: message || value.description,
      });
    },
  },
});

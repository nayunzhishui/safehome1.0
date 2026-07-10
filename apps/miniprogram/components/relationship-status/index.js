const { reportStatus } = require("../../utils/relationshipStatus.generated");

Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    status: { type: String, value: "" },
  },
  data: { label: "状态待核对", tone: "neutral" },
  observers: {
    status(value) {
      this.setData(reportStatus(value));
    },
  },
});

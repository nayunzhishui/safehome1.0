// StageHeader（Figma 642:447）：几节深色竹即第几阶段，其余竹节淡到 22%。
const JOINTS = [1, 2, 3];

Component({
  options: { styleIsolation: "apply-shared" },
  properties: {
    level: { type: Number, value: 1 },
    title: { type: String, value: "" },
    subtitle: { type: String, value: "" },
  },
  data: { joints: JOINTS },
});

// 数据导出（研究者工作台“管理”页，只有总管理）：先生成表格存到手机，再点一次发到微信（比如文件传输助手），
// 到电脑上打开。发出后手机里的这份文件会删掉。微信要求转发文件必须由点击直接触发，所以分两步。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const EXPORT_TYPES = [
  { id: "diaries", label: "情绪日记" },
  { id: "assessment_items", label: "测评答题明细" },
  { id: "assessment_wide", label: "按量表导出" },
  { id: "assessments", label: "测评总分" },
  { id: "checkins", label: "练习打卡" },
  { id: "goals", label: "目标" },
  { id: "feedback", label: "反馈" },
  { id: "reports", label: "本周复盘" },
  { id: "supervision", label: "人工支持" },
  { id: "records", label: "项目记录" },
];
const LIMITS = [1000, 5000];
// 文件名里不能有的字符：\ / : * ? " < > |（量表名里可能出现，比如“学业复原力/学业浮力”）。
const FILE_NAME_UNSAFE = new RegExp("[\\\\/:*?\\u0022<>|]", "g");
// 这两类带题目和每题得分；行数上限按“份答卷”算。量表清单和测一测同一份，加量表不用改这里。
const SCALE_TYPES = ["assessment_items", "assessment_wide"];
const TYPE_HINTS = {
  assessment_items: "每道题一行：题目、选了什么、得分、属于哪个维度。文字作答只给字数，不导出原文。",
  assessment_wide: "选一份量表，每份答卷一行：总分、各维度分，后面每题一列（列名是题目，格子里是这题的得分）。",
  assessments: "每份答卷一行，只有量表名和总分。",
};

function dateStamp() {
  const now = new Date();
  const pad = (number) => String(number).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
}

function removeFile(filePath) {
  if (!filePath) return;
  try {
    wx.getFileSystemManager().unlinkSync(filePath);
  } catch (error) {
    // 文件已经不在就不用管。
  }
}

Component({
  data: {
    types: EXPORT_TYPES,
    limits: LIMITS,
    type: "diaries",
    limit: 1000,
    typeHint: "",
    scaleLabels: ["全部量表"],
    scaleIndex: 0,
    busy: false,
    file: null,
    message: "",
  },

  lifetimes: {
    detached() {
      removeFile(this.data.file && this.data.file.path);
    },
  },

  methods: {
    pickType(event) {
      const type = event.currentTarget.dataset.id;
      this.discardFile();
      this.setData({ type, typeHint: TYPE_HINTS[type] || "", message: "" });
      if (SCALE_TYPES.includes(type) && !this.scales) this.loadScales();
    },

    async loadScales() {
      try {
        this.scales = (await api.getResearchAssessmentCatalog()).items || [];
        this.setData({ scaleLabels: ["全部量表", ...this.scales.map((item) => item.title)] });
      } catch (error) {
        this.setData({ message: error.message || "量表清单暂时读不出来，请稍后再试。" });
      }
    },

    pickScale(event) {
      this.discardFile();
      this.setData({ scaleIndex: Number(event.detail.value) || 0, message: "" });
    },

    pickLimit(event) {
      this.discardFile();
      this.setData({ limit: Number(event.currentTarget.dataset.limit), message: "" });
    },

    discardFile() {
      removeFile(this.data.file && this.data.file.path);
      if (this.data.file) this.setData({ file: null });
    },

    async generate() {
      if (this.data.busy) return;
      const scale = SCALE_TYPES.includes(this.data.type) ? (this.scales || [])[this.data.scaleIndex - 1] : null;
      if (this.data.type === "assessment_wide" && !scale) {
        this.setData({ message: "按量表导出要先选一份量表。" });
        return;
      }
      this.discardFile();
      this.setData({ busy: true, message: "" });
      const params = { type: this.data.type, limit: this.data.limit, worksheet_id: scale ? scale.id : undefined };
      try {
        let csv;
        try {
          csv = await api.exportResearchCsv(params);
        } catch (error) {
          if (error.code !== "high_risk_export_confirmation_required") throw error;
          const confirmed = await new Promise((resolve) => {
            wx.showModal({
              title: "包含高风险内容",
              content: "这次导出包含高风险或需要复核的内容。确定导出吗？导出会记在审计里。",
              confirmText: "导出",
              success: (result) => resolve(Boolean(result.confirm)),
              fail: () => resolve(false),
            });
          });
          if (!confirmed) {
            this.setData({ busy: false });
            return;
          }
          csv = await api.exportResearchCsv({ ...params, confirm_high_risk: 1 });
        }
        const lines = String(csv || "").split("\n").filter((line) => line.trim()).length;
        const rows = lines > 1 ? lines - 1 : 0;
        if (!rows) {
          this.setData({ busy: false, message: "这一类现在没有可导出的数据。" });
          return;
        }
        const label = (EXPORT_TYPES.find((item) => item.id === this.data.type) || {}).label || this.data.type;
        // 量表名里可能有“/”之类不能做文件名的字符。
        const name = `安心陪伴-${label}${scale ? `-${scale.title}` : ""}-${dateStamp()}.csv`.replace(FILE_NAME_UNSAFE, "-");
        const path = `${wx.env.USER_DATA_PATH}/${name}`;
        // 开头的 BOM 让 Excel 按 UTF-8 打开，中文不乱码；万一传输中丢了就补上。
        const text = String(csv);
        wx.getFileSystemManager().writeFileSync(path, text.charCodeAt(0) === 0xfeff ? text : `\ufeff${text}`, "utf8");
        this.setData({ busy: false, file: { path, name, rows }, message: `已生成 ${rows} 行。点“发到微信”，选文件传输助手或要发的人。` });
      } catch (error) {
        this.setData({ busy: false, message: error.message || "导出没有成功，请稍后再试。" });
      }
    },

    share() {
      const file = this.data.file;
      if (!file) return;
      wx.shareFileMessage({
        filePath: file.path,
        fileName: file.name,
        success: () => {
          removeFile(file.path);
          this.setData({ file: null, message: "已发出，手机里的这份文件已删掉。" });
        },
        fail: (error) => {
          const cancelled = /cancel/i.test(String((error && error.errMsg) || ""));
          this.setData({ message: cancelled ? "没有发出，文件还在，可以再点一次。" : "这台手机发不了文件，请把微信升级到最新版。" });
        },
      });
    },
  },
});

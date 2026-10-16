// 数据导出（研究者工作台“管理”页，只有总管理）：先生成表格存到手机，再点一次发到微信（比如文件传输助手），
// 到电脑上打开。发出后手机里的这份文件会删掉。微信要求转发文件必须由点击直接触发，所以分两步。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
const EXPORT_TYPES = [
  { id: "diaries", label: "情绪日记" },
  { id: "assessments", label: "测评结果" },
  { id: "checkins", label: "练习打卡" },
  { id: "goals", label: "目标" },
  { id: "feedback", label: "反馈" },
  { id: "reports", label: "本周复盘" },
  { id: "supervision", label: "人工支持" },
  { id: "records", label: "项目记录" },
];
const LIMITS = [1000, 5000];

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
      this.discardFile();
      this.setData({ type: event.currentTarget.dataset.id, message: "" });
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
      this.discardFile();
      this.setData({ busy: true, message: "" });
      const params = { type: this.data.type, limit: this.data.limit };
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
        const name = `安心陪伴-${label}-${dateStamp()}.csv`;
        const path = `${wx.env.USER_DATA_PATH}/${name}`;
        wx.getFileSystemManager().writeFileSync(path, csv, "utf8");
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

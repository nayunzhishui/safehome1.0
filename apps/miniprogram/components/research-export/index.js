// 数据导出（研究者工作台“管理”页，只有总管理）：先生成表格存到手机，再点一次发到微信（比如文件传输助手），
// 到电脑上打开。发出后手机里的这份文件会删掉。微信要求转发文件必须由点击直接触发，所以分两步。
// 加一种导出：后端 backend/routes/admin.py 的 export_csv 加类型，这里的 EXPORT_GROUPS 加一行。
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();
// scales：one 必须选一份量表，optional 可选一份，multi 可多选（不选=全部）。量表清单和测一测同一份，加量表不用改这里。
const EXPORT_GROUPS = [
  {
    title: "量表（带题目和得分）",
    types: [
      {
        id: "assessment_person_wide", label: "每人一行（多份量表并排）", unit: "人", scales: "multi",
        hint: "每人一行，选中的量表依次并排；同一份量表填过几次就有几组列，标“第1次、第2次…”和填写时间（北京时间）。不选量表就导出全部。",
      },
      {
        id: "assessment_wide", label: "按量表导出", unit: "份答卷", scales: "one",
        hint: "选一份量表，每份答卷一行：总分、各维度分，后面每题一列（列名是题目，格子里是这题的得分）。",
      },
      {
        id: "assessment_items", label: "测评答题明细", unit: "份答卷", scales: "optional",
        hint: "每道题一行：题目、选了什么、得分、属于哪个维度。文字作答只给字数，原文在“用户写的文字”里导。",
      },
      { id: "assessments", label: "测评总分", unit: "行", hint: "每份答卷一行，只有量表名和总分。" },
    ],
  },
  {
    title: "用户写的文字（原文）",
    types: [
      {
        id: "texts", label: "用户写的文字", unit: "条", sources: true,
        hint: "导出用户写的原文。手机号、邮箱、证件号、IP 会自动遮盖；人名、学校名认不出来，使用前请通读。每次导出都要确认，并记在审计里。",
      },
    ],
  },
  {
    title: "记录摘要（不含原文）",
    types: [
      { id: "diaries", label: "情绪日记" },
      { id: "checkins", label: "练习打卡" },
      { id: "goals", label: "目标" },
      { id: "feedback", label: "反馈" },
      { id: "reports", label: "本周复盘" },
      { id: "supervision", label: "人工支持" },
      { id: "records", label: "项目记录" },
    ],
  },
];
const TYPES = EXPORT_GROUPS.reduce((all, group) => all.concat(group.types), []);
// 与后端 research_text_export_service.TEXT_SOURCES 对应；加来源两边各加一行。
const TEXT_SOURCES = [
  { id: "diaries", label: "情绪日记" },
  { id: "checkins", label: "练习感想" },
  { id: "thermometer", label: "情绪温度计备注" },
  { id: "assessment_answers", label: "量表里的文字作答" },
];
// 后端要求再确认时返回的错误码 → 弹窗文字和确认后补带的参数。
const CONFIRMATIONS = {
  high_risk_export_confirmation_required: {
    param: "confirm_high_risk",
    title: "包含高风险内容",
    content: "这次导出包含高风险或需要复核的内容。确定导出吗？导出会记在审计里。",
  },
  raw_text_export_confirmation_required: {
    param: "confirm_raw_text",
    title: "导出用户原文",
    content: "表格里是用户写的原文。手机号、邮箱、证件号和 IP 已自动遮盖，人名等认不出来。只用于研究，用完请删掉文件。确定导出吗？",
  },
};
const LIMITS = [1000, 5000];
// 文件名里不能有的字符：\ / : * ? " < > |（量表名里可能出现，比如“学业复原力/学业浮力”）。
const FILE_NAME_UNSAFE = new RegExp("[\\\\/:*?\\u0022<>|]", "g");

function dateStamp() {
  const now = new Date();
  const pad = (number) => String(number).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
}

// 数据行数：引号里的换行（比如日记原文分段）不算新行。
function csvRowCount(text) {
  let rows = 0;
  let quoted = false;
  let content = false;
  for (const char of String(text || "").replace(/^﻿/, "")) {
    if (char === "\"") quoted = !quoted;
    if (char === "\n" && !quoted) {
      if (content) rows += 1;
      content = false;
    } else if (char.trim()) {
      content = true;
    }
  }
  if (content) rows += 1;
  return Math.max(rows - 1, 0);
}

function removeFile(filePath) {
  if (!filePath) return;
  try {
    wx.getFileSystemManager().unlinkSync(filePath);
  } catch (error) {
    // 文件已经不在就不用管。
  }
}

function confirmExport(confirmation) {
  return new Promise((resolve) => {
    wx.showModal({
      title: confirmation.title,
      content: confirmation.content,
      confirmText: "导出",
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false),
    });
  });
}

Component({
  data: {
    groups: EXPORT_GROUPS,
    limits: LIMITS,
    type: "diaries",
    typeInfo: TYPES.find((item) => item.id === "diaries"),
    limit: 1000,
    scaleLabels: ["全部量表"],
    scaleIndex: 0,
    scaleOptions: [],
    sourceLabels: TEXT_SOURCES.map((item) => item.label),
    sourceIndex: 0,
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
      const typeInfo = TYPES.find((item) => item.id === event.currentTarget.dataset.id);
      if (!typeInfo) return;
      this.discardFile();
      this.setData({ type: typeInfo.id, typeInfo, message: "" });
      if (typeInfo.scales && !this.scales) this.loadScales();
    },

    async loadScales() {
      try {
        this.scales = (await api.getResearchAssessmentCatalog()).items || [];
        this.setData({
          scaleLabels: ["全部量表", ...this.scales.map((item) => item.title)],
          scaleOptions: this.scales.map((item) => ({ id: item.id, title: item.title, checked: false })),
        });
      } catch (error) {
        this.scales = null;
        this.setData({ message: error.message || "量表清单暂时读不出来，请稍后再试。" });
      }
    },

    pickScale(event) {
      this.discardFile();
      this.setData({ scaleIndex: Number(event.detail.value) || 0, message: "" });
    },

    toggleScale(event) {
      const index = Number(event.currentTarget.dataset.index);
      const option = this.data.scaleOptions[index];
      if (!option) return;
      this.discardFile();
      this.setData({ [`scaleOptions[${index}].checked`]: !option.checked, message: "" });
    },

    pickSource(event) {
      this.discardFile();
      this.setData({ sourceIndex: Number(event.detail.value) || 0, message: "" });
    },

    pickLimit(event) {
      this.discardFile();
      this.setData({ limit: Number(event.currentTarget.dataset.limit), message: "" });
    },

    discardFile() {
      removeFile(this.data.file && this.data.file.path);
      if (this.data.file) this.setData({ file: null });
    },

    // 本次导出的参数和文件名里的说明（量表名、文字来源）。
    exportRequest() {
      const info = this.data.typeInfo;
      const params = { type: info.id, limit: this.data.limit };
      let detail = "";
      if (info.scales === "multi") {
        const picked = this.data.scaleOptions.filter((item) => item.checked);
        if (picked.length) params.worksheet_ids = picked.map((item) => item.id).join(",");
        detail = picked.length === 1 ? picked[0].title : picked.length ? `${picked.length}份量表` : "全部量表";
      } else if (info.scales) {
        const scale = (this.scales || [])[this.data.scaleIndex - 1];
        if (info.scales === "one" && !scale) return { error: "按量表导出要先选一份量表。" };
        if (scale) params.worksheet_id = scale.id;
        detail = scale ? scale.title : "";
      }
      if (info.sources) {
        const source = TEXT_SOURCES[this.data.sourceIndex];
        params.source = source.id;
        detail = source.label;
      }
      return { params, detail };
    },

    async generate() {
      if (this.data.busy) return;
      const request = this.exportRequest();
      if (request.error) {
        this.setData({ message: request.error });
        return;
      }
      this.discardFile();
      this.setData({ busy: true, message: "" });
      const params = { ...request.params };
      try {
        let csv;
        for (;;) {
          try {
            csv = await api.exportResearchCsv(params);
            break;
          } catch (error) {
            const confirmation = CONFIRMATIONS[error.code];
            if (!confirmation || params[confirmation.param]) throw error;
            if (!(await confirmExport(confirmation))) {
              this.setData({ busy: false });
              return;
            }
            params[confirmation.param] = 1;
          }
        }
        const rows = csvRowCount(csv);
        if (!rows) {
          this.setData({ busy: false, message: "这一类现在没有可导出的数据。" });
          return;
        }
        const name = `安心陪伴-${this.data.typeInfo.label}${request.detail ? `-${request.detail}` : ""}-${dateStamp()}.csv`
          .replace(FILE_NAME_UNSAFE, "-");
        const path = `${wx.env.USER_DATA_PATH}/${name}`;
        // 开头的 BOM 让 Excel 按 UTF-8 打开，中文不乱码；万一传输中丢了就补上。
        const text = String(csv);
        wx.getFileSystemManager().writeFileSync(path, text.charCodeAt(0) === 0xfeff ? text : `﻿${text}`, "utf8");
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

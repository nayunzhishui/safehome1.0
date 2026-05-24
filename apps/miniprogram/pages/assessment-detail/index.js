const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function withAnswerState(worksheet) {
  return {
    ...worksheet,
    questions: (worksheet.questions || []).map((question) => ({
      ...question,
      answerValue: "",
      answerScore: undefined,
    })),
  };
}

Page({
  data: {
    worksheetId: "",
    worksheet: null,
    loading: true,
    submitting: false,
    errorMessage: "",
  },

  onLoad(options) {
    const worksheetId = decodeURIComponent(options.id || "");
    this.setData({ worksheetId });
    this.loadWorksheet(worksheetId);
  },

  async loadWorksheet(worksheetId) {
    if (!worksheetId) {
      this.setData({ loading: false, errorMessage: "缺少工作表 ID。" });
      return;
    }

    this.setData({ loading: true, errorMessage: "" });
    try {
      const worksheet = await api.getAssessment(worksheetId);
      this.setData({
        worksheet: withAnswerState(worksheet),
        loading: false,
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "工作表读取失败，请确认 backend 是否已启动。",
      });
    }
  },

  onTextInput(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.setData({ [`worksheet.questions[${index}].answerValue`]: event.detail.value, errorMessage: "" });
  },

  selectOption(event) {
    const index = Number(event.currentTarget.dataset.index);
    const value = String(event.currentTarget.dataset.value);
    const scoreText = event.currentTarget.dataset.score;
    const score = scoreText === undefined || scoreText === "" ? undefined : Number(scoreText);
    this.setData({
      [`worksheet.questions[${index}].answerValue`]: value,
      [`worksheet.questions[${index}].answerScore`]: Number.isNaN(score) ? undefined : score,
      errorMessage: "",
    });
  },

  buildAnswers() {
    const worksheet = this.data.worksheet || {};
    return (worksheet.questions || []).map((question) => {
      const payload = {
        question_id: question.id,
        prompt: question.prompt,
        value: question.answerValue || "",
      };
      if (question.answerScore !== undefined) {
        payload.score = question.answerScore;
      }
      return payload;
    });
  },

  validateAnswers(answers) {
    const worksheet = this.data.worksheet || {};
    const missing = (worksheet.questions || []).filter((question) => {
      if (!question.required) return false;
      const answer = answers.find((item) => item.question_id === question.id);
      return !answer || !String(answer.value || "").trim();
    });
    return missing;
  },

  async submitWorksheet() {
    const worksheet = this.data.worksheet;
    if (!worksheet || this.data.submitting) return;

    const answers = this.buildAnswers();
    const missing = this.validateAnswers(answers);
    if (missing.length) {
      this.setData({ errorMessage: "还有必填内容没有填写，请先补充后再保存。" });
      return;
    }

    this.setData({ submitting: true, errorMessage: "" });
    try {
      const result = await api.createAssessmentResult({
        worksheet_id: worksheet.id,
        answers,
      });
      wx.showToast({ title: "已保存", icon: "success" });
      wx.navigateTo({
        url: `/pages/assessment-result/index?id=${encodeURIComponent(result.id)}&worksheet_id=${encodeURIComponent(worksheet.id)}`,
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "保存失败，请确认 backend 是否已启动。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },
});

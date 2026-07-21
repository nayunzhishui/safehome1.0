const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");

const api = createSafeHomeApi();

function cleanDisplayText(value) {
  return String(value || "")
    .replace(/请按照原工作表内容填写。当前电子版保留原文标题和来源，完整题项将按原 PDF 逐页补录。/g, "当前页面是电子版简化记录，先保留最小填写项。你可以按当前问题填写，完整内容后续再补充。")
    .replace(/请按照原工作表内容填写。/g, "请按当前问题填写。")
    .replace(/请填写原表中的/g, "请填写")
    .replace(/请填写原表中/g, "请填写")
    .replace(/原工作表/g, "测评内容")
    .replace(/原表/g, "当前内容")
    .replace(/\.pdf/gi, "")
    .replace(/PDF/g, "内容");
}

function cleanDisplayTitle(value) {
  return cleanDisplayText(value).replace(/^工作表\d+(?:\.\d+)?[：:\s]*/, "");
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function formatOption(option) {
  const value = String(option.value ?? option.score ?? "");
  const rawLabel = cleanDisplayText(option.label || value);
  const displayLabel = value ? rawLabel.replace(new RegExp(`^${escapeRegExp(value)}[\\.、\\s]*`), "") || rawLabel : rawLabel;
  return {
    ...option,
    value,
    displayLabel,
  };
}

function withAnswerState(worksheet) {
  const isStudentProfile = worksheet.id === "student_profile_v1" || worksheet.category === "学生画像";
  const isReference = !!worksheet.is_reference || worksheet.category === "示例参考";
  return {
    ...worksheet,
    display_title: isStudentProfile ? worksheet.display_title : cleanDisplayTitle(worksheet.display_title || worksheet.source_title),
    displaySourceText: isStudentProfile ? "支持性测评" : isReference ? "示例参考" : "电子版简化记录",
    instructions: cleanDisplayText(worksheet.instructions),
    sections: (worksheet.sections || []).map((section) => ({
      ...section,
      title: cleanDisplayTitle(section.title),
      content: cleanDisplayText(section.content),
    })),
    isStudentProfile,
    questions: (worksheet.questions || []).map((question) => ({
      ...question,
      prompt: cleanDisplayText(question.prompt),
      options: (question.options || []).map(formatOption),
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
    needsLogin: false,
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
  },

  onLoad(options) {
    const worksheetId = decodeURIComponent(options.id || "");
    if (!requireLogin({
      redirectUrl: `/pages/assessment-detail/index?id=${encodeURIComponent(worksheetId)}`,
      message: "请先登录后再填写测评。",
    })) {
      this.setData({ worksheetId, loading: false, needsLogin: true });
      return;
    }
    this.setData({ worksheetId });
    this.draftController = createResilientForm({
      storageKey: `safehome:resilientDraft:assessment:${worksheetId}`,
      fields: ["answers"],
      submissionPrefix: "assessment",
      hasContent: (values) => Array.isArray(values.answers) && values.answers.some((answer) => String(answer.value || "").trim()),
    });
    this.pendingDraft = this.draftController.restore();
    this.loadWorksheet(worksheetId);
  },

  onHide() {
    if (this.draftController && !this.data.submitting && this.data.worksheet) {
      this.setData(this.draftController.flush({ answers: this.buildAnswers() }));
    }
  },

  onUnload() {
    if (this.draftController && !this.data.submitting && this.data.worksheet) {
      this.draftController.flush({ answers: this.buildAnswers() });
    }
  },

  async loadWorksheet(worksheetId) {
    if (!worksheetId) {
      this.setData({ loading: false, errorMessage: "缺少工作表 ID。" });
      return;
    }

    this.setData({ loading: true, errorMessage: "" });
    try {
      const worksheet = await api.getAssessment(worksheetId);
      const hydrated = withAnswerState(worksheet);
      const restoredAnswers = this.pendingDraft && this.pendingDraft.values && this.pendingDraft.values.answers;
      if (Array.isArray(restoredAnswers)) {
        const answerMap = new Map(restoredAnswers.map((answer) => [answer.question_id, answer]));
        hydrated.questions = hydrated.questions.map((question) => {
          const answer = answerMap.get(question.id);
          return answer ? { ...question, answerValue: answer.value || "", answerScore: answer.score } : question;
        });
      }
      this.setData({
        worksheet: hydrated,
        loading: false,
        needsLogin: false,
        saveStatus: this.pendingDraft ? this.pendingDraft.saveStatus : "尚未填写",
        draftRestored: Boolean(this.pendingDraft),
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "内容暂时没能读取，请检查网络后再试一次。",
      });
    }
  },

  onTextInput(event) {
    const index = Number(event.currentTarget.dataset.index);
    this.setData({ [`worksheet.questions[${index}].answerValue`]: event.detail.value, errorMessage: "" }, () => this.scheduleDraftSave());
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
    }, () => this.scheduleDraftSave());
  },

  scheduleDraftSave() {
    if (!this.draftController) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule({ answers: this.buildAnswers() }, (status) => this.setData(status));
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

  getAnswerValue(answers, questionId) {
    const answer = answers.find((item) => item.question_id === questionId);
    return answer ? answer.value : "";
  },

  getAnswerScore(answers, questionId) {
    const answer = answers.find((item) => item.question_id === questionId);
    if (!answer) return undefined;
    if (answer.score !== undefined) return Number(answer.score);
    const parsed = Number(answer.value);
    return Number.isNaN(parsed) ? undefined : parsed;
  },

  buildProfilePayload(answers) {
    return {
      scores: {
        test_anxiety: this.getAnswerScore(answers, "test_anxiety"),
        iu_score: this.getAnswerScore(answers, "iu_score"),
        fear_score: this.getAnswerScore(answers, "fear_score"),
        self_compassion: this.getAnswerScore(answers, "self_compassion"),
      },
      support_resource: this.getAnswerValue(answers, "support_resource"),
      free_text: this.getAnswerValue(answers, "free_text"),
      client_submission_id: this.draftController ? this.draftController.getSubmissionId() : undefined,
    };
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

    if (this.draftController) this.setData(this.draftController.flush({ answers }));
    this.setData({ submitting: true, slowSubmitting: false, errorMessage: "" });
    this.slowTimer = setTimeout(() => this.setData({ slowSubmitting: true }), 8000);
    try {
      const result = worksheet.isStudentProfile
        ? await api.createProfile(this.buildProfilePayload(answers))
        : await api.createAssessmentResult({
            worksheet_id: worksheet.id,
            answers,
            client_submission_id: this.draftController ? this.draftController.getSubmissionId() : undefined,
          });
      const resultId = worksheet.isStudentProfile ? result.assessment_result_id : result.id;
      if (!resultId) {
        throw new Error("后端未返回结果 ID，请稍后重试。");
      }
      if (this.draftController) this.draftController.clear();
      wx.showToast({ title: "已保存", icon: "success" });
      wx.navigateTo({
        url: `/pages/assessment-result/index?id=${encodeURIComponent(resultId)}&worksheet_id=${encodeURIComponent(worksheet.id)}`,
      });
    } catch (error) {
      const needsLogin = error && (
        error.statusCode === 401
        || error.status === 401
        || error.code === "auth_required"
        || error.code === "unauthorized"
      );
      this.setData({
        needsLogin,
        errorMessage: error.message || "保存暂时没能完成，请检查网络后再试一次。你填写的内容还在。",
      });
    } finally {
      if (this.slowTimer) clearTimeout(this.slowTimer);
      this.setData({ submitting: false, slowSubmitting: false });
    }
  },

  goLogin() {
    requireLogin({
      redirectUrl: `/pages/assessment-detail/index?id=${encodeURIComponent(this.data.worksheetId)}`,
      message: "请先登录后再填写测评。",
    });
  },
});

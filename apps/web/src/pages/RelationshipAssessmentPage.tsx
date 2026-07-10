import { useEffect, useState } from "react";

import type { AssessmentProfilePosition, AssessmentResult, AssessmentWorksheet } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { formatSafeHomeError, SafeHomeApiClient } from "../services/safehomeApi";

const api = new SafeHomeApiClient();
const SCALE_IDS = new Set([
  "regulatory_focus_relationship_18",
  "micro_ysq_relationship_18",
  "relationship_initiation_intention_action",
]);

export function RelationshipAssessmentPage() {
  const user = getStoredAuthUser();
  const [worksheets, setWorksheets] = useState<AssessmentWorksheet[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [profile, setProfile] = useState<AssessmentProfilePosition | null>(null);
  const [message, setMessage] = useState("正在读取关系探索测评...");

  useEffect(() => {
    api.listAssessments({ audience_class: "student", q: "关系" })
      .then(async (payload) => {
        const items = payload.items.filter((item) => SCALE_IDS.has(item.id));
        const details = await Promise.all(items.map((item) => api.getAssessment(item.id)));
        setWorksheets(details);
        setSelectedId(details[0]?.id || "");
        setMessage(details.length ? "请选择一份量表开始填写。" : "当前没有可用的关系探索量表。");
      })
      .catch((error) => setMessage(formatSafeHomeError(error, "量表读取失败。")));
  }, []);

  const worksheet = worksheets.find((item) => item.id === selectedId) || null;

  function selectWorksheet(id: string) {
    setSelectedId(id);
    setAnswers({});
    setResult(null);
    setProfile(null);
  }

  async function submit() {
    if (!worksheet) return;
    const missing = worksheet.questions.filter((question) => question.required !== false && !answers[question.id]);
    if (missing.length) {
      setMessage(`还有 ${missing.length} 题未填写。`);
      return;
    }
    try {
      const saved = await api.createAssessmentResult({
        worksheet_id: worksheet.id,
        answers: worksheet.questions.map((question) => ({
          question_id: question.id,
          prompt: question.prompt,
          value: answers[question.id],
        })),
      });
      setResult(saved);
      const position = await api.getAssessmentProfilePosition(saved.id);
      setProfile(position);
      setMessage("测评已保存。以下为阶段性画像位置和支持性解释。");
    } catch (error) {
      setMessage(formatSafeHomeError(error, "提交失败，请检查登录状态后重试。"));
    }
  }

  if (!user || user.role !== "student") {
    return (
      <section className="dashboardShell">
        <div className="dashboardHeader"><div><p className="eyebrow">Relationship Pilot</p><h1>大学生关系探索测评</h1><p className="summary">当前只向已授权的学生试点账号开放。</p></div></div>
        <a className="primaryButton" href="/login">使用学生账号登录</a>
      </section>
    );
  }

  return (
    <section className="dashboardShell" aria-label="大学生关系探索测评">
      <div className="dashboardHeader">
        <div><p className="eyebrow">Relationship Pilot</p><h1>大学生关系探索测评</h1><p className="summary">三份量表分别计分和建模，不生成诊断、人格标签或关系能力排名。</p></div>
      </div>
      <div className="status">{message}</div>
      <label className="tokenField">选择量表
        <select value={selectedId} onChange={(event) => selectWorksheet(event.target.value)}>
          {worksheets.map((item) => <option key={item.id} value={item.id}>{item.display_title} · {item.questions.length}题</option>)}
        </select>
      </label>
      {worksheet && !result ? (
        <section className="guidanceBox">
          <h2>{worksheet.display_title}</h2><p>{worksheet.instructions}</p>
          <div className="recordList">
            {worksheet.questions.map((question, index) => (
              <fieldset className="recordItem" key={question.id}>
                <legend className="recordScene">{index + 1}. {question.prompt}</legend>
                {(question.options || []).map((option) => (
                  <label className="recordDescription" key={option.value}>
                    <input type="radio" name={question.id} value={option.value} checked={answers[question.id] === option.value} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))} /> {option.label}
                  </label>
                ))}
              </fieldset>
            ))}
          </div>
          <button className="primaryButton" type="button" onClick={() => void submit()}>提交并查看阶段性画像</button>
          <p className="muted">{worksheet.result_disclaimer}</p>
        </section>
      ) : null}
      {result && profile ? (
        <section className="guidanceBox">
          <h2>{profile.position?.can_use_interpretation ? profile.position.display_name || profile.position.profile_name : "本次只保留位置参考"}</h2>
          <p>{profile.explanation}</p>
          <p>{profile.strength_note}</p><p>{profile.small_step}</p>
          <h3>建议评估问题</h3><ul>{(profile.suggested_assessment_questions || []).map((question) => <li key={question}>{question}</li>)}</ul>
          <p className="muted">{profile.boundary_notice}</p>
          <a className="primaryButton" href="/student">返回学生入口</a>
        </section>
      ) : null}
    </section>
  );
}

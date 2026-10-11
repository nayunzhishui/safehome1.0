import { expect, test } from "@playwright/test";


const API = "http://127.0.0.1:5050";

test("研究者确认发送、下载脱敏与越权保护形成真实闭环", async ({ request }) => {
  const suffix = Date.now().toString(36);
  const register = await request.post(`${API}/api/auth/register`, {
    data: { username: `workflow_${suffix}`, password: "student-password-123", role: "student", nickname: "流程学生" },
  });
  expect(register.ok()).toBeTruthy();
  const student = (await register.json()).data;
  const studentHeaders = { Authorization: `Bearer ${student.token}` };

  const worksheetResponse = await request.get(`${API}/api/assessments/relationship_initiation_intention_action`);
  const worksheet = (await worksheetResponse.json()).data;
  const answers = worksheet.questions.map((question: { id: string; prompt: string; options: Array<{ value: string }> }) => ({
    question_id: question.id,
    prompt: question.prompt,
    value: question.options[0].value,
  }));
  const assessmentResponse = await request.post(`${API}/api/assessment-results`, {
    headers: studentHeaders,
    data: { worksheet_id: worksheet.id, answers },
  });
  expect(assessmentResponse.status()).toBe(201);
  const assessment = (await assessmentResponse.json()).data;

  const enrollmentResponse = await request.post(`${API}/api/relationship-pilot/enrollments`, {
    headers: studentHeaders,
    data: { research_consent: true, assessment_result_id: assessment.id },
  });
  expect(enrollmentResponse.status(), await enrollmentResponse.text()).toBe(201);
  const enrollment = (await enrollmentResponse.json()).data;

  // Current contract: students cannot author research feedback; researchers need object scope.
  const studentGeneration = await request.post(`${API}/api/relationship-pilot/enrollments/${enrollment.id}/report`, { headers: studentHeaders });
  expect(studentGeneration.status()).toBe(403);
  expect((await studentGeneration.json()).error.details.required_capability).toBe("research.feedback.write");

  const researcherLogin = await request.post(`${API}/api/auth/login`, {
    data: { username: "e2e_researcher", password: "e2e-password-123" },
  });
  expect(researcherLogin.ok(), await researcherLogin.text()).toBeTruthy();
  const researcher = (await researcherLogin.json()).data;
  const researcherHeaders = { Authorization: `Bearer ${researcher.token}` };
  const unassigned = await request.post(`${API}/api/relationship-pilot/enrollments/${enrollment.id}/report`, { headers: researcherHeaders });
  expect([403, 404]).toContain(unassigned.status());
  const claim = await request.post(`${API}/api/research/access/enrollments/${enrollment.id}/claim`, {
    headers: { ...researcherHeaders, "Idempotency-Key": `claim-${suffix}` },
  });
  expect(claim.status(), await claim.text()).toBe(201);
  const reportResponse = await request.post(`${API}/api/relationship-pilot/enrollments/${enrollment.id}/report`, { headers: researcherHeaders });
  expect(reportResponse.status(), await reportResponse.text()).toBe(201);
  const report = (await reportResponse.json()).data;
  const pendingDownload = await request.get(`${API}/api/relationship-pilot/reports/${report.id}?download=1`, { headers: studentHeaders });
  expect(pendingDownload.status()).toBe(409);

  const other = await request.post(`${API}/api/auth/register`, {
    data: { username: `other_${suffix}`, password: "student-password-123", role: "student" },
  });
  const otherToken = (await other.json()).data.token;
  const forbidden = await request.get(`${API}/api/relationship-pilot/reports/${report.id}`, { headers: { Authorization: `Bearer ${otherToken}` } });
  // Do not disclose the existence of another participant's report.
  expect(forbidden.status()).toBe(404);
  expect((await forbidden.json()).error.code).toBe("not_found");
  expect((await request.post(`${API}/api/relationship-pilot/reports/${report.id}/confirm`, { headers: researcherHeaders })).status()).toBe(200);
  expect((await request.post(`${API}/api/relationship-pilot/reports/${report.id}/send`, { headers: researcherHeaders })).status()).toBe(201);
  expect((await request.post(`${API}/api/relationship-pilot/reports/${report.id}/send`, { headers: researcherHeaders })).status()).toBe(200);

  const download = await request.get(`${API}/api/relationship-pilot/reports/${report.id}?download=1`, { headers: studentHeaders });
  expect(download.ok()).toBeTruthy();
  const text = await download.text();
  expect(text).not.toContain("assessment_result_id");
  expect(text).not.toContain("model_id");
  expect(text).not.toContain("research_notes");
});

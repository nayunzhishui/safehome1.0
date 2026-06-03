import { useEffect, useMemo, useState, type MouseEvent } from "react";

import { safeHomeApi as api } from "../services/safehomeApi";
import type {
  ParentAssessmentPayload,
  ParentAssessmentResult,
  ProfileDimension,
  SandplaySymbol,
  ProfileVisuals,
  ScaleDefinition,
  ScaleItem,
  StudentAssessmentPayload,
  StudentProfileRecord,
  StudentProfileResult,
} from "../../../../shared/types/api";

type LoadState = "loading" | "ready" | "saving" | "error";
type ViewMode = "block" | "single";

function pathId(pattern: RegExp): string {
  const match = window.location.pathname.match(pattern);
  return match ? decodeURIComponent(match[1]) : "";
}

function asNumber(value: string | number | null | undefined): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function totalScaleItems(scales: ScaleDefinition[]): number {
  return scales.reduce((total, scale) => total + scale.items.length, 0);
}

function answeredScaleItems(scales: ScaleDefinition[], answers: Record<string, string>): number {
  return scales.reduce((total, scale) => total + scale.items.filter((item) => Boolean(answers[item.item_code])).length, 0);
}

function dimensionRows(record?: StudentProfileRecord | StudentProfileResult | null): ProfileDimension[] {
  if (!record) return [];
  if ("dimensions" in record && Array.isArray(record.dimensions)) return record.dimensions;
  if ("dimensions_json" in record && record.dimensions_json) {
    try {
      return JSON.parse(record.dimensions_json) as ProfileDimension[];
    } catch {
      return [];
    }
  }
  return [];
}

function ProgressHeader({
  current,
  total,
  answered,
  totalAnswers,
}: {
  current: number;
  total: number;
  answered: number;
  totalAnswers: number;
}) {
  const percent = total <= 1 ? 100 : Math.round(((current + 1) / total) * 100);
  return (
    <div className="progress-wrap" aria-label="答题进度">
      <div className="progress-bar"><span style={{ width: `${percent}%` }} /></div>
      <span>第 {current + 1} 步 / {total}</span>
      <span className="answer-progress">已完成 {answered} / {totalAnswers} 题</span>
    </div>
  );
}

function LikertQuestion({
  item,
  value,
  onChange,
}: {
  item: ScaleItem;
  value: string;
  onChange: (value: string) => void;
}) {
  const options = [
    ["1", "完全不符合"],
    ["2", "有点不符合"],
    ["3", "基本符合"],
    ["4", "比较符合"],
    ["5", "完全符合"],
  ];
  return (
    <fieldset className="question-card scale-item">
      <legend>
        <span>{item.display_order}</span>
        {item.text}
      </legend>
      <div className="likert-grid">
        {options.map(([optionValue, label]) => (
          <label className={`likert-option ${value === optionValue ? "active" : ""}`} key={optionValue}>
            <input type="radio" checked={value === optionValue} value={optionValue} onChange={() => onChange(optionValue)} />
            <span>{label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function ScaleFields({
  scales,
  answers,
  onChange,
  viewMode,
  activeScaleIndex,
}: {
  scales: ScaleDefinition[];
  answers: Record<string, string>;
  onChange: (itemCode: string, value: string) => void;
  viewMode: ViewMode;
  activeScaleIndex?: number;
}) {
  const visibleScales = viewMode === "single" && activeScaleIndex !== undefined ? scales.slice(activeScaleIndex, activeScaleIndex + 1) : scales;
  return (
    <div className="detailStack">
      {visibleScales.map((scale) => {
        const answered = scale.items.filter((item) => answers[item.item_code]).length;
        return (
          <section className="guidanceBox scale-block" key={scale.scale_code}>
            <div className="scale-heading">
              <p className="eyebrow">{scale.scale_code}</p>
              <h3>{scale.short_name || scale.name}</h3>
              <p>{scale.score_direction}</p>
              <span className="countBadge">本板块 {answered} / {scale.items.length} 题</span>
            </div>
            {scale.items.map((item) => (
              <LikertQuestion
                item={item}
                key={item.item_code}
                value={answers[item.item_code] || ""}
                onChange={(value) => onChange(item.item_code, value)}
              />
            ))}
          </section>
        );
      })}
    </div>
  );
}

function RadarChart({ visuals }: { visuals?: ProfileVisuals | null }) {
  const rows = visuals?.radar || [];
  if (!rows.length) return <p>暂无图表数据。</p>;
  const cx = 170;
  const cy = 150;
  const r = 100;
  const points = rows.map((item, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / rows.length;
    const radius = r * clamp(item.value / item.max, 0, 1);
    return `${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`;
  });
  return (
    <div className="chart-box">
      <svg viewBox="0 0 340 300" role="img" aria-label="维度雷达图">
        {[0.25, 0.5, 0.75, 1].map((level) => (
          <polygon
            fill="none"
            key={level}
            points={rows.map((_, index) => {
              const angle = -Math.PI / 2 + (Math.PI * 2 * index) / rows.length;
              return `${cx + Math.cos(angle) * r * level},${cy + Math.sin(angle) * r * level}`;
            }).join(" ")}
            stroke="#d8e2eb"
          />
        ))}
        {rows.map((item, index) => {
          const angle = -Math.PI / 2 + (Math.PI * 2 * index) / rows.length;
          return (
            <g key={item.label}>
              <line x1={cx} y1={cy} x2={cx + Math.cos(angle) * r} y2={cy + Math.sin(angle) * r} stroke="#d8e2eb" />
              <text x={cx + Math.cos(angle) * (r + 32)} y={cy + Math.sin(angle) * (r + 32)} textAnchor="middle" fontSize="12">
                {item.label}
              </text>
            </g>
          );
        })}
        <polygon points={points.join(" ")} fill="#2B6CB055" stroke="#2B6CB0" strokeWidth="2" />
      </svg>
    </div>
  );
}

function PcaChart({ visuals }: { visuals?: ProfileVisuals | null }) {
  const pca = visuals?.pca;
  if (!pca?.user) return <p>暂无 PCA 位置数据。</p>;
  const colors = ["#2B6CB0", "#C05621", "#2F855A", "#805AD5", "#B83280"];
  const points = pca.points || [];
  const xs = points.map((point) => point.pc1).concat([Number(pca.user.pc1 || 0)]);
  const ys = points.map((point) => point.pc2).concat([Number(pca.user.pc2 || 0)]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const sx = (x: number) => 32 + ((x - minX) / (maxX - minX || 1)) * 316;
  const sy = (y: number) => 248 - ((y - minY) / (maxY - minY || 1)) * 210;
  return (
    <div className="chart-box">
      <svg viewBox="0 0 380 280" role="img" aria-label="PCA 分类位置">
        <line x1="32" y1="248" x2="356" y2="248" stroke="#9aa6b2" />
        <line x1="32" y1="24" x2="32" y2="248" stroke="#9aa6b2" />
        {points.slice(0, 220).map((point, index) => (
          <circle
            cx={sx(point.pc1).toFixed(1)}
            cy={sy(point.pc2).toFixed(1)}
            fill={colors[(point.cluster_id - 1) % colors.length]}
            key={`${point.pc1}-${point.pc2}-${index}`}
            opacity="0.45"
            r="2"
          />
        ))}
        <circle cx={sx(Number(pca.user.pc1 || 0)).toFixed(1)} cy={sy(Number(pca.user.pc2 || 0)).toFixed(1)} r="7" fill="#111827" stroke="#fff" strokeWidth="2">
          <title>你的位置</title>
        </circle>
      </svg>
      <p className="muted">PC1：{pca.user.pc1 ?? "未计算"}；PC2：{pca.user.pc2 ?? "未计算"}；聚类：{pca.user.cluster_id ?? "需人工查看"}。</p>
    </div>
  );
}

function TrendChart({ visuals }: { visuals?: ProfileVisuals | null }) {
  const items = visuals?.trends || [];
  if (!items.length) return <p>暂无轮次数据。</p>;
  const sx = (index: number) => 35 + (index / Math.max(1, items.length - 1)) * 300;
  const sy = (value: number) => 240 - ((value - 1) / 4) * 190;
  const path = items.map((item, index) => `${index ? "L" : "M"}${sx(index).toFixed(1)},${sy(Number(item.state_score || 1)).toFixed(1)}`).join(" ");
  return (
    <div className="chart-box">
      <svg viewBox="0 0 380 280" role="img" aria-label="轮次状态变化">
        <line x1="35" y1="240" x2="340" y2="240" stroke="#9aa6b2" />
        <line x1="35" y1="40" x2="35" y2="240" stroke="#9aa6b2" />
        <path d={path} fill="none" stroke="#C05621" strokeWidth="2" />
        {items.map((item, index) => (
          <circle cx={sx(index)} cy={sy(Number(item.state_score || 1))} fill="#C05621" key={`${item.label}-${index}`} r="4">
            <title>{item.label}: {item.state_score}</title>
          </circle>
        ))}
        <text x="12" y="45" fontSize="11">5</text>
        <text x="12" y="242" fontSize="11">1</text>
      </svg>
    </div>
  );
}

function KeywordChart({ visuals }: { visuals?: ProfileVisuals | null }) {
  const keywords = visuals?.keywords || [];
  if (!keywords.length) return <p className="muted">暂未识别到关键词。后续轮次填写文本后会显示变化。</p>;
  const max = Math.max(...keywords.map((item) => item.count));
  return (
    <div className="keywordChart">
      {keywords.map((item) => (
        <div className="keyword-row" key={item.word}>
          <span>{item.word}</span>
          <i style={{ width: `${Math.max(8, (item.count / max) * 72)}%` }} />
          <strong>{item.count}</strong>
        </div>
      ))}
    </div>
  );
}

function SandplayBoard({
  symbols,
  onSave,
}: {
  symbols: SandplaySymbol[];
  onSave: (scene: { symbols: Array<{ id: string; type: string; label?: string; x: number; y: number }> }, reflection: string) => Promise<void>;
}) {
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [items, setItems] = useState<Array<{ id: string; type: string; label?: string; x: number; y: number }>>([]);
  const [reflection, setReflection] = useState("");
  const [summary, setSummary] = useState("");
  const symbolLookup = useMemo(() => Object.fromEntries(symbols.map((symbol) => [symbol.type, symbol])), [symbols]);

  function boardPoint(event: MouseEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = clamp(((event.clientX - rect.left) / rect.width) * 100, 0, 100);
    const y = clamp(((event.clientY - rect.top) / rect.height) * 100, 0, 100);
    return { x: Number(x.toFixed(1)), y: Number(y.toFixed(1)) };
  }

  function addSymbol(event: MouseEvent<HTMLDivElement>) {
    if (!selectedSymbol || items.length >= 12) return;
    const point = boardPoint(event);
    const meta = symbolLookup[selectedSymbol];
    setItems((current) => [
      ...current,
      {
        id: `${selectedSymbol}-${Date.now()}-${current.length}`,
        type: selectedSymbol,
        label: meta?.label || selectedSymbol,
        ...point,
      },
    ]);
  }

  async function save() {
    if (!items.length) {
      setSummary("请至少放入 1 个象征物后再保存。");
      return;
    }
    await onSave({ symbols: items }, reflection);
    const resourceCount = items.filter((item) => symbolLookup[item.type]?.category === "resource").length;
    const stressCount = items.filter((item) => symbolLookup[item.type]?.category === "stress").length;
    setSummary(`已保存：象征物 ${items.length} 个，压力象征 ${stressCount} 个，资源象征 ${resourceCount} 个。`);
  }

  return (
    <div className="sandplay-layout">
      <div>
        <div className="sandplay-palette" aria-label="象征物选择">
          {symbols.map((symbol) => (
            <button
              className={`symbol-button ${selectedSymbol === symbol.type ? "active" : ""}`}
              key={symbol.type}
              type="button"
              onClick={() => setSelectedSymbol(symbol.type)}
            >
              {symbol.mark} {symbol.label}
            </button>
          ))}
        </div>
        <div className="sandplay-board" role="application" aria-label="意象沙盘板" onClick={addSymbol}>
          {items.map((item) => {
            const meta = symbolLookup[item.type];
            return (
              <button
                className={`sand-symbol ${meta?.category || "other"}`}
                key={item.id}
                style={{ left: `${item.x}%`, top: `${item.y}%` }}
                type="button"
                title={meta?.label || item.type}
                onClick={(event) => {
                  event.stopPropagation();
                  setItems((current) => current.filter((currentItem) => currentItem.id !== item.id));
                }}
              >
                {meta?.mark || "?"}
              </button>
            );
          })}
        </div>
        <div className="sandplay-actions">
          <button className="secondaryButton" type="button" onClick={() => setItems([])}>清空沙盘</button>
          <span className="muted">选择象征物后点击沙盘放置；点击已放置象征物可移除。</span>
        </div>
      </div>
      <aside className="sandplay-side">
        <label className="tokenField">
          写一句你对这个场景的理解
          <textarea value={reflection} maxLength={600} onChange={(event) => setReflection(event.target.value)} />
        </label>
        <button className="primaryButton" type="button" onClick={save}>保存沙盘记录</button>
        {summary ? <p className="status ready">{summary}</p> : null}
      </aside>
    </div>
  );
}

export function AboutStudyPage() {
  return (
    <div className="landingPage">
      <header className="landingNav">
        <a className="brandMark landingBrand" href="/">
          <span className="landingBrandIcon" aria-hidden="true" />
          <span>
            <strong>安心家</strong>
            <small>研究说明</small>
          </span>
        </a>
        <nav className="landingLinks">
          <a href="/student">学生画像</a>
          <a href="/assessment">家长测评</a>
          <a href="/dashboard">研究后台</a>
        </nav>
      </header>
      <section className="landingHero">
        <div className="heroText">
          <p className="eyebrow">Study Boundary</p>
          <h1>研究说明与使用边界</h1>
          <p className="heroCopy">
            安心家把旧 ReadFeedback 的学生画像、家长测评和后台导出整合为一个支持性研究平台。所有报告只用于自我理解、练习推荐和研究资料整理，不构成诊断。
          </p>
          <div className="heroActions">
            <a className="primaryButton landingPrimary" href="/student/assessment">进入学生测评</a>
            <a className="secondaryButton landingSecondary" href="/assessment">进入家长测评</a>
          </div>
        </div>
      </section>
      <section className="landingSection ethicsSection">
        <div className="ethicsList">
          <div className="ethicsItem">自由文本只作为辅助线索，不作为诊断依据。</div>
          <div className="ethicsItem">聚类画像是阶段性支持参考，不代表固定人格。</div>
          <div className="ethicsItem">高风险表达需要优先联系现实中的可信成年人或专业支持资源。</div>
          <div className="ethicsItem">研究导出应默认匿名化、脱敏，并保留审计记录。</div>
        </div>
      </section>
    </div>
  );
}

export function StudentEntryPage() {
  return (
    <div className="landingPage">
      <header className="landingNav">
        <a className="brandMark landingBrand" href="/">
          <span className="landingBrandIcon" aria-hidden="true" />
          <span>
            <strong>安心家</strong>
            <small>学生阶段性画像</small>
          </span>
        </a>
        <nav className="landingLinks">
          <a href="/about-study">研究说明</a>
          <a href="/assessment">家长测评</a>
        </nav>
      </header>
      <section className="landingHero">
        <div className="heroText">
          <p className="eyebrow">Student Profile</p>
          <h1>学生阶段性压力反应画像</h1>
          <p className="heroCopy">
            通过考试压力、不确定性耐受、自我支持和情绪调节灵活性四类线索，生成非诊断的阶段性支持画像，并推荐一个小练习。
          </p>
          <div className="heroActions">
            <a className="primaryButton landingPrimary" href="/student/assessment">开始填写</a>
            <a className="secondaryButton landingSecondary" href="/about-study">先看边界</a>
          </div>
        </div>
      </section>
    </div>
  );
}

export function StudentAssessmentPage() {
  const [payload, setPayload] = useState<StudentAssessmentPayload | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>({});
  const [participantCode, setParticipantCode] = useState("");
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [researchConsent, setResearchConsent] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("block");
  const [step, setStep] = useState(0);
  const [status, setStatus] = useState<LoadState>("loading");
  const [message, setMessage] = useState("正在读取学生测评题目...");

  useEffect(() => {
    api
      .getStudentAssessment()
      .then((data) => {
        setPayload(data);
        setStatus("ready");
        setMessage(data.boundary_notice);
      })
      .catch((error) => {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "学生测评题目读取失败。");
      });
  }, []);

  async function submit() {
    if (!payload) return;
    if (!consentAccepted) {
      setStatus("error");
      setMessage("请先确认本测评用于自我理解和研究反馈，不构成诊断。");
      return;
    }
    const requiredCodes = payload.scales.flatMap((scale) => scale.items.map((item) => item.item_code));
    const missing = requiredCodes.filter((code) => !answers[code]);
    if (missing.length) {
      setStatus("error");
      setMessage(`还有 ${missing.length} 道题未完成。`);
      return;
    }
    setStatus("saving");
    setMessage("正在生成阶段性画像...");
    try {
      const result = await api.createProfile({
        nickname: participantCode || undefined,
        answers,
        text_answers: textAnswers,
        free_text: Object.values(textAnswers).join(" "),
        support_resource: researchConsent ? "同意匿名研究分析" : "仅生成个人反馈",
        round: 1,
      });
      window.location.href = `/student/report/${encodeURIComponent(result.student_profile_id || "")}`;
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "提交失败，请确认后端服务已启动。");
    }
  }

  const totalSteps = payload ? payload.scales.length + 2 : 1;
  const totalItems = payload ? totalScaleItems(payload.scales) : 0;
  const answeredItems = payload ? answeredScaleItems(payload.scales, answers) : 0;
  const activeScaleIndex = clamp(step - 1, 0, Math.max(0, (payload?.scales.length || 1) - 1));
  const isIntroStep = step === 0;
  const isSubmitStep = payload ? step === totalSteps - 1 : false;

  function goNext() {
    if (!payload) return;
    if (isIntroStep && !consentAccepted) {
      setStatus("error");
      setMessage("请先勾选知情提示。");
      return;
    }
    setStatus("ready");
    setMessage(payload.boundary_notice);
    setStep((current) => clamp(current + 1, 0, totalSteps - 1));
  }

  return (
    <section className="dashboardShell">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Student Assessment</p>
          <h1>学生阶段性画像测评</h1>
          <p className="summary">请按最近两周的真实体验填写。结果用于支持性反馈，不构成诊断。</p>
        </div>
        <a className="secondaryButton" href="/student">返回学生入口</a>
      </div>
      <div className={`status ${status}`}>{message}</div>
      {payload ? (
        <>
          <div className="view-toggle" aria-label="测评显示方式">
            <button className={`view-toggle-button ${viewMode === "block" ? "active" : ""}`} type="button" onClick={() => setViewMode("block")}>板块模式</button>
            <button className={`view-toggle-button ${viewMode === "single" ? "active" : ""}`} type="button" onClick={() => setViewMode("single")}>一题一屏</button>
          </div>
          <ProgressHeader current={step} total={totalSteps} answered={answeredItems} totalAnswers={totalItems} />

          {isIntroStep ? (
            <section className="guidanceBox consent-panel">
              <h2>开始前，请先了解</h2>
              <ul>
                <li>这不是医学或心理疾病诊断。</li>
                <li>匿名编号用于后续追踪，可不填写真实姓名。</li>
                <li>画像来自研究聚类模型，只作为阶段性支持参考。</li>
                <li>如出现自伤、自杀或严重安全风险，请优先联系线下专业支持。</li>
              </ul>
              <label className="tokenField">
                匿名编号（可选）
                <input value={participantCode} maxLength={80} onChange={(event) => setParticipantCode(event.target.value)} placeholder="例如 S001" />
              </label>
              <label className="check-row">
                <input checked={consentAccepted} type="checkbox" onChange={(event) => setConsentAccepted(event.target.checked)} />
                <span>我了解本测评用于自我理解和研究反馈，不构成临床诊断。</span>
              </label>
              <label className="check-row">
                <input checked={researchConsent} type="checkbox" onChange={(event) => setResearchConsent(event.target.checked)} />
                <span>我同意匿名结果用于研究分析。</span>
              </label>
            </section>
          ) : null}

          {!isIntroStep && !isSubmitStep ? (
            <ScaleFields
              activeScaleIndex={viewMode === "single" ? activeScaleIndex : undefined}
              answers={answers}
              onChange={(code, value) => setAnswers((current) => ({ ...current, [code]: value }))}
              scales={payload.scales}
              viewMode={viewMode}
            />
          ) : null}

          {isSubmitStep ? (
            <section className="guidanceBox submit-review">
              <h2>准备提交</h2>
              <p>请确认四个量表板块均已完成。提交后会生成非诊断的阶段性画像报告。</p>
              <div className="review-counts">
                {payload.scales.map((scale) => (
                  <span key={scale.scale_code}>{scale.short_name} {scale.items.filter((item) => answers[item.item_code]).length} / {scale.items.length} 题</span>
                ))}
              </div>
              <h3>结构化文本</h3>
              {payload.open_questions.map((question) => (
                <label className="tokenField" key={question.item_code}>
                  {question.label}
                  <textarea
                    value={textAnswers[question.item_code] || ""}
                    maxLength={question.max_length}
                    onChange={(event) => setTextAnswers((current) => ({ ...current, [question.item_code]: event.target.value }))}
                    placeholder="可简短填写，也可以留空。"
                  />
                </label>
              ))}
            </section>
          ) : null}

          <div className="form-footer flow-footer">
            <button className="secondaryButton" disabled={step === 0 || status === "saving"} type="button" onClick={() => setStep((current) => clamp(current - 1, 0, totalSteps - 1))}>上一步</button>
            {!isSubmitStep ? (
              <button className="primaryButton" type="button" onClick={goNext}>下一步</button>
            ) : (
              <button className="primaryButton" type="button" onClick={submit} disabled={status === "saving"}>
                {status === "saving" ? "生成中..." : "生成画像报告"}
              </button>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}

export function StudentReportPage() {
  const id = useMemo(() => pathId(/^\/student\/report\/([^/]+)$/), []);
  const [record, setRecord] = useState<StudentProfileRecord | null>(null);
  const [visuals, setVisuals] = useState<ProfileVisuals | null>(null);
  const [status, setStatus] = useState<LoadState>("loading");
  const [message, setMessage] = useState("正在读取学生画像报告...");
  const [followupText, setFollowupText] = useState("");
  const [stateScore, setStateScore] = useState("3");

  useEffect(() => {
    async function load() {
      try {
        const [detail, visualData] = await Promise.all([api.getProfileResult(id), api.getProfileVisuals(id)]);
        setRecord(detail);
        setVisuals(visualData);
        setStatus("ready");
        setMessage(detail.boundary_notice || "本画像只用于支持性理解和练习推荐，不构成诊断。");
      } catch (error) {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "报告读取失败。");
      }
    }
    if (id) load();
  }, [id]);

  async function saveFollowup() {
    setStatus("saving");
    try {
      await api.createProfileFollowup(id, {
        round_no: 1,
        fit: "待人工查看",
        task_done: "学生端提交",
        state_score: asNumber(stateScore),
        text: followupText,
      });
      setStatus("ready");
      setMessage("追踪反馈已保存。");
      setFollowupText("");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "追踪反馈保存失败。");
    }
  }

  async function saveSandplay(scene: { symbols: Array<{ id: string; type: string; label?: string; x: number; y: number }> }, reflection: string) {
    await api.createProfileSandplay(id, {
      task_title: record?.report?.sandplay_task?.title || "沙盘式表达任务",
      scene,
      reflection_text: reflection,
    });
    setMessage("沙盘表达记录已保存。");
  }

  const dimensions = dimensionRows(record);

  return (
    <section className="dashboardShell">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Student Report</p>
          <h1>{record?.profile_name || "学生画像报告"}</h1>
          <p className="summary">{record?.report?.summary || "正在读取报告内容。"}</p>
        </div>
        <a className="secondaryButton" href="/student/assessment">重新填写</a>
      </div>
      <div className={`status ${status}`}>{message}</div>
      {record ? (
        <>
          <section className="metricGrid">
            {(record.report?.metrics || []).map((metric) => (
              <article className="metricCard" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </article>
            ))}
            <article className="metricCard">
              <span>模型</span>
              <strong>{record.model_type || "KMeans/PCA"}</strong>
            </article>
          </section>

          <section className="dashboardGrid twoColumn visual-grid">
            <article className="panel">
              <h2>维度雷达图</h2>
              <RadarChart visuals={visuals} />
            </article>
            <article className="panel">
              <h2>画像分类位置</h2>
              <PcaChart visuals={visuals} />
            </article>
            <article className="panel">
              <h2>轮次状态变化</h2>
              <TrendChart visuals={visuals} />
            </article>
            <article className="panel">
              <h2>文本关键词</h2>
              <KeywordChart visuals={visuals} />
            </article>
          </section>

          <section className="panel">
            <h2>为什么会落在这一类</h2>
            <p>{record.report?.mechanism || record.report?.summary || "暂无机制解释。"}</p>
            <h3>首轮任务</h3>
            <p className="task-card">{record.report?.first_task || "先完成一次情绪命名练习。"}</p>
            <div className="detailBlock">
              <h3>维度观察</h3>
              {dimensions.map((dimension) => (
                <p key={dimension.key}><strong>{dimension.label}</strong>：{dimension.summary}</p>
              ))}
            </div>
          </section>

          <section className="panel">
            <h2>标本同治：整合干预路径</h2>
            <div className="path-grid">
              {Object.entries(record.report?.integrative_path || {}).map(([name, text]) => (
                <article key={name}>
                  <strong>{name}</strong>
                  <p>{text}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <h2>下一轮收束问题</h2>
            <ul>
              {(record.report?.next_questions || []).map((question) => <li key={question}>{question}</li>)}
            </ul>
            <p className="risk">{record.report?.escalation}</p>
          </section>

          <section className="panel">
            <h2>第 1/2/3 轮追踪</h2>
            <div className="followup-form">
              <label className="tokenField">
                画像吻合度
                <select defaultValue="部分像我">
                  <option>像我</option>
                  <option>部分像我</option>
                  <option>不像我</option>
                </select>
              </label>
              <label className="tokenField">
                任务完成情况
                <select defaultValue="部分完成">
                  <option>已完成</option>
                  <option>部分完成</option>
                  <option>未完成</option>
                </select>
              </label>
              <label className="tokenField">
                当前考试压力 1-5
                <select value={stateScore} onChange={(event) => setStateScore(event.target.value)}>
                  {[1, 2, 3, 4, 5].map((value) => <option value={value} key={value}>{value}</option>)}
                </select>
              </label>
              <label className="tokenField wide">
                这一轮的变化或困难
                <textarea value={followupText} maxLength={600} onChange={(event) => setFollowupText(event.target.value)} />
              </label>
              <button className="primaryButton" type="button" onClick={saveFollowup}>保存这一轮</button>
            </div>
          </section>

          <section className="panel sandplay-panel">
            <div className="sectionHeader">
              <div>
                <p className="eyebrow">沙盘式表达任务</p>
                <h2>{record.report?.sandplay_task?.title || "沙盘式表达任务"}</h2>
              </div>
              <span className="countBadge">表达线索，不做诊断</span>
            </div>
            <p>{record.report?.sandplay_task?.prompt || "用象征物摆出当前压力、资源和下一步行动的位置。"}</p>
            <p className="muted">{record.report?.sandplay_task?.focus}</p>
            <SandplayBoard symbols={record.report?.sandplay_task?.symbols || []} onSave={saveSandplay} />
            <div className="guidanceBox">
              <h3>反思问题</h3>
              <ul>
                {(record.report?.sandplay_task?.reflection_questions || []).map((question) => <li key={question}>{question}</li>)}
              </ul>
            </div>
            <p className="risk">{record.report?.sandplay_task?.safety_note}</p>
          </section>
        </>
      ) : null}
    </section>
  );
}

export function ParentAssessmentPage() {
  const [payload, setPayload] = useState<ParentAssessmentPayload | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [questionAnswers, setQuestionAnswers] = useState<Record<string, string>>({});
  const [participantCode, setParticipantCode] = useState("");
  const [studyBatch, setStudyBatch] = useState("");
  const [sourceChannel, setSourceChannel] = useState("safehome-web");
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [researchConsent, setResearchConsent] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("block");
  const [step, setStep] = useState(0);
  const [status, setStatus] = useState<LoadState>("loading");
  const [message, setMessage] = useState("正在读取家长测评题目...");
  const startedAt = useMemo(() => new Date().toISOString(), []);

  useEffect(() => {
    api
      .getParentAssessment()
      .then((data) => {
        setPayload(data);
        setStatus("ready");
        setMessage(data.boundary_notice);
      })
      .catch((error) => {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "家长测评读取失败。");
      });
  }, []);

  async function submit() {
    if (!payload) return;
    if (!consentAccepted) {
      setStatus("error");
      setMessage("请先确认已了解说明，并同意提交答题以生成支持性反馈。");
      return;
    }
    const requiredCodes = payload.scales.scales.flatMap((scale) => scale.items.map((item) => item.item_code));
    const missing = requiredCodes.filter((code) => !answers[code]);
    if (missing.length) {
      setStatus("error");
      setMessage(`还有 ${missing.length} 道量表题未完成。`);
      return;
    }
    setStatus("saving");
    setMessage("正在生成家长支持性反馈...");
    try {
      const result = await api.createParentAssessment({
        participant_code: participantCode,
        research_consent: researchConsent,
        study_batch: studyBatch,
        source_channel: sourceChannel,
        started_at: startedAt,
        completed_at: new Date().toISOString(),
        answers,
        question_answers: questionAnswers,
      });
      window.location.href = `/assessment/report/${encodeURIComponent(result.id)}`;
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "提交失败，请确认后端服务已启动。");
    }
  }

  const scales = payload?.scales.scales || [];
  const totalSteps = scales.length + 2;
  const totalItems = totalScaleItems(scales);
  const answeredItems = answeredScaleItems(scales, answers);
  const activeScaleIndex = clamp(step - 1, 0, Math.max(0, scales.length - 1));
  const isIntroStep = step === 0;
  const isSubmitStep = step === totalSteps - 1;

  function goNext() {
    if (isIntroStep && !consentAccepted) {
      setStatus("error");
      setMessage("请先勾选知情提示。");
      return;
    }
    setStatus("ready");
    setMessage(payload?.boundary_notice || "");
    setStep((current) => clamp(current + 1, 0, totalSteps - 1));
  }

  return (
    <section className="dashboardShell">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Parent Assessment</p>
          <h1>家长双量表测评</h1>
          <p className="summary">用于观察自我关怀和不确定性耐受，生成支持性反馈报告。</p>
        </div>
        <a className="secondaryButton" href="/about-study">查看研究说明</a>
      </div>
      <div className={`status ${status}`}>{message}</div>
      {payload ? (
        <>
          <div className="view-toggle" aria-label="测评显示方式">
            <button className={`view-toggle-button ${viewMode === "block" ? "active" : ""}`} type="button" onClick={() => setViewMode("block")}>板块模式</button>
            <button className={`view-toggle-button ${viewMode === "single" ? "active" : ""}`} type="button" onClick={() => setViewMode("single")}>一题一屏</button>
          </div>
          <ProgressHeader current={step} total={totalSteps} answered={answeredItems} totalAnswers={totalItems} />

          {isIntroStep ? (
            <section className="guidanceBox consent-panel">
              <h2>开始前，请先了解</h2>
              <ul>
                <li>这不是医学或心理疾病诊断。</li>
                <li>测评不要求填写姓名、手机号等强身份信息。</li>
                <li>匿名研究使用同意与生成反馈同意分开记录。</li>
                <li>如需删除数据，可联系项目负责人并提供报告编号或匿名编号。</li>
              </ul>
              <div className="metadata-grid">
                <label className="tokenField">
                  匿名编号
                  <input value={participantCode} maxLength={80} onChange={(event) => setParticipantCode(event.target.value)} placeholder="例如 P001，可留空" />
                </label>
                <label className="tokenField">
                  研究批次
                  <input value={studyBatch} maxLength={80} onChange={(event) => setStudyBatch(event.target.value)} placeholder="例如 2026春季试点，可留空" />
                </label>
                <label className="tokenField">
                  来源渠道
                  <input value={sourceChannel} maxLength={80} onChange={(event) => setSourceChannel(event.target.value)} placeholder="例如 家长课堂/学校/社群" />
                </label>
              </div>
              <label className="check-row">
                <input checked={consentAccepted} type="checkbox" onChange={(event) => setConsentAccepted(event.target.checked)} />
                <span>我已了解说明，并同意提交答题以生成支持性反馈。</span>
              </label>
              <label className="check-row">
                <input checked={researchConsent} type="checkbox" onChange={(event) => setResearchConsent(event.target.checked)} />
                <span>我同意将匿名数据用于研究分析和量表优化。</span>
              </label>
            </section>
          ) : null}

          {!isIntroStep && !isSubmitStep ? (
            <ScaleFields
              activeScaleIndex={viewMode === "single" ? activeScaleIndex : undefined}
              answers={answers}
              onChange={(code, value) => setAnswers((current) => ({ ...current, [code]: value }))}
              scales={scales}
              viewMode={viewMode}
            />
          ) : null}

          {isSubmitStep ? (
            <section className="guidanceBox submit-review">
              <h2>准备提交</h2>
              <p>请确认两个量表板块均已完成。提交后会生成一份非诊断性的研究反馈报告。</p>
              <div className="review-counts">
                {scales.map((scale) => (
                  <span key={scale.scale_code}>{scale.short_name} {scale.items.filter((item) => answers[item.item_code]).length} / {scale.items.length} 题</span>
                ))}
              </div>
              <h3>补充问题</h3>
              {payload.questions.questions.map((question) => (
                <label className="tokenField" key={question.id}>
                  {question.text}
                  {question.type === "textarea" ? (
                    <textarea value={questionAnswers[question.id] || ""} onChange={(event) => setQuestionAnswers((current) => ({ ...current, [question.id]: event.target.value }))} />
                  ) : (
                    <select value={questionAnswers[question.id] || ""} onChange={(event) => setQuestionAnswers((current) => ({ ...current, [question.id]: event.target.value }))}>
                      <option value="">请选择</option>
                      {(question.options || []).map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}
                    </select>
                  )}
                </label>
              ))}
            </section>
          ) : null}

          <div className="form-footer flow-footer">
            <button className="secondaryButton" disabled={step === 0 || status === "saving"} type="button" onClick={() => setStep((current) => clamp(current - 1, 0, totalSteps - 1))}>上一步</button>
            {!isSubmitStep ? (
              <button className="primaryButton" type="button" onClick={goNext}>下一步</button>
            ) : (
              <button className="primaryButton" type="button" onClick={submit} disabled={status === "saving"}>
                {status === "saving" ? "生成中..." : "生成研究反馈"}
              </button>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}

export function ParentReportPage() {
  const id = useMemo(() => pathId(/^\/assessment\/report\/([^/]+)$/), []);
  const [record, setRecord] = useState<ParentAssessmentResult | null>(null);
  const [status, setStatus] = useState<LoadState>("loading");
  const [message, setMessage] = useState("正在读取家长测评报告...");

  useEffect(() => {
    if (!id) return;
    api
      .getParentAssessmentResult(id)
      .then((data) => {
        setRecord(data);
        setStatus("ready");
        setMessage(data.report.boundary_notice);
      })
      .catch((error) => {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "家长报告读取失败。");
      });
  }, [id]);

  async function saveAction(actionKey: string) {
    setStatus("saving");
    try {
      await api.createParentReportAction(id, actionKey);
      setStatus("ready");
      setMessage("行动反馈已保存。");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "行动反馈保存失败。");
    }
  }

  const report = record?.report as (ParentAssessmentResult["report"] & {
    scale_report?: Record<string, {
      name: string;
      score_direction: string;
      mean: number;
      total: number;
      dimensions?: Record<string, { mean: number; total: number }>;
    }>;
  }) | undefined;

  return (
    <section className="dashboardShell">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Parent Report</p>
          <h1>{record?.report.role || "家长支持性反馈报告"}</h1>
          <p className="summary">{record?.report.summary || "正在读取报告内容。"}</p>
        </div>
        <a className="secondaryButton" href="/assessment">重新填写</a>
      </div>
      <div className={`status ${status}`}>{message}</div>
      {record ? (
        <>
          <section className="dashboardGrid twoColumn">
            <article className="panel">
              <span>报告定位</span>
              <h2>支持性反馈，不作诊断</h2>
              <p>这份报告用于帮助你理解近期体验，不用于判断人格、能力或亲子关系好坏。</p>
            </article>
            <article className="panel">
              <span>测评内容</span>
              <h2>自我关怀 × 不确定性体验</h2>
              <p>系统会保留量表分数与维度结果，便于后续研究分析和服务优化。</p>
            </article>
          </section>

          <section className="metricGrid">
            {record.report.metrics.map((metric) => (
              <article className="metricCard" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </article>
            ))}
          </section>

          {report?.scale_report ? (
            <section className="dashboardGrid twoColumn scale-results">
              {Object.entries(report.scale_report).map(([scaleCode, scale]) => (
                <article className="panel scale-result-card" key={scaleCode}>
                  <p className="eyebrow">{scaleCode}</p>
                  <h2>{scale.name}</h2>
                  <p>{scale.score_direction}</p>
                  <div className="score-dashboard">
                    <div className="score-main">
                      <span>均分</span>
                      <strong>{Number(scale.mean || 0).toFixed(2)}</strong>
                      <small>总分 {scale.total}</small>
                    </div>
                    <div className="score-bar" aria-label={`${scale.name}均分进度`}>
                      <span style={{ width: `${Math.round((Number(scale.mean || 0) / 5) * 100)}%` }} />
                    </div>
                  </div>
                  <h3>维度均分</h3>
                  <div className="dimension-list">
                    {Object.entries(scale.dimensions || {}).map(([dimension, score]) => (
                      <div className="dimension-score-row" key={dimension}>
                        <div>
                          <span>{dimension}</span>
                          <strong>{Number(score.mean || 0).toFixed(2)}</strong>
                        </div>
                        <div className="dimension-bar" aria-hidden="true">
                          <span style={{ width: `${Math.round((Number(score.mean || 0) / 5) * 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </section>
          ) : null}

          <section className="dashboardGrid twoColumn report-interpretation">
            <article className="panel">
              <h2>如何理解结果</h2>
              <p>分数反映的是你近期在相关题项上的自我报告体验，可以帮助你观察压力中的应对方式。它更适合被当作一次自我觉察，而不是固定结论。</p>
            </article>
            <article className="panel">
              <h2>结果不代表什么</h2>
              <p>本报告不代表医学或心理疾病诊断，不用于判断人格好坏、亲子关系好坏，也不说明你是不是“合格父母”。</p>
            </article>
          </section>

          <section className="dashboardGrid twoColumn">
            <article className="panel">
              <h2>结果说明</h2>
              <p>{record.report.empathy}</p>
            </article>
            <article className="panel">
              <h2>你的资源</h2>
              <p>{record.report.strength}</p>
            </article>
            <article className="panel action-card">
              <span>一个小练习</span>
              <h2>{record.report.action_title}</h2>
              <p>{record.report.action}</p>
            </article>
            <article className="panel next-step">
              <span>适合你的下一步</span>
              <h2>{record.report.course}</h2>
              <p>如果你愿意继续参与追踪测评或了解后续研究反馈，可以记录这个意向。试点期不会自动跳转或要求付款。</p>
            </article>
          </section>

          <section className="panel">
            <h2>行动反馈</h2>
            <div className="dashboardActions">
              <button className="primaryButton" type="button" onClick={() => saveAction(record.report.course)}>我愿意了解后续研究</button>
              <button className="secondaryButton" type="button" onClick={() => window.print()}>保存或打印报告</button>
              <a className="secondaryButton" href="/assessment">再测一次</a>
              <a className="secondaryButton" href="/">返回首页</a>
            </div>
          </section>
        </>
      ) : null}
    </section>
  );
}

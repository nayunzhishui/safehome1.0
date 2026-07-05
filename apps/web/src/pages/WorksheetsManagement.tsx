import { useEffect, useMemo, useState } from "react";

import { formatSafeHomeError, SafeHomeApiClient } from "../services/safehomeApi";
import { getStoredAdminToken, setStoredAdminToken } from "../services/adminToken";
import type { AdminWorksheet, AdminWorksheetInput } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

const api = new SafeHomeApiClient();

const emptyForm: AdminWorksheetInput = {
  id: "",
  display_title: "",
  source_title: "",
  source_file: "",
  category: "支持性测评",
  audience_class: "student_support",
  reflex_node: "",
  profile_model_id: "",
  review_status: "pilot_review_required",
  enabled_for_user: false,
  boundary_notice: "本测评只用于自我理解、练习推荐和后续复测参考，不用于诊断、筛查或贴标签。",
  result_disclaimer: "结果仅供支持性参考，不能替代专业咨询、诊断或紧急帮助。",
  instructions: "",
  scoring: "",
  source_version: "manual_admin",
  source_type: "database_admin",
  pages: 1,
  sections: [],
  questions: [],
  recommended_card_ids: [],
};

function boolText(value?: boolean) {
  return value ? "用户端可见" : "用户端隐藏";
}

function normalizeList(value?: string | string[]) {
  if (Array.isArray(value)) return value;
  return String(value || "")
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formFromWorksheet(item: AdminWorksheet): AdminWorksheetInput {
  return {
    ...item,
    profile_model_id: item.profile_model_id || "",
    recommended_card_ids: item.recommended_card_ids || [],
    search_keywords: item.search_keywords || [],
  };
}

export function WorksheetsManagement() {
  const [adminToken, setAdminToken] = useState(getStoredAdminToken);
  const [worksheets, setWorksheets] = useState<AdminWorksheet[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [form, setForm] = useState<AdminWorksheetInput>(emptyForm);
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [message, setMessage] = useState("正在准备测评题库管理。");

  const selected = useMemo(() => worksheets.find((item) => item.id === selectedId), [selectedId, worksheets]);
  const enabledCount = worksheets.filter((item) => item.enabled_for_user).length;

  async function loadWorksheets() {
    setStatus("loading");
    setMessage("正在读取数据库中的测评题库。");
    try {
      const response = await api.listAdminWorksheets(adminToken.trim());
      setWorksheets(response.items);
      const nextSelected = selectedId || response.items[0]?.id || "";
      setSelectedId(nextSelected);
      if (nextSelected) {
        const item = response.items.find((worksheet) => worksheet.id === nextSelected);
        if (item) setForm(formFromWorksheet(item));
      }
      setStatus("success");
      setMessage("已读取数据库测评题库。这里管理的是小程序实际读取的 assessment_worksheets。");
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "读取测评题库失败。"));
    }
  }

  useEffect(() => {
    void loadWorksheets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateField<K extends keyof AdminWorksheetInput>(key: K, value: AdminWorksheetInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function selectWorksheet(id: string) {
    const item = worksheets.find((worksheet) => worksheet.id === id);
    setSelectedId(id);
    setForm(item ? formFromWorksheet(item) : emptyForm);
  }

  function startCreate() {
    setSelectedId("");
    setForm({ ...emptyForm });
  }

  async function saveWorksheet() {
    if (!form.id?.trim()) {
      setStatus("error");
      setMessage("请先填写量表 ID。");
      return;
    }
    if (!form.display_title?.trim()) {
      setStatus("error");
      setMessage("请先填写量表名称。");
      return;
    }

    setStatus("loading");
    setMessage("正在保存测评题库。");
    const payload: AdminWorksheetInput = {
      ...form,
      id: form.id.trim(),
      display_title: form.display_title.trim(),
      source_title: form.source_title || form.display_title,
      search_keywords: normalizeList(form.search_keywords),
      recommended_card_ids: normalizeList(form.recommended_card_ids),
      profile_model_id: form.profile_model_id || null,
      pages: Number(form.pages || 1),
    };
    if (!selected) {
      payload.enabled_for_user = false;
    } else if (payload.enabled_for_user) {
      delete payload.enabled_for_user;
    }

    try {
      const saved = selected
        ? await api.updateAdminWorksheet(selected.id, payload, adminToken.trim())
        : await api.createAdminWorksheet(payload, adminToken.trim());
      setSelectedId(saved.id);
      setForm(formFromWorksheet(saved));
      await loadWorksheets();
      setStatus("success");
      setMessage("已保存测评题库配置。开放到小程序前仍需人工核对题项、选项和边界。");
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "保存测评题库失败。"));
    }
  }

  async function disableWorksheet() {
    if (!selected) return;
    setStatus("loading");
    setMessage("正在隐藏该测评。");
    try {
      const saved = await api.disableAdminWorksheet(selected.id, adminToken.trim());
      setForm(formFromWorksheet(saved));
      await loadWorksheets();
      setStatus("success");
      setMessage("已将该测评从用户端隐藏，原始记录和内容库未删除。");
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "隐藏测评失败。"));
    }
  }

  return (
    <section className="dashboardShell" aria-label="测评题库管理">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Assessment Worksheets</p>
          <h1>测评题库管理</h1>
          <p className="summary">
            管理数据库中的小程序测评入口、开放状态和画像模型绑定。这里不编辑题项原文，题项仍以内容库和人工验收为准。
          </p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/content/scales">
            量表目录审核
          </a>
          <button className="primaryButton" type="button" onClick={loadWorksheets} disabled={status === "loading"}>
            {status === "loading" ? "刷新中..." : "刷新题库"}
          </button>
        </div>
      </div>

      <div className={`status ${status}`}>{message}</div>

      <section className="guidanceBox" aria-label="后台令牌">
        <label className="tokenField">
          后台令牌
          <input
            type="password"
            value={adminToken}
            onChange={(event) => {
              setAdminToken(event.target.value);
              setStoredAdminToken(event.target.value);
            }}
            placeholder="请输入 X-Admin-Token"
          />
        </label>
      </section>

      <div className="metricGrid" aria-label="题库状态">
        <MetricCard label="数据库测评" value={worksheets.length} />
        <MetricCard label="用户端可见" value={enabledCount} />
        <MetricCard label="暂不开放" value={worksheets.length - enabledCount} />
        <MetricCard label="已绑画像模型" value={worksheets.filter((item) => item.profile_model_id).length} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="测评列表">
          <div className="sectionTitleRow">
            <h2>测评入口</h2>
            <button className="secondaryButton" type="button" onClick={startCreate}>
              新增入口
            </button>
          </div>
          <div className="recordList">
            {worksheets.map((item) => (
              <button
                className={`recordItem ${selectedId === item.id ? "active" : ""}`}
                key={item.id}
                type="button"
                onClick={() => selectWorksheet(item.id)}
              >
                <span className="recordScene">{item.display_title}</span>
                <span className="recordDescription">{item.boundary_notice || "未填写边界说明"}</span>
                <span className="recordMeta">
                  {item.category || "未分类"} · {boolText(item.enabled_for_user)}
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="detailPanel" aria-label="测评配置">
          <div className="sectionTitleRow">
            <h2>{selected ? "编辑测评入口" : "新增测评入口"}</h2>
            <span className="countBadge">{selected ? selected.id : "new"}</span>
          </div>

          <div className="detailContent">
            <label className="tokenField">
              量表 ID
              <input value={form.id || ""} onChange={(event) => updateField("id", event.target.value)} disabled={Boolean(selected)} />
            </label>
            <label className="tokenField">
              量表名称
              <input value={form.display_title || ""} onChange={(event) => updateField("display_title", event.target.value)} />
            </label>
            <label className="tokenField">
              来源标题
              <input value={form.source_title || ""} onChange={(event) => updateField("source_title", event.target.value)} />
            </label>
            <label className="tokenField">
              来源文件
              <input value={form.source_file || ""} onChange={(event) => updateField("source_file", event.target.value)} />
            </label>
            <label className="tokenField">
              分类
              <input value={form.category || ""} onChange={(event) => updateField("category", event.target.value)} />
            </label>
            <label className="tokenField">
              用户分组
              <input value={form.audience_class || ""} onChange={(event) => updateField("audience_class", event.target.value)} />
            </label>
            <label className="tokenField">
              反射节点
              <input value={form.reflex_node || ""} onChange={(event) => updateField("reflex_node", event.target.value)} />
            </label>
            <label className="tokenField">
              画像模型 ID
              <input value={form.profile_model_id || ""} onChange={(event) => updateField("profile_model_id", event.target.value)} />
            </label>
            <label className="tokenField">
              审核状态
              <input value={form.review_status || ""} onChange={(event) => updateField("review_status", event.target.value)} />
            </label>
            <div className="status idle">
              当前开放状态：{form.enabled_for_user ? "用户端可见" : "用户端隐藏"}。本页不能直接开放测评，开放必须走内容审核流程；如需下线可点击“隐藏入口”。
            </div>
            <label className="tokenField">
              边界说明
              <textarea value={form.boundary_notice || ""} onChange={(event) => updateField("boundary_notice", event.target.value)} />
            </label>
            <label className="tokenField">
              结果免责声明
              <textarea value={form.result_disclaimer || ""} onChange={(event) => updateField("result_disclaimer", event.target.value)} />
            </label>
            <label className="tokenField">
              推荐训练卡 ID
              <input
                value={normalizeList(form.recommended_card_ids).join("，")}
                onChange={(event) => updateField("recommended_card_ids", normalizeList(event.target.value))}
              />
            </label>

            <div className="dashboardActions">
              <button className="primaryButton" type="button" onClick={saveWorksheet} disabled={status === "loading"}>
                保存配置
              </button>
              {selected ? (
                <button className="secondaryButton" type="button" onClick={disableWorksheet} disabled={status === "loading"}>
                  隐藏入口
                </button>
              ) : null}
            </div>

            <section className="guidanceBox" aria-label="题库管理边界">
              <h3>管理边界</h3>
              <p>这里只管理数据库入口、用户端可见状态和画像模型绑定，不自动确认题项正确性。</p>
              <p>题项文字、选项、题序、计分和反向题仍需使用人工验收表逐项核对。</p>
            </section>
          </div>
        </section>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="metricCard">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

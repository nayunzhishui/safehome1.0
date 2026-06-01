import { useMemo, useState } from "react";

import { ADMIN_EXPORT_TYPES } from "../../../../shared/constants/api";
import { SafeHomeApiClient } from "../services/safehomeApi";

type ExportType = (typeof ADMIN_EXPORT_TYPES)[number];
type LoadStatus = "idle" | "loading" | "success" | "error";

interface ExportState {
  status: LoadStatus;
  message: string;
  previewText: string;
}

const api = new SafeHomeApiClient();
const LOCAL_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token";

const EXPORT_TYPE_LABELS: Record<ExportType, string> = {
  goals: "目标数据",
  diaries: "情绪记录",
  feedback: "反馈结果",
  checkins: "打卡记录",
  assessments: "测一测结果",
  profile: "学生画像",
  reports: "周报记录",
  supervision: "督导请求",
  cards: "训练卡内容",
};

const EXPORT_TYPE_NOTES: Record<ExportType, string> = {
  goals: "用于查看试点目标设定情况。",
  diaries: "用于查看家长提交的情绪事件记录。",
  feedback: "用于查看规则反馈结果和推荐卡片线索。",
  checkins: "用于查看训练卡练习后的打卡情况。",
  assessments: "用于查看测一测填写结果。",
  profile: "用于导出学生画像摘要，默认匿名化且不含自由文本原文。",
  reports: "用于查看已经生成的周度复盘记录。",
  supervision: "用于查看家长提交的人工补充支持请求。",
  cards: "用于查看后端训练卡表中的内容快照。",
};

export function ExportManagement() {
  const [exportType, setExportType] = useState<ExportType>("diaries");
  const [userId, setUserId] = useState("");
  const [adminToken, setAdminToken] = useState(LOCAL_ADMIN_EXPORT_TOKEN);
  const [state, setState] = useState<ExportState>({
    status: "idle",
    message: "请选择导出类型，可先预览 CSV 前几行，再按需保存文件。",
    previewText: "",
  });

  const exportUrl = useMemo(() => {
    return api.buildAdminExportUrl({
      type: exportType,
      user_id: userId.trim() || undefined,
    });
  }, [exportType, userId]);

  const canFilterByUser = exportType !== "cards";
  const selectedNote = EXPORT_TYPE_NOTES[exportType];

  async function readCsvBlob() {
    return api.downloadAdminExport({
      type: exportType,
      user_id: canFilterByUser ? userId.trim() || undefined : undefined,
      adminToken: adminToken.trim(),
    });
  }

  async function previewExport() {
    setState({
      status: "loading",
      message: "正在读取导出内容...",
      previewText: "",
    });

    try {
      const blob = await readCsvBlob();
      const text = (await blob.text()).replace(/^\uFEFF/, "");
      const preview = text
        .split(/\r?\n/)
        .filter(Boolean)
        .slice(0, 8)
        .join("\n");

      setState({
        status: "success",
        message: preview ? "已读取 CSV 预览。" : "接口返回为空内容。",
        previewText: preview || "empty",
      });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "读取失败，请确认 backend 是否已启动，令牌是否正确。",
        previewText: "",
      });
    }
  }

  async function saveExport() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在准备 CSV 文件...",
    }));

    try {
      const blob = await readCsvBlob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `safehome_${exportType}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      setState((current) => ({
        ...current,
        status: "success",
        message: "CSV 文件已准备完成。",
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: error instanceof Error ? error.message : "导出失败，请确认 backend 是否已启动，令牌是否正确。",
      }));
    }
  }

  return (
    <section className="dashboardShell" aria-label="数据导出后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Data Export</p>
          <h1>数据导出</h1>
          <p className="summary">复用现有后台 CSV 导出接口，用于试点数据核对和研究资料整理。导出前请确认使用场景和数据保护要求。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <button className="primaryButton" type="button" onClick={previewExport} disabled={state.status === "loading"}>
            {state.status === "loading" ? "读取中..." : "预览 CSV"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <div className="metricGrid" aria-label="导出概况">
        <MetricCard label="导出类型" value={ADMIN_EXPORT_TYPES.length} />
        <MetricCard label="当前类型" value={EXPORT_TYPE_LABELS[exportType]} />
        <MetricCard label="用户筛选" value={canFilterByUser ? "可用" : "不适用"} />
        <MetricCard label="接口格式" value="CSV" />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="导出设置">
          <div className="sectionTitleRow">
            <h2>导出设置</h2>
            <span className="countBadge">只读</span>
          </div>

          <label className="tokenField">
            导出类型
            <select value={exportType} onChange={(event) => setExportType(event.target.value as ExportType)}>
              {ADMIN_EXPORT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {EXPORT_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
          </label>

          <label className="tokenField">
            用户 ID（可选）
            <input
              type="text"
              value={canFilterByUser ? userId : ""}
              disabled={!canFilterByUser}
              onChange={(event) => setUserId(event.target.value)}
              placeholder={canFilterByUser ? "例如 demo-parent" : "训练卡内容不按用户筛选"}
            />
          </label>

          <label className="tokenField">
            后台导出令牌
            <input
              type="password"
              value={adminToken}
              onChange={(event) => setAdminToken(event.target.value)}
              placeholder="请输入 X-Admin-Token"
            />
          </label>

          <div className="dashboardActions exportActions">
            <button className="secondaryButton" type="button" onClick={previewExport} disabled={state.status === "loading"}>
              预览 CSV
            </button>
            <button className="primaryButton" type="button" onClick={saveExport} disabled={state.status === "loading"}>
              保存 CSV
            </button>
          </div>
        </section>

        <section className="detailPanel" aria-label="导出详情">
          <div className="sectionTitleRow">
            <h2>导出详情</h2>
            <span className="countBadge">{exportType}</span>
          </div>

          <div className="detailContent">
            <DetailRow label="当前类型" value={EXPORT_TYPE_LABELS[exportType]} />
            <DetailRow label="用途说明" value={selectedNote} />
            <DetailRow label="导出接口" value="GET /api/admin/export" />
            <DetailRow label="请求头" value="X-Admin-Token" />
            <DetailRow label="请求地址" value={exportUrl} />

            <section className="guidanceBox" aria-label="数据保护提示">
              <h3>数据保护提示</h3>
              <p>
                导出文件可能包含试点记录、联系方式或复盘文本。对外讨论、汇报或归档前，请先确认是否需要去除可识别个人身份的信息。
              </p>
            </section>

            <section className="guidanceBox" aria-label="CSV 预览">
              <h3>CSV 预览</h3>
              {state.previewText ? <pre className="csvPreview">{state.previewText}</pre> : <p>点击“预览 CSV”后，这里会显示前几行内容。</p>}
            </section>
          </div>
        </section>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="metricCard">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DetailRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{value ?? "未填写"}</span>
    </div>
  );
}

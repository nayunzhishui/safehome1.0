import { useMemo, useState } from "react";

import scalesCatalog from "../../../../content/scales_catalog.json";

interface ScaleCatalogItem {
  id: string;
  display_name: string;
  audience: string;
  theme: string;
  source_folder: string;
  source_files: string[];
  source_type: string;
  review_status: string;
  enabled: boolean;
  first_batch_candidate?: boolean;
  excluded_from_user_flow?: boolean;
  item_status?: string;
  scoring_status?: string;
  not_open_reason?: string;
  exclusion_reason?: string;
  recommended_card_ids?: string[];
  notes?: string;
}

const scales = scalesCatalog.scales as ScaleCatalogItem[];

function statusText(value?: string) {
  const labels: Record<string, string> = {
    metadata_only: "仅元数据",
    draft: "草稿",
    pending_review: "待审核",
    reviewed: "已审核",
    trial_enabled: "试用开放",
    enabled: "正式开放",
    disabled: "已停用",
    pending_extraction: "待抽取",
    draft_extracted: "草稿已抽取",
    source_insufficient: "来源不足",
    missing_items: "缺少题项",
    pending_review_scoring: "计分待审核",
    draft_from_syntax_pending_review: "计分草稿待审核",
    draft_from_pdf_and_sps_pending_review: "PDF/SPS 草稿待审核",
  };
  return labels[value || ""] || value || "未标记";
}

function audienceText(value: string) {
  const labels: Record<string, string> = {
    parent: "家长",
    adult: "成人",
    family: "家庭",
    student: "学生",
  };
  return labels[value] || value;
}

export function ScalesReview() {
  const [selectedId, setSelectedId] = useState<string | undefined>(scales[0]?.id);

  const selectedScale = useMemo(() => {
    return scales.find((scale) => scale.id === selectedId) ?? scales[0];
  }, [selectedId]);

  const enabledScales = scales.filter((scale) => scale.enabled);
  const firstBatch = scales.filter((scale) => scale.first_batch_candidate);
  const extracted = scales.filter((scale) => scale.item_status === "draft_extracted");
  const excluded = scales.filter((scale) => scale.excluded_from_user_flow);
  const blocked = scales.filter((scale) => !scale.enabled);

  return (
    <section className="dashboardShell" aria-label="量表目录审核">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Review</p>
          <h1>量表目录审核</h1>
          <p className="summary">
            只读查看本地量表目录，用于确认来源、题项、计分和开放边界。未完成人工复核前，真实量表不得面向用户开放。
          </p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/content/review">
            内容总览
          </a>
          <a className="secondaryButton" href="/content/worksheets">
            测评题库
          </a>
          <a className="secondaryButton" href="/content/rules">
            规则
          </a>
        </div>
      </div>

      <div className="status success">
        已读取 {scalesCatalog.version}。当前页面只读展示量表目录；小程序实际可见入口以“测评题库管理”和 assessment_worksheets 为准。
      </div>

      <div className="metricGrid" aria-label="量表目录概况">
        <MetricCard label="量表总数" value={scales.length} />
        <MetricCard label="第一批候选" value={firstBatch.length} />
        <MetricCard label="题项草稿" value={extracted.length} />
        <MetricCard label="已剔除" value={excluded.length} />
        <MetricCard label="用户端开放" value={enabledScales.length} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="量表列表">
          <div className="sectionTitleRow">
            <h2>量表目录</h2>
            <span className="countBadge">{blocked.length} 项暂不开放</span>
          </div>

          <div className="recordList">
            {scales.map((scale) => (
              <button
                className={`recordItem ${selectedScale?.id === scale.id ? "active" : ""}`}
                key={scale.id}
                type="button"
                onClick={() => setSelectedId(scale.id)}
              >
                <span className="recordScene">{scale.display_name}</span>
                <span className="recordDescription">{scale.notes || scale.not_open_reason || "待补充说明"}</span>
                <span className="recordMeta">
                  {audienceText(scale.audience)} · {statusText(scale.review_status)} · {scale.enabled ? "已开放" : "暂不开放"}
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="detailPanel" aria-label="量表详情">
          <div className="sectionTitleRow">
            <h2>审核状态详情</h2>
            {selectedScale && <span className="countBadge">ID {selectedScale.id}</span>}
          </div>

          {selectedScale ? (
            <div className="detailContent">
              <DetailRow label="量表名称" value={selectedScale.display_name} />
              <DetailRow label="人群" value={audienceText(selectedScale.audience)} />
              <DetailRow label="主题" value={selectedScale.theme} />
              <DetailRow label="来源类型" value={selectedScale.source_type} />
              <DetailRow label="审核状态" value={statusText(selectedScale.review_status)} />
              <DetailRow label="用户端开放" value={selectedScale.enabled ? "已开放" : "暂不开放"} />
              <DetailRow label="题项状态" value={statusText(selectedScale.item_status)} />
              <DetailRow label="计分状态" value={statusText(selectedScale.scoring_status)} />
              <DetailRow label="第一批候选" value={selectedScale.first_batch_candidate ? "是" : "否"} />
              <DetailRow label="剔除用户端流程" value={selectedScale.excluded_from_user_flow ? "是" : "否"} />
              <DetailRow label="推荐训练卡" value={(selectedScale.recommended_card_ids || []).join("、") || "暂无"} />
              <DetailRow label="不能开放原因" value={selectedScale.not_open_reason || "未完成人工复核前默认不开放。"} />
              <DetailRow label="剔除原因" value={selectedScale.exclusion_reason || "未标记为剔除。"} />
              <DetailRow label="来源文件" value={(selectedScale.source_files || []).join("\n")} />
              <DetailRow label="备注" value={selectedScale.notes} />

              <section className="guidanceBox" aria-label="量表开放边界">
                <h3>量表开放边界</h3>
                <p>{scalesCatalog.boundary_notice}</p>
                <p>正式开放前必须人工核对来源授权、题项、计分、结果解释、非诊断边界和高风险处理说明。</p>
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧量表后，这里会显示审核状态。</div>
          )}
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

function DetailRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{value || "未填写"}</span>
    </div>
  );
}

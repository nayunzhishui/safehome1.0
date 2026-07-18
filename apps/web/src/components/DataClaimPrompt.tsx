import type { DataClaimPreview } from "../../../../shared/types/api";

interface DataClaimPromptProps {
  preview: DataClaimPreview;
  status: "idle" | "loading" | "error";
  message: string;
  onConfirm: () => void;
  onSkip: () => void;
}

export function DataClaimPrompt({ preview, status, message, onConfirm, onSkip }: DataClaimPromptProps) {
  return (
    <section className="dataClaimPanel" aria-labelledby="data-claim-title">
      <span className="dataClaimMarker">找到本机记录</span>
      <h2 id="data-claim-title">把试用记录放进当前账号</h2>
      <p>共 {preview.total_records} 条。确认后会归到当前账号；暂不处理也不会删除。</p>
      <div className="dataClaimModules">
        {preview.modules.map((item) => <span key={item.module}>{item.label} {item.count}</span>)}
      </div>
      <p className="muted">{preview.boundary_notice}</p>
      {message ? <div className={`status compact ${status}`} role={status === "error" ? "alert" : "status"} aria-live="polite">{message}</div> : null}
      <div className="dashboardActions">
        <button className="primaryButton" type="button" onClick={onConfirm} disabled={status === "loading"}>确认合并</button>
        <button className="secondaryButton" type="button" onClick={onSkip} disabled={status === "loading"}>暂不处理</button>
      </div>
    </section>
  );
}

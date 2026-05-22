interface DeferredAdminPageProps {
  path: string;
}

export function DeferredAdminPage({ path }: DeferredAdminPageProps) {
  return (
    <section className="dashboardShell" aria-label="后台暂缓页面">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Deferred Page</p>
          <h1>后台页面暂缓</h1>
          <p className="summary">当前路径还没有独立页面。为避免误解，系统不会把它自动落到其他后台页面。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <a className="primaryButton" href="/diaries">
            查看情绪记录
          </a>
        </div>
      </div>

      <div className="status">当前路径：{path}</div>

      <section className="guidanceBox" aria-label="暂缓说明">
        <h2>暂缓说明</h2>
        <p>如需启用该页面，请先规划复用哪些现有 API，并确认不会影响小程序核心链路。</p>
      </section>

      <section className="guidanceBox" aria-label="边界提示">
        <h2>边界提示</h2>
        <p>暂缓页面不做数据写入、不新增后端 API，也不展示诊断性标签。小程序端核心流程不受影响。</p>
      </section>
    </section>
  );
}

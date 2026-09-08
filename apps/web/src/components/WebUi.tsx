import { Children, cloneElement, isValidElement, type HTMLAttributes, type ReactNode } from "react";
export function UiIcon({ name = "document", size = 20 }: { name?: string; size?: number }) {
  const paths: Record<string, string> = {
    overview: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
    document: "M7 3h8l4 4v14H5V3h2M14 3v5h5M8 12h8M8 16h6",
    people: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 4a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.87M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
    message: "M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9H13a8.5 8.5 0 0 1 8 8v.5ZM8 10h8M8 14h5",
    book: "M12 5v16M12 5C9 3 5 3 2 4v15c4-1 7 0 10 2 3-2 6-3 10-2V4c-3-1-7-1-10 1",
    chart: "M4 3v17h17M8 15v-4M13 15V7M18 15V5",
    shield: "M12 3 3 7v5c0 5 9 9 9 9s9-4 9-9V7l-9-4ZM8 12l3 3 5-6",
    settings: "M4 6h16M4 12h16M4 18h16M8 3v6M16 9v6M10 15v6",
    download: "M12 3v12M7 10l5 5 5-5M5 16v5h14v-5",
    target: "M21 12a9 9 0 1 1-9-9M17 12a5 5 0 1 1-5-5M12 12 21 3M16 3h5v5",
    check: "m5 12 4 4L19 6",
    arrow: "M4 12h16m-6-6 6 6-6 6",
    external: "M7 17 17 7M7 7h10v10",
    clock: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M12 7v5l3 2",
    home: "m3 10 9-7 9 7v11H3V10ZM9 21v-8h6v8",
    menu: "M4 6h16M4 12h16M4 18h16",
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name] || paths.document} /></svg>;
}

export function navigationIcon(path: string) {
  if (path === "/dashboard") return "overview";
  if (path.includes("privacy") || path.includes("security") || path === "/reviews") return "shield";
  if (path.includes("research") || path === "/reports" || path.includes("reliability")) return "chart";
  if (path.includes("content")) return "book";
  if (path.includes("supervision") || path.includes("feedback") || path.includes("sandbox")) return "message";
  if (path === "/goals") return "target";
  if (path.includes("profiles") || path.includes("family")) return "people";
  if (path.includes("system") || path.includes("integration")) return "settings";
  if (path === "/export") return "download";
  if (path === "/checkins") return "check";
  return "document";
}

export function SiteBrand({ href = "/", compact = false }: { href?: string; compact?: boolean }) {
  return <a className={`siteBrand${compact ? " siteBrand--compact" : ""}`} href={href} aria-label={href === "/dashboard" ? "安心陪伴工作台" : "安心陪伴首页"}>
    <svg width="30" height="36" viewBox="0 0 34 40" aria-hidden="true" focusable="false"><path d="M9 4v10m0 6v15M23 10v10m0 6v9M5 16h8M19 22h8" stroke="currentColor" fill="none" strokeWidth="3.5" strokeLinecap="round" /><path d="M12 9c8-8 13-6 16-7-2 6-6 10-16 7Z" fill="currentColor" /></svg>
    <strong>安心陪伴</strong>
  </a>;
}

export function SiteHeader({ home = false }: { home?: boolean }) {
  const links = home
    ? [["#home", "首页"], ["#flow", "核心流程"], ["/student", "学生画像"], ["/assessment", "家长测评"], ["#usage", "使用说明"], ["#privacy", "隐私边界"]]
    : [["/", "首页"], ["/student", "学生画像"], ["/assessment", "家长测评"], ["/about-study", "研究说明"], ["/privacy", "隐私中心"]];
  return <header className="siteHeader"><div className="siteHeaderInner">
    <SiteBrand />
    <nav className="siteDesktopNav" aria-label="网站导航">{links.map(([href, label]) => <a href={href} key={href}>{label}</a>)}</nav>
    <a className="siteResearchLink" href="/dashboard">研究者平台 <UiIcon name="external" size={16} /></a>
    <details className="siteMobileNav"
      onKeyDown={(event) => {
        if (event.key === "Escape" && event.currentTarget.open) {
          event.preventDefault();
          event.currentTarget.open = false;
          event.currentTarget.querySelector("summary")?.focus();
        }
      }}
      onClick={(event) => {
        if (event.target instanceof Element && event.target.closest("a")) {
          event.currentTarget.open = false;
          event.currentTarget.querySelector("summary")?.focus();
        }
      }}><summary aria-label="展开网站导航"><UiIcon name="menu" /></summary><nav aria-label="移动网站导航">{links.map(([href, label]) => <a href={href} key={href}>{label}</a>)}<a href="/dashboard">研究者平台</a></nav></details>
  </div></header>;
}

export function SiteFooter() {
  return <footer className="siteFooter"><div><SiteBrand compact /><p>家长情绪管理与亲子陪伴支持系统</p></div><nav aria-label="页脚导航"><a href="/">网站首页</a><a href="/privacy">隐私中心</a><a href="/dashboard">研究者平台 <UiIcon name="external" size={16} /></a></nav></footer>;
}

export function AuthIntro({ registering = false }: { registering?: boolean }) {
  return <aside className="authIntro"><span className="authIntroMark" aria-hidden="true"><UiIcon name="book" size={32} /></span><h2>{registering ? <>给陪伴，<br />留一个开始的位置。</> : <>允许自己有情绪。<br />陪伴，从这里继续。</>}</h2><p>记录具体的小事，<br />理解当时的感受，<br />再试一个不同的回应。</p><span className="authIntroBoundary">支持性练习，不作心理诊断。</span></aside>;
}


/** Display-only page anatomy. Existing headings, messages and action handlers are retained. */
export function PageHeader({ children, className = "", ...attributes }: HTMLAttributes<HTMLElement>) {
  const identity: ReactNode[] = [];
  const context: ReactNode[] = [];
  const actions: ReactNode[] = [];
  const nodes = Children.toArray(children);
  for (const child of nodes) {
    if (!isValidElement<{ children?: ReactNode; className?: string }>(child)) {
      context.push(child);
      continue;
    }
    const nested = Children.toArray(child.props.children);
    if (child.type === "div" && nested.some(node => isValidElement(node) && node.type === "h1")) {
      const titleParts = nested.filter(node => isValidElement<{ className?: string }>(node) && (node.type === "h1" || /eyebrow/i.test(node.props.className || "")));
      identity.push(cloneElement(child, undefined, titleParts));
      context.push(...nested.filter(node => !titleParts.includes(node)));
    } else if (child.type === "p" || child.type === "span") {
      context.push(child);
    } else {
      actions.push(child);
    }
  }
  return <header {...attributes} className={`${className} webPageHeader`}>
    <div className="webPageIdentity">{identity}</div>
    {context.length ? <div className="webPageContext">{context}</div> : null}
    {actions.length ? <div className="webPageActions">{actions}</div> : null}
  </header>;
}

export function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return <section className="detailSection" aria-label={title}><h3>{title}</h3><div className="detailSectionRows">{children}</div></section>;
}

export function SectionNavigation({ items }: { items: ReadonlyArray<{ id: string; label: string }> }) {
  return <nav className="sectionNavigation" aria-label="本页分区导航">{items.map(item => <a key={item.id} href={`#${item.id}`}>{item.label}</a>)}</nav>;
}

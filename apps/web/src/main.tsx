import React from "react";
import { createRoot } from "react-dom/client";

import { AdminDashboard } from "./pages/AdminDashboard";
import { CardsManagement } from "./pages/CardsManagement";
import { CheckinsManagement } from "./pages/CheckinsManagement";
import { DeferredAdminPage } from "./pages/DeferredAdminPage";
import { ExportManagement } from "./pages/ExportManagement";
import { FeedbackManagement } from "./pages/FeedbackManagement";
import { GoalsManagement } from "./pages/GoalsManagement";
import { IntegrationSmokeTest } from "./pages/IntegrationSmokeTest";
import { LandingPage } from "./pages/LandingPage";
import { ResearchDashboard } from "./pages/ResearchDashboard";
import { ReportsManagement } from "./pages/ReportsManagement";
import { RulesManagement } from "./pages/RulesManagement";
import { SupervisionManagement } from "./pages/SupervisionManagement";
import "./styles.css";

const adminLinks = [
  { href: "/dashboard", label: "总览仪表盘", match: (path: string) => path === "/dashboard" },
  { href: "/diaries", label: "用户与记录", match: (path: string) => path === "/diaries" || path.startsWith("/diaries/") },
  { href: "/feedback", label: "AI反馈审核", match: (path: string) => path === "/feedback" || path.startsWith("/feedback/") },
  { href: "/content/cards", label: "训练卡管理", match: (path: string) => path === "/content/cards" },
  { href: "/supervision", label: "督导工作台", match: (path: string) => path === "/supervision" || path.startsWith("/supervision/") },
  { href: "/checkins", label: "练习打卡", match: (path: string) => path === "/checkins" },
  { href: "/reports", label: "周度报告", match: (path: string) => path === "/reports" },
  { href: "/goals", label: "目标管理", match: (path: string) => path === "/goals" },
  { href: "/content/rules", label: "反馈规则", match: (path: string) => path === "/content/rules" },
  { href: "/export", label: "数据导出", match: (path: string) => path === "/export" },
  { href: "/integration-test", label: "联调测试", match: (path: string) => path === "/integration-test" },
];

function App() {
  const path = window.location.pathname;
  const isLandingPath = path === "/";
  const isDashboardPath = path === "/dashboard";
  const isDiariesPath = path === "/diaries" || path.startsWith("/diaries/");
  const isCheckinsPath = path === "/checkins";
  const isSupervisionPath = path === "/supervision" || path.startsWith("/supervision/");
  const isCardsPath = path === "/content/cards";
  const isRulesPath = path === "/content/rules";
  const isExportPath = path === "/export";
  const isReportsPath = path === "/reports";
  const isFeedbackPath = path === "/feedback";
  const isKnownAdminPath = [
    "/dashboard",
    "/goals",
    "/diaries",
    "/feedback",
    "/checkins",
    "/reports",
    "/supervision",
    "/content/cards",
    "/content/rules",
    "/export",
    "/integration-test",
  ].some((route) => path === route || path.startsWith(`${route}/`));
  const shouldRenderDeferredAdmin =
    isKnownAdminPath &&
    !isDashboardPath &&
    path !== "/goals" &&
    !isDiariesPath &&
    !isFeedbackPath &&
    !isCheckinsPath &&
    !isReportsPath &&
    !isSupervisionPath &&
    !isCardsPath &&
    !isRulesPath &&
    !isExportPath &&
    path !== "/integration-test";

  const pageContent = (
    <>
      {isLandingPath ? <LandingPage /> : null}
      {isDashboardPath ? <ResearchDashboard /> : null}
      {path === "/goals" ? <GoalsManagement /> : null}
      {isFeedbackPath ? <FeedbackManagement /> : null}
      {isCheckinsPath ? <CheckinsManagement /> : null}
      {isSupervisionPath ? <SupervisionManagement /> : null}
      {isCardsPath ? <CardsManagement /> : null}
      {isRulesPath ? <RulesManagement /> : null}
      {isExportPath ? <ExportManagement /> : null}
      {isReportsPath ? <ReportsManagement /> : null}
      {path === "/integration-test" ? <IntegrationSmokeTest /> : null}
      {isDiariesPath ? <AdminDashboard /> : null}
      {shouldRenderDeferredAdmin ? <DeferredAdminPage path={path} /> : null}
    </>
  );

  if (!isKnownAdminPath) {
    return <main className="page landingMode">{pageContent}</main>;
  }

  return (
    <main className="adminWorkspace">
      <aside className="adminSidebar" aria-label="后台导航">
        <a className="adminBrand" href="/dashboard" aria-label="安心陪伴管理后台">
          <span className="adminBrandMark" aria-hidden="true" />
          <span>
            <strong>安心陪伴</strong>
            <small>ReadFeedback Admin</small>
          </span>
        </a>
        <nav className="adminNav" aria-label="后台功能导航">
          {adminLinks.map((link) => (
            <a className={link.match(path) ? "active" : ""} href={link.href} key={link.href}>
              <span className="navDot" aria-hidden="true" />
              {link.label}
            </a>
          ))}
          <a href="/">
            <span className="navDot" aria-hidden="true" />
            网站首页
          </a>
        </nav>
        <section className="adminPrinciple" aria-label="平台原则">
          <strong>非诊断支持原则</strong>
          <span>所有反馈都保持非评判、支持性表达</span>
        </section>
      </aside>
      <section className="adminMain">
        <header className="adminTopbar">
          <div className="adminChromeDots" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <span className="adminPath">safehome1.0 {path}</span>
          <strong>管理员后台</strong>
        </header>
        {pageContent}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

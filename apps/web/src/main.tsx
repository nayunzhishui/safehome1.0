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

  return (
    <main className="page">
      {isKnownAdminPath ? (
        <nav className="adminNav" aria-label="后台导航">
          <a className={isDashboardPath ? "active" : ""} href="/dashboard">
            总览
          </a>
          <a className={path === "/goals" ? "active" : ""} href="/goals">
            目标管理
          </a>
          <a className={isDiariesPath ? "active" : ""} href="/diaries">
            情绪记录
          </a>
          <a className={isFeedbackPath ? "active" : ""} href="/feedback">
            反馈结果
          </a>
          <a className={isCheckinsPath ? "active" : ""} href="/checkins">
            打卡记录
          </a>
          <a className={isReportsPath ? "active" : ""} href="/reports">
            周报记录
          </a>
          <a className={isSupervisionPath ? "active" : ""} href="/supervision">
            督导请求
          </a>
          <a className={isCardsPath ? "active" : ""} href="/content/cards">
            训练卡
          </a>
          <a className={isRulesPath ? "active" : ""} href="/content/rules">
            反馈规则
          </a>
          <a className={isExportPath ? "active" : ""} href="/export">
            数据导出
          </a>
          <a className={path === "/integration-test" ? "active" : ""} href="/integration-test">
            联调测试
          </a>
          <a href="/">
            网站首页
          </a>
        </nav>
      ) : null}

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
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

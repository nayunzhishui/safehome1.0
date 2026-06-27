import React from "react";
import { createRoot } from "react-dom/client";

import { AdminDashboard } from "./pages/AdminDashboard";
import { CardsManagement } from "./pages/CardsManagement";
import { CheckinsManagement } from "./pages/CheckinsManagement";
import { ContentReviewOverview } from "./pages/ContentReviewOverview";
import { DeferredAdminPage } from "./pages/DeferredAdminPage";
import { ExportManagement } from "./pages/ExportManagement";
import { FeedbackManagement } from "./pages/FeedbackManagement";
import { GoalsManagement } from "./pages/GoalsManagement";
import { IntegrationSmokeTest } from "./pages/IntegrationSmokeTest";
import { LandingPage } from "./pages/LandingPage";
import { ProfilesManagement } from "./pages/ProfilesManagement";
import {
  AboutStudyPage,
  ParentAssessmentPage,
  ParentReportPage,
  StudentAssessmentPage,
  StudentEntryPage,
  StudentReportPage,
} from "./pages/ReadFeedbackIntegrationPages";
import { FamilyBindPage } from "./pages/FamilyBindPage";
import { LoginPage } from "./pages/LoginPage";
import { PrivacyCenterPage } from "./pages/PrivacyCenterPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResearchDashboard } from "./pages/ResearchDashboard";
import { ReportsManagement } from "./pages/ReportsManagement";
import { ReviewManagement } from "./pages/ReviewManagement";
import { RulesManagement } from "./pages/RulesManagement";
import { ScalesReview } from "./pages/ScalesReview";
import { SupervisionManagement } from "./pages/SupervisionManagement";
import { getStoredAuthUser } from "./services/authState";
import "./styles.css";

interface AdminLink {
  href: string;
  label: string;
  match: (path: string) => boolean;
  roles?: string[];
}

const allAdminLinks: AdminLink[] = [
  { href: "/dashboard", label: "总览仪表盘", match: (p) => p === "/dashboard", roles: ["admin", "researcher", "supervisor"] },
  { href: "/diaries", label: "用户与记录", match: (p) => p === "/diaries" || p.startsWith("/diaries/"), roles: ["admin", "researcher"] },
  { href: "/feedback", label: "支持性反馈审核", match: (p) => p === "/feedback" || p.startsWith("/feedback/"), roles: ["admin", "researcher"] },
  { href: "/content/review", label: "内容审核总览", match: (p) => p === "/content/review", roles: ["admin", "researcher", "supervisor"] },
  { href: "/content/scales", label: "量表目录审核", match: (p) => p === "/content/scales", roles: ["admin", "researcher"] },
  { href: "/content/cards", label: "训练卡管理", match: (p) => p === "/content/cards", roles: ["admin", "researcher"] },
  { href: "/supervision", label: "督导工作台", match: (p) => p === "/supervision" || p.startsWith("/supervision/"), roles: ["admin", "supervisor"] },
  { href: "/checkins", label: "练习记录", match: (p) => p === "/checkins", roles: ["admin", "researcher"] },
  { href: "/reports", label: "周度报告", match: (p) => p === "/reports", roles: ["admin", "researcher"] },
  { href: "/profiles", label: "学生画像", match: (p) => p === "/profiles" || p.startsWith("/profiles/"), roles: ["admin", "researcher", "supervisor"] },
  { href: "/reviews", label: "人工复核", match: (p) => p === "/reviews", roles: ["admin", "supervisor"] },
  { href: "/goals", label: "目标管理", match: (p) => p === "/goals", roles: ["admin", "researcher"] },
  { href: "/content/rules", label: "反馈规则", match: (p) => p === "/content/rules", roles: ["admin", "researcher"] },
  { href: "/export", label: "数据导出", match: (p) => p === "/export", roles: ["admin", "researcher"] },
  { href: "/integration-test", label: "联调测试", match: (p) => p === "/integration-test", roles: ["admin"] },
  { href: "/privacy", label: "隐私中心", match: (p) => p === "/privacy" },
  { href: "/family", label: "家庭绑定", match: (p) => p === "/family" || p.startsWith("/family/"), roles: ["parent", "student"] },
];

const publicLinks: AdminLink[] = [
  { href: "/privacy", label: "隐私中心", match: (p) => p === "/privacy" },
  { href: "/login", label: "登录", match: (p) => p === "/login" },
  { href: "/register", label: "注册", match: (p) => p === "/register" },
];

function visibleLinks(): AdminLink[] {
  const user = getStoredAuthUser();
  if (!user || !user.role) return publicLinks;
  return allAdminLinks.filter((link) => !link.roles || link.roles.includes(user.role));
}

function findAdminLink(path: string): AdminLink | undefined {
  return allAdminLinks.find((link) => link.match(path));
}

function canAccessPath(link?: AdminLink): boolean {
  if (!link || !link.roles) return true;
  const user = getStoredAuthUser();
  return Boolean(user?.role && link.roles.includes(user.role));
}

function AccessDeniedPage({ path, allowedRoles }: { path: string; allowedRoles: string[] }) {
  return (
    <section className="dashboardShell" aria-label="权限不足">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Access Control</p>
          <h1>当前账号不能访问此页面</h1>
          <p className="summary">内容审核后台只向对应后台角色开放。家长和学生账号不可访问内容审核、规则审核或量表审核页面。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <a className="primaryButton" href="/login">
            切换账号
          </a>
        </div>
      </div>

      <div className="status error">当前路径：{path}</div>

      <section className="guidanceBox" aria-label="权限说明">
        <h2>权限说明</h2>
        <p>允许角色：{allowedRoles.join("、")}</p>
        <p>researcher 只能只读查看审核状态；admin 可进行本地受控修改，开启用户端开放状态仍需人工单独确认。</p>
      </section>
    </section>
  );
}

function App() {
  const path = window.location.pathname;
  const isLandingPath = path === "/";
  const isAboutStudyPath = path === "/about-study";
  const isParentAssessmentPath = path === "/assessment";
  const isParentReportPath = path.startsWith("/assessment/report/");
  const isStudentEntryPath = path === "/student";
  const isStudentAssessmentPath = path === "/student/assessment";
  const isStudentReportPath = path.startsWith("/student/report/");
  const isDashboardPath = path === "/dashboard";
  const isDiariesPath = path === "/diaries" || path.startsWith("/diaries/");
  const isCheckinsPath = path === "/checkins";
  const isSupervisionPath = path === "/supervision" || path.startsWith("/supervision/");
  const isContentReviewPath = path === "/content/review";
  const isScalesPath = path === "/content/scales";
  const isCardsPath = path === "/content/cards";
  const isRulesPath = path === "/content/rules";
  const isExportPath = path === "/export";
  const isReportsPath = path === "/reports";
  const isProfilesPath = path === "/profiles" || path.startsWith("/profiles/");
  const isReviewsPath = path === "/reviews";
  const isFeedbackPath = path === "/feedback";
  const isFamilyPath = path === "/family" || path.startsWith("/family/");
  const isKnownAdminPath = [
    "/dashboard",
    "/goals",
    "/diaries",
    "/feedback",
    "/checkins",
    "/reports",
    "/profiles",
    "/reviews",
    "/supervision",
    "/content/review",
    "/content/scales",
    "/content/cards",
    "/content/rules",
    "/export",
    "/integration-test",
    "/family",
  ].some((route) => path === route || path.startsWith(`${route}/`));
  const matchedAdminLink = findAdminLink(path);
  const shouldBlockAdminPath = isKnownAdminPath && matchedAdminLink && !canAccessPath(matchedAdminLink);
  const shouldRenderDeferredAdmin =
    isKnownAdminPath &&
    !isDashboardPath &&
    path !== "/goals" &&
    !isDiariesPath &&
    !isFeedbackPath &&
    !isCheckinsPath &&
    !isReportsPath &&
    !isProfilesPath &&
    !isReviewsPath &&
    !isSupervisionPath &&
    !isContentReviewPath &&
    !isScalesPath &&
    !isCardsPath &&
    !isRulesPath &&
    !isExportPath &&
    path !== "/integration-test";

  const pageContent = shouldBlockAdminPath ? (
    <AccessDeniedPage path={path} allowedRoles={matchedAdminLink.roles || []} />
  ) : (
    <>
      {isLandingPath ? <LandingPage /> : null}
      {isAboutStudyPath ? <AboutStudyPage /> : null}
      {path === "/login" ? <LoginPage /> : null}
      {path === "/register" ? <RegisterPage /> : null}
      {path === "/privacy" ? <PrivacyCenterPage /> : null}
      {isParentAssessmentPath ? <ParentAssessmentPage /> : null}
      {isParentReportPath ? <ParentReportPage /> : null}
      {isStudentEntryPath ? <StudentEntryPage /> : null}
      {isStudentAssessmentPath ? <StudentAssessmentPage /> : null}
      {isStudentReportPath ? <StudentReportPage /> : null}
      {isDashboardPath ? <ResearchDashboard /> : null}
      {path === "/goals" ? <GoalsManagement /> : null}
      {isFeedbackPath ? <FeedbackManagement /> : null}
      {isCheckinsPath ? <CheckinsManagement /> : null}
      {isSupervisionPath ? <SupervisionManagement /> : null}
      {isContentReviewPath ? <ContentReviewOverview /> : null}
      {isScalesPath ? <ScalesReview /> : null}
      {isCardsPath ? <CardsManagement /> : null}
      {isRulesPath ? <RulesManagement /> : null}
      {isExportPath ? <ExportManagement /> : null}
      {isReportsPath ? <ReportsManagement /> : null}
      {isProfilesPath ? <ProfilesManagement /> : null}
      {isReviewsPath ? <ReviewManagement /> : null}
      {isFamilyPath ? <FamilyBindPage /> : null}
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
          {visibleLinks().map((link) => (
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

import React, { lazy, Suspense, useState } from "react";
import { createRoot } from "react-dom/client";

import { clearAuthSession, getStoredAuthToken, saveAuthSession, type AuthUser } from "./services/authState";
import { safeHomeApi, SafeHomeApiError } from "./services/safehomeApi";
import "./styles.css";

const AdminDashboard = lazy(() => import("./pages/AdminDashboard").then((module) => ({ default: module.AdminDashboard })));
const CardsManagement = lazy(() => import("./pages/CardsManagement").then((module) => ({ default: module.CardsManagement })));
const CheckinsManagement = lazy(() => import("./pages/CheckinsManagement").then((module) => ({ default: module.CheckinsManagement })));
const ContentReviewOverview = lazy(() => import("./pages/ContentReviewOverview").then((module) => ({ default: module.ContentReviewOverview })));
const DeferredAdminPage = lazy(() => import("./pages/DeferredAdminPage").then((module) => ({ default: module.DeferredAdminPage })));
const ExportManagement = lazy(() => import("./pages/ExportManagement").then((module) => ({ default: module.ExportManagement })));
const FeedbackManagement = lazy(() => import("./pages/FeedbackManagement").then((module) => ({ default: module.FeedbackManagement })));
const GoalsManagement = lazy(() => import("./pages/GoalsManagement").then((module) => ({ default: module.GoalsManagement })));
const IntegrationSmokeTest = lazy(() => import("./pages/IntegrationSmokeTest").then((module) => ({ default: module.IntegrationSmokeTest })));
const LandingPage = lazy(() => import("./pages/LandingPage").then((module) => ({ default: module.LandingPage })));
const ProfilesManagement = lazy(() => import("./pages/ProfilesManagement").then((module) => ({ default: module.ProfilesManagement })));
const AboutStudyPage = lazy(() => import("./pages/ReadFeedbackIntegrationPages").then((module) => ({ default: module.AboutStudyPage })));
const ParentAssessmentPage = lazy(() => import("./pages/ReadFeedbackIntegrationPages").then((module) => ({ default: module.ParentAssessmentPage })));
const ParentReportPage = lazy(() => import("./pages/ReadFeedbackIntegrationPages").then((module) => ({ default: module.ParentReportPage })));
const StudentAssessmentPage = lazy(() => import("./pages/ReadFeedbackIntegrationPages").then((module) => ({ default: module.StudentAssessmentPage })));
const StudentEntryPage = lazy(() => import("./pages/ReadFeedbackIntegrationPages").then((module) => ({ default: module.StudentEntryPage })));
const StudentReportPage = lazy(() => import("./pages/ReadFeedbackIntegrationPages").then((module) => ({ default: module.StudentReportPage })));
const FamilyBindPage = lazy(() => import("./pages/FamilyBindPage").then((module) => ({ default: module.FamilyBindPage })));
const LoginPage = lazy(() => import("./pages/LoginPage").then((module) => ({ default: module.LoginPage })));
const PrivacyCenterPage = lazy(() => import("./pages/PrivacyCenterPage").then((module) => ({ default: module.PrivacyCenterPage })));
const PrivacyRequestsManagement = lazy(() => import("./pages/PrivacyRequestsManagement").then((module) => ({ default: module.PrivacyRequestsManagement })));
const RegisterPage = lazy(() => import("./pages/RegisterPage").then((module) => ({ default: module.RegisterPage })));
const ResearchDashboard = lazy(() => import("./pages/ResearchDashboard").then((module) => ({ default: module.ResearchDashboard })));
const RelationshipAssessmentPage = lazy(() => import("./pages/RelationshipAssessmentPage").then((module) => ({ default: module.RelationshipAssessmentPage })));
const ReportsManagement = lazy(() => import("./pages/ReportsManagement").then((module) => ({ default: module.ReportsManagement })));
const ReviewManagement = lazy(() => import("./pages/ReviewManagement").then((module) => ({ default: module.ReviewManagement })));
const RulesManagement = lazy(() => import("./pages/RulesManagement").then((module) => ({ default: module.RulesManagement })));
const ScalesReview = lazy(() => import("./pages/ScalesReview").then((module) => ({ default: module.ScalesReview })));
const SupervisionManagement = lazy(() => import("./pages/SupervisionManagement").then((module) => ({ default: module.SupervisionManagement })));
const WorksheetsManagement = lazy(() => import("./pages/WorksheetsManagement").then((module) => ({ default: module.WorksheetsManagement })));
const AiQaSandboxPage = lazy(() => import("./pages/AiQaSandboxPage").then((module) => ({ default: module.AiQaSandboxPage })));
const OfflineBenchmarkWorkbench = lazy(() => import("./pages/OfflineBenchmarkWorkbench").then((module) => ({ default: module.OfflineBenchmarkWorkbench })));
const ResearchMethodologyWorkbench = lazy(() => import("./pages/ResearchMethodologyWorkbench").then((module) => ({ default: module.ResearchMethodologyWorkbench })));
const SecurityPrivacyWorkbench = lazy(() => import("./pages/SecurityPrivacyWorkbench").then((module) => ({ default: module.SecurityPrivacyWorkbench })));
const ReliabilityReleaseWorkbench = lazy(() => import("./pages/ReliabilityReleaseWorkbench").then((module) => ({ default: module.ReliabilityReleaseWorkbench })));
const ExperienceGovernanceWorkbench = lazy(() => import("./pages/ExperienceGovernanceWorkbench").then((module) => ({ default: module.ExperienceGovernanceWorkbench })));

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
  { href: "/content/worksheets", label: "测评题库管理", match: (p) => p === "/content/worksheets", roles: ["admin"] },
  { href: "/content/cards", label: "训练卡管理", match: (p) => p === "/content/cards", roles: ["admin", "researcher"] },
  { href: "/supervision", label: "督导工作台", match: (p) => p === "/supervision" || p.startsWith("/supervision/"), roles: ["admin", "supervisor"] },
  { href: "/checkins", label: "练习记录", match: (p) => p === "/checkins", roles: ["admin", "researcher"] },
  { href: "/reports", label: "周度报告", match: (p) => p === "/reports", roles: ["admin", "researcher"] },
  { href: "/profiles", label: "学生画像", match: (p) => p === "/profiles" || p.startsWith("/profiles/"), roles: ["admin", "researcher", "supervisor"] },
  { href: "/reviews", label: "人工复核", match: (p) => p === "/reviews", roles: ["admin", "supervisor"] },
  { href: "/privacy-requests", label: "隐私申请", match: (p) => p === "/privacy-requests", roles: ["admin", "supervisor"] },
  { href: "/goals", label: "目标管理", match: (p) => p === "/goals", roles: ["admin", "researcher"] },
  { href: "/content/rules", label: "反馈规则", match: (p) => p === "/content/rules", roles: ["admin", "researcher"] },
  { href: "/ai-sandbox", label: "AI 合成沙盒", match: (p) => p === "/ai-sandbox", roles: ["admin", "researcher", "supervisor"] },
  { href: "/research/benchmarks", label: "离线算法基准", match: (p) => p === "/research/benchmarks", roles: ["admin", "researcher", "supervisor"] },
  { href: "/research/methodology", label: "研究方法冻结准备", match: (p) => p === "/research/methodology", roles: ["admin", "researcher", "supervisor"] },
  { href: "/security/privacy", label: "安全与隐私防护", match: (p) => p === "/security/privacy", roles: ["admin", "researcher", "supervisor"] },
  { href: "/reliability/release", label: "可靠性与发布证据", match: (p) => p === "/reliability/release", roles: ["admin", "researcher", "supervisor"] },
  { href: "/system/experience", label: "体验与无障碍", match: (p) => p === "/system/experience", roles: ["admin", "researcher", "supervisor"] },
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

const researcherWorkspaces = [
  { label: "待处理", paths: ["/dashboard", "/feedback", "/supervision", "/reviews", "/privacy-requests"] },
  { label: "参与者", paths: ["/diaries", "/goals", "/checkins", "/reports", "/profiles", "/family", "/privacy"] },
  { label: "内容", paths: ["/content/review", "/content/scales", "/content/worksheets", "/content/cards", "/content/rules"] },
  { label: "研究/导出", paths: ["/ai-sandbox", "/research/benchmarks", "/research/methodology", "/export"] },
  { label: "系统状态", paths: ["/security/privacy", "/reliability/release", "/system/experience", "/integration-test"] },
];

function groupedVisibleLinks(user: AuthUser | null, showcaseEnabled = false) {
  const links = visibleLinks(user, showcaseEnabled);
  return researcherWorkspaces.map((workspace) => ({ ...workspace, links: links.filter((link) => workspace.paths.includes(link.href)) })).filter((workspace) => workspace.links.length);
}

function visibleLinks(user: AuthUser | null, showcaseEnabled = false): AdminLink[] {
  if (!user || !user.role) return publicLinks;
  if (showcaseEnabled) return allAdminLinks;
  return allAdminLinks.filter((link) => !link.roles || link.roles.includes(user.role));
}

function findAdminLink(path: string): AdminLink | undefined {
  return allAdminLinks.find((link) => link.match(path));
}

function canAccessPath(link: AdminLink | undefined, user: AuthUser | null, showcaseEnabled = false): boolean {
  if (!link || !link.roles) return true;
  if (showcaseEnabled && user) return true;
  return Boolean(user?.role && link.roles.includes(user.role));
}

function AccessDeniedPage({ path, allowedRoles }: { path: string; allowedRoles: string[] }) {
  return (
    <section className="dashboardShell" aria-label="权限不足">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">访问权限</p>
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

      <div className="status error" role="alert">此页面未向当前账号开放。</div>

      <section className="guidanceBox" aria-label="权限说明">
        <h2>权限说明</h2>
        <p>允许角色：{allowedRoles.join("、")}</p>
        <p>researcher 只能只读查看审核状态；admin 可进行本地受控修改，开启用户端开放状态仍需人工单独确认。</p>
      </section>
    </section>
  );
}

function RouteFallback() {
  return (
    <section className="dashboardShell" aria-live="polite" aria-label="页面加载中">
      <div className="status">正在加载页面...</div>
    </section>
  );
}

function App({ authUser, showcaseEnabled }: { authUser: AuthUser | null; showcaseEnabled: boolean }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const path = window.location.pathname;
  const isLandingPath = path === "/";
  const isAboutStudyPath = path === "/about-study";
  const isParentAssessmentPath = path === "/assessment";
  const isParentReportPath = path.startsWith("/assessment/report/");
  const isStudentEntryPath = path === "/student";
  const isStudentAssessmentPath = path === "/student/assessment";
  const isStudentReportPath = path.startsWith("/student/report/");
  const isRelationshipAssessmentPath = path === "/relationship-assessment";
  const isDashboardPath = path === "/dashboard";
  const isDiariesPath = path === "/diaries" || path.startsWith("/diaries/");
  const isCheckinsPath = path === "/checkins";
  const isSupervisionPath = path === "/supervision" || path.startsWith("/supervision/");
  const isContentReviewPath = path === "/content/review";
  const isScalesPath = path === "/content/scales";
  const isWorksheetsPath = path === "/content/worksheets";
  const isCardsPath = path === "/content/cards";
  const isRulesPath = path === "/content/rules";
  const isExportPath = path === "/export";
  const isReportsPath = path === "/reports";
  const isProfilesPath = path === "/profiles" || path.startsWith("/profiles/");
  const isReviewsPath = path === "/reviews";
  const isFeedbackPath = path === "/feedback";
  const isPrivacyRequestsPath = path === "/privacy-requests";
  const isFamilyPath = path === "/family" || path.startsWith("/family/");
  const isAiQaSandboxPath = path === "/ai-sandbox";
  const isOfflineBenchmarkPath = path === "/research/benchmarks";
  const isResearchMethodologyPath = path === "/research/methodology";
  const isSecurityPrivacyPath = path === "/security/privacy";
  const isReliabilityReleasePath = path === "/reliability/release";
  const isExperienceGovernancePath = path === "/system/experience";
  const isKnownAdminPath = [
    "/dashboard",
    "/goals",
    "/diaries",
    "/feedback",
    "/checkins",
    "/reports",
    "/profiles",
    "/reviews",
    "/privacy-requests",
    "/supervision",
    "/content/review",
    "/content/scales",
    "/content/worksheets",
    "/content/cards",
    "/content/rules",
    "/export",
    "/integration-test",
    "/family",
    "/ai-sandbox",
    "/research/benchmarks",
    "/research/methodology",
    "/security/privacy",
    "/reliability/release",
    "/system/experience",
  ].some((route) => path === route || path.startsWith(`${route}/`));
  const matchedAdminLink = findAdminLink(path);
  const shouldBlockAdminPath = isKnownAdminPath && matchedAdminLink && !canAccessPath(matchedAdminLink, authUser, showcaseEnabled);
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
    !isPrivacyRequestsPath &&
    !isFamilyPath &&
    !isAiQaSandboxPath &&
    !isOfflineBenchmarkPath &&
    !isResearchMethodologyPath &&
    !isSecurityPrivacyPath &&
    !isReliabilityReleasePath &&
    !isExperienceGovernancePath &&
    !isSupervisionPath &&
    !isContentReviewPath &&
    !isScalesPath &&
    !isWorksheetsPath &&
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
      {isRelationshipAssessmentPath ? <RelationshipAssessmentPage /> : null}
      {isDashboardPath ? <ResearchDashboard /> : null}
      {path === "/goals" ? <GoalsManagement /> : null}
      {isFeedbackPath ? <FeedbackManagement /> : null}
      {isCheckinsPath ? <CheckinsManagement /> : null}
      {isSupervisionPath ? <SupervisionManagement /> : null}
      {isContentReviewPath ? <ContentReviewOverview /> : null}
      {isScalesPath ? <ScalesReview /> : null}
      {isWorksheetsPath ? <WorksheetsManagement /> : null}
      {isCardsPath ? <CardsManagement /> : null}
      {isRulesPath ? <RulesManagement /> : null}
      {isExportPath ? <ExportManagement /> : null}
      {isReportsPath ? <ReportsManagement /> : null}
      {isProfilesPath ? <ProfilesManagement /> : null}
      {isReviewsPath ? <ReviewManagement /> : null}
      {isPrivacyRequestsPath ? <PrivacyRequestsManagement /> : null}
      {isFamilyPath ? <FamilyBindPage /> : null}
      {isAiQaSandboxPath ? <AiQaSandboxPage /> : null}
      {isOfflineBenchmarkPath ? <OfflineBenchmarkWorkbench /> : null}
      {isResearchMethodologyPath ? <ResearchMethodologyWorkbench /> : null}
      {isSecurityPrivacyPath ? <SecurityPrivacyWorkbench /> : null}
      {isReliabilityReleasePath ? <ReliabilityReleaseWorkbench /> : null}
      {isExperienceGovernancePath ? <ExperienceGovernanceWorkbench /> : null}
      {path === "/integration-test" ? <IntegrationSmokeTest /> : null}
      {isDiariesPath ? <AdminDashboard /> : null}
      {shouldRenderDeferredAdmin ? <DeferredAdminPage path={path} /> : null}
    </>
  );
  const suspendedPageContent = <Suspense fallback={<RouteFallback />}>{pageContent}</Suspense>;

  if (!isKnownAdminPath) {
    return (
      <>
        <a className="skipLink" href="#main-content">跳到主要内容</a>
        <main className="page landingMode" id="main-content">{suspendedPageContent}</main>
      </>
    );
  }

  return (
    <>
      <a className="skipLink" href="#main-content">跳到主要内容</a>
      <main className="adminWorkspace" id="main-content">
      <aside className="adminSidebar" aria-label="后台导航">
        <a className="adminBrand" href="/dashboard" aria-label="安心陪伴管理后台">
          <span className="adminBrandMark" aria-hidden="true" />
          <span>
            <strong>安心陪伴</strong>
            <small>ReadFeedback Admin</small>
          </span>
        </a>
        <button
          className="adminNavToggle"
          type="button"
          aria-expanded={mobileNavOpen}
          aria-controls="admin-function-nav"
          onClick={() => setMobileNavOpen((current) => !current)}
        >
          <span>{mobileNavOpen ? "收起导航" : "打开导航"}</span>
          <span aria-hidden="true">{mobileNavOpen ? "−" : "+"}</span>
        </button>
        <nav className={`adminNav ${mobileNavOpen ? "isOpen" : ""}`} id="admin-function-nav" aria-label="后台功能导航">
          {groupedVisibleLinks(authUser, showcaseEnabled).map((workspace) => (
            <section className="adminNavGroup" aria-label={workspace.label} key={workspace.label}>
              <strong className="adminNavGroupLabel">{workspace.label}</strong>
              {workspace.links.map((link) => (
                <a className={link.match(path) ? "active" : ""} href={link.href} key={link.href}>
                  <span className="navDot" aria-hidden="true" />
                  {link.label}
                </a>
              ))}
            </section>
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
        {suspendedPageContent}
      </section>
      </main>
    </>
  );
}

const root = createRoot(document.getElementById("root") as HTMLElement);

function renderApp(authUser: AuthUser | null, showcaseEnabled = false) {
  root.render(
    <React.StrictMode>
      <App authUser={authUser} showcaseEnabled={showcaseEnabled} />
    </React.StrictMode>,
  );
}

async function bootstrapAuth() {
  const showcase = await safeHomeApi.getShowcaseAccess().catch(() => ({ enabled: false }));
  const token = getStoredAuthToken();
  if (!token) {
    renderApp(null, showcase.enabled);
    return;
  }

  try {
    const user = await safeHomeApi.getCurrentUser();
    saveAuthSession(token, user);
    renderApp(user, showcase.enabled);
  } catch (error) {
    if (error instanceof SafeHomeApiError && error.status === 401) {
      clearAuthSession();
    }
    renderApp(null, showcase.enabled);
  }
}

void bootstrapAuth();

import { useEffect, useMemo, useState } from "react";

import { SafeHomeApiClient } from "../services/safehomeApi";
import type { Checkin, EmotionDiary, Goal, RiskReviewRecord, StudentProfileRecord, TrainingCard } from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface OverviewState {
  status: LoadStatus;
  message: string;
  goals: Goal[];
  diaries: EmotionDiary[];
  checkins: Checkin[];
  cards: TrainingCard[];
  riskReviews: RiskReviewRecord[];
  profiles: StudentProfileRecord[];
}

interface TodoItem {
  title: string;
  value: string | number;
  note: string;
  href?: string;
}

const api = new SafeHomeApiClient();

const COMPLETED_ADMIN_PAGES = [
  { path: "/dashboard", label: "总览", note: "研究者平台运行概况" },
  { path: "/goals", label: "目标管理", note: "查看小程序端目标设定" },
  { path: "/diaries", label: "情绪记录", note: "查看记录列表、详情、反馈和训练卡推荐" },
  { path: "/feedback", label: "反馈结果", note: "通过导出接口查看已生成反馈" },
  { path: "/checkins", label: "练习记录", note: "查看训练卡练习尝试" },
  { path: "/reports", label: "周报记录", note: "通过导出接口查看已生成周报" },
  { path: "/supervision", label: "督导请求", note: "通过导出接口查看人工督导请求" },
  { path: "/content/cards", label: "训练卡", note: "只读查看训练卡内容" },
  { path: "/content/rules", label: "反馈规则", note: "只读查看反馈规则边界和支持性反馈" },
  { path: "/export", label: "数据导出", note: "复用后台 CSV 导出接口" },
];

const DEFERRED_ADMIN_PAGES: Array<{ path: string; label: string; note: string }> = [];

function formatTime(value?: string | null) {
  if (!value) {
    return "未记录";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toDate(value?: string | null) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function dateKey(date: Date) {
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function isToday(value?: string | null) {
  const date = toDate(value);
  if (!date) {
    return false;
  }
  return dateKey(date) === dateKey(new Date());
}

function isThisWeek(value?: string | null) {
  const date = toDate(value);
  if (!date) {
    return false;
  }

  const today = new Date();
  const start = new Date(today);
  const day = today.getDay() === 0 ? 6 : today.getDay() - 1;
  start.setDate(today.getDate() - day);
  start.setHours(0, 0, 0, 0);

  const end = new Date(start);
  end.setDate(start.getDate() + 7);
  return date >= start && date < end;
}

function isOpenRiskReview(item: RiskReviewRecord) {
  return !["reviewed", "closed"].includes(item.review_status);
}

function isOpenProfileReview(item: StudentProfileRecord) {
  const latestStatus = item.latest_review?.review_status;
  return Boolean(item.requires_review) && !["reviewed", "closed"].includes(latestStatus || "");
}

export function ResearchDashboard() {
  const [state, setState] = useState<OverviewState>({
    status: "idle",
    message: "正在准备研究者平台总览。",
    goals: [],
    diaries: [],
    checkins: [],
    cards: [],
    riskReviews: [],
    profiles: [],
  });

  const latestDiary = state.diaries[0];
  const latestGoal = state.goals[0];
  const activeGoals = useMemo(() => state.goals.filter((goal) => goal.status === "active"), [state.goals]);
  const completedCheckins = useMemo(() => state.checkins.filter((checkin) => checkin.completed === 1), [state.checkins]);
  const todayDiaries = useMemo(() => state.diaries.filter((diary) => isToday(diary.created_at)), [state.diaries]);
  const todayHighRiskReviews = useMemo(
    () => state.riskReviews.filter((item) => item.risk_level === "high" && isToday(item.created_at)),
    [state.riskReviews],
  );
  const todayHighRiskProfiles = useMemo(
    () => state.profiles.filter((item) => item.risk_level === "high" && isToday(item.created_at)),
    [state.profiles],
  );
  const pendingRiskReviews = useMemo(() => state.riskReviews.filter(isOpenRiskReview), [state.riskReviews]);
  const pendingProfileReviews = useMemo(() => state.profiles.filter(isOpenProfileReview), [state.profiles]);
  const weeklyCheckins = useMemo(() => state.checkins.filter((checkin) => isThisWeek(checkin.created_at)), [state.checkins]);
  const todoItems: TodoItem[] = [
    {
      title: "今日新增记录",
      value: todayDiaries.length,
      note: todayDiaries.length > 0 ? "优先查看是否需要补充反馈或训练卡建议。" : "今天暂未读取到新的情绪记录。",
      href: "/diaries",
    },
    {
      title: "今日高风险",
      value: todayHighRiskReviews.length + todayHighRiskProfiles.length,
      note: "只显示数量，不展示高风险原文；请进入复核或画像页面查看处置状态。",
      href: "/reviews",
    },
    {
      title: "待人工复核",
      value: pendingRiskReviews.length + pendingProfileReviews.length,
      note: "包含风险复核队列和需复核画像。",
      href: "/reviews",
    },
    {
      title: "本周练习尝试",
      value: weeklyCheckins.length,
      note: "用于观察练习积累，不作为完成率或考核。",
      href: "/checkins",
    },
    {
      title: "最近导出记录",
      value: "待接入",
      note: "导出审计已写入 audit_logs，当前还没有前端列表接口。",
      href: "/export",
    },
    {
      title: "内容文件异常",
      value: "需运行脚本",
      note: "提交前运行 python backend\\scripts\\validate_content.py。",
    },
  ];

  async function loadOverview() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取目标、记录、练习、风险复核和训练卡数据...",
    }));

    try {
      const [goals, diaries, checkins, cards, riskReviews, profiles] = await Promise.all([
        api.listGoals(),
        api.listDiaries({ limit: 50 }),
        api.listCheckins({ limit: 50 }),
        api.listCards(),
        api.listRiskReviews({ limit: 50 }),
        api.listProfileResults({ limit: 50 }),
      ]);

      setState({
        status: "success",
        message: "已读取研究者平台总览数据。",
        goals: goals.items,
        diaries: diaries.items,
        checkins: checkins.items,
        cards: cards.items,
        riskReviews: riskReviews.items,
        profiles: profiles.items,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: error instanceof Error ? error.message : "读取失败，请确认 backend 是否已启动。",
      }));
    }
  }

  useEffect(() => {
    void loadOverview();
  }, []);

  return (
    <section className="dashboardShell" aria-label="研究者平台总览">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Research Platform</p>
          <h1>研究者平台总览</h1>
          <p className="summary">用于快速查看试点运行状态。这里不展示诊断性标签，也不替代正式研究数据审查。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/diaries">
            查看情绪记录
          </a>
          <button className="primaryButton" type="button" onClick={loadOverview} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新总览"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

      <section className="guidanceBox" aria-label="今日待处理">
        <div className="sectionTitleRow">
          <h2>今日待处理</h2>
          <span className="countBadge">P2-06</span>
        </div>
        <div className="recordList">
          {todoItems.map((item) =>
            item.href ? (
              <a className="recordItem textLink" href={item.href} key={item.title}>
                <span className="recordScene">{item.title}</span>
                <span className="recordDescription">{item.note}</span>
                <span className="recordMeta">{item.value}</span>
              </a>
            ) : (
              <div className="recordItem" key={item.title}>
                <span className="recordScene">{item.title}</span>
                <span className="recordDescription">{item.note}</span>
                <span className="recordMeta">{item.value}</span>
              </div>
            ),
          )}
        </div>
      </section>

      <div className="metricGrid" aria-label="总览指标">
        <MetricCard label="目标总数" value={state.goals.length} />
        <MetricCard label="进行中目标" value={activeGoals.length} />
        <MetricCard label="情绪记录" value={state.diaries.length} />
        <MetricCard label="已记录尝试" value={completedCheckins.length} />
      </div>

      <div className="metricGrid" aria-label="内容与练习指标">
        <MetricCard label="训练卡" value={state.cards.length} />
        <MetricCard label="尝试记录" value={state.checkins.length} />
        <MetricCard label="已关联目标记录" value={state.diaries.filter((diary) => diary.goal_id).length} />
        <MetricCard label="可用数据类型" value={4} />
      </div>

      <div className="dashboardGrid overviewGrid">
        <section className="listPanel" aria-label="最近情绪记录">
          <div className="sectionTitleRow">
            <h2>最近情绪记录</h2>
            <a className="textLink" href="/diaries">
              查看全部
            </a>
          </div>
          {latestDiary ? (
            <div className="overviewBlock">
              <span className="recordMeta">{formatTime(latestDiary.created_at)}</span>
              <h3>{latestDiary.scene}</h3>
              <p>{latestDiary.event_description}</p>
              <p className="muted">家长情绪：{latestDiary.parent_emotion} / 强度 {latestDiary.parent_emotion_intensity}</p>
            </div>
          ) : (
            <div className="emptyState">还没有情绪记录。</div>
          )}
        </section>

        <section className="detailPanel" aria-label="最近目标">
          <div className="sectionTitleRow">
            <h2>最近目标</h2>
            <a className="textLink" href="/goals">
              查看目标
            </a>
          </div>
          {latestGoal ? (
            <div className="overviewBlock">
              <span className="recordMeta">{formatTime(latestGoal.created_at)} · {latestGoal.status}</span>
              <h3>{latestGoal.scene}</h3>
              <p>{latestGoal.smart_goal}</p>
              <p className="muted">{latestGoal.motivation || "未填写练习动机"}</p>
            </div>
          ) : (
            <div className="emptyState">还没有目标。</div>
          )}
        </section>
      </div>

      <div className="dashboardGrid overviewGrid">
        <section className="listPanel" aria-label="已完成后台页面">
          <div className="sectionTitleRow">
            <h2>已完成页面</h2>
            <span className="countBadge">{COMPLETED_ADMIN_PAGES.length} 个</span>
          </div>
          <div className="recordList">
            {COMPLETED_ADMIN_PAGES.map((page) => (
              <a className="recordItem textLink" href={page.path} key={page.path}>
                <span className="recordScene">{page.label}</span>
                <span className="recordDescription">{page.note}</span>
                <span className="recordMeta">{page.path}</span>
              </a>
            ))}
          </div>
        </section>

        <section className="detailPanel" aria-label="暂缓后台页面">
          <div className="sectionTitleRow">
            <h2>暂缓页面</h2>
            <span className="countBadge">{DEFERRED_ADMIN_PAGES.length} 个</span>
          </div>
          {DEFERRED_ADMIN_PAGES.length > 0 ? (
            <div className="recordList">
              {DEFERRED_ADMIN_PAGES.map((page) => (
                <a className="recordItem textLink" href={page.path} key={page.path}>
                  <span className="recordScene">{page.label}</span>
                  <span className="recordDescription">{page.note}</span>
                  <span className="recordMeta">{page.path}</span>
                </a>
              ))}
            </div>
          ) : (
            <div className="emptyState">当前没有明确暂缓的后台页面。</div>
          )}
        </section>
      </div>

      <section className="guidanceBox" aria-label="研究者平台边界">
        <h2>平台边界</h2>
        <p>
          当前总览只用于本地试点管理和数据完整性检查。正式研究导出前仍需进行权限控制、匿名化和脱敏处理。
        </p>
      </section>
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

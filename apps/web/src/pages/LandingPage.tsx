const flowSteps = [
  {
    title: "目标设定",
    text: "先确定这一周想练习的一个亲子互动小目标。",
  },
  {
    title: "情绪事件记录",
    text: "记录一次具体事件，包括情绪、想法、身体感觉和回应。",
  },
  {
    title: "情绪与互动模式识别",
    text: "把这次记录中的触发点和互动线索温和地呈现出来。",
  },
  {
    title: "非诊断反馈",
    text: "提供支持性、非评判的理解和下一步练习方向。",
  },
  {
    title: "UP训练卡推送",
    text: "根据记录线索推荐一张可执行的陪伴练习卡。",
  },
  {
    title: "家长练习与打卡",
    text: "完成一次小练习，并记录练习前后的感受变化。",
  },
  {
    title: "周度报告",
    text: "一周后回看高频场景、常见情绪和可以继续练习的位置。",
  },
  {
    title: "人工督导补充",
    text: "需要时提交给老师进一步查看，获得边界内的补充建议。",
  },
];

const scenes = ["孩子写作业拖延", "亲子争吵", "手机使用冲突", "考试成绩焦虑", "孩子顶嘴或沉默", "家长事后内疚"];

const startSteps = [
  { title: "第一步：记录一次具体事件", text: "写下发生了什么、我的情绪和当时回应。" },
  { title: "第二步：查看支持性反馈", text: "把这次记录中的互动线索和可调整位置看清楚。" },
  { title: "第三步：选择一个小练习并打卡", text: "从推荐训练卡里选一个动作，完成后记录一次尝试。" },
];

const ethics = [
  "本系统不提供心理诊断。",
  "不替代心理咨询、医学诊断、危机干预或法律判断。",
  "所有反馈仅用于情绪觉察、亲子沟通练习和自我复盘参考。",
  "如涉及自伤、自杀、家庭暴力、儿童安全风险，应及时寻求专业支持。",
  "试点或研究数据应进行匿名化和脱敏处理。",
];

const quickEntries = [
  { title: "情绪日记", text: "记录此刻", tone: "green" },
  { title: "规则识别", text: "支持性反馈", tone: "blue" },
  { title: "训练中心", text: "提升自己", tone: "leaf" },
  { title: "专家支持", text: "人工督导", tone: "soft" },
];

export function LandingPage() {
  return (
    <div className="landingPage">
      <header className="landingNav">
        <a className="brandMark landingBrand" href="/" aria-label="安心陪伴首页">
          <span className="landingBrandIcon" aria-hidden="true" />
          <span>
            <strong>安心陪伴</strong>
            <small>家长情绪管理支持系统</small>
          </span>
        </a>
        <nav className="landingLinks" aria-label="首页导航">
          <a href="#home">首页</a>
          <a href="#flow">核心流程</a>
          <a href="/student">学生画像</a>
          <a href="/assessment">家长测评</a>
          <a href="#usage">使用说明</a>
          <a href="#privacy">隐私边界</a>
        </nav>
        <a className="researchButton" href="/dashboard">
          研究者平台
        </a>
      </header>

      <section className="landingHero" id="home">
        <div className="heroText">
          <p className="eyebrow">ReadFeedback 家长支持系统</p>
          <h1>安心陪伴</h1>
          <p className="heroSubtitle">面向家长的情绪管理与亲子陪伴支持系统</p>
          <p className="heroCopy">
            记录一次亲子情绪事件，获得一条非评判反馈，再进入一张可执行的陪伴练习卡。系统帮助家长先照顾好自己，再更稳定地陪伴孩子。
          </p>
          <div className="heroActions">
            <a className="primaryButton landingPrimary" href="#flow">
              了解安心流程
            </a>
            <a className="secondaryButton landingSecondary" href="/student">
              学生画像入口
            </a>
            <a className="secondaryButton landingSecondary" href="/dashboard">
              研究者平台
            </a>
          </div>
          <div className="landingMoodTags" aria-label="情感关键词">
            <span>温暖</span>
            <span>陪伴</span>
            <span>专业</span>
            <span>安全感</span>
          </div>
        </div>

        <div className="heroPhone" aria-label="小程序首页预览">
          <div className="phoneChrome">
            <span>9:41</span>
            <span>安心陪伴</span>
          </div>
          <div className="phoneGreeting">
            <div>
              <strong>早上好，妈妈</strong>
              <span>新的一天，记得先照顾自己</span>
            </div>
            <span className="bellDot" aria-hidden="true" />
          </div>
          <section className="moodCard" aria-label="今日情绪状态">
            <div>
              <span className="miniLabel">今日情绪状态</span>
              <strong>还可以</strong>
              <span>轻度压力</span>
            </div>
            <button type="button">记录我的情绪</button>
          </section>
          <section className="quickGrid" aria-label="核心功能入口">
            {quickEntries.map((entry) => (
              <article className={`quickCard ${entry.tone}`} key={entry.title}>
                <span aria-hidden="true" />
                <strong>{entry.title}</strong>
                <small>{entry.text}</small>
              </article>
            ))}
          </section>
          <section className="recommendMini" aria-label="今日推荐训练">
            <div className="recommendImage" aria-hidden="true" />
            <div>
              <span className="miniLabel">今日推荐训练</span>
              <strong>5分钟呼吸放松练习</strong>
              <small>缓解紧张情绪，找回平静</small>
            </div>
            <button type="button" aria-label="开始练习" />
          </section>
          <section className="recentMini" aria-label="最近记录">
            <span className="miniFace" aria-hidden="true">?</span>
            <div>
              <strong>有点烦，孩子写作业磨蹭</strong>
              <small>支持性反馈已完成</small>
            </div>
          </section>
          <section className="tipMini" aria-label="安心小贴士">
            <strong>安心小贴士</strong>
            <span>允许自己有情绪，照顾好自己，才能更好地陪伴孩子。</span>
          </section>
        </div>
      </section>

      <section className="landingSection startSection" id="start">
        <div className="sectionIntro">
          <p className="eyebrow">三步开始</p>
          <h2>第一次使用时，先完成一个最小闭环</h2>
          <p>不用一次写很多内容，先从一件具体小事开始。</p>
        </div>
        <div className="startGrid">
          {startSteps.map((step) => (
            <article className="startCard" key={step.title}>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landingSection" id="flow">
        <div className="sectionIntro">
          <p className="eyebrow">核心闭环</p>
          <h2>从一次记录到一次可练习的陪伴回应</h2>
          <p>系统围绕轻量、可复盘的家长练习闭环设计，不把网站变成诊断工具或课程替代品。</p>
        </div>
        <div className="flowGrid">
          {flowSteps.map((step, index) => (
            <article className="flowCard" key={step.title}>
              <span className="stepNumber">{String(index + 1).padStart(2, "0")}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landingSection scenesSection">
        <div className="sectionIntro">
          <p className="eyebrow">适用场景</p>
          <h2>聚焦普通家庭中的高频亲子互动片段</h2>
          <p>这些场景只用于帮助家长观察和练习，不代表对孩子、家长或家庭关系的判断。</p>
        </div>
        <div className="sceneGrid">
          {scenes.map((scene) => (
            <article className="sceneCard" key={scene}>
              {scene}
            </article>
          ))}
        </div>
      </section>

      <section className="landingSection usageSection" id="usage">
        <div className="sectionIntro">
          <p className="eyebrow">使用说明</p>
          <h2>小程序用于日常练习，网站用于了解项目和进入研究者平台</h2>
        </div>
        <div className="usageGrid">
          <article className="usageCard">
            <h3>家长主要使用微信小程序</h3>
            <p>家长主要通过微信小程序完成目标设定、情绪记录、即时反馈、训练卡练习和打卡。</p>
          </article>
          <article className="usageCard">
            <h3>网站首页用于了解项目</h3>
            <p>网站首页用于了解项目定位、核心流程、使用方式和隐私边界。</p>
          </article>
          <article className="usageCard">
            <h3>研究者平台用于试点管理</h3>
            <p>研究者平台用于项目管理、数据查看、训练卡维护、反馈规则查看和试点评估。</p>
          </article>
        </div>
      </section>

      <section className="landingSection ethicsSection" id="privacy">
        <div className="sectionIntro">
          <p className="eyebrow">隐私与伦理边界</p>
          <h2>保持非诊断、非标签化、支持性的使用边界</h2>
        </div>
        <div className="ethicsList">
          {ethics.map((item) => (
            <div className="ethicsItem" key={item}>
              {item}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

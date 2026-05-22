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

const ethics = [
  "本系统不提供心理诊断。",
  "不替代心理咨询、医学诊断、危机干预或法律判断。",
  "所有反馈仅用于情绪觉察、亲子沟通练习和自我复盘参考。",
  "如涉及自伤、自杀、家庭暴力、儿童安全风险，应及时寻求专业支持。",
  "试点或研究数据应进行匿名化和脱敏处理。",
];

export function LandingPage() {
  return (
    <div className="landingPage">
      <header className="landingNav">
        <a className="brandMark" href="/" aria-label="安心陪伴首页">
          安心陪伴
        </a>
        <nav className="landingLinks" aria-label="首页导航">
          <a href="#home">首页</a>
          <a href="#flow">核心流程</a>
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
          <p className="heroCopy">记录一次亲子情绪事件，获得一条非评判反馈，完成一张陪伴练习卡。</p>
          <div className="heroActions">
            <a className="primaryButton landingPrimary" href="#flow">
              了解核心流程
            </a>
            <a className="secondaryButton landingSecondary" href="/dashboard">
              研究者平台
            </a>
          </div>
        </div>
        <div className="heroPanel" aria-label="核心闭环摘要">
          <span>目标</span>
          <span>记录</span>
          <span>识别</span>
          <span>反馈</span>
          <span>练习</span>
          <span>打卡</span>
          <span>周报</span>
          <span>督导</span>
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

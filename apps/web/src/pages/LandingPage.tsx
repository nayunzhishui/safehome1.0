import { useState } from "react";
import { SiteFooter, SiteHeader, UiIcon } from "../components/WebUi";

const flowSteps = [
  ["目标设定", "确定这一周想练习的一个亲子互动小目标。"],
  ["情绪事件记录", "记录具体事件，以及情绪、想法、身体感觉和回应。"],
  ["识别互动线索", "温和地呈现这次记录中的触发点与互动线索。"],
  ["非诊断反馈", "获得支持性、非评判的理解和下一步练习方向。"],
  ["推荐 UP 训练卡", "根据记录线索，推荐一张可执行的陪伴练习卡。"],
  ["练习与打卡", "完成一次小练习，记录练习前后的感受变化。"],
  ["周度回看", "回看高频场景、常见情绪和可以继续练习的位置。"],
  ["人工督导补充", "需要时提交给老师查看，获得边界内的补充建议。"],
];

// Synthetic UI examples only: never sent to an API or presented as user records.
const examples = [
  { label: "作业拖延", event: "晚饭后，我催了几次作业。孩子说“等一下”，我越来越着急，声音也大了起来。", moods: ["着急", "无奈"], feedback: "这次示例里，你似乎很在意孩子能否按时完成作业。着急时，语气可能会变重。可以先留意自己开口前的感受。" },
  { label: "手机使用", event: "约好的手机使用时间到了，孩子还不愿放下。我连续催促了几次，说话的声音越来越大。", moods: ["着急", "生气"], feedback: "这次示例里，着急和催促似乎连在了一起。可以先观察自己的感受，再用一句具体的话说明请求。" },
  { label: "亲子沟通", event: "我问孩子今天过得怎么样，他只说“没什么”。我又连续追问了几句，心里有些担心。", moods: ["担心", "失落"], feedback: "这次示例里，你可能希望多了解孩子一些。对方还没有说话时，可以先给彼此一点停顿，再温和地表达关心。" },
];

const questions = [
  ["第一次使用，应该从哪里开始？", "家长日常使用以微信小程序为主。先记录一次具体事件，再查看支持性反馈，并选择一个可以尝试的小练习。"],
  ["网站和小程序有什么不同？", "小程序用于日常记录与练习。网站用于了解项目、进入支持性测评，以及供研究者、督导与管理员开展试点管理。"],
  ["测评结果能用来诊断吗？", "不能。支持性测评只提供自我了解与阶段性观察线索，不替代心理咨询、医学诊断或危机干预。"],
  ["谁可以进入研究者平台？", "研究者、督导与管理员按现有账号权限进入。不同角色可查看、操作的内容不同。"],
];

export function LandingPage() {
  const [scene, setScene] = useState(0);
  const example = examples[scene];
  return <div className="companionHome">
    <SiteHeader home />
    <section className="companionHero" id="home">
      <h1>陪伴孩子，<br />也别忘了照顾自己。</h1>
      <div className="companionActions"><a className="primaryButton" href="#flow">了解安心流程 <UiIcon name="arrow" size={18} /></a><a className="plainAction" href="#usage">使用说明 <span aria-hidden="true">↓</span></a></div>
      <section className="companionPreview" aria-label="陪伴流程示例">
        <div className="previewHeading"><h2>一次记录，如何走向一个小练习</h2><span>示例 · 非真实记录</span></div>
        <div className="sceneSwitcher" role="group" aria-label="选择演示场景">{examples.map((item, index) => <button type="button" key={item.label} aria-pressed={scene === index} onClick={() => setScene(index)}>{item.label}</button>)}</div>
        <div className="previewBody" aria-live="polite" aria-atomic="true">
          <article className="previewDiary"><h3>01 · 事件记录</h3><p>{example.event}</p><div className="previewMoods" aria-label="示例中的感受">{example.moods.map((mood) => <span key={mood}>{mood}</span>)}</div></article>
          <div className="previewResponse"><section><h3>02 · 支持性反馈</h3><p>{example.feedback}</p></section><article className="previewPractice"><span className="previewClock"><UiIcon name="clock" size={28} /></span><div><p className="previewMetadata">03 · 小练习 / 约 1 分钟</p><h3>3 秒暂停卡：开口前先停一下</h3><p>发现自己想立刻批评时，先停住第一句话 3 秒。</p></div></article></div>
        </div>
      </section>
      <div className="companionBoundary"><span>情绪觉察 · 亲子沟通练习 · 自我复盘</span><span>提供支持性反馈，不作心理诊断</span></div>
    </section>
    <section className="companionSection companionScenes"><div><h2>那些来不及<br />好好说话的时刻。</h2><p>聚焦普通家庭里的具体互动，<br />不是给孩子、家长或关系下结论。</p></div><ul>{["孩子写作业拖延", "亲子争吵", "手机使用冲突", "考试成绩焦虑", "孩子顶嘴或沉默", "家长事后内疚"].map((label) => <li key={label}>{label}</li>)}</ul></section>
    <section className="companionSection companionFlow" id="flow"><div className="companionSectionHeading"><h2>把一次情绪，<br />变成一次练习。</h2><p>不用一次写很多。先从一件具体小事开始，<br />再慢慢积累可以回看的陪伴经验。</p></div><nav className="journeyLinks" aria-label="流程分段导航">{[["记录 · 1—2", 1], ["理解 · 3—4", 3], ["练习 · 5—6", 5], ["回看与支持 · 7—8", 7]].map(([label, step]) => <a href={`#journey-${step}`} key={step}>{label}</a>)}</nav><ol className="companionSteps">{flowSteps.map(([title, copy], index) => <li key={title} id={`journey-${index + 1}`}><span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span><h3>{title}</h3><p>{copy}</p></li>)}</ol></section>
    <section className="companionSection companionUsage" id="usage"><h2>日常陪伴在小程序，<br />在这里，先了解彼此。</h2><div className="companionPurposes">{[
      ["微信小程序", "家长的日常练习入口。完成目标设定、情绪记录、反馈查看、训练卡练习和打卡。"],
      ["网站首页", "了解项目定位、完整流程、使用方式与隐私边界，也可进入支持性测评。"],
      ["研究者平台", "面向试点管理与人工支持。查看记录、维护内容、管理督导与研究导出。"],
    ].map(([title, copy]) => <article key={title}><h3>{title}</h3><p>{copy}</p></article>)}</div><div className="assessmentEntries"><h3>想多了解一点自己的状态？</h3><div>{[
      ["/student", "学生支持性画像", "从支持性测评中，认识自己的阶段性状态。"],
      ["/assessment", "家长支持性测评", "从日常互动出发，了解自己的感受与回应。"],
    ].map(([href, title, copy]) => <a href={href} key={href}><span className="entryIcon"><UiIcon name="document" size={24} /></span><span><strong>{title}</strong><span>{copy}</span></span><UiIcon name="external" size={24} /></a>)}</div></div></section>
    <section className="companionSection companionFaq" id="faq"><div><h2>开始之前，<br />你也许想问。</h2><p>选择一个问题，展开了解。</p></div><div>{questions.map(([question, answer], index) => <details key={question} open={index === 0 || undefined}><summary>{question}<span aria-hidden="true" className="faqPlus" /></summary><p>{answer}</p></details>)}</div></section>
    <section className="companionSection companionEthics" id="privacy"><div><h2>安心，也来自<br />清楚的边界。</h2><p>非诊断 · 非标签化 · 支持性</p></div><div><article><h3>支持练习，不替代专业判断</h3><p>所有反馈仅用于情绪觉察、亲子沟通练习和自我复盘参考，不替代心理咨询、医学诊断、危机干预或法律判断。</p></article><article><h3>遇到安全风险，及时寻求专业支持</h3><p>如涉及自伤、自杀、家庭暴力或儿童安全风险，应及时寻求专业支持。</p></article><article><h3>试点与研究，重视数据边界</h3><p>试点或研究数据应进行匿名化和脱敏处理。</p></article></div></section>
    <SiteFooter />
  </div>;
}

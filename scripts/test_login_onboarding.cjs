const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const consent = require("../apps/miniprogram/utils/serviceConsent");
let storage = { auth_user: { id: "synthetic-user" } };
global.wx = { getStorageSync: k => storage[k], setStorageSync: (k,v) => storage[k]=v, removeStorageSync: k => delete storage[k], getPrivacySetting: ({success}) => success({needAuthorization:false}) };
const page = () => ({ data:{}, setData(v){ Object.assign(this.data,v); } });
const tick = () => new Promise(resolve => setImmediate(resolve));
consent.acceptLocalNotice();
let count = 0, failures = 0;
async function check(name, fn) { if(process.argv[2] && !name.includes(process.argv[2])) return; try { await fn(); count++; console.log("PASS " + name); } catch(error) { failures++; console.error("FAIL " + name, error.message); } }
(async () => {
 await check("rejecting a feature notice sends no consent or participant data", async () => {
   const p=page();let writes=0;
   const api={listConsentRecords:async()=>({items:[]}),createConsent:async()=>{writes++;}};
   const pending=consent.ensureServiceConsent(p,api,"diary");await tick();
   assert.equal(p.data.serviceConsent.purpose,"diary_record");consent.finishServiceConsent(p,false);
   assert.equal(await pending,false);assert.equal(writes,0);
 });
 await check("agreement is saved with exact feature, version and concurrency guard", async () => {
   const p=page();let saved;
   const api={listConsentRecords:async()=>({items:[{id:"previous",consent_type:"service_data",agreed:false,event_version:3}]}),createConsent:async data=>{saved=data;}};
   const pending=consent.ensureServiceConsent(p,api,"assessment");await tick();consent.finishServiceConsent(p,true);
   assert.equal(await pending,true);assert.equal(saved.expected_latest_id,"previous");assert.equal(saved.purpose,"supportive_assessment");assert.equal(saved.consent_version,consent.VERSION);
 });
 await check("consent save failure cannot be treated as permission to submit", async () => {
   const p=page();const api={listConsentRecords:async()=>({items:[]}),createConsent:async()=>{throw Error("offline");}};
   const pending=consent.ensureServiceConsent(p,api,"diary");await tick();consent.finishServiceConsent(p,true);await assert.rejects(pending,/offline/);assert.equal(p._consentPending,false);
 });
 await check("feature acknowledgements survive other feature use but not withdrawal", async () => {
   const items=[{id:"a",consent_type:"service_data",agreed:true,event_version:1,consent_version:consent.VERSION,purpose:"diary_record"},{id:"b",consent_type:"service_data",agreed:true,event_version:2,consent_version:consent.VERSION,purpose:"program_entry"}];
   const api={listConsentRecords:async()=>({items}),createConsent:async()=>{throw Error("unexpected write");}};
   assert.equal(await consent.ensureServiceConsent(page(),api,"diary"),true);
   items.push({id:"c",consent_type:"service_data",agreed:false,event_version:3});
   const p=page();const pending=consent.ensureServiceConsent(p,api,"diary");await tick();assert.ok(p.data.serviceConsent);consent.finishServiceConsent(p,false);assert.equal(await pending,false);
 });
 await check("changing accounts while consent is open cannot save another user's choice", async () => {
   const p=page();let writes=0;const api={listConsentRecords:async()=>({items:[]}),createConsent:async()=>{writes++;}};
   const pending=consent.ensureServiceConsent(p,api,"program");await tick();storage.auth_user={id:"other"};consent.finishServiceConsent(p,true);await assert.rejects(pending,/账号已变化/);assert.equal(writes,0);storage.auth_user={id:"synthetic-user"};
 });
 function loadPage(file, api, wxOverrides={}) {
   let definition;
   const w={...global.wx,hideTabBar(){},showTabBar(){},pageScrollTo({complete}){complete();},getWindowInfo(){return {windowHeight:700,windowWidth:390};},createSelectorQuery(){return {in(){return this;},select(){return this;},boundingClientRect(cb){cb({left:20,top:90,bottom:170,width:350,height:80});return this;},exec(){}};},...wxOverrides};
   const sandbox={wx:w,Page:p=>definition=p,require:name=> name.endsWith("serviceConsent")?consent:name.endsWith("resilientForm")?require("../apps/miniprogram/utils/resilientForm"):name.endsWith("cloudConfig")?{getCloudConfig:()=>({useLocalHttp:false})}:name.endsWith("/api")?{createSafeHomeApi:()=>api}:new Proxy({}, {get:()=>()=>({})}),getApp:()=>({}),console,setTimeout,clearTimeout};
   vm.runInNewContext(fs.readFileSync(path.join(root,file),"utf8"),sandbox,{filename:file});
   const p={...definition,data:{...definition.data},setData(v,callback){Object.assign(this.data,v);if(callback)callback();}};return p;
 }
 await check("cloud identity mode does not require wx.login or submit a fabricated code", async () => {
   let payload,completed=0;
   const p=loadPage("apps/miniprogram/pages/login/index.js",{wechatLogin:async data=>{payload=data;return {user:{role:"parent"}};}});
   p.data.wechatMode="cloudbase_identity";p.completeLogin=()=>{completed++;};p.submitWechatLogin();await tick();assert.deepEqual(JSON.parse(JSON.stringify(payload)),{});assert.equal(completed,1);assert.equal(p.data.wechatLoading,false);
 });
 await check("first visit shows privacy before home data and declining does not approve", async () => {
   delete storage["safehome:serviceNotice:v1"];let reads=0;
   const p=loadPage("apps/miniprogram/pages/home/index.js",{}, {navigateTo(){}});p.refreshHomeData=()=>{reads++;};
   p.onShow();assert.equal(p.data.welcomeVisible,true);assert.equal(reads,0);p.onGuideDecline();assert.equal(consent.hasLocalNotice(),false);
 });
 await check("tutorial advances, goes back and completes without recording participation", async () => {
   consent.acceptLocalNotice();const p=loadPage("apps/miniprogram/pages/home/index.js",{});p.startGuide();assert.equal(p.data.tourIndex,0);assert.ok(p.data.tourRect);p.nextGuide();assert.equal(p.data.tourIndex,1);p.previousGuide();assert.equal(p.data.tourIndex,0);for(let n=0;n<6;n++)p.nextGuide();assert.equal(p.data.tourVisible,false);assert.equal(storage["safehome:homeTour:v1"],true);
 });
 await check("all guide anchors and privacy destinations resolve in source", async () => {
   const s=fs.readFileSync(path.join(root,"apps/miniprogram/pages/home/index.js"),"utf8");
   const markup=fs.readFileSync(path.join(root,"apps/miniprogram/pages/home/index.wxml"),"utf8");
   for(const match of s.matchAll(/selector: "#([^"]+)"/g))assert.ok(markup.includes(`id="${match[1]}"`),match[1]);
   const app=JSON.parse(fs.readFileSync(path.join(root,"apps/miniprogram/app.json"),"utf8"));assert.ok(app.pages.includes("pages/settings-detail/index"));
   for(const name of ["diary-form","assessment-detail"]) {
     const source=fs.readFileSync(path.join(root,`apps/miniprogram/pages/${name}/index.js`),"utf8");
     assert.ok(source.indexOf("await ensureServiceConsent")<source.indexOf("loadAfterConsent(this._entryOptions)"));
     assert.ok(fs.readFileSync(path.join(root,`apps/miniprogram/pages/${name}/index.wxml`),"utf8").includes('wx:if="{{serviceReady}}"'));
   }
 });
 await check("a pending platform privacy update blocks homepage reads", async () => {
   consent.acceptLocalNotice();let respond,reads=0;
   const p=loadPage("apps/miniprogram/pages/home/index.js",{}, {getPrivacySetting(options){respond=options;}});
   p.refreshHomeData=()=>{reads++;};p.onShow();assert.equal(reads,0);respond.success({needAuthorization:true});assert.equal(reads,0);assert.equal(p.data.welcomeVisible,true);
 });
 await check("a failed platform privacy query cannot release home data", async () => {
   consent.acceptLocalNotice();let respond,reads=0;
   const p=loadPage("apps/miniprogram/pages/home/index.js",{}, {getPrivacySetting(options){respond=options;}});
   p.refreshHomeData=()=>{reads++;};p.onShow();respond.fail({});assert.equal(reads,0);assert.equal(p.data.welcomeVisible,true);
 });
 await check("native consent wrappers stop declined writes and preserve accepted payloads", async () => {
   consent.acceptLocalNotice();storage.auth_token="synthetic-token";
   const { createSafeHomeApi } = require("../apps/miniprogram/services/api");
   const client=createSafeHomeApi({defaultUserId:"synthetic-user"});
   const p=page();global.getCurrentPages=()=>[p];
   let consentChoice=false;const calls=[];
   global.wx.showModal=({success})=>success({confirm:consentChoice});
   global.wx.request=options=>{
     calls.push({url:options.url,data:options.data,method:options.method});
     options.success({statusCode:200,data:{ok:true,data:options.url.endsWith("/api/consent")&&options.method==="GET"?{items:[]}:{id:"synthetic-result"}},header:{}});
   };
   await assert.rejects(client.createGoal({smart_goal:"合成目标"}),error=>error.code==="consent_declined");
   assert.equal(calls.filter(c=>c.url.endsWith("/api/goals")).length,0);
   calls.length=0;consentChoice=true;
   await client.createGoal({smart_goal:"合成目标"});
   const write=calls.find(c=>c.url.endsWith("/api/goals"));assert.equal(write.data.smart_goal,"合成目标");assert.equal(write.data.user_id,"synthetic-user");
   assert.ok(calls.findIndex(c=>c.url.endsWith("/api/consent")&&c.method==="POST")<calls.indexOf(write));
   calls.length=0;
   global.wx.request=options=>{
     calls.push({url:options.url,method:options.method});
     const fail=options.url.endsWith("/api/consent")&&options.method==="POST";
     options.success({statusCode:fail?503:200,data:fail?{ok:false,error:{code:"service_unavailable"}}:{ok:true,data:{items:[]}},header:{}});
   };
   await assert.rejects(client.createCheckin({completed:true}));
   assert.equal(calls.filter(c=>c.url.endsWith("/api/checkins")).length,0);
   delete global.getCurrentPages;
 });
 await check("an old consent modal cannot continue after its page is disposed", async () => {
   consent.acceptLocalNotice();const p=page();let writes=0;
   const pending=consent.ensureServiceConsent(p,{listConsentRecords:async()=>({items:[]}),createConsent:async()=>{writes++;}},"diary");
   await tick();p._consentDisposed=true;consent.finishServiceConsent(p,true);await assert.rejects(pending,/页面已关闭/);assert.equal(writes,0);
 });
 await check("deep-linked feature cannot collect consent before the basic privacy notice", async () => {
   delete storage["safehome:serviceNotice:v1"];let reads=0;
   await assert.rejects(consent.ensureServiceConsent(page(),{listConsentRecords:async()=>{reads++;}},"assessment"),/返回首页/);assert.equal(reads,0);consent.acceptLocalNotice();
 });
 await check("platform privacy revocation and query failure block feature consent reads", async () => {
   consent.acceptLocalNotice();const original=global.wx.getPrivacySetting;let reads=0;
   const api={listConsentRecords:async()=>{reads++;return {items:[]};}};
   global.wx.showModal=({success})=>success({confirm:false});
   try {
     global.wx.getPrivacySetting=({success})=>success({needAuthorization:true});
     await assert.rejects(consent.ensureServiceConsent(page(),api,"goal",true),/隐私/);
     global.wx.getPrivacySetting=({fail})=>fail({});
     await assert.rejects(consent.ensureServiceConsent(page(),api,"goal",true),/隐私/);
     assert.equal(reads,0);
   } finally { global.wx.getPrivacySetting=original; }
 });
 await check("declined welcome stays blocking when privacy navigation fails", async () => {
   delete storage["safehome:serviceNotice:v1"];
   const p=loadPage("apps/miniprogram/pages/home/index.js",{}, {navigateTo(options){if(options.fail)options.fail({});}});
   p.onShow();p.onGuideDecline();assert.equal(p.data.welcomeVisible,true);assert.equal(consent.hasLocalNotice(),false);
   consent.acceptLocalNotice();
 });
 await check("account and phone login ignore overlapping requests", async () => {
   let calls=0;const pending=()=>{calls++;return new Promise(()=>{});};
   const p=loadPage("apps/miniprogram/pages/login/index.js",{login:pending,phoneLogin:pending});
   p.data.username="synthetic";p.data.password="synthetic-only";p.submitLogin();p.submitLogin();p.handlePhoneLogin({detail:{code:"synthetic-code"}});
   assert.equal(calls,1);
   const q=loadPage("apps/miniprogram/pages/login/index.js",{login:pending,phoneLogin:pending});
   q.handlePhoneLogin({detail:{code:"synthetic-code"}});q.handlePhoneLogin({detail:{code:"synthetic-code"}});assert.equal(calls,2);
 });
 await check("resilient drafts are isolated between accounts and restored to their owner", async () => {
   const {createResilientForm}=require("../apps/miniprogram/utils/resilientForm");
   const make=()=>createResilientForm({storageKey:"synthetic:review-draft",fields:["text"],submissionPrefix:"review",hasContent:v=>!!v.text});
   try {
     storage.auth_user={id:"synthetic-A"};make().flush({text:"synthetic-A-text"});
     storage.auth_user={id:"synthetic-B"};assert.equal(make().restore(),null);make().flush({text:"synthetic-B-text"});
     storage.auth_user={id:"synthetic-A"};assert.equal(make().restore().values.text,"synthetic-A-text");
   } finally {storage.auth_user={id:"synthetic-user"};}
 });
 await check("an old draft controller cannot save after account switch", async () => {
   const {createResilientForm}=require("../apps/miniprogram/utils/resilientForm");
   const make=()=>createResilientForm({storageKey:"synthetic:old-controller",fields:["text"],submissionPrefix:"review",hasContent:v=>!!v.text});
   try {
     storage.auth_user={id:"synthetic-A"};const old=make();old.flush({text:"original"});
     storage.auth_user={id:"synthetic-B"};old.flush({text:"wrong-session"});
     assert.throws(()=>old.getSubmissionId(),/账号已变化/);
     storage.auth_user={id:"synthetic-A"};assert.equal(make().restore().values.text,"original");
   } finally {storage.auth_user={id:"synthetic-user"};}
 });
 await check("tutorial skip, replay and missing anchor do not create participation", async () => {
   consent.acceptLocalNotice();const p=loadPage("apps/miniprogram/pages/home/index.js",{}, {createSelectorQuery(){return {in(){return this;},select(){return this;},boundingClientRect(cb){cb(null);return this;},exec(){}};}});
   p.startGuide();assert.equal(p.data.tourRect,null);p.endGuide();assert.equal(p.data.tourVisible,false);p.startGuide();assert.equal(p.data.tourVisible,true);assert.equal(p.data.tourIndex,0);
 });
 await check("privacy components never emit agreement without an explicit checkbox", async () => {
   for(const name of ["service-consent","onboarding-guide"]) {
     let definition;const events=[];
     vm.runInNewContext(fs.readFileSync(path.join(root,`apps/miniprogram/components/${name}/index.js`),"utf8"),{Component:value=>definition=value,wx:global.wx});
     const c={...definition.methods,data:{...definition.data},setData(v){Object.assign(this.data,v);},triggerEvent(...args){events.push(args);}};
     c.agree();assert.equal(events.length,0);c.check({detail:{value:["agree"]}});c.agree();assert.equal(events.length,1);
     c.check({detail:{value:[]}});c.agree();assert.equal(events.length,1);
   }
 });
 await check("phone authorization denial sends no login request", async () => {
   let calls=0;const p=loadPage("apps/miniprogram/pages/login/index.js",{phoneLogin(){calls++;}});
   p.handlePhoneLogin({detail:{errMsg:"getPhoneNumber:fail user deny"}});assert.equal(calls,0);assert.equal(p.data.status,"idle");assert.equal(p.data.phoneLoading,false);
 });
 await check("standard WeChat login submits the returned code and handles missing code", async () => {
   let payload,completed=0;const api={wechatLogin:async data=>{payload=data;return {user:{role:"parent"}};}};
   const p=loadPage("apps/miniprogram/pages/login/index.js",api,{login:({success})=>success({code:"synthetic-wx-code"})});
   p.completeLogin=()=>{completed++;};p.submitWechatLogin();await tick();assert.equal(payload.code,"synthetic-wx-code");assert.equal(completed,1);
   payload=null;const q=loadPage("apps/miniprogram/pages/login/index.js",api,{login:({success})=>success({})});q.submitWechatLogin();await tick();assert.equal(payload,null);assert.equal(q.data.status,"error");assert.equal(q.data.wechatLoading,false);
 });
 for(const name of ["goal-setting","checkin","supervision","program-detail","relationship-task"]) {
   await check(`${name} waits for consent before initializing or restoring local data`,async()=>{
     let initialized=0;
     const p=loadPage(`apps/miniprogram/pages/${name}/index.js`,{listConsentRecords:async()=>({items:[]}),createConsent:async()=>({})});
     p.loadAfterConsent=()=>{initialized++;};
     const opening=p.onLoad({id:"synthetic-program",type:"sentence_completion",enrollment_id:"synthetic-enrollment"});await tick();
     assert.equal(initialized,0);assert.equal(p.data.serviceReady,false);assert.ok(p.data.serviceConsent);
     if(p.onHide)p.onHide();assert.equal(p.draftController,undefined);
     consent.finishServiceConsent(p,false);await opening;assert.equal(initialized,0);assert.equal(p.data.serviceReady,false);
     const retry=p.beginServiceEntry();await tick();consent.finishServiceConsent(p,true);await retry;assert.equal(initialized,1);assert.equal(p.data.serviceReady,true);
   });
 }
 await check("program draft key separates accounts and rejects an old page writer",async()=>{
   const api={listConsentRecords:async()=>({items:[]}),createConsent:async()=>({})};
   const make=()=>{const p=loadPage("apps/miniprogram/pages/program-detail/index.js",api,{showToast(){}});p.loadProgram=()=>{};p.loadAfterConsent({id:"synthetic-program"});p.setData({selectedSession:{session_no:1},draftText:"A-only",serviceReady:true});return p;};
   try {
     storage.auth_user={id:"synthetic-A"};const a=make();let saving=a.saveDraft();await tick();consent.finishServiceConsent(a,true);await saving;
     storage.auth_user={id:"synthetic-B"};const b=make();b.loadDraft();assert.equal(b.data.draftText,"");
     a.setData({draftText:"wrong-owner"});await a.saveDraft();
     storage.auth_user={id:"synthetic-A"};const restored=make();restored.loadDraft();assert.equal(restored.data.draftText,"A-only");
   }finally{storage.auth_user={id:"synthetic-user"};}
 });
 await check("relationship drafts and home discovery are account scoped",async()=>{
   const make=()=>{const p=loadPage("apps/miniprogram/pages/relationship-task/index.js",{});p.loadAfterConsent({enrollment_id:"synthetic-enrollment",type:"sentence_completion"});p.setData({serviceReady:true});return p;};
   try {
     storage.auth_user={id:"synthetic-A"};const a=make();a.setData({answers:{"争吵":"synthetic-A"},narration:"synthetic-note"});a.persistDraftNow();
     storage.auth_user={id:"synthetic-B"};const b=make();assert.equal(b.data.draftRestored,false);assert.notEqual(a.draftKey,b.draftKey);
     const keys=Object.keys(storage).filter(k=>k.startsWith("relationship_task_draft:")||k.startsWith("safehome:programDraft:"));
     let findDraft;vm.runInNewContext(fs.readFileSync(path.join(root,"apps/miniprogram/pages/home/index.js"),"utf8")+"\nexpose(findLocalDraftAction);",{wx:{...global.wx,getStorageInfoSync:()=>({keys})},require:()=>({createSafeHomeApi:()=>({})}),Page(){},expose:fn=>findDraft=fn});
     assert.equal(findDraft(),null);storage.auth_user={id:"synthetic-A"};assert.ok(findDraft());
   }finally{storage.auth_user={id:"synthetic-user"};}
 });
 await check("task availability: closed and unknown cards cannot use cached or default content",async()=>{
   storage["safehome:selectedTrainingCard"]={id:"emotion_naming",title:"stale",stepsList:[{text:"stale"}]};
   for(const options of [{id:"emotion_awareness"},{card_id:"missing"}]) {
     const p=loadPage("apps/miniprogram/pages/task-detail/index.js",{listCards:async()=>({items:[]})});
     await p.onLoad(options);if(p.onShow)await p.onShow();
     assert.equal(p.data.task,null);assert.ok(p.data.errorMessage);
   }
 });
 await check("task availability: current server content replaces cached title and steps",async()=>{
   const p=loadPage("apps/miniprogram/pages/task-detail/index.js",{listCards:async()=>({items:[{id:"emotion_naming",title:"current",steps:["server step"],boundary_notice:"temporary notice"}]})});
   await p.onLoad({id:"emotion_awareness",card_title:"spoofed"});if(p.onShow)await p.onShow();
   assert.equal(p.data.task.title,"current");assert.equal(p.data.task.steps[0],"server step");assert.equal(p.data.task.boundaryNotice,"temporary notice");
 });
 await check("task availability: hidden page drops pending response and rechecks on return",async()=>{
   let resolve;const api={listCards:()=>new Promise(r=>{resolve=r;})};
   const p=loadPage("apps/miniprogram/pages/task-detail/index.js",api);p.onLoad({id:"emotion_awareness"});const pending=p.onShow();p.onHide();
   resolve({items:[{id:"emotion_naming",title:"stale",steps:["stale"]}]});await pending;assert.equal(p.data.task,null);
   api.listCards=async()=>({items:[]});await p.onShow();assert.equal(p.data.task,null);assert.ok(p.data.errorMessage);
 });
 await check("task availability: reflection requires explicit consent before accepting input",async()=>{
   consent.acceptLocalNotice();const api={listCards:async()=>({items:[{id:"emotion_naming",steps:["step"]}]}),listConsentRecords:async()=>({items:[]}),createConsent:async()=>({})};
   const p=loadPage("apps/miniprogram/pages/task-detail/index.js",api);p.onLoad({id:"emotion_awareness"});await p.onShow();
   p.onReflectionInput({detail:{value:"must not save"}});assert.equal(p.data.reflection,"");
   const declined=p.beginReflection();await tick();consent.finishServiceConsent(p,false);await declined;assert.equal(p.data.serviceReady,false);
   const accepted=p.beginReflection();await tick();consent.finishServiceConsent(p,true);await accepted;
   p.onReflectionInput({detail:{value:"synthetic"}});assert.equal(p.data.reflection,"synthetic");
 });
 await check("training catalogue: shows exactly the current API cards and handles closure",async()=>{
   let items=[{id:"synthetic_new_card",title:"新卡",steps:["step"]}];let url;
   const p=loadPage("apps/miniprogram/pages/training/index.js",{listCards:async()=>({items})},{navigateTo:o=>{url=o.url;}});
   await p.loadAvailableCards();assert.equal(p.data.trainingStages[0].tasks.length,1);assert.equal(p.data.trainingStages[0].tasks[0].id,"synthetic_new_card");
   p.openTrainingCard({detail:{id:"synthetic_new_card"},currentTarget:{dataset:{}}});assert.ok(url.includes("card_id=synthetic_new_card"));
   items=[];await p.loadAvailableCards();assert.equal(p.data.trainingStages.length,0);
 });
 await check("training catalogue: closed cards cannot persist in cached recommendations",async()=>{
   storage["safehome:latestTrainingRecommendation"]={cardIds:["closed"],cards:[{id:"closed",title:"old"}]};
   storage["safehome:threeDayLightPlan"]={sourceType:"assessment",days:[{day:1,cardId:"closed"}]};
   const p=loadPage("apps/miniprogram/pages/training/index.js",{listCards:async()=>({items:[]}),getShowcaseAccess:async()=>({enabled:false}),getTrainingPlan:async()=>({})});
   await p.onShow();assert.equal(p.data.latestRecommendation,null);assert.equal(p.data.threeDayPlan,null);
 });
 console.log(`${count} focused checks passed; ${failures} failed`);
 if(failures)process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1;});

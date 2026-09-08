const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const consent = require("../apps/miniprogram/utils/serviceConsent");
let storage = { auth_user: { id: "synthetic-user" } };
global.wx = { getStorageSync: k => storage[k], setStorageSync: (k,v) => storage[k]=v };
const page = () => ({ data:{}, setData(v){ Object.assign(this.data,v); } });
const tick = () => new Promise(resolve => setImmediate(resolve));
consent.acceptLocalNotice();
let count = 0;
async function check(name, fn) { await fn(); count++; console.log("PASS " + name); }
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
   const sandbox={wx:w,Page:p=>definition=p,require:name=> name.endsWith("serviceConsent")?consent:name.endsWith("cloudConfig")?{getCloudConfig:()=>({useLocalHttp:false})}:name.endsWith("/api")?{createSafeHomeApi:()=>api}:new Proxy({}, {get:()=>()=>({})}),getApp:()=>({}),console,setTimeout,clearTimeout};
   vm.runInNewContext(fs.readFileSync(path.join(root,file),"utf8"),sandbox,{filename:file});
   const p={...definition,data:{...definition.data},setData(v){Object.assign(this.data,v);}};return p;
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
 console.log(`${count} focused checks passed`);
})().catch(error=>{console.error(error);process.exitCode=1;});

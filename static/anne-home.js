(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const activity = [];
  const names = {home:"Home",create:"Create",intelligence:"Intelligence",agents:"Agents",business:"Business",projects:"Projects",assets:"Assets",activity:"Activity",settings:"Settings"};
  function record(title, detail, ok) {
    activity.unshift({title,detail,ok,time:new Date().toLocaleTimeString()});
    activity.splice(12);
    renderActivity();
  }
  function renderActivity() {
    const host=$("activity-list"); if(!host) return;
    host.replaceChildren();
    if(!activity.length){const p=document.createElement("p");p.className="empty-state";p.textContent="No checks recorded yet.";host.append(p);return;}
    activity.forEach(item=>{const row=document.createElement("div");row.className="activity-item";const dot=document.createElement("i");dot.style.background=item.ok===true?"#b7c5bc":item.ok===false?"#b99c9c":"#78838a";const body=document.createElement("div");const b=document.createElement("b");b.textContent=item.title;const small=document.createElement("small");small.textContent=item.detail+" · "+item.time;body.append(b,small);row.append(dot,body);host.append(row);});
  }
  function showView(name) {
    if(!names[name]) return;
    document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id==="view-"+name));
    document.querySelectorAll(".nav-item[data-view]").forEach(b=>b.classList.toggle("active",b.dataset.view===name));
    $("crumb-current").textContent=names[name];
    document.title="ANNE — "+names[name];
    $("sidebar").classList.remove("open");
    try{history.replaceState(null,"","#"+name);}catch(_){}
  }
  document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>showView(b.dataset.view)));
  document.querySelectorAll("[data-go]").forEach(b=>b.addEventListener("click",()=>showView(b.dataset.go)));
  $("mobile-menu").addEventListener("click",()=>$("sidebar").classList.toggle("open"));
  $("today-date").textContent=new Intl.DateTimeFormat(undefined,{weekday:"long",month:"long",day:"numeric"}).format(new Date());
  $("copy-brief").addEventListener("click",async()=>{
    const value=$("design-brief").value.trim();
    if(!value){$("copy-feedback").textContent="Add a few words to your brief first.";return;}
    try{await navigator.clipboard.writeText(value);$("copy-feedback").textContent="Design brief copied. Ready to paste into Cursor.";}
    catch(_){$("design-brief").focus();$("design-brief").select();$("copy-feedback").textContent="Select the text and copy it from here.";}
  });
  function pillText(el,text,kind){el.textContent=text;el.className=kind||"";}
  function addProviderRow(host,name,detail,allowed){
    const row=document.createElement("div");row.className="provider-item";
    const left=document.createElement("div");const b=document.createElement("b");b.textContent=name;const small=document.createElement("small");small.textContent=detail;left.append(b,small);
    const state=document.createElement("span");state.className="provider-state"+(allowed?"":" blocked");state.textContent=allowed?"Self-hosted":"Hosted / unverified";row.append(left,state);host.append(row);
  }
  async function getJson(path){
    const response=await fetch(path,{method:"GET",credentials:"same-origin",cache:"no-store",headers:{Accept:"application/json"}});
    if(!response.ok)throw new Error(path+" · HTTP "+response.status);
    return response.json();
  }
  async function refresh(){
    const [healthResult,providersResult]=await Promise.allSettled([getJson("/api/health/agent"),getJson("/api/providers")]);
    if(healthResult.status==="fulfilled"){
      const h=healthResult.value;const online=h&&h.alive===true;
      $("home-runtime").textContent=online?"Online":h&&h.alive===false?"Offline":"Unverified";
      $("runtime-note").textContent=online?"Hermes reports a live heartbeat.":"No live heartbeat confirmed.";
      $("runtime-status").textContent=online?"Heartbeat verified":"Runtime not verified";
      $("runtime-dot").className="mini-dot"+(online?"":" offline");
      $("service-runtime").textContent=online?"Online":h&&h.alive===false?"Offline":"Unverified";
      $("intel-runtime").textContent=online?"Online":h&&h.alive===false?"Offline":"Unverified";
      $("intel-runtime-note").textContent=online?"Live heartbeat confirmed":"Health endpoint returned no live heartbeat";
      record("Hermes runtime check",online?"Live heartbeat confirmed":"Runtime not confirmed",online);
    }else{
      $("home-runtime").textContent="Unavailable";$("runtime-note").textContent="Could not read Hermes health."; $("runtime-status").textContent="Check unavailable";$("runtime-dot").className="mini-dot offline";$("service-runtime").textContent="Unavailable";$("intel-runtime").textContent="Unavailable";$("intel-runtime-note").textContent=healthResult.reason.message;record("Hermes runtime check",healthResult.reason.message,false);
    }
    if(providersResult.status==="fulfilled"){
      const payload=providersResult.value||{};const providers=Array.isArray(payload.providers)?payload.providers:[];
      const count=providers.reduce((n,p)=>n+(Array.isArray(p.models)?p.models.length:0),0);
      $("home-models").textContent=count+" models";$("models-note").textContent=providers.length+" registered provider(s)";$("models-status").textContent="Registry read";$("models-dot").className="mini-dot";
      $("service-providers").textContent=providers.length+" provider(s)";$("intel-models").textContent=count+" models";$("intel-models-note").textContent=providers.length+" provider(s) in existing registry";
      const host=$("provider-list");host.replaceChildren();
      if(!providers.length){const p=document.createElement("p");p.className="empty-state";p.textContent="No providers returned by the existing Hermes registry.";host.append(p);}
      providers.forEach(p=>addProviderRow(host,String(p.display_name||p.id||"Unnamed provider"),(Array.isArray(p.models)?p.models.length:0)+" registered model(s) · "+(p.base_url||"endpoint not disclosed"),p.is_self_hosted===true));
      record("Provider registry check",providers.length+" provider(s), "+count+" model(s) read",true);
    }else{
      $("home-models").textContent="Unavailable";$("models-note").textContent="Provider registry could not be read.";$("models-status").textContent="Check unavailable";$("models-dot").className="mini-dot offline";$("service-providers").textContent="Unavailable";$("intel-models").textContent="Unavailable";$("intel-models-note").textContent=providersResult.reason.message;
      const host=$("provider-list");host.replaceChildren();const p=document.createElement("p");p.className="empty-state";p.textContent=providersResult.reason.message;host.append(p);record("Provider registry check",providersResult.reason.message,false);
    }
  }
  $("refresh-intel").addEventListener("click",refresh);
  const initial=location.hash.replace("#","");showView(names[initial]?initial:"home");
  refresh();
})();
/* Referral Bridge portal: sign-in, authenticator-app MFA, password setup and invite codes.
   The database (row-level security) decides what each person can see. This page only
   moves people through sign-in and shows what my_access() reports. */
(function(){
"use strict";
var $=function(s){return document.querySelector(s)};
var app=$("#app"), signoutBtn=$("#signout");
var esc=function(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})};
var MIN_PW=12;
var ROLE={company_admin:"Company admin",employee:"Employee",guest:"Guest",bot:"Bot"};

var screen="";
function show(html,name){screen=name||"";app.innerHTML='<div class="card">'+html+'</div>';var f=app.querySelector("input");if(f)f.focus()}
function fail(msg){var e=$("#msg");if(e){e.className="err";e.textContent=msg;e.hidden=false}}
function busy(on){app.querySelectorAll("button,input").forEach(function(x){x.disabled=on})}
function friendly(err){
  var m=String(err&&err.message||err||"");
  if(/invalid login credentials/i.test(m))return"That email and password don't match.";
  if(/email not confirmed/i.test(m))return"Confirm your email first. Check your inbox for the link.";
  if(/rate limit|too many/i.test(m))return"Too many tries. Wait a few minutes and try again.";
  if(/invalid totp|invalid code|code.*(expired|invalid)/i.test(m))return"That code didn't work. Codes change every 30 seconds, so try the newest one.";
  if(/password.*(weak|short|at least)/i.test(m))return"Choose a longer password (at least "+MIN_PW+" characters).";
  if(/invite/i.test(m))return m;
  if(/fetch|network/i.test(m))return"Can't reach the server. Check your connection and try again.";
  return"Something went wrong. Try again.";
}

/* ---------- configuration ---------- */
var cfg=window.RB_CONFIG||{};
function keyIsSecret(k){
  if(/^sb_secret_/.test(k))return true;
  var p=String(k).split(".");if(p.length!==3)return false;
  try{return JSON.parse(atob(p[1].replace(/-/g,"+").replace(/_/g,"/"))).role==="service_role"}catch(e){return false}
}
if(!cfg.supabaseUrl||!cfg.supabaseKey||!window.supabase){
  show('<h1>Not set up yet</h1><p class="muted">This portal is missing its Supabase settings. See docs/deploy.md.</p>');return;
}
if(keyIsSecret(cfg.supabaseKey)){
  show('<h1>Wrong key</h1><p>This page was given a secret key. It must only ever use the publishable key. Replace it and redeploy.</p>');return;
}
/* EcoBridge home page, for "Back to home" and "Request access". */
var HOME=/^https:\/\//.test(cfg.homeUrl||"")?cfg.homeUrl:"https://eco-bridge.cc-christophercontreras.workers.dev/";
var homeLink=$("#home");if(homeLink)homeLink.href=HOME;
var sb=window.supabase.createClient(cfg.supabaseUrl,cfg.supabaseKey,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});

/* ---------- state from the link that opened this page ---------- */
var hashType=new URLSearchParams(location.hash.slice(1)).get("type")||new URLSearchParams(location.search).get("type");
var needPassword=hashType==="invite"||hashType==="recovery";
var q=new URLSearchParams(location.search);
try{if(q.get("invite")){sessionStorage.setItem("rb-invite",q.get("invite"));q.delete("invite");history.replaceState(null,"",location.pathname+(q.toString()?"?"+q:"")+location.hash)}}catch(e){}
function pendingInvite(){try{return sessionStorage.getItem("rb-invite")||""}catch(e){return""}}
function clearInvite(){try{sessionStorage.removeItem("rb-invite")}catch(e){}}

/* ---------- routing: decides the one screen to show ---------- */
var routing=false, again=false;
function schedule(){setTimeout(route,0)}
async function route(){
  if(routing){again=true;return}routing=true;
  try{await step()}catch(e){show('<h1>Something went wrong</h1><p class="muted">'+esc(friendly(e))+'</p><button class="btn" id="retry">Try again</button>');$("#retry").onclick=schedule}
  finally{routing=false;if(again){again=false;schedule()}}
}
async function step(){
  var s=(await sb.auth.getSession()).data.session;
  signoutBtn.hidden=!s;
  if(!s)return viewSignIn();
  var aal=(await sb.auth.mfa.getAuthenticatorAssuranceLevel()).data||{};
  var f=(await sb.auth.mfa.listFactors()).data||{};
  var verified=(f.totp||[]).filter(function(x){return x.status==="verified"});
  if(aal.currentLevel!=="aal2"){
    if(verified.length)return viewVerify(verified[0].id);
    if(needPassword)return viewPassword(s.user.email);
    if(screen==="enroll")return; /* keep the QR code the person may be scanning */
    return viewEnroll(f.all||[]);
  }
  if(needPassword)return viewPassword(s.user.email);
  return viewHome(s.user.email);
}

/* ---------- screens ---------- */
/* "Client" or "Team" only changes the page's wording. It is never sent to sign-in and
   grants nothing: what each person can see comes from the database and my_access(). */
var signInAs="Client";
var EYE='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M1.5 12S5.5 4.5 12 4.5 22.5 12 22.5 12 18.5 19.5 12 19.5 1.5 12 1.5 12Z"/><circle cx="12" cy="12" r="3.2"/></svg>';
var EYE_OFF='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 4.5c6.5 0 10.5 7.5 10.5 7.5a17.6 17.6 0 0 1-3.3 4.2M6.6 6.6C3.4 8.6 1.5 12 1.5 12s4 7.5 10.5 7.5c1.6 0 3-.4 4.3-1"/><path d="M9.9 9.9a3.2 3.2 0 0 0 4.2 4.2"/></svg>';
var ARROW='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg>';
function viewSignIn(){
  show('<p class="eyebrow">Referral Bridge</p><h1>Welcome back</h1><p class="muted">Sign in to continue to your network.</p>'+
    '<div class="seg" role="group" aria-label="Signing in as">'+
      '<button type="button" data-as="Client" aria-pressed="'+(signInAs==="Client")+'">Client</button>'+
      '<button type="button" data-as="Team" aria-pressed="'+(signInAs==="Team")+'">Team</button></div>'+
    '<form id="f" novalidate><label for="em">Email</label><input id="em" type="email" autocomplete="username" placeholder="you@company.com" required>'+
    '<label for="pw">Password</label><div class="pw"><input id="pw" type="password" autocomplete="current-password" required>'+
    '<button type="button" class="eye" id="eye" aria-label="Show password" aria-pressed="false">'+EYE+'</button></div>'+
    '<div class="under"><button type="button" class="link" id="forgot">Forgot password?</button></div>'+
    '<div id="msg" hidden></div><button class="btn" type="submit" id="go">Sign in '+ARROW+'</button></form>'+
    '<div class="invite"><p>Need an invitation? <a class="link" id="request" href="'+esc(HOME)+'#contact">Request access</a></p></div>');
  app.querySelectorAll(".seg button").forEach(function(b){b.onclick=function(){
    signInAs=b.getAttribute("data-as");
    app.querySelectorAll(".seg button").forEach(function(x){x.setAttribute("aria-pressed",String(x===b))});
    $("#go").setAttribute("aria-label","Sign in as "+signInAs.toLowerCase());
  }});
  $("#eye").onclick=function(){var pw=$("#pw"),show=pw.type==="password";
    pw.type=show?"text":"password";this.setAttribute("aria-pressed",String(show));
    this.setAttribute("aria-label",show?"Hide password":"Show password");this.innerHTML=show?EYE_OFF:EYE;pw.focus()};
  $("#forgot").onclick=viewReset;
  $("#f").onsubmit=async function(e){e.preventDefault();
    var em=$("#em").value.trim(),pw=$("#pw").value;if(!em||!pw)return fail("Enter your email and password.");
    if(this.getAttribute("aria-busy")==="true")return;
    var go=$("#go");this.setAttribute("aria-busy","true");busy(true);go.textContent="Signing in\u2026";var r;
    try{r=await sb.auth.signInWithPassword({email:em,password:pw})}catch(x){r={error:x}}
    finally{this.setAttribute("aria-busy","false");busy(false);go.innerHTML="Sign in "+ARROW}
    if(r.error){$("#pw").value="";$("#pw").focus();return fail(friendly(r.error))}schedule()};
}
function viewReset(){
  show('<h1>Reset your password</h1><p class="muted">We\'ll email you a link to choose a new one.</p>'+
    '<form id="f" novalidate><label for="em">Email</label><input id="em" type="email" autocomplete="username" required>'+
    '<div id="msg" hidden></div><button class="btn" type="submit">Send reset link</button></form>'+
    '<div class="row"><button class="link" id="back">Back to sign in</button></div>');
  $("#back").onclick=viewSignIn;
  $("#f").onsubmit=async function(e){e.preventDefault();var em=$("#em").value.trim();if(!em)return fail("Enter your email.");
    busy(true);var r=await sb.auth.resetPasswordForEmail(em,{redirectTo:location.origin+location.pathname});busy(false);
    if(r.error&&/rate limit|too many/i.test(r.error.message||""))return fail(friendly(r.error));
    /* Same answer whether or not the account exists, so the page can't be used to check emails. */
    var m=$("#msg");m.className="ok";m.hidden=false;m.textContent="If that email has an account, a reset link is on its way."};
}
async function viewEnroll(all){
  for(var i=0;i<all.length;i++){var x=all[i];if(x.factor_type==="totp"&&x.status!=="verified")await sb.auth.mfa.unenroll({factorId:x.id})}
  var r=await sb.auth.mfa.enroll({factorType:"totp",friendlyName:"Authenticator app"});
  if(r.error)throw r.error;var d=r.data;
  show('<h1>Set up your authenticator app</h1><p class="muted">Every sign-in needs a 6-digit code from an app like Google Authenticator, Microsoft Authenticator, 1Password or Authy.</p>'+
    '<ol class="steps"><li>Open your authenticator app and add an account.</li><li>Scan this code, or type the setup key below.</li><li>Enter the 6-digit code the app shows.</li></ol>'+
    '<img class="qr" alt="QR code for your authenticator app" src="'+esc(d.totp.qr_code)+'">'+
    '<p class="small muted">Setup key</p><div class="secret">'+esc(d.totp.secret)+'</div>'+
    codeForm("Turn on"),"enroll");
  bindCode(d.id);
}
function viewVerify(factorId){
  show('<h1>Enter your code</h1><p class="muted">Open your authenticator app and enter the 6-digit code for Referral Bridge.</p>'+codeForm("Continue"));
  bindCode(factorId);
}
function codeForm(label){return'<form id="f" novalidate><label for="code">6-digit code</label><input id="code" class="code" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required>'+
  '<div id="msg" hidden></div><button class="btn" type="submit">'+esc(label)+'</button></form>'}
function bindCode(factorId){
  $("#f").onsubmit=async function(e){e.preventDefault();var c=$("#code").value.replace(/\D/g,"");
    if(c.length!==6)return fail("Enter all 6 digits.");
    busy(true);var r=await sb.auth.mfa.challengeAndVerify({factorId:factorId,code:c});busy(false);
    if(r.error)return fail(friendly(r.error));schedule()};
}
function viewPassword(email){
  show('<h1>Choose a password</h1><p class="muted">For '+esc(email)+'. Use at least '+MIN_PW+' characters. A short phrase you don\'t use anywhere else works well.</p>'+
    '<form id="f" novalidate><input type="email" autocomplete="username" value="'+esc(email)+'" hidden>'+
    '<label for="pw">New password</label><input id="pw" type="password" autocomplete="new-password" minlength="'+MIN_PW+'" required>'+
    '<label for="pw2">Type it again</label><input id="pw2" type="password" autocomplete="new-password" required>'+
    '<div id="msg" hidden></div><button class="btn" type="submit">Save password</button></form>');
  $("#f").onsubmit=async function(e){e.preventDefault();var a=$("#pw").value,b=$("#pw2").value;
    if(a.length<MIN_PW)return fail("Use at least "+MIN_PW+" characters.");if(a!==b)return fail("The two passwords don't match.");
    busy(true);var r=await sb.auth.updateUser({password:a});busy(false);
    if(r.error)return fail(friendly(r.error));
    needPassword=false;if(location.hash)history.replaceState(null,"",location.pathname+location.search);schedule()};
}
async function viewHome(email){
  var inv=pendingInvite();
  if(inv){var a=await sb.rpc("accept_invite",{code:inv});clearInvite();
    if(a.error)return viewInvite(friendly(a.error))}
  var r=await sb.rpc("my_access");if(r.error)throw r.error;var acc=r.data||{};
  var cos=acc.companies||[];
  if(!cos.length&&!acc.platform_owner)return viewInvite("");
  show('<h1>You\'re signed in</h1><p class="muted">'+esc(email)+(acc.platform_owner?' · <b>Platform owner</b>':'')+'</p>'+
    (cos.length?cos.map(function(c){return'<div class="co"><span>'+esc(c.name)+(c.scope==="assigned"?' <span class="small muted">· assigned records only</span>':'')+'</span><span class="tag">'+esc(ROLE[c.role]||c.role)+'</span></div>'}).join(""):'<p class="muted">No company memberships yet.</p>')+
    '<p class="small muted gap">Your CRM moves into this portal in the next step. Until then, keep using the current Referral Bridge app.</p>');
}
function viewInvite(err){
  show('<h1>Join your company</h1><p class="muted">Your account isn\'t part of a company yet. Enter the invite code you were sent.</p>'+
    '<form id="f" novalidate><label for="ic">Invite code</label><input id="ic" autocomplete="off" spellcheck="false" required>'+
    '<div id="msg" hidden></div><button class="btn" type="submit">Join</button></form>');
  if(err)fail(err);
  $("#f").onsubmit=async function(e){e.preventDefault();var c=$("#ic").value.trim();if(!c)return fail("Enter the code.");
    busy(true);var r=await sb.rpc("accept_invite",{code:c});busy(false);
    if(r.error)return fail(friendly(r.error));schedule()};
}

signoutBtn.onclick=async function(){signoutBtn.disabled=true;await sb.auth.signOut();signoutBtn.disabled=false;needPassword=false;schedule()};
/* Re-route only when sign-in state really changes; token refreshes must not restart MFA setup. */
var ROUTE_ON={INITIAL_SESSION:1,SIGNED_IN:1,SIGNED_OUT:1,PASSWORD_RECOVERY:1};
sb.auth.onAuthStateChange(function(ev){if(ev==="PASSWORD_RECOVERY")needPassword=true;if(ROUTE_ON[ev])schedule()});
})();

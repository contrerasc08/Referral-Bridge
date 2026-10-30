"""Browser tests for the sign-in portal (web/).

Serves web/ locally and swaps the Supabase client for a mock, so no network or real
project is needed. Checks sign-in, authenticator-app setup and verification, password
setup from an invite or reset link, invite codes, key safety checks, the page's
security policy, phone layout, and the CRM inside the portal: it loads only this
company's records, saves to the right table and columns, undoes failed saves, follows
live changes, and keeps demo data on the device.
Usage: python3 tests/test_portal.py   (exits 1 if any check fails)
Set RB_CHROMIUM to a Chromium binary to use one that's already installed.
"""
import asyncio, functools, http.server, json, os, pathlib, subprocess, sys, threading
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
subprocess.run(["node", str(ROOT / "scripts" / "build-crm.mjs")], check=True)
PUB = {"supabaseUrl": "https://demo.supabase.co", "supabaseKey": "sb_publishable_test"}

# A stand-in for supabase-js with just the calls the portal makes.
MOCK = r"""
window.__S = Object.assign({session:null, aal:"aal1", factors:[], companies:[], owner:false, calls:[], db:{}, deny:[], rt:{}}, window.__INIT||{});
const S = window.__S, subs = [];
const ok = d => ({data:d, error:null}), bad = m => ({data:null, error:{message:m}});
window.supabase = {createClient:(url,key,opt)=>{ S.calls.push(["create",url,key]); return {
  auth:{
    getSession: async()=>ok({session:S.session}),
    onAuthStateChange: cb => { subs.push(cb); window.__fire = ev => subs.forEach(f=>f(ev,S.session)); setTimeout(()=>cb("INITIAL_SESSION",S.session),0); return {data:{subscription:{unsubscribe(){}}}} },
    signInWithPassword: async({email,password})=>{ S.calls.push(["signin",email]);
      if(password!=="correct horse battery") return bad("Invalid login credentials");
      S.session={user:{email, id:"u1"}}; return ok({session:S.session}) },
    signOut: async()=>{ S.session=null; S.aal="aal1"; return ok({}) },
    resetPasswordForEmail: async(email,o)=>{ S.calls.push(["reset",email,o.redirectTo]); return ok({}) },
    updateUser: async({password})=>{ S.calls.push(["password",password]); return ok({user:S.session.user}) },
    mfa:{
      getAuthenticatorAssuranceLevel: async()=>ok({currentLevel:S.aal, nextLevel:S.factors.some(f=>f.status==="verified")?"aal2":"aal1"}),
      listFactors: async()=>ok({all:S.factors, totp:S.factors.filter(f=>f.status==="verified")}),
      unenroll: async({factorId})=>{ S.calls.push(["unenroll",factorId]); S.factors=S.factors.filter(f=>f.id!==factorId); return ok({}) },
      enroll: async()=>{ const f={id:"f"+(S.factors.length+1),factor_type:"totp",status:"unverified"}; S.factors.push(f);
        return ok({id:f.id, totp:{qr_code:"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'/>", secret:"JBSWY3DPEHPK3PXP"}}) },
      challengeAndVerify: async({factorId,code})=>{ S.calls.push(["verify",factorId,code]);
        if(code!=="123456") return bad("Invalid TOTP code entered");
        S.factors.forEach(f=>{ if(f.id===factorId) f.status="verified" }); S.aal="aal2"; return ok({}) }
    }},
  from: t => query(t),
  channel: name => { const ch = {on(type,f,cb){ (S.rt[f.table]=S.rt[f.table]||[]).push([f,cb]); return ch },
    subscribe(cb){ S.subscribed=(S.subscribed||0)+1; setTimeout(()=>cb("SUBSCRIBED"),0); return ch }}; return ch },
  rpc: async(name,args)=>{ S.calls.push(["rpc",name,args&&args.code]);
    if(name==="my_access") return S.aal!=="aal2" ? bad("mfa required") : ok({user_id:"u1", mfa:true, platform_owner:S.owner, companies:S.companies});
    if(name==="accept_invite"){ if(args.code!=="GOOD-CODE") return bad("This invite is invalid or expired");
      S.companies=[{company_id:"c1",name:"Referral Bridge",role:"employee",scope:"all"}]; return ok("c1") } }
}}};
"""

# A stand-in for the database tables and live updates the CRM uses.
MOCK += r"""
const copy = o => JSON.parse(JSON.stringify(o));
function query(t){ const st={t, f:[], op:"select", body:null, from:0, to:1e9};
  const b={ select(){ return b }, eq(c,v){ st.f.push([c,v]); return b }, order(){ return b }, range(a,z){ st.from=a; st.to=z; return b },
    update(o){ st.op="update"; st.body=o; return b }, insert(o){ st.op="insert"; st.body=o; return b }, delete(){ st.op="delete"; return b },
    then(res,rej){ return new Promise(r=>setTimeout(r,5)).then(()=>run(st)).then(res,rej) } };
  return b }
function run(st){ S.calls.push(["db",st.op,st.t,st.f.map(x=>x.join("=")).join("&")]);
  const rows=(S.db[st.t]=S.db[st.t]||[]), m=r=>st.f.every(([c,v])=>r[c]===v);
  if(st.op!=="select" && S.deny.includes(st.t)) return bad("new row violates row-level security policy");
  if(st.op==="select") return ok(rows.filter(m).slice(st.from, st.to+1).map(r=>({id:r.id, data:copy(r.data)})));
  if(st.op==="insert"){ if(rows.some(r=>r.id===st.body.id && r.company_id===st.body.company_id)) return {data:null, error:{code:"23505", message:"duplicate key"}};
    rows.push(copy(st.body)); return ok(null) }
  if(st.op==="update"){ const hit=rows.filter(m); hit.forEach(r=>Object.assign(r,copy(st.body))); return ok(hit.map(r=>({id:r.id}))) }
  if(st.op==="delete"){ const hit=rows.filter(m); S.db[st.t]=rows.filter(r=>!m(r)); return ok(hit.map(r=>({id:r.id}))) } }
window.__rt = (t,p) => (S.rt[t]||[]).forEach(([f,cb])=>cb(p));
"""

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok))); print(("PASS " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))

def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=str(WEB))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

async def page(br, base, cfg=PUB, init=None, path="/", width=1280):
    pg = await br.new_page(viewport={"width": width, "height": 900})
    errs, csp = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: csp.append(m.text) if "Content Security Policy" in m.text else None)
    vendor = "window.__INIT=" + json.dumps(init or {}) + ";(function(){" + MOCK + "})();"
    await pg.route("**/vendor/*.js", lambda r: r.fulfill(status=200, content_type="text/javascript", body=vendor))
    await pg.route("**/config.js", lambda r: r.fulfill(status=200, content_type="text/javascript",
        body=("window.RB_CONFIG=" + json.dumps(cfg) + ";") if cfg is not None else ""))
    await pg.goto(base + path); await pg.wait_for_timeout(150)
    return pg, errs, csp

async def crm(pg):
    await pg.wait_for_selector("#view", state="attached", timeout=5000); await pg.wait_for_timeout(200)
async def h1(pg): return (await pg.inner_text("#app h1")).strip()
async def submit(pg): await pg.click("#app button[type=submit]"); await pg.wait_for_timeout(120)
async def msg(pg): return (await pg.inner_text("#msg")).strip() if await pg.locator("#msg:visible").count() else ""

async def main():
  srv = serve(); base = f"http://127.0.0.1:{srv.server_address[1]}"
  async with async_playwright() as p:
    exe = os.environ.get("RB_CHROMIUM")
    br = await (p.chromium.launch(executable_path=exe) if exe else p.chromium.launch())

    # 1. New account: sign in, set up the authenticator app, join with an invite code
    pg, errs, csp = await page(br, base)
    check("signed out shows sign in", await h1(pg) == "Sign in")
    check("sign out button hidden when signed out", not await pg.is_visible("#signout"))
    await pg.fill("#em", "owner@example.com"); await pg.fill("#pw", "wrong"); await submit(pg)
    check("wrong password says so", await msg(pg) == "That email and password don't match.", await msg(pg))
    await pg.fill("#pw", "correct horse battery"); await submit(pg)
    check("no MFA yet goes to authenticator setup", await h1(pg) == "Set up your authenticator app")
    check("setup shows QR code and setup key", await pg.locator("img.qr").count() == 1 and "JBSWY3DPEHPK3PXP" in await pg.inner_text(".secret"))
    await pg.fill("#code", "12345"); await submit(pg)
    check("short code is refused", "6 digits" in await msg(pg))
    await pg.fill("#code", "000000"); await submit(pg)
    check("wrong code says so", "didn't work" in await msg(pg), await msg(pg))
    await pg.fill("#code", "123456"); await submit(pg)
    check("no company yet asks for an invite code", await h1(pg) == "Join your company")
    await pg.fill("#ic", "BAD"); await submit(pg)
    check("bad invite code says so", "invalid or expired" in await msg(pg), await msg(pg))
    await pg.fill("#ic", "GOOD-CODE"); await submit(pg)
    await crm(pg)
    check("good invite code opens the CRM", await pg.locator("#view").count() == 1 and await pg.locator("#app").count() == 0)
    check("CRM says it's synced to the account", await pg.inner_text("#sync") == "Synced to your account")
    check("a new company starts empty, nothing invented", await pg.evaluate("S.biz.length+S.coi.length+S.match.length") == 0
          and not await pg.is_visible("#demobar"))
    await pg.click("[data-act=menu]"); await pg.wait_for_timeout(100)
    t = await pg.inner_text("#sheetBody")
    check("menu shows the account, role and company", "owner@example.com" in t and "Employee, Referral Bridge" in t, t)
    await pg.click("[data-act=signout]"); await pg.wait_for_load_state(); await pg.wait_for_timeout(250)
    check("sign out returns to sign in", await h1(pg) == "Sign in")
    check("no page errors (new account)", not errs, errs)
    check("no security policy violations", not csp, csp)
    await pg.close()

    # 2. Returning user with MFA: a stale unfinished setup is cleared, the code is asked every sign-in
    init = {"factors": [{"id": "fv", "factor_type": "totp", "status": "verified"}],
            "companies": [{"company_id": "c1", "name": "Referral Bridge", "role": "company_admin", "scope": "all"}], "owner": True}
    pg, errs, _ = await page(br, base, init=init)
    await pg.fill("#em", "owner@example.com"); await pg.fill("#pw", "correct horse battery"); await submit(pg)
    check("returning user is asked for a code", await h1(pg) == "Enter your code")
    await pg.fill("#code", "123456"); await submit(pg)
    await crm(pg)
    await pg.click("[data-act=menu]"); await pg.wait_for_timeout(100)
    t = await pg.inner_text("#sheetBody")
    check("owner sees Platform owner and Company admin", "Platform owner" in t and "Company admin" in t, t)
    check("no page errors (returning user)", not errs, errs)
    await pg.close()

    init = {"session": {"user": {"email": "x@example.com"}}, "factors": [{"id": "old", "factor_type": "totp", "status": "unverified"}]}
    pg, errs, _ = await page(br, base, init=init)
    calls = await pg.evaluate("__S.calls")
    check("unfinished setup is cleared before a new one", ["unenroll", "old"] in calls, calls)
    check("setup is started only once per visit", sum(1 for c in calls if c[0] == "unenroll") == 1, calls)
    await pg.evaluate("__S.calls.length=0")
    for ev in ["TOKEN_REFRESHED", "SIGNED_IN"]:
        await pg.evaluate("ev=>window.__fire(ev)", ev); await pg.wait_for_timeout(100)
    check("token refresh doesn't replace the QR code", not any(c[0] == "unenroll" for c in await pg.evaluate("__S.calls")) and await h1(pg) == "Set up your authenticator app")
    await pg.close()

    # 3. Invite email link: choose a password first, then set up MFA
    init = {"session": {"user": {"email": "new@example.com"}}}
    pg, errs, _ = await page(br, base, init=init, path="/#access_token=x&type=invite")
    check("invite link asks for a password", await h1(pg) == "Choose a password")
    await pg.fill("#pw", "short"); await pg.fill("#pw2", "short"); await submit(pg)
    check("short password refused", "at least 12" in await msg(pg), await msg(pg))
    await pg.fill("#pw", "a long enough phrase"); await pg.fill("#pw2", "a different phrase!"); await submit(pg)
    check("mismatched passwords refused", "don't match" in await msg(pg))
    await pg.fill("#pw2", "a long enough phrase"); await submit(pg)
    check("after password, MFA setup", await h1(pg) == "Set up your authenticator app")
    check("token removed from the address bar", "access_token" not in pg.url, pg.url)
    await pg.close()

    # 4. Reset link for an MFA user: code first, then new password
    init = {"session": {"user": {"email": "owner@example.com"}}, "factors": [{"id": "fv", "factor_type": "totp", "status": "verified"}]}
    pg, errs, _ = await page(br, base, init=init, path="/#access_token=x&type=recovery")
    check("reset link with MFA asks for code first", await h1(pg) == "Enter your code")
    await pg.fill("#code", "123456"); await submit(pg)
    check("then asks for the new password", await h1(pg) == "Choose a password")
    await pg.close()

    # 5. Forgot password gives the same answer for any email
    pg, errs, _ = await page(br, base)
    await pg.click("#forgot"); await pg.fill("#em", "someone@example.com"); await submit(pg)
    calls = await pg.evaluate("__S.calls")
    check("reset sends link back to this page", any(c[0] == "reset" and c[2].startswith(base) for c in calls), calls)
    check("reset reply doesn't reveal if the account exists", await msg(pg) == "If that email has an account, a reset link is on its way.")
    await pg.close()

    # 6. Invite link with a code: kept through sign-in, applied after MFA, removed from the URL
    init = {"factors": [{"id": "fv", "factor_type": "totp", "status": "verified"}]}
    pg, errs, _ = await page(br, base, init=init, path="/?invite=GOOD-CODE")
    check("invite code removed from the address bar", "GOOD-CODE" not in pg.url, pg.url)
    await pg.fill("#em", "new@example.com"); await pg.fill("#pw", "correct horse battery"); await submit(pg)
    await pg.fill("#code", "123456"); await submit(pg)
    await crm(pg)
    check("invite applied automatically after sign-in", ["rpc", "accept_invite", "GOOD-CODE"] in await pg.evaluate("__S.calls")
          and await pg.locator("#view").count() == 1)
    await pg.close()

    # 7. Key safety
    pg, errs, _ = await page(br, base, cfg={"supabaseUrl": "https://demo.supabase.co", "supabaseKey": "sb_secret_abc"})
    check("secret key is refused", await h1(pg) == "Wrong key")
    check("secret key never reaches the client", await pg.evaluate("__S.calls.length") == 0)
    await pg.close()
    import base64
    jwt = "x." + base64.urlsafe_b64encode(json.dumps({"role": "service_role"}).encode()).decode().rstrip("=") + ".y"
    pg, errs, _ = await page(br, base, cfg={"supabaseUrl": "https://demo.supabase.co", "supabaseKey": jwt})
    check("service_role key is refused", await h1(pg) == "Wrong key")
    await pg.close()
    pg, errs, _ = await page(br, base, cfg=None)
    check("missing settings explained", await h1(pg) == "Not set up yet")
    await pg.close()

    # 9. The CRM in the portal: this company's records only, saved to the right table and columns
    biz = lambda i, co, name: {"id": i, "company_id": co, "owner_id": "u2", "data": {"name": name, "industry": "Retail", "state": "NJ"}}
    init = {"session": {"user": {"email": "owner@example.com", "id": "u1"}}, "aal": "aal2",
            "factors": [{"id": "fv", "factor_type": "totp", "status": "verified"}],
            "companies": [{"company_id": "c1", "name": "Referral Bridge", "role": "company_admin", "scope": "all"}], "owner": True,
            "db": {"businesses": [biz("b1", "c1", "Ours Bakery"), biz("b9", "c2", "Other Company Co")],
                   "signals": [{"id": f"s{i}", "company_id": "c1", "data": {"businessId": "b1", "type": "hiring", "eventDate": "2026-10-01", "provenance": "PROVIDER DATA", "confidence": 0.8, "provider": "test", "providerName": "Test"}} for i in range(2500)]}}
    pg, errs, csp = await page(br, base, init=init)
    await crm(pg); await pg.wait_for_timeout(300)
    names = await pg.evaluate("S.biz.map(b=>b.name)")
    check("loads this company's records", names == ["Ours Bakery"], names)
    calls = await pg.evaluate("__S.calls.filter(c=>c[0]==='db'&&c[1]==='select')")
    check("every load is limited to this company", calls and all("company_id=c1" in c[3] for c in calls), calls[:3])
    check("loads past 1,000 rows (2,500 signals)", await pg.evaluate("S.signal.length") == 2500)
    check("live updates opened once for all tables", await pg.evaluate("__S.subscribed") == 1)
    ok = await pg.evaluate("put('biz',{id:'bn',name:'New Florist',industry:'Retail'})")
    row = await pg.evaluate("__S.db.businesses.find(r=>r.id==='bn')")
    check("new record saved with company and owner", ok and row and row["company_id"] == "c1" and row["owner_id"] == "u1"
          and row["data"]["name"] == "New Florist" and "id" not in row["data"], row)
    ok = await pg.evaluate("put('biz',{...byId('biz','b1'),name:'Ours Bakery & Cafe'})")
    row = await pg.evaluate("__S.db.businesses.find(r=>r.id==='b1')")
    check("edit updates the record and keeps its owner", ok and row["data"]["name"] == "Ours Bakery & Cafe" and row["owner_id"] == "u2", row)
    ok = await pg.evaluate("put('match',{id:'m1',bizId:'b1',coiId:'c7',status:'Approved'})")
    row = await pg.evaluate("__S.db.matches.find(r=>r.id==='m1')")
    check("links filled in for bridges", ok and row["biz_id"] == "b1" and row["coi_id"] == "c7", row)
    ok = await pg.evaluate("put('req',{id:'r1',note:'x'})")
    check("camelCase collections map to their tables", ok and await pg.evaluate("!!__S.db.lead_requests.find(r=>r.id==='r1')"))
    await pg.evaluate("__S.deny=['businesses']")
    ok = await pg.evaluate("put('biz',{...byId('biz','b1'),name:'Should Not Stick'})")
    await pg.wait_for_timeout(100)
    check("refused save returns false and is undone", ok is False and await pg.evaluate("byId('biz','b1').name") == "Ours Bakery & Cafe")
    check("refused save says so", "Couldn't save" in await pg.inner_text("#toast"))
    ok = await pg.evaluate("put('biz',{id:'bz',name:'Refused New'})")
    check("refused new record disappears", ok is False and not await pg.evaluate("!!byId('biz','bz')"))
    await pg.evaluate("__S.deny=[]")
    ok = await pg.evaluate("del('biz','bn')")
    check("delete removes the row", ok and not await pg.evaluate("!!__S.db.businesses.find(r=>r.id==='bn')"))
    await pg.evaluate("""__rt('businesses',{eventType:'INSERT',new:{id:'b5',company_id:'c1',data:{name:'Added By Teammate'}}})""")
    await pg.wait_for_timeout(50)
    check("a teammate's new record appears live", await pg.evaluate("!!byId('biz','b5')"))
    await pg.evaluate("""__rt('businesses',{eventType:'INSERT',new:{id:'b6',company_id:'c2',data:{name:'Wrong Company'}}})""")
    check("another company's change is ignored", not await pg.evaluate("!!byId('biz','b6')"))
    await pg.evaluate("""__rt('businesses',{eventType:'DELETE',old:{id:'b5',company_id:'c1'}})""")
    await pg.wait_for_timeout(50)
    check("a teammate's delete disappears live", not await pg.evaluate("!!byId('biz','b5')"))
    check("nothing saved on the device", await pg.evaluate("localStorage.getItem('rb-data')") is None)
    await pg.click("#sidenav [data-sub=biz]"); await pg.wait_for_timeout(150)
    check("records show on screen", "Ours Bakery" in await pg.inner_text("#view"))
    check("no page errors (CRM)", not errs, errs)
    check("no security policy violations (CRM)", not csp, csp[:3])
    check("CRM font is served from this site", await pg.evaluate("document.fonts.check('16px Figtree')"))

    # demo mode stays on the device and is labeled
    await pg.click("[data-act=menu]"); await pg.wait_for_timeout(100)
    await pg.click("[data-act=demoon]"); await pg.wait_for_load_state(); await crm(pg)
    check("demo is labeled", await pg.is_visible("#demobar") and await pg.inner_text("#sync") == "Demo data")
    check("demo shows sample records", await pg.evaluate("S.biz.length") > 0)
    writes = await pg.evaluate("__S.calls.filter(c=>c[0]==='db'&&c[1]!=='select').length")
    await pg.evaluate("put('biz',{...S.biz[0],name:'Demo edit'})")
    check("demo edits never reach the database", await pg.evaluate("__S.calls.filter(c=>c[0]==='db'&&c[1]!=='select').length") == writes)
    await pg.click("[data-act=demoexit]"); await pg.wait_for_load_state(); await crm(pg)
    check("leaving demo goes back to the company's records", not await pg.is_visible("#demobar") and await pg.inner_text("#sync") == "Synced to your account")
    await pg.close()

    pg, errs, _ = await page(br, base, init=init, width=375)
    await crm(pg)
    check("CRM fits a phone, no sideways scroll", not await pg.evaluate("document.documentElement.scrollWidth>innerWidth"))
    await pg.screenshot(path="/tmp/rb-portal-crm-phone.png")
    await pg.close()

    owner_only = {**init, "companies": [], "db": {}}
    pg, errs, _ = await page(br, base, init=owner_only)
    await pg.wait_for_timeout(200)
    check("owner with no company sees a message, not an empty CRM", "aren't a member of any company" in await pg.inner_text("#app"))
    await pg.close()

    two = {**init, "companies": init["companies"] + [{"company_id": "c2", "name": "Second Co", "role": "employee", "scope": "all"}]}
    pg, errs, _ = await page(br, base, init=two)
    await crm(pg)
    await pg.click("[data-act=menu]"); await pg.wait_for_timeout(100)
    await pg.click("[data-company=c2]"); await pg.wait_for_load_state(); await crm(pg); await pg.wait_for_timeout(200)
    check("switching company loads that company's records", await pg.evaluate("S.biz.map(b=>b.name)") == ["Other Company Co"])
    await pg.close()

    # 8. Phone layout
    pg, errs, _ = await page(br, base, width=375)
    check("no sideways scroll on a phone", not await pg.evaluate("document.documentElement.scrollWidth>innerWidth"))
    await pg.screenshot(path="/tmp/rb-portal-phone.png")
    await pg.close()

    await br.close()
  srv.shutdown()
  failed = [r for r in results if not r[1]]
  print(f"\n{len(results)-len(failed)}/{len(results)} passed")
  sys.exit(1 if failed else 0)

asyncio.run(main())

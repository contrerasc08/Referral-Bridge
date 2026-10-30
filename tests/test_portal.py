"""Browser tests for the sign-in portal (web/).

Serves web/ locally and swaps the Supabase client for a mock, so no network or real
project is needed. Checks sign-in, authenticator-app setup and verification, password
setup from an invite or reset link, invite codes, key safety checks, the page's
security policy, and phone layout.
Usage: python3 tests/test_portal.py   (exits 1 if any check fails)
Set RB_CHROMIUM to a Chromium binary to use one that's already installed.
"""
import asyncio, functools, http.server, json, os, pathlib, sys, threading
from playwright.async_api import async_playwright

WEB = pathlib.Path(__file__).resolve().parent.parent / "web"
PUB = {"supabaseUrl": "https://demo.supabase.co", "supabaseKey": "sb_publishable_test"}

# A stand-in for supabase-js with just the calls the portal makes.
MOCK = r"""
window.__S = Object.assign({session:null, aal:"aal1", factors:[], companies:[], owner:false, calls:[]}, window.__INIT||{});
const S = window.__S, subs = [];
const ok = d => ({data:d, error:null}), bad = m => ({data:null, error:{message:m}});
window.supabase = {createClient:(url,key,opt)=>{ S.calls.push(["create",url,key]); return {
  auth:{
    getSession: async()=>ok({session:S.session}),
    onAuthStateChange: cb => { subs.push(cb); window.__fire = ev => subs.forEach(f=>f(ev,S.session)); setTimeout(()=>cb("INITIAL_SESSION",S.session),0); return {data:{subscription:{unsubscribe(){}}}} },
    signInWithPassword: async({email,password})=>{ S.calls.push(["signin",email]);
      if(password!=="correct horse battery") return bad("Invalid login credentials");
      S.session={user:{email}}; return ok({session:S.session}) },
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
  rpc: async(name,args)=>{ S.calls.push(["rpc",name,args&&args.code]);
    if(name==="my_access") return S.aal!=="aal2" ? bad("mfa required") : ok({user_id:"u1", mfa:true, platform_owner:S.owner, companies:S.companies});
    if(name==="accept_invite"){ if(args.code!=="GOOD-CODE") return bad("This invite is invalid or expired");
      S.companies=[{company_id:"c1",name:"Referral Bridge",role:"employee",scope:"all"}]; return ok("c1") } }
}}};
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
    vendor = "window.__INIT=" + json.dumps(init or {}) + ";" + MOCK
    await pg.route("**/vendor/*.js", lambda r: r.fulfill(status=200, content_type="text/javascript", body=vendor))
    await pg.route("**/config.js", lambda r: r.fulfill(status=200, content_type="text/javascript",
        body=("window.RB_CONFIG=" + json.dumps(cfg) + ";") if cfg is not None else ""))
    await pg.goto(base + path); await pg.wait_for_timeout(150)
    return pg, errs, csp

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
    check("good invite code lands on home", await h1(pg) == "You're signed in")
    check("home shows company and role", "Referral Bridge" in await pg.inner_text("#app") and "Employee" in await pg.inner_text("#app"))
    check("home doesn't present sample data as live", "Your CRM moves into this portal" in await pg.inner_text("#app"))
    check("sign out button shown when signed in", await pg.is_visible("#signout"))
    await pg.click("#signout"); await pg.wait_for_timeout(150)
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
    t = await pg.inner_text("#app")
    check("owner sees Platform owner and Company admin", "Platform owner" in t and "Company admin" in t)
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
    check("invite applied automatically after sign-in", await h1(pg) == "You're signed in" and "Referral Bridge" in await pg.inner_text("#app"))
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

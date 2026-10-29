"""Browser tests for the CRM-style navigation and task commands.

Runs src/index.html in headless Chromium against a mock artifact database and checks:
  1. wide screens get a left sidebar; phones keep the bottom tabs and section pills
  2. Prospect pipeline: a column per stage with counts, "Needs a next step" flags,
     moving a business by its menu and by drag and drop, and list view
  3. Outreach history: summary numbers, outcome chips, search, logging from the header, export
  4. Follow-up tasks: overdue / today / upcoming groups, Done, and businesses with no next step
  5. Appointments: upcoming discovery calls
Requires: pip install playwright && playwright install chromium
Usage:    python3 tests/test_crm_navigation.py   (exits 1 if any check fails)
Screenshots go to $RB_SHOTS, or a temp folder.
"""
import asyncio, json, sys, os, pathlib, tempfile, datetime
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = (ROOT / "src" / "index.html").as_uri()
OUT = os.environ.get("RB_SHOTS", tempfile.mkdtemp(prefix="rb-shots-"))
today = datetime.date.today()
D = lambda n: (today + datetime.timedelta(days=n)).isoformat()
T = lambda n: D(n) + "T12:00:00Z"
def biz(i, name, stage=None, **kw):
    b = {"id": i, "name": name, "industry": "Healthcare - therapy and rehab", "state": "NJ", "city": "Paramus", "createdAt": T(-20)}
    if stage: b["prospectStage"] = stage
    b.update(kw); return b
seed = {
 "businesses": [
   biz("b1", "Riverview Physical Therapy", "Prospect"),
   biz("b2", "Long Island PT", "Qualified", followUpAt=D(-2), followUpNote="Call back", contact="Ann Lee (Owner)", phone="555-0100"),
   biz("b3", "Central Jersey PT", "Contacted"),
   biz("b4", "Harbor Point Dental", "Engaged", followUpAt=D(0)),
   biz("b5", "Summit Builders", "Discovery call", followUpAt=D(5)),
   biz("b6", "Old Sample Co", "Prospect", sample=True)],
 "outreach": [
   {"id": "o1", "bizId": "b3", "channel": "call", "outcome": "none", "note": "Left with front desk", "at": T(-3)},
   {"id": "o2", "bizId": "b4", "channel": "email", "outcome": "interested", "contact": "Dr. Ruiz", "note": "Wants pricing", "at": T(-2)},
   {"id": "o3", "bizId": "b5", "channel": "call", "outcome": "booked", "at": T(-1), "apptAt": D(3), "apptTime": "10:00"},
   {"id": "o4", "bizId": "b2", "channel": "call", "outcome": "voicemail", "at": T(-4)}],
 "cois": [], "matches": [], "settings": [{"id": "providers", "revUnknown": True}]
}
MOCK = """
window.__FAIL=false; window.__store=%s; const subs={};
function snap(col){const docs=Object.values(window.__store[col]||{}).map(d=>({id:d.id,data:()=>{const c={...d};delete c.id;return c}}));(subs[col]||[]).forEach(cb=>cb({docs}))}
for(const k of Object.keys(window.__store)){const o={};for(const d of window.__store[k])o[d.id]=d;window.__store[k]=o}
const coll=col=>({limit:()=>coll(col),onSnapshot:(cb)=>{(subs[col]=subs[col]||[]).push(cb);setTimeout(()=>snap(col),0);return()=>{}},
  doc:id=>({set:async v=>{if(window.__FAIL)throw {code:"network"};(window.__store[col]=window.__store[col]||{})[id]={id,...v};snap(col)},
            delete:async()=>{if(window.__FAIL)throw {code:"network"};delete (window.__store[col]||{})[id];snap(col)}})});
window.claude={use:async n=>n==="db"?{collection:coll}:null};
""" % json.dumps(seed)
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); errs = []
    pg = await br.new_page(viewport={"width": 1280, "height": 900}); pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.add_init_script(MOCK); await pg.goto(APP); await pg.wait_for_timeout(600)
    E = pg.evaluate; vis = lambda sel: pg.locator(sel).first.is_visible()
    check("app connected to mock database", await E("db!==null && S.biz.length===6"))
    # 1. navigation
    check("wide screen shows the sidebar", await vis("#sidenav"))
    check("wide screen hides the bottom tabs", not await vis(".tabs"))
    nav = await pg.inner_text("#sidenav")
    check("sidebar lists the CRM sections", all(x in nav for x in ["Today", "Businesses", "Pipeline", "Touch log", "Next steps", "Discovery calls", "Bridges", "Specialists", "Scout"]))
    # 2. prospect pipeline
    await pg.click("#sidenav [data-sub=prospects]"); await pg.wait_for_timeout(150)
    check("sidebar marks the current page", await E("document.querySelector('#sidenav [data-sub=prospects]').getAttribute('aria-current')") == "page")
    cols = await E("[...document.querySelectorAll('[data-kcol]')].map(c=>c.dataset.kcol+':'+c.querySelector('.khead b').textContent)")
    check("board has a column per stage with counts", cols[:5] == ["Prospect:1", "Qualified:1", "Contacted:1", "Engaged:1", "Discovery call:1"] and len(cols) == 9, cols)
    check("sample records stay off the board", await pg.locator("[data-kid=b6]").count() == 0)
    check("worked prospect with no follow-up shows Needs a next step", await pg.locator("[data-kid=b3] .tag.due:has-text('Needs a next step')").count() == 1)
    check("prospect with a follow-up doesn't", await pg.locator("[data-kid=b5]:has-text('Needs a next step')").count() == 0)
    check("card shows contact info completeness", "2/4" in await pg.inner_text("[data-kid=b2]"))
    await pg.screenshot(path=f"{OUT}/crm-prospects-wide.png", full_page=True)
    await pg.click("[data-kid=b3] [data-lmenu]"); await pg.wait_for_timeout(100)
    menu = await pg.inner_text("#sheetBody")
    check("card menu offers the task commands", all(x in menu for x in ["Record a touch", "Set follow-up", "Open business page", "Move to stage"]))
    await pg.click("#sheetBody [data-pstage='b3|Engaged']"); await pg.wait_for_timeout(150)
    check("moving by menu saves the stage and closes the menu", await E("window.__store.businesses.b3.prospectStage") == "Engaged" and not await E("document.querySelector('#sheet').open"))
    check("moved card shows in its new column", await pg.locator("[data-kcol=Engaged] [data-kid=b3]").count() == 1)
    await pg.drag_and_drop("[data-kid=b1]", "[data-kcol=Qualified]"); await pg.wait_for_timeout(200)
    check("drag and drop moves a card to another stage", await E("window.__store.businesses.b1.prospectStage") == "Qualified")
    await pg.fill("#qpb", "harbor"); await pg.wait_for_timeout(100)
    check("pipeline search filters cards", await pg.locator("[data-kid]").count() == 1)
    await pg.fill("#qpb", ""); await pg.wait_for_timeout(100)
    await pg.click("[data-act=pblist]"); await pg.wait_for_timeout(100)
    check("list view shows a table", await pg.locator("#view table tbody tr").count() == 5)
    await pg.click("[data-act=pblist]")
    # 3. outreach history
    await pg.click("#sidenav [data-sub=outreach]"); await pg.wait_for_timeout(150)
    st = await pg.inner_text(".ostats")
    check("outreach summary: logged, with an outcome, interested or spoke", "4\ntouches" in st and "75%" in st and "2\nreal conversations" in st, st)
    check("outreach table lists every touch", await pg.locator("#ohBody tbody tr").count() == 4)
    check("outcome chips show counts", "1" in await pg.inner_text("[data-ohf=interested] small"))
    await pg.click("[data-ohf=interested]"); await pg.wait_for_timeout(100)
    check("outcome chip filters the table", await pg.locator("#ohBody tbody tr").count() == 1 and "Harbor Point" in await pg.inner_text("#ohBody"))
    await pg.click("[data-ohf=all]"); await pg.fill("#qoh", "front desk"); await pg.wait_for_timeout(100)
    check("search covers notes", await pg.locator("#ohBody tbody tr").count() == 1)
    await pg.fill("#qoh", "")
    await pg.screenshot(path=f"{OUT}/crm-outreach-wide.png", full_page=True)
    await pg.click("[data-act=logpick]"); await pg.wait_for_timeout(100)
    await pg.select_option("#pk_biz", "b1"); await pg.click("[data-act=pickbiz]"); await pg.wait_for_timeout(100)
    check("Log call or email opens the log form for the chosen business", "Riverview" in await pg.inner_text("#sheetBody") and await pg.locator("#lo_out").count() == 1)
    await pg.select_option("#lo_out", "spoke"); await pg.click("[data-saveout=b1]"); await pg.wait_for_timeout(200)
    check("logged touch is saved and listed", len(await E("Object.keys(window.__store.outreach)")) == 5 and await pg.locator("#ohBody tbody tr").count() == 5)
    await E("window.__toasts=[];new MutationObserver(()=>window.__toasts.push(document.querySelector('#toast').textContent)).observe(document.querySelector('#toast'),{childList:true,characterData:true,subtree:true})")
    async with pg.expect_download() as dl: await pg.click("[data-act=exportOut]")
    d = await dl.value; path = await d.path(); txt = open(path, encoding="utf-8-sig").read()
    check("Export downloads the outreach log as CSV", txt.startswith("Business,Industry,Channel,Outcome") and txt.count("\n") == 5, txt.splitlines()[:2])
    # 4. next steps: your list, suggestions, and working a task
    await pg.click("#sidenav [data-sub=followups]"); await pg.wait_for_timeout(150)
    lst = await pg.inner_text(".tlist")
    check("your list is grouped overdue, today, coming up in date order", all(x in lst.lower() for x in ["overdue", "today", "coming up"]) and lst.index("Long Island") < lst.index("Harbor Point") < lst.index("Summit"), lst[:200])
    check("suggestions panel renders", await pg.locator(".sugs").count() == 1)
    nn = await E("document.querySelector('details.sec2') ? document.querySelector('details.sec2').textContent : ''")
    check("needs-a-next-step list holds worked prospects without a date", "Needs a next step" in nn and "Central Jersey" in nn)
    await pg.click("[data-tdone='biz|b2']"); await pg.wait_for_timeout(150)
    check("ticking a follow-up clears it", await E("window.__store.businesses.b2.followUpAt") == "")
    await pg.click("[data-act=newtask]"); await pg.wait_for_timeout(100)
    await pg.fill("#tk_t", "Send Dr. Ruiz the CPA bio"); await pg.select_option("#tk_b", "b4"); await pg.click("[data-when='tk_d|1']")
    await pg.click("[data-act=savetask]"); await pg.wait_for_timeout(150)
    tasks = await E("Object.values(window.__store.tasks||{})")
    check("New task saves with a date picked by chip", len(tasks) == 1 and tasks[0]["dueAt"] == D(1) and tasks[0]["status"] == "open", tasks)
    tid = tasks[0]["id"] if tasks else ""
    await pg.click(f"[data-tfocus='task|{tid}'] >> nth=0"); await pg.wait_for_timeout(100)
    fx = await pg.inner_text("#sheetBody")
    check("opening a task pulls up the client, history and quick actions", "Harbor Point Dental" in fx and "Called them" in fx and "They emailed me" in fx and "Wants pricing" in fx, fx[:200])
    await pg.click("[data-qlog='b4|email|in']"); await pg.wait_for_timeout(100)
    check("quick log presets channel and direction", await E("document.querySelector('#sheetBody').dataset.ch") == "email" and await E("document.querySelector('#sheetBody').dataset.dir") == "in" and await pg.locator("#lo_done").is_checked())
    await pg.select_option("#lo_out", "spoke"); await pg.click("[data-when='lo_fu|7']"); await pg.click("[data-saveout=b4]"); await pg.wait_for_timeout(200)
    check("saving the touch records it, finishes the task and sets the next follow-up",
          await E(f"window.__store.tasks['{tid}'].status") == "done" and await E("Object.values(window.__store.outreach).some(o=>o.bizId==='b4'&&o.dir==='in'&&o.channel==='email')") and await E("window.__store.businesses.b4.followUpAt") == D(7))
    await pg.click("[data-tfocus='biz|b5'] >> nth=0"); await pg.wait_for_timeout(100)
    await pg.click("[data-tnext='14']"); await pg.wait_for_timeout(150)
    check("Done + next follow-up chip reschedules in one tap", await E("window.__store.businesses.b5.followUpAt") == D(14))
    await pg.screenshot(path=f"{OUT}/crm-followups-wide.png", full_page=True)
    # 5. appointments
    await pg.click("#sidenav [data-sub=appts]"); await pg.wait_for_timeout(150)
    check("appointments list upcoming discovery calls", "Summit Builders" in await pg.inner_text("#view") and "10:00" in await pg.inner_text("#view"))
    # Today's follow-up chip opens the task list
    await pg.click("#sidenav [data-sub=today]"); await pg.wait_for_timeout(100)
    await pg.click(".kpi[data-go=followups] >> nth=0"); await pg.wait_for_timeout(100)
    check("Today's follow-ups chip opens Follow-up tasks", await E("tab") == "followups")
    # Today home page
    await pg.click("#sidenav [data-sub=today]"); await pg.wait_for_timeout(150)
    hero = await pg.inner_text(".hero.today")
    check("Today leads with the date and week number", "week " in hero.lower() and str(today.day) in hero, hero.splitlines()[:3])
    await E("put('task',{id:'tt1',kind:'task',title:'Call the bank about Summit',status:'open',dueAt:localDay()}).then(render)"); await pg.wait_for_timeout(150)
    ag = await pg.inner_text(".agenda") if await pg.locator(".agenda").count() else ""
    check("Today's agenda includes tasks due today", "Call the bank about Summit" in ag, ag)
    check("upcoming discovery call shows under Coming up", "Summit Builders" in ag.lower().split("coming up")[-1].title() if "coming up" in ag.lower() else False, ag)
    tp = await pg.inner_text(".tps")
    check("talking points render", await pg.locator(".tps").count() == 1 and len(tp) > 10, tp[:120])
    check("industry briefing renders", await pg.locator(".brief").count() == 1)
    await pg.screenshot(path=f"{OUT}/crm-today-wide.png", full_page=True)
    # Find businesses: search-engine layout
    await pg.click("#sidenav [data-sub=leads]"); await pg.wait_for_timeout(150)
    check("Find businesses opens on a search bar, not a wall of links", await pg.locator("#leadForm").count() == 1 and await pg.locator(".res").count() == 0)
    await pg.select_option("#lwhat", "Healthcare - therapy and rehab"); await pg.select_option("#lstate", "NJ")
    await pg.click("#leadForm button[type=submit]"); await pg.wait_for_timeout(150)
    meta = await pg.inner_text(".rmeta")
    check("search shows ranked results with a summary line", "physical therapy clinics" in meta and "New Jersey" in meta and await pg.locator(".res").count() > 5, meta)
    g0 = await pg.inner_text(".rgrp >> nth=0"); check("matches already in your list come first", "already in your list" in g0.lower() and (await pg.locator(".res").first.inner_text()).startswith(("Riverview", "Long Island", "Central Jersey")))
    await pg.fill("#lq", "now open"); await pg.press("#lq", "Enter"); await pg.wait_for_timeout(150)
    hrefs = await E("[...document.querySelectorAll('.res a.rt')].map(a=>a.href)")
    check("web results carry the keywords", any("now%20open" in h or "now+open" in h for h in hrefs[:8]))
    await pg.click("[data-rtab=off]"); await pg.wait_for_timeout(100)
    check("Official records tab shows only official sources", "NJ license verification" in await pg.inner_text("#view .rmain") and "Across the web" not in await pg.inner_text("#view .rmain"))
    await pg.screenshot(path=f"{OUT}/crm-find-wide.png", full_page=True)
    # phone layout
    ph = await br.new_page(viewport={"width": 390, "height": 844}); ph.on("pageerror", lambda e: errs.append(str(e)))
    await ph.add_init_script(MOCK); await ph.goto(APP); await ph.wait_for_timeout(500)
    check("phone hides the sidebar and keeps bottom tabs", not await ph.locator("#sidenav").is_visible() and await ph.locator(".tabs").is_visible())
    pills = await ph.inner_text("#view .subnav")
    check("phone Today pills include the CRM pages", all(x in pills for x in ["Pipeline", "Next steps", "Discovery calls", "Touch log"]), pills)
    for sub in ["prospects", "outreach", "followups", "appts"]:
        await ph.click(f"#view [data-sub={sub}]"); await ph.wait_for_timeout(150)
        check(f"no horizontal page scroll at 390px on {sub}", await ph.evaluate("document.documentElement.scrollWidth") <= 390)
        await ph.screenshot(path=f"{OUT}/crm-{sub}-phone.png", full_page=True)
    dk = await br.new_page(viewport={"width": 1280, "height": 900}, color_scheme="dark"); dk.on("pageerror", lambda e: errs.append(str(e)))
    await dk.add_init_script(MOCK); await dk.goto(APP); await dk.wait_for_timeout(500)
    await dk.click("#sidenav [data-sub=prospects]"); await dk.wait_for_timeout(150); await dk.screenshot(path=f"{OUT}/crm-prospects-dark.png", full_page=True)
    check("no JavaScript errors", not errs, errs)
    print(f"\n{sum(r[1] for r in results)}/{len(results)} passed  (screenshots: {OUT})")
    if not all(r[1] for r in results): sys.exit(1)
asyncio.run(main())

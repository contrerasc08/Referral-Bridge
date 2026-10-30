"""Browser tests: a failed save never shows a success message.

Runs src/index.html in headless Chromium against a mock artifact database that can be
forced to fail (window.__FAIL). For each action it checks that, when the database
refuses the write:
  1. the message on screen is the failure message, not the success message
  2. the stored data is unchanged
It also checks that the same actions still show their success message when the save works.
Requires: pip install playwright && playwright install chromium
Usage:    python3 tests/test_save_failures.py   (exits 1 if any check fails)
Set RB_CHROMIUM to a Chromium binary to use one that's already installed.
"""
import asyncio, json, os, pathlib, sys
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = (ROOT / "src" / "index.html").as_uri()
seed = {
 "businesses": [
   {"id":"b1","name":"Maple Dental Group","industry":"Healthcare - dental","state":"NJ","county":"Bergen","city":"Paramus","contact":"Dr. Ann Lee (Owner)",
    "possibleDupOf":"b2","followUpAt":"2026-11-02","contacts":[{"name":"Ann Lee","role":"Owner","provenance":"USER-ENTERED"}],"createdAt":"2026-10-01T12:00:00Z"},
   {"id":"b2","name":"Maple Dental","industry":"Healthcare - dental","state":"NJ","county":"Bergen","createdAt":"2026-10-01T12:00:00Z"}],
 "signals": [{"id":"s1","businessId":"b1","type":"succession","provider":"web-research","providerName":"Test","eventDate":"2026-10-20","detectedAt":"2026-10-20T12:00:00Z","evidence":"Owner plans to retire.","confidence":0.9,"provenance":"PROVIDER DATA","mock":False,"legacy":False}],
 "outreach": [{"id":"o1","bizId":"b1","channel":"call","outcome":"spoke","at":"2026-10-21T12:00:00Z"}],
 "cois": [{"id":"c1","name":"Ok Advisor","profession":"M&A advisor or business broker","state":"NJ","serviceArea":"NJ","healthcare":True,"specialties":"dental practice sales","bestStage":"Planning exit"}],
 "matches": [{"id":"m1","bizId":"b1","coiId":"c1","status":"Approved","score":70,"history":[]}],
 "drafts": [{"id":"d1","bizId":"b1","coiId":"c1","kind":"owner_email","subject":"Hi","body":"Hello","status":"new","createdAt":"2026-10-28T12:00:00Z"}],
 "settings": [{"id":"providers","revUnknown":True}, {"id":"targeting","gens":{"succession":True}}]
}
MOCK = """
window.__FAIL=false; window.__store=%s; const subs={};
function snap(col){const docs=Object.values(window.__store[col]||{}).map(d=>({id:d.id,data:()=>{const c={...d};delete c.id;return c}}));(subs[col]||[]).forEach(cb=>cb({docs}))}
for(const k of Object.keys(window.__store)){const o={};for(const d of window.__store[k])o[d.id]=d;window.__store[k]=o}
const coll=col=>({limit:()=>coll(col),onSnapshot:(cb)=>{(subs[col]=subs[col]||[]).push(cb);setTimeout(()=>snap(col),0);return()=>{}},
  doc:id=>({set:async v=>{if(window.__FAIL)throw {code:"network"};(window.__store[col]=window.__store[col]||{})[id]={id,...v};snap(col)},
            delete:async()=>{if(window.__FAIL)throw {code:"network"};delete (window.__store[col]||{})[id];snap(col)}})});
window.__snap=snap;
window.claude={use:async n=>n==="db"?{collection:coll}:null};
""" % json.dumps(seed)

# name, kind, setup, success message (or None to skip the success check).
# "click" adds a button with these data attributes to the page and clicks it.
# "change" adds an input inside the main view and fires its change event.
CASES = [
 ("Follow-up saved", "click", {"savefu":"b1"}, "Follow-up saved", "openSheet('<input id=fu_d value=2026-11-09><input id=fu_n value=Call>')"),
 ("Follow-up done", "click", {"clearfu":"b1"}, "Follow-up done", None),
 ("Stage change from the menu", "click", {"pstage":"b1|Qualified"}, "Stage: Qualified", None),
 ("Follow a business", "click", {"follow":"b1"}, "Following", None),
 ("Not a duplicate", "click", {"notdup":"b1"}, "Marked as a separate business", None),
 ("Skip research", "click", {"rskip":"b1"}, "Skipped", None),
 ("Remove a contact", "click", {"delcontact":"b1|0","confirm":"1"}, "Contact removed", None),
 ("Remove a signal", "click", {"delsig":"s1","confirm":"1"}, "Signal removed", None),
 ("Learning on or off", "click", {"learn":"1"}, "Learning", None),
 ("Climate focus", "click", {"climf":"off"}, "Climate no longer changes scores", None),
 ("Find a real contact", "click", {"findcontact":"b1"}, "Moved to the front", None),
 ("Lead generator on or off", "click", {"tggen":"succession"}, " is ", None),
 ("Dismiss a suggested bridge", "click", {"dismiss":"b2|c1"}, "Dismissed", None),
 ("Draft dismissed", "click", {"ddis":"d1"}, None, None),
 ("Draft marked sent", "click", {"dsent":"d1"}, "Logged as outreach", None),
 ("Match saved", "click", {"savematch":"m1"}, "Match saved", "openSheet('<div id=f_reason></div><input id=f_value value=5000><textarea id=f_mnotes>x</textarea>');$('#sheetBody').dataset.stage='Introduced'"),
 ("Delete a business", "click", {"del":"biz|b2","confirm":"1"}, "Business deleted", None),
 ("News on or off", "change", {"id":"news_on","type":"checkbox"}, "News", None),
 ("Daily limit", "change", {"id":"src_quota","value":"25"}, "Daily limit saved", None),
 ("Targeting keywords", "change", {"id":"tg_kw","value":"dental"}, "Targeting saved", None),
 ("Owner-run only list", "change", {"id":"tg_only","type":"checkbox"}, "Showing", None),
]

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))

async def run(pg, kind, attrs, setup):
    E = pg.evaluate
    await E("document.querySelectorAll('.__t').forEach(x=>x.remove()); const t=document.getElementById('toast'); t.textContent=''")
    if setup: await E(setup)
    if kind == "click":
        await E("""a=>{const b=document.createElement('button');b.className='__t';for(const [k,v] of Object.entries(a))b.dataset[k]=v;document.body.appendChild(b);b.click()}""", attrs)
    else:
        await E("""a=>{const i=document.createElement('input');i.className='__t';i.id=a.id;i.type=a.type||'text';if(a.value)i.value=a.value;if(a.type==='checkbox')i.checked=true;
                  document.getElementById('view').appendChild(i);i.dispatchEvent(new Event('change',{bubbles:true}))}""", attrs)
    await pg.wait_for_timeout(250)
    return await E("document.getElementById('toast').textContent")

async def main():
  async with async_playwright() as p:
    exe = os.environ.get("RB_CHROMIUM")
    br = await (p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()); errs = []
    pg = await br.new_page(viewport={"width": 1280, "height": 900}); pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.add_init_script(MOCK); await pg.goto(APP); await pg.wait_for_timeout(600)
    E = pg.evaluate
    check("app connected to mock database", await E("db!==null && S.biz.length===2"))
    for name, kind, attrs, ok_msg, setup in CASES:
        before = await E("JSON.stringify(window.__store)")
        await E("window.__FAIL=true")
        msg = await run(pg, kind, attrs, setup)
        await E("window.__FAIL=false")
        after = await E("JSON.stringify(window.__store)")
        check(f"{name}: failure shows the failure message", msg.startswith("Couldn't"), msg)
        check(f"{name}: failure leaves stored data unchanged", before == after)
    # the same actions still confirm a save that worked
    for name, kind, attrs, ok_msg, setup in CASES:
        if not ok_msg: continue
        if attrs.get("dsent"): await E("window.__store.drafts.d1.status='new'")
        msg = await run(pg, kind, attrs, setup)
        check(f"{name}: success shows its message", ok_msg in msg and not msg.startswith("Couldn't"), msg)
    # a partly failed delete says what didn't go
    await E("window.__store.businesses.b9={id:'b9',name:'Gone Co',industry:'Construction',state:'NJ'};window.__store.signals.s9={id:'s9',businessId:'b9',type:'succession',provider:'web-research',providerName:'Test',eventDate:'2026-10-20',detectedAt:'2026-10-20T12:00:00Z',evidence:'x',confidence:0.9,provenance:'PROVIDER DATA',mock:false,legacy:false};__snap('businesses');__snap('signals')")
    await pg.wait_for_timeout(100)
    await E("""(()=>{const orig=db.collection;db.collection=c=>{const x=orig(c);if(c!=='signals')return x;return{...x,doc:id=>({...x.doc(id),delete:async()=>{throw {code:'network'}}})}};window.__restore=()=>{db.collection=orig}})()""")
    msg = await run(pg, "click", {"del":"biz|b9","confirm":"1"}, None)
    await E("window.__restore()")
    check("delete with a failed related record says so", "Business deleted, but 1 related record couldn't be removed" in msg, msg)
    check("no page errors", not errs, errs)
    await br.close()
  failed = [r for r in results if not r[1]]
  print(f"\n{len(results)-len(failed)}/{len(results)} passed")
  sys.exit(1 if failed else 0)

asyncio.run(main())

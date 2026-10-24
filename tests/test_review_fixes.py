"""Browser tests for the PR #1 review fixes.

Runs src/index.html in headless Chromium against a mock artifact database that can be
forced to fail, and checks:
  1. failed saves and deletes restore the previous data
  2. flagged specialists are excluded from scoring, bridges and new approvals
  3. each bridge is scored against its own need
  4. learning counts only Closed and Rejected referrals
Requires: pip install playwright && playwright install chromium
Usage:    python3 tests/test_review_fixes.py   (exits 1 if any check fails)
Screenshots go to $RB_SHOTS, or a temp folder.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright
import os, pathlib, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = (ROOT / "src" / "index.html").as_uri()
OUT = os.environ.get("RB_SHOTS", tempfile.mkdtemp(prefix="rb-shots-"))
D = lambda n: f"2026-10-{22-n:02d}"
seed = {
 "businesses": [{"id":"b1","name":"Maple Dental Group","industry":"Healthcare - dental","state":"NJ","county":"Bergen","city":"Paramus","contact":"Dr. Ann Lee (Owner)","createdAt":"2026-10-01T12:00:00Z"}],
 "signals": [
   {"id":"s1","businessId":"b1","type":"succession","provider":"web-research","providerName":"Test","eventDate":D(3),"detectedAt":D(3)+"T12:00:00Z","evidence":"Owner plans to retire.","confidence":0.9,"provenance":"PROVIDER DATA","mock":False,"legacy":False},
   {"id":"s2","businessId":"b1","type":"expansion","provider":"web-watch","providerName":"Test2","eventDate":D(5),"detectedAt":D(5)+"T12:00:00Z","evidence":"Adding a second office.","confidence":0.85,"provenance":"PROVIDER DATA","mock":False,"legacy":False}],
 "cois": [
   {"id":"c1","name":"Ok Advisor","profession":"M&A advisor or business broker","state":"NJ","serviceArea":"NJ","healthcare":True,"specialties":"dental practice sales","bestStage":"Planning exit"},
   {"id":"c2","name":"Flagged Advisor","profession":"M&A advisor or business broker","state":"NJ","county":"Bergen","serviceArea":"Bergen, NJ","healthcare":True,"specialties":"dental practice sales","bestStage":"Planning exit","profile":{"vetting":{"status":"flag","note":"License lapsed in 2025."}}},
   {"id":"c3","name":"Bank Person","profession":"Banker","state":"NJ","serviceArea":"NJ","specialties":"dental, healthcare","bestStage":"Any stage"}],
 "matches": [], "settings": [{"id":"providers","revUnknown":True}]
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
results=[]
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ")+name+(" — "+str(detail) if detail else ""))
async def main():
  async with async_playwright() as p:
    b = await p.chromium.launch(); errs=[]
    pg = await b.new_page(viewport={"width":390,"height":844}); pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.add_init_script(MOCK)
    await pg.goto(APP); await pg.wait_for_timeout(600)
    E = pg.evaluate
    check("app connected to mock database", await E("db!==null && S.biz.length===1 && S.coi.length===3"))
    # 1. failed save/delete keep data
    await E("window.__FAIL=true")
    r = await E("put('biz',{...byId('biz','b1'),name:'CHANGED'})")
    check("failed edit returns false", r is False, r)
    check("failed edit keeps original name", await E("byId('biz','b1').name")=="Maple Dental Group")
    r = await E("put('biz',{id:'bnew',name:'New Co'})")
    check("failed new record is not left on screen", await E("!byId('biz','bnew')") and r is False)
    r = await E("del('biz','b1')")
    check("failed delete returns false and keeps record", r is False and await E("!!byId('biz','b1')"))
    check("failed delete keeps record in database", await E("!!window.__store.businesses.b1"))
    await E("window.__toasts=[];new MutationObserver(()=>window.__toasts.push(document.querySelector('#toast').textContent)).observe(document.querySelector('#toast'),{childList:true,characterData:true,subtree:true})")
    await E("importCSV(new File(['name,state\\nAcme Plumbing LLC,NJ\\nBeta Bakery,NJ\\n'],'x.csv'))"); await pg.wait_for_timeout(50)
    last = await E("window.__toasts.at(-1)")
    check("failed CSV import doesn't claim success", "0 of 2" in last and await E("S.biz.length")==1, last)
    await E("window.__FAIL=false")
    r = await E("put('biz',{...byId('biz','b1'),notes:'ok'})"); await pg.wait_for_timeout(50)
    check("successful save still works", r is True and await E("window.__store.businesses.b1.notes==='ok'"))
    r = await E("""(async()=>{const b=byId('biz','b1');window.__FAIL=true;const p1=put('biz',{...b,notes:'first'});window.__FAIL=false;const p2=put('biz',{...b,notes:'second'});return [await p1,await p2]})()"""); await pg.wait_for_timeout(50)
    check("a failed edit doesn't undo a newer saved edit", r==[False,True] and await E("byId('biz','b1').notes")=="second"==await E("window.__store.businesses.b1.notes"), r)
    # 2. flagged specialists
    check("flagged specialist scores 0", await E("score(byId('biz','b1'),byId('coi','c2')).score")==0)
    check("flagged specialist's reason explains why", "Specialist checker" in (await E("score(byId('biz','b1'),byId('coi','c2')).why[0]")))
    check("flagged specialist never appears in bridges", await E("bridgesFor(byId('biz','b1')).every(x=>x.c.id!=='c2')"))
    check("unflagged peer still bridges", await E("bridgesFor(byId('biz','b1')).some(x=>x.c.id==='c1')"), await E("bridgesFor(byId('biz','b1')).map(x=>x.need.id+'->'+x.c.id+':'+x.score)"))
    r = await E("approve('b1','c2',90)"); await pg.wait_for_timeout(50)
    check("approving a flagged specialist is blocked", r is False and await E("S.match.length===0 && Object.keys(window.__store.matches||{}).length===0"))
    check("block shows a message", "flagged" in (await E("document.querySelector('#toast').textContent")).lower())
    r = await E("approve('b1','c2',0,'Dismissed')")
    check("dismissing a flagged suggestion still allowed", r is True)
    await E("del('match',S.match[0].id)")
    r = await E("approve('b1','c1',70)"); await pg.wait_for_timeout(50)
    check("approving an unflagged specialist works", r is True and await E("S.match.some(m=>m.coiId==='c1'&&m.status==='Approved')"))
    # 3. need-specific bridge scores
    rows = await E("""(()=>{const b=byId('biz','b1');return bridgesFor(b).map(x=>({need:x.need.id,conf:x.need.conf,c:x.c.id,bridge:x.score,specific:score(b,x.c,x.need).score,generic:score(b,x.c).score}))})()""")
    check("each bridge score equals its need-specific score", all(r["bridge"]==r["specific"] for r in rows), rows)
    diff = await E("""(()=>{const b=byId('biz','b1'),c=byId('coi','c3');const ns=needsFor(b).filter(n=>n.profs.includes(c.profession));return ns.map(n=>({need:n.id,conf:n.conf,score:score(b,c,n).score}))})()""")
    check("banker gets a different score per need", len({d["score"] for d in diff})>1 or len(diff)<2, diff)
    check("specialist who doesn't serve a need scores 0 for it", await E("(()=>{const b=byId('biz','b1');const n=needsFor(b).find(x=>!x.profs.includes('Banker'));return n?score(b,byId('coi','c3'),n).score===0:true})()"))
    # 4. learning only from Closed/Rejected
    await E("""(async()=>{for(let i=0;i<12;i++)await put('match',{id:'L'+i,bizId:'b1',coiId:'c1',status:i%2?'Introduced':'Meeting',sigTypes:['succession'],history:[]})})()"""); await pg.wait_for_timeout(100)
    check("open intros (Introduced/Meeting) don't count for learning", await E("learnedWeights().dec")==0)
    await E("""(async()=>{for(let i=0;i<10;i++)await put('match',{id:'D'+i,bizId:'b1',coiId:'c1',status:i<6?'Closed':'Rejected',sigTypes:['succession'],history:[]})})()"""); await pg.wait_for_timeout(100)
    check("closed and rejected referrals count", await E("learnedWeights().dec")==10)
    check("learning turns on after 10 finished", await E("learnedWeights().on")==True)
    # UI smoke
    for t in ["today","people","pipeline","brain"]:
        await pg.click(f"[data-tab={t}]"); await pg.wait_for_timeout(150); await pg.screenshot(path=f"{OUT}/ui-{t}.png", full_page=True)
    await pg.click("[data-tab=people]"); await pg.click("#view [data-sub=coi]"); await pg.wait_for_timeout(150)
    check("specialist list shows Flagged tag", await pg.locator(".card.c:has-text('Flagged Advisor') .tag.due").count()==1)
    await pg.screenshot(path=f"{OUT}/ui-specialists.png", full_page=True)
    await pg.click("#view [data-sub=biz]"); await pg.click("[data-bizview=b1]"); await pg.wait_for_timeout(150)
    await pg.screenshot(path=f"{OUT}/ui-business.png", full_page=True)
    check("business page doesn't offer Flagged Advisor as a bridge", await pg.locator("#view [data-approve*='|c2|']").count()==0)
    check("demo bar hidden outside demo mode", await E("getComputedStyle(document.querySelector('#demobar')).display")=="none")
    check("no horizontal scroll at 390px", await E("document.documentElement.scrollWidth")<=390)
    dk = await b.new_page(viewport={"width":390,"height":844}, color_scheme="dark"); dk.on("pageerror", lambda e: errs.append(str(e)))
    await dk.add_init_script(MOCK); await dk.goto(APP); await dk.wait_for_timeout(500); await dk.screenshot(path=f"{OUT}/ui-dark-today.png", full_page=True)
    check("no JavaScript errors", not errs, errs)
    print(f"\n{sum(r[1] for r in results)}/{len(results)} passed  (screenshots: {OUT})")
    if not all(r[1] for r in results): sys.exit(1)
asyncio.run(main())

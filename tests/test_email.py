"""Browser tests for Email: choose contacts, write one message, send through Gmail.

Runs src/index.html in headless Chromium with a mock artifact database and a mock
Gmail connector (the page's `mcp` capability). Checks the safety rules (daily cap,
mailing address and unsubscribe link on every email, Do not email always skipped,
no health details), personalization, logging, failures, and the website sign-ups import.
Requires: pip install playwright && playwright install chromium
Usage:    python3 tests/test_email.py   (exits 1 if any check fails)
Set RB_CHROMIUM to a Chromium binary to use one that's already installed.
"""
import asyncio, json, os, pathlib, sys, tempfile
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = (ROOT / "src" / "index.html").as_uri()
seed = {
 "businesses": [
   {"id":"b1","name":"Maple Dental Group","industry":"Healthcare - dental","state":"NJ","city":"Paramus","contact":"Dr. Ann Lee (Owner)",
    "contacts":[{"name":"Dr. Ann Lee","role":"Owner","email":"ann@mapledental.test"}]},
   {"id":"b2","name":"Riverside Pediatrics","industry":"Healthcare - medical","state":"NY","city":"Yonkers","contact":"Raj Patel (Practice manager)","email":"raj@riverside.test"},
   {"id":"b3","name":"No Email Clinic","industry":"Healthcare - medical","state":"NY"},
   {"id":"b4","name":"Opted Out Ortho","industry":"Healthcare - dental","state":"NJ","email":"gone@optout.test","contact":"Sam Roe"},
   {"id":"b5","name":"Maple Dental Annex","industry":"Healthcare - dental","state":"NJ","email":"ANN@mapledental.test","contact":"Ann Lee"}],
 "cois": [{"id":"c1","name":"Priya Nair, CPA","firm":"Nair & Associates","profession":"CPA","email":"priya@nair.test","state":"NJ"}],
 "emailOptOuts": [{"id":"x1","email":"gone@optout.test","source":"Unsubscribe page","at":"2026-11-01T12:00:00Z"}],
 "settings": [{"id":"providers","revUnknown":True}]
}
MOCK = """
window.__store=%s; const subs={};
function snap(col){const docs=Object.values(window.__store[col]||{}).map(d=>({id:d.id,data:()=>{const c={...d};delete c.id;return c}}));(subs[col]||[]).forEach(cb=>cb({docs}))}
for(const k of Object.keys(window.__store)){const o={};for(const d of window.__store[k])o[d.id]=d;window.__store[k]=o}
const coll=col=>({limit:()=>coll(col),onSnapshot:(cb)=>{(subs[col]=subs[col]||[]).push(cb);setTimeout(()=>snap(col),0);return()=>{}},
  doc:id=>({set:async v=>{(window.__store[col]=window.__store[col]||{})[id]={id,...v};snap(col)},
            delete:async()=>{delete (window.__store[col]||{})[id];snap(col)}})});
window.__snap=snap; window.__calls=[]; window.__fail={}; window.__noMcp=%s;
const schema={type:"object",properties:{to:{type:"array",items:{type:"string"}},subject:{type:"string"},body:{type:"string"},html_body:{type:"string"}},required:["to","subject","body"]};
const mcp={listTools:async()=>({servers:[{server:"Gmail",authStatus:"connected",tools:[{name:"create_draft",description:""},{name:"send_message",description:""}]}]}),
  describeTool:async(s,t)=>({name:t,description:"",inputSchema:schema}),
  callTool:async(s,t,a)=>{const to=(a.to||[])[0];const f=window.__fail[to]||window.__fail["*"];if(f)throw {code:f,message:"refused "+to};window.__calls.push({tool:t,args:a});return{content:[],payload:{id:"m"+window.__calls.length}}}};
window.claude={use:async n=>n==="db"?{collection:coll}:n==="mcp"?(window.__noMcp?null:mcp):null};
"""

async def main():
    fails, passed = [], 0
    def check(name, ok, detail=""):
        nonlocal passed
        if ok: passed += 1
        else: fails.append(name + (": " + str(detail) if detail else ""))
    async with async_playwright() as p:
        exe = os.environ.get("RB_CHROMIUM")
        br = await (p.chromium.launch(executable_path=exe) if exe else p.chromium.launch())
        errs = []
        async def page_for(no_mcp=False, width=1280):
            pg = await br.new_page(viewport={"width":width,"height":900})
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.add_init_script(MOCK % (json.dumps(seed), "true" if no_mcp else "false"))
            await pg.goto(APP); await pg.wait_for_timeout(300)
            return pg
        async def toast(pg): return await pg.eval_on_selector("#toast", "e=>e.textContent")
        async def go_email(pg):
            await pg.click("#sidenav [data-sub='email']"); await pg.wait_for_timeout(250)

        pg = await page_for()
        await go_email(pg)
        check("Email page opens from the sidebar", await pg.is_visible("text=1. Who gets it"))
        check("Gmail shows as connected", "Gmail connected" in await pg.inner_text("#emSum"))
        rows = await pg.inner_text("#emList")
        check("Business with a contact email is listed", "ann@mapledental.test" in rows)
        check("Business without email is marked", "No email" in rows)
        check("Do not email is marked", "Do not email" in rows)
        check("Opted-out row can't be ticked", await pg.is_disabled("[data-emsel='biz|b4']"))
        check("No-email row can't be ticked", await pg.is_disabled("[data-emsel='biz|b3']"))

        # Nothing set up yet: Send explains what's missing and sends nothing
        await pg.check("[data-emsel='biz|b1']")
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(150)
        check("Send blocked without sender details", "Add your name" in await toast(pg), await toast(pg))
        check("Nothing sent when blocked", await pg.evaluate("window.__calls.length") == 0)

        # Sender details
        await pg.click("summary:has-text('Sender details')") if not await pg.is_visible("#ems_fromName") else None
        for k, v in [("fromName","Chris Rivera"),("fromEmail","me@chris.test"),("mailingAddress","PO Box 12, Fort Lee, NJ 07024")]:
            await pg.fill("#ems_"+k, v); await pg.dispatch_event("#ems_"+k, "change"); await pg.wait_for_timeout(80)
        st = await pg.evaluate("window.__store.settings.email")
        check("Sender details saved", st and st.get("mailingAddress","").startswith("PO Box"), st)

        # A test send is required before a blast
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(150)
        check("Blast needs a test first", "test to yourself" in await toast(pg), await toast(pg))
        await pg.click("[data-act='emTest']"); await pg.wait_for_timeout(400)
        calls = await pg.evaluate("window.__calls")
        check("Test goes to my own address", len(calls)==1 and calls[0]["args"]["to"]==["me@chris.test"], calls)
        check("Test uses the send tool", calls and calls[0]["tool"]=="send_message", calls)
        body = calls[0]["args"]["body"] if calls else ""
        check("Fill-ins replaced in test", "Hi Chris," in body and "{" not in body, body[:200])
        check("Plain style sends no HTML", calls and "html_body" not in calls[0]["args"], calls)
        check("Test isn't logged as a send", await pg.evaluate("Object.keys(window.__store.emailLog||{}).length") == 0)

        # Blast: b1 and b5 share an address, b4 is opted out
        await pg.evaluate("window.__calls=[]")
        await pg.check("[data-emsel='biz|b2']"); await pg.check("[data-emsel='biz|b5']")
        summary = await pg.inner_text("#emSum")
        check("Summary counts one per address", "Will get this email\n2" in summary.replace("\t","\n") or "Will get this email 2" in summary, summary)
        check("Duplicate address noted", "duplicate" in summary, summary)
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(3500)
        calls = await pg.evaluate("window.__calls")
        tos = sorted(c["args"]["to"][0].lower() for c in calls)
        check("Blast reaches each address once", tos == ["ann@mapledental.test","raj@riverside.test"], tos)
        ann = next((c["args"] for c in calls if c["args"]["to"][0].lower()=="ann@mapledental.test"), {})
        check("First name from 'Dr. Ann Lee'", ann.get("body","").startswith("Hi Ann,"), ann.get("body","")[:40])
        check("Practice filled in", "Maple Dental" in ann.get("body",""))
        check("Mailing address in every email", all("PO Box 12, Fort Lee" in c["args"]["body"] for c in calls))
        check("Personal unsubscribe link in every email", all("/unsubscribe?e="+c["args"]["to"][0].replace("@","%40") in c["args"]["body"] for c in calls), [c["args"]["body"][-160:] for c in calls])
        log = await pg.evaluate("Object.values(window.__store.emailLog||{})")
        check("Each send logged", len([l for l in log if l["status"]=="sent"])==2, log)
        out = await pg.evaluate("Object.values(window.__store.outreach||{})")
        check("Business sends recorded as email touches", len([o for o in out if o["channel"]=="email"])==2, out)
        check("Stage moves to Contacted", await pg.evaluate("stageOf(byId('biz','b2'))") == "Contacted")
        check("Sent contacts and duplicates are unselected", await pg.evaluate("EM.sel.size") == 0, await pg.evaluate("[...EM.sel]"))
        check("Sent today counter", "Sent today" in await pg.inner_text("#emSum") and await pg.evaluate("emSentToday()")==2)

        # Daily cap
        await pg.fill("#ems_dailyCap","3"); await pg.dispatch_event("#ems_dailyCap","change"); await pg.wait_for_timeout(100)
        await pg.evaluate("window.__calls=[]")
        await pg.click("[data-emwho='coi']"); await pg.check("[data-emsel='coi|c1']")
        await pg.click("[data-emwho='biz']"); await pg.evaluate("EM.sel.add('biz|b1')"); await pg.evaluate("emRefresh()")
        check("Cap note shows", "limit lets 1 go now" in await pg.inner_text("#emSum"), await pg.inner_text("#emSum"))
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(1200)
        check("Daily cap stops at the limit", await pg.evaluate("window.__calls.length") == 1)
        check("The rest stays selected for tomorrow", await pg.evaluate("EM.sel.size") == 1)
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(200)
        check("At the limit, Send says so", "today's limit" in await toast(pg), await toast(pg))
        await pg.fill("#ems_dailyCap","50"); await pg.dispatch_event("#ems_dailyCap","change"); await pg.wait_for_timeout(100)

        # Styled template, placeholders and health words
        await pg.click("[data-emtpl='update']"); await pg.wait_for_timeout(100)
        await pg.click("[data-emtpl='update']"); await pg.wait_for_timeout(100)
        check("Update template chosen", (await pg.input_value("#em_subj")).startswith("EcoBridge update"))
        await pg.click("[data-act='emTest']"); await pg.wait_for_timeout(150)
        check("Unfilled [brackets] block sending", "Replace [" in await toast(pg), await toast(pg))
        await pg.fill("#em_subj","EcoBridge update: Spring mixer")
        await pg.fill("#em_body","Hi {first name},\n\nJoin us on May 2 at the Fort Lee library. Details: https://example.com/mixer\n\n{my name}")
        await pg.dispatch_event("#em_body","input")
        prev = await pg.inner_html("#emPrev")
        check("Styled preview uses Ivory & Slate", "#f7f4ee" in prev and "EcoBridge" in prev)
        await pg.evaluate("window.__calls=[]")
        await pg.click("[data-act='emTest']"); await pg.wait_for_timeout(400)
        calls = await pg.evaluate("window.__calls")
        html = calls[0]["args"].get("html_body","") if calls else ""
        check("Styled email sends HTML", "#fffdf9" in html and "Unsubscribe" in html and "PO Box 12" in html, html[:120])
        check("Styled email keeps a plain-text version", calls and "To stop getting these emails" in calls[0]["args"]["body"])
        check("Links in styled email are clickable", 'href="https://example.com/mixer"' in html)
        await pg.fill("#em_body","Hi {first name}, your patient's diagnosis is ready."); await pg.dispatch_event("#em_body","input")
        await pg.click("[data-act='emTest']"); await pg.wait_for_timeout(150)
        check("Health details block sending", "patient or health" in await toast(pg), await toast(pg))
        await pg.fill("#em_body","Hi {firstname}"); await pg.dispatch_event("#em_body","input")
        await pg.click("[data-act='emTest']"); await pg.wait_for_timeout(150)
        check("Unknown fill-in blocks sending", "{firstname}" in await toast(pg), await toast(pg))

        # Failures: a refused email is logged and the run continues; no answer stops the run
        await pg.click("[data-emtpl='intro']"); await pg.click("[data-emtpl='intro']"); await pg.wait_for_timeout(100)
        await pg.click("[data-act='emTest']"); await pg.wait_for_timeout(400)
        await pg.evaluate("""()=>{window.__calls=[];window.__store.emailLog={};window.__snap('emailLog');
          window.__fail={'priya@nair.test':'tool_error'};EM.sel=new Set(['biz|b2','coi|c1','biz|b1']);emRefresh()}""")
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(4500)
        log = await pg.evaluate("Object.values(window.__store.emailLog||{})")
        check("Refused email logged as failed", any(l["status"]=="failed" and l["to"]=="priya@nair.test" for l in log), log)
        check("Run continues after one refusal", len([l for l in log if l["status"]=="sent"])==2, log)
        check("Failed contact stays selected", await pg.evaluate("EM.sel.has('coi|c1')"))
        await pg.evaluate("""()=>{window.__calls=[];window.__store.emailLog={};window.__snap('emailLog');
          window.__fail={'*':'server_unavailable'};EM.sel=new Set(['biz|b2','coi|c1']);emRefresh()}""")
        await pg.click("[data-act='emSend']"); await pg.wait_for_timeout(800)
        check("No answer from Gmail stops the run", await pg.evaluate("Object.values(window.__store.emailLog||{}).length") == 1)
        check("No answer warns to check Sent", "check your Gmail Sent folder" in await pg.inner_text("#emSum"))
        await pg.evaluate("window.__fail={}")

        # Do not email from a row
        await pg.click("[data-emwho='coi']"); await pg.wait_for_timeout(100)
        await pg.click("[data-emopt='priya@nair.test']"); await pg.click("[data-emopt='priya@nair.test']"); await pg.wait_for_timeout(200)
        opts = await pg.evaluate("Object.values(window.__store.emailOptOuts).map(o=>o.email)")
        check("Row button adds to Do not email", "priya@nair.test" in opts, opts)
        check("Opted-out contact unselected", not await pg.evaluate("EM.sel.has('coi|c1')"))
        await pg.click("summary:has-text('Do not email')")
        await pg.fill("#em_optadd","a@b.test, notanemail"); await pg.click("[data-act='emOptAdd']"); await pg.wait_for_timeout(200)
        check("Pasted addresses added", "a@b.test" in await pg.evaluate("Object.values(window.__store.emailOptOuts).map(o=>o.email)"))
        check("Bad pasted address reported", "didn't look like" in await toast(pg), await toast(pg))

        # Website sign-ups import
        csv = ("name,email,role,company,message,updates,unsubscribe,unsubscribe_email,_subject,_date\n"
               "Lena Ortiz,lena@ortiz.test,Practice owner,Ortiz Family Medicine,Hello,yes,,,,2026-11-06T06:09:00Z\n"
               "Ben Cho,ben@cho.test,Other,,Hi,,,,,2026-11-06T07:00:00Z\n"
               ",lena@ortiz.test,,,,yes,,,,\n"
               ",,,,,,yes,bye@leave.test,Unsubscribe request,\n")
        f = pathlib.Path(tempfile.gettempdir()) / "formspree-export.csv"; f.write_text(csv)
        await pg.set_input_files("#signupInput", str(f)); await pg.wait_for_timeout(300)
        sheet = await pg.inner_text("#sheetBody")
        check("Import preview counts", "will be added\n1" in sheet.replace("\t","\n") or "will be added 1" in sheet, sheet)
        await pg.click("[data-act='emImpOK']"); await pg.wait_for_timeout(300)
        subsc = await pg.evaluate("Object.values(window.__store.subscribers||{})")
        check("Ticked sign-up added once, tagged Website", [s["email"] for s in subsc]==["lena@ortiz.test"] and subsc[0]["tags"]==["Website"] and subsc[0]["consent"], subsc)
        check("Unticked sign-up not added by default", not any(s["email"]=="ben@cho.test" for s in subsc))
        check("Unsubscribe request goes to Do not email", "bye@leave.test" in await pg.evaluate("Object.values(window.__store.emailOptOuts).map(o=>o.email)"))
        check("Lands on Website sign-ups", await pg.evaluate("EM.who") == "sub" and "Ortiz Family Medicine" in await pg.inner_text("#emList"))
        await pg.set_input_files("#signupInput", str(f)); await pg.wait_for_timeout(300)
        check("Second import skips people already added", "Already on your list" in await pg.inner_text("#sheetBody"))
        await pg.check("#em_impall"); await pg.click("[data-act='emImpOK']"); await pg.wait_for_timeout(300)
        ben = await pg.evaluate("Object.values(window.__store.subscribers).find(s=>s.email==='ben@cho.test')")
        check("Unticked can be added on request, marked", ben and ben["consent"] is False, ben)
        check("Unticked shows a tag", "Didn't tick updates" in await pg.inner_text("#emList"))

        # Email these, from Businesses
        await pg.click("#sidenav [data-sub='biz']"); await pg.wait_for_timeout(150)
        check("Opted-out business tagged in list", "Do not email" in await pg.inner_text("#listBiz"))
        await pg.click("[data-emfrom='biz']"); await pg.wait_for_timeout(200)
        sel = await pg.evaluate("[...EM.sel].sort()")
        check("Email these selects emailable businesses", sel==["biz|b1","biz|b2","biz|b5"], sel)
        check("Email these opens Email", await pg.evaluate("tab") == "email")

        # Mail-merge download works without Gmail
        pg2 = await page_for(no_mcp=True)
        await go_email(pg2)
        check("Without Gmail, explains how to connect", "Sending needs this app open in claude.ai" in await pg2.inner_text("#emSum"))
        await pg2.evaluate("""()=>{put('settings',{id:'email',fromName:'Chris',mailingAddress:'PO Box 1',fromEmail:'me@x.test'});EM.sel=new Set(['biz|b1','biz|b4']);EM.mode='csv';emRefresh()}""")
        await pg2.wait_for_timeout(100)
        async with pg2.expect_download() as dl:
            await pg2.click("[data-act='emSend']")
        path = await (await dl.value).path(); text = pathlib.Path(path).read_text(encoding="utf-8-sig")
        check("Mail-merge file has filled-in rows", "ann@mapledental.test" in text and "Hi Ann," in text, text[:200])
        check("Mail-merge file leaves out Do not email", "gone@optout.test" not in text)
        await pg2.close()

        # Demo mode never sends
        pg3 = await page_for()
        await pg3.evaluate("localStorage.setItem('rb-mode','demo')"); await pg3.reload(); await pg3.wait_for_timeout(300)
        await go_email(pg3)
        await pg3.click("[data-act='emTest']"); await pg3.wait_for_timeout(150)
        check("Demo mode blocks sending", "Demo mode never sends" in await toast(pg3), await toast(pg3))
        await pg3.evaluate("localStorage.removeItem('rb-mode')"); await pg3.close()

        # Phone width
        pg4 = await page_for(width=390)
        await pg4.evaluate("tab='email';render()"); await pg4.wait_for_timeout(300)
        ow = await pg4.evaluate("document.documentElement.scrollWidth - innerWidth")
        check("No sideways scroll on a phone", ow <= 1, ow)
        shots = pathlib.Path(tempfile.mkdtemp(prefix="rb-email-"))
        await pg4.screenshot(path=str(shots/"email-phone.png"), full_page=True)
        await pg.evaluate("tab='email';EM.who='biz';render()"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(shots/"email-wide.png"), full_page=True)
        check("No page errors", not errs, errs)
        await br.close()
    total = passed + len(fails)
    print(f"{passed}/{total} passed  (screenshots: {shots})")
    for x in fails: print("FAIL", x)
    sys.exit(1 if fails else 0)

asyncio.run(main())

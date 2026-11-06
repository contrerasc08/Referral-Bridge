"""Browser tests for Company research (a RelPro-style sourced company profile).

Runs src/index.html in headless Chromium against a mock artifact database and checks:
  1. "Company research" is in the sidebar and opens the search form
  2. Building a profile saves a queued record and shows prefilled source links
  3. A researched profile pins key facts at the top, and its Overview shows merged fields with
     source chips, agreement badges, conflicts, Filings and Funding summaries and Favorite roles
  4. Preview shows key firmographics and the sources; Finance groups loans, liens and funding;
     Highlights shows industry codes and census tract; Sources is the single-source view
  4b. People tab: search, Favorite Roles filter, editing role groups, CSV export, adding contacts
  5. "Add what you found" merges pasted facts (via a mocked Claude) with the page as a new source
  6. "Save to my businesses" creates a business with contacts, profile sources and signals,
     then a second save updates it instead of making a duplicate
  7. Searching the same company again opens the existing profile
Requires: pip install playwright && playwright install chromium
Usage:    python3 tests/test_company_research.py   (exits 1 if any check fails)
"""
import asyncio, json, sys, os, pathlib, tempfile
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = (ROOT / "src" / "index.html").as_uri()
OUT = os.environ.get("RB_SHOTS", tempfile.mkdtemp(prefix="rb-shots-"))
researched = {
 "id": "p9", "name": "Acme Tooling", "city": "Erie", "state": "PA", "status": "done", "requestedAt": "2026-11-01T12:00:00Z",
 "researchedAt": "2026-11-02T12:00:00Z", "industryGroup": "Manufacturing", "summary": "Family-owned tool and die shop.",
 "sources": [
   {"id": "s1", "name": "PA business registry", "url": "https://file.dos.pa.gov/search/business", "type": "official", "found": True},
   {"id": "s2", "name": "Company website", "url": "https://acme.example", "type": "company", "found": True},
   {"id": "s3", "name": "Indeed", "url": "https://www.indeed.com/", "type": "directory", "found": True},
   {"id": "s4", "name": "SEC EDGAR", "url": "https://www.sec.gov/", "type": "official", "found": False, "note": "No filings."}],
 "fields": {"legalName": {"v": "Acme Tooling, LLC", "src": ["s1", "s2"]}, "employees": {"v": "40", "src": ["s2"], "alt": [{"v": "55", "src": ["s3"]}]},
   "revenue": {"v": "About $6.5M", "src": ["s2"]}, "entityType": {"v": "LLC", "src": ["s1"]}, "phone": {"v": "555-0199", "src": ["s2"]},
   "website": {"v": "acme.example", "src": ["s2"]}, "description": {"v": "Tool and die shop.", "src": ["s2"]}, "formed": {"v": "2001-05-01", "src": ["s1"]},
   "naics": {"v": "333514", "src": ["s1"]}, "tractIncome": {"v": "Moderate income (LMI)", "src": ["s1"]}, "linkedin": {"v": "https://www.linkedin.com/company/acme", "src": ["s3"]}},
 "people": [{"name": "Jane Roe", "title": "Owner", "src": ["s1", "s2"]}, {"name": "Sam Ito", "title": "Controller", "src": ["s2"]}, {"name": "Ava Cruz", "title": "Machinist", "src": ["s3"]}],
 "filings": [{"date": "2026-10-01", "kind": "UCC lien", "detail": "Equipment lien", "src": ["s1"]}, {"date": "2020-05-01", "kind": "PPP loan", "detail": "$310,000", "src": ["s1"]},
   {"date": "2025-02-01", "kind": "SEC Form D", "detail": "$2M equity raise", "src": ["s1"]}],
 "news": [{"date": "2026-10-20", "title": "Acme expands", "url": "https://example.com/", "sourceName": "Erie News"}],
 "signals": [{"type": "expansion", "date": "2026-10-20", "evidence": "New building", "src": ["s2"]}],
 "needs": ["Equipment financing"], "talkingPoints": ["Ask about the new building."]}
seed = {"businesses": [], "cois": [], "matches": [], "signals": [], "settings": [{"id": "providers", "revUnknown": True}], "companyProfiles": [researched]}
MOCK = """
window.__store=%s; const subs={};
function snap(col){const docs=Object.values(window.__store[col]||{}).map(d=>({id:d.id,data:()=>{const c={...d};delete c.id;return c}}));(subs[col]||[]).forEach(cb=>cb({docs}))}
for(const k of Object.keys(window.__store)){const o={};for(const d of window.__store[k])o[d.id]=d;window.__store[k]=o}
const coll=col=>({limit:()=>coll(col),onSnapshot:(cb)=>{(subs[col]=subs[col]||[]).push(cb);setTimeout(()=>snap(col),0);return()=>{}},
  doc:id=>({set:async v=>{(window.__store[col]=window.__store[col]||{})[id]={id,...v};snap(col)},delete:async()=>{delete (window.__store[col]||{})[id];snap(col)}})});
window.__snap=snap; const sample=async()=>({text:""}); sample.json=async(p)=>{window.__prompt=p;return {fields:{legalName:"Acme Tooling, LLC",employees:"55",sic:"3544"},people:[{name:"Jane Roe",title:"Owner"},{name:"Bob Lee",title:"Plant manager"}],filings:[],type:"directory"}};
window.__dl=null; const downloads={save:async x=>{window.__dl=x}};
window.claude={use:async n=>n==="db"?{collection:coll}:n==="sample"?sample:n==="downloads"?downloads:null};
""" % json.dumps(seed)
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); errs = []
    pg = await br.new_page(viewport={"width": 1280, "height": 900}); pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.add_init_script(MOCK); await pg.goto(APP); await pg.wait_for_timeout(600)
    E = pg.evaluate; txt = lambda: pg.inner_text("#view")
    store = lambda col: E(f"Object.values(window.__store['{col}']||{{}})")
    # 1
    await pg.click("#sidenav [data-sub=crs]"); await pg.wait_for_timeout(150)
    check("sidebar opens Company research", await pg.locator("#crForm").count() == 1)
    check("existing profile listed", "Acme Tooling" in await txt())
    # 2
    await pg.fill("#crName", "Lakeside Orthodontics"); await pg.fill("#crDomain", "https://lakesideortho.example/"); await pg.select_option("#crState", "NJ")
    await pg.click("#crForm button[type=submit]"); await pg.wait_for_timeout(250)
    profs = await store("companyProfiles"); new = [x for x in profs if x["name"] == "Lakeside Orthodontics"]
    check("profile saved as queued", len(new) == 1 and new[0]["status"] == "queued" and new[0]["domain"] == "lakesideortho.example", new)
    t = await txt()
    check("waiting message shown", "Waiting for research" in t)
    check("new profile opens on Sources", await E("CR.tab==='sources'"))
    links = await E("[...document.querySelectorAll('.crlink')].map(a=>a.href)")
    check("prefilled source links", any("njportal" in u for u in links) and any("opencorporates.com/companies/us_nj?q=Lakeside" in u for u in links) and any(u.startswith("https://lakesideortho.example") for u in links), len(links))
    await pg.screenshot(path=f"{OUT}/cr-queued.png", full_page=True)
    # 7
    await pg.click("[data-crback]"); await pg.fill("#crName", "lakeside orthodontics inc"); await pg.select_option("#crState", "NJ")
    await pg.click("#crForm button[type=submit]"); await pg.wait_for_timeout(250)
    check("same company reopens existing profile", len([x for x in await store("companyProfiles") if "akeside" in x["name"]]) == 1)
    # 3
    await pg.click("[data-crback]"); await pg.click("[data-crpreview=p9]"); await pg.wait_for_timeout(150); sh = await pg.inner_text("#sheet")
    check("preview: firmographics, alternate names, sources", all(x in sh for x in ["About $6.5M", "40", "acme.example", "Acme Tooling, LLC", "Sources contributing", "Indeed"]))
    await pg.click("#sheet [data-crid=p9]"); await pg.wait_for_timeout(150); t = await txt()
    kt = await pg.inner_text(".crkey")
    check("key facts pinned at top", await E("getComputedStyle(document.querySelector('.crkey')).position==='sticky'") and all(x in kt for x in ["About $6.5M", "40", "LinkedIn", "Overview", "People", "Finance", "Highlights", "Sources"]))
    check("merged field with agreement badge", "Acme Tooling, LLC" in t and "2 sources agree" in t)
    check("conflict shown", "Sources disagree" in t and "Also reported" in t and "55" in t)
    check("source chips link out with details on hover", await pg.locator(".crsrc[href='https://file.dos.pa.gov/search/business'][title*='Official record']").count() >= 1)
    check("filings and funding summaries", "2 found" in t and "Latest: UCC lien" in t and "Latest: SEC Form D" in t)
    check("favorite roles on overview", "Jane Roe" in t and "Sam Ito" in t and "Ava Cruz" not in t and "Owners and executives" in t)
    check("news and brief", all(x in t for x in ["Acme expands", "Before you call", "Equipment financing"]))
    await pg.screenshot(path=f"{OUT}/cr-overview.png", full_page=True)
    # 4
    await pg.click(".crsum"); await pg.wait_for_timeout(100); t = await txt()
    check("summary opens Finance tab", await E("CR.tab==='finance'") and "Loans (1)" in t and "Funding (1)" in t and "Liens (1)" in t and "PPP loan" in t)
    await pg.click(".crtabs [data-crtab=highlights]"); t = await txt()
    check("highlights tab", "333514" in t and "Moderate income (LMI)" in t and "Census tract" in t)
    await pg.click(".crtabs [data-crtab=sources]"); t = await txt()
    check("sources tab is single-source view", "Indeed" in t and "Nothing found" in t and "No filings." in t and "Sources to check" in t)
    # 4b
    await pg.click(".crtabs [data-crtab=people]"); t = await txt()
    check("people tab lists everyone", all(x in t for x in ["Jane Roe", "Sam Ito", "Ava Cruz"]))
    await pg.fill("#crpq", "machin"); await pg.wait_for_timeout(100); t = await pg.inner_text("#crPeople")
    check("people search by title", "Ava Cruz" in t and "Jane Roe" not in t)
    await pg.fill("#crpq", ""); await pg.click("[data-crrole='Finance']"); t = await pg.inner_text("#crPeople")
    check("filter by favorite role", "Sam Ito" in t and "Jane Roe" not in t)
    await pg.click("[data-crroles]"); await pg.fill("#cr_roles", "Shop floor: machinist, operator\nOwners: owner"); await pg.click("[data-crrolessave]"); await pg.wait_for_timeout(200)
    st = await store("settings"); fr = [x for x in st if x["id"] == "favroles"]
    check("role groups saved", fr and fr[0]["groups"][0] == {"name": "Shop floor", "words": "machinist, operator"})
    await pg.click("[data-crrole='Shop floor']"); t = await pg.inner_text("#crPeople")
    check("custom group filters", "Ava Cruz" in t and "Sam Ito" not in t)
    await pg.click("[data-crrole='']"); await pg.check("[data-crpick='0']"); await pg.check("[data-crpick='2']")
    check("export button counts selection", "Export 2 selected" in await txt())
    await pg.click("[data-crpexport]"); await pg.wait_for_timeout(150); dl = await E("window.__dl")
    check("CSV export of selected people", dl and dl["filename"].endswith(".csv") and "Jane Roe" in dl["data"] and "Ava Cruz" in dl["data"] and "Sam Ito" not in dl["data"] and "PA business registry" in dl["data"])
    check("add contacts needs a saved business", await pg.locator("[data-crpadd]").count() == 0)
    await pg.click("[data-crroles]"); await pg.click("[data-crrolesreset]"); await pg.wait_for_timeout(150)
    await pg.click(".crtabs [data-crtab=overview]")
    # 5
    await pg.click("[data-cradd=p9]"); await pg.fill("#cr_url", "https://www.linkedin.com/company/acme"); await pg.fill("#cr_sname", "LinkedIn"); await pg.fill("#cr_text", "Acme Tooling LLC, 55 employees. Owner Jane Roe. Plant manager Bob Lee.")
    await pg.click("[data-crextract=p9]"); await pg.wait_for_timeout(300)
    pr = [x for x in await store("companyProfiles") if x["id"] == "p9"][0]; li = [s for s in pr["sources"] if s["name"] == "LinkedIn"]
    check("pasted source added", len(li) == 1 and li[0]["url"].startswith("https://www.linkedin.com"))
    sid = li[0]["id"] if li else ""
    check("same value adds the source", sid in pr["fields"]["legalName"]["src"])
    check("matching conflict gains the source", sid in pr["fields"]["employees"]["alt"][0]["src"])
    check("new field and new person", pr["fields"].get("sic", {}).get("v") == "3544" and any(x["name"] == "Bob Lee" for x in pr["people"]))
    # 6
    await pg.click("[data-crsave=p9]"); await pg.wait_for_timeout(300)
    bz = await store("businesses")
    check("business created", len(bz) == 1 and bz[0]["name"] == "Acme Tooling" and bz[0]["industry"] == "Manufacturing" and bz[0]["revenue"] == 6500000 and bz[0]["employees"] == 40 and bz[0]["entityType"] == "LLC", bz)
    b = bz[0] if bz else {}
    check("contacts and sources carried over", len(b.get("contacts", [])) == 4 and b.get("contact") == "Jane Roe (Owner)" and len(b.get("profile", {}).get("sources", [])) >= 3)
    sg = await store("signals")
    check("signal created", len(sg) == 1 and sg[0]["type"] == "expansion" and sg[0]["businessId"] == b.get("id"))
    check("profile linked to business", [x for x in await store("companyProfiles") if x["id"] == "p9"][0].get("bizId") == b.get("id"))
    check("Open business page shown", await pg.locator("[data-bizview]").count() >= 1)
    bz0 = (await store("businesses"))[0]; await E(f"window.__store.businesses['{bz0['id']}'].contacts=[]"); await E("window.__snap('businesses')")
    await pg.click(".crtabs [data-crtab=people]"); await pg.click("[data-crpadd]"); await pg.wait_for_timeout(200)
    names = sorted(c["name"] for c in (await store("businesses"))[0]["contacts"])
    check("only the selected people added as contacts", names == ["Ava Cruz", "Jane Roe"], names)
    await pg.click(".crtabs [data-crtab=overview]")
    await pg.click("[data-crsave=p9]"); await pg.wait_for_timeout(300)
    check("second save updates, no duplicate", len(await store("businesses")) == 1 and len(await store("signals")) == 1)
    # phone layout
    await pg.set_viewport_size({"width": 390, "height": 844}); await pg.wait_for_timeout(150)
    over = await E("document.documentElement.scrollWidth>window.innerWidth+1")
    check("no sideways scroll on a phone", not over)
    await pg.screenshot(path=f"{OUT}/cr-phone.png", full_page=True)
    # demo mode has sample profiles
    d = await br.new_page(viewport={"width": 1280, "height": 900}); d.on("pageerror", lambda e: errs.append(str(e)))
    await d.goto(APP); await d.evaluate("localStorage.setItem('rb-mode','demo');localStorage.removeItem('rb-demo')"); await d.reload(); await d.wait_for_timeout(400)
    check("demo has sample profiles", await d.evaluate("S.prof.length===2 && S.prof[0].bizId==='b2'"))
    await d.evaluate("tab='crs';CR.id='p1';render()"); await d.wait_for_timeout(150)
    await d.screenshot(path=f"{OUT}/cr-demo.png", full_page=True)
    check("no page errors", not errs, errs)
    await br.close()
  print("Screenshots:", OUT)
  sys.exit(0 if all(r[1] for r in results) else 1)
asyncio.run(main())

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re, io, time, xml.etree.ElementTree as ET, random, pandas as pd, urllib.robotparser
from urllib.parse import urljoin, urlparse
from collections import deque
from datetime import datetime

try:
    import dns.resolver as _dns_resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

st.set_page_config(
    page_title="MailHunter",
    page_icon="✉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ─────────────────────────────────────────────────────────────────────
# Only styling — no layout overrides, no position tricks
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"]  { display: none !important; }
[data-testid="collapsedControl"]   { display: none !important; }

.block-container {
    padding: 2rem 2.5rem 5rem !important;
    max-width: 100% !important;
}

/* ── page header ── */
.mh-header {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 1.25rem; margin-bottom: 1.5rem;
    border-bottom: 1px solid #ebebeb;
}
.mh-logo { font-size: 16px; font-weight: 700; color: #111; display: flex; align-items: center; gap: 8px; }
.mh-dot  { width: 9px; height: 9px; background: #111; border-radius: 50%; flex-shrink: 0; }

/* ── section label ── */
.sec {
    font-size: 10px; font-weight: 700; letter-spacing: 0.9px;
    text-transform: uppercase; color: #bbb;
    margin: 0 0 8px; display: block;
}

/* ── buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: #111 !important;
    border: none !important;
    color: #fff !important;
}
.stButton > button[kind="primary"]:hover  { background: #333 !important; }
.stButton > button[kind="primary"]:disabled { background: #ddd !important; color: #aaa !important; }
.stButton > button[kind="secondary"] {
    background: #fff !important;
    border: 1px solid #e0e0e0 !important;
    color: #555 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #111 !important; color: #111 !important;
}
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 13px !important;
    background: #fff !important; border: 1px solid #e0e0e0 !important; color: #555 !important;
    width: 100%;
}
.stDownloadButton > button:hover { border-color: #111 !important; color: #111 !important; }

/* ── inputs ── */
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important; border-radius: 8px !important;
    border: 1px solid #e0e0e0 !important; background: #fafafa !important;
    line-height: 1.7 !important;
}
.stTextArea textarea:focus {
    border-color: #111 !important; box-shadow: 0 0 0 3px rgba(0,0,0,.05) !important;
}
.stTextInput > div > input {
    border-radius: 8px !important; border: 1px solid #e0e0e0 !important;
    font-size: 13px !important;
}
.stTextInput > div > input:focus {
    border-color: #111 !important; box-shadow: 0 0 0 3px rgba(0,0,0,.05) !important;
}

/* ── metrics ── */
[data-testid="stMetric"] {
    background: #fff; border: 1px solid #ebebeb;
    border-radius: 10px; padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 11px !important; font-weight: 600 !important;
    color: #999 !important; text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important; font-weight: 700 !important;
    color: #111 !important; letter-spacing: -0.5px !important;
}

/* ── live log ── */
.log-box {
    background: #fafafa; border: 1px solid #ebebeb; border-radius: 8px;
    padding: 10px 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px;
    line-height: 1.9; max-height: 220px; overflow-y: auto; margin-top: 10px;
}
.log-box .ll-site   { color: #111; font-weight: 700; }
.log-box .ll-email  { color: #16a34a; font-weight: 600; }
.log-box .ll-page   { color: #aaa; }
.log-box .ll-skip   { color: #d97706; }
.log-box .ll-timing { color: #ccc; }
.log-box .ll-done   { color: #bbb; }
.log-box .ll-social { color: #2563eb; }

/* ── progress ── */
.prog-outer {
    margin: 10px 0 4px;
}
.prog-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 12px; font-weight: 600; margin-bottom: 6px;
}
.prog-count { font-size: 11px; font-weight: 400; color: #999; }
.prog-track {
    height: 4px; background: #f0f0f0; border-radius: 99px; overflow: hidden;
}
.prog-fill { height: 100%; background: #111; border-radius: 99px; transition: width .4s; }
.scan-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #16a34a; border-radius: 50%; margin-right: 7px;
    animation: blink 1.4s ease-in-out infinite;
}
.scan-dot.paused { background: #d97706; animation: none; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.15} }

/* ── url pills ── */
.pills { display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0 2px; }
.pill {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    background: #f5f5f5; border: 1px solid #e8e8e8;
    border-radius: 4px; padding: 2px 7px; color: #888;
}

/* ── divider ── */
.div { border-top: 1px solid #ebebeb; margin: 16px 0; }

/* ── expander ── */
details summary { font-weight: 600 !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ────────────────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
TIER1 = re.compile(r"^(editor|admin|press|advert|contact)[a-z0-9._%+\-]*@", re.IGNORECASE)
TIER2 = re.compile(r"^(info|sales|hello|office|team|support|help)[a-z0-9._%+\-]*@", re.IGNORECASE)
BLOCKED_TLDS = {'png','jpg','jpeg','webp','gif','svg','ico','bmp','tiff','avif','mp4','mp3','wav','ogg','mov','avi','webm','pdf','zip','rar','tar','gz','7z','js','css','php','asp','aspx','xml','json','ts','jsx','tsx','woff','woff2','ttf','eot','otf','map','exe','dmg','pkg','deb','apk'}
PLACEHOLDER_DOMAINS = {'example.com','example.org','example.net','test.com','domain.com','yoursite.com','yourwebsite.com','website.com','email.com','sampleemail.com','mailtest.com','placeholder.com'}
PLACEHOLDER_LOCALS  = {'you','user','name','email','test','example','someone','username','yourname','youremail','enter','address','sample'}
SUPPRESS_PREFIXES   = ['noreply','no-reply','donotreply','do-not-reply','mailer-daemon','bounce','bounces','unsubscribe','notifications','notification','newsletter','newsletters','postmaster','webmaster','auto-reply','autoreply','daemon','robot','alerts','alert','system']
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
]
PRIORITY_PATHS = ["/contact","/contact-us","/contact_us","/contactus","/reach-us","/get-in-touch","/about","/about-us","/about_us","/aboutus","/team","/our-team","/staff","/people","/write-for-us","/writeforus","/guest-post","/guest-posts","/contribute","/contributors","/submission","/submissions","/submit","/pitch","/advertise","/advertise-with-us","/advertising","/work-with-us","/partner"]
TWITTER_SKIP  = {'share','intent','home','search','hashtag','i','status','twitter','x'}
LINKEDIN_SKIP = {'share','shareArticle','in','company','pub','feed','login','authwall'}
FACEBOOK_SKIP = {'sharer','share','dialog','login','home','watch','groups','events','marketplace'}

# ── SESSION STATE ────────────────────────────────────────────────────────────
for k, v in {
    "results":{}, "scraped_domains":set(), "scan_state":"idle",
    "scan_queue":[], "scan_idx":0, "log_lines":[], "sessions":[],
    "active_session":None, "mode":"Easy", "tbl_filter":"All",
    "single_mode":False, "skip_t1":True, "respect_robots":False,
    "scrape_fb":False, "f_tier1":True, "f_tier2":True, "f_tier3":True,
    "mx_cache":{},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CORE FUNCTIONS (verbatim from v9) ────────────────────────────────────────
def is_valid_email(email):
    e = email.strip()
    if not e or e.count('@') != 1: return False
    local, domain = e.split('@'); lo, do = local.lower(), domain.lower()
    if not local or not domain: return False
    if local.startswith('.') or local.endswith('.'): return False
    if local.startswith('-'): return False
    if len(local) > 64 or len(domain) > 255: return False
    if '.' not in domain: return False
    tld = do.rsplit('.', 1)[-1]
    if len(tld) < 2 or tld in BLOCKED_TLDS: return False
    if re.search(r'@\d+x[\-\d]', '@'+do): return False
    if re.match(r'^\d+x', do): return False
    if do in PLACEHOLDER_DOMAINS: return False
    if lo in PLACEHOLDER_LOCALS: return False
    if any(lo == p or lo.startswith(p) for p in SUPPRESS_PREFIXES): return False
    if re.search(r'\d+x\d+', lo): return False
    return True

def tier_key(email):
    if TIER1.match(email): return "1"
    if TIER2.match(email): return "2"
    return "3"

def tier_short(email): return {"1":"Tier 1","2":"Tier 2","3":"Tier 3"}[tier_key(email)]
def tier_label(email): return {"1":"🥇 Tier 1","2":"🥈 Tier 2","3":"🥉 Tier 3"}[tier_key(email)]
def sort_by_tier(emails): return sorted(emails, key=tier_key)

def pick_best(emails):
    pool = [e for e in emails if is_valid_email(e)]
    if not pool: return None
    t1 = [e for e in pool if TIER1.match(e)]
    if t1: return t1[0]
    t2 = [e for e in pool if TIER2.match(e)]
    if t2: return t2[0]
    return pool[0]

def make_headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.5"}

def fetch_page(url, timeout=10):
    try:
        r = requests.get(url, headers=make_headers(), timeout=timeout, allow_redirects=True)
        if r.ok and "text" in r.headers.get("Content-Type", ""): return r.text
    except: pass
    return None

def extract_emails(html):
    soup = BeautifulSoup(html, "html.parser"); raw = set()
    raw.update(EMAIL_REGEX.findall(soup.get_text(" ")))
    raw.update(EMAIL_REGEX.findall(html))
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            raw.add(a["href"][7:].split("?")[0].strip())
    return {e for e in raw if is_valid_email(e)}

def extract_social(html):
    soup = BeautifulSoup(html, "html.parser"); tw, li, fb = set(), set(), set()
    for a in soup.find_all("a", href=True):
        href = a["href"]; hl = href.lower()
        if "twitter.com/" in hl or "x.com/" in hl:
            m = re.search(r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})', href)
            if m and m.group(1).lower() not in TWITTER_SKIP: tw.add("@"+m.group(1))
        elif "linkedin.com/in/" in hl or "linkedin.com/company/" in hl:
            m = re.search(r'linkedin\.com/(in|company)/([^/?&#\s]{2,80})', href)
            if m and m.group(2).lower() not in LINKEDIN_SKIP: li.add(f"linkedin.com/{m.group(1)}/{m.group(2)}")
        elif "facebook.com/" in hl and "facebook.com/tr?" not in hl:
            m = re.search(r'facebook\.com/([A-Za-z0-9_.]{3,80})', href)
            if m and m.group(1).lower() not in FACEBOOK_SKIP: fb.add(f"facebook.com/{m.group(1)}")
    return tw, li, fb

def get_internal_links(html, base_url, root_domain):
    soup = BeautifulSoup(html, "html.parser"); links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"]); p = urlparse(full)
        if p.netloc == root_domain and p.scheme in ("http","https"):
            links.append(full.split("#")[0].split("?")[0])
    return list(set(links))

def find_write_for_us_links(html, base_url, root_domain):
    KW = ["write for us","write-for-us","writeforus","guest post","guest-post","guestpost","contribute","contributors","submission","submissions","submit a","pitch us","pitch to us","advertise","advertising","advertise with","work with us","partner with","partnerships","become a contributor","become an author","join our team","write with us"]
    soup = BeautifulSoup(html, "html.parser"); found = []
    for a in soup.find_all("a", href=True):
        href = a.get("href",""); text = (a.get_text(" ",strip=True)+" "+href).lower()
        if any(kw in text for kw in KW):
            full = urljoin(base_url, href); p = urlparse(full)
            if p.netloc == root_domain and p.scheme in ("http","https"):
                found.append(full.split("#")[0].split("?")[0])
    return list(set(found))

def check_mx(email):
    if not DNS_AVAILABLE: return None
    domain = email.split("@")[1].lower(); cache = st.session_state.mx_cache
    if domain in cache: return cache[domain]
    try: result = len(_dns_resolver.resolve(domain,"MX",lifetime=4)) > 0
    except: result = False
    cache[domain] = result; return result

def load_robots(root_url, respect):
    if not respect: return None
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(root_url.rstrip("/")+"/robots.txt")
    try: rp.read()
    except: pass
    return rp

def robots_allowed(rp, url):
    if rp is None: return True
    try: return rp.can_fetch("*", url)
    except: return True

def scrape_facebook_page(fb_handle, log_cb):
    slug = fb_handle.replace("facebook.com/","").strip("/")
    if not slug: return set()
    url = f"https://www.facebook.com/{slug}"
    log_cb(("page_start", url.replace("https://",""), "facebook", None), "active")
    t0 = time.time(); html = fetch_page(url, timeout=14); elapsed = round(time.time()-t0,2)
    if html:
        found = extract_emails(html)
        for e in sort_by_tier(found): log_cb(("email", e, f"facebook.com/{slug}", tier_label(e)), "email")
        log_cb(("timing", f"{elapsed}s · {len(found)} email(s) from Facebook", url, None), "timing")
        return found
    log_cb(("timing", f"{elapsed}s · Facebook blocked", url, None), "timing")
    return set()

def fetch_sitemap_urls(root_url):
    urls = []
    for c in [urljoin(root_url,"/sitemap.xml"), urljoin(root_url,"/sitemap_index.xml")]:
        html = fetch_page(c)
        if not html: continue
        try:
            root_el = ET.fromstring(html); ns = {"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root_el.findall(".//sm:loc",ns):
                u = loc.text.strip()
                if u.endswith(".xml"):
                    sub = fetch_page(u)
                    if sub:
                        try:
                            sr = ET.fromstring(sub)
                            for sl in sr.findall(".//sm:loc",ns): urls.append(sl.text.strip())
                        except: pass
                else: urls.append(u)
        except: pass
        if urls: break
    return urls

def scrape_one_site(root_url, cfg, skip_t1, respect_robots, log_cb):
    t_start = time.time(); parsed = urlparse(root_url); root_domain = parsed.netloc
    visited = set(); queue = deque(); all_emails = set(); all_tw,all_li,all_fb = set(),set(),set()
    base = root_url.rstrip("/"); rp = load_robots(root_url, respect_robots)
    for path in PRIORITY_PATHS: queue.append((base+path,0,True))
    queue.append((root_url,0,False))
    if cfg.get("sitemap"):
        sm_urls = fetch_sitemap_urls(root_url)
        log_cb(("info",f"{len(sm_urls)} URLs in sitemap",None,None),"info")
        for u in sm_urls[:cfg["max_pages"]]: queue.append((u,0,False))
    max_pages = cfg["max_pages"]; max_depth = cfg["max_depth"]; pages_done = 0
    while queue and pages_done < max_pages+len(PRIORITY_PATHS):
        url,depth,is_priority = queue.popleft()
        if url in visited: continue
        visited.add(url)
        label = "priority" if is_priority else f"{pages_done+1}/{max_pages}"
        short = url.replace("https://","").replace("http://",""); t_page = time.time()
        if not robots_allowed(rp, url):
            log_cb(("timing",f"robots.txt blocked — {short}",url,None),"timing")
            if not is_priority: pages_done += 1
            continue
        log_cb(("page_start",short,label,None),"active")
        html = fetch_page(url); elapsed = round(time.time()-t_page,2)
        if html:
            found = extract_emails(html); new_emails = found-all_emails
            tw,li,fb = extract_social(html)
            new_tw=tw-all_tw; new_li=li-all_li; new_fb=fb-all_fb
            all_emails.update(found); all_tw.update(tw); all_li.update(li); all_fb.update(fb)
            for wlink in find_write_for_us_links(html,url,root_domain):
                if wlink not in visited:
                    queue.appendleft((wlink,0,True))
                    log_cb(("info",f"write-for-us → {wlink.replace('https:///','')}",None,None),"info")
            for email in sort_by_tier(new_emails): log_cb(("email",email,short,tier_label(email)),"email")
            for handle in sorted(new_tw|new_li|new_fb): log_cb(("social",handle,short,None),"social")
            log_cb(("timing",f"{elapsed}s · {len(new_emails)} new email(s)",short,None),"timing")
            if not is_priority and depth < max_depth:
                for link in get_internal_links(html,url,root_domain):
                    if link not in visited: queue.append((link,depth+1,False))
            if skip_t1 and any(TIER1.match(e) for e in all_emails):
                t1e = next(e for e in all_emails if TIER1.match(e))
                log_cb(("skip",f"Tier 1 ({t1e}) — skipping {root_domain}",None,None),"skip")
                break
        else:
            log_cb(("timing",f"{elapsed}s · no response",short,None),"timing")
        if not is_priority: pages_done += 1
    total_time = round(time.time()-t_start,1)
    if st.session_state.get("scrape_fb") and all_fb:
        primary_fb = sorted(all_fb)[0]
        log_cb(("info",f"Auto-scraping Facebook: {primary_fb}",None,None),"info")
        fb_emails = scrape_facebook_page(primary_fb,log_cb); all_emails.update(fb_emails)
    sorted_emails = sort_by_tier(all_emails); best = pick_best(all_emails)
    log_cb(("done",f"{root_domain} — {len(all_emails)} email(s) in {total_time}s",None,None),"done")
    return {"Domain":root_domain,"Best Email":best or "","Best Tier":tier_short(best) if best else "",
            "All Emails":sorted_emails,"Twitter":sorted(all_tw),"LinkedIn":sorted(all_li),
            "Facebook":sorted(all_fb),"Pages Scraped":pages_done,"Total Time":total_time,
            "Source URL":root_url,"MX":{}}

def render_log(ph):
    html = ""
    for item,kind in st.session_state.log_lines[-50:]:
        _,text,_,extra = item
        if   kind=="site":   html+=f'<div class="ll-site">▶ {text}</div>'
        elif kind=="active": html+=f'<div class="ll-page">↳ [{extra or ""}] {text}</div>'
        elif kind=="email":  html+=f'<div class="ll-email">✉ {text}</div>'
        elif kind=="social": html+=f'<div class="ll-social">⟐ {text}</div>'
        elif kind=="timing": html+=f'<div class="ll-timing">  {text}</div>'
        elif kind=="skip":   html+=f'<div class="ll-skip">⚡ {text}</div>'
        elif kind in ("done","info"): html+=f'<div class="ll-done">  {text}</div>'
    ph.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)

def log_cb_factory(ph):
    def cb(item, kind):
        st.session_state.log_lines.append((item,kind))
        render_log(ph)
    return cb

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
hd_left, hd_right = st.columns([3,1])
with hd_left:
    st.markdown('<div class="mh-logo"><div class="mh-dot"></div>MailHunter</div>', unsafe_allow_html=True)
    st.caption("Scrape contact emails, social handles and tier-ranked contacts from any site.")
with hd_right:
    # Export lives here so it's always visible top-right
    if st.session_state.results:
        csv_rows = [{"Domain":d,"Best Email":r.get("Best Email",""),"All Emails":"; ".join(r.get("All Emails",[])),"Twitter":"; ".join(r.get("Twitter",[])),"LinkedIn":"; ".join(r.get("LinkedIn",[])),"Facebook":"; ".join(r.get("Facebook",[])),"Pages":r.get("Pages Scraped",0),"Time(s)":r.get("Total Time",""),"Source URL":r.get("Source URL","")} for d,r in st.session_state.results.items()]
        buf = io.StringIO(); pd.DataFrame(csv_rows).to_csv(buf,index=False)
        st.download_button("⬇ Export CSV", buf.getvalue(),
                           f"mailhunter_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           "text/csv", key="export_top")

st.markdown('<div class="div"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  TWO-COLUMN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 2.6], gap="large")

# ═══════════════════════════════════════════════════════════════════════════
#  LEFT COLUMN — controls
# ═══════════════════════════════════════════════════════════════════════════
with left:

    # ── URL INPUT ──────────────────────────────────────────────────────────
    st.markdown('<span class="sec">Target URLs</span>', unsafe_allow_html=True)
    tab_paste, tab_upload = st.tabs(["📋 Paste", "📁 Upload"])
    urls_to_scrape = []

    with tab_paste:
        raw = st.text_area("urls", label_visibility="collapsed",
                           placeholder="https://magazine.com\nhttps://techblog.io\nnewspaper.org",
                           height=130, key="url_input")
        if raw.strip():
            for line in raw.splitlines():
                line = line.strip()
                if not line: continue
                if not line.startswith("http"): line = "https://"+line
                urls_to_scrape.append(line)

    with tab_upload:
        uploaded = st.file_uploader("file", type=["csv","txt"], label_visibility="collapsed")
        if uploaded:
            rb = uploaded.read()
            if uploaded.name.endswith(".csv"):
                try:
                    df_up = pd.read_csv(io.BytesIO(rb)); cols_u = list(df_up.columns)
                    hints = ["url","link","website","site","domain","href"]
                    defcol = next((c for c in cols_u if any(h in c.lower() for h in hints)), cols_u[0])
                    col_sel = st.selectbox("URL column", cols_u, index=cols_u.index(defcol))
                    for u in df_up[col_sel].dropna().astype(str):
                        u=u.strip()
                        if not u.startswith("http"): u="https://"+u
                        urls_to_scrape.append(u)
                    st.caption(f"✓ {len(urls_to_scrape)} URLs loaded")
                except Exception as ex: st.error(f"CSV error: {ex}")
            else:
                for line in rb.decode("utf-8","ignore").splitlines():
                    line=line.strip()
                    if not line: continue
                    if not line.startswith("http"): line="https://"+line
                    urls_to_scrape.append(line)
                st.caption(f"✓ {len(urls_to_scrape)} URLs loaded")

    if urls_to_scrape:
        pills = "".join(f'<span class="pill">{u.replace("https://","")[:26]}</span>' for u in urls_to_scrape[:5])
        if len(urls_to_scrape) > 5: pills += f'<span class="pill">+{len(urls_to_scrape)-5}</span>'
        st.markdown(f'<div class="pills">{pills}</div>', unsafe_allow_html=True)

    # ── CRAWL MODE ─────────────────────────────────────────────────────────
    st.markdown('<span class="sec" style="margin-top:20px;display:block">Crawl Mode</span>', unsafe_allow_html=True)
    m1,m2,m3 = st.columns(3)
    for col, m in zip([m1,m2,m3], ["Easy","Medium","Extreme"]):
        with col:
            if st.button(m, key=f"mode_{m}",
                         type="primary" if st.session_state.mode==m else "secondary",
                         use_container_width=True):
                st.session_state.mode = m; st.rerun()

    mode_key = st.session_state.mode
    cfg = {"Easy":{"max_pages":1,"max_depth":0,"sitemap":False,"delay":0.3},
           "Medium":{"max_pages":50,"max_depth":3,"sitemap":False,"delay":0.5},
           "Extreme":{"max_pages":300,"max_depth":6,"sitemap":True,"delay":0.3}}[mode_key].copy()
    st.caption({"Easy":"Homepage only — fast","Medium":"Crawls links — thorough","Extreme":"Sitemap + deep crawl"}[mode_key])

    if mode_key == "Medium":
        cfg["max_depth"] = st.slider("Crawl depth",    1,  5,   3, key="depth_s")
        cfg["max_pages"] = st.slider("Max pages/site", 10, 200, 50, key="pages_s")
    elif mode_key == "Extreme":
        cfg["max_pages"] = st.slider("Max pages/site", 50, 500, 300, key="pages_x")

    # ── SCAN BUTTONS ───────────────────────────────────────────────────────
    st.markdown('<div class="div"></div>', unsafe_allow_html=True)
    scan_state = st.session_state.scan_state
    ba1, ba2 = st.columns(2)

    with ba1:
        if scan_state == "idle":
            start = st.button("▶ Start", type="primary", use_container_width=True,
                              disabled=not urls_to_scrape, key="btn_start")
        elif scan_state == "running":
            start = False
            if st.button("⏸ Pause", type="primary", use_container_width=True, key="btn_pause"):
                st.session_state.scan_state = "paused"; st.rerun()
        elif scan_state == "paused":
            start = False
            if st.button("▶ Resume", type="primary", use_container_width=True, key="btn_resume"):
                st.session_state.scan_state = "running"; st.rerun()
        else:
            start = st.button("▶ New Scan", type="primary", use_container_width=True,
                              disabled=not urls_to_scrape, key="btn_new")

    with ba2:
        if st.button("✕ Clear", type="secondary", use_container_width=True, key="btn_clear"):
            st.session_state.results    = {}
            st.session_state.scan_queue = []
            st.session_state.log_lines  = []
            st.session_state.scan_state = "idle"
            st.session_state.scan_idx   = 0
            st.rerun()

    # save button (only when results exist)
    if st.session_state.results:
        if st.button("💾 Save Session", type="secondary", use_container_width=True, key="btn_save"):
            ts = datetime.now().strftime("%b %d %H:%M")
            st.session_state.sessions.append({
                "name": f"Scan {len(st.session_state.sessions)+1} · {ts}",
                "results": dict(st.session_state.results)
            }); st.rerun()

    # trigger start
    start = start if "start" in dir() else False
    if start and urls_to_scrape:
        new_urls = [u for u in urls_to_scrape if urlparse(u).netloc not in st.session_state.scraped_domains]
        if new_urls:
            if scan_state == "done": st.session_state.results = {}
            st.session_state.scan_queue  = new_urls
            st.session_state.scan_idx    = 0
            st.session_state.scan_state  = "running"
            st.session_state.log_lines   = []
            st.rerun()

    # ── PROGRESS + LOG ─────────────────────────────────────────────────────
    prog_ph = st.empty()
    log_ph  = st.empty()

    if scan_state in ("running","paused") and st.session_state.scan_queue:
        idx   = st.session_state.scan_idx
        total = len(st.session_state.scan_queue)
        pct   = int(idx/total*100) if total else 0
        dot   = "scan-dot paused" if scan_state=="paused" else "scan-dot"
        lbl   = "Paused" if scan_state=="paused" else "Scanning…"
        prog_ph.markdown(f"""
        <div class="prog-outer">
          <div class="prog-row">
            <span><span class="{dot}"></span>{lbl}</span>
            <span class="prog-count">{idx} / {total} sites</span>
          </div>
          <div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.log_lines:
        render_log(log_ph)

    # ── SETTINGS ───────────────────────────────────────────────────────────
    st.markdown('<div class="div"></div>', unsafe_allow_html=True)
    with st.expander("⚙ Settings", expanded=False):
        st.markdown("**Behaviour**")
        st.session_state.single_mode    = st.toggle("Best email per site only",  value=st.session_state.single_mode,    key="t_single")
        st.session_state.skip_t1        = st.toggle("Skip once Tier 1 found",    value=st.session_state.skip_t1,        key="t_skip")
        st.session_state.respect_robots = st.toggle("Respect robots.txt",        value=st.session_state.respect_robots,  key="t_robots")
        st.divider()
        st.markdown("**Extra Sources**")
        st.session_state.scrape_fb = st.toggle("Auto-scrape Facebook page", value=st.session_state.scrape_fb, key="t_fb")
        st.divider()
        st.markdown("**Tier Filters**")
        st.session_state.f_tier1 = st.checkbox("🥇 Tier 1 — editor / admin / press", value=st.session_state.f_tier1, key="cb_t1")
        st.session_state.f_tier2 = st.checkbox("🥈 Tier 2 — info / sales / support", value=st.session_state.f_tier2, key="cb_t2")
        st.session_state.f_tier3 = st.checkbox("🥉 Tier 3 — other valid emails",      value=st.session_state.f_tier3, key="cb_t3")
        st.divider()
        n_mem = len(st.session_state.scraped_domains)
        st.caption(f"Domain memory: {n_mem} domain(s) stored")
        if n_mem:
            if st.button("Clear memory", key="btn_clearmem", type="secondary", use_container_width=True):
                st.session_state.scraped_domains = set(); st.rerun()

    # ── SESSIONS ───────────────────────────────────────────────────────────
    if st.session_state.sessions:
        with st.expander(f"💾 Sessions ({len(st.session_state.sessions)})", expanded=False):
            for i, sess in enumerate(st.session_state.sessions):
                n_d = len(sess["results"])
                n_e = sum(len(r.get("All Emails",[])) for r in sess["results"].values())
                sc1,sc2,sc3 = st.columns([3,1,1])
                with sc1: st.caption(f"**{sess['name']}**  \n{n_d} domains · {n_e} emails")
                with sc2:
                    if st.button("Load", key=f"load_{i}", type="secondary", use_container_width=True):
                        st.session_state.results    = sess["results"]
                        st.session_state.scan_state = "done"; st.rerun()
                with sc3:
                    if st.button("Del", key=f"del_{i}", type="secondary", use_container_width=True):
                        st.session_state.sessions.pop(i); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  RIGHT COLUMN — results
# ═══════════════════════════════════════════════════════════════════════════
with right:
    results    = st.session_state.results
    scan_state = st.session_state.scan_state

    if not results:
        # empty state
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:80px 20px;text-align:center;">
          <div style="font-size:48px;opacity:0.1;margin-bottom:20px">✉</div>
          <div style="font-size:18px;font-weight:700;color:#111;margin-bottom:10px">
            No results yet
          </div>
          <div style="font-size:14px;color:#999;line-height:1.7;max-width:320px">
            Paste URLs on the left, choose a crawl mode,<br>and hit <strong>▶ Start</strong>.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── METRICS ───────────────────────────────────────────────────────
        tot_d  = len(results)
        tot_e  = sum(len(r.get("All Emails",[])) for r in results.values())
        t1_cnt = sum(1 for r in results.values() if r.get("Best Tier","").startswith("Tier 1"))
        mx_ok  = sum(1 for r in results.values() for v in r.get("MX",{}).values() if v is True)
        no_e   = sum(1 for r in results.values() if not r.get("Best Email"))

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Domains",      tot_d)
        c2.metric("Emails",       tot_e)
        c3.metric("Tier 1",       t1_cnt)
        c4.metric("MX Verified",  mx_ok)
        c5.metric("No Email",     no_e)

        st.markdown("")

        # ── SEARCH + FILTER ────────────────────────────────────────────────
        sr_col, f1,f2,f3,f4,f5 = st.columns([2.5, 1, 1, 1, 1, 1])
        with sr_col:
            search = st.text_input("s", placeholder="🔍 Search domain or email…",
                                   label_visibility="collapsed", key="search_box")
        for col,lbl,fval in zip(
            [f1,f2,f3,f4,f5],
            ["All","Tier 1","Tier 2","Tier 3","None"],
            ["All","T1",   "T2",   "T3",   "None"]
        ):
            with col:
                if st.button(lbl, key=f"flt_{fval}", use_container_width=True,
                             type="primary" if st.session_state.tbl_filter==fval else "secondary"):
                    st.session_state.tbl_filter = fval; st.rerun()

        # ── BUILD TABLE ────────────────────────────────────────────────────
        rows = []
        for domain, r in results.items():
            all_e = r.get("All Emails",[]); best = r.get("Best Email",""); bt = r.get("Best Tier","")
            extra = len(all_e)-1 if len(all_e)>1 else 0
            mx_data = r.get("MX",{})
            mx_disp = f"✓ {sum(1 for v in mx_data.values() if v)}/{len(mx_data)}" if mx_data else "—"
            rows.append({
                "Domain":     domain,
                "Best Email": best or "—",
                "Tier":       bt or "—",
                "More":       f"+{extra}" if extra else "",
                "MX":         mx_disp,
                "Twitter":    ", ".join(r.get("Twitter",[])[:2]) or "—",
                "LinkedIn":   ", ".join(r.get("LinkedIn",[])[:1]) or "—",
                "Facebook":   ", ".join(r.get("Facebook",[])[:1]) or "—",
                "Pages":      r.get("Pages Scraped",0),
                "Time(s)":    r.get("Total Time","—"),
            })

        df = pd.DataFrame(rows)
        if search:
            m = df["Domain"].str.contains(search,case=False,na=False) | df["Best Email"].str.contains(search,case=False,na=False)
            df = df[m]
        flt = st.session_state.tbl_filter
        if   flt=="T1":   df = df[df["Tier"].str.startswith("Tier 1",na=False)]
        elif flt=="T2":   df = df[df["Tier"].str.startswith("Tier 2",na=False)]
        elif flt=="T3":   df = df[df["Tier"].str.startswith("Tier 3",na=False)]
        elif flt=="None": df = df[df["Best Email"]=="—"]

        st.caption(f"Showing **{len(df)}** of {tot_d} domains")
        st.dataframe(df, use_container_width=True, hide_index=True,
                     height=min(600, 44+max(len(df),1)*36),
                     column_config={
                         "Domain":     st.column_config.TextColumn("Domain",      width=170),
                         "Best Email": st.column_config.TextColumn("Best Email",  width=200),
                         "Tier":       st.column_config.TextColumn("Tier",        width=90),
                         "More":       st.column_config.TextColumn("+",           width=50),
                         "MX":         st.column_config.TextColumn("MX",          width=72),
                         "Twitter":    st.column_config.TextColumn("Twitter",     width=120),
                         "LinkedIn":   st.column_config.TextColumn("LinkedIn",    width=145),
                         "Facebook":   st.column_config.TextColumn("Facebook",    width=145),
                         "Pages":      st.column_config.NumberColumn("Pages",     width=60),
                         "Time(s)":    st.column_config.NumberColumn("Time(s)",   width=72),
                     })

        # ── PER-DOMAIN ACTIONS ─────────────────────────────────────────────
        st.divider()
        st.markdown("**Per-domain actions**")
        pa1,pa2,pa3,pa4 = st.columns([2.5,1.2,1.2,1.2])
        with pa1:
            sel_domain = st.selectbox("domain", list(results.keys()),
                                      label_visibility="collapsed", key="action_domain")
        r_sel     = results.get(sel_domain,{})
        fb_pages  = r_sel.get("Facebook",[])
        all_e_sel = r_sel.get("All Emails",[])

        with pa2:
            if fb_pages:
                if st.button("Scrape Facebook", key="fb_act", type="secondary", use_container_width=True):
                    st.session_state[f"fb_run_{sel_domain}"] = True; st.rerun()
            else:
                st.button("Scrape Facebook", key="fb_dis", type="secondary", disabled=True, use_container_width=True)
        with pa3:
            if DNS_AVAILABLE and all_e_sel:
                if st.button("Verify MX", key="mx_act", type="secondary", use_container_width=True):
                    st.session_state[f"mx_run_{sel_domain}"] = True; st.rerun()
            else:
                st.button("Verify MX", key="mx_dis", type="secondary", disabled=True, use_container_width=True)
        with pa4:
            if all_e_sel:
                st.download_button("Copy emails", "\n".join(all_e_sel),
                                   f"{sel_domain}_emails.txt", key="copy_em", use_container_width=True)

        # run FB
        if sel_domain and st.session_state.get(f"fb_run_{sel_domain}"):
            st.session_state[f"fb_run_{sel_domain}"] = False
            fb_ph2 = st.empty(); fb_lines2 = []
            def fb_log(item,kind):
                fb_lines2.append((item,kind))
                h2 = "".join(f'<div class="{"ll-email" if k=="email" else "ll-done"}">{t[1]}</div>' for t,k in fb_lines2[-15:])
                fb_ph2.markdown(f'<div class="log-box">{h2}</div>',unsafe_allow_html=True)
            fb_found = scrape_facebook_page(fb_pages[0], fb_log)
            if fb_found:
                upd = sort_by_tier(set(r_sel.get("All Emails",[])) | fb_found)
                st.session_state.results[sel_domain]["All Emails"] = upd
                st.session_state.results[sel_domain]["Best Email"] = pick_best(set(upd)) or ""
            time.sleep(0.4); st.rerun()

        # run MX
        if sel_domain and st.session_state.get(f"mx_run_{sel_domain}") and DNS_AVAILABLE:
            st.session_state[f"mx_run_{sel_domain}"] = False
            mx_ph2=st.empty(); mx_l2=[]; new_mx={}
            for email in all_e_sel:
                res=check_mx(email); new_mx[email]=res; mx_l2.append((email,res))
                rh="".join(f'<div class="{"ll-email" if g else "ll-skip"}">{"✓" if g else "✗"} {e}</div>' for e,g in mx_l2)
                ok=sum(1 for _,g in mx_l2 if g)
                mx_ph2.markdown(f'<div class="log-box"><div style="color:#bbb;font-size:10px;margin-bottom:4px">MX — {ok}/{len(mx_l2)} valid</div>{rh}</div>',unsafe_allow_html=True)
            st.session_state.results[sel_domain]["MX"] = new_mx
            valid=[e for e in all_e_sel if new_mx.get(e) is not False]
            if len(valid)<len(all_e_sel): st.session_state.results[sel_domain]["All Emails"]=valid
            time.sleep(0.3); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  SCAN ENGINE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.scan_state == "running":
    queue = st.session_state.scan_queue
    idx   = st.session_state.scan_idx
    total = len(queue)
    if idx < total:
        url = queue[idx]
        if not url.startswith("http"): url = "https://"+url
        st.session_state.log_lines.append((("site",urlparse(url).netloc,None,None),"site"))
        row = scrape_one_site(url, cfg, st.session_state.skip_t1,
                              st.session_state.respect_robots, log_cb_factory(log_ph))
        st.session_state.results[row["Domain"]] = row
        st.session_state.scraped_domains.add(row["Domain"])
        st.session_state.scan_idx = idx+1
        time.sleep(cfg.get("delay",0.3))
        if st.session_state.scan_idx >= total:
            st.session_state.scan_state = "done"
        st.rerun()
    else:
        st.session_state.scan_state = "done"; st.rerun()

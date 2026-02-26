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

st.set_page_config(page_title="MailHunter", page_icon="✉️",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
#  CSS  — matches mockup exactly
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:       #fafaf9;
  --surface:  #ffffff;
  --border:   #e8e8e5;
  --border-2: #f0f0ed;
  --text:     #0f0f0e;
  --muted:    #8a8a82;
  --subtle:   #c4c4bc;
  --green:    #16a34a;  --green-bg: #f0fdf4;  --green-bd: #bbf7d0;
  --amber:    #d97706;  --amber-bg: #fffbeb;  --amber-bd: #fde68a;
  --red:      #dc2626;  --red-bg:   #fef2f2;  --red-bd:   #fecaca;
  --blue:     #2563eb;  --blue-bg:  #eff6ff;  --blue-bd:  #bfdbfe;
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* hide all Streamlit chrome */
#MainMenu, footer, header,
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }

/* remove default padding */
.block-container { padding: 0 !important; max-width: 100% !important; }
.main > div:first-child { padding: 0 !important; }

/* ── TOPBAR ── */
.topbar {
  height: 52px; background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; position: sticky; top: 0; z-index: 100;
}
.topbar-logo {
  font-size: 15px; font-weight: 800; letter-spacing: -0.4px;
  color: var(--text); display: flex; align-items: center; gap: 8px;
}
.topbar-dot {
  width: 8px; height: 8px; background: var(--text); border-radius: 50%;
}
.topbar-right { display: flex; align-items: center; gap: 6px; }
.tb-btn {
  height: 30px; padding: 0 12px; border-radius: 6px;
  font-size: 12.5px; font-weight: 600; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
  font-family: inherit; transition: all .15s; display: inline-flex;
  align-items: center; gap: 5px;
}
.tb-btn:hover { background: var(--bg); color: var(--text); }
.tb-btn-primary {
  background: var(--text) !important; color: white !important;
  border-color: var(--text) !important;
}
.tb-btn-primary:hover { background: #333 !important; }

/* ── TWO COLUMN LAYOUT ── */
.layout-row {
  display: flex; height: calc(100vh - 52px);
}

/* ── LEFT PANEL ── */
.left-panel {
  width: 320px; flex-shrink: 0;
  background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
}
.left-scroll { flex: 1; overflow-y: auto; padding: 20px; }
.left-footer {
  padding: 14px 20px; border-top: 1px solid var(--border-2);
  background: var(--surface);
}

/* ── RIGHT PANEL ── */
.right-panel {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
  background: var(--bg);
}
.metrics-row {
  display: grid; grid-template-columns: repeat(5, 1fr);
  background: var(--border); gap: 1px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.metric-cell {
  background: var(--surface); padding: 14px 20px;
}
.metric-val {
  font-size: 22px; font-weight: 800; letter-spacing: -0.5px;
  line-height: 1; color: var(--text);
}
.metric-lbl { font-size: 11px; color: var(--muted); margin-top: 3px; }

.table-toolbar {
  padding: 10px 16px; background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}
.right-scroll { flex: 1; overflow-y: auto; }

/* ── EMPTY STATE ── */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; gap: 12px; padding: 60px;
  text-align: center;
}
.empty-icon  { font-size: 32px; opacity: .25; }
.empty-title { font-size: 15px; font-weight: 700; color: var(--text); }
.empty-sub   { font-size: 13px; color: var(--muted); line-height: 1.6; max-width: 280px; }

/* ── SECTION LABEL ── */
.sec-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
  text-transform: uppercase; color: var(--subtle);
  margin-bottom: 8px; margin-top: 18px; display: block;
}
.sec-label:first-child { margin-top: 0; }

/* ── MODE PILLS ── */
.mode-pills {
  display: flex; gap: 3px; background: var(--bg);
  border: 1px solid var(--border); border-radius: 8px; padding: 3px;
}
.mode-pill {
  flex: 1; padding: 6px; border-radius: 6px; font-size: 12px;
  font-weight: 600; text-align: center; cursor: pointer;
  color: var(--muted); border: none; background: transparent;
  font-family: inherit; transition: all .15s;
}
.mode-pill.active {
  background: var(--surface); color: var(--text); font-weight: 700;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.mode-pill.easy.active   { color: var(--green); }
.mode-pill.medium.active { color: var(--amber); }
.mode-pill.extreme.active{ color: var(--red); }
.mode-desc { font-size: 11px; color: var(--muted); margin-top: 5px; }

/* ── SCAN PROGRESS ── */
.scan-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px; font-size: 12px;
}
.scan-label { font-weight: 700; display: flex; align-items: center; gap: 6px; }
.scan-dot {
  width: 6px; height: 6px; background: var(--green);
  border-radius: 50%; display: inline-block;
  animation: pulse 1.4s infinite;
}
.scan-dot.paused { background: var(--amber); animation: none; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.25} }
.progress-track {
  height: 3px; background: var(--border-2); border-radius: 99px; overflow: hidden; margin-bottom: 5px;
}
.progress-fill {
  height: 100%; background: var(--text); border-radius: 99px; transition: width .4s;
}
.scan-sub { font-size: 11px; color: var(--muted); display: flex; justify-content: space-between; }

/* ── LIVE LOG ── */
.live-log {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 12px;
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  max-height: 160px; overflow-y: auto; line-height: 2;
  margin-top: 10px;
}
.ll-row { display: flex; gap: 10px; }
.ll-time { color: var(--subtle); flex-shrink: 0; width: 32px; font-size: 10px; }
.ll-email { color: var(--green); font-weight: 600; }
.ll-page  { color: var(--muted); }
.ll-skip  { color: var(--amber); font-style: italic; }
.ll-done  { color: var(--subtle); }
.ll-info  { color: var(--subtle); font-style: italic; }
.ll-site  { color: var(--text); font-weight: 700; font-size: 11.5px; }
.ll-social{ color: var(--blue); }

/* ── URL PILLS ── */
.url-pills { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.url-pill {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 4px; padding: 2px 7px; color: var(--muted);
}

/* ── FILTER PILLS ── */
.filter-pill {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 10px; border-radius: 99px; font-size: 11.5px;
  font-weight: 600; border: 1px solid; cursor: pointer;
  transition: all .12s; white-space: nowrap;
}
.fp-all  { background:var(--surface); border-color:var(--border); color:var(--text); }
.fp-t1   { background:var(--green-bg); border-color:var(--green-bd); color:var(--green); }
.fp-t2   { background:var(--amber-bg); border-color:var(--amber-bd); color:var(--amber); }
.fp-t3   { background:var(--bg); border-color:var(--border); color:var(--muted); }
.fp-noemail { background:var(--red-bg); border-color:var(--red-bd); color:var(--red); }

/* ── BUTTONS ── */
.stButton > button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important; border-radius: 8px !important;
  font-size: 13px !important; letter-spacing: 0 !important;
  text-transform: none !important; transition: all .15s !important;
  height: 36px !important; padding: 0 16px !important;
}
.stButton > button[kind="primary"] {
  background: var(--text) !important; color: white !important;
  border: none !important; box-shadow: 0 1px 3px rgba(0,0,0,.15) !important;
}
.stButton > button[kind="primary"]:hover {
  background: #2a2a28 !important; transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:disabled {
  background: var(--border) !important; color: var(--subtle) !important;
  transform: none !important; box-shadow: none !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface) !important; color: var(--muted) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  color: var(--text) !important; border-color: var(--text) !important;
  background: var(--bg) !important;
}
.stDownloadButton > button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important; border-radius: 8px !important;
  font-size: 12.5px !important; height: 36px !important;
  background: var(--surface) !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; transition: all .15s !important;
}
.stDownloadButton > button:hover {
  border-color: var(--text) !important; background: var(--bg) !important;
}

/* ── INPUTS ── */
.stTextArea textarea, .stTextInput input {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important; background: var(--bg) !important;
  border: 1px solid var(--border) !important; border-radius: 8px !important;
  color: var(--text) !important; transition: border-color .15s, box-shadow .15s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--text) !important;
  box-shadow: 0 0 0 3px rgba(0,0,0,.06) !important;
}
.stTextArea textarea::placeholder,
.stTextInput input::placeholder { color: var(--subtle) !important; }

/* selects */
[data-baseweb="select"] > div {
  background: var(--bg) !important; border: 1px solid var(--border) !important;
  border-radius: 8px !important; color: var(--text) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 13px !important;
}
[data-baseweb="popover"] > div {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important; box-shadow: 0 8px 24px rgba(0,0,0,.1) !important;
  overflow: hidden !important;
}
[role="option"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 13px !important; padding: 9px 14px !important;
  background: var(--surface) !important; color: var(--text) !important;
}
[role="option"]:hover { background: var(--bg) !important; }

/* tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg) !important; border-radius: 0 !important;
  padding: 0 !important; gap: 0 !important;
  border-bottom: 1px solid var(--border-2) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; color: var(--muted) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 12.5px !important; font-weight: 500 !important;
  border-radius: 0 !important; padding: 8px 14px !important;
  border: none !important; border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text) !important; font-weight: 700 !important;
  border-bottom-color: var(--text) !important;
  background: transparent !important; box-shadow: none !important;
}
[data-testid="stTabsContent"] {
  padding: 12px 0 0 !important; border: none !important;
  background: transparent !important;
}

/* toggles + checkboxes */
label[data-testid="stWidgetLabel"] p {
  font-size: 12.5px !important; font-weight: 500 !important; color: var(--text) !important;
}
[data-testid="stCheckbox"] label span { font-size: 12.5px !important; }
.stCheckbox [data-testid="stMarkdownContainer"] p { font-size: 12.5px !important; }

/* dataframe */
[data-testid="stDataFrame"] iframe {
  border: none !important;
}

/* file uploader */
[data-testid="stFileUploader"] section {
  background: var(--bg) !important; border: 1px dashed var(--border) !important;
  border-radius: 8px !important;
}

/* metrics - kill default styling */
[data-testid="stMetric"] { background: transparent !important; padding: 0 !important; border: none !important; }
[data-testid="stMetricLabel"] { font-size: 11px !important; font-weight: 600 !important; color: var(--muted) !important; }
[data-testid="stMetricValue"] {
  font-size: 22px !important; font-weight: 800 !important;
  color: var(--text) !important; letter-spacing: -0.5px !important;
}

/* sliders */
[data-testid="stSlider"] > div > div > div {
  background: var(--text) !important;
}

/* scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

/* settings drawer */
.drawer-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.2);
  backdrop-filter: blur(2px); z-index: 200;
}
.drawer {
  position: fixed; top: 0; right: 0; width: 360px; height: 100vh;
  background: var(--surface); border-left: 1px solid var(--border);
  z-index: 201; display: flex; flex-direction: column;
  box-shadow: -8px 0 40px rgba(0,0,0,.1);
  overflow: hidden;
}
.drawer-header {
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.drawer-title { font-size: 14px; font-weight: 800; color: var(--text); }
.drawer-body  { flex: 1; overflow-y: auto; padding: 20px; }
.drawer-sec {
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
  text-transform: uppercase; color: var(--subtle);
  margin-bottom: 10px; margin-top: 20px; display: block;
}
.drawer-sec:first-child { margin-top: 0; }
.toggle-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid var(--border-2); gap: 12px;
}
.toggle-row:last-child { border-bottom: none; }
.toggle-info { flex: 1; }
.toggle-lbl  { font-size: 12.5px; font-weight: 600; color: var(--text); }
.toggle-desc { font-size: 11px; color: var(--muted); margin-top: 2px; }

/* tier badges in table */
.t1-badge { display:inline-flex;align-items:center;padding:2px 8px;border-radius:99px;
  font-size:11px;font-weight:700;background:var(--green-bg);
  border:1px solid var(--green-bd);color:var(--green); }
.t2-badge { display:inline-flex;align-items:center;padding:2px 8px;border-radius:99px;
  font-size:11px;font-weight:700;background:var(--amber-bg);
  border:1px solid var(--amber-bd);color:var(--amber); }
.t3-badge { display:inline-flex;align-items:center;padding:2px 8px;border-radius:99px;
  font-size:11px;font-weight:700;background:var(--bg);
  border:1px solid var(--border);color:var(--muted); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
TIER1 = re.compile(r"^(editor|admin|press|advert|contact)[a-z0-9._%+\-]*@", re.IGNORECASE)
TIER2 = re.compile(r"^(info|sales|hello|office|team|support|help)[a-z0-9._%+\-]*@", re.IGNORECASE)

BLOCKED_TLDS = {
    'png','jpg','jpeg','webp','gif','svg','ico','bmp','tiff','avif',
    'mp4','mp3','wav','ogg','mov','avi','webm','pdf','zip','rar','tar',
    'gz','7z','js','css','php','asp','aspx','xml','json','ts','jsx','tsx',
    'woff','woff2','ttf','eot','otf','map','exe','dmg','pkg','deb','apk',
}
PLACEHOLDER_DOMAINS = {
    'example.com','example.org','example.net','test.com','domain.com',
    'yoursite.com','yourwebsite.com','website.com','email.com',
    'sampleemail.com','mailtest.com','placeholder.com',
}
PLACEHOLDER_LOCALS = {
    'you','user','name','email','test','example','someone','username',
    'yourname','youremail','enter','address','sample',
}
SUPPRESS_PREFIXES = [
    'noreply','no-reply','donotreply','do-not-reply','mailer-daemon',
    'bounce','bounces','unsubscribe','notifications','notification',
    'newsletter','newsletters','postmaster','webmaster','auto-reply',
    'autoreply','daemon','robot','alerts','alert','system',
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
]
PRIORITY_PATHS = [
    "/contact","/contact-us","/contact_us","/contactus","/reach-us","/get-in-touch",
    "/about","/about-us","/about_us","/aboutus","/team","/our-team","/staff","/people",
    "/write-for-us","/writeforus","/guest-post","/guest-posts","/contribute",
    "/contributors","/submission","/submissions","/submit","/pitch",
    "/advertise","/advertise-with-us","/advertising","/work-with-us","/partner",
]
TWITTER_SKIP  = {'share','intent','home','search','hashtag','i','status','twitter','x'}
LINKEDIN_SKIP = {'share','shareArticle','in','company','pub','feed','login','authwall'}
FACEBOOK_SKIP = {'sharer','share','dialog','login','home','watch','groups','events','marketplace'}

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "results":         {},
    "scraped_domains": set(),
    "scan_state":      "idle",
    "scan_queue":      [],
    "scan_idx":        0,
    "log_lines":       [],
    "sessions":        [],
    "active_session":  None,
    "mode":            "Easy",
    "f_tier1":         True,
    "f_tier2":         True,
    "f_tier3":         True,
    "single_mode":     False,
    "skip_t1":         True,
    "respect_robots":  False,
    "scrape_fb":       False,
    "mx_cache":        {},
    "settings_open":   False,
    "tbl_filter":      "All",
    "tbl_search":      "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
#  CORE FUNCTIONS  — identical logic, unchanged
# ─────────────────────────────────────────────────────────────────────────────
def is_valid_email(email):
    e = email.strip()
    if not e or e.count('@') != 1: return False
    local, domain = e.split('@')
    lo, do = local.lower(), domain.lower()
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

def tier_short(email):
    return {"1":"Tier 1","2":"Tier 2","3":"Tier 3"}[tier_key(email)]

def tier_label(email):
    return {"1":"🥇 Tier 1","2":"🥈 Tier 2","3":"🥉 Tier 3"}[tier_key(email)]

def sort_by_tier(emails):
    return sorted(emails, key=lambda e: tier_key(e))

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
        if r.ok and "text" in r.headers.get("Content-Type",""):
            return r.text
    except: pass
    return None

def extract_emails(html):
    soup = BeautifulSoup(html, "html.parser")
    raw  = set()
    raw.update(EMAIL_REGEX.findall(soup.get_text(" ")))
    raw.update(EMAIL_REGEX.findall(html))
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            raw.add(a["href"][7:].split("?")[0].strip())
    return {e for e in raw if is_valid_email(e)}

def extract_social(html):
    soup = BeautifulSoup(html, "html.parser")
    tw, li, fb = set(), set(), set()
    for a in soup.find_all("a", href=True):
        href = a["href"]; hl = href.lower()
        if "twitter.com/" in hl or "x.com/" in hl:
            m = re.search(r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})', href)
            if m and m.group(1).lower() not in TWITTER_SKIP:
                tw.add("@"+m.group(1))
        elif "linkedin.com/in/" in hl or "linkedin.com/company/" in hl:
            m = re.search(r'linkedin\.com/(in|company)/([^/?&#\s]{2,80})', href)
            if m and m.group(2).lower() not in LINKEDIN_SKIP:
                li.add(f"linkedin.com/{m.group(1)}/{m.group(2)}")
        elif "facebook.com/" in hl and "facebook.com/tr?" not in hl:
            m = re.search(r'facebook\.com/([A-Za-z0-9_.]{3,80})', href)
            if m and m.group(1).lower() not in FACEBOOK_SKIP:
                fb.add(f"facebook.com/{m.group(1)}")
    return tw, li, fb

def get_internal_links(html, base_url, root_domain):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        p = urlparse(full)
        if p.netloc == root_domain and p.scheme in ("http","https"):
            links.append(full.split("#")[0].split("?")[0])
    return list(set(links))

def find_write_for_us_links(html, base_url, root_domain):
    WRITE_KEYWORDS = [
        "write for us","write-for-us","writeforus","guest post","guest-post",
        "contribute","submission","submissions","submit a","pitch us",
        "advertise","advertising","work with us","partner with",
        "become a contributor","become an author","write with us",
    ]
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for a in soup.find_all("a", href=True):
        href = a.get("href","")
        text = (a.get_text(" ",strip=True)+" "+href).lower()
        if any(kw in text for kw in WRITE_KEYWORDS):
            full = urljoin(base_url, href)
            p = urlparse(full)
            if p.netloc == root_domain and p.scheme in ("http","https"):
                found.append(full.split("#")[0].split("?")[0])
    return list(set(found))

def check_mx(email: str):
    if not DNS_AVAILABLE: return None
    domain = email.split("@")[1].lower()
    cache  = st.session_state.mx_cache
    if domain in cache: return cache[domain]
    try:
        records = _dns_resolver.resolve(domain, "MX", lifetime=4)
        result  = len(records) > 0
    except: result = False
    cache[domain] = result
    return result

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
    t0 = time.time()
    html = fetch_page(url, timeout=14)
    elapsed = round(time.time()-t0, 2)
    if html:
        found = extract_emails(html)
        for e in sort_by_tier(found):
            log_cb(("email", e, f"facebook.com/{slug}", tier_label(e)), "email")
        log_cb(("timing", f"{elapsed}s · {len(found)} email(s) from Facebook", url, None), "timing")
        return found
    else:
        log_cb(("timing", f"{elapsed}s · Facebook blocked", url, None), "timing")
        return set()

def fetch_sitemap_urls(root_url):
    urls = []
    for c in [urljoin(root_url,"/sitemap.xml"), urljoin(root_url,"/sitemap_index.xml")]:
        html = fetch_page(c)
        if not html: continue
        try:
            root_el = ET.fromstring(html)
            ns = {"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root_el.findall(".//sm:loc", ns):
                u = loc.text.strip()
                if u.endswith(".xml"):
                    sub = fetch_page(u)
                    if sub:
                        try:
                            sr = ET.fromstring(sub)
                            for sl in sr.findall(".//sm:loc", ns): urls.append(sl.text.strip())
                        except: pass
                else: urls.append(u)
        except: pass
        if urls: break
    return urls

def scrape_one_site(root_url, cfg, skip_t1, respect_robots, log_cb):
    t_start = time.time()
    parsed  = urlparse(root_url)
    root_domain = parsed.netloc
    visited, queue = set(), deque()
    all_emails = set()
    all_tw, all_li, all_fb = set(), set(), set()

    base = root_url.rstrip("/")
    rp   = load_robots(root_url, respect_robots)

    for path in PRIORITY_PATHS:
        queue.append((base+path, 0, True))
    queue.append((root_url, 0, False))

    if cfg.get("sitemap"):
        sm_urls = fetch_sitemap_urls(root_url)
        log_cb(("info", f"{len(sm_urls)} URLs in sitemap", None, None), "info")
        for u in sm_urls[:cfg["max_pages"]]: queue.append((u, 0, False))

    max_pages = cfg["max_pages"]; max_depth = cfg["max_depth"]; pages_done = 0

    while queue and pages_done < max_pages + len(PRIORITY_PATHS):
        url, depth, is_priority = queue.popleft()
        if url in visited: continue
        visited.add(url)
        label = "priority" if is_priority else f"{pages_done+1}/{max_pages}"
        short = url.replace("https://","").replace("http://","")
        t_page = time.time()

        if not robots_allowed(rp, url):
            log_cb(("timing", f"robots.txt blocked — {short}", url, None), "timing")
            if not is_priority: pages_done += 1
            continue

        log_cb(("page_start", short, label, None), "active")
        html    = fetch_page(url)
        elapsed = round(time.time()-t_page, 2)

        if html:
            found = extract_emails(html)
            new_emails = found - all_emails
            tw, li, fb = extract_social(html)
            all_emails.update(found)
            all_tw.update(tw); all_li.update(li); all_fb.update(fb)

            # Write-for-us link hunting
            for wlink in find_write_for_us_links(html, url, root_domain):
                if wlink not in visited:
                    queue.appendleft((wlink, 0, True))
                    log_cb(("info", f"write-for-us → {wlink.replace('https://','')}", None, None), "info")

            for email in sort_by_tier(new_emails):
                log_cb(("email", email, short, tier_label(email)), "email")
            for handle in sorted((tw-all_tw)|(li-all_li)|(fb-all_fb)):
                log_cb(("social", handle, short, None), "social")
            log_cb(("timing", f"{elapsed}s · {len(new_emails)} new email(s)", short, None), "timing")

            if not is_priority and depth < max_depth:
                for link in get_internal_links(html, url, root_domain):
                    if link not in visited: queue.append((link, depth+1, False))

            if skip_t1 and any(TIER1.match(e) for e in all_emails):
                t1e = next(e for e in all_emails if TIER1.match(e))
                log_cb(("skip", f"Tier 1 found ({t1e}) — skipping {root_domain}", None, None), "skip")
                break
        else:
            log_cb(("timing", f"{elapsed}s · no response", short, None), "timing")

        if not is_priority: pages_done += 1

    total_time = round(time.time()-t_start, 1)

    if st.session_state.get("scrape_fb") and all_fb:
        primary_fb = sorted(all_fb)[0]
        log_cb(("info", f"Auto-scraping Facebook: {primary_fb}", None, None), "info")
        fb_emails = scrape_facebook_page(primary_fb, log_cb)
        all_emails.update(fb_emails)

    sorted_emails = sort_by_tier(all_emails)
    best = pick_best(all_emails)
    log_cb(("done", f"{root_domain} — {len(all_emails)} email(s) in {total_time}s", None, None), "done")

    return {
        "Domain":        root_domain,
        "Best Email":    best or "",
        "Best Tier":     tier_short(best) if best else "",
        "All Emails":    sorted_emails,
        "Twitter":       sorted(all_tw),
        "LinkedIn":      sorted(all_li),
        "Facebook":      sorted(all_fb),
        "Pages Scraped": pages_done,
        "Total Time":    total_time,
        "Source URL":    root_url,
        "MX":            {},
    }

# ─────────────────────────────────────────────────────────────────────────────
#  LOG RENDERER
# ─────────────────────────────────────────────────────────────────────────────
def render_log(ph):
    lines_html = ""
    email_count = sum(1 for _, k in st.session_state.log_lines if k == "email")
    for item, kind in st.session_state.log_lines[-40:]:
        event, text, page, extra = item
        if kind == "site":
            lines_html += f'<div class="ll-row"><span class="ll-site">▶ {text}</span></div>'
        elif kind == "active":
            lines_html += f'<div class="ll-row"><span class="ll-page">↳ [{extra or ""}] {text}</span></div>'
        elif kind == "email":
            lines_html += f'<div class="ll-row"><span class="ll-email">✉ {text}</span></div>'
        elif kind == "social":
            lines_html += f'<div class="ll-row"><span class="ll-social">⟐ {text}</span></div>'
        elif kind == "timing":
            lines_html += f'<div class="ll-row"><span class="ll-done">⏱ {text}</span></div>'
        elif kind == "skip":
            lines_html += f'<div class="ll-row"><span class="ll-skip">⚡ {text}</span></div>'
        elif kind == "done":
            lines_html += f'<div class="ll-row"><span class="ll-done">✓ {text}</span></div>'
        elif kind == "info":
            lines_html += f'<div class="ll-row"><span class="ll-info">· {text}</span></div>'

    total_line = (f'<div style="border-bottom:1px solid var(--border-2);margin-bottom:6px;'
                  f'padding-bottom:6px;font-size:10px;color:var(--subtle);letter-spacing:.5px">'
                  f'LIVE LOG · {email_count} EMAIL(S) FOUND</div>') if st.session_state.log_lines else ""
    ph.markdown(f'<div class="live-log">{total_line}{lines_html}</div>', unsafe_allow_html=True)

def log_cb_factory(ph):
    def log_cb(item, kind):
        st.session_state.log_lines.append((item, kind))
        render_log(ph)
    return log_cb

# ─────────────────────────────────────────────────────────────────────────────
#  TOPBAR
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <div class="topbar-logo">
    <div class="topbar-dot"></div>
    MailHunter
  </div>
  <div class="topbar-right" id="topbar-right"></div>
</div>
""", unsafe_allow_html=True)

# Topbar buttons rendered as Streamlit buttons in a tight column row
tb1, tb2, tb3, tb4, tb_space = st.columns([1, 1, 1, 1, 6])
with tb1:
    if st.button("⚙ Settings", key="open_settings", type="secondary", use_container_width=True):
        st.session_state.settings_open = not st.session_state.settings_open
        st.rerun()
with tb2:
    if st.button("Sessions", key="open_sessions", type="secondary", use_container_width=True):
        st.session_state.settings_open = False
        st.session_state.show_sessions = not st.session_state.get("show_sessions", False)
        st.rerun()
with tb3:
    # Export CSV
    if st.session_state.results:
        csv_rows = []
        for domain, r in st.session_state.results.items():
            csv_rows.append({
                "Domain": domain, "Best Email": r.get("Best Email",""),
                "All Emails": "; ".join(r.get("All Emails",[])),
                "Twitter": "; ".join(r.get("Twitter",[])),
                "LinkedIn": "; ".join(r.get("LinkedIn",[])),
                "Facebook": "; ".join(r.get("Facebook",[])),
                "Pages": r.get("Pages Scraped",0), "Time(s)": r.get("Total Time",""),
                "MX": "; ".join(f"{e}={'ok' if v else 'no-mx'}"
                                for e,v in r.get("MX",{}).items() if v is not None),
                "Source URL": r.get("Source URL",""),
            })
        buf = io.StringIO()
        pd.DataFrame(csv_rows).to_csv(buf, index=False)
        st.download_button("Export CSV", buf.getvalue(),
                           f"mailhunter_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           "text/csv", key="export_csv", use_container_width=True)
    else:
        st.button("Export CSV", key="export_csv_disabled", type="secondary",
                  disabled=True, use_container_width=True)
with tb4:
    if st.session_state.results:
        if st.button("Save", key="save_session_tb", type="secondary", use_container_width=True):
            ts   = datetime.now().strftime("%b %d %H:%M")
            name = f"Scan {len(st.session_state.sessions)+1} · {ts}"
            st.session_state.sessions.append({
                "name": name, "ts": ts,
                "results": dict(st.session_state.results),
            })
            st.session_state.active_session = name
            st.rerun()
    else:
        st.button("Save", key="save_disabled", type="secondary", disabled=True, use_container_width=True)

# Push topbar buttons to top with CSS
st.markdown("""
<style>
/* Reposition topbar buttons into the topbar */
[data-testid="stHorizontalBlock"]:first-of-type {
  position: fixed !important;
  top: 10px !important;
  right: 20px !important;
  z-index: 1000 !important;
  width: auto !important;
  gap: 6px !important;
  background: transparent !important;
}
[data-testid="stHorizontalBlock"]:first-of-type > div {
  width: auto !important;
  min-width: 0 !important;
  flex: 0 0 auto !important;
}
[data-testid="stHorizontalBlock"]:first-of-type > div:last-child {
  display: none !important;
}
[data-testid="stHorizontalBlock"]:first-of-type button,
[data-testid="stHorizontalBlock"]:first-of-type .stDownloadButton button {
  height: 30px !important; padding: 0 12px !important;
  font-size: 12.5px !important; border-radius: 6px !important;
  white-space: nowrap !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS DRAWER
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.settings_open:
    st.markdown('<div class="drawer-overlay"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="drawer"><div class="drawer-header"><span class="drawer-title">Settings</span></div><div class="drawer-body">', unsafe_allow_html=True)
        st.markdown('<span class="drawer-sec">Behaviour</span>', unsafe_allow_html=True)

        dr1, dr2 = st.columns([3,1])
        with dr1:
            st.markdown('<div class="toggle-lbl">Best email per site only</div>'
                        '<div class="toggle-desc">Pick one winner per domain using tier priority</div>',
                        unsafe_allow_html=True)
        with dr2:
            st.session_state.single_mode = st.toggle("", value=st.session_state.single_mode,
                                                       key="t_single", label_visibility="collapsed")

        dr1, dr2 = st.columns([3,1])
        with dr1:
            st.markdown('<div class="toggle-lbl">Skip site once Tier 1 found</div>'
                        '<div class="toggle-desc">Stop crawling when top-tier email found</div>',
                        unsafe_allow_html=True)
        with dr2:
            st.session_state.skip_t1 = st.toggle("", value=st.session_state.skip_t1,
                                                   key="t_skip", label_visibility="collapsed")

        dr1, dr2 = st.columns([3,1])
        with dr1:
            st.markdown('<div class="toggle-lbl">Respect robots.txt</div>'
                        '<div class="toggle-desc">Honour disallow rules — polite but may miss pages</div>',
                        unsafe_allow_html=True)
        with dr2:
            st.session_state.respect_robots = st.toggle("", value=st.session_state.respect_robots,
                                                          key="t_robots", label_visibility="collapsed")

        st.markdown('<span class="drawer-sec">Extra Sources</span>', unsafe_allow_html=True)
        dr1, dr2 = st.columns([3,1])
        with dr1:
            st.markdown('<div class="toggle-lbl">Auto-scrape Facebook page</div>'
                        '<div class="toggle-desc">Fetch the linked FB page after each site crawl</div>',
                        unsafe_allow_html=True)
        with dr2:
            st.session_state.scrape_fb = st.toggle("", value=st.session_state.scrape_fb,
                                                     key="t_fb", label_visibility="collapsed")

        st.markdown('<span class="drawer-sec">Tier Filters</span>', unsafe_allow_html=True)
        st.session_state.f_tier1 = st.checkbox("🥇 Tier 1 — editor / admin / press",
                                                 value=st.session_state.f_tier1, key="cb_t1")
        st.session_state.f_tier2 = st.checkbox("🥈 Tier 2 — info / sales / support",
                                                 value=st.session_state.f_tier2, key="cb_t2")
        st.session_state.f_tier3 = st.checkbox("🥉 Tier 3 — other valid emails",
                                                 value=st.session_state.f_tier3, key="cb_t3")

        st.markdown('<span class="drawer-sec">Domain Memory</span>', unsafe_allow_html=True)
        n_dedup = len(st.session_state.scraped_domains)
        st.caption(f"{n_dedup} domain(s) in memory — already-scraped sites are skipped.")
        if n_dedup:
            if st.button("Clear memory", type="secondary", key="clear_dedup"):
                st.session_state.scraped_domains = set()
                st.rerun()

        if st.session_state.get("show_sessions") and st.session_state.sessions:
            st.markdown('<span class="drawer-sec">Saved Sessions</span>', unsafe_allow_html=True)
            for i, sess in enumerate(st.session_state.sessions):
                total_e = sum(len(r.get("All Emails",[])) for r in sess["results"].values())
                sc1, sc2, sc3 = st.columns([3,1,1])
                with sc1:
                    st.markdown(f'<div class="toggle-lbl">{sess["name"]}</div>'
                                f'<div class="toggle-desc">{len(sess["results"])} domains · {total_e} emails</div>',
                                unsafe_allow_html=True)
                with sc2:
                    if st.button("Load", key=f"load_{i}", type="secondary", use_container_width=True):
                        st.session_state.results        = sess["results"]
                        st.session_state.active_session = sess["name"]
                        st.session_state.scan_state     = "done"
                        st.session_state.settings_open  = False
                        st.rerun()
                with sc3:
                    if st.button("Del", key=f"del_{i}", type="secondary", use_container_width=True):
                        st.session_state.sessions.pop(i)
                        st.rerun()

        if st.button("Close Settings", type="primary", key="close_settings"):
            st.session_state.settings_open = False
            st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSIONS PANEL (standalone if not in settings)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.get("show_sessions") and not st.session_state.settings_open:
    if st.session_state.sessions:
        with st.container():
            st.markdown('<div style="background:var(--surface);border:1px solid var(--border);'
                        'border-radius:10px;padding:16px 20px;margin-bottom:12px;">', unsafe_allow_html=True)
            for i, sess in enumerate(st.session_state.sessions):
                total_e = sum(len(r.get("All Emails",[])) for r in sess["results"].values())
                sc1, sc2, sc3 = st.columns([4,1,1])
                with sc1:
                    st.markdown(f'**{sess["name"]}** — {len(sess["results"])} domains · {total_e} emails',
                                unsafe_allow_html=False)
                with sc2:
                    if st.button("Load", key=f"sess_load_{i}", type="secondary", use_container_width=True):
                        st.session_state.results = sess["results"]
                        st.session_state.active_session = sess["name"]
                        st.session_state.scan_state = "done"
                        st.rerun()
                with sc3:
                    if st.button("Del", key=f"sess_del_{i}", type="secondary", use_container_width=True):
                        st.session_state.sessions.pop(i)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN LAYOUT  — Left panel + Right panel
# ─────────────────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2.5], gap="small")

# shared config derived from settings
mode_key = st.session_state.mode
cfg = {
    "Easy":    {"max_pages":1,   "max_depth":0, "sitemap":False, "delay":0.3},
    "Medium":  {"max_pages":50,  "max_depth":3, "sitemap":False, "delay":0.5},
    "Extreme": {"max_pages":300, "max_depth":6, "sitemap":True,  "delay":0.3},
}[mode_key].copy()

# ── LEFT PANEL ────────────────────────────────────────────────────────────────
with left_col:
    st.markdown('<style>[data-testid="column"]:first-of-type{background:white;border-right:1px solid #e8e8e5;min-height:calc(100vh - 52px);padding:20px !important;}</style>', unsafe_allow_html=True)

    # URL INPUT
    st.markdown('<span class="sec-label">Target URLs</span>', unsafe_allow_html=True)
    tab_paste, tab_upload = st.tabs(["Paste", "Upload CSV / TXT"])
    urls_to_scrape = []

    with tab_paste:
        raw = st.text_area("", placeholder="https://magazine.com\nhttps://techblog.io\nnewspaper.org",
                           height=120, label_visibility="collapsed", key="url_input")
        if raw.strip():
            for line in raw.splitlines():
                line = line.strip()
                if not line: continue
                if not line.startswith("http"): line = "https://"+line
                urls_to_scrape.append(line)

    with tab_upload:
        uploaded = st.file_uploader("", type=["csv","txt"], label_visibility="collapsed")
        if uploaded:
            raw_bytes = uploaded.read()
            if uploaded.name.endswith(".csv"):
                try:
                    df_up  = pd.read_csv(io.BytesIO(raw_bytes))
                    cols_u = list(df_up.columns)
                    hints  = ["url","link","website","site","domain","href"]
                    defcol = next((c for c in cols_u if any(h in c.lower() for h in hints)), cols_u[0])
                    sel    = st.selectbox("URL column", cols_u, index=cols_u.index(defcol))
                    for u in df_up[sel].dropna().astype(str):
                        u = u.strip()
                        if not u.startswith("http"): u = "https://"+u
                        urls_to_scrape.append(u)
                    st.caption(f"✓ {len(urls_to_scrape)} URLs loaded")
                except Exception as ex:
                    st.error(f"CSV error: {ex}")
            else:
                for line in raw_bytes.decode("utf-8").splitlines():
                    line = line.strip()
                    if not line: continue
                    if not line.startswith("http"): line = "https://"+line
                    urls_to_scrape.append(line)
                st.caption(f"✓ {len(urls_to_scrape)} URLs loaded")

    if urls_to_scrape:
        pills = "".join(
            f'<span class="url-pill">{u.replace("https://","").replace("http://","")[:32]}</span>'
            for u in urls_to_scrape[:8])
        if len(urls_to_scrape) > 8:
            pills += f'<span class="url-pill">+{len(urls_to_scrape)-8} more</span>'
        st.markdown(f'<div class="url-pills">{pills}</div>', unsafe_allow_html=True)

    # MODE
    st.markdown('<span class="sec-label" style="margin-top:18px;">Mode</span>', unsafe_allow_html=True)
    mode_descs = {"Easy":"Homepage only · fast","Medium":"Crawl links · thorough","Extreme":"Sitemap + deep · exhaustive"}
    mc1, mc2, mc3 = st.columns(3)
    for col, m in zip([mc1, mc2, mc3], ["Easy","Medium","Extreme"]):
        with col:
            is_active = st.session_state.mode == m
            if st.button(m, key=f"mode_{m}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                st.session_state.mode = m
                st.rerun()
    st.caption(mode_descs[mode_key])

    if mode_key == "Medium":
        cfg["max_depth"] = st.slider("Crawl depth", 1, 5, 3, key="depth_s")
        cfg["max_pages"] = st.slider("Max pages per site", 10, 200, 50, key="pages_s")
    elif mode_key == "Extreme":
        cfg["max_pages"] = st.slider("Max pages per site", 50, 500, 300, key="pages_x")

    # SCAN PROGRESS (shown when scanning or paused)
    scan_state = st.session_state.scan_state
    prog_ph = st.empty()
    log_ph  = st.empty()

    if scan_state in ("running","paused","done") and st.session_state.log_lines:
        render_log(log_ph)

    if scan_state in ("running","paused"):
        idx   = st.session_state.scan_idx
        total = len(st.session_state.scan_queue)
        pct   = idx / total if total else 0
        dot_cls = "scan-dot paused" if scan_state == "paused" else "scan-dot"
        prog_ph.markdown(f"""
        <div style="margin-top:14px">
          <div class="scan-header">
            <span class="scan-label">
              <span class="{dot_cls}"></span>
              {"Paused" if scan_state=="paused" else "Scanning…"}
            </span>
            <span style="font-size:11px;color:var(--muted)">{idx} / {total}</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width:{pct*100:.1f}%"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ACTION BUTTONS
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns([2, 1, 1])
    with a1:
        if scan_state == "idle":
            start_btn = st.button("Start Scan", type="primary", use_container_width=True,
                                  disabled=not urls_to_scrape, key="start")
        elif scan_state == "running":
            start_btn = False
            if st.button("Pause", type="primary", use_container_width=True, key="pause"):
                st.session_state.scan_state = "paused"
                st.rerun()
        elif scan_state == "paused":
            start_btn = False
            if st.button("Resume", type="primary", use_container_width=True, key="resume"):
                st.session_state.scan_state = "running"
                st.rerun()
        else:
            start_btn = st.button("New Scan", type="primary", use_container_width=True,
                                  disabled=not urls_to_scrape, key="new_scan")
    with a2:
        pass  # save is in topbar
    with a3:
        if st.button("Clear", type="secondary", use_container_width=True, key="clear"):
            for k in ["results","scan_queue","log_lines"]:
                st.session_state[k] = {} if k == "results" else []
            st.session_state.scan_state     = "idle"
            st.session_state.scan_idx       = 0
            st.session_state.active_session = None
            st.rerun()

    # Start scan logic
    if "start_btn" in dir() and start_btn and urls_to_scrape:
        new_urls, skipped = [], []
        for u in urls_to_scrape:
            d = urlparse(u if u.startswith("http") else "https://"+u).netloc
            if d in st.session_state.scraped_domains: skipped.append(d)
            else: new_urls.append(u)
        if skipped:
            st.info(f"Skipping {len(skipped)} already-scraped domain(s).")
        if new_urls:
            st.session_state.scan_queue  = new_urls
            st.session_state.scan_idx    = 0
            st.session_state.scan_state  = "running"
            st.session_state.log_lines   = []
            if scan_state == "done":  # new scan clears results
                st.session_state.results = {}
            st.rerun()

# ── RIGHT PANEL ───────────────────────────────────────────────────────────────
with right_col:
    results    = st.session_state.results
    scan_state = st.session_state.scan_state

    if not results:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">✉</div>
          <div class="empty-title">No results yet</div>
          <div class="empty-sub">Paste URLs in the panel on the left, choose a mode, and hit Start Scan.</div>
        </div>""", unsafe_allow_html=True)
    else:
        # METRICS
        tot_d  = len(results)
        tot_e  = sum(len(r.get("All Emails",[])) for r in results.values())
        t1_cnt = sum(1 for r in results.values() if r.get("Best Tier","").startswith("Tier 1"))
        mx_ok  = sum(1 for r in results.values()
                     for v in r.get("MX",{}).values() if v is True)
        no_e   = sum(1 for r in results.values() if not r.get("Best Email"))

        st.markdown(f"""
        <div class="metrics-row">
          <div class="metric-cell">
            <div class="metric-val">{tot_d}</div>
            <div class="metric-lbl">domains</div>
          </div>
          <div class="metric-cell">
            <div class="metric-val">{tot_e}</div>
            <div class="metric-lbl">emails found</div>
          </div>
          <div class="metric-cell">
            <div class="metric-val">{t1_cnt}</div>
            <div class="metric-lbl">Tier 1 hits</div>
          </div>
          <div class="metric-cell">
            <div class="metric-val">{mx_ok}</div>
            <div class="metric-lbl">MX verified</div>
          </div>
          <div class="metric-cell">
            <div class="metric-val">{no_e}</div>
            <div class="metric-lbl">no email</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # TOOLBAR
        tf1, tf2, tf3, tf4, tf5, tf6 = st.columns([2.5, 1, 1, 1, 1, 1])
        with tf1:
            search = st.text_input("", placeholder="Search domain or email…",
                                   label_visibility="collapsed", key="search_input")
        with tf2:
            f_all = st.button(f"All {tot_e}", key="f_all", type="primary" if st.session_state.tbl_filter=="All" else "secondary", use_container_width=True)
        with tf3:
            f_t1 = st.button("Tier 1", key="f_t1", type="primary" if st.session_state.tbl_filter=="T1" else "secondary", use_container_width=True)
        with tf4:
            f_t2 = st.button("Tier 2", key="f_t2", type="primary" if st.session_state.tbl_filter=="T2" else "secondary", use_container_width=True)
        with tf5:
            f_t3 = st.button("Tier 3", key="f_t3", type="primary" if st.session_state.tbl_filter=="T3" else "secondary", use_container_width=True)
        with tf6:
            f_no = st.button("No email", key="f_no", type="primary" if st.session_state.tbl_filter=="None" else "secondary", use_container_width=True)

        if f_all: st.session_state.tbl_filter = "All";  st.rerun()
        if f_t1:  st.session_state.tbl_filter = "T1";   st.rerun()
        if f_t2:  st.session_state.tbl_filter = "T2";   st.rerun()
        if f_t3:  st.session_state.tbl_filter = "T3";   st.rerun()
        if f_no:  st.session_state.tbl_filter = "None"; st.rerun()

        # BUILD TABLE DATA
        tier_filter = []
        if st.session_state.f_tier1: tier_filter.append("1")
        if st.session_state.f_tier2: tier_filter.append("2")
        if st.session_state.f_tier3: tier_filter.append("3")

        rows = []
        for domain, r in results.items():
            all_e = r.get("All Emails",[])
            best  = r.get("Best Email","")
            bt    = r.get("Best Tier","")

            # Apply tier filter
            if st.session_state.single_mode:
                disp_emails = best or ""
            else:
                filtered    = [e for e in all_e if tier_key(e) in tier_filter]
                disp_emails = "; ".join(filtered)

            # Count extra emails
            extra = len(all_e) - 1 if len(all_e) > 1 else 0
            emails_disp = best + (f"  +{extra}" if extra else "") if best else "—"

            # MX status
            mx_data = r.get("MX",{})
            if mx_data:
                mx_vals = list(mx_data.values())
                ok = sum(1 for v in mx_vals if v is True)
                mx_disp = f"✓ {ok}/{len(mx_vals)}"
            else:
                mx_disp = "—"

            tw = ", ".join(r.get("Twitter",[])[:2]) or "—"
            li = ", ".join(r.get("LinkedIn",[])[:1]) or "—"
            fb = ", ".join(r.get("Facebook",[])[:1]) or "—"

            rows.append({
                "Domain":   domain,
                "Best Email": best or "—",
                "Tier":     bt or "—",
                "All Emails": disp_emails or "—",
                "MX":       mx_disp,
                "Twitter":  tw,
                "LinkedIn": li,
                "Facebook": fb,
                "Pages":    r.get("Pages Scraped",0),
                "Time(s)":  r.get("Total Time","—"),
            })

        df = pd.DataFrame(rows)

        # Apply search filter
        if search:
            mask = (df["Domain"].str.contains(search, case=False, na=False) |
                    df["Best Email"].str.contains(search, case=False, na=False) |
                    df["All Emails"].str.contains(search, case=False, na=False))
            df = df[mask]

        # Apply tier/status filter
        filt = st.session_state.tbl_filter
        if filt == "T1":   df = df[df["Tier"].str.startswith("Tier 1", na=False)]
        elif filt == "T2": df = df[df["Tier"].str.startswith("Tier 2", na=False)]
        elif filt == "T3": df = df[df["Tier"].str.startswith("Tier 3", na=False)]
        elif filt == "None": df = df[df["Best Email"] == "—"]

        st.caption(f"{len(df)} of {tot_d} domains")

        st.dataframe(
            df, use_container_width=True, hide_index=True,
            height=max(200, min(600, 44 + len(df)*35)),
            column_config={
                "Domain":     st.column_config.TextColumn("Domain",     width=160),
                "Best Email": st.column_config.TextColumn("Best Email", width=200),
                "Tier":       st.column_config.TextColumn("Tier",       width=80),
                "All Emails": st.column_config.TextColumn("All Emails", width=220),
                "MX":         st.column_config.TextColumn("MX",         width=70),
                "Twitter":    st.column_config.TextColumn("Twitter",    width=130),
                "LinkedIn":   st.column_config.TextColumn("LinkedIn",   width=140),
                "Facebook":   st.column_config.TextColumn("Facebook",   width=140),
                "Pages":      st.column_config.NumberColumn("Pages",    width=60),
                "Time(s)":    st.column_config.NumberColumn("Time(s)",  width=70),
            }
        )

        # Per-domain actions (FB + MX verify)
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        act_lbl, act_domain, act_btn1, act_btn2 = st.columns([0.8, 2, 1.2, 1.2])
        with act_lbl:
            st.caption("Actions for:")
        with act_domain:
            domains_with_fb = [d for d, r in results.items() if r.get("Facebook")]
            all_domains = list(results.keys())
            sel_domain = st.selectbox("", all_domains, label_visibility="collapsed",
                                      key="action_domain")
        with act_btn1:
            r_sel = results.get(sel_domain, {})
            fb_pages = r_sel.get("Facebook",[])
            if fb_pages:
                if st.button("Scrape Facebook", key="fb_action", type="secondary", use_container_width=True):
                    st.session_state[f"fb_run_{sel_domain}"] = True
                    st.rerun()
            else:
                st.button("Scrape Facebook", key="fb_action_dis", type="secondary",
                          disabled=True, use_container_width=True)
        with act_btn2:
            if DNS_AVAILABLE and r_sel.get("All Emails"):
                if st.button("Verify MX", key="mx_action", type="secondary", use_container_width=True):
                    st.session_state[f"mx_run_{sel_domain}"] = True
                    st.rerun()
            else:
                st.button("Verify MX", key="mx_action_dis", type="secondary",
                          disabled=True, use_container_width=True)

        # Run Facebook scrape for selected domain
        if sel_domain and st.session_state.get(f"fb_run_{sel_domain}"):
            st.session_state[f"fb_run_{sel_domain}"] = False
            fb_ph  = st.empty()
            fb_lines = []
            def fb_log_fn(item, kind):
                fb_lines.append((item, kind))
                html_lines = "".join(
                    f'<div class="{"ll-email" if k=="email" else "ll-done"}">{t[1]}</div>'
                    for t, k in fb_lines[-15:]
                )
                fb_ph.markdown(f'<div class="live-log">{html_lines}</div>', unsafe_allow_html=True)

            fb_emails = scrape_facebook_page(fb_pages[0], fb_log_fn)
            if fb_emails:
                r_sel_cur = st.session_state.results[sel_domain]
                updated = sort_by_tier(set(r_sel_cur.get("All Emails",[])) | fb_emails)
                st.session_state.results[sel_domain]["All Emails"] = updated
                best = pick_best(set(updated))
                st.session_state.results[sel_domain]["Best Email"] = best or ""
            time.sleep(0.4)
            st.rerun()

        # Run MX verification for selected domain
        if sel_domain and st.session_state.get(f"mx_run_{sel_domain}") and DNS_AVAILABLE:
            st.session_state[f"mx_run_{sel_domain}"] = False
            mx_ph    = st.empty()
            mx_lines = []
            new_mx   = {}
            all_e_sel = results[sel_domain].get("All Emails",[])
            for email in all_e_sel:
                result = check_mx(email)
                new_mx[email] = result
                mx_lines.append((email, result))
                rows_html = "".join(
                    f'<div class="{"ll-email" if g else "ll-skip"}">'
                    f'{"✓" if g else "✗"} {e}</div>'
                    for e, g in mx_lines
                )
                ok_count = sum(1 for _, g in mx_lines if g)
                mx_ph.markdown(
                    f'<div class="live-log"><div style="font-size:10px;color:var(--subtle);'
                    f'margin-bottom:6px">MX VERIFICATION — {ok_count}/{len(mx_lines)} valid</div>'
                    f'{rows_html}</div>', unsafe_allow_html=True)

            st.session_state.results[sel_domain]["MX"] = new_mx
            # Remove confirmed no-MX emails
            valid = [e for e in all_e_sel if new_mx.get(e) is not False]
            if len(valid) < len(all_e_sel):
                st.session_state.results[sel_domain]["All Emails"] = valid
            time.sleep(0.3)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  SCAN ENGINE  — one site per rerun, writes into left panel log
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.scan_state == "running":
    queue = st.session_state.scan_queue
    idx   = st.session_state.scan_idx
    total = len(queue)

    if idx < total:
        url = queue[idx]
        if not url.startswith("http"): url = "https://"+url

        # Append site header to log
        domain_short = urlparse(url).netloc
        st.session_state.log_lines.append(
            (("site", domain_short, None, None), "site"))

        # Use the log_ph placeholder created earlier in left_col
        # (it renders inside the left column due to Streamlit's sequential rendering)
        cb = log_cb_factory(log_ph)
        row = scrape_one_site(url, cfg,
                              st.session_state.skip_t1,
                              st.session_state.respect_robots, cb)

        st.session_state.results[row["Domain"]] = row
        st.session_state.scraped_domains.add(row["Domain"])
        st.session_state.scan_idx = idx + 1

        time.sleep(cfg.get("delay", 0.3))

        if st.session_state.scan_idx >= total:
            st.session_state.scan_state = "done"
        st.rerun()
    else:
        st.session_state.scan_state = "done"
        st.rerun()

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re, io, time, xml.etree.ElementTree as ET, random, pandas as pd, urllib.robotparser
import smtplib, socket
from urllib.parse import urljoin, urlparse
from email_validator import validate_email as ev_validate, EmailNotValidError
from collections import deque
from datetime import datetime

try:
    import dns.resolver as _dns_resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

# ── DISPOSABLE DOMAIN LIST ────────────────────────────────────────────────────
_DISPOSABLE_FALLBACK = {
    'mailinator.com','guerrillamail.com','tempmail.com','throwaway.email','yopmail.com',
    'sharklasers.com','spam4.me','trashmail.com','trashmail.me','maildrop.cc',
    '10minutemail.com','fakeinbox.com','discard.email','mailnesia.com','mohmal.com',
    'tempr.email','trashmail.at','trashmail.io','wegwerfemail.de','meltmail.com',
}

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_disposable_domains():
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf",
            timeout=8)
        if r.status_code == 200:
            return set(r.text.splitlines())
    except Exception:
        pass
    return _DISPOSABLE_FALLBACK

FREE_EMAIL_DOMAINS = {"gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com",
                      "icloud.com","protonmail.com","zoho.com","live.com","msn.com"}

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MailHunter", page_icon="✉", layout="wide",
                   initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;1,14..32,400&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
.block-container { padding: 1.5rem 2rem 4rem !important; max-width: 100% !important; background: #f8f8f6 !important; }

/* ── logo ── */
.logo {
    font-size: 20px; font-weight: 800; color: #0f0f0f;
    letter-spacing: -0.5px; line-height: 1;
    display: inline-flex; align-items: center; gap: 10px;
}
.logo-icon {
    width: 28px; height: 28px; background: #0f0f0f; border-radius: 7px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 14px; color: #fff; flex-shrink: 0;
}

/* ── left panel card ── */
[data-testid="column"]:first-of-type > div > div > div {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 14px;
    padding: 1.25rem 1.25rem 1rem !important;
}

/* ── section label ── */
.lbl {
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #b0b0b0; display: block; margin-bottom: 6px;
}

/* ── all buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    transition: all 0.15s ease !important;
    height: 38px !important;
    letter-spacing: -0.1px !important;
}
.stButton > button[kind="primary"] {
    background: #0f0f0f !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.2) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #2a2a2a !important;
    box-shadow: 0 2px 6px rgba(0,0,0,.25) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #e8e8e8 !important; color: #bbb !important;
    box-shadow: none !important; transform: none !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important;
    border: 1.5px solid #e0e0e0 !important;
    color: #555 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #aaa !important; color: #111 !important;
    background: #fafafa !important;
}

/* ── download button ── */
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 13px !important; height: 38px !important;
    background: #fff !important; border: 1.5px solid #e0e0e0 !important; color: #555 !important;
}
.stDownloadButton > button:hover {
    border-color: #aaa !important; color: #111 !important;
}

/* ── textarea ── */
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important; font-size: 11.5px !important;
    border-radius: 8px !important; border: 1.5px solid #e8e8e8 !important;
    background: #fcfcfc !important; line-height: 1.65 !important; resize: none !important;
}
.stTextArea textarea:focus {
    border-color: #0f0f0f !important;
    box-shadow: 0 0 0 3px rgba(15,15,15,.06) !important;
}
.stTextArea textarea::placeholder { color: #ccc !important; }

/* ── text input ── */
.stTextInput > div > input {
    border-radius: 8px !important; border: 1.5px solid #e8e8e8 !important;
    font-size: 13px !important; height: 38px !important;
    background: #fcfcfc !important;
}
.stTextInput > div > input:focus {
    border-color: #0f0f0f !important;
    box-shadow: 0 0 0 3px rgba(15,15,15,.06) !important;
}

/* ── mode selector (radio horizontal) ── */
[data-testid="stHorizontalRadio"] {
    background: #f4f4f2 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #e8e8e8 !important;
}
[data-testid="stHorizontalRadio"] label {
    font-size: 12.5px !important; font-weight: 600 !important;
    border-radius: 7px !important; padding: 5px 12px !important;
    cursor: pointer !important; color: #888 !important;
    transition: all 0.15s !important;
}
[data-testid="stHorizontalRadio"] label:has(input:checked) {
    background: #fff !important; color: #111 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.1) !important;
}
[data-testid="stHorizontalRadio"] [data-baseweb="radio"] { display: none !important; }

/* ── metric cards ── */
[data-testid="stMetric"] {
    background: #fff; border: 1px solid #ebebeb;
    border-radius: 10px; padding: .8rem 1rem !important;
    transition: box-shadow .15s;
}
[data-testid="stMetric"]:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); }
[data-testid="stMetricLabel"] p {
    font-size: 10px !important; font-weight: 700 !important;
    color: #bbb !important; text-transform: uppercase !important;
    letter-spacing: .6px !important;
}
[data-testid="stMetricValue"] {
    font-size: 24px !important; font-weight: 800 !important;
    color: #0f0f0f !important; letter-spacing: -.8px !important;
}

/* ── live log (light, readable) ── */
.log-box {
    background: #fafaf8; border: 1px solid #eae9e4; border-radius: 8px;
    padding: 10px 12px; font-family: 'JetBrains Mono', monospace; font-size: 10.5px;
    line-height: 1.8; max-height: 190px; overflow-y: auto; margin-top: 8px;
}
.log-box::-webkit-scrollbar { width: 4px; }
.log-box::-webkit-scrollbar-track { background: #f0efe9; }
.log-box::-webkit-scrollbar-thumb { background: #d0cfc8; border-radius: 2px; }
.ll-site   { color: #0f0f0f; font-weight: 700; margin-top: 4px; padding-top: 4px;
             border-top: 1px solid #eeede8; }
.ll-site:first-child { border-top: none; margin-top: 0; padding-top: 0; }
.ll-email  { color: #15803d; font-weight: 600; }
.ll-page   { color: #bbb; }
.ll-skip   { color: #d97706; font-weight: 500; }
.ll-timing { color: #ccc; font-size: 10px; }
.ll-done   { color: #aaa; }
.ll-social { color: #2563eb; }
.ll-info   { color: #bbb; font-style: italic; }

/* ── filter chip bar ── */
.flt-bar .stButton > button {
    height: 30px !important; font-size: 11.5px !important;
    border-radius: 99px !important; padding: 0 12px !important;
    font-weight: 600 !important; letter-spacing: 0.1px !important;
}
/* inactive chips */
.flt-bar .stButton > button[kind="secondary"] {
    background: #f4f4f2 !important; border: 1px solid #e4e4e0 !important;
    color: #888 !important;
}
.flt-bar .stButton > button[kind="secondary"]:hover {
    background: #ebebea !important; color: #333 !important;
    border-color: #ccc !important;
}
/* active chips — nth-child gives each filter its own accent */
/* All  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="primary"] { background: #0f0f0f !important; color: #fff !important; border-color: #0f0f0f !important; }
/* T1  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="primary"] { background: #d97706 !important; color: #fff !important; border-color: #d97706 !important; }
/* T2  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(3) button[kind="primary"] { background: #6366f1 !important; color: #fff !important; border-color: #6366f1 !important; }
/* T3  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(4) button[kind="primary"] { background: #64748b !important; color: #fff !important; border-color: #64748b !important; }
/* No  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(5) button[kind="primary"] { background: #e11d48 !important; color: #fff !important; border-color: #e11d48 !important; }
/* ✅  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(6) button[kind="primary"] { background: #16a34a !important; color: #fff !important; border-color: #16a34a !important; }
/* ⚠️  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(7) button[kind="primary"] { background: #d97706 !important; color: #fff !important; border-color: #d97706 !important; }
/* ❌  */ .flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(8) button[kind="primary"] { background: #dc2626 !important; color: #fff !important; border-color: #dc2626 !important; }

/* inactive tinted variants */
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"] { color: #d97706 !important; border-color: #fde68a !important; background: #fffbeb !important; }
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(3) button[kind="secondary"] { color: #6366f1 !important; border-color: #c7d2fe !important; background: #eef2ff !important; }
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(4) button[kind="secondary"] { color: #64748b !important; border-color: #cbd5e1 !important; background: #f1f5f9 !important; }
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(5) button[kind="secondary"] { color: #e11d48 !important; border-color: #fecdd3 !important; background: #fff1f2 !important; }
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(6) button[kind="secondary"] { color: #16a34a !important; border-color: #bbf7d0 !important; background: #f0fdf4 !important; }
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(7) button[kind="secondary"] { color: #d97706 !important; border-color: #fde68a !important; background: #fffbeb !important; }
.flt-bar [data-testid="stHorizontalBlock"] > div:nth-child(8) button[kind="secondary"] { color: #dc2626 !important; border-color: #fecaca !important; background: #fff5f5 !important; }

/* ── per-domain action bar ── */
.action-bar {
    background: #fafaf8; border: 1px solid #eae9e4; border-radius: 10px;
    padding: 12px 14px; margin-top: 4px;
}

/* ── progress ── */
.prog-wrap  { margin: 10px 0 0; }
.prog-row   { display:flex; justify-content:space-between; align-items:center;
              font-size:11.5px; font-weight:600; margin-bottom:5px; color:#333; }
.prog-sub   { font-size:11px; font-weight:400; color:#aaa; }
.prog-track { height:3px; background:#ebebeb; border-radius:99px; overflow:hidden; }
.prog-fill  { height:100%; background:#0f0f0f; border-radius:99px; transition:width .35s ease; }
.scan-dot   { display:inline-block; width:7px; height:7px; background:#4ade80;
              border-radius:50%; margin-right:6px; animation:pulse 1.6s ease-in-out infinite; }
.scan-dot.paused { background:#fb923c; animation:none; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(.85)} }

/* ── mode description card ── */
.mode-card {
    background: #f8f8f6; border: 1px solid #e8e8e8; border-radius: 8px;
    padding: 8px 12px; margin-top: 8px; display: flex; align-items: center; gap: 10px;
}
.mode-icon { font-size: 16px; flex-shrink: 0; }
.mode-name { font-size: 12px; font-weight: 700; color: #0f0f0f; }
.mode-desc { font-size: 11px; color: #999; margin-top: 1px; }

/* ── url pills ── */
.pills { display:flex; flex-wrap:wrap; gap:4px; margin:6px 0 2px; }
.pill  {
    font-family:'JetBrains Mono',monospace; font-size:10.5px;
    background: #f0f0ee; border: 1px solid #e4e4e4;
    border-radius: 5px; padding: 2px 7px; color: #888;
}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px !important; background: #f4f4f2 !important;
    border-radius: 8px !important; padding: 3px !important;
    border: 1px solid #e8e8e8 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 12px !important; font-weight: 600 !important;
    border-radius: 6px !important; padding: 4px 14px !important;
    color: #999 !important;
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: #111 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.08) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }

/* ── expander ── */
details {
    border: 1px solid #ebebeb !important; border-radius: 8px !important;
    background: #fff !important;
}
details > summary {
    font-size: 12.5px !important; font-weight: 600 !important;
    color: #333 !important; padding: 10px 14px !important;
}
details[open] > summary { border-bottom: 1px solid #f0f0f0 !important; }

/* ── sliders ── */
[data-testid="stSlider"] > div > div > div > div {
    background: #0f0f0f !important;
}

/* ── divider ── */
hr { border-color: #f0f0f0 !important; margin: 12px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
TIER1 = re.compile(r"^(editor|admin|press|advert|contact)[a-z0-9._%+\-]*@", re.IGNORECASE)
TIER2 = re.compile(r"^(info|sales|hello|office|team|support|help)[a-z0-9._%+\-]*@", re.IGNORECASE)
BLOCKED_TLDS = {'png','jpg','jpeg','webp','gif','svg','ico','bmp','tiff','avif','mp4','mp3',
    'wav','ogg','mov','avi','webm','pdf','zip','rar','tar','gz','7z','js','css','php',
    'asp','aspx','xml','json','ts','jsx','tsx','woff','woff2','ttf','eot','otf','map',
    'exe','dmg','pkg','deb','apk'}
PLACEHOLDER_DOMAINS = {'example.com','example.org','example.net','test.com','domain.com',
    'yoursite.com','yourwebsite.com','website.com','email.com','sampleemail.com',
    'mailtest.com','placeholder.com'}
PLACEHOLDER_LOCALS = {'you','user','name','email','test','example','someone','username',
    'yourname','youremail','enter','address','sample'}
SUPPRESS_PREFIXES = ['noreply','no-reply','donotreply','do-not-reply','mailer-daemon',
    'bounce','bounces','unsubscribe','notifications','notification','newsletter',
    'newsletters','postmaster','webmaster','auto-reply','autoreply','daemon',
    'robot','alerts','alert','system']
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
]
# Scored priority keywords — higher = more relevant
PRIORITY_KEYWORDS = [
    ("contact",      100), ("write-for-us",95), ("writeforus",95), ("write_for_us",95),
    ("guest-post",   90),  ("guest_post",  90),  ("guestpost",  90),
    ("advertise",    88),  ("advertising", 88),  ("contribute", 85), ("contributor",85),
    ("submit",       82),  ("submission",  82),  ("pitch",      80),
    ("about",        75),  ("about-us",    75),  ("about_us",   75),
    ("team",         70),  ("our-team",    70),  ("staff",      70), ("people",70),
    ("work-with-us", 68),  ("partner",     65),  ("reach-us",   60),
    ("get-in-touch", 60),  ("press",       55),  ("media",      50),
]
TWITTER_SKIP  = {'share','intent','home','search','hashtag','i','status','twitter','x'}
LINKEDIN_SKIP = {'share','shareArticle','in','company','pub','feed','login','authwall'}
FACEBOOK_SKIP = {'sharer','share','dialog','login','home','watch','groups','events','marketplace'}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "results":{}, "scraped_domains":set(), "scan_state":"idle",
    "scan_queue":[], "scan_idx":0, "log_lines":[], "sessions":[],
    "mode":"Quick", "tbl_filter":"All",
    "skip_t1":True, "respect_robots":False, "scrape_fb":False,
    "f_tier1":True, "f_tier2":True, "f_tier3":True,
    "mx_cache":{}, "auto_validate":False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CORE HELPERS ──────────────────────────────────────────────────────────────
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

def tier_key(e):
    if TIER1.match(e): return "1"
    if TIER2.match(e): return "2"
    return "3"

def tier_short(e): return {"1":"Tier 1","2":"Tier 2","3":"Tier 3"}[tier_key(e)]
def tier_label(e): return {"1":"🥇 T1","2":"🥈 T2","3":"🥉 T3"}[tier_key(e)]
def sort_by_tier(emails): return sorted(emails, key=tier_key)

def pick_best(emails):
    pool = [e for e in emails if is_valid_email(e)]
    if not pool: return None
    for pat in [TIER1, TIER2]:
        hit = [e for e in pool if pat.match(e)]
        if hit: return hit[0]
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
            if m and m.group(2).lower() not in LINKEDIN_SKIP:
                li.add(f"linkedin.com/{m.group(1)}/{m.group(2)}")
        elif "facebook.com/" in hl and "facebook.com/tr?" not in hl:
            m = re.search(r'facebook\.com/([A-Za-z0-9_.]{3,80})', href)
            if m and m.group(1).lower() not in FACEBOOK_SKIP:
                fb.add(f"facebook.com/{m.group(1)}")
    return tw, li, fb

def get_internal_links(html, base_url, root_domain):
    soup = BeautifulSoup(html, "html.parser"); links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"]); p = urlparse(full)
        if p.netloc == root_domain and p.scheme in ("http","https"):
            links.append(full.split("#")[0].split("?")[0])
    return list(set(links))

def find_write_for_us_links(html, base_url, root_domain):
    KW = ["write for us","write-for-us","writeforus","guest post","guest-post",
          "contribute","submission","submit a","pitch us","advertise","advertising",
          "work with us","partner with","become a contributor","write with us"]
    soup = BeautifulSoup(html, "html.parser"); found = []
    for a in soup.find_all("a", href=True):
        href = a.get("href",""); text = (a.get_text(" ",strip=True)+" "+href).lower()
        if any(kw in text for kw in KW):
            full = urljoin(base_url, href); p = urlparse(full)
            if p.netloc == root_domain and p.scheme in ("http","https"):
                found.append(full.split("#")[0].split("?")[0])
    return list(set(found))

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

# ── VALIDATION (from hu repo) ─────────────────────────────────────────────────
def _val_syntax(email):
    try: ev_validate(email); return True
    except EmailNotValidError: return False

def _val_mx(domain):
    try:
        records = _dns_resolver.resolve(domain, "MX")
        return True, [str(r.exchange) for r in records]
    except Exception: return False, []

def _val_spf(domain):
    try:
        for rdata in _dns_resolver.resolve(domain, "TXT"):
            if "v=spf1" in str(rdata): return True
    except Exception: pass
    return False

def _val_mailbox(email, mx_records):
    try:
        mx = mx_records[0].rstrip(".")
        with smtplib.SMTP(mx, timeout=6) as s:
            s.helo("example.com"); s.mail("test@example.com")
            code, _ = s.rcpt(email)
            return code == 250
    except Exception: return False

def _val_catch_all(domain, mx_records):
    try:
        mx = mx_records[0].rstrip(".")
        with smtplib.SMTP(mx, timeout=6) as s:
            s.helo("example.com"); s.mail("test@example.com")
            code, _ = s.rcpt(f"randomaddress9x7z@{domain}")
            return code == 250
    except Exception: return False

def _deliverability(syntax, domain_ok, mailbox_ok, disposable, free, catch_all, mx_ok, spf_ok):
    if not syntax:    return "Not Deliverable", "Invalid syntax"
    if not domain_ok: return "Not Deliverable", "Domain doesn't exist"
    if disposable:    return "Not Deliverable", "Disposable domain"
    if not mx_ok:     return "Not Deliverable", "No MX records"
    if mailbox_ok:
        if free:
            return ("Risky","Catch-all + free email") if catch_all else ("Deliverable","Free email provider")
        if catch_all:  return "Risky", "Catch-all enabled"
        if not spf_ok: return "Risky", "Missing SPF record"
        return "Deliverable", "—"
    else:
        if catch_all:  return "Risky", "Catch-all + mailbox unknown"
        if free:       return "Deliverable", "Free provider, mailbox unverified"
        if not spf_ok: return "Risky", "No SPF — spam risk"
        return "Deliverable", "Mailbox unconfirmed, MX/SPF OK"

def validate_email_full(email):
    disp_list = fetch_disposable_domains()
    domain = email.split("@")[-1].lower()
    syntax = _val_syntax(email)
    mx_ok, mx_hosts = _val_mx(domain) if DNS_AVAILABLE else (False, [])
    spf_ok     = _val_spf(domain) if DNS_AVAILABLE else False
    disposable = domain in disp_list
    free       = domain in FREE_EMAIL_DOMAINS
    mailbox_ok = _val_mailbox(email, mx_hosts) if (mx_ok and DNS_AVAILABLE) else False
    catch_all  = _val_catch_all(domain, mx_hosts) if (mx_ok and DNS_AVAILABLE) else False
    status, reason = _deliverability(syntax, mx_ok, mailbox_ok, disposable, free, catch_all, mx_ok, spf_ok)
    return {"status":status,"reason":reason,"syntax":syntax,"mx":mx_ok,
            "spf":spf_ok,"mailbox":mailbox_ok,"disposable":disposable,
            "free":free,"catch_all":catch_all}

def val_icon(s):
    return {"Deliverable":"✅","Risky":"⚠️","Not Deliverable":"❌"}.get(s,"—")

def check_mx(email):
    if not DNS_AVAILABLE: return None
    domain = email.split("@")[1].lower(); cache = st.session_state.mx_cache
    if domain in cache: return cache[domain]
    try: result = len(_dns_resolver.resolve(domain,"MX",lifetime=4)) > 0
    except: result = False
    cache[domain] = result; return result

# ── SITEMAP-FIRST PRIORITY ENGINE ─────────────────────────────────────────────
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

def score_url(url):
    """Score a URL by priority keyword match, penalising deep paths."""
    path = urlparse(url).path.lower(); best = 0
    for kw, score in PRIORITY_KEYWORDS:
        if kw in path:
            depth_penalty = path.count("/") * 3
            best = max(best, score - depth_penalty)
    return best

def get_priority_urls(root_url, limit=None):
    """
    Sitemap-first: fetch sitemap, score URLs, return sorted priority list.
    Falls back to hardcoded PRIORITY_PATHS if no sitemap found.
    Returns (priority_urls, used_sitemap).
    """
    sm_urls = fetch_sitemap_urls(root_url)
    if sm_urls:
        scored = sorted([(u, score_url(u)) for u in sm_urls if score_url(u) > 0],
                        key=lambda x: -x[1])
        urls = [u for u,_ in scored]
        return (urls[:limit] if limit else urls), True
    # fallback — build from known paths
    base = root_url.rstrip("/")
    fallback = sorted([(base+p, score_url(base+p)) for p in
        ["/contact","/contact-us","/about","/about-us","/team","/write-for-us",
         "/advertise","/contribute","/pitch","/submit","/partner","/press",
         "/guest-post","/work-with-us","/reach-us","/get-in-touch","/staff",
         "/our-team","/people","/submission","/advertising","/contributors"]
        if score_url(base+p) > 0], key=lambda x: -x[1])
    urls = [u for u,_ in fallback]
    return (urls[:limit] if limit else urls), False

# ── FACEBOOK SCRAPER ──────────────────────────────────────────────────────────
def scrape_facebook_page(fb_handle, log_cb):
    slug = fb_handle.replace("facebook.com/","").strip("/")
    if not slug: return set()
    url = f"https://www.facebook.com/{slug}"
    log_cb(("info", f"Facebook: {slug}", None, None), "info")
    t0 = time.time(); html = fetch_page(url, timeout=14); elapsed = round(time.time()-t0,2)
    if html:
        found = extract_emails(html)
        for e in sort_by_tier(found): log_cb(("email", e, f"fb/{slug}", tier_label(e)), "email")
        log_cb(("timing", f"{elapsed}s · {len(found)} email(s) from Facebook", None, None), "timing")
        return found
    log_cb(("timing", f"{elapsed}s · Facebook blocked", None, None), "timing")
    return set()

# ── QUICK MODE ────────────────────────────────────────────────────────────────
def scrape_quick_site(root_url, log_cb):
    """
    Quick — sitemap-first, scrape top 4 priority pages only (contact/about/write-for-us etc).
    5s timeout per page. Stops early if Tier 1 found.
    """
    t0 = time.time(); root_domain = urlparse(root_url).netloc
    all_emails = set(); all_tw, all_li, all_fb = set(), set(), set(); pages_hit = 0

    log_cb(("info", "Sitemap scan…", None, None), "info")
    priority_urls, used_sitemap = get_priority_urls(root_url, limit=4)
    src = f"sitemap → {len(priority_urls)} page(s)" if used_sitemap else f"known paths ({len(priority_urls)})"
    log_cb(("info", src, None, None), "info")

    for url in priority_urls:
        short = url.replace("https://","").replace("http://","")
        t_p = time.time()
        log_cb(("page_start", short, "quick", None), "active")
        html = fetch_page(url, timeout=5); elapsed = round(time.time()-t_p, 2)
        if html:
            found = extract_emails(html); new = found - all_emails
            tw, li, fb = extract_social(html)
            all_emails.update(found); all_tw.update(tw); all_li.update(li); all_fb.update(fb)
            for e in sort_by_tier(new): log_cb(("email", e, short, tier_label(e)), "email")
            log_cb(("timing", f"{elapsed}s · {len(new)} email(s)", None, None), "timing")
            pages_hit += 1
            if any(TIER1.match(e) for e in all_emails):
                t1e = next(e for e in all_emails if TIER1.match(e))
                log_cb(("skip", f"Tier 1 found ({t1e})", None, None), "skip"); break
        else:
            log_cb(("timing", f"{elapsed}s · no response", None, None), "timing")

    if st.session_state.get("scrape_fb") and all_fb:
        all_emails.update(scrape_facebook_page(sorted(all_fb)[0], log_cb))

    best = pick_best(all_emails); total_t = round(time.time()-t0, 1)
    log_cb(("done", f"{root_domain} — {len(all_emails)} email(s) in {total_t}s", None, None), "done")
    return {"Domain":root_domain,"Best Email":best or "","Best Tier":tier_short(best) if best else "",
            "All Emails":sort_by_tier(all_emails),"Twitter":sorted(all_tw),
            "LinkedIn":sorted(all_li),"Facebook":sorted(all_fb),
            "Pages Scraped":pages_hit,"Total Time":total_t,"Source URL":root_url,"MX":{}}

# ── STANDARD MODES ────────────────────────────────────────────────────────────
def scrape_one_site(root_url, cfg, skip_t1, respect_robots, log_cb):
    """
    Easy / Medium / Extreme — sitemap-first priority detection for all modes.
    Priority pages (contact/about/write-for-us etc) always scraped first.
    Remaining page budget used for crawling.
    """
    t0 = time.time(); root_domain = urlparse(root_url).netloc
    visited = set(); queue = deque()
    all_emails = set(); all_tw, all_li, all_fb = set(), set(), set()
    rp = load_robots(root_url, respect_robots)

    log_cb(("info", "Sitemap scan for priority pages…", None, None), "info")
    priority_urls, used_sitemap = get_priority_urls(root_url)
    src = f"sitemap → {len(priority_urls)} priority page(s)" if used_sitemap else "no sitemap — using known paths"
    log_cb(("info", src, None, None), "info")

    # For Extreme: add ALL remaining sitemap URLs to crawl queue
    if cfg.get("sitemap") and used_sitemap:
        all_sm = fetch_sitemap_urls(root_url)
        priority_set = set(priority_urls)
        for u in all_sm:
            if u not in priority_set: queue.append((u, 0, False))

    # Priority pages go first (front of queue)
    for u in reversed(priority_urls):
        queue.appendleft((u, 0, True))

    # Homepage always in the mix for Easy+
    queue.append((root_url, 0, False))

    max_pages = cfg["max_pages"]; max_depth = cfg["max_depth"]; pages_done = 0

    while queue and pages_done < max_pages + len(priority_urls):
        url, depth, is_priority = queue.popleft()
        if url in visited: continue
        visited.add(url)
        short = url.replace("https://","").replace("http://","")
        t_p = time.time(); label = "priority" if is_priority else f"{pages_done+1}/{max_pages}"

        if not robots_allowed(rp, url):
            log_cb(("timing", f"robots blocked — {short}", None, None), "timing")
            if not is_priority: pages_done += 1
            continue

        log_cb(("page_start", short, label, None), "active")
        html = fetch_page(url); elapsed = round(time.time()-t_p, 2)

        if html:
            found = extract_emails(html); new = found - all_emails
            tw, li, fb = extract_social(html)
            new_tw = tw-all_tw; new_li = li-all_li; new_fb = fb-all_fb
            all_emails.update(found); all_tw.update(tw); all_li.update(li); all_fb.update(fb)

            for wlink in find_write_for_us_links(html, url, root_domain):
                if wlink not in visited:
                    queue.appendleft((wlink, 0, True))
                    log_cb(("info", f"write-for-us → {wlink.replace('https://','')[:40]}", None, None), "info")

            for e in sort_by_tier(new): log_cb(("email", e, short, tier_label(e)), "email")
            for h in sorted(new_tw|new_li|new_fb): log_cb(("social", h, short, None), "social")
            log_cb(("timing", f"{elapsed}s · {len(new)} email(s)", None, None), "timing")

            if not is_priority and depth < max_depth:
                for link in get_internal_links(html, url, root_domain):
                    if link not in visited: queue.append((link, depth+1, False))

            if skip_t1 and any(TIER1.match(e) for e in all_emails):
                t1e = next(e for e in all_emails if TIER1.match(e))
                log_cb(("skip", f"Tier 1 ({t1e}) — skipping {root_domain}", None, None), "skip")
                break
        else:
            log_cb(("timing", f"{elapsed}s · no response", None, None), "timing")

        if not is_priority: pages_done += 1

    if st.session_state.get("scrape_fb") and all_fb:
        log_cb(("info", f"Auto-scraping Facebook…", None, None), "info")
        all_emails.update(scrape_facebook_page(sorted(all_fb)[0], log_cb))

    best = pick_best(all_emails); total_t = round(time.time()-t0, 1)
    sorted_emails = sort_by_tier(all_emails)
    log_cb(("done", f"{root_domain} — {len(all_emails)} email(s) in {total_t}s", None, None), "done")
    return {"Domain":root_domain,"Best Email":best or "","Best Tier":tier_short(best) if best else "",
            "All Emails":sorted_emails,"Twitter":sorted(all_tw),"LinkedIn":sorted(all_li),
            "Facebook":sorted(all_fb),"Pages Scraped":pages_done,"Total Time":total_t,
            "Source URL":root_url,"MX":{}}

# ── LOG RENDERER ──────────────────────────────────────────────────────────────
def render_log(ph):
    h = ""
    for item, kind in st.session_state.log_lines[-60:]:
        _, text, _, extra = item
        if   kind == "site":   h += f'<div class="ll-site">▶ {text}</div>'
        elif kind == "active": h += f'<div class="ll-page">  ↳ {text}</div>'
        elif kind == "email":  h += f'<div class="ll-email">  ✉ {text}</div>'
        elif kind == "social": h += f'<div class="ll-social">  ⟐ {text}</div>'
        elif kind == "timing": h += f'<div class="ll-timing">    {text}</div>'
        elif kind == "skip":   h += f'<div class="ll-skip">  ⚡ {text}</div>'
        elif kind == "done":   h += f'<div class="ll-done">  ✓ {text}</div>'
        elif kind == "info":   h += f'<div class="ll-info">  {text}</div>'
    ph.markdown(f'<div class="log-box">{h}</div>', unsafe_allow_html=True)

def log_cb_factory(ph):
    def cb(item, kind):
        st.session_state.log_lines.append((item, kind))
        render_log(ph)
    return cb

# ─────────────────────────────────────────────────────────────────────────────
#  PRE-LOAD
# ─────────────────────────────────────────────────────────────────────────────
fetch_disposable_domains()  # warm cache silently

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
h1, h2 = st.columns([5, 1])
with h1:
    st.markdown(
        '<div class="logo">'
        '<div class="logo-icon">✉</div>'
        'MailHunter'
        '</div>'
        '<div style="font-size:12px;color:#aaa;margin-top:4px;font-weight:400">'
        'Sitemap-first email scraper &nbsp;·&nbsp; tier ranking &nbsp;·&nbsp; SMTP validation'
        '</div>',
        unsafe_allow_html=True)
with h2:
    if st.session_state.results:
        rows = []
        for d, r in st.session_state.results.items():
            val = r.get("Validation", {})
            rows.append({"Domain":d,"Best Email":r.get("Best Email",""),
                "Deliverability":val.get("status",""),"Reason":val.get("reason",""),
                "SPF":val.get("spf",""),"MX":val.get("mx",""),
                "Catch-All":val.get("catch_all",""),"Disposable":val.get("disposable",""),
                "Free Email":val.get("free",""),"All Emails":"; ".join(r.get("All Emails",[])),
                "Twitter":"; ".join(r.get("Twitter",[])),"LinkedIn":"; ".join(r.get("LinkedIn",[])),
                "Facebook":"; ".join(r.get("Facebook",[])),"Pages":r.get("Pages Scraped",0),
                "Time(s)":r.get("Total Time",""),"Source URL":r.get("Source URL","")})
        buf = io.StringIO(); pd.DataFrame(rows).to_csv(buf, index=False)
        st.download_button("⬇ Export CSV", buf.getvalue(),
                           f"mailhunter_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           "text/csv", key="export_top")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 2.8], gap="large")

# ═══════════════════════════════════════════════════════════════════════════
#  LEFT PANEL
# ═══════════════════════════════════════════════════════════════════════════
with left:

    # ── URL INPUT ────────────────────────────────────────────────────────
    st.markdown('<span class="lbl">Target URLs</span>', unsafe_allow_html=True)
    tab_paste, tab_csv = st.tabs(["Paste", "Upload CSV"])
    urls_to_scrape = []

    with tab_paste:
        raw = st.text_area("u", label_visibility="collapsed",
                           placeholder="https://magazine.com\nhttps://techblog.io\nnewspaper.org",
                           height=115, key="url_input")
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            if not line.startswith("http"): line = "https://"+line
            urls_to_scrape.append(line)

    with tab_csv:
        uploaded = st.file_uploader("f", type=["csv","txt"], label_visibility="collapsed")
        if uploaded:
            rb = uploaded.read()
            if uploaded.name.endswith(".csv"):
                try:
                    df_up = pd.read_csv(io.BytesIO(rb)); cols_u = list(df_up.columns)
                    hints = ["url","link","website","site","domain","href"]
                    defcol = next((c for c in cols_u if any(h in c.lower() for h in hints)), cols_u[0])
                    col_sel = st.selectbox("Column", cols_u, index=cols_u.index(defcol), key="csv_col")
                    for u in df_up[col_sel].dropna().astype(str):
                        u = u.strip()
                        if not u.startswith("http"): u = "https://"+u
                        urls_to_scrape.append(u)
                    st.caption(f"✓ {len(urls_to_scrape)} URLs")
                except Exception as ex: st.error(f"CSV error: {ex}")
            else:
                for line in rb.decode("utf-8","ignore").splitlines():
                    line = line.strip()
                    if not line: continue
                    if not line.startswith("http"): line = "https://"+line
                    urls_to_scrape.append(line)
                st.caption(f"✓ {len(urls_to_scrape)} URLs")

    if urls_to_scrape:
        pills = "".join(f'<span class="pill">{u.replace("https://","")[:24]}</span>'
                        for u in urls_to_scrape[:6])
        if len(urls_to_scrape) > 6:
            pills += f'<span class="pill">+{len(urls_to_scrape)-6}</span>'
        st.markdown(f'<div class="pills">{pills}</div>', unsafe_allow_html=True)

    # ── MODE ─────────────────────────────────────────────────────────────
    st.markdown('<span class="lbl" style="margin-top:16px;display:block">Crawl Mode</span>',
                unsafe_allow_html=True)

    MODE_CFG = {
        "⚡ Quick":   {"max_pages":0,"max_depth":0,"sitemap":False,"delay":0.1,
                       "icon":"⚡","name":"Quick",
                       "desc":"Sitemap → top 4 contact/about/write-for-us pages",
                       "color":"#7c3aed"},
        "✦ Easy":    {"max_pages":5,"max_depth":0,"sitemap":False,"delay":0.3,
                       "icon":"✦","name":"Easy",
                       "desc":"Sitemap priority pages + homepage",
                       "color":"#16a34a"},
        "◈ Medium":  {"max_pages":50,"max_depth":3,"sitemap":False,"delay":0.5,
                       "icon":"◈","name":"Medium",
                       "desc":"Sitemap first, then crawl up to 50 pages",
                       "color":"#d97706"},
        "⬡ Extreme": {"max_pages":300,"max_depth":6,"sitemap":True,"delay":0.3,
                       "icon":"⬡","name":"Extreme",
                       "desc":"Full sitemap + deep crawl, 300 pages",
                       "color":"#dc2626"},
    }
    MODE_LABELS = list(MODE_CFG.keys())
    MODE_NAMES  = [v["name"] for v in MODE_CFG.values()]

    # find current label
    cur_label = next((l for l in MODE_LABELS if MODE_CFG[l]["name"] == st.session_state.mode),
                     MODE_LABELS[0])

    chosen_label = st.radio("mode_r", MODE_LABELS, index=MODE_LABELS.index(cur_label),
                             horizontal=True, label_visibility="collapsed", key="mode_radio")

    mode_info = MODE_CFG[chosen_label]
    mode_key  = mode_info["name"]
    if mode_key != st.session_state.mode:
        st.session_state.mode = mode_key; st.rerun()

    # mode description card
    st.markdown(
        f'<div class="mode-card">'
        f'<div class="mode-icon">{mode_info["icon"]}</div>'
        f'<div><div class="mode-name" style="color:{mode_info["color"]}">{mode_key}</div>'
        f'<div class="mode-desc">{mode_info["desc"]}</div></div>'
        f'</div>', unsafe_allow_html=True)

    cfg = {k:v for k,v in mode_info.items() if k not in ("icon","name","desc","color")}

    if mode_key == "Medium":
        cfg["max_depth"] = st.slider("Depth", 1, 5, 3, key="sl_depth")
        cfg["max_pages"] = st.slider("Pages/site", 10, 200, 50, key="sl_pages")
    elif mode_key == "Extreme":
        cfg["max_pages"] = st.slider("Pages/site", 50, 500, 300, key="sl_pagesx")

    # ── SCAN CONTROLS ────────────────────────────────────────────────────
    st.divider()
    scan_state = st.session_state.scan_state

    if scan_state == "idle":
        do_start = st.button("▶  Start Scan", type="primary", use_container_width=True,
                             disabled=not urls_to_scrape, key="btn_start")
    elif scan_state == "running":
        do_start = False
        c_p, c_c = st.columns(2)
        with c_p:
            if st.button("⏸  Pause", type="primary", use_container_width=True, key="btn_pause"):
                st.session_state.scan_state = "paused"; st.rerun()
        with c_c:
            if st.button("✕  Stop", type="secondary", use_container_width=True, key="btn_stop"):
                st.session_state.scan_state = "done"; st.rerun()
    elif scan_state == "paused":
        do_start = False
        c_r, c_c = st.columns(2)
        with c_r:
            if st.button("▶  Resume", type="primary", use_container_width=True, key="btn_resume"):
                st.session_state.scan_state = "running"; st.rerun()
        with c_c:
            if st.button("✕  Stop", type="secondary", use_container_width=True, key="btn_stop2"):
                st.session_state.scan_state = "done"; st.rerun()
    else:  # done
        do_start = st.button("▶  New Scan", type="primary", use_container_width=True,
                             disabled=not urls_to_scrape, key="btn_new")

    ca, cb_ = st.columns(2)
    with ca:
        if st.button("🗑  Clear all", type="secondary", use_container_width=True, key="btn_clear"):
            for k in ("results","scan_queue","log_lines"):
                st.session_state[k] = {} if k == "results" else []
            st.session_state.scan_state = "idle"
            st.session_state.scan_idx   = 0
            st.rerun()
    with cb_:
        if st.session_state.results and scan_state != "running":
            if st.button("💾  Save", type="secondary", use_container_width=True, key="btn_save"):
                ts = datetime.now().strftime("%b %d %H:%M")
                st.session_state.sessions.append({
                    "name": f"Scan {len(st.session_state.sessions)+1} · {ts}",
                    "results": dict(st.session_state.results)})
                st.rerun()

    # start trigger
    do_start = do_start if "do_start" in dir() else False
    if do_start and urls_to_scrape:
        new_urls = [u for u in urls_to_scrape
                    if urlparse(u).netloc not in st.session_state.scraped_domains]
        if new_urls:
            if scan_state == "done": st.session_state.results = {}
            st.session_state.update(scan_queue=new_urls, scan_idx=0,
                                    scan_state="running", log_lines=[])
            st.rerun()

    # ── PROGRESS + LOG ───────────────────────────────────────────────────
    prog_ph = st.empty()
    log_ph  = st.empty()

    if scan_state in ("running","paused") and st.session_state.scan_queue:
        idx = st.session_state.scan_idx; total = len(st.session_state.scan_queue)
        pct = int(idx / total * 100) if total else 0
        dot = "scan-dot paused" if scan_state == "paused" else "scan-dot"
        lbl = "Paused" if scan_state == "paused" else "Scanning"
        prog_ph.markdown(f"""
        <div style="margin:8px 0 4px">
          <div class="prog-row">
            <span><span class="{dot}"></span>{lbl}</span>
            <span class="prog-sub">{idx} / {total}</span>
          </div>
          <div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.log_lines:
        render_log(log_ph)

    # ── SETTINGS ─────────────────────────────────────────────────────────
    st.divider()
    with st.expander("⚙  Settings"):
        st.markdown("**Crawl**")
        st.session_state.skip_t1        = st.toggle("Stop once Tier 1 found",   value=st.session_state.skip_t1,        key="t_skip")
        st.session_state.respect_robots = st.toggle("Respect robots.txt",        value=st.session_state.respect_robots,  key="t_robots")
        st.session_state.auto_validate  = st.toggle("Auto-validate after scan",  value=st.session_state.auto_validate,   key="t_autovalidate")
        st.markdown("**Sources**")
        st.session_state.scrape_fb = st.toggle("Auto-scrape Facebook", value=st.session_state.scrape_fb, key="t_fb")
        st.markdown("**Show tiers**")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1: st.session_state.f_tier1 = st.checkbox("T1", value=st.session_state.f_tier1, key="cb_t1")
        with col_t2: st.session_state.f_tier2 = st.checkbox("T2", value=st.session_state.f_tier2, key="cb_t2")
        with col_t3: st.session_state.f_tier3 = st.checkbox("T3", value=st.session_state.f_tier3, key="cb_t3")
        n_mem = len(st.session_state.scraped_domains)
        if n_mem:
            st.caption(f"Domain memory: {n_mem}")
            if st.button("Clear memory", key="btn_mem", use_container_width=True):
                st.session_state.scraped_domains = set(); st.rerun()

    # ── SESSIONS ─────────────────────────────────────────────────────────
    if st.session_state.sessions:
        with st.expander(f"💾  Sessions ({len(st.session_state.sessions)})"):
            for i, sess in enumerate(st.session_state.sessions):
                n_d = len(sess["results"])
                n_e = sum(len(r.get("All Emails",[])) for r in sess["results"].values())
                rc1, rc2, rc3 = st.columns([3,1,1])
                with rc1: st.caption(f"**{sess['name']}** · {n_d}d · {n_e}e")
                with rc2:
                    if st.button("Load", key=f"load_{i}", use_container_width=True):
                        st.session_state.results    = sess["results"]
                        st.session_state.scan_state = "done"; st.rerun()
                with rc3:
                    if st.button("✕", key=f"del_{i}", use_container_width=True):
                        st.session_state.sessions.pop(i); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  RIGHT PANEL
# ═══════════════════════════════════════════════════════════════════════════
with right:
    results    = st.session_state.results
    scan_state = st.session_state.scan_state

    if not results:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:90px 20px;text-align:center">
          <div style="width:56px;height:56px;background:#f0f0ee;border-radius:14px;
                      display:flex;align-items:center;justify-content:center;
                      font-size:24px;margin-bottom:20px;border:1px solid #e8e8e8">✉</div>
          <div style="font-size:17px;font-weight:800;color:#0f0f0f;margin-bottom:8px;letter-spacing:-.3px">
            No results yet
          </div>
          <div style="font-size:12.5px;color:#bbb;line-height:1.8;max-width:280px">
            Paste URLs on the left and hit <strong style="color:#555">▶ Start Scan</strong>.<br>
            Quick mode finds contact pages automatically via sitemap.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── METRICS ──────────────────────────────────────────────────────
        tot_d  = len(results)
        tot_e  = sum(len(r.get("All Emails",[])) for r in results.values())
        t1_cnt = sum(1 for r in results.values() if r.get("Best Tier","").startswith("Tier 1"))
        val_ok = sum(1 for r in results.values() if r.get("Validation",{}).get("status")=="Deliverable")
        no_e   = sum(1 for r in results.values() if not r.get("Best Email"))

        mc1,mc2,mc3,mc4,mc5 = st.columns(5)
        mc1.metric("Domains",    tot_d)
        mc2.metric("Emails",     tot_e)
        mc3.metric("Tier 1",     t1_cnt)
        mc4.metric("Validated",  val_ok)
        mc5.metric("No Email",   no_e)

        # ── VALIDATE ALL ─────────────────────────────────────────────────
        if scan_state == "done":
            to_val = [d for d,r in results.items()
                      if r.get("Best Email") and not r.get("Validation")]
            if to_val:
                st.markdown(
                    f'<div style="display:flex;align-items:center;justify-content:space-between;'
                    f'background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;'
                    f'padding:8px 14px;margin:6px 0 2px;">'
                    f'<span style="font-size:12px;color:#15803d;font-weight:600">'
                    f'✓ {len(to_val)} email(s) ready to validate</span></div>',
                    unsafe_allow_html=True)
                if st.button("🔍 Validate All emails", key="val_all", type="primary", use_container_width=True):
                    st.session_state["run_validate_all"] = True; st.rerun()

        # ── SEARCH + FILTER CHIPS ─────────────────────────────────────────
        search = st.text_input("s", placeholder="🔍  Search domains or emails…",
                               label_visibility="collapsed", key="search_box")

        FLT_CHIPS = [
            ("All",      "All",      "All"),
            ("🥇 T1",    "T1",       "T1"),
            ("🥈 T2",    "T2",       "T2"),
            ("🥉 T3",    "T3",       "T3"),
            ("∅ None",   "No Email", "None"),
            ("✅ Deliv.", "Deliv.",   "val_ok"),
            ("⚠️ Risky", "Risky",    "val_risky"),
            ("❌ Bad",   "Bad",      "val_bad"),
        ]
        st.markdown('<div class="flt-bar">', unsafe_allow_html=True)
        flt_cols = st.columns(len(FLT_CHIPS))
        for col, (label, _, val) in zip(flt_cols, FLT_CHIPS):
            with col:
                is_active = st.session_state.tbl_filter == val
                if st.button(label, key=f"flt_{val}",
                             type="primary" if is_active else "secondary",
                             use_container_width=True):
                    st.session_state.tbl_filter = val; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── TABLE ─────────────────────────────────────────────────────────
        rows = []
        for domain, r in results.items():
            all_e = r.get("All Emails",[]); best = r.get("Best Email",""); bt = r.get("Best Tier","")
            val = r.get("Validation",{})
            val_st = val.get("status","") if val else ""
            rows.append({
                "Domain":     domain,
                "Best Email": best or "—",
                "Tier":       bt or "—",
                "✓":          val_icon(val_st) if val_st else "—",
                "Reason":     val.get("reason","—") if val else "—",
                "SPF":        ("✓" if val.get("spf") else "✗") if val else "—",
                "Catch-all":  ("⚠" if val.get("catch_all") else "✓") if val else "—",
                "+":          f'+{len(all_e)-1}' if len(all_e) > 1 else "",
                "Twitter":    (r.get("Twitter",[])+["—"])[0],
                "LinkedIn":   (r.get("LinkedIn",[])+["—"])[0],
                "Pages":      r.get("Pages Scraped",0),
                "s":          r.get("Total Time","—"),
            })

        df = pd.DataFrame(rows)
        if search:
            m = (df["Domain"].str.contains(search,case=False,na=False) |
                 df["Best Email"].str.contains(search,case=False,na=False))
            df = df[m]

        flt = st.session_state.tbl_filter
        if   flt=="T1":       df = df[df["Tier"].str.startswith("Tier 1",na=False)]
        elif flt=="T2":       df = df[df["Tier"].str.startswith("Tier 2",na=False)]
        elif flt=="T3":       df = df[df["Tier"].str.startswith("Tier 3",na=False)]
        elif flt=="None":     df = df[df["Best Email"]=="—"]
        elif flt=="val_ok":   df = df[df["✓"]=="✅"]
        elif flt=="val_risky":df = df[df["✓"]=="⚠️"]
        elif flt=="val_bad":  df = df[df["✓"]=="❌"]

        st.caption(f"**{len(df)}** of {tot_d} domains")
        st.dataframe(df, use_container_width=True, hide_index=True,
                     height=min(560, 44+max(len(df),1)*36),
                     column_config={
                         "Domain":    st.column_config.TextColumn("Domain",    width=155),
                         "Best Email":st.column_config.TextColumn("Email",     width=190),
                         "Tier":      st.column_config.TextColumn("Tier",      width=72),
                         "✓":         st.column_config.TextColumn("✓",         width=42),
                         "Reason":    st.column_config.TextColumn("Reason",    width=175),
                         "SPF":       st.column_config.TextColumn("SPF",       width=38),
                         "Catch-all": st.column_config.TextColumn("Catch-all", width=65),
                         "+":         st.column_config.TextColumn("+",         width=38),
                         "Twitter":   st.column_config.TextColumn("Twitter",   width=105),
                         "LinkedIn":  st.column_config.TextColumn("LinkedIn",  width=130),
                         "Pages":     st.column_config.NumberColumn("Pages",   width=50),
                         "s":         st.column_config.NumberColumn("s",       width=45),
                     })

        # ── PER-DOMAIN ACTIONS ────────────────────────────────────────────
        st.divider()
        st.markdown('<span class="lbl">Per-domain actions</span>', unsafe_allow_html=True)
        st.markdown('<div class="action-bar">', unsafe_allow_html=True)
        pa1, pa2, pa3, pa4, pa5 = st.columns([2.8, 1, 1, 1, 0.9])
        with pa1:
            sel = st.selectbox("d", list(results.keys()),
                               label_visibility="collapsed", key="sel_domain")
        r_sel    = results.get(sel,{})
        fb_pages = r_sel.get("Facebook",[])
        all_e_s  = r_sel.get("All Emails",[])
        best_s   = r_sel.get("Best Email","")

        with pa2:
            if st.button("🔍 Validate", key="val_one", type="primary",
                         disabled=not best_s, use_container_width=True):
                st.session_state[f"vrun_{sel}"] = True; st.rerun()
        with pa3:
            if st.button("𝒇 Facebook", key="fb_act", type="secondary",
                         disabled=not fb_pages, use_container_width=True):
                st.session_state[f"fbrun_{sel}"] = True; st.rerun()
        with pa4:
            if st.button("⟳ MX Check", key="mx_act", type="secondary",
                         disabled=not (DNS_AVAILABLE and all_e_s), use_container_width=True):
                st.session_state[f"mxrun_{sel}"] = True; st.rerun()
        with pa5:
            if all_e_s:
                st.download_button("⬇", "\n".join(all_e_s),
                                   f"{sel}_emails.txt", key="copy_em", use_container_width=True)

        # show validation result inline if available
        val_data = r_sel.get("Validation", {})
        if val_data:
            icon   = val_icon(val_data.get("status",""))
            reason = val_data.get("reason","—")
            spf    = "✓ SPF" if val_data.get("spf") else "✗ SPF"
            ca     = "⚠ catch-all" if val_data.get("catch_all") else ""
            parts  = [p for p in [reason, spf, ca] if p]
            st.markdown(
                f'<div style="margin-top:8px;font-size:11.5px;color:#555;">'
                f'<strong style="color:#0f0f0f">{icon} {best_s}</strong>'
                f' &nbsp;·&nbsp; {" · ".join(parts)}'
                f'</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # validate single
        if sel and st.session_state.get(f"vrun_{sel}"):
            st.session_state[f"vrun_{sel}"] = False
            with st.spinner(f"Validating {best_s}…"):
                vres = validate_email_full(best_s)
            st.session_state.results[sel]["Validation"] = vres; st.rerun()

        # validate all
        if st.session_state.get("run_validate_all"):
            st.session_state["run_validate_all"] = False
            todo = [(d,r["Best Email"]) for d,r in results.items()
                    if r.get("Best Email") and not r.get("Validation")]
            if todo:
                vph = st.empty()
                for i,(dom,em) in enumerate(todo):
                    vph.markdown(
                        f'<div class="log-box"><div class="ll-site">Validating {i+1}/{len(todo)}</div>'
                        f'<div class="ll-page">↳ {em}</div></div>', unsafe_allow_html=True)
                    st.session_state.results[dom]["Validation"] = validate_email_full(em)
                vph.empty(); st.rerun()

        # FB scrape
        if sel and st.session_state.get(f"fbrun_{sel}"):
            st.session_state[f"fbrun_{sel}"] = False
            fb_ph = st.empty(); fb_l = []
            def fb_log(item, kind):
                fb_l.append((item, kind))
                h = "".join(f'<div class="{"ll-email" if k=="email" else "ll-done"}">{t[1]}</div>'
                            for t,k in fb_l[-15:])
                fb_ph.markdown(f'<div class="log-box">{h}</div>', unsafe_allow_html=True)
            found = scrape_facebook_page(fb_pages[0], fb_log)
            if found:
                upd = sort_by_tier(set(all_e_s)|found)
                st.session_state.results[sel]["All Emails"] = upd
                st.session_state.results[sel]["Best Email"] = pick_best(set(upd)) or ""
            time.sleep(0.3); st.rerun()

        # MX check
        if sel and st.session_state.get(f"mxrun_{sel}") and DNS_AVAILABLE:
            st.session_state[f"mxrun_{sel}"] = False
            mx_ph = st.empty(); mx_l = []; new_mx = {}
            for email in all_e_s:
                res = check_mx(email); new_mx[email] = res; mx_l.append((email,res))
                rh = "".join(f'<div class="{"ll-email" if g else "ll-skip"}">{"✓" if g else "✗"} {e}</div>'
                             for e,g in mx_l)
                ok = sum(1 for _,g in mx_l if g)
                mx_ph.markdown(f'<div class="log-box"><div class="ll-info">MX — {ok}/{len(mx_l)} valid</div>{rh}</div>',
                               unsafe_allow_html=True)
            st.session_state.results[sel]["MX"] = new_mx
            valid = [e for e in all_e_s if new_mx.get(e) is not False]
            if len(valid) < len(all_e_s):
                st.session_state.results[sel]["All Emails"] = valid
            time.sleep(0.2); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  SCAN ENGINE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.scan_state == "running":
    queue = st.session_state.scan_queue
    idx   = st.session_state.scan_idx
    if idx < len(queue):
        url = queue[idx]
        if not url.startswith("http"): url = "https://"+url
        st.session_state.log_lines.append((("site", urlparse(url).netloc, None, None), "site"))
        cb = log_cb_factory(log_ph)
        if mode_key == "Quick":
            row = scrape_quick_site(url, cb)
        else:
            row = scrape_one_site(url, cfg, st.session_state.skip_t1,
                                  st.session_state.respect_robots, cb)
        st.session_state.results[row["Domain"]] = row
        st.session_state.scraped_domains.add(row["Domain"])
        st.session_state.scan_idx = idx + 1
        time.sleep(cfg.get("delay", 0.2))
        if st.session_state.scan_idx >= len(queue):
            st.session_state.scan_state = "done"
            if st.session_state.get("auto_validate"):
                st.session_state["run_validate_all"] = True
        st.rerun()
    else:
        st.session_state.scan_state = "done"; st.rerun()

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re, io, time, xml.etree.ElementTree as ET, random, pandas as pd
import urllib.robotparser, smtplib, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from email_validator import validate_email as ev_validate, EmailNotValidError
from collections import deque
from datetime import datetime

try:
    import dns.resolver as _dns_resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

# ── DISPOSABLE LIST ───────────────────────────────────────────────────────────
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
            "https://raw.githubusercontent.com/disposable-email-domains/"
            "disposable-email-domains/main/disposable_email_blocklist.conf",
            timeout=8)
        if r.status_code == 200:
            return set(r.text.splitlines())
    except Exception:
        pass
    return _DISPOSABLE_FALLBACK

FREE_EMAIL_DOMAINS = {
    "gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com",
    "icloud.com","protonmail.com","zoho.com","live.com","msn.com",
}

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MailHunter", page_icon="✉", layout="wide",
                   initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
.block-container { padding: 1.4rem 1.8rem 4rem !important; max-width: 100% !important; background: #f7f7f5 !important; }

/* logo */
.logo { font-size: 19px; font-weight: 800; color: #111; letter-spacing: -.5px;
        display: inline-flex; align-items: center; gap: 9px; }
.logo-icon { width: 30px; height: 30px; background: #111; border-radius: 8px;
             display: inline-flex; align-items: center; justify-content: center;
             font-size: 15px; color: #fff; flex-shrink: 0; }
.logo-sub { font-size: 11.5px; color: #aaa; margin-top: 3px; font-weight: 400; }

/* section labels */
.lbl { font-size: 10px; font-weight: 700; letter-spacing: 1.1px;
       text-transform: uppercase; color: #bbb; display: block; margin-bottom: 5px; }

/* buttons */
.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 12.5px !important;
    transition: all 0.14s ease !important; height: 36px !important;
    letter-spacing: -.1px !important;
}
.stButton > button[kind="primary"] {
    background: #111 !important; border: none !important; color: #fff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.18) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #333 !important; transform: translateY(-1px) !important;
    box-shadow: 0 3px 8px rgba(0,0,0,.2) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #e6e6e6 !important; color: #bbb !important;
    box-shadow: none !important; transform: none !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important; border: 1.5px solid #ddd !important; color: #555 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #999 !important; color: #111 !important; background: #fafaf8 !important;
}

/* download button */
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 12.5px !important; height: 36px !important;
    background: #fff !important; border: 1.5px solid #ddd !important; color: #555 !important;
}
.stDownloadButton > button:hover { border-color: #999 !important; color: #111 !important; }

/* textarea */
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important; font-size: 11.5px !important;
    border-radius: 8px !important; border: 1.5px solid #e5e5e5 !important;
    background: #fcfcfc !important; line-height: 1.65 !important; resize: none !important;
}
.stTextArea textarea:focus { border-color: #111 !important; box-shadow: 0 0 0 3px rgba(0,0,0,.05) !important; }
.stTextArea textarea::placeholder { color: #ccc !important; }

/* text input */
.stTextInput > div > input {
    border-radius: 8px !important; border: 1.5px solid #e5e5e5 !important;
    font-size: 13px !important; height: 36px !important; background: #fcfcfc !important;
}
.stTextInput > div > input:focus { border-color: #111 !important; box-shadow: 0 0 0 3px rgba(0,0,0,.05) !important; }

/* mode radio pill */
[data-testid="stHorizontalRadio"] {
    background: #efefed !important; border-radius: 10px !important;
    padding: 3px !important; border: 1px solid #e4e4e2 !important;
}
[data-testid="stHorizontalRadio"] label {
    font-size: 12px !important; font-weight: 600 !important;
    border-radius: 7px !important; padding: 5px 10px !important;
    cursor: pointer !important; color: #999 !important; transition: all .12s !important;
}
[data-testid="stHorizontalRadio"] label:has(input:checked) {
    background: #fff !important; color: #111 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.1) !important;
}
[data-testid="stHorizontalRadio"] [data-baseweb="radio"] { display: none !important; }

/* metrics */
[data-testid="stMetric"] {
    background: #fff; border: 1px solid #eaeae8; border-radius: 10px;
    padding: .75rem .9rem !important; transition: box-shadow .12s;
}
[data-testid="stMetric"]:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); }
[data-testid="stMetricLabel"] p {
    font-size: 10px !important; font-weight: 700 !important; color: #bbb !important;
    text-transform: uppercase !important; letter-spacing: .5px !important;
}
[data-testid="stMetricValue"] {
    font-size: 22px !important; font-weight: 800 !important;
    color: #111 !important; letter-spacing: -.6px !important;
}

/* live log */
.log-box {
    background: #fafaf8; border: 1px solid #e8e8e4; border-radius: 8px;
    padding: 9px 11px; font-family: 'JetBrains Mono', monospace; font-size: 10.5px;
    line-height: 1.8; max-height: 200px; overflow-y: auto; margin-top: 6px;
}
.log-box::-webkit-scrollbar { width: 4px; }
.log-box::-webkit-scrollbar-thumb { background: #d0cfcb; border-radius: 2px; }
.ll-site  { color: #111; font-weight: 700; border-top: 1px solid #eee;
            margin-top: 3px; padding-top: 3px; }
.ll-site:first-child { border-top: none; margin-top: 0; padding-top: 0; }
.ll-email { color: #15803d; font-weight: 600; }
.ll-page  { color: #ccc; }
.ll-skip  { color: #d97706; }
.ll-timing{ color: #ccc; font-size: 10px; }
.ll-done  { color: #aaa; }
.ll-social{ color: #2563eb; }
.ll-info  { color: #bbb; font-style: italic; }
.ll-warn  { color: #dc2626; }
.ll-fb    { color: #1d4ed8; }

/* parallel tile grid */
.site-tiles { display: flex; flex-wrap: wrap; gap: 5px; margin: 6px 0; }
.site-tile {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    background: #fff; border: 1px solid #e4e4e0; border-radius: 6px;
    padding: 4px 8px; display: flex; align-items: center; gap: 5px;
}
.tile-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.tile-dot.running  { background: #4ade80; animation: blink 1.2s infinite; }
.tile-dot.done     { background: #22c55e; }
.tile-dot.error    { background: #ef4444; }
.tile-dot.queued   { background: #d1d5db; }

/* progress */
.prog-row  { display:flex; justify-content:space-between; align-items:center;
             font-size:11.5px; font-weight:600; margin-bottom:4px; color:#333; }
.prog-sub  { font-size:11px; color:#aaa; font-weight:400; }
.prog-track{ height:3px; background:#eee; border-radius:99px; overflow:hidden; }
.prog-fill { height:100%; background:#111; border-radius:99px; transition:width .3s; }
.scan-dot  { display:inline-block; width:7px; height:7px; background:#4ade80;
             border-radius:50%; margin-right:5px; animation:blink 1.4s infinite; }
.scan-dot.paused { background:#fb923c; animation:none; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }

/* mode card */
.mode-card {
    background: #f4f4f2; border: 1px solid #e4e4e0; border-radius: 8px;
    padding: 9px 12px; margin: 6px 0 2px; display: flex; gap: 10px; align-items: flex-start;
}
.mode-card-icon { font-size: 18px; margin-top: 1px; flex-shrink: 0; }
.mode-card-name { font-size: 12.5px; font-weight: 700; color: #111; }
.mode-card-desc { font-size: 11px; color: #888; margin-top: 2px; line-height: 1.5; }

/* url pills */
.pills { display:flex; flex-wrap:wrap; gap:3px; margin:5px 0 1px; }
.pill  { font-family:'JetBrains Mono',monospace; font-size:10px;
         background:#efefed; border:1px solid #e0e0dc; border-radius:4px;
         padding:2px 6px; color:#888; }

/* filter chip bar */
.flt-bar .stButton > button {
    height: 28px !important; font-size: 11px !important;
    border-radius: 99px !important; padding: 0 10px !important;
    font-weight: 600 !important;
}
.flt-bar .stButton > button[kind="secondary"] {
    background: #efefed !important; border: 1px solid #e0e0dc !important; color: #888 !important;
}
.flt-bar .stButton > button[kind="secondary"]:hover {
    background: #e5e5e3 !important; color: #333 !important;
}
/* active chip accent per position */
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(1) button[kind="primary"]{background:#111 !important;border-color:#111 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(2) button[kind="primary"]{background:#d97706 !important;border-color:#d97706 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(3) button[kind="primary"]{background:#6366f1 !important;border-color:#6366f1 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(4) button[kind="primary"]{background:#64748b !important;border-color:#64748b !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(5) button[kind="primary"]{background:#e11d48 !important;border-color:#e11d48 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(6) button[kind="primary"]{background:#16a34a !important;border-color:#16a34a !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(7) button[kind="primary"]{background:#d97706 !important;border-color:#d97706 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(8) button[kind="primary"]{background:#dc2626 !important;border-color:#dc2626 !important;}
/* tinted inactive */
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(2) button[kind="secondary"]{color:#b45309 !important;background:#fffbeb !important;border-color:#fde68a !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(3) button[kind="secondary"]{color:#4f46e5 !important;background:#eef2ff !important;border-color:#c7d2fe !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(4) button[kind="secondary"]{color:#475569 !important;background:#f1f5f9 !important;border-color:#cbd5e1 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(5) button[kind="secondary"]{color:#be123c !important;background:#fff1f2 !important;border-color:#fecdd3 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(6) button[kind="secondary"]{color:#15803d !important;background:#f0fdf4 !important;border-color:#bbf7d0 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(7) button[kind="secondary"]{color:#b45309 !important;background:#fffbeb !important;border-color:#fde68a !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(8) button[kind="secondary"]{color:#b91c1c !important;background:#fff5f5 !important;border-color:#fecaca !important;}

/* confidence bar */
.conf-bar { height:3px; border-radius:99px; display:inline-block; vertical-align: middle; }

/* action card */
.action-card {
    background: #fafaf8; border: 1px solid #e8e8e4; border-radius: 10px;
    padding: 12px 14px; margin-top: 2px;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px !important; background: #efefed !important;
    border-radius: 8px !important; padding: 3px !important;
    border: 1px solid #e4e4e2 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 12px !important; font-weight: 600 !important;
    border-radius: 6px !important; padding: 4px 12px !important; color: #999 !important;
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: #111 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.08) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* expander */
details { border: 1px solid #eaeae8 !important; border-radius: 8px !important; background: #fff !important; }
details > summary { font-size: 12.5px !important; font-weight: 600 !important; color: #333 !important; padding: 10px 14px !important; }
details[open] > summary { border-bottom: 1px solid #f0f0ee !important; }

/* divider */
hr { border-color: #eee !important; margin: 10px 0 !important; }

/* sliders */
[data-testid="stSlider"] > div > div > div > div { background: #111 !important; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
TIER1 = re.compile(r"^(editor|admin|press|advert|contact)[a-z0-9._%+\-]*@", re.IGNORECASE)
TIER2 = re.compile(r"^(info|sales|hello|office|team|support|help)[a-z0-9._%+\-]*@", re.IGNORECASE)
BLOCKED_TLDS = {
    'png','jpg','jpeg','webp','gif','svg','ico','bmp','tiff','avif','mp4','mp3',
    'wav','ogg','mov','avi','webm','pdf','zip','rar','tar','gz','7z','js','css',
    'php','asp','aspx','xml','json','ts','jsx','tsx','woff','woff2','ttf','eot',
    'otf','map','exe','dmg','pkg','deb','apk',
}
PLACEHOLDER_DOMAINS = {
    'example.com','example.org','example.net','test.com','domain.com',
    'yoursite.com','yourwebsite.com','website.com','email.com','placeholder.com',
}
PLACEHOLDER_LOCALS = {
    'you','user','name','email','test','example','someone','username',
    'yourname','youremail','enter','address','sample',
}
SUPPRESS_PREFIXES = [
    'noreply','no-reply','donotreply','do-not-reply','mailer-daemon','bounce',
    'bounces','unsubscribe','notifications','notification','newsletter',
    'newsletters','postmaster','webmaster','auto-reply','autoreply','daemon',
    'robot','alerts','alert','system',
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
]
PRIORITY_KEYWORDS = [
    ("contact",100),("write-for-us",95),("writeforus",95),("write_for_us",95),
    ("guest-post",90),("guest_post",90),("guestpost",90),
    ("advertise",88),("advertising",88),("contribute",85),("contributor",85),
    ("submit",82),("submission",82),("pitch",80),
    ("about",75),("about-us",75),("about_us",75),
    ("team",70),("our-team",70),("staff",70),("people",70),
    ("work-with-us",68),("partner",65),("reach-us",60),
    ("get-in-touch",60),("press",55),("media",50),
]
HUNT_KEYWORDS = [
    # Hunt mode — outreach-only keywords, higher threshold
    ("write-for-us",100),("writeforus",100),("write_for_us",100),
    ("guest-post",98),("guest_post",98),("guestpost",98),
    ("advertise",95),("advertising",95),("sponsor",90),
    ("contribute",88),("contributor",88),("submit",85),("submission",85),
    ("pitch",83),("work-with-us",80),("partner",78),
]
TWITTER_SKIP  = {'share','intent','home','search','hashtag','i','status','twitter','x'}
LINKEDIN_SKIP = {'share','shareArticle','in','company','pub','feed','login','authwall'}
FACEBOOK_SKIP = {'sharer','share','dialog','login','home','watch','groups','events','marketplace'}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_DEFAULTS = {
    "results":{}, "scraped_domains":set(), "scan_state":"idle",
    "scan_queue":[], "scan_idx":0, "log_lines":[], "sessions":[],
    "mode":"Quick", "tbl_filter":"All",
    "skip_t1":True, "respect_robots":False, "scrape_fb":False,
    "auto_validate":False, "mx_cache":{},
    "seen_emails":set(),          # dedup across sessions
    "parallel":True,              # parallel scraping toggle
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CORE EMAIL HELPERS ────────────────────────────────────────────────────────
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

def confidence_score(email, val_data):
    """0–100 score combining tier, MX, SPF, catch-all, deliverability."""
    if not val_data: return None
    s = 100
    t = tier_key(email)
    if t == "2": s -= 10
    if t == "3": s -= 25
    if not val_data.get("spf"):      s -= 15
    if val_data.get("catch_all"):    s -= 20
    if val_data.get("free"):         s -= 8
    status = val_data.get("status","")
    if status == "Risky":            s -= 30
    if status == "Not Deliverable":  s -= 65
    return max(0, s)

def conf_color(score):
    if score is None: return "#ccc"
    if score >= 75: return "#16a34a"
    if score >= 45: return "#d97706"
    return "#dc2626"

# ── FETCH HELPERS ─────────────────────────────────────────────────────────────
def make_headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.5"}

def fetch_page(url, timeout=10):
    """Fetch a page, returns (html|None, status_code)."""
    try:
        r = requests.get(url, headers=make_headers(), timeout=timeout, allow_redirects=True)
        ct = r.headers.get("Content-Type","")
        if "text" in ct and r.ok:
            return r.text, r.status_code
        return None, r.status_code
    except Exception:
        return None, 0

def is_rate_limited(status):
    return status in (429, 503)

def is_blocked(status, html):
    if status == 403: return True
    if html and "cloudflare" in html.lower() and "challenge" in html.lower(): return True
    return False

# ── EXTRACTION ────────────────────────────────────────────────────────────────
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

def find_outreach_links(html, base_url, root_domain):
    KW = ["write for us","write-for-us","guest post","guest-post","contribute",
          "submission","submit a","pitch","advertise","advertising","sponsor",
          "work with us","partner","become a contributor"]
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

def robots_ok(rp, url):
    if rp is None: return True
    try: return rp.can_fetch("*", url)
    except: return True

# ── VALIDATION ENGINE ─────────────────────────────────────────────────────────
def _val_syntax(email):
    try: ev_validate(email); return True
    except EmailNotValidError: return False

def _val_mx(domain):
    try:
        recs = _dns_resolver.resolve(domain, "MX")
        return True, [str(r.exchange) for r in recs]
    except Exception: return False, []

def _val_spf(domain):
    try:
        for rd in _dns_resolver.resolve(domain, "TXT"):
            if "v=spf1" in str(rd): return True
    except Exception: pass
    return False

def _val_dmarc(domain):
    """Check _dmarc.domain TXT for v=DMARC1."""
    try:
        for rd in _dns_resolver.resolve(f"_dmarc.{domain}", "TXT"):
            if "v=DMARC1" in str(rd): return True
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
        if free: return ("Risky","Catch-all + free") if catch_all else ("Deliverable","Free provider")
        if catch_all:  return "Risky","Catch-all enabled"
        if not spf_ok: return "Risky","Missing SPF"
        return "Deliverable","—"
    else:
        if catch_all:  return "Risky","Catch-all, mailbox unknown"
        if free:       return "Deliverable","Free provider (unverified)"
        if not spf_ok: return "Risky","No SPF — spam risk"
        return "Deliverable","MX/SPF OK, mailbox unconfirmed"

def validate_email_full(email):
    disp = fetch_disposable_domains()
    domain = email.split("@")[-1].lower()
    syntax  = _val_syntax(email)
    mx_ok, mx_hosts = _val_mx(domain) if DNS_AVAILABLE else (False, [])
    spf_ok   = _val_spf(domain)   if DNS_AVAILABLE else False
    dmarc_ok = _val_dmarc(domain) if DNS_AVAILABLE else False
    disp_ok  = domain in disp
    free     = domain in FREE_EMAIL_DOMAINS
    mbox     = _val_mailbox(email, mx_hosts) if (mx_ok and DNS_AVAILABLE) else False
    ca       = _val_catch_all(domain, mx_hosts) if (mx_ok and DNS_AVAILABLE) else False
    status, reason = _deliverability(syntax, mx_ok, mbox, disp_ok, free, ca, mx_ok, spf_ok)
    return {"status":status,"reason":reason,"syntax":syntax,"mx":mx_ok,
            "spf":spf_ok,"dmarc":dmarc_ok,"mailbox":mbox,"disposable":disp_ok,
            "free":free,"catch_all":ca}

def val_icon(s):
    return {"Deliverable":"✅","Risky":"⚠️","Not Deliverable":"❌"}.get(s,"—")

def validate_with_fallback(all_emails, current_best, existing_val=None):
    """
    Validate current_best. If Risky or Not Deliverable,
    try remaining emails in tier order and return the first Deliverable one.
    Returns (chosen_email, validation_result, was_fallback).
    """
    if not current_best: return current_best, None, False

    # validate the current best
    if existing_val:
        val = existing_val
    else:
        val = validate_email_full(current_best)

    if val["status"] == "Deliverable":
        return current_best, val, False

    # Not ideal — try the rest in tier order
    others = [e for e in sort_by_tier(all_emails) if e != current_best]
    for email in others:
        alt_val = validate_email_full(email)
        if alt_val["status"] == "Deliverable":
            return email, alt_val, True

    # None deliverable — try to find least-bad (Risky > Not Deliverable)
    if val["status"] == "Risky":
        return current_best, val, False

    for email in others:
        alt_val = validate_email_full(email)
        if alt_val["status"] == "Risky":
            return email, alt_val, True

    return current_best, val, False

def check_mx(email):
    if not DNS_AVAILABLE: return None
    domain = email.split("@")[1].lower(); cache = st.session_state.mx_cache
    if domain in cache: return cache[domain]
    try: result = len(_dns_resolver.resolve(domain,"MX",lifetime=4)) > 0
    except: result = False
    cache[domain] = result; return result

# ── SITEMAP ENGINE ────────────────────────────────────────────────────────────
def fetch_sitemap_urls(root_url):
    urls = []
    for c in [urljoin(root_url,"/sitemap.xml"), urljoin(root_url,"/sitemap_index.xml")]:
        html, _ = fetch_page(c, timeout=8)
        if not html: continue
        try:
            root_el = ET.fromstring(html)
            ns = {"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root_el.findall(".//sm:loc",ns):
                u = loc.text.strip()
                if u.endswith(".xml"):
                    sub, _ = fetch_page(u, timeout=8)
                    if sub:
                        try:
                            for sl in ET.fromstring(sub).findall(".//sm:loc",ns):
                                urls.append(sl.text.strip())
                        except: pass
                else: urls.append(u)
        except: pass
        if urls: break
    return urls

def score_url(url, keyword_set=None):
    path = urlparse(url).path.lower(); best = 0
    kws = keyword_set or PRIORITY_KEYWORDS
    for kw, sc in kws:
        if kw in path:
            best = max(best, sc - path.count("/")*3)
    return best

def get_priority_urls(root_url, limit=None, hunt_mode=False):
    kws = HUNT_KEYWORDS if hunt_mode else PRIORITY_KEYWORDS
    sm_urls = fetch_sitemap_urls(root_url)
    if sm_urls:
        scored = sorted(
            [(u, score_url(u, kws)) for u in sm_urls if score_url(u, kws) > 0],
            key=lambda x: -x[1])
        urls = [u for u,_ in scored]
        return (urls[:limit] if limit else urls), True
    # fallback paths
    base = root_url.rstrip("/")
    paths = ["/contact","/contact-us","/about","/about-us","/team",
             "/write-for-us","/advertise","/contribute","/pitch","/submit",
             "/partner","/press","/guest-post","/work-with-us","/sponsor",
             "/submission","/contributors","/advertising","/staff","/people"]
    fallback = sorted(
        [(base+p, score_url(base+p, kws)) for p in paths if score_url(base+p, kws) > 0],
        key=lambda x: -x[1])
    urls = [u for u,_ in fallback]
    return (urls[:limit] if limit else urls), False

# ── FACEBOOK ──────────────────────────────────────────────────────────────────
def scrape_facebook_page(fb_handle, log_cb):
    slug = fb_handle.replace("facebook.com/","").strip("/")
    if not slug: return set()
    url = f"https://www.facebook.com/{slug}"
    log_cb(("info",f"FB: {slug}",None,None),"fb")
    t0 = time.time()
    html, status = fetch_page(url, timeout=14)
    elapsed = round(time.time()-t0,2)
    if html:
        found = extract_emails(html)
        for e in sort_by_tier(found): log_cb(("email",e,f"fb/{slug}",tier_label(e)),"email")
        log_cb(("timing",f"{elapsed}s · {len(found)} email(s) from Facebook",None,None),"timing")
        return found
    log_cb(("timing",f"{elapsed}s · Facebook blocked ({status})",None,None),"timing")
    return set()

# ── SCRAPE SINGLE SITE ────────────────────────────────────────────────────────
def _scrape_site_core(root_url, cfg, skip_t1, respect_robots, hunt_mode=False):
    """
    Core scraper used by both sequential and parallel modes.
    Returns (row_dict, log_list).
    """
    logs = []
    def log(item, kind): logs.append((item, kind))

    t0 = time.time(); root_domain = urlparse(root_url).netloc
    visited = set(); queue = deque()
    all_emails = set(); all_tw, all_li, all_fb = set(), set(), set()
    rp = load_robots(root_url, respect_robots)
    domain_blocked = False

    log(("info","Sitemap scan…",None,None),"info")
    priority_urls, used_sitemap = get_priority_urls(root_url, hunt_mode=hunt_mode,
                                                    limit=4 if cfg.get("quick") else None)
    src = f"sitemap → {len(priority_urls)} page(s)" if used_sitemap else f"known paths"
    log(("info",src,None,None),"info")

    quick_mode = cfg.get("quick", False)
    if not quick_mode:
        if cfg.get("sitemap") and used_sitemap:
            all_sm = fetch_sitemap_urls(root_url)
            pset = set(priority_urls)
            for u in all_sm:
                if u not in pset: queue.append((u, 0, False))

    for u in reversed(priority_urls):
        queue.appendleft((u, 0, True))
    if not quick_mode:
        queue.append((root_url, 0, False))

    max_pages = cfg.get("max_pages", 0) if not quick_mode else 0
    max_depth = cfg.get("max_depth", 0); pages_done = 0
    retry_urls = []

    while queue and (quick_mode or pages_done < max_pages + len(priority_urls)):
        url, depth, is_priority = queue.popleft()
        if url in visited: continue
        visited.add(url)

        short = url.replace("https://","").replace("http://","")[:60]

        if not robots_ok(rp, url):
            log(("timing",f"robots blocked",short,None),"timing")
            if not is_priority: pages_done += 1
            continue

        log(("page_start",short,"priority" if is_priority else f"{pages_done+1}/{max_pages}",None),"active")
        t_p = time.time()
        tmo = 5 if quick_mode else 10
        html, status = fetch_page(url, timeout=tmo)
        elapsed = round(time.time()-t_p,2)

        if is_rate_limited(status):
            log(("warn",f"Rate limited ({status}) — retrying after 6s…",short,None),"warn")
            time.sleep(6)
            html, status = fetch_page(url, timeout=tmo)

        if html and is_blocked(status, html):
            log(("warn",f"Blocked ({status}) — skipping domain",short,None),"warn")
            domain_blocked = True; break

        if html:
            found = extract_emails(html); new = found - all_emails
            tw, li, fb = extract_social(html)
            new_tw=tw-all_tw; new_li=li-all_li; new_fb=fb-all_fb
            all_emails.update(found); all_tw.update(tw); all_li.update(li); all_fb.update(fb)

            if not hunt_mode:
                for wlink in find_outreach_links(html, url, root_domain):
                    if wlink not in visited:
                        queue.appendleft((wlink,0,True))
                        log(("info",f"outreach → {wlink.replace('https://','')[:40]}",None,None),"info")

            for e in sort_by_tier(new): log(("email",e,short,tier_label(e)),"email")
            for h in sorted(new_tw|new_li|new_fb): log(("social",h,short,None),"social")
            log(("timing",f"{elapsed}s · {len(new)} email(s)",None,None),"timing")

            if not is_priority and not quick_mode and depth < max_depth:
                for link in get_internal_links(html, url, root_domain):
                    if link not in visited: queue.append((link,depth+1,False))

            if skip_t1 and any(TIER1.match(e) for e in all_emails):
                t1e = next(e for e in all_emails if TIER1.match(e))
                log(("skip",f"Tier 1 found ({t1e})",None,None),"skip"); break
        else:
            log(("timing",f"{elapsed}s · no response ({status})",None,None),"timing")

        if not is_priority: pages_done += 1
        if quick_mode and pages_done >= 4: break

    total_t = round(time.time()-t0,1)
    best = pick_best(all_emails)
    log(("done",f"{root_domain} — {len(all_emails)} email(s) in {total_t}s",None,None),"done")

    row = {
        "Domain": root_domain, "Best Email": best or "",
        "Best Tier": tier_short(best) if best else "",
        "All Emails": sort_by_tier(all_emails),
        "Twitter": sorted(all_tw), "LinkedIn": sorted(all_li), "Facebook": sorted(all_fb),
        "Pages Scraped": pages_done, "Total Time": total_t,
        "Source URL": root_url, "MX": {}, "Blocked": domain_blocked,
    }
    return row, logs

# ── LOG RENDERER ──────────────────────────────────────────────────────────────
def render_log(ph, lines=None):
    src = lines if lines is not None else st.session_state.log_lines
    h = ""
    for item, kind in src[-70:]:
        _, text, _, extra = item
        if   kind=="site":   h+=f'<div class="ll-site">▶ {text}</div>'
        elif kind=="active": h+=f'<div class="ll-page">  ↳ {text}</div>'
        elif kind=="email":  h+=f'<div class="ll-email">  ✉ {text}</div>'
        elif kind=="social": h+=f'<div class="ll-social">  ⟐ {text}</div>'
        elif kind=="timing": h+=f'<div class="ll-timing">    {text}</div>'
        elif kind=="skip":   h+=f'<div class="ll-skip">  ⚡ {text}</div>'
        elif kind=="done":   h+=f'<div class="ll-done">  ✓ {text}</div>'
        elif kind in ("info","fb"): h+=f'<div class="ll-info">  {text}</div>'
        elif kind=="warn":   h+=f'<div class="ll-warn">  ⚠ {text}</div>'
    ph.markdown(f'<div class="log-box">{h}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PRE-LOAD
# ─────────────────────────────────────────────────────────────────────────────
fetch_disposable_domains()

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([5,1])
with hc1:
    st.markdown(
        '<div class="logo"><div class="logo-icon">✉</div>MailHunter</div>'
        '<div class="logo-sub">Sitemap-first scraper &nbsp;·&nbsp; parallel engine'
        ' &nbsp;·&nbsp; SMTP validation &nbsp;·&nbsp; confidence scoring</div>',
        unsafe_allow_html=True)
with hc2:
    if st.session_state.results:
        rows_csv = []
        for d, r in st.session_state.results.items():
            val = r.get("Validation",{}) or {}
            vb  = r.get("ValidatedBest",{}) or {}
            rows_csv.append({
                "Domain":d,
                "Best Email":r.get("Best Email",""),
                "Validated Best":r.get("ValidatedBestEmail",""),
                "Was Fallback":r.get("WasFallback",False),
                "Deliverability":val.get("status",""),
                "Reason":val.get("reason",""),
                "Confidence":r.get("Confidence",""),
                "SPF":val.get("spf",""),"MX":val.get("mx",""),
                "DMARC":val.get("dmarc",""),
                "Catch-All":val.get("catch_all",""),
                "Disposable":val.get("disposable",""),
                "Free":val.get("free",""),
                "All Emails":"; ".join(r.get("All Emails",[])),
                "Twitter":"; ".join(r.get("Twitter",[])),
                "LinkedIn":"; ".join(r.get("LinkedIn",[])),
                "Facebook":"; ".join(r.get("Facebook",[])),
                "Pages":r.get("Pages Scraped",0),
                "Time(s)":r.get("Total Time",""),
                "Source URL":r.get("Source URL",""),
            })
        buf = io.StringIO(); pd.DataFrame(rows_csv).to_csv(buf,index=False)
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
    tab_paste, tab_csv = st.tabs(["Paste", "Upload CSV / TXT"])
    urls_to_scrape = []

    with tab_paste:
        raw = st.text_area("u", label_visibility="collapsed",
                           placeholder="https://magazine.com\nhttps://techblog.io\nnewspaper.org",
                           height=110, key="url_input")
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
        pills = "".join(f'<span class="pill">{u.replace("https://","")[:22]}</span>'
                        for u in urls_to_scrape[:6])
        if len(urls_to_scrape)>6: pills+=f'<span class="pill">+{len(urls_to_scrape)-6}</span>'
        st.markdown(f'<div class="pills">{pills}</div>', unsafe_allow_html=True)

    # ── MODE ─────────────────────────────────────────────────────────────
    st.markdown('<span class="lbl" style="margin-top:14px;display:block">Crawl Mode</span>',
                unsafe_allow_html=True)

    MODE_CFG = {
        "⚡ Quick": {
            "name":"Quick","icon":"⚡","color":"#7c3aed",
            "quick":True,"max_pages":0,"max_depth":0,"sitemap":False,"delay":0.05,
            "desc":"Reads your sitemap, scores every URL by keyword relevance, then hits "
                   "the top 4 contact/about/write-for-us pages only. Fastest mode — "
                   "typically under 10 seconds per site.",
        },
        "✦ Easy": {
            "name":"Easy","icon":"✦","color":"#16a34a",
            "quick":False,"max_pages":5,"max_depth":0,"sitemap":False,"delay":0.2,
            "desc":"Sitemap priority pages first, then homepage. Good for sites that "
                   "list contact emails on their main pages. ~30s per site.",
        },
        "◈ Medium": {
            "name":"Medium","icon":"◈","color":"#d97706",
            "quick":False,"max_pages":50,"max_depth":3,"sitemap":False,"delay":0.4,
            "desc":"Sitemap priority pages, then crawls internal links up to 3 levels "
                   "deep with a 50-page budget. Finds buried contact pages. ~2–5 min.",
        },
        "⬡ Extreme": {
            "name":"Extreme","icon":"⬡","color":"#dc2626",
            "quick":False,"max_pages":300,"max_depth":6,"sitemap":True,"delay":0.2,
            "desc":"Full sitemap crawl + deep link traversal up to 300 pages. "
                   "Leaves no stone unturned. Use for stubborn sites. 5–15 min.",
        },
        "🎯 Hunt": {
            "name":"Hunt","icon":"🎯","color":"#0891b2",
            "quick":False,"max_pages":8,"max_depth":1,"sitemap":False,"delay":0.1,
            "hunt":True,
            "desc":"Outreach-only mode. Ignores contact/about pages entirely — "
                   "scores only write-for-us, advertise, pitch, sponsor, contribute "
                   "URLs. Perfect for link building and partnership prospecting.",
        },
    }
    MODE_LABELS = list(MODE_CFG.keys())

    cur_label = next((l for l in MODE_LABELS if MODE_CFG[l]["name"]==st.session_state.mode),
                     MODE_LABELS[0])
    chosen = st.radio("mode_r", MODE_LABELS, index=MODE_LABELS.index(cur_label),
                      horizontal=True, label_visibility="collapsed", key="mode_radio")
    mi = MODE_CFG[chosen]
    if mi["name"] != st.session_state.mode:
        st.session_state.mode = mi["name"]; st.rerun()

    st.markdown(
        f'<div class="mode-card">'
        f'<div class="mode-card-icon">{mi["icon"]}</div>'
        f'<div>'
        f'<div class="mode-card-name" style="color:{mi["color"]}">{mi["name"]} Mode</div>'
        f'<div class="mode-card-desc">{mi["desc"]}</div>'
        f'</div></div>', unsafe_allow_html=True)

    mode_key = mi["name"]
    cfg = {k:v for k,v in mi.items() if k not in ("name","icon","color","desc")}

    if mode_key == "Medium":
        cfg["max_depth"] = st.slider("Crawl depth", 1, 6, 3, key="sl_depth")
        cfg["max_pages"] = st.slider("Pages / site", 10, 200, 50, key="sl_pages")
    elif mode_key == "Extreme":
        cfg["max_pages"] = st.slider("Pages / site", 50, 500, 300, key="sl_pagesx")

    # ── SCAN CONTROLS ────────────────────────────────────────────────────
    st.divider()
    scan_state = st.session_state.scan_state

    if scan_state == "idle":
        do_start = st.button("▶  Start Scan", type="primary",
                             use_container_width=True, disabled=not urls_to_scrape, key="btn_start")
    elif scan_state == "running":
        do_start = False
        cp,cc = st.columns(2)
        with cp:
            if st.button("⏸  Pause", type="primary", use_container_width=True, key="btn_pause"):
                st.session_state.scan_state="paused"; st.rerun()
        with cc:
            if st.button("✕  Stop", type="secondary", use_container_width=True, key="btn_stop"):
                st.session_state.scan_state="done"; st.rerun()
    elif scan_state == "paused":
        do_start = False
        cr,cc = st.columns(2)
        with cr:
            if st.button("▶  Resume", type="primary", use_container_width=True, key="btn_resume"):
                st.session_state.scan_state="running"; st.rerun()
        with cc:
            if st.button("✕  Stop", type="secondary", use_container_width=True, key="btn_stop2"):
                st.session_state.scan_state="done"; st.rerun()
    else:
        do_start = st.button("▶  New Scan", type="primary",
                             use_container_width=True, disabled=not urls_to_scrape, key="btn_new")

    ca_, cb_ = st.columns(2)
    with ca_:
        if st.button("🗑  Clear", type="secondary", use_container_width=True, key="btn_clear"):
            for k in ("results","scan_queue","log_lines"):
                st.session_state[k] = {} if k=="results" else []
            st.session_state.scan_state="idle"; st.session_state.scan_idx=0
            st.rerun()
    with cb_:
        if st.session_state.results and scan_state!="running":
            if st.button("💾  Save", type="secondary", use_container_width=True, key="btn_save"):
                ts = datetime.now().strftime("%b %d %H:%M")
                # add all current emails to seen set for dedup
                for r in st.session_state.results.values():
                    for e in r.get("All Emails",[]):
                        st.session_state.seen_emails.add(e)
                st.session_state.sessions.append({
                    "name":f"Scan {len(st.session_state.sessions)+1} · {ts}",
                    "results":dict(st.session_state.results)})
                st.rerun()

    do_start = do_start if "do_start" in dir() else False
    if do_start and urls_to_scrape:
        new_urls = [u for u in urls_to_scrape
                    if urlparse(u).netloc not in st.session_state.scraped_domains]
        if new_urls:
            if scan_state=="done": st.session_state.results={}
            st.session_state.update(scan_queue=new_urls, scan_idx=0,
                                    scan_state="running", log_lines=[])
            st.rerun()

    # ── PROGRESS + LOG ───────────────────────────────────────────────────
    prog_ph = st.empty()
    log_ph  = st.empty()

    if scan_state in ("running","paused") and st.session_state.scan_queue:
        idx=st.session_state.scan_idx; total=len(st.session_state.scan_queue)
        pct=int(idx/total*100) if total else 0
        dot="scan-dot paused" if scan_state=="paused" else "scan-dot"
        lbl="Paused" if scan_state=="paused" else "Scanning"
        done_count = len(st.session_state.results)
        prog_ph.markdown(f"""
        <div style="margin:8px 0 4px">
          <div class="prog-row">
            <span><span class="{dot}"></span>{lbl}</span>
            <span class="prog-sub">{done_count}/{total} sites · {pct}%</span>
          </div>
          <div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.log_lines:
        render_log(log_ph)

    # ── SETTINGS ─────────────────────────────────────────────────────────
    st.divider()
    with st.expander("⚙  Settings"):
        st.markdown("**Crawl**")
        st.session_state.skip_t1        = st.toggle("Stop once Tier 1 found",  value=st.session_state.skip_t1,        key="t_skip")
        st.session_state.respect_robots = st.toggle("Respect robots.txt",       value=st.session_state.respect_robots, key="t_robots")
        st.session_state.auto_validate  = st.toggle("Auto-validate after scan", value=st.session_state.auto_validate,  key="t_auto")
        st.session_state.parallel       = st.toggle("Parallel scraping (4×)",   value=st.session_state.parallel,       key="t_parallel",
                                                    help="Scrape up to 4 sites simultaneously")
        st.markdown("**Sources**")
        st.session_state.scrape_fb = st.toggle("Auto-scrape Facebook", value=st.session_state.scrape_fb, key="t_fb")
        n_mem = len(st.session_state.scraped_domains)
        n_seen = len(st.session_state.seen_emails)
        if n_mem or n_seen:
            st.caption(f"Domain memory: {n_mem}  ·  Seen emails: {n_seen}")
            if st.button("Clear memory", key="btn_mem", use_container_width=True):
                st.session_state.scraped_domains=set()
                st.session_state.seen_emails=set(); st.rerun()

    if st.session_state.sessions:
        with st.expander(f"💾  Sessions ({len(st.session_state.sessions)})"):
            for i,sess in enumerate(st.session_state.sessions):
                n_d=len(sess["results"])
                n_e=sum(len(r.get("All Emails",[])) for r in sess["results"].values())
                sc1,sc2,sc3=st.columns([3,1,1])
                with sc1: st.caption(f"**{sess['name']}** · {n_d} sites · {n_e} emails")
                with sc2:
                    if st.button("Load",key=f"load_{i}",use_container_width=True):
                        st.session_state.results=sess["results"]
                        st.session_state.scan_state="done"; st.rerun()
                with sc3:
                    if st.button("✕",key=f"del_{i}",use_container_width=True):
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
          <div style="width:54px;height:54px;background:#f0f0ee;border-radius:14px;
                      display:flex;align-items:center;justify-content:center;
                      font-size:22px;margin-bottom:18px;border:1px solid #e4e4e0">✉</div>
          <div style="font-size:17px;font-weight:800;color:#111;margin-bottom:8px;
                      letter-spacing:-.3px">No results yet</div>
          <div style="font-size:12px;color:#bbb;line-height:1.85;max-width:300px">
            Paste URLs on the left and hit <strong style="color:#444">▶ Start Scan</strong>.<br>
            <strong style="color:#7c3aed">Quick</strong> — hits contact pages via sitemap<br>
            <strong style="color:#0891b2">Hunt</strong> — finds write-for-us &amp; advertise pages<br>
            Enable <em>Parallel scraping</em> in Settings for 4× speed.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── METRICS ──────────────────────────────────────────────────────
        tot_d  = len(results)
        tot_e  = sum(len(r.get("All Emails",[])) for r in results.values())
        t1_cnt = sum(1 for r in results.values() if r.get("Best Tier","").startswith("Tier 1"))
        val_ok = sum(1 for r in results.values()
                     if (r.get("Validation",{}) or {}).get("status")=="Deliverable")
        fallbk = sum(1 for r in results.values() if r.get("WasFallback"))
        no_e   = sum(1 for r in results.values() if not r.get("Best Email"))

        mc1,mc2,mc3,mc4,mc5,mc6 = st.columns(6)
        mc1.metric("Sites",     tot_d)
        mc2.metric("Emails",    tot_e)
        mc3.metric("Tier 1",    t1_cnt)
        mc4.metric("Validated", val_ok)
        mc5.metric("Fallback",  fallbk,  help="Emails where best was bad, fallback found")
        mc6.metric("No Email",  no_e)

        # ── VALIDATE ALL ─────────────────────────────────────────────────
        if scan_state == "done":
            to_val = [d for d,r in results.items()
                      if r.get("All Emails") and not r.get("Validation")]
            if to_val:
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;'
                    f'border-radius:8px;padding:8px 14px;margin:4px 0;">'
                    f'<span style="font-size:12px;color:#15803d;font-weight:600">'
                    f'✓ {len(to_val)} domain(s) ready to validate — '
                    f'will try fallback emails if best is not deliverable</span></div>',
                    unsafe_allow_html=True)
                if st.button("🔍 Validate All  (with fallback)", key="val_all",
                             type="primary", use_container_width=True):
                    st.session_state["run_validate_all"]=True; st.rerun()

        # ── SEARCH + FILTER CHIPS ─────────────────────────────────────────
        search = st.text_input("s", placeholder="🔍  Search domains or emails…",
                               label_visibility="collapsed", key="search_box")

        FLT = [("All","All"),("🥇 T1","T1"),("🥈 T2","T2"),("🥉 T3","T3"),
               ("∅ None","None"),("✅ Deliv.","val_ok"),("⚠️ Risky","val_risky"),("❌ Bad","val_bad")]
        st.markdown('<div class="flt-bar">', unsafe_allow_html=True)
        fcols = st.columns(len(FLT))
        for col,(lbl,val) in zip(fcols,FLT):
            with col:
                active = st.session_state.tbl_filter==val
                if st.button(lbl, key=f"flt_{val}",
                             type="primary" if active else "secondary",
                             use_container_width=True):
                    st.session_state.tbl_filter=val; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── BUILD TABLE ───────────────────────────────────────────────────
        rows = []
        seen = st.session_state.seen_emails
        for domain, r in results.items():
            all_e = r.get("All Emails",[]); best = r.get("Best Email","")
            bt    = r.get("Best Tier","")
            vb    = r.get("ValidatedBestEmail","") or best
            val   = r.get("Validation",{}) or {}
            val_st= val.get("status","")
            conf  = r.get("Confidence")
            fb    = r.get("WasFallback",False)
            is_dup = best in seen and scan_state!="running"

            rows.append({
                "Domain":    domain,
                "Email":     (vb or "—") + (" ↻" if fb else "") + (" ★" if is_dup else ""),
                "Tier":      bt or "—",
                "Score":     conf if conf is not None else "—",
                "✓":         val_icon(val_st) if val_st else "—",
                "Reason":    val.get("reason","—") if val else "—",
                "SPF":       ("✓" if val.get("spf") else "✗") if val else "—",
                "DMARC":     ("✓" if val.get("dmarc") else "✗") if val else "—",
                "Catch-all": ("⚠" if val.get("catch_all") else "✓") if val else "—",
                "+":         f'+{len(all_e)-1}' if len(all_e)>1 else "",
                "Twitter":   (r.get("Twitter",[])+[""])[0],
                "LinkedIn":  (r.get("LinkedIn",[])+[""])[0],
                "Pages":     r.get("Pages Scraped",0),
                "s":         r.get("Total Time",""),
            })

        df = pd.DataFrame(rows)
        if search:
            m = (df["Domain"].str.contains(search,case=False,na=False) |
                 df["Email"].str.contains(search,case=False,na=False))
            df = df[m]

        flt = st.session_state.tbl_filter
        if   flt=="T1":        df = df[df["Tier"].str.startswith("Tier 1",na=False)]
        elif flt=="T2":        df = df[df["Tier"].str.startswith("Tier 2",na=False)]
        elif flt=="T3":        df = df[df["Tier"].str.startswith("Tier 3",na=False)]
        elif flt=="None":      df = df[df["Email"]=="—"]
        elif flt=="val_ok":    df = df[df["✓"]=="✅"]
        elif flt=="val_risky": df = df[df["✓"]=="⚠️"]
        elif flt=="val_bad":   df = df[df["✓"]=="❌"]

        st.caption(
            f'**{len(df)}** of {tot_d} domains &nbsp;·&nbsp; '
            f'<span style="color:#888;font-size:11px">↻ = fallback email used &nbsp; ★ = seen before</span>',
            unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True, hide_index=True,
                     height=min(560,44+max(len(df),1)*36),
                     column_config={
                         "Domain":   st.column_config.TextColumn("Domain",   width=150),
                         "Email":    st.column_config.TextColumn("Email",    width=195),
                         "Tier":     st.column_config.TextColumn("Tier",     width=68),
                         "Score":    st.column_config.NumberColumn("Score",  width=52),
                         "✓":        st.column_config.TextColumn("✓",        width=40),
                         "Reason":   st.column_config.TextColumn("Reason",   width=165),
                         "SPF":      st.column_config.TextColumn("SPF",      width=38),
                         "DMARC":    st.column_config.TextColumn("DMARC",    width=48),
                         "Catch-all":st.column_config.TextColumn("Catch-all",width=62),
                         "+":        st.column_config.TextColumn("+",        width=36),
                         "Twitter":  st.column_config.TextColumn("Twitter",  width=105),
                         "LinkedIn": st.column_config.TextColumn("LinkedIn", width=125),
                         "Pages":    st.column_config.NumberColumn("Pages",  width=48),
                         "s":        st.column_config.NumberColumn("s",      width=44),
                     })

        # ── PER-DOMAIN ACTIONS ────────────────────────────────────────────
        st.divider()
        st.markdown('<span class="lbl">Per-domain actions</span>', unsafe_allow_html=True)
        st.markdown('<div class="action-card">', unsafe_allow_html=True)
        pa1,pa2,pa3,pa4,pa5 = st.columns([2.8,1,1,1,0.8])
        with pa1:
            sel = st.selectbox("d", list(results.keys()),
                               label_visibility="collapsed", key="sel_domain")
        r_sel    = results.get(sel,{})
        fb_pages = r_sel.get("Facebook",[])
        all_e_s  = r_sel.get("All Emails",[])
        best_s   = r_sel.get("Best Email","")

        with pa2:
            if st.button("🔍 Validate", key="val_one", type="primary",
                         disabled=not all_e_s, use_container_width=True):
                st.session_state[f"vrun_{sel}"]=True; st.rerun()
        with pa3:
            if st.button("FB Scrape", key="fb_act", type="secondary",
                         disabled=not fb_pages, use_container_width=True):
                st.session_state[f"fbrun_{sel}"]=True; st.rerun()
        with pa4:
            if st.button("MX Check", key="mx_act", type="secondary",
                         disabled=not (DNS_AVAILABLE and all_e_s), use_container_width=True):
                st.session_state[f"mxrun_{sel}"]=True; st.rerun()
        with pa5:
            if all_e_s:
                st.download_button("⬇", "\n".join(all_e_s),
                                   f"{sel}_emails.txt", key="copy_em", use_container_width=True)

        # inline validation summary
        val_d = r_sel.get("Validation",{}) or {}
        if val_d:
            vbest = r_sel.get("ValidatedBestEmail","") or best_s
            icon  = val_icon(val_d.get("status",""))
            conf  = r_sel.get("Confidence")
            conf_c= conf_color(conf)
            fb_flag = " ↻ fallback" if r_sel.get("WasFallback") else ""
            spf   = "✓ SPF" if val_d.get("spf") else "✗ SPF"
            dmarc = "✓ DMARC" if val_d.get("dmarc") else ""
            ca    = "⚠ catch-all" if val_d.get("catch_all") else ""
            parts = [p for p in [val_d.get("reason",""), spf, dmarc, ca] if p and p!="—"]
            score_html = (f'<span style="color:{conf_c};font-weight:700">{conf}/100</span>'
                          if conf is not None else "")
            st.markdown(
                f'<div style="margin-top:8px;font-size:11.5px;color:#666;line-height:1.7">'
                f'<strong style="color:#111">{icon} {vbest}</strong>'
                f'<span style="color:#bbb;font-size:10px">{fb_flag}</span>'
                f' &nbsp;·&nbsp; {score_html}'
                f' &nbsp;·&nbsp; {" · ".join(parts)}'
                f'</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── validate single (with fallback) ──
        if sel and st.session_state.get(f"vrun_{sel}"):
            st.session_state[f"vrun_{sel}"]=False
            with st.spinner(f"Validating {sel}…"):
                chosen, vres, was_fb = validate_with_fallback(all_e_s, best_s)
            if vres:
                conf = confidence_score(chosen, vres)
                st.session_state.results[sel].update({
                    "Validation":vres,"ValidatedBestEmail":chosen,
                    "WasFallback":was_fb,"Confidence":conf})
            st.rerun()

        # ── validate all (with fallback) ──
        if st.session_state.get("run_validate_all"):
            st.session_state["run_validate_all"]=False
            todo = [(d,r) for d,r in results.items()
                    if r.get("All Emails") and not r.get("Validation")]
            if todo:
                vph=st.empty()
                for i,(dom,r) in enumerate(todo):
                    vph.markdown(
                        f'<div class="log-box"><div class="ll-site">Validating {i+1}/{len(todo)}: {dom}</div>'
                        f'<div class="ll-info">  Checking {r.get("Best Email","")}…</div></div>',
                        unsafe_allow_html=True)
                    chosen, vres, was_fb = validate_with_fallback(
                        r.get("All Emails",[]), r.get("Best Email",""))
                    if vres:
                        conf = confidence_score(chosen, vres)
                        st.session_state.results[dom].update({
                            "Validation":vres,"ValidatedBestEmail":chosen,
                            "WasFallback":was_fb,"Confidence":conf})
                vph.empty(); st.rerun()

        # ── FB scrape ──
        if sel and st.session_state.get(f"fbrun_{sel}"):
            st.session_state[f"fbrun_{sel}"]=False
            fb_ph=st.empty(); fb_l=[]
            def fb_log(item,kind):
                fb_l.append((item,kind))
                h="".join(f'<div class="{"ll-email" if k=="email" else "ll-done"}">{t[1]}</div>'
                           for t,k in fb_l[-15:])
                fb_ph.markdown(f'<div class="log-box">{h}</div>',unsafe_allow_html=True)
            found=scrape_facebook_page(fb_pages[0],fb_log)
            if found:
                upd=sort_by_tier(set(all_e_s)|found)
                st.session_state.results[sel]["All Emails"]=upd
                st.session_state.results[sel]["Best Email"]=pick_best(set(upd)) or ""
            time.sleep(0.3); st.rerun()

        # ── MX check ──
        if sel and st.session_state.get(f"mxrun_{sel}") and DNS_AVAILABLE:
            st.session_state[f"mxrun_{sel}"]=False
            mx_ph=st.empty(); mx_l=[]; new_mx={}
            for email in all_e_s:
                res=check_mx(email); new_mx[email]=res; mx_l.append((email,res))
                rh="".join(f'<div class="{"ll-email" if g else "ll-skip"}">{"✓" if g else "✗"} {e}</div>'
                           for e,g in mx_l)
                ok=sum(1 for _,g in mx_l if g)
                mx_ph.markdown(f'<div class="log-box"><div class="ll-info">MX — {ok}/{len(mx_l)} valid</div>{rh}</div>',
                               unsafe_allow_html=True)
            st.session_state.results[sel]["MX"]=new_mx
            valid=[e for e in all_e_s if new_mx.get(e) is not False]
            if len(valid)<len(all_e_s):
                st.session_state.results[sel]["All Emails"]=valid
            time.sleep(0.2); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  SCAN ENGINE  (sequential or parallel batch)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.scan_state == "running":
    queue   = st.session_state.scan_queue
    idx     = st.session_state.scan_idx
    total   = len(queue)
    use_parallel = st.session_state.get("parallel", True)
    BATCH   = 4 if use_parallel else 1

    if idx < total:
        batch_urls = queue[idx:idx+BATCH]
        skip_t1    = st.session_state.skip_t1
        respect    = st.session_state.respect_robots
        hunt       = cfg.get("hunt", False)

        if use_parallel and len(batch_urls) > 1:
            # ── parallel: run batch simultaneously ──
            lock = threading.Lock()
            all_logs = []

            def run_one(url):
                if not url.startswith("http"): url="https://"+url
                row, logs = _scrape_site_core(url, cfg, skip_t1, respect, hunt_mode=hunt)
                # prepend site marker
                site_log = [((("site", row["Domain"],None,None),"site"))]
                return row, site_log + [(item,kind) for item,kind in logs]

            batch_results = {}
            with ThreadPoolExecutor(max_workers=BATCH) as ex:
                futs = {ex.submit(run_one, u): u for u in batch_urls}
                for fut in as_completed(futs):
                    try:
                        row, logs = fut.result()
                        batch_results[row["Domain"]] = (row, logs)
                    except Exception as e:
                        pass

            # merge results and logs in URL order
            for url in batch_urls:
                domain = urlparse(url).netloc.replace("www.","")
                # find matching result
                for d,(row,logs) in batch_results.items():
                    if d == domain or d.endswith(domain) or domain.endswith(d):
                        st.session_state.results[d] = row
                        st.session_state.scraped_domains.add(d)
                        st.session_state.log_lines.extend(logs)
                        break

        else:
            # ── sequential: one site ──
            url = batch_urls[0]
            if not url.startswith("http"): url="https://"+url
            st.session_state.log_lines.append((("site",urlparse(url).netloc,None,None),"site"))
            row, logs = _scrape_site_core(url, cfg, skip_t1, respect, hunt_mode=hunt)
            st.session_state.log_lines.extend(logs)
            st.session_state.results[row["Domain"]] = row
            st.session_state.scraped_domains.add(row["Domain"])

        st.session_state.scan_idx = idx + len(batch_urls)
        time.sleep(cfg.get("delay",0.1))

        if st.session_state.scan_idx >= total:
            st.session_state.scan_state = "done"
            if st.session_state.get("auto_validate"):
                st.session_state["run_validate_all"] = True

        st.rerun()
    else:
        st.session_state.scan_state="done"; st.rerun()

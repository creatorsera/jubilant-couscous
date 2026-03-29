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

_DISPOSABLE_FALLBACK = {
    'mailinator.com','guerrillamail.com','tempmail.com','throwaway.email','yopmail.com',
    'sharklasers.com','spam4.me','trashmail.com','trashmail.me','maildrop.cc',
    '10minutemail.com','fakeinbox.com','discard.email','mailnesia.com',
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

st.set_page_config(page_title="MailHunter", page_icon="=", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
.block-container { padding: 1.5rem 2rem 4rem !important; max-width: 100% !important; background: #f5f5f3 !important; }

[data-testid="column"]:first-of-type {
    background: #fff; border-radius: 14px; border: 1px solid #e8e8e6;
    padding: 1.2rem 1.1rem 1rem !important;
}

.logo { font-size: 18px; font-weight: 800; color: #111; letter-spacing: -.5px;
        display: flex; align-items: center; gap: 9px; margin-bottom: 2px; }
.logo-box { width: 32px; height: 32px; background: #111; border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; flex-shrink: 0; color: #fff; }
.logo-tag { font-size: 11px; color: #bbb; font-weight: 400; letter-spacing: 0; }
.sec { font-size: 9.5px; font-weight: 700; letter-spacing: 1.3px;
       text-transform: uppercase; color: #c0c0bc; display: block; margin-bottom: 5px; }

.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 12.5px !important; height: 36px !important;
    transition: all 0.13s !important;
}
.stButton > button[kind="primary"] {
    background: #111 !important; border: 2px solid #111 !important;
    color: #fff !important; box-shadow: 0 1px 2px rgba(0,0,0,.15) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #2d2d2d !important; border-color: #2d2d2d !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.2) !important; transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #e4e4e4 !important; border-color: #e4e4e4 !important;
    color: #aaa !important; box-shadow: none !important; transform: none !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important; border: 1.5px solid #ddd !important; color: #555 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #999 !important; color: #111 !important; background: #fafaf8 !important;
}
.start-btn .stButton > button {
    height: 42px !important; font-size: 14px !important; font-weight: 700 !important;
}
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; font-size: 12.5px !important; height: 36px !important;
    background: #fff !important; border: 1.5px solid #ddd !important; color: #555 !important;
}
.stDownloadButton > button:hover { border-color: #999 !important; color: #111 !important; }

.stTextArea textarea {
    font-size: 12px !important; border-radius: 8px !important;
    border: 1.5px solid #e4e4e0 !important; background: #fafaf8 !important;
    line-height: 1.6 !important; resize: none !important; color: #333 !important;
}
.stTextArea textarea:focus {
    border-color: #111 !important; box-shadow: 0 0 0 3px rgba(0,0,0,.05) !important;
}
.stTextArea textarea::placeholder { color: #ccc !important; }
.stTextInput > div > input {
    border-radius: 8px !important; border: 1.5px solid #e4e4e0 !important;
    font-size: 13px !important; height: 36px !important; background: #fafaf8 !important;
}
.stTextInput > div > input:focus {
    border-color: #111 !important; box-shadow: 0 0 0 3px rgba(0,0,0,.05) !important;
}

[data-testid="stHorizontalRadio"] {
    background: #eeeeed !important; border-radius: 10px !important;
    padding: 3px !important; border: 1px solid #e2e2e0 !important; display: flex;
}
[data-testid="stHorizontalRadio"] label {
    font-size: 11.5px !important; font-weight: 600 !important;
    border-radius: 7px !important; padding: 5px 10px !important;
    color: #999 !important; flex: 1 !important; text-align: center !important;
    cursor: pointer !important; white-space: nowrap !important;
}
[data-testid="stHorizontalRadio"] label:has(input:checked) {
    background: #fff !important; color: #111 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.1) !important;
}
[data-testid="stHorizontalRadio"] [data-baseweb="radio"] { display: none !important; }

.mode-strip { display: flex; align-items: flex-start; gap: 9px; padding: 8px 11px;
    border-radius: 8px; background: #f8f8f6; border: 1px solid #e8e8e4; margin: 5px 0 0; }
.mode-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.mode-name { font-size: 12px; font-weight: 700; }
.mode-tip  { font-size: 10.5px; color: #888; margin-top: 2px; line-height: 1.45; }

[data-testid="stMetric"] {
    background: #fff; border: 1px solid #eaeae6; border-radius: 10px;
    padding: .7rem .85rem !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 9.5px !important; font-weight: 700 !important; color: #bbb !important;
    text-transform: uppercase !important; letter-spacing: .6px !important;
}
[data-testid="stMetricValue"] {
    font-size: 22px !important; font-weight: 800 !important;
    color: #111 !important; letter-spacing: -.7px !important;
}

.log-box {
    background: #1c1c1c; border-radius: 8px; padding: 10px 12px;
    font-family: 'Courier New', Courier, monospace; font-size: 10.5px;
    line-height: 1.8; max-height: 210px; overflow-y: auto; margin-top: 6px;
}
.log-box::-webkit-scrollbar { width: 4px; }
.log-box::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }
.ll-site  { color: #fff; font-weight: 700; margin-top:4px; padding-top:4px;
             border-top: 1px solid #2a2a2a; }
.ll-site:first-child { border-top:none; margin-top:0; padding-top:0; }
.ll-email { color: #4ade80; font-weight: 600; }
.ll-page  { color: #444; }
.ll-skip  { color: #fb923c; }
.ll-timing{ color: #3a3a3a; font-size: 10px; }
.ll-done  { color: #555; }
.ll-social{ color: #60a5fa; }
.ll-info  { color: #444; }
.ll-warn  { color: #f87171; }

.prog-wrap { margin: 8px 0 2px; }
.prog-top  { display:flex; justify-content:space-between; align-items:center;
              font-size:12px; font-weight:600; color:#333; margin-bottom:5px; }
.prog-right{ font-size:11px; color:#aaa; font-weight:400; }
.prog-track{ height:4px; background:#eee; border-radius:99px; overflow:hidden; }
.prog-fill { height:100%; border-radius:99px; transition:width .4s ease; }
.scan-dot  { display:inline-block; width:7px; height:7px; border-radius:50%;
              margin-right:6px; animation:pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.25;transform:scale(.8)} }

.flt-bar .stButton > button {
    height: 27px !important; font-size: 10.5px !important;
    border-radius: 99px !important; padding: 0 9px !important; font-weight: 600 !important;
}
.flt-bar .stButton > button[kind="secondary"] {
    background: #eeeeed !important; border: 1px solid #e0e0dc !important; color: #888 !important;
}
.flt-bar .stButton > button[kind="secondary"]:hover {
    background: #e4e4e2 !important; color: #333 !important; border-color:#ccc !important;
}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(1) button[kind="primary"]{background:#111 !important;border-color:#111 !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(2) button[kind="primary"]{background:#d97706 !important;border-color:#d97706 !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(3) button[kind="primary"]{background:#6366f1 !important;border-color:#6366f1 !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(4) button[kind="primary"]{background:#64748b !important;border-color:#64748b !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(5) button[kind="primary"]{background:#e11d48 !important;border-color:#e11d48 !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(6) button[kind="primary"]{background:#16a34a !important;border-color:#16a34a !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(7) button[kind="primary"]{background:#d97706 !important;border-color:#d97706 !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(8) button[kind="primary"]{background:#dc2626 !important;border-color:#dc2626 !important;color:#fff !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(2) button[kind="secondary"]{color:#92400e !important;background:#fffbeb !important;border-color:#fde68a !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(3) button[kind="secondary"]{color:#4338ca !important;background:#eef2ff !important;border-color:#c7d2fe !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(4) button[kind="secondary"]{color:#475569 !important;background:#f1f5f9 !important;border-color:#cbd5e1 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(5) button[kind="secondary"]{color:#be123c !important;background:#fff1f2 !important;border-color:#fecdd3 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(6) button[kind="secondary"]{color:#15803d !important;background:#f0fdf4 !important;border-color:#bbf7d0 !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(7) button[kind="secondary"]{color:#92400e !important;background:#fffbeb !important;border-color:#fde68a !important;}
.flt-bar [data-testid="stHorizontalBlock"]>div:nth-child(8) button[kind="secondary"]{color:#b91c1c !important;background:#fff5f5 !important;border-color:#fecaca !important;}

.act-card { background:#fafaf8; border:1px solid #e8e8e4; border-radius:10px; padding:11px 13px; margin-top:3px; }
.val-result { margin-top:8px; font-size:11.5px; color:#666; padding:6px 9px;
               background:#fff; border:1px solid #eee; border-radius:6px; line-height:1.6; }
.pills { display:flex; flex-wrap:wrap; gap:3px; margin:5px 0 0; }
.pill  { font-size:10.5px; background:#eeeeed; border:1px solid #e0e0dc;
         border-radius:4px; padding:2px 7px; color:#888; }

.stTabs [data-baseweb="tab-list"] {
    gap:2px !important; background:#eeeeed !important; border-radius:8px !important;
    padding:3px !important; border:1px solid #e2e2e0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size:11.5px !important; font-weight:600 !important; border-radius:6px !important;
    padding:4px 12px !important; color:#999 !important;
}
.stTabs [aria-selected="true"] {
    background:#fff !important; color:#111 !important; box-shadow:0 1px 3px rgba(0,0,0,.08) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display:none !important; }
details { border:1px solid #e8e8e4 !important; border-radius:8px !important; }
details > summary {
    font-size:12px !important; font-weight:600 !important;
    color:#444 !important; padding:9px 13px !important;
}
details[open] > summary { border-bottom:1px solid #f0f0ee !important; }
hr { border-color:#eeeeec !important; margin:10px 0 !important; }
[data-testid="stSlider"] > div > div > div > div { background:#111 !important; }
</style>
""", unsafe_allow_html=True)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
TIER1 = re.compile(r"^(editor|admin|press|advert|contact)[a-z0-9._%+\-]*@", re.IGNORECASE)
TIER2 = re.compile(r"^(info|sales|hello|office|team|support|help)[a-z0-9._%+\-]*@", re.IGNORECASE)
BLOCKED_TLDS = {'png','jpg','jpeg','webp','gif','svg','ico','bmp','tiff','avif','mp4','mp3',
    'wav','ogg','mov','avi','webm','pdf','zip','rar','tar','gz','7z','js','css','php',
    'asp','aspx','xml','json','ts','jsx','tsx','woff','woff2','ttf','eot','otf','map','exe','dmg','pkg','deb','apk'}
PLACEHOLDER_DOMAINS = {'example.com','example.org','example.net','test.com','domain.com',
    'yoursite.com','yourwebsite.com','website.com','email.com','placeholder.com'}
PLACEHOLDER_LOCALS  = {'you','user','name','email','test','example','someone','username',
    'yourname','youremail','enter','address','sample'}
SUPPRESS_PREFIXES   = ['noreply','no-reply','donotreply','do-not-reply','mailer-daemon',
    'bounce','bounces','unsubscribe','notifications','notification','newsletter',
    'newsletters','postmaster','webmaster','auto-reply','autoreply','daemon',
    'robot','alerts','alert','system']
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
]
PRIORITY_KEYWORDS = [
    ("contact",100),("write-for-us",95),("writeforus",95),("write_for_us",95),
    ("guest-post",90),("guest_post",90),("guestpost",90),("advertise",88),("advertising",88),
    ("contribute",85),("contributor",85),("submit",82),("submission",82),("pitch",80),
    ("about",75),("about-us",75),("about_us",75),("team",70),("our-team",70),("staff",70),
    ("people",70),("work-with-us",68),("partner",65),("reach-us",60),("get-in-touch",60),
    ("press",55),("media",50),
]
HUNT_KEYWORDS = [
    ("write-for-us",100),("writeforus",100),("write_for_us",100),
    ("guest-post",98),("guest_post",98),("guestpost",98),("advertise",96),("advertising",96),
    ("sponsor",92),("contribute",90),("contributor",90),("submit",86),("submission",86),
    ("pitch",84),("work-with-us",82),("partner",78),
]
TWITTER_SKIP  = {'share','intent','home','search','hashtag','i','status','twitter','x'}
LINKEDIN_SKIP = {'share','shareArticle','in','company','pub','feed','login','authwall'}
FACEBOOK_SKIP = {'sharer','share','dialog','login','home','watch','groups','events','marketplace'}

MODE_CFG = {
    "Quick":   {"quick":True,"max_pages":0,"max_depth":0,"sitemap":False,"delay":0.05,"hunt":False,
                "icon":"lightning","color":"#7c3aed","tag":"Sitemap top-4 priority pages",
                "tip":"Reads sitemap, scores URLs, scrapes top 4 contact/about/write-for-us pages. ~5-15s per site."},
    "Easy":    {"quick":False,"max_pages":5,"max_depth":0,"sitemap":False,"delay":0.2,"hunt":False,
                "icon":"star","color":"#16a34a","tag":"Priority pages + homepage",
                "tip":"Sitemap priority pages first, then homepage. Good for well-structured sites. ~30s per site."},
    "Medium":  {"quick":False,"max_pages":50,"max_depth":3,"sitemap":False,"delay":0.4,"hunt":False,
                "icon":"diamond","color":"#d97706","tag":"Sitemap-first then crawl links",
                "tip":"Priority pages then crawls up to 50 internal pages 3 levels deep. Finds buried contacts. 2-5 min."},
    "Extreme": {"quick":False,"max_pages":300,"max_depth":6,"sitemap":True,"delay":0.2,"hunt":False,
                "icon":"hex","color":"#dc2626","tag":"Full sitemap + deep crawl",
                "tip":"Exhaustive - full sitemap plus 300-page deep crawl. Nothing gets missed. 5-15 min per site."},
    "Hunt":    {"quick":False,"max_pages":8,"max_depth":1,"sitemap":False,"delay":0.1,"hunt":True,
                "icon":"target","color":"#0891b2","tag":"Write-for-us and advertise pages only",
                "tip":"Outreach mode. Skips contact/about - scores only write-for-us, advertise, sponsor, pitch pages."},
}

for k, v in {
    "results":{},"scraped_domains":set(),"scan_state":"idle","scan_queue":[],"scan_idx":0,
    "log_lines":[],"sessions":[],"mode":"Quick","tbl_filter":"All",
    "skip_t1":True,"respect_robots":False,"scrape_fb":False,
    "auto_validate":False,"parallel":True,"mx_cache":{},"seen_emails":set(),
}.items():
    if k not in st.session_state: st.session_state[k] = v

def is_valid_email(email):
    e = email.strip()
    if not e or e.count('@') != 1: return False
    local, domain = e.split('@'); lo, do = local.lower(), domain.lower()
    if not local or not domain: return False
    if local.startswith('.') or local.endswith('.') or local.startswith('-'): return False
    if len(local) > 64 or len(domain) > 255: return False
    if '.' not in domain: return False
    tld = do.rsplit('.',1)[-1]
    if len(tld) < 2 or tld in BLOCKED_TLDS: return False
    if re.search(r'@\d+x[\-\d]','@'+do): return False
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
def tier_label(e): return {"1":"[T1]","2":"[T2]","3":"[T3]"}[tier_key(e)]
def sort_by_tier(emails): return sorted(emails, key=tier_key)

def pick_best(emails):
    pool = [e for e in emails if is_valid_email(e)]
    if not pool: return None
    for pat in [TIER1, TIER2]:
        h = [e for e in pool if pat.match(e)]
        if h: return h[0]
    return pool[0]

def confidence_score(email, val):
    if not val: return None
    s = 100; t = tier_key(email)
    if t == "2": s -= 10
    if t == "3": s -= 25
    if not val.get("spf"):       s -= 15
    if val.get("catch_all"):     s -= 20
    if val.get("free"):          s -= 8
    st_ = val.get("status","")
    if st_ == "Risky":           s -= 30
    if st_ == "Not Deliverable": s -= 65
    return max(0, s)

def conf_color(sc):
    if sc is None: return "#ccc"
    if sc >= 75: return "#16a34a"
    if sc >= 45: return "#d97706"
    return "#dc2626"

def make_headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.5"}

def fetch_page(url, timeout=10):
    try:
        r = requests.get(url, headers=make_headers(), timeout=timeout, allow_redirects=True)
        if "text" in r.headers.get("Content-Type","") and r.ok:
            return r.text, r.status_code
        return None, r.status_code
    except Exception:
        return None, 0

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
    soup = BeautifulSoup(html,"html.parser"); found = []
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

def _val_syntax(email):
    try: ev_validate(email); return True
    except EmailNotValidError: return False

def _val_mx(domain):
    try:
        recs = _dns_resolver.resolve(domain, "MX")
        return True, [str(r.exchange) for r in recs]
    except: return False, []

def _val_spf(domain):
    try:
        for rd in _dns_resolver.resolve(domain, "TXT"):
            if "v=spf1" in str(rd): return True
    except: pass
    return False

def _val_dmarc(domain):
    try:
        for rd in _dns_resolver.resolve(f"_dmarc.{domain}", "TXT"):
            if "v=DMARC1" in str(rd): return True
    except: pass
    return False

def _val_mailbox(email, mx_records):
    try:
        mx = mx_records[0].rstrip(".")
        with smtplib.SMTP(mx, timeout=6) as s:
            s.helo("example.com"); s.mail("test@example.com")
            code, _ = s.rcpt(email)
            return code == 250
    except: return False

def _val_catch_all(domain, mx_records):
    try:
        mx = mx_records[0].rstrip(".")
        with smtplib.SMTP(mx, timeout=6) as s:
            s.helo("example.com"); s.mail("test@example.com")
            code, _ = s.rcpt(f"randomaddress9x7z@{domain}")
            return code == 250
    except: return False

def _deliverability(syntax, domain_ok, mailbox_ok, disposable, free, catch_all, mx_ok, spf_ok):
    if not syntax:    return "Not Deliverable","Invalid syntax"
    if not domain_ok: return "Not Deliverable","Domain doesn't exist"
    if disposable:    return "Not Deliverable","Disposable domain"
    if not mx_ok:     return "Not Deliverable","No MX records"
    if mailbox_ok:
        if free: return ("Risky","Catch-all + free") if catch_all else ("Deliverable","Free provider")
        if catch_all:  return "Risky","Catch-all enabled"
        if not spf_ok: return "Risky","Missing SPF"
        return "Deliverable","--"
    else:
        if catch_all:  return "Risky","Catch-all, mailbox unknown"
        if free:       return "Deliverable","Free provider (unverified)"
        if not spf_ok: return "Risky","No SPF - spam risk"
        return "Deliverable","MX/SPF OK, mailbox unconfirmed"

def validate_email_full(email):
    disp = fetch_disposable_domains()
    domain = email.split("@")[-1].lower()
    syntax = _val_syntax(email)
    mx_ok, mx_h = _val_mx(domain) if DNS_AVAILABLE else (False,[])
    spf   = _val_spf(domain)   if DNS_AVAILABLE else False
    dmarc = _val_dmarc(domain) if DNS_AVAILABLE else False
    disp_ = domain in disp
    free  = domain in FREE_EMAIL_DOMAINS
    mbox  = _val_mailbox(email, mx_h) if (mx_ok and DNS_AVAILABLE) else False
    ca    = _val_catch_all(domain, mx_h) if (mx_ok and DNS_AVAILABLE) else False
    status, reason = _deliverability(syntax, mx_ok, mbox, disp_, free, ca, mx_ok, spf)
    return {"status":status,"reason":reason,"syntax":syntax,"mx":mx_ok,
            "spf":spf,"dmarc":dmarc,"mailbox":mbox,"disposable":disp_,"free":free,"catch_all":ca}

def val_icon(s): return {"Deliverable":"OK","Risky":"RISK","Not Deliverable":"FAIL"}.get(s,"--")
def val_emoji(s): return {"Deliverable":"v","Risky":"~","Not Deliverable":"x"}.get(s,"")

def validate_with_fallback(all_emails, current_best, existing_val=None):
    if not current_best or not all_emails: return current_best, None, False
    val = existing_val or validate_email_full(current_best)
    if val["status"] == "Deliverable": return current_best, val, False
    for email in sort_by_tier(all_emails):
        if email == current_best: continue
        v = validate_email_full(email)
        if v["status"] == "Deliverable": return email, v, True
    if val["status"] == "Not Deliverable":
        for email in sort_by_tier(all_emails):
            if email == current_best: continue
            v = validate_email_full(email)
            if v["status"] == "Risky": return email, v, True
    return current_best, val, False

def check_mx(email):
    if not DNS_AVAILABLE: return None
    domain = email.split("@")[1].lower(); cache = st.session_state.mx_cache
    if domain in cache: return cache[domain]
    try: result = len(_dns_resolver.resolve(domain,"MX",lifetime=4)) > 0
    except: result = False
    cache[domain] = result; return result

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

def score_url(url, kws):
    path = urlparse(url).path.lower(); best = 0
    for kw, sc in kws:
        if kw in path: best = max(best, sc - path.count("/")*3)
    return best

def get_priority_urls(root_url, hunt_mode=False, limit=None):
    kws = HUNT_KEYWORDS if hunt_mode else PRIORITY_KEYWORDS
    sm_urls = fetch_sitemap_urls(root_url)
    if sm_urls:
        scored = sorted([(u, score_url(u,kws)) for u in sm_urls if score_url(u,kws)>0],
                        key=lambda x:-x[1])
        urls = [u for u,_ in scored]
        return (urls[:limit] if limit else urls), True
    base = root_url.rstrip("/")
    paths = ["/contact","/contact-us","/about","/about-us","/team","/write-for-us",
             "/advertise","/contribute","/pitch","/submit","/partner","/press",
             "/guest-post","/work-with-us","/sponsor","/submission","/contributors",
             "/advertising","/staff","/people","/get-in-touch"]
    fb = sorted([(base+p, score_url(base+p,kws)) for p in paths if score_url(base+p,kws)>0],
                key=lambda x:-x[1])
    urls = [u for u,_ in fb]
    return (urls[:limit] if limit else urls), False

def _scrape_site(root_url, cfg_snap, skip_t1, respect_robots, scrape_fb_flag):
    """Thread-safe scraper. No st.session_state access. Returns (row, logs)."""
    logs = []
    def log(item, kind): logs.append((item,kind))

    t0 = time.time(); root_domain = urlparse(root_url).netloc
    visited = set(); queue = deque()
    all_emails = set(); all_tw, all_li, all_fb = set(), set(), set()
    rp = load_robots(root_url, respect_robots)

    quick_mode  = cfg_snap.get("quick", False)
    hunt_mode   = cfg_snap.get("hunt",  False)
    max_pages   = cfg_snap.get("max_pages", 0)
    max_depth   = cfg_snap.get("max_depth", 0)
    use_sitemap = cfg_snap.get("sitemap", False)

    log(("info","scanning sitemap...",None,None),"info")
    limit = 4 if quick_mode else None
    priority_urls, used_sitemap = get_priority_urls(root_url, hunt_mode=hunt_mode, limit=limit)
    src = f"sitemap: {len(priority_urls)} pages" if used_sitemap else "no sitemap, using known paths"
    log(("info",src,None,None),"info")

    if not quick_mode and use_sitemap and used_sitemap:
        all_sm = fetch_sitemap_urls(root_url)
        pset = set(priority_urls)
        for u in all_sm:
            if u not in pset: queue.append((u,0,False))

    for u in reversed(priority_urls): queue.appendleft((u,0,True))
    if not quick_mode: queue.append((root_url,0,False))

    pages_done = 0; domain_blocked = False
    page_limit = max_pages + len(priority_urls)

    while queue and (quick_mode or pages_done < page_limit):
        url, depth, is_priority = queue.popleft()
        if url in visited: continue
        visited.add(url)
        short = url.replace("https://","").replace("http://","")[:55]

        if not robots_ok(rp, url):
            if not is_priority: pages_done += 1
            continue

        log(("page_start", short, "P" if is_priority else str(pages_done+1), None), "active")
        tmo = 6 if quick_mode else 12
        t_p = time.time(); html, status = fetch_page(url, timeout=tmo)
        elapsed = round(time.time()-t_p, 2)

        if status in (429, 503):
            log(("warn",f"rate limited ({status}), retry...",short,None),"warn")
            time.sleep(7)
            html, status = fetch_page(url, timeout=tmo)

        if status == 403 and (not html or "cloudflare" in (html or "").lower()):
            log(("warn",f"blocked ({status}) - skipping",short,None),"warn")
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
                        log(("info",f"outreach: {wlink.replace('https://','')[:38]}",None,None),"info")

            for e in sort_by_tier(new): log(("email",e,short,tier_label(e)),"email")
            for h in sorted(new_tw|new_li|new_fb): log(("social",h,short,None),"social")
            log(("timing",f"{elapsed}s - {len(new)} email(s)",None,None),"timing")

            if not is_priority and not quick_mode and depth < max_depth:
                for link in get_internal_links(html, url, root_domain):
                    if link not in visited: queue.append((link,depth+1,False))

            if skip_t1 and any(TIER1.match(e) for e in all_emails):
                t1e = next(e for e in all_emails if TIER1.match(e))
                log(("skip",f"tier 1 found ({t1e}) - done",None,None),"skip"); break
        else:
            log(("timing",f"{elapsed}s - no response ({status})",None,None),"timing")

        if not is_priority: pages_done += 1
        if quick_mode and pages_done >= 4: break

    if scrape_fb_flag and all_fb:
        slug = sorted(all_fb)[0].replace("facebook.com/","").strip("/")
        if slug:
            log(("info",f"FB: {slug}",None,None),"info")
            fb_html, _ = fetch_page(f"https://www.facebook.com/{slug}", timeout=14)
            if fb_html:
                fb_emails = extract_emails(fb_html)
                for e in sort_by_tier(fb_emails): log(("email",e,"fb",""),"email")
                all_emails.update(fb_emails)

    best = pick_best(all_emails); total_t = round(time.time()-t0,1)
    log(("done",f"{root_domain} - {len(all_emails)} email(s) in {total_t}s",None,None),"done")

    return {
        "Domain":root_domain,"Best Email":best or "","Best Tier":tier_short(best) if best else "",
        "All Emails":sort_by_tier(all_emails),"Twitter":sorted(all_tw),
        "LinkedIn":sorted(all_li),"Facebook":sorted(all_fb),
        "Pages Scraped":pages_done,"Total Time":total_t,"Source URL":root_url,"MX":{},
        "Blocked":domain_blocked,
    }, logs

def render_log(ph):
    h = ""
    for item, kind in st.session_state.log_lines[-80:]:
        _, text, _, extra = item
        t = str(text)[:88]
        if   kind=="site":   h+=f'<div class="ll-site">[ {t} ]</div>'
        elif kind=="active": h+=f'<div class="ll-page">  &gt; {t}</div>'
        elif kind=="email":  h+=f'<div class="ll-email">  @ {t}</div>'
        elif kind=="social": h+=f'<div class="ll-social">  ~ {t}</div>'
        elif kind=="timing": h+=f'<div class="ll-timing">    {t}</div>'
        elif kind=="skip":   h+=f'<div class="ll-skip">  ! {t}</div>'
        elif kind=="done":   h+=f'<div class="ll-done">  ok {t}</div>'
        elif kind=="info":   h+=f'<div class="ll-info">  . {t}</div>'
        elif kind=="warn":   h+=f'<div class="ll-warn">  !! {t}</div>'
    ph.markdown(f'<div class="log-box">{h}</div>', unsafe_allow_html=True)

fetch_disposable_domains()

hc1, hc2 = st.columns([5,1])
with hc1:
    st.markdown(
        '<div class="logo"><div class="logo-box">M</div>MailHunter</div>'
        '<div class="logo-tag">sitemap-first &nbsp;|&nbsp; parallel engine &nbsp;|&nbsp; '
        'SMTP validation &nbsp;|&nbsp; fallback emails &nbsp;|&nbsp; confidence score</div>',
        unsafe_allow_html=True)
with hc2:
    if st.session_state.results:
        rows_csv = []
        for d, r in st.session_state.results.items():
            val = r.get("Validation",{}) or {}
            rows_csv.append({
                "Domain":d,"Best Email":r.get("Best Email",""),
                "Validated Best":r.get("ValidatedBestEmail",""),
                "Was Fallback":r.get("WasFallback",False),
                "Deliverability":val.get("status",""),"Reason":val.get("reason",""),
                "Confidence":r.get("Confidence",""),
                "SPF":val.get("spf",""),"MX":val.get("mx",""),"DMARC":val.get("dmarc",""),
                "Catch-All":val.get("catch_all",""),
                "All Emails":"; ".join(r.get("All Emails",[])),
                "Twitter":"; ".join(r.get("Twitter",[])),
                "LinkedIn":"; ".join(r.get("LinkedIn",[])),
                "Pages":r.get("Pages Scraped",0),"Time(s)":r.get("Total Time",""),
                "Source URL":r.get("Source URL",""),
            })
        buf = io.StringIO(); pd.DataFrame(rows_csv).to_csv(buf,index=False)
        st.download_button("Export CSV", buf.getvalue(),
                           f"mailhunter_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           "text/csv", key="export_top")
st.divider()

left, right = st.columns([1, 2.8], gap="large")

with left:
    st.markdown('<span class="sec">Target URLs</span>', unsafe_allow_html=True)
    tp, tc = st.tabs(["Paste", "Upload"])
    urls_to_scrape = []

    with tp:
        raw = st.text_area("u", label_visibility="collapsed",
                           placeholder="https://magazine.com\nhttps://techblog.io\nnewspaper.org",
                           height=105, key="url_input")
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            if not line.startswith("http"): line = "https://"+line
            urls_to_scrape.append(line)

    with tc:
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
                    st.caption(f"OK {len(urls_to_scrape)} URLs")
                except Exception as ex: st.error(f"CSV error: {ex}")
            else:
                for line in rb.decode("utf-8","ignore").splitlines():
                    line=line.strip()
                    if not line: continue
                    if not line.startswith("http"): line="https://"+line
                    urls_to_scrape.append(line)
                st.caption(f"OK {len(urls_to_scrape)} URLs")

    if urls_to_scrape:
        pills = "".join(f'<span class="pill">{u.replace("https://","")[:20]}</span>'
                        for u in urls_to_scrape[:5])
        if len(urls_to_scrape)>5: pills+=f'<span class="pill">+{len(urls_to_scrape)-5}</span>'
        st.markdown(f'<div class="pills">{pills}</div>', unsafe_allow_html=True)

    st.markdown('<span class="sec" style="margin-top:14px;display:block">Crawl Mode</span>',
                unsafe_allow_html=True)

    MODE_LABELS = list(MODE_CFG.keys())
    cur_mode = st.session_state.get("mode","Quick")
    if cur_mode not in MODE_LABELS: cur_mode = "Quick"

    chosen = st.radio("mode_r", MODE_LABELS, index=MODE_LABELS.index(cur_mode),
                      horizontal=True, label_visibility="collapsed", key="mode_radio")
    if chosen != st.session_state.mode:
        st.session_state.mode = chosen; st.rerun()

    mi = MODE_CFG[chosen]
    st.markdown(
        f'<div class="mode-strip">'
        f'<div class="mode-dot" style="background:{mi["color"]}"></div>'
        f'<div>'
        f'<div class="mode-name" style="color:{mi["color"]}">{chosen} &mdash; {mi["tag"]}</div>'
        f'<div class="mode-tip">{mi["tip"]}</div>'
        f'</div></div>', unsafe_allow_html=True)

    mode_key = chosen
    cfg = {k:v for k,v in mi.items() if k not in ("icon","color","tag","tip")}

    if mode_key == "Medium":
        cfg["max_depth"] = st.slider("Depth", 1, 6, 3, key="sl_d")
        cfg["max_pages"] = st.slider("Pages/site", 10, 200, 50, key="sl_p")
    elif mode_key == "Extreme":
        cfg["max_pages"] = st.slider("Pages/site", 50, 500, 300, key="sl_px")

    st.divider()
    scan_state = st.session_state.scan_state

    if scan_state == "idle":
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        do_start = st.button("Start Scan", type="primary",
                             use_container_width=True, disabled=not urls_to_scrape, key="btn_s")
        st.markdown('</div>', unsafe_allow_html=True)
    elif scan_state == "running":
        do_start = False
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Pause", type="primary", use_container_width=True, key="btn_p"):
                st.session_state.scan_state="paused"; st.rerun()
        with c2:
            if st.button("Stop", type="secondary", use_container_width=True, key="btn_st"):
                st.session_state.scan_state="done"; st.rerun()
    elif scan_state == "paused":
        do_start = False
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Resume", type="primary", use_container_width=True, key="btn_r"):
                st.session_state.scan_state="running"; st.rerun()
        with c2:
            if st.button("Stop", type="secondary", use_container_width=True, key="btn_st2"):
                st.session_state.scan_state="done"; st.rerun()
    else:
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        do_start = st.button("New Scan", type="primary",
                             use_container_width=True, disabled=not urls_to_scrape, key="btn_ns")
        st.markdown('</div>', unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        if st.button("Clear", type="secondary", use_container_width=True, key="btn_cl"):
            for k in ("results","scan_queue","log_lines"):
                st.session_state[k] = {} if k=="results" else []
            st.session_state.scan_state="idle"; st.session_state.scan_idx=0; st.rerun()
    with c2:
        if st.session_state.results and scan_state!="running":
            if st.button("Save", type="secondary", use_container_width=True, key="btn_sv"):
                ts = datetime.now().strftime("%b %d %H:%M")
                for r in st.session_state.results.values():
                    for e in r.get("All Emails",[]): st.session_state.seen_emails.add(e)
                st.session_state.sessions.append({
                    "name":f"Scan {len(st.session_state.sessions)+1} - {ts}",
                    "results":dict(st.session_state.results)})
                st.rerun()

    do_start = do_start if "do_start" in dir() else False
    if do_start and urls_to_scrape:
        new_urls = [u for u in urls_to_scrape
                    if urlparse(u).netloc not in st.session_state.scraped_domains]
        if new_urls:
            if scan_state=="done": st.session_state.results={}
            st.session_state.update(scan_queue=new_urls,scan_idx=0,
                                    scan_state="running",log_lines=[])
            st.rerun()

    prog_ph = st.empty()
    log_ph  = st.empty()

    if scan_state in ("running","paused") and st.session_state.scan_queue:
        idx   = st.session_state.scan_idx
        total = len(st.session_state.scan_queue)
        pct   = round(idx/total*100,1) if total else 0
        done  = len(st.session_state.results)
        paused_ = scan_state=="paused"
        dot_c = "#fb923c" if paused_ else "#4ade80"
        bar_c = "#fb923c" if paused_ else "#16a34a"
        lbl   = "Paused" if paused_ else "Scanning"
        par_n = " | 4x parallel" if st.session_state.get("parallel",True) else ""
        prog_ph.markdown(f"""
        <div class="prog-wrap">
          <div class="prog-top">
            <span><span class="scan-dot" style="background:{dot_c}"></span>{lbl}</span>
            <span class="prog-right">{done} done / {total} total{par_n}</span>
          </div>
          <div class="prog-track">
            <div class="prog-fill" style="width:{pct}%;background:{bar_c}"></div>
          </div>
          <div style="font-size:10px;color:#bbb;margin-top:2px;text-align:right">{pct}%</div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.log_lines:
        render_log(log_ph)

    st.divider()
    with st.expander("Settings"):
        st.session_state.parallel       = st.toggle("Parallel scraping (4x faster)", value=st.session_state.parallel, key="t_par")
        st.session_state.skip_t1        = st.toggle("Stop once Tier 1 found",        value=st.session_state.skip_t1,  key="t_sk")
        st.session_state.respect_robots = st.toggle("Respect robots.txt",             value=st.session_state.respect_robots, key="t_rb")
        st.session_state.auto_validate  = st.toggle("Auto-validate after scan",       value=st.session_state.auto_validate,  key="t_av")
        st.session_state.scrape_fb      = st.toggle("Auto-scrape Facebook",           value=st.session_state.scrape_fb,      key="t_fb")
        n_mem = len(st.session_state.scraped_domains)
        n_seen= len(st.session_state.seen_emails)
        if n_mem or n_seen:
            st.caption(f"Memory: {n_mem} domains | {n_seen} seen emails")
            if st.button("Clear memory", key="btn_mem", use_container_width=True):
                st.session_state.scraped_domains=set()
                st.session_state.seen_emails=set(); st.rerun()

    if st.session_state.sessions:
        with st.expander(f"Saved sessions ({len(st.session_state.sessions)})"):
            for i, sess in enumerate(st.session_state.sessions):
                nd=len(sess["results"])
                ne=sum(len(r.get("All Emails",[])) for r in sess["results"].values())
                a,b,c = st.columns([3,1,1])
                with a: st.caption(f"**{sess['name']}** | {nd} sites | {ne} emails")
                with b:
                    if st.button("Load",key=f"ld_{i}",use_container_width=True):
                        st.session_state.results=sess["results"]
                        st.session_state.scan_state="done"; st.rerun()
                with c:
                    if st.button("Del",key=f"dl_{i}",use_container_width=True):
                        st.session_state.sessions.pop(i); st.rerun()

with right:
    results    = st.session_state.results
    scan_state = st.session_state.scan_state

    if not results:
        mi_ = MODE_CFG.get(st.session_state.mode, MODE_CFG["Quick"])
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:80px 0;text-align:center">
          <div style="font-size:38px;margin-bottom:14px;opacity:.12">M</div>
          <div style="font-size:17px;font-weight:800;color:#111;letter-spacing:-.4px;
                      margin-bottom:12px">No results yet</div>
          <div style="font-size:12px;color:#aaa;line-height:2;max-width:320px">
            Paste URLs on the left, pick a mode, hit <strong style="color:#333">Start Scan</strong>
            <br>
            <span style="color:{mi_['color']};font-weight:600">{chosen} mode:</span>
            {mi_['tag']}
            <br>
            <span style="color:#bbb">Enable Parallel in Settings for 4x speed</span>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        tot_d  = len(results)
        tot_e  = sum(len(r.get("All Emails",[])) for r in results.values())
        t1_cnt = sum(1 for r in results.values() if r.get("Best Tier","").startswith("Tier 1"))
        val_ok = sum(1 for r in results.values()
                     if (r.get("Validation",{}) or {}).get("status")=="Deliverable")
        fallbk = sum(1 for r in results.values() if r.get("WasFallback"))
        no_e   = sum(1 for r in results.values() if not r.get("Best Email"))

        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("Sites",    tot_d)
        m2.metric("Emails",   tot_e)
        m3.metric("Tier 1",   t1_cnt)
        m4.metric("Validated",val_ok)
        m5.metric("Fallback", fallbk)
        m6.metric("No Email", no_e)

        if scan_state == "done":
            to_val = [d for d,r in results.items()
                      if r.get("All Emails") and not r.get("Validation")]
            if to_val:
                v1,v2 = st.columns([4,1.3])
                with v1:
                    st.markdown(
                        f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;'
                        f'border-radius:8px;padding:8px 13px;font-size:12px;color:#15803d;'
                        f'font-weight:600;margin:2px 0">'
                        f'{len(to_val)} domain(s) ready to validate - uses fallback if best email fails</div>',
                        unsafe_allow_html=True)
                with v2:
                    if st.button("Validate All", key="val_all", type="primary", use_container_width=True):
                        st.session_state["run_validate_all"]=True; st.rerun()

        search = st.text_input("s", placeholder="Search domains or emails...",
                               label_visibility="collapsed", key="srch")

        FLT = [("All","All"),("T1","T1"),("T2","T2"),("T3","T3"),
               ("None","None"),("OK","val_ok"),("Risk","val_risky"),("Fail","val_bad")]
        st.markdown('<div class="flt-bar">', unsafe_allow_html=True)
        fc = st.columns(len(FLT))
        for col,(lbl,val) in zip(fc, FLT):
            with col:
                active = st.session_state.tbl_filter==val
                if st.button(lbl, key=f"flt_{val}",
                             type="primary" if active else "secondary",
                             use_container_width=True):
                    st.session_state.tbl_filter=val; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        seen = st.session_state.seen_emails
        rows = []
        for domain, r in results.items():
            all_e = r.get("All Emails",[]); best = r.get("Best Email","")
            bt    = r.get("Best Tier","")
            vbest = r.get("ValidatedBestEmail","") or best
            val   = r.get("Validation",{}) or {}
            val_st= val.get("status","")
            conf  = r.get("Confidence")
            fb_   = r.get("WasFallback",False)
            is_dup= best in seen and best and scan_state!="running"

            email_display = (vbest or "---")
            if fb_: email_display += " [fb]"
            if is_dup: email_display += " [dup]"

            rows.append({
                "Domain":   domain,
                "Email":    email_display,
                "Tier":     bt or "---",
                "Score":    conf if conf is not None else "",
                "Val":      val_icon(val_st) if val_st else "---",
                "Reason":   val.get("reason","---") if val else "---",
                "SPF":      ("ok" if val.get("spf") else "no") if val else "---",
                "DMARC":    ("ok" if val.get("dmarc") else "no") if val else "---",
                "CA":       ("yes" if val.get("catch_all") else "no") if val else "---",
                "+":        f'+{len(all_e)-1}' if len(all_e)>1 else "",
                "Twitter":  (r.get("Twitter",[])+[""])[0],
                "LinkedIn": (r.get("LinkedIn",[])+[""])[0],
                "Pages":    r.get("Pages Scraped",0),
                "s":        r.get("Total Time",""),
            })

        df = pd.DataFrame(rows)
        if search:
            m = (df["Domain"].str.contains(search,case=False,na=False)|
                 df["Email"].str.contains(search,case=False,na=False))
            df = df[m]

        flt = st.session_state.tbl_filter
        if   flt=="T1":        df = df[df["Tier"].str.startswith("Tier 1",na=False)]
        elif flt=="T2":        df = df[df["Tier"].str.startswith("Tier 2",na=False)]
        elif flt=="T3":        df = df[df["Tier"].str.startswith("Tier 3",na=False)]
        elif flt=="None":      df = df[df["Email"]=="---"]
        elif flt=="val_ok":    df = df[df["Val"]=="OK"]
        elif flt=="val_risky": df = df[df["Val"]=="RISK"]
        elif flt=="val_bad":   df = df[df["Val"]=="FAIL"]

        st.caption(f'Showing {len(df)} of {tot_d} &nbsp;|&nbsp; [fb]=fallback used &nbsp; [dup]=seen before')

        st.dataframe(df, use_container_width=True, hide_index=True,
                     height=min(560, 44+max(len(df),1)*36),
                     column_config={
                         "Domain":  st.column_config.TextColumn("Domain",  width=148),
                         "Email":   st.column_config.TextColumn("Email",   width=200),
                         "Tier":    st.column_config.TextColumn("Tier",    width=65),
                         "Score":   st.column_config.NumberColumn("Score", width=50),
                         "Val":     st.column_config.TextColumn("Val",     width=45),
                         "Reason":  st.column_config.TextColumn("Reason",  width=160),
                         "SPF":     st.column_config.TextColumn("SPF",     width=38),
                         "DMARC":   st.column_config.TextColumn("DMARC",   width=48),
                         "CA":      st.column_config.TextColumn("CA",      width=40),
                         "+":       st.column_config.TextColumn("+",       width=35),
                         "Twitter": st.column_config.TextColumn("Twitter", width=100),
                         "LinkedIn":st.column_config.TextColumn("LinkedIn",width=120),
                         "Pages":   st.column_config.NumberColumn("Pages", width=48),
                         "s":       st.column_config.NumberColumn("s",     width=42),
                     })

        st.divider()
        st.markdown('<span class="sec">Per-domain actions</span>', unsafe_allow_html=True)
        st.markdown('<div class="act-card">', unsafe_allow_html=True)

        pa1,pa2,pa3,pa4,pa5 = st.columns([2.8,1,1,1,0.8])
        with pa1:
            sel = st.selectbox("d", list(results.keys()),
                               label_visibility="collapsed", key="sel_d")
        r_sel   = results.get(sel,{})
        fb_pgs  = r_sel.get("Facebook",[])
        all_e_s = r_sel.get("All Emails",[])
        best_s  = r_sel.get("Best Email","")

        with pa2:
            if st.button("Validate", key="v1", type="primary",
                         disabled=not all_e_s, use_container_width=True):
                st.session_state[f"vrun_{sel}"]=True; st.rerun()
        with pa3:
            if st.button("FB", key="fb1", type="secondary",
                         disabled=not fb_pgs, use_container_width=True):
                st.session_state[f"fbrun_{sel}"]=True; st.rerun()
        with pa4:
            if st.button("MX", key="mx1", type="secondary",
                         disabled=not (DNS_AVAILABLE and all_e_s), use_container_width=True):
                st.session_state[f"mxrun_{sel}"]=True; st.rerun()
        with pa5:
            if all_e_s:
                st.download_button("Get", "\n".join(all_e_s),
                                   f"{sel}_emails.txt", key="cp1", use_container_width=True)

        val_d = r_sel.get("Validation",{}) or {}
        if val_d:
            vbest  = r_sel.get("ValidatedBestEmail","") or best_s
            icon   = val_icon(val_d.get("status",""))
            conf   = r_sel.get("Confidence")
            conf_c = conf_color(conf)
            fb_fl  = " [fallback]" if r_sel.get("WasFallback") else ""
            spf    = "SPF ok" if val_d.get("spf") else "no SPF"
            dmarc  = " | DMARC ok" if val_d.get("dmarc") else ""
            ca     = " | catch-all" if val_d.get("catch_all") else ""
            score_h= f' | <strong style="color:{conf_c}">{conf}/100</strong>' if conf is not None else ""
            st.markdown(
                f'<div class="val-result">'
                f'<strong>[{icon}] {vbest}</strong>{fb_fl}{score_h}'
                f' &nbsp;|&nbsp; {val_d.get("reason","")}'
                f' &nbsp;|&nbsp; {spf}{dmarc}{ca}'
                f'</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        if sel and st.session_state.get(f"vrun_{sel}"):
            st.session_state[f"vrun_{sel}"]=False
            with st.spinner(f"Validating {sel} - checking fallbacks if needed..."):
                chosen_e, vres, was_fb = validate_with_fallback(all_e_s, best_s)
            if vres:
                conf_ = confidence_score(chosen_e, vres)
                st.session_state.results[sel].update({
                    "Validation":vres,"ValidatedBestEmail":chosen_e,
                    "WasFallback":was_fb,"Confidence":conf_})
            st.rerun()

        if st.session_state.get("run_validate_all"):
            st.session_state["run_validate_all"]=False
            todo = [(d,r) for d,r in results.items()
                    if r.get("All Emails") and not r.get("Validation")]
            if todo:
                vph=st.empty()
                for i,(dom,r) in enumerate(todo):
                    vph.markdown(
                        f'<div class="log-box">'
                        f'<div class="ll-site">[ {dom} ]</div>'
                        f'<div class="ll-info">  . checking {r.get("Best Email","")} ({i+1}/{len(todo)})</div>'
                        f'</div>', unsafe_allow_html=True)
                    chosen_e, vres, was_fb = validate_with_fallback(
                        r.get("All Emails",[]), r.get("Best Email",""))
                    if vres:
                        conf_ = confidence_score(chosen_e, vres)
                        st.session_state.results[dom].update({
                            "Validation":vres,"ValidatedBestEmail":chosen_e,
                            "WasFallback":was_fb,"Confidence":conf_})
                vph.empty(); st.rerun()

        if sel and st.session_state.get(f"fbrun_{sel}"):
            st.session_state[f"fbrun_{sel}"]=False
            with st.spinner("Scraping Facebook..."):
                slug = fb_pgs[0].replace("facebook.com/","").strip("/") if fb_pgs else ""
                if slug:
                    fb_html, _ = fetch_page(f"https://www.facebook.com/{slug}", timeout=14)
                    if fb_html:
                        found = extract_emails(fb_html)
                        if found:
                            upd=sort_by_tier(set(all_e_s)|found)
                            st.session_state.results[sel]["All Emails"]=upd
                            st.session_state.results[sel]["Best Email"]=pick_best(set(upd)) or ""
            st.rerun()

        if sel and st.session_state.get(f"mxrun_{sel}") and DNS_AVAILABLE:
            st.session_state[f"mxrun_{sel}"]=False
            mx_ph=st.empty(); mx_l=[]; new_mx={}
            for email in all_e_s:
                res=check_mx(email); new_mx[email]=res; mx_l.append((email,res))
                rh="".join(f'<div class="{"ll-email" if g else "ll-warn"}">{"ok" if g else "!!"} {e}</div>'
                           for e,g in mx_l)
                ok=sum(1 for _,g in mx_l if g)
                mx_ph.markdown(f'<div class="log-box"><div class="ll-info">MX: {ok}/{len(mx_l)} valid</div>{rh}</div>',
                               unsafe_allow_html=True)
            st.session_state.results[sel]["MX"]=new_mx
            valid=[e for e in all_e_s if new_mx.get(e) is not False]
            if len(valid)<len(all_e_s): st.session_state.results[sel]["All Emails"]=valid
            time.sleep(0.2); st.rerun()

if st.session_state.scan_state == "running":
    queue = st.session_state.scan_queue
    idx   = st.session_state.scan_idx
    total = len(queue)

    if idx >= total:
        st.session_state.scan_state = "done"; st.rerun()
    else:
        use_parallel = st.session_state.get("parallel", True)
        BATCH = 4 if use_parallel else 1

        # snapshot everything needed — worker threads must NOT touch session_state
        cfg_snap   = dict(cfg)
        skip_t1_   = bool(st.session_state.skip_t1)
        respect_   = bool(st.session_state.respect_robots)
        scrape_fb_ = bool(st.session_state.scrape_fb)

        batch_urls = queue[idx:idx+BATCH]

        def run_one_site(url):
            if not url.startswith("http"): url = "https://"+url
            row, logs = _scrape_site(url, cfg_snap, skip_t1_, respect_, scrape_fb_)
            site_marker = (("site", row["Domain"], None, None), "site")
            return row, [site_marker] + logs

        batch_results = []
        if use_parallel and len(batch_urls) > 1:
            with ThreadPoolExecutor(max_workers=BATCH) as ex:
                futs = [ex.submit(run_one_site, u) for u in batch_urls]
                for fut in as_completed(futs):
                    try:
                        batch_results.append(fut.result())
                    except Exception as e:
                        st.session_state.log_lines.append(
                            (("warn", f"thread error: {str(e)[:60]}", None, None), "warn"))
        else:
            try:
                batch_results.append(run_one_site(batch_urls[0]))
            except Exception as e:
                st.session_state.log_lines.append(
                    (("warn", f"scrape error: {str(e)[:60]}", None, None), "warn"))

        for row, logs in batch_results:
            domain = row["Domain"]
            st.session_state.results[domain] = row
            st.session_state.scraped_domains.add(domain)
            st.session_state.log_lines.extend(logs)

        st.session_state.scan_idx = idx + len(batch_urls)
        time.sleep(cfg_snap.get("delay", 0.1))

        if st.session_state.scan_idx >= total:
            st.session_state.scan_state = "done"
            if st.session_state.get("auto_validate"):
                st.session_state["run_validate_all"] = True

        st.rerun()

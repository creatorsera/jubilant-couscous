import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import io
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from collections import deque
import random
import pandas as pd

st.set_page_config(
    page_title="MailHunter",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap');

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: #ffffff !important;
    color: #111827 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem !important; max-width: 860px !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #f0f0f0 !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 28px 20px !important; }
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }

/* sidebar toggle arrow button — style it as a hamburger feel */
[data-testid="collapsedControl"] {
    top: 18px !important;
    background: #f4f4f5 !important;
    border-radius: 10px !important;
    border: none !important;
    width: 36px !important;
    height: 36px !important;
}

/* ── SIDEBAR HEADINGS ── */
.sb-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid #f0f0f0;
}
.sb-section {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #a1a1aa;
    margin: 20px 0 10px;
}
.sb-stat {
    background: #f4f4f5;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 20px;
    text-align: center;
}
.sb-stat-num {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 26px;
    font-weight: 800;
    color: #6366f1;
}
.sb-stat-label { font-size: 11px; color: #71717a; margin-top: 2px; }

/* ── MODE CARDS IN SIDEBAR ── */
.mode-option {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 6px;
    cursor: default;
    transition: background 0.15s;
}
.mode-option.active { background: #f5f3ff; }
.mode-option .m-icon { font-size: 16px; }
.mode-option .m-name { font-size: 13px; font-weight: 600; color: #111827; }
.mode-option .m-desc { font-size: 11px; color: #a1a1aa; }

/* ── MAIN HEADINGS ── */
.page-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 36px;
    font-weight: 800;
    color: #111827;
    letter-spacing: -0.8px;
    line-height: 1.15;
    margin-bottom: 8px;
}
.page-title span { color: #6366f1; }
.page-sub {
    font-size: 14px;
    color: #71717a;
    margin-bottom: 32px;
    line-height: 1.6;
}

/* ── ACTIVE MODE CHIP ── */
.active-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 99px;
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 28px;
}
.chip-easy    { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.chip-medium  { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.chip-extreme { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }

/* ── CARD ── */
.card {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 16px;
}

/* ── INPUTS ── */
.stTextArea textarea {
    background: #ffffff !important;
    border: 1.5px solid #e4e4e7 !important;
    border-radius: 12px !important;
    color: #111827 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    padding: 12px 14px !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
    outline: none !important;
}
.stTextArea textarea::placeholder { color: #d4d4d8 !important; }

/* ── SELECTBOX ── */
[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1.5px solid #e4e4e7 !important;
    border-radius: 12px !important;
    color: #111827 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
[data-baseweb="popover"] > div {
    background: #ffffff !important;
    border: 1px solid #e4e4e7 !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08) !important;
    overflow: hidden !important;
}
[role="option"] {
    background: #ffffff !important;
    color: #111827 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    padding: 9px 14px !important;
}
[role="option"]:hover { background: #f5f3ff !important; color: #6366f1 !important; }

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] > section {
    background: #ffffff !important;
    border: 1.5px dashed #d4d4d8 !important;
    border-radius: 14px !important;
    padding: 20px !important;
    transition: border-color 0.15s !important;
}
[data-testid="stFileUploader"] > section:hover { border-color: #6366f1 !important; }
[data-testid="stFileUploader"] * { color: #71717a !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f4f4f5 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: none !important;
    margin-bottom: 16px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #71717a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 9px !important;
    padding: 7px 16px !important;
    border: none !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #111827 !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}
[data-testid="stTabsContent"] { padding: 0 !important; border: none !important; background: transparent !important; }

/* ── BUTTONS ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    border: none !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #6366f1 !important;
    color: #ffffff !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #4f46e5 !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #e4e4e7 !important;
    color: #a1a1aa !important;
    box-shadow: none !important;
    transform: none !important;
}
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: #71717a !important;
    border: 1.5px solid #e4e4e7 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #fca5a5 !important;
    color: #ef4444 !important;
}

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    background: #ffffff !important;
    border: 1.5px solid #6366f1 !important;
    color: #6366f1 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: #f5f3ff !important;
    box-shadow: 0 2px 12px rgba(99,102,241,0.2) !important;
    transform: translateY(-1px) !important;
}

/* ── PROGRESS ── */
.stProgress > div > div { background: #f4f4f5 !important; border-radius: 99px !important; height: 5px !important; }
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #6366f1, #818cf8) !important;
    border-radius: 99px !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 16px;
    padding: 18px !important;
    transition: box-shadow 0.15s, transform 0.15s;
}
[data-testid="stMetric"]:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-1px); }
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #a1a1aa !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 26px !important;
    font-weight: 800 !important;
    color: #111827 !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border: 1px solid #f0f0f0 !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    background: #fafafa !important;
    border: 1px solid #f0f0f0 !important;
    border-radius: 12px !important;
    font-size: 13px !important;
    color: #374151 !important;
}

/* ── SLIDERS ── */
[data-baseweb="slider"] [role="slider"] {
    background: #6366f1 !important;
    box-shadow: 0 0 0 4px rgba(99,102,241,0.18) !important;
}
[data-baseweb="slider"] [data-testid="stTickBar"] > div { color: #a1a1aa !important; font-size: 11px !important; }

/* ── RADIO IN SIDEBAR ── */
[data-testid="stSidebar"] .stRadio label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
}
[data-testid="stSidebar"] .stRadio > div { gap: 6px !important; }

/* ── CHECKBOXES IN SIDEBAR ── */
[data-testid="stSidebar"] .stCheckbox label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
}

/* ── WIDGET LABELS ── */
label[data-testid="stWidgetLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #374151 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    margin-bottom: 6px !important;
}
[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {
    font-size: 10px !important;
    font-weight: 600 !important;
    color: #a1a1aa !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ── DIVIDER ── */
hr { border-color: #f0f0f0 !important; margin: 20px 0 !important; }

/* ── URL PILLS ── */
.url-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.url-pill {
    display: inline-block;
    background: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 99px;
    padding: 4px 12px;
    font-size: 12px;
    color: #52525b;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
}

/* ── COL PREVIEW ── */
.col-preview {
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    padding: 12px 14px;
    margin-top: 10px;
    font-size: 12px;
    color: #71717a;
    line-height: 1.8;
    max-height: 90px;
    overflow-y: auto;
    font-family: 'Inter', sans-serif;
}
.col-preview-label {
    font-size: 10px;
    font-weight: 600;
    color: #a1a1aa;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* ── INFO CHIP ── */
.info-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f5f3ff;
    border-radius: 99px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 500;
    color: #6366f1;
    margin-top: 10px;
    font-family: 'Inter', sans-serif;
}

/* ── TIER LEGEND ── */
.tier-legend { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.tier-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 12px; border-radius: 99px;
    font-size: 12px; font-weight: 500;
    border: 1px solid; font-family: 'Inter', sans-serif;
}
.t1 { background:#f0fdf4; border-color:#bbf7d0; color:#16a34a; }
.t2 { background:#fffbeb; border-color:#fde68a; color:#d97706; }
.t3 { background:#f4f4f5; border-color:#e4e4e7; color:#71717a; }

/* ── LOG BOX ── */
.log-wrap {
    background: #18181b;
    border-radius: 14px;
    padding: 18px 20px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 12px;
    max-height: 200px;
    overflow-y: auto;
    line-height: 1.9;
    margin-bottom: 16px;
}
.log-wrap::before {
    content: '● ● ●';
    display: block;
    font-size: 9px;
    color: #3f3f46;
    letter-spacing: 3px;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid #27272a;
}
.ll-active { color: #a5b4fc; font-weight: 500; }
.ll-active::before { content: '▸ '; }
.ll-done { color: #3f3f46; }
.ll-done::before { content: '✓ '; color: #4ade8050; }

/* ── SECTION LABEL ── */
.sec-label {
    font-size: 11px;
    font-weight: 600;
    color: #a1a1aa;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 28px 0 14px;
    display: flex; align-items: center; gap: 10px;
    font-family: 'Inter', sans-serif;
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: #f0f0f0; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e4e4e7; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #a1a1aa; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
TIER1 = re.compile(r"^(editor|admin|press|advert|contact)[a-z0-9._%+\-]*@", re.IGNORECASE)
TIER2 = re.compile(r"^(info|sales|hello|office|team|support|help)[a-z0-9._%+\-]*@", re.IGNORECASE)

BLOCKED_TLDS = {
    'png','jpg','jpeg','webp','gif','svg','ico','bmp','tiff','avif',
    'mp4','mp3','wav','ogg','mov','avi','webm','pdf','zip','rar',
    'tar','gz','7z','js','css','php','asp','aspx','xml','json',
    'ts','jsx','tsx','woff','woff2','ttf','eot','otf','map','exe','dmg','pkg','deb','apk',
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
MODE_CONFIG = {
    "Easy":    {"max_pages": 1,   "max_depth": 0, "sitemap": False, "delay": 0.2},
    "Medium":  {"max_pages": 50,  "max_depth": 3, "sitemap": False, "delay": 0.5},
    "Extreme": {"max_pages": 300, "max_depth": 6, "sitemap": True,  "delay": 0.3},
}

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
for k, v in {
    "all_emails": {}, "best_emails": {}, "scraped": False,
    "log_lines": [], "f_tier1": True, "f_tier2": True, "f_tier3": True,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
#  CORE FUNCTIONS
# ─────────────────────────────────────────
def is_valid_email(email: str) -> bool:
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
    if re.search(r'@\d+x[\-\d]', '@' + do): return False
    if re.match(r'^\d+x', do): return False
    if do in PLACEHOLDER_DOMAINS: return False
    if lo in PLACEHOLDER_LOCALS: return False
    if any(lo == p or lo.startswith(p) for p in SUPPRESS_PREFIXES): return False
    if re.search(r'\d+x\d+', lo): return False
    return True

def get_tier(email: str):
    if TIER1.match(email): return "1", "🥇 Tier 1 — editor / admin / press / contact"
    if TIER2.match(email): return "2", "🥈 Tier 2 — info / sales / support / office"
    return "3", "🥉 Tier 3 — other valid email"

def pick_best_email(emails: set):
    pool = [e for e in emails if is_valid_email(e)]
    if not pool: return None, None
    t1 = [e for e in pool if TIER1.match(e)]
    if t1: return t1[0], "🥇 Tier 1 — editor / admin / press / contact"
    t2 = [e for e in pool if TIER2.match(e)]
    if t2: return t2[0], "🥈 Tier 2 — info / sales / support / office"
    return pool[0], "🥉 Tier 3 — other valid email"

def make_headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.5"}

def fetch_page(url, timeout=10):
    try:
        r = requests.get(url, headers=make_headers(), timeout=timeout, allow_redirects=True)
        if r.ok and "text" in r.headers.get("Content-Type", ""):
            return r.text
    except: pass
    return None

def extract_emails(html):
    soup = BeautifulSoup(html, "html.parser")
    raw = set()
    raw.update(EMAIL_REGEX.findall(soup.get_text(" ")))
    raw.update(EMAIL_REGEX.findall(html))
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            raw.add(a["href"][7:].split("?")[0].strip())
    return {e for e in raw if is_valid_email(e)}

def get_internal_links(html, base_url, root_domain):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        p = urlparse(full)
        if p.netloc == root_domain and p.scheme in ("http", "https"):
            links.append(full.split("#")[0].split("?")[0])
    return list(set(links))

def fetch_sitemap_urls(root_url):
    urls = []
    for c in [urljoin(root_url, "/sitemap.xml"), urljoin(root_url, "/sitemap_index.xml")]:
        html = fetch_page(c)
        if not html: continue
        try:
            root_el = ET.fromstring(html)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root_el.findall(".//sm:loc", ns):
                u = loc.text.strip()
                if u.endswith(".xml"):
                    sub = fetch_page(u)
                    if sub:
                        try:
                            sr = ET.fromstring(sub)
                            for sl in sr.findall(".//sm:loc", ns): urls.append(sl.text.strip())
                        except: pass
                else:
                    urls.append(u)
        except: pass
        if urls: break
    return urls

def scrape_site(root_url, cfg, store, log_cb, page_cb, best_mode=False):
    parsed = urlparse(root_url)
    root_domain = parsed.netloc
    visited, queue, all_found = set(), deque(), set()
    seed_urls = []

    if cfg["sitemap"]:
        log_cb(f"sitemap → {root_domain}", "active")
        seed_urls = fetch_sitemap_urls(root_url)
        log_cb(f"sitemap → {len(seed_urls)} urls indexed", "done")

    if not seed_urls: seed_urls = [root_url]
    for u in seed_urls[:cfg["max_pages"]]: queue.append((u, 0))

    pages_done = 0
    while queue and pages_done < cfg["max_pages"]:
        url, depth = queue.popleft()
        if url in visited: continue
        visited.add(url)
        short = url.replace("https://","").replace("http://","")[:62]
        log_cb(f"[{pages_done+1}] {short}", "active")
        html = fetch_page(url)
        if html:
            found = extract_emails(html)
            all_found.update(found)
            if not best_mode:
                for email in found:
                    if email not in store:
                        tk, tl = get_tier(email)
                        store[email] = {"Tier": tl, "Email": email, "Domain": root_domain, "Found On": url}
            if depth < cfg["max_depth"]:
                for link in get_internal_links(html, url, root_domain):
                    if link not in visited: queue.append((link, depth + 1))
            if best_mode and any(TIER1.match(e) for e in all_found):
                log_cb("tier-1 hit — stopping early", "done")
                break
        log_cb(f"✓ [{pages_done+1}] {short}", "done")
        pages_done += 1
        page_cb(pages_done, min(cfg["max_pages"], pages_done + len(queue)))
        time.sleep(cfg["delay"])

    if best_mode:
        best_email, tier = pick_best_email(all_found)
        store[root_domain] = {
            "Domain": root_domain,
            "Best Email": best_email or "No email found",
            "Priority": tier or "—",
            "Total Found": len(all_found),
            "Source URL": root_url,
        }
        log_cb(f"best → {best_email or 'none found'}", "done")

# ─────────────────────────────────────────
#  SIDEBAR — SETTINGS PANEL
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-title">⚙️ Settings</div>', unsafe_allow_html=True)

    # Scraping mode
    st.markdown('<div class="sb-section">Scraping Mode</div>', unsafe_allow_html=True)
    mode = st.radio(
        "",
        ["🟢  Easy — single page", "🟡  Medium — crawl links", "🔴  Extreme — full domain"],
        label_visibility="collapsed",
    )
    mode_key = "Easy" if "Easy" in mode else "Medium" if "Medium" in mode else "Extreme"
    cfg = MODE_CONFIG[mode_key].copy()

    if mode_key == "Medium":
        st.markdown('<div class="sb-section">Parameters</div>', unsafe_allow_html=True)
        cfg["max_depth"] = st.slider("Crawl depth", 1, 5, 3)
        cfg["max_pages"] = st.slider("Max pages / site", 10, 200, 50)
    elif mode_key == "Extreme":
        st.markdown('<div class="sb-section">Parameters</div>', unsafe_allow_html=True)
        cfg["max_pages"] = st.slider("Max pages / site", 50, 500, 300)

    st.markdown("---")

    # Extraction mode
    st.markdown('<div class="sb-section">Extraction</div>', unsafe_allow_html=True)
    single_mode = st.toggle("Best email per site only",
                            help="Uses priority logic: Tier 1 → Tier 2 → Tier 3")

    st.markdown("---")

    # Tier filters
    st.markdown('<div class="sb-section">Tier Filters</div>', unsafe_allow_html=True)
    st.session_state.f_tier1 = st.checkbox("🥇 Tier 1 — editor / admin / press", value=st.session_state.f_tier1)
    st.session_state.f_tier2 = st.checkbox("🥈 Tier 2 — info / sales / support", value=st.session_state.f_tier2)
    st.session_state.f_tier3 = st.checkbox("🥉 Tier 3 — other valid emails",     value=st.session_state.f_tier3)

    # Stat
    total_indexed = len(st.session_state.all_emails) + len(st.session_state.best_emails)
    if total_indexed:
        st.markdown(f"""
        <div class="sb-stat">
          <div class="sb-stat-num">{total_indexed}</div>
          <div class="sb-stat-label">emails indexed</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  MAIN PAGE
# ─────────────────────────────────────────
chip_class = {"Easy": "chip-easy", "Medium": "chip-medium", "Extreme": "chip-extreme"}[mode_key]
chip_icon  = {"Easy": "🟢", "Medium": "🟡", "Extreme": "🔴"}[mode_key]
extract_label = "🎯 Best email per site" if single_mode else "📋 All emails"

st.markdown(f"""
<div class="page-title">Find the right<br><span>contact</span>, fast.</div>
<p class="page-sub">Paste URLs or upload a file — MailHunter scrapes, filters and exports with smart tier priority.</p>
<div style="display:flex;gap:8px;margin-bottom:32px;flex-wrap:wrap">
  <span class="active-chip {chip_class}">{chip_icon} {mode_key} mode</span>
  <span class="active-chip" style="background:#f4f4f5;color:#52525b;border:1px solid #e4e4e7">{extract_label}</span>
</div>
""", unsafe_allow_html=True)

# ── INPUT ──
tab_paste, tab_upload = st.tabs(["✏️  Paste URLs", "📁  Upload File"])
urls_to_scrape = []

with tab_paste:
    raw = st.text_area(
        "",
        placeholder="https://magazine.com\nhttps://newspaper.org\nhttps://agency.co",
        height=130,
        label_visibility="collapsed",
    )
    if raw.strip():
        urls_to_scrape = [u.strip() for u in raw.splitlines() if u.strip().startswith("http")]

with tab_upload:
    uploaded = st.file_uploader("", type=["csv","txt"], label_visibility="collapsed")
    if uploaded:
        raw_bytes = uploaded.read()
        if uploaded.name.endswith(".csv"):
            try:
                df_up  = pd.read_csv(io.BytesIO(raw_bytes))
                cols   = list(df_up.columns)
                hints  = ["url","link","website","site","domain","href","address","web"]
                defcol = next((c for c in cols if any(h in c.lower() for h in hints)), cols[0])
                sel    = st.selectbox("Which column contains the URLs?", cols, index=cols.index(defcol))
                prev   = df_up[sel].dropna().head(5).tolist()
                prev_html = "".join(f"<div>{str(v)[:70]}</div>" for v in prev)
                st.markdown(f'<div class="col-preview"><div class="col-preview-label">Preview — first 5 rows</div>{prev_html}</div>',
                            unsafe_allow_html=True)
                for u in df_up[sel].dropna().astype(str):
                    u = u.strip()
                    if not u.startswith("http"): u = "https://" + u
                    urls_to_scrape.append(u)
                st.markdown(f'<span class="info-chip">✓ {len(urls_to_scrape)} URLs · {len(cols)} columns</span>',
                            unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")
        else:
            content = raw_bytes.decode("utf-8")
            urls_to_scrape = [u.strip() for u in content.splitlines() if u.strip().startswith("http")]
            st.markdown(f'<span class="info-chip">✓ {len(urls_to_scrape)} URLs loaded</span>',
                        unsafe_allow_html=True)

# URL pills preview
if urls_to_scrape:
    pills = "".join(
        f'<span class="url-pill">{u.replace("https://","").replace("http://","")[:38]}</span>'
        for u in urls_to_scrape[:10]
    )
    if len(urls_to_scrape) > 10:
        pills += f'<span class="url-pill" style="color:#a1a1aa">+{len(urls_to_scrape)-10} more</span>'
    st.markdown(f'<div class="url-pills">{pills}</div><br>', unsafe_allow_html=True)

# ── BUTTONS ──
c1, c2, c3 = st.columns([2, 1, 4])
with c1:
    start = st.button("Scan →", type="primary", disabled=not urls_to_scrape, use_container_width=True)
with c2:
    if st.button("Clear", type="secondary", use_container_width=True):
        st.session_state.all_emails  = {}
        st.session_state.best_emails = {}
        st.session_state.scraped     = False
        st.session_state.log_lines   = []
        st.rerun()

# ─────────────────────────────────────────
#  SCRAPING
# ─────────────────────────────────────────
if start and urls_to_scrape:
    st.session_state.all_emails  = {}
    st.session_state.best_emails = {}
    st.session_state.scraped     = False
    st.session_state.log_lines   = []

    store = st.session_state.best_emails if single_mode else st.session_state.all_emails

    st.markdown('<div class="sec-label">Live log</div>', unsafe_allow_html=True)
    log_ph   = st.empty()
    prog_ph  = st.progress(0)
    table_ph = st.empty()

    def render_log():
        lines = "".join(
            f'<div class="{"ll-active" if k=="active" else "ll-done"}">{t}</div>'
            for t, k in st.session_state.log_lines[-24:]
        )
        log_ph.markdown(f'<div class="log-wrap">{lines}</div>', unsafe_allow_html=True)

    def log_cb(msg, kind="active"):
        st.session_state.log_lines.append((msg, kind))
        render_log()

    total_sites = len(urls_to_scrape)
    for si, url in enumerate(urls_to_scrape):
        if not url.startswith("http"): url = "https://" + url
        log_cb(f"── target {si+1}/{total_sites}: {url}", "active")

        def page_cb(done, total, i=si):
            pct = (i / total_sites) + (min(done, total) / max(total, 1)) / total_sites
            prog_ph.progress(min(pct, 1.0))
            rows = list(store.values())
            if rows:
                table_ph.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=200)

        scrape_site(url, cfg, store, log_cb, page_cb, best_mode=single_mode)
        log_cb(f"── done: {url}", "done")

    prog_ph.progress(1.0)
    log_cb(f"── complete · {len(store)} results ──", "done")
    st.session_state.scraped = True

# ─────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────
has_results = (single_mode and st.session_state.best_emails) or \
              (not single_mode and st.session_state.all_emails)

if has_results:
    st.markdown('<div class="sec-label">Results</div>', unsafe_allow_html=True)

    if single_mode:
        df = pd.DataFrame(list(st.session_state.best_emails.values()))
        t1 = len(df[df["Priority"].str.startswith("🥇", na=False)])
        t2 = len(df[df["Priority"].str.startswith("🥈", na=False)])
        t3 = len(df[df["Priority"].str.startswith("🥉", na=False)])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sites scraped", len(df))
        c2.metric("🥇 Tier 1", t1)
        c3.metric("🥈 Tier 2", t2)
        c4.metric("🥉 Tier 3", t3)

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True, height=360,
            column_config={
                "Domain":      st.column_config.TextColumn("Domain",      width="medium"),
                "Best Email":  st.column_config.TextColumn("Best Email",  width="large"),
                "Priority":    st.column_config.TextColumn("Tier",        width="medium"),
                "Total Found": st.column_config.NumberColumn("Found",     width="small"),
                "Source URL":  st.column_config.LinkColumn("Source",      width="medium"),
            })

        buf = io.StringIO(); df.to_csv(buf, index=False)
        dc, _, _ = st.columns([1, 1, 2])
        with dc:
            st.download_button("⬇ Export CSV", buf.getvalue(),
                               f"mailhunter_best_{int(time.time())}.csv", "text/csv",
                               use_container_width=True)
    else:
        df_all = pd.DataFrame(list(st.session_state.all_emails.values()))

        def tk(lbl):
            if str(lbl).startswith("🥇"): return "1"
            if str(lbl).startswith("🥈"): return "2"
            return "3"
        df_all["_tk"] = df_all["Tier"].apply(tk)

        tier_filter = []
        if st.session_state.f_tier1: tier_filter.append("1")
        if st.session_state.f_tier2: tier_filter.append("2")
        if st.session_state.f_tier3: tier_filter.append("3")

        df_filt   = df_all[df_all["_tk"].isin(tier_filter)] if tier_filter else df_all
        df_show   = df_filt.drop(columns=["_tk"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total emails", len(df_all))
        c2.metric("🥇 Tier 1", len(df_all[df_all["_tk"]=="1"]))
        c3.metric("🥈 Tier 2", len(df_all[df_all["_tk"]=="2"]))
        c4.metric("🥉 Tier 3", len(df_all[df_all["_tk"]=="3"]))

        st.markdown("""
        <div class="tier-legend">
          <span class="tier-badge t1">🥇 Tier 1 — editor / admin / press / contact</span>
          <span class="tier-badge t2">🥈 Tier 2 — info / sales / support / office</span>
          <span class="tier-badge t3">🥉 Tier 3 — other valid emails</span>
        </div>""", unsafe_allow_html=True)

        st.markdown(
            f'<p style="font-size:12px;color:#a1a1aa;margin:4px 0 12px">Showing {len(df_filt)} of {len(df_all)} emails</p>',
            unsafe_allow_html=True)

        st.dataframe(df_show.sort_values("Tier"), use_container_width=True,
                     hide_index=True, height=420,
                     column_config={
                         "Tier":     st.column_config.TextColumn("Tier",       width="medium"),
                         "Email":    st.column_config.TextColumn("Email",      width="large"),
                         "Domain":   st.column_config.TextColumn("Domain",     width="medium"),
                         "Found On": st.column_config.LinkColumn("Source URL", width="large"),
                     })

        buf = io.StringIO(); df_show.sort_values("Tier").to_csv(buf, index=False)
        dc, _, _ = st.columns([1, 1, 2])
        with dc:
            st.download_button("⬇ Export CSV", buf.getvalue(),
                               f"mailhunter_all_{int(time.time())}.csv", "text/csv",
                               use_container_width=True)

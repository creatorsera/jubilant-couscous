import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import io
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from collections import deque
from datetime import datetime
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&family=Bricolage+Grotesque:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background: #f7f7f5 !important;
    color: #1a1a1a !important;
}
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
.block-container { padding: 2.5rem 3rem 6rem !important; max-width: 1020px !important; }

/* ── BRAND ── */
.brand {
    display: flex; align-items: baseline; gap: 0;
    margin-bottom: 6px;
}
.brand-name {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 28px; font-weight: 800; color: #1a1a1a; letter-spacing: -0.5px;
}
.brand-name span { color: #5b5bd6; }
.brand-sub { font-size: 13px; color: #999; margin-bottom: 20px; }

/* ── SETTINGS PANEL ── */
.settings-panel {
    background: #ffffff;
    border: 1.5px solid #ebebeb;
    border-radius: 18px;
    padding: 20px 24px;
    margin-bottom: 20px;
}
.settings-row {
    display: flex; align-items: flex-start;
    gap: 32px; flex-wrap: wrap;
}
.settings-group { min-width: 160px; }
.sg-label {
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #bbb; margin-bottom: 10px; display: block;
}

/* mode buttons */
.mode-btns { display: flex; gap: 6px; }
.mode-btn {
    padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600;
    border: 1.5px solid #e0e0e0; background: #fff; color: #888;
    cursor: pointer; transition: all .15s; font-family: 'DM Sans', sans-serif;
    white-space: nowrap;
}
.mode-btn.active-easy    { background:#f0fdf4; border-color:#86efac; color:#16a34a; }
.mode-btn.active-medium  { background:#fffbeb; border-color:#fde68a; color:#d97706; }
.mode-btn.active-extreme { background:#fff1f2; border-color:#fecdd3; color:#e11d48; }

/* toggle row */
.toggle-row { display: flex; flex-direction: column; gap: 8px; }
.t-item { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; color: #444; }

/* tier checkboxes */
.tier-row { display: flex; gap: 8px; flex-wrap: wrap; }
.tier-check {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 11px; border-radius: 8px; border: 1.5px solid;
    font-size: 12px; font-weight: 600; cursor: pointer;
    transition: all .12s; user-select: none;
}
.tier-check.t1-on  { background:#f0fdf4; border-color:#86efac; color:#16a34a; }
.tier-check.t1-off { background:#fff;    border-color:#e0e0e0; color:#bbb; }
.tier-check.t2-on  { background:#fffbeb; border-color:#fde68a; color:#d97706; }
.tier-check.t2-off { background:#fff;    border-color:#e0e0e0; color:#bbb; }
.tier-check.t3-on  { background:#f8f8f6; border-color:#d0d0d0; color:#777; }
.tier-check.t3-off { background:#fff;    border-color:#e0e0e0; color:#bbb; }

/* dedup badge */
.dedup-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 11px; border-radius: 8px;
    background: #f5f3ff; border: 1.5px solid #c4b5fd;
    font-size: 12px; font-weight: 600; color: #5b5bd6;
}

/* ── STATUS CHIPS ── */
.chips { display: flex; gap: 6px; flex-wrap: wrap; margin: 12px 0 20px; }
.chip {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 4px 11px; border-radius: 99px; font-size: 11px;
    font-weight: 600; border: 1.5px solid; font-family: 'DM Sans', sans-serif;
}
.c-easy    { background:#f0fdf4; color:#16a34a; border-color:#bbf7d0; }
.c-medium  { background:#fffbeb; color:#d97706; border-color:#fde68a; }
.c-extreme { background:#fff1f2; color:#e11d48; border-color:#fecdd3; }
.c-violet  { background:#f5f3ff; color:#5b5bd6; border-color:#c4b5fd; }
.c-neutral { background:#f8f8f6; color:#555;    border-color:#e0e0e0; }
.c-amber   { background:#fff8ed; color:#c47d00; border-color:#fcd34d; }
.c-green   { background:#f0fdf4; color:#16a34a; border-color:#86efac; }

/* ── SESSION CARDS ── */
.sess-card {
    background: #fff; border: 1.5px solid #ebebeb; border-radius: 14px;
    padding: 14px 16px; transition: border-color .15s, box-shadow .15s;
}
.sess-card.active { border-color: #5b5bd6; box-shadow: 0 2px 12px rgba(91,91,214,.12); }
.sess-name { font-size: 13px; font-weight: 700; color: #1a1a1a; }
.sess-meta { font-size: 11px; color: #aaa; margin-top: 2px; }
.sess-nums { display: flex; gap: 8px; margin-top: 10px; }
.sess-n {
    flex: 1; background: #f7f7f5; border-radius: 8px;
    padding: 6px 4px; text-align: center;
}
.sess-n-v { font-size: 16px; font-weight: 700; color: #1a1a1a; }
.sess-n-l { font-size: 10px; color: #aaa; }

/* ── INPUTS ── */
.stTextArea textarea {
    background: #fff !important; border: 1.5px solid #e0e0e0 !important;
    border-radius: 12px !important; color: #1a1a1a !important;
    font-family: 'DM Mono', monospace !important; font-size: 12.5px !important;
    padding: 12px 14px !important; line-height: 1.7 !important;
    transition: border-color .15s, box-shadow .15s !important;
}
.stTextArea textarea:focus {
    border-color: #5b5bd6 !important;
    box-shadow: 0 0 0 3px rgba(91,91,214,.1) !important;
}
.stTextArea textarea::placeholder { color: #ccc !important; }

[data-baseweb="select"] > div {
    background: #fff !important; border: 1.5px solid #e0e0e0 !important;
    border-radius: 12px !important; color: #1a1a1a !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 13px !important;
}
[data-baseweb="popover"] > div {
    background: #fff !important; border: 1.5px solid #e0e0e0 !important;
    border-radius: 14px !important; box-shadow: 0 8px 30px rgba(0,0,0,.08) !important;
    overflow: hidden !important;
}
[role="option"] {
    background: #fff !important; color: #1a1a1a !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 13px !important;
    padding: 9px 14px !important;
}
[role="option"]:hover { background: #f5f3ff !important; color: #5b5bd6 !important; }
[data-testid="stFileUploader"] section {
    background: #fff !important; border: 1.5px dashed #d0d0d0 !important;
    border-radius: 14px !important; transition: border-color .15s !important;
}
[data-testid="stFileUploader"] section:hover { border-color: #5b5bd6 !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #efefed !important; border-radius: 12px !important;
    padding: 4px !important; gap: 2px !important; border: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #888 !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 13px !important;
    font-weight: 500 !important; border-radius: 9px !important;
    padding: 7px 16px !important; border: none !important;
    letter-spacing: 0 !important; text-transform: none !important;
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: #1a1a1a !important;
    font-weight: 700 !important; box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
}
[data-testid="stTabsContent"] {
    padding: 12px 0 0 !important; border: none !important; background: transparent !important;
}

/* ── BUTTONS ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important; font-size: 13px !important;
    font-weight: 700 !important; border-radius: 10px !important;
    padding: 10px 20px !important; letter-spacing: 0 !important;
    text-transform: none !important; transition: all .15s !important; border: none !important;
}
.stButton > button[kind="primary"] {
    background: #1a1a1a !important; color: #fff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.18) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #333 !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.22) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #e0e0e0 !important; color: #aaa !important;
    box-shadow: none !important; transform: none !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important; color: #555 !important;
    border: 1.5px solid #e0e0e0 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #c4b5fd !important; color: #5b5bd6 !important;
}
.stDownloadButton > button {
    font-family: 'DM Sans', sans-serif !important; font-size: 13px !important;
    font-weight: 700 !important; border-radius: 10px !important;
    padding: 10px 20px !important; letter-spacing: 0 !important;
    text-transform: none !important; transition: all .15s !important;
    background: #fff !important; border: 1.5px solid #5b5bd6 !important;
    color: #5b5bd6 !important;
}
.stDownloadButton > button:hover {
    background: #f5f3ff !important;
    box-shadow: 0 2px 12px rgba(91,91,214,.18) !important;
    transform: translateY(-1px) !important;
}

/* ── PROGRESS ── */
.stProgress > div > div {
    background: #ebebeb !important; border-radius: 99px !important; height: 5px !important;
}
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #5b5bd6, #818cf8) !important;
    border-radius: 99px !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: #fff; border: 1.5px solid #ebebeb; border-radius: 14px;
    padding: 16px !important; transition: box-shadow .15s, transform .15s;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,.06); transform: translateY(-1px);
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important; font-weight: 700 !important;
    color: #aaa !important; letter-spacing: .5px !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-size: 26px !important; font-weight: 800 !important; color: #1a1a1a !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border: 1.5px solid #ebebeb !important; border-radius: 16px !important;
    overflow: hidden !important; box-shadow: 0 2px 8px rgba(0,0,0,.03) !important;
}

/* ── LIVE LOG ── */
.log-wrap {
    background: #fff; border: 1.5px solid #ebebeb; border-radius: 14px;
    padding: 0; overflow: hidden; margin-bottom: 14px;
}
.log-header {
    padding: 10px 16px; border-bottom: 1px solid #f0f0f0;
    display: flex; align-items: center; justify-content: space-between;
    background: #fafaf8;
}
.log-header-title {
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #bbb;
}
.log-header-stat {
    font-size: 11px; font-weight: 600; color: #5b5bd6;
    background: #f5f3ff; border-radius: 99px; padding: 2px 10px;
}
.log-body {
    padding: 12px 16px; max-height: 260px; overflow-y: auto;
    font-family: 'DM Mono', monospace; font-size: 12px; line-height: 2;
}
/* site header in log */
.ll-site {
    font-weight: 700; color: #1a1a1a; font-size: 12.5px;
    margin-top: 6px;
}
.ll-site::before { content: '▶  '; color: #5b5bd6; }
/* page being scraped */
.ll-page { color: #aaa; padding-left: 16px; }
.ll-page::before { content: '↳ '; }
/* email found */
.ll-email {
    color: #16a34a; font-weight: 600; padding-left: 28px;
    background: #f0fdf4; border-radius: 6px; padding: 2px 8px 2px 28px;
    display: inline-block; margin: 1px 0;
}
.ll-email::before { content: '✉ '; }
/* social found */
.ll-social { color: #5b5bd6; padding-left: 28px; }
.ll-social::before { content: '⟐ '; }
/* tier-1 skip */
.ll-skip { color: #d97706; font-weight: 600; padding-left: 16px; font-style: italic; }
.ll-skip::before { content: '⚡ '; }
/* timing */
.ll-timing { color: #bbb; padding-left: 16px; font-size: 11px; }
.ll-timing::before { content: '⏱ '; }
/* done */
.ll-done { color: #ccc; padding-left: 16px; }
.ll-done::before { content: '✓ '; }

/* ── SEC LABEL ── */
.sec-lbl {
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #bbb;
    margin: 24px 0 12px; display: flex; align-items: center; gap: 10px;
}
.sec-lbl::after { content: ''; flex: 1; height: 1.5px; background: #f0f0f0; }

/* ── URL PILLS ── */
.url-pills { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 4px; }
.url-pill {
    background: #efefed; border: 1.5px solid #e0e0e0;
    border-radius: 99px; padding: 3px 11px;
    font-size: 12px; color: #555; font-weight: 500;
}

/* col preview */
.col-prev {
    background: #f7f7f5; border: 1.5px solid #ebebeb; border-radius: 10px;
    padding: 10px 14px; margin-top: 8px; font-size: 12px; color: #888;
    line-height: 1.8; max-height: 90px; overflow-y: auto;
    font-family: 'DM Mono', monospace;
}
.col-prev-l {
    font-size: 10px; font-weight: 700; color: #bbb;
    letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px;
}

/* info chip */
.info-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f5f3ff; border-radius: 99px; padding: 4px 13px;
    font-size: 12px; font-weight: 600; color: #5b5bd6; margin-top: 8px;
}

/* tier legend */
.tier-legend { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
.tl-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 11px; border-radius: 99px;
    font-size: 12px; font-weight: 600; border: 1.5px solid;
}
.tl1 { background: #f0fdf4; border-color: #bbf7d0; color: #16a34a; }
.tl2 { background: #fffbeb; border-color: #fde68a; color: #d97706; }
.tl3 { background: #f8f8f6; border-color: #e0e0e0; color: #777; }

/* divider */
hr { border-color: #f0f0f0 !important; margin: 16px 0 !important; }

/* scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #aaa; }

/* label */
label[data-testid="stWidgetLabel"] {
    font-size: 10px !important; font-weight: 700 !important;
    color: #bbb !important; letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
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
    # Contact
    "/contact", "/contact-us", "/contact_us", "/contactus",
    "/reach-us", "/get-in-touch", "/say-hello",
    # About / team
    "/about",   "/about-us",   "/about_us",   "/aboutus",
    "/team",    "/our-team",   "/staff",       "/people",
    # Write for us / guest / submissions
    "/write-for-us", "/write-for-us/", "/writeforus",
    "/guest-post",   "/guest-posts",   "/guest-author",
    "/contribute",   "/contributors",  "/submission",
    "/submissions",  "/submit",        "/pitch",
    "/advertise",    "/advertise-with-us", "/advertising",
    "/work-with-us", "/partner",       "/partnerships",
]

# Keywords to detect "write for us" style links ON the homepage
WRITE_LINK_KEYWORDS = [
    "write-for", "write for", "guest post", "guest-post",
    "contribute", "submission", "submit", "pitch us",
    "advertis", "work with us", "partner with",
]
TWITTER_SKIP  = {'share','intent','home','search','hashtag','i','status','twitter','x'}
LINKEDIN_SKIP = {'share','shareArticle','in','company','pub','feed','login','authwall'}
FACEBOOK_SKIP = {'sharer','share','dialog','login','home','watch','groups','events','marketplace'}

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
for k, v in {
    "results":         {},
    "scraped_domains": set(),
    "scan_state":      "idle",
    "scan_queue":      [],
    "scan_idx":        0,
    "log_lines":       [],
    "sessions":        [],
    "active_session":  None,
    "f_tier1":         True,
    "f_tier2":         True,
    "f_tier3":         True,
    "mode":            "Easy",
    "single_mode":     False,
    "skip_t1":         True,
    "scrape_fb":       False,
    "scrape_fb":       False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
#  CORE FUNCTIONS
# ─────────────────────────────────────────
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
    if re.search(r'@\d+x[\-\d]', '@' + do): return False
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

def tier_label(email):
    k = tier_key(email)
    return {"1": "🥇 Tier 1", "2": "🥈 Tier 2", "3": "🥉 Tier 3"}[k]

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
        if r.ok and "text" in r.headers.get("Content-Type", ""):
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
        href = a["href"]
        hl   = href.lower()
        if "twitter.com/" in hl or "x.com/" in hl:
            m = re.search(r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})', href)
            if m and m.group(1).lower() not in TWITTER_SKIP:
                tw.add("@" + m.group(1))
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
    soup  = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        p    = urlparse(full)
        if p.netloc == root_domain and p.scheme in ("http","https"):
            links.append(full.split("#")[0].split("?")[0])
    return list(set(links))

def find_write_for_us_links(html, base_url, root_domain):
    """
    Scan any page for links whose text or href contains write-for-us keywords.
    Returns a list of internal URLs to add to the priority queue.
    """
    WRITE_KEYWORDS = [
        "write for us", "write-for-us", "writeforus",
        "guest post", "guest-post", "guestpost",
        "contribute", "contributors", "submission", "submissions",
        "submit a", "pitch us", "pitch to us",
        "advertise", "advertising", "advertise with",
        "work with us", "partner with", "partnerships",
        "become a contributor", "become an author",
        "join our team", "write with us",
    ]
    soup  = BeautifulSoup(html, "html.parser")
    found = []
    for a in soup.find_all("a", href=True):
        href    = a.get("href","")
        text    = (a.get_text(" ", strip=True) + " " + href).lower()
        if any(kw in text for kw in WRITE_KEYWORDS):
            full = urljoin(base_url, href)
            p    = urlparse(full)
            if p.netloc == root_domain and p.scheme in ("http","https"):
                found.append(full.split("#")[0].split("?")[0])
    return list(set(found))


def scrape_facebook_page(fb_handle, log_cb):
    """
    Fetch ONE Facebook page — the main page linked from the site.
    fb_handle is like "facebook.com/somepage"
    Returns set of emails found.
    """
    slug = fb_handle.replace("facebook.com/","").strip("/")
    if not slug: return set()

    url = f"https://www.facebook.com/{slug}"
    log_cb(("page_start", url.replace("https://",""), "facebook", None), "active")
    t0      = time.time()
    html    = fetch_page(url, timeout=14)
    elapsed = round(time.time() - t0, 2)

    if html:
        found = extract_emails(html)
        for e in sort_by_tier(found):
            log_cb(("email", e, f"facebook.com/{slug}", tier_label(e)), "email")
        log_cb(("timing", f"{elapsed}s · {len(found)} email(s) from Facebook page", url, None), "timing")
        return found
    else:
        log_cb(("timing", f"{elapsed}s · Facebook blocked or no content returned", url, None), "timing")
        return set()


def fetch_sitemap_urls(root_url):
    urls = []
    for c in [urljoin(root_url,"/sitemap.xml"), urljoin(root_url,"/sitemap_index.xml")]:
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
                else: urls.append(u)
        except: pass
        if urls: break
    return urls

def scrape_one_site(root_url, cfg, skip_t1, log_cb):
    """Scrape a site, calling log_cb with rich per-page events."""
    t_start     = time.time()
    parsed      = urlparse(root_url)
    root_domain = parsed.netloc
    visited     = set()
    queue       = deque()
    all_emails  = set()
    all_tw, all_li, all_fb = set(), set(), set()

    base = root_url.rstrip("/")
    for path in PRIORITY_PATHS:
        queue.append((base + path, 0, True))
    queue.append((root_url, 0, False))

    if cfg.get("sitemap"):
        log_cb(("sitemap", f"Scanning sitemap for {root_domain}...", None, None), "info")
        sm_urls = fetch_sitemap_urls(root_url)
        log_cb(("sitemap", f"{len(sm_urls)} URLs found in sitemap", None, None), "info")
        for u in sm_urls[:cfg["max_pages"]]:
            queue.append((u, 0, False))

    max_pages  = cfg["max_pages"]
    max_depth  = cfg["max_depth"]
    pages_done = 0

    while queue and pages_done < max_pages + len(PRIORITY_PATHS):
        url, depth, is_priority = queue.popleft()
        if url in visited: continue
        visited.add(url)

        label    = "priority" if is_priority else f"{pages_done+1}/{max_pages}"
        short    = url.replace("https://","").replace("http://","")
        t_page   = time.time()

        log_cb(("page_start", short, label, None), "active")

        html = fetch_page(url)
        elapsed = round(time.time() - t_page, 2)

        if html:
            found        = extract_emails(html)
            new_emails   = found - all_emails
            tw, li, fb   = extract_social(html)
            new_tw       = tw - all_tw
            new_li       = li - all_li
            new_fb       = fb - all_fb

            all_emails.update(found)
            all_tw.update(tw); all_li.update(li); all_fb.update(fb)

            # Hunt for write-for-us / guest-post / advertise links on every page
            wfu_links = find_write_for_us_links(html, url, root_domain)
            for wlink in wfu_links:
                if wlink not in visited:
                    queue.appendleft((wlink, 0, True))  # push to front as priority
                    log_cb(("info", f"Write-for-us link found → {wlink.replace('https://','')}", None, None), "info")

            # Log each new email found
            for email in sort_by_tier(new_emails):
                log_cb(("email", email, short, tier_label(email)), "email")

            # Log new social handles
            for handle in sorted(new_tw | new_li | new_fb):
                log_cb(("social", handle, short, None), "social")

            log_cb(("timing", f"{elapsed}s · {len(new_emails)} new email(s) on this page", short, None), "timing")

            if not is_priority and depth < max_depth:
                for link in get_internal_links(html, url, root_domain):
                    if link not in visited:
                        queue.append((link, depth+1, False))

            if skip_t1 and any(TIER1.match(e) for e in all_emails):
                t1 = next(e for e in all_emails if TIER1.match(e))
                log_cb(("skip", f"Tier 1 found ({t1}) — skipping rest of {root_domain}", None, None), "skip")
                break
        else:
            log_cb(("timing", f"{elapsed}s · no response", short, None), "timing")

        if not is_priority:
            pages_done += 1

    total_time = round(time.time() - t_start, 1)
    sorted_emails = sort_by_tier(all_emails)
    best = pick_best(all_emails)

    log_cb(("done", f"{root_domain} — {len(all_emails)} email(s) in {total_time}s", None, None), "done")

    return {
        "Domain":        root_domain,
        "Best Email":    best or "",
        "Best Tier":     tier_label(best) if best else "—",
        "All Emails":    sorted_emails,
        "Twitter":       sorted(all_tw),
        "LinkedIn":      sorted(all_li),
        "Facebook":      sorted(all_fb),
        "Pages Scraped": pages_done,
        "Total Time":    total_time,
        "Source URL":    root_url,
    }

# ─────────────────────────────────────────
#  LOG RENDERER
# ─────────────────────────────────────────
def render_log(placeholder):
    """Render the rich log from st.session_state.log_lines."""
    lines_html = ""
    total_emails = sum(1 for _, k in st.session_state.log_lines if k == "email")
    for item, kind in st.session_state.log_lines[-60:]:
        event, text, page, extra = item
        if kind == "active":
            lines_html += f'<div class="ll-page">[{extra or ""}] {text}</div>'
        elif kind == "email":
            lines_html += f'<div class="ll-email">{text} <span style="color:#aaa;font-weight:400;font-size:11px">· {extra}</span></div>'
        elif kind == "social":
            lines_html += f'<div class="ll-social">{text} <span style="color:#aaa;font-size:11px">· {page}</span></div>'
        elif kind == "timing":
            lines_html += f'<div class="ll-timing">{text}</div>'
        elif kind == "skip":
            lines_html += f'<div class="ll-skip">{text}</div>'
        elif kind == "done":
            lines_html += f'<div class="ll-done">{text}</div>'
        elif kind == "site":
            lines_html += f'<div class="ll-site">{text}</div>'
        elif kind == "info":
            lines_html += f'<div class="ll-done">{text}</div>'

    placeholder.markdown(f"""
    <div class="log-wrap">
      <div class="log-header">
        <span class="log-header-title">Live Log</span>
        <span class="log-header-stat">{total_emails} emails found so far</span>
      </div>
      <div class="log-body">{lines_html}</div>
    </div>""", unsafe_allow_html=True)

def log_cb_factory(placeholder):
    def log_cb(item, kind):
        st.session_state.log_lines.append((item, kind))
        render_log(placeholder)
    return log_cb

# ─────────────────────────────────────────
#  BRAND
# ─────────────────────────────────────────
st.markdown("""
<div class="brand">
  <div class="brand-name">Mail<span>Hunter</span></div>
</div>
<div class="brand-sub">Scrape contact emails, social handles and tier-ranked contacts from any website.</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  SETTINGS PANEL (inline, no sidebar)
# ─────────────────────────────────────────
with st.expander("⚙️  Settings", expanded=True):
    col_mode, col_extract, col_tiers, col_dedup = st.columns([2, 2, 2.5, 2])

    with col_mode:
        st.markdown('<span class="sg-label">Scraping Mode</span>', unsafe_allow_html=True)
        mode_options = ["Easy", "Medium", "Extreme"]
        mode_icons   = {"Easy":"🟢","Medium":"🟡","Extreme":"🔴"}
        mode_descs   = {"Easy":"Homepage only","Medium":"Crawl site links","Extreme":"Sitemap + deep"}
        for m in mode_options:
            active_cls = f"active-{m.lower()}" if st.session_state.mode == m else ""
            st.markdown(f'<div style="margin-bottom:4px"></div>', unsafe_allow_html=True)
            if st.button(f"{mode_icons[m]}  {m} — {mode_descs[m]}",
                         key=f"mode_{m}",
                         type="primary" if st.session_state.mode == m else "secondary",
                         use_container_width=True):
                st.session_state.mode = m
                st.rerun()

    with col_extract:
        st.markdown('<span class="sg-label">Extraction</span>', unsafe_allow_html=True)
        st.session_state.single_mode = st.toggle(
            "Best email per site only",
            value=st.session_state.single_mode,
            help="ON = one best email per domain. OFF = all valid emails grouped.",
        )
        st.session_state.skip_t1 = st.toggle(
            "Skip site once Tier 1 found",
            value=st.session_state.skip_t1,
            help="Stops crawling as soon as editor/admin/press/contact email is found.",
        )
        st.caption("All modes auto-scrape /contact, /about & write-for-us pages.")

    with col_tiers:
        st.markdown('<span class="sg-label">Tier Filters</span>', unsafe_allow_html=True)
        st.session_state.f_tier1 = st.checkbox("🥇 Tier 1 — editor / admin / press",  value=st.session_state.f_tier1)
        st.session_state.f_tier2 = st.checkbox("🥈 Tier 2 — info / sales / support",  value=st.session_state.f_tier2)
        st.session_state.f_tier3 = st.checkbox("🥉 Tier 3 — other valid emails",       value=st.session_state.f_tier3)

    with col_dedup:
        st.markdown('<span class="sg-label">Parameters & Memory</span>', unsafe_allow_html=True)
        mode_key = st.session_state.mode
        cfg = {
            "Easy":    {"max_pages": 1,   "max_depth": 0, "sitemap": False, "delay": 0.3},
            "Medium":  {"max_pages": 50,  "max_depth": 3, "sitemap": False, "delay": 0.5},
            "Extreme": {"max_pages": 300, "max_depth": 6, "sitemap": True,  "delay": 0.3},
        }[mode_key].copy()

        if mode_key == "Medium":
            cfg["max_depth"] = st.slider("Crawl depth",        1, 5, 3, key="depth_s")
            cfg["max_pages"] = st.slider("Max pages per site", 10, 200, 50, key="pages_s")
        elif mode_key == "Extreme":
            cfg["max_pages"] = st.slider("Max pages per site", 50, 500, 300, key="pages_x")

        n_dedup = len(st.session_state.scraped_domains)
        st.markdown(f'<div style="margin-top:8px"></div>', unsafe_allow_html=True)
        st.caption(f"{n_dedup} domain(s) in memory — won't be re-scraped.")
        if n_dedup and st.button("Clear domain memory", type="secondary", use_container_width=True):
            st.session_state.scraped_domains = set()
            st.rerun()

# ─────────────────────────────────────────
#  STATUS CHIPS
# ─────────────────────────────────────────
mode_key   = st.session_state.mode
single_m   = st.session_state.single_mode
skip_t1    = st.session_state.skip_t1
scrape_fb  = st.session_state.scrape_fb
scan_state = st.session_state.scan_state

scrape_fb  = st.session_state.get("scrape_fb", False)
chip_cls   = {"Easy":"c-easy","Medium":"c-medium","Extreme":"c-extreme"}[mode_key]
chip_ico   = {"Easy":"🟢","Medium":"🟡","Extreme":"🔴"}[mode_key]
state_chip = {"idle":"","running":'<span class="chip c-violet">● Running</span>',
              "paused":'<span class="chip c-amber">⏸ Paused</span>',
              "done":'<span class="chip c-green">✓ Done</span>'}[scan_state]

st.markdown(f"""
<div class="chips">
  <span class="chip {chip_cls}">{chip_ico} {mode_key}</span>
  <span class="chip {'c-violet' if single_m else 'c-neutral'}">{'🎯 Best email' if single_m else '📋 All emails'}</span>
  <span class="chip {'c-violet' if skip_t1 else 'c-neutral'}">{'⚡ Skip on Tier 1' if skip_t1 else 'No early skip'}</span>
  <span class="chip c-neutral">✅ /contact, /about & write-for-us always scraped</span>
  {state_chip}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  SESSION CARDS
# ─────────────────────────────────────────
sessions = st.session_state.sessions
if sessions:
    st.markdown('<div class="sec-lbl">Saved Sessions</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(sessions), 5))
    for i, sess in enumerate(sessions):
        with cols[i % 5]:
            total_e = sum(len(r.get("All Emails",[])) for r in sess["results"].values())
            is_act  = st.session_state.active_session == sess["name"]
            st.markdown(f"""
            <div class="sess-card {'active' if is_act else ''}">
              <div class="sess-name">{sess['name']}</div>
              <div class="sess-meta">{sess['ts']}</div>
              <div class="sess-nums">
                <div class="sess-n"><div class="sess-n-v">{len(sess['results'])}</div><div class="sess-n-l">domains</div></div>
                <div class="sess-n"><div class="sess-n-v">{total_e}</div><div class="sess-n-l">emails</div></div>
              </div>
            </div>""", unsafe_allow_html=True)
            lc, rc = st.columns(2)
            with lc:
                if st.button("Load", key=f"ls_{i}", use_container_width=True, type="secondary"):
                    st.session_state.results        = sess["results"]
                    st.session_state.active_session = sess["name"]
                    st.session_state.scan_state     = "done"
                    st.rerun()
            with rc:
                if st.button("Del",  key=f"ds_{i}", use_container_width=True, type="secondary"):
                    st.session_state.sessions.pop(i)
                    st.rerun()

# ─────────────────────────────────────────
#  TARGET INPUT
# ─────────────────────────────────────────
st.markdown('<div class="sec-lbl">Target URLs</div>', unsafe_allow_html=True)
tab_paste, tab_upload = st.tabs(["✏️  Paste URLs", "📁  Upload CSV / TXT"])
urls_to_scrape = []

with tab_paste:
    raw = st.text_area("", placeholder="https://magazine.com\nhttps://newspaper.org\nagency.co  ← bare domains work too",
                       height=120, label_visibility="collapsed")
    if raw.strip():
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            if not line.startswith("http"): line = "https://" + line
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
                prev   = df_up[sel].dropna().head(5).tolist()
                ph     = "".join(f"<div>{str(v)[:72]}</div>" for v in prev)
                st.markdown(f'<div class="col-prev"><div class="col-prev-l">Preview — first 5</div>{ph}</div>',
                            unsafe_allow_html=True)
                for u in df_up[sel].dropna().astype(str):
                    u = u.strip()
                    if not u.startswith("http"): u = "https://" + u
                    urls_to_scrape.append(u)
                st.markdown(f'<span class="info-chip">✓ {len(urls_to_scrape)} URLs · {len(cols_u)} columns</span>',
                            unsafe_allow_html=True)
            except Exception as e:
                st.error(f"CSV error: {e}")
        else:
            for line in raw_bytes.decode("utf-8").splitlines():
                line = line.strip()
                if not line: continue
                if not line.startswith("http"): line = "https://" + line
                urls_to_scrape.append(line)
            st.markdown(f'<span class="info-chip">✓ {len(urls_to_scrape)} URLs</span>', unsafe_allow_html=True)

if urls_to_scrape:
    pills = "".join(
        f'<span class="url-pill">{u.replace("https://","").replace("http://","")[:38]}</span>'
        for u in urls_to_scrape[:12])
    if len(urls_to_scrape) > 12:
        pills += f'<span class="url-pill" style="color:#aaa">+{len(urls_to_scrape)-12} more</span>'
    st.markdown(f'<div class="url-pills">{pills}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  ACTION BUTTONS
# ─────────────────────────────────────────
b1, b2, b3, b4, b5 = st.columns([2, 1.6, 1, 1, 3])
with b1:
    start_btn = st.button("Start Scan",
                          type="primary",
                          disabled=(not urls_to_scrape or scan_state == "running"),
                          use_container_width=True)
with b2:
    pause_lbl = "Pause" if scan_state == "running" else "Resume"
    pause_btn = st.button(pause_lbl, type="secondary",
                          disabled=(scan_state not in ("running","paused")),
                          use_container_width=True)
with b3:
    save_btn  = st.button("Save", type="secondary",
                          disabled=not st.session_state.results,
                          use_container_width=True)
with b4:
    clear_btn = st.button("Clear", type="secondary",
                          use_container_width=True)

# ── Button logic ──
if start_btn and urls_to_scrape:
    new_urls, skipped = [], []
    for u in urls_to_scrape:
        d = urlparse(u if u.startswith("http") else "https://"+u).netloc
        if d in st.session_state.scraped_domains:
            skipped.append(d)
        else:
            new_urls.append(u)
    if skipped:
        st.info(f"Skipping {len(skipped)} already-scraped domain(s). Clear domain memory in Settings to re-scrape.")
    if new_urls:
        st.session_state.scan_queue  = new_urls
        st.session_state.scan_idx    = 0
        st.session_state.scan_state  = "running"
        st.session_state.log_lines   = []
        st.rerun()

if pause_btn:
    st.session_state.scan_state = "paused" if scan_state == "running" else "running"
    st.rerun()

if save_btn and st.session_state.results:
    ts   = datetime.now().strftime("%b %d %H:%M")
    name = f"Scan {len(st.session_state.sessions)+1} · {ts}"
    st.session_state.sessions.append({
        "name":    name,
        "ts":      ts,
        "results": dict(st.session_state.results),
    })
    st.session_state.active_session = name
    st.rerun()

if clear_btn:
    for k in ["results","scan_queue","log_lines"]:
        st.session_state[k] = {} if k=="results" else []
    st.session_state.scan_state     = "idle"
    st.session_state.scan_idx       = 0
    st.session_state.active_session = None
    st.rerun()

# ─────────────────────────────────────────
#  SCAN ENGINE  (one site per rerun)
# ─────────────────────────────────────────
if st.session_state.scan_state == "running":
    queue = st.session_state.scan_queue
    idx   = st.session_state.scan_idx
    total = len(queue)

    if idx < total:
        url = queue[idx]
        if not url.startswith("http"): url = "https://" + url

        # progress
        prog_ph  = st.progress(idx / total)
        st.markdown(f'<div style="font-size:12px;color:#aaa;margin:-6px 0 8px">'
                    f'Site {idx+1} of {total}: {url}</div>', unsafe_allow_html=True)

        # log placeholder
        log_ph = st.empty()
        render_log(log_ph)  # show existing log

        # log site header
        domain_short = urlparse(url).netloc
        st.session_state.log_lines.append((
            ("site", domain_short, None, None), "site"))

        log_cb = log_cb_factory(log_ph)
        row    = scrape_one_site(url, cfg, skip_t1, log_cb)

        # store
        st.session_state.results[row["Domain"]] = row
        st.session_state.scraped_domains.add(row["Domain"])
        st.session_state.scan_idx = idx + 1

        prog_ph.progress((idx + 1) / total)
        time.sleep(cfg.get("delay", 0.3))

        if st.session_state.scan_idx >= total:
            st.session_state.scan_state = "done"
        st.rerun()
    else:
        st.session_state.scan_state = "done"
        st.rerun()

elif st.session_state.scan_state == "paused" and st.session_state.log_lines:
    log_ph = st.empty()
    render_log(log_ph)
    rem = len(st.session_state.scan_queue) - st.session_state.scan_idx
    st.warning(f"Paused after site {st.session_state.scan_idx} of {len(st.session_state.scan_queue)}. "
               f"{rem} site(s) remaining — click Resume.")

elif st.session_state.scan_state == "done" and st.session_state.log_lines:
    log_ph = st.empty()
    render_log(log_ph)

# ─────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results
    st.markdown('<div class="sec-lbl">Results</div>', unsafe_allow_html=True)

    tier_filter = []
    if st.session_state.f_tier1: tier_filter.append("1")
    if st.session_state.f_tier2: tier_filter.append("2")
    if st.session_state.f_tier3: tier_filter.append("3")

    # ── METRICS ──
    tot_d  = len(results)
    tot_e  = sum(len(r.get("All Emails",[])) for r in results.values())
    t1_cnt = sum(1 for r in results.values() if r.get("Best Tier","").startswith("🥇"))
    soc    = sum(1 for r in results.values() if r.get("Twitter") or r.get("LinkedIn") or r.get("Facebook"))
    no_e   = sum(1 for r in results.values() if not r.get("Best Email"))

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Domains",     tot_d)
    c2.metric("Emails",      tot_e)
    c3.metric("Tier 1 hits", t1_cnt)
    c4.metric("Social found",soc)
    c5.metric("No email",    no_e)

    if not st.session_state.single_mode:
        st.markdown("""
        <div class="tier-legend">
          <span class="tl-badge tl1">🥇 Tier 1 — editor/admin/press/contact</span>
          <span class="tl-badge tl2">🥈 Tier 2 — info/sales/support/office</span>
          <span class="tl-badge tl3">🥉 Tier 3 — other valid emails</span>
        </div>""", unsafe_allow_html=True)

    # ── PER-DOMAIN RESULT ROWS ──
    for domain, r in results.items():
        all_e    = r.get("All Emails", [])
        fb_pages = r.get("Facebook", [])

        if st.session_state.single_mode:
            disp_emails = r.get("Best Email","") or "—"
        else:
            filtered    = [e for e in all_e if tier_key(e) in tier_filter]
            disp_emails = " | ".join(filtered) if filtered else "—"

        # Row card
        st.markdown(f"""
        <div style="background:#fff;border:1.5px solid #ebebeb;border-radius:14px;
                    padding:14px 18px;margin-bottom:8px;">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <div>
              <div style="font-size:13px;font-weight:700;color:#1a1a1a">{domain}</div>
              <div style="font-size:12px;color:#5b5bd6;margin-top:3px;font-family:'DM Mono',monospace;word-break:break-all">{disp_emails}</div>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
              {"".join(f'<span style="font-size:11px;color:#aaa">{h}</span>' for h in r.get("Twitter",[])[:2])}
              {"".join(f'<span style="font-size:11px;color:#3b5998">{f}</span>' for f in fb_pages[:1])}
              <span style="font-size:11px;color:#aaa">{r.get("Pages Scraped",0)} pages · {r.get("Total Time","?")}s</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Facebook scrape button — only show if a FB page was found
        if fb_pages:
            primary_fb = fb_pages[0]   # only the first / main page linked from the site
            fb_btn_key = f"fb_{domain}"
            fb_col, _ = st.columns([2, 5])
            with fb_col:
                if st.button(f"Scrape Facebook — {primary_fb.replace('facebook.com/','')[:28]}",
                             key=fb_btn_key, type="secondary", use_container_width=True):
                    st.session_state[f"fb_run_{domain}"] = True
                    st.rerun()

            # Run if button was clicked
            if st.session_state.get(f"fb_run_{domain}"):
                st.session_state[f"fb_run_{domain}"] = False
                fb_log_ph = st.empty()
                fb_lines  = []

                def fb_log(item, kind):
                    fb_lines.append((item, kind))
                    lines_html = ""
                    for itm, knd in fb_lines[-20:]:
                        ev, txt, pg, ex = itm
                        if knd == "active":  lines_html += f'<div class="ll-page">[facebook] {txt}</div>'
                        elif knd == "email": lines_html += f'<div class="ll-email">{txt}</div>'
                        elif knd == "timing":lines_html += f'<div class="ll-timing">{txt}</div>'
                        else:                lines_html += f'<div class="ll-done">{txt}</div>'
                    fb_log_ph.markdown(f'<div class="log-wrap"><div class="log-header"><span class="log-header-title">Facebook Log</span></div><div class="log-body">{lines_html}</div></div>',
                                       unsafe_allow_html=True)

                fb_emails = scrape_facebook_page(primary_fb, fb_log)
                if fb_emails:
                    new_fb_e = fb_emails - set(r.get("All Emails",[]))
                    updated  = sort_by_tier(set(r.get("All Emails",[])) | fb_emails)
                    st.session_state.results[domain]["All Emails"] = updated
                    best = pick_best(set(updated))
                    st.session_state.results[domain]["Best Email"] = best or ""
                    fb_log(("done", f"Added {len(new_fb_e)} new email(s) from Facebook", None, None), "done")
                else:
                    fb_log(("done", "No emails found — Facebook likely blocked the request", None, None), "done")
                time.sleep(0.5)
                st.rerun()

    # ── TABLE VIEW (collapsible) ──
    with st.expander("View as table"):
        rows = []
        for domain, r in results.items():
            all_e = r.get("All Emails", [])
            if st.session_state.single_mode:
                disp = r.get("Best Email","") or "—"
            else:
                filtered = [e for e in all_e if tier_key(e) in tier_filter]
                disp = " | ".join(filtered) if filtered else "—"
            rows.append({
                "Domain":   domain,
                "Emails":   disp,
                "Twitter":  ", ".join(r.get("Twitter",[])) or "—",
                "LinkedIn": ", ".join(r.get("LinkedIn",[])) or "—",
                "Facebook": ", ".join(r.get("Facebook",[])) or "—",
                "Pages":    r.get("Pages Scraped", 0),
                "Time (s)": r.get("Total Time", "—"),
                "Source":   r.get("Source URL",""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=380,
            column_config={
                "Domain":   st.column_config.TextColumn("Domain",    width="medium"),
                "Emails":   st.column_config.TextColumn("Emails",    width="large"),
                "Twitter":  st.column_config.TextColumn("Twitter",   width="medium"),
                "LinkedIn": st.column_config.TextColumn("LinkedIn",  width="medium"),
                "Facebook": st.column_config.TextColumn("Facebook",  width="medium"),
                "Pages":    st.column_config.NumberColumn("Pages",   width="small"),
                "Time (s)": st.column_config.NumberColumn("Time (s)",width="small"),
                "Source":   st.column_config.LinkColumn("Source",    width="medium"),
            })

    # ── CSV EXPORT ──
    st.markdown("<br>", unsafe_allow_html=True)
    csv_rows = []
    for domain, r in results.items():
        csv_rows.append({
            "Domain":        domain,
            "Best Email":    r.get("Best Email",""),
            "All Emails":    "; ".join(r.get("All Emails",[])),
            "Twitter":       "; ".join(r.get("Twitter",[])),
            "LinkedIn":      "; ".join(r.get("LinkedIn",[])),
            "Facebook":      "; ".join(r.get("Facebook",[])),
            "Pages Scraped": r.get("Pages Scraped",0),
            "Time (s)":      r.get("Total Time",""),
            "Source URL":    r.get("Source URL",""),
        })
    buf = io.StringIO()
    pd.DataFrame(csv_rows).to_csv(buf, index=False)

    d1, _, d3 = st.columns([2, 1, 3])
    with d1:
        st.download_button("Export CSV", buf.getvalue(),
                           f"mailhunter_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           "text/csv", use_container_width=True)
    with d3:
        st.caption("One row per domain · all emails in one cell · no tier labels")

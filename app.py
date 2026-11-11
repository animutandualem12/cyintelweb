from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os
from dotenv import load_dotenv

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Flask ----------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")  # fallback for local dev

# ---------- MongoDB ----------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["cti_db"]   # use your database name here


# ---------- Collections ----------
users = db.users
articles = db.articles
indicators = db.indicators
ads = db.ads
categories = db.categories
users.create_index("username", unique=True)
articles.create_index([("title", "text"), ("summary", "text"), ("content", "text")])
indicators.create_index([("value", "text"), ("description", "text"), ("tags", "text")])

# NEW: Category index
categories.create_index("name", unique=True)


# ---------- Auto Image Picker ----------
IMAGE_MAP = {
    # --- Trending Topic: Ransomware ---
    "ransomware": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "ransom": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "extortion": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "lockbit": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "double extortion": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",

    # --- Trending Topic: APT Groups ---
    "apt": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "apt groups": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "apt29": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "apt41": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "lazarus": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "nation-state": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "cyber espionage": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",

    # --- Trending Topic: Zero-Day ---
    "zero-day": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "zero day": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "0day": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",

    # --- Trending Topic: Phishing ---
    "phishing": "https://images.unsplash.com/photo-1614064642639-e398cf05badb?w=800&q=80",
    "spear phishing": "https://images.unsplash.com/photo-1614064642639-e398cf05badb?w=800&q=80",
    "quishing": "https://images.unsplash.com/photo-1614064642639-e398cf05badb?w=800&q=80",
    "email": "https://images.unsplash.com/photo-1596526131083-e8c633c948d2?w=800&q=80",
    "credential harvesting": "https://images.unsplash.com/photo-1596526131083-e8c633c948d2?w=800&q=80",

    # --- Trending Topic: Malware ---
    "malware": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "virus": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "trojan": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "infostealer": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "spyware": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
    "rootkit": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",

    # --- Trending Topic: Data Breach ---
    "data breach": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80",
    "breach": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80",
    "data leak": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80",
    "leak": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80",
    "exfiltration": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80",

    # --- Trending Topic: CISA ---
    "cisa": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",
    "government": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",
    "fbi": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",
    "advisory": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",
    "federal": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",

    # --- Trending Topic: Vulnerabilities ---
    "vulnerability": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "vulnerabilities": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "cve": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "vpn": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "patch": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    "rce": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",

    # --- Trending Topic: Jobs ---
    "jobs": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800&q=80",
    "careers": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800&q=80",

    # --- Extra Technical / Attack Simulation ---
    "red team": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "pentest": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "exploit": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "attack": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "hacker": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "hackers": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",

    # --- Extra Defensive / Blue Team ---
    "defense": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "defence": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "blue team": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "siem": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "edr": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "monitoring": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "soc": "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=800&q=80",
    "analyst": "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=800&q=80",

    # --- Extra Network / C2 ---
    "c2": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
    "command and control": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
    "botnet": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
    "network": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
    "server": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
    "ddos": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",

    # --- Extra Cloud / AI / IoT ---
    "cloud": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&q=80",
    "aws": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&q=80",
    "azure": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&q=80",
    "ai": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80",
    "artificial intelligence": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80",
    "machine learning": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80",
    "iot": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
    "mobile": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&q=80",
    "supply chain": "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=800&q=80",
    "insider": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=800&q=80",
    "database": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=800&q=80",
    "server room": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
}

CATEGORY_FALLBACK = {
    "News": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=800&q=80",
    "Business": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&q=80",
    "Government": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80",
    "Technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
    "Intelligence": "https://images.unsplash.com/photo-1614064548237-096f735f344f?w=800&q=80",
    "Jobs": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800&q=80",
}
def pick_image(title, category="", tags=None, custom=None):
    """Choose a relevant image for an article based on its title/keywords."""
    if custom and custom.strip():
        return custom.strip()

    haystack = f"{title} {category} {' '.join(tags or [])}".lower()

    matches = [(kw, url) for kw, url in IMAGE_MAP.items() if kw in haystack]

    if matches:
        matches.sort(key=lambda x: -len(x[0]))
        return matches[0][1]

    if category in CATEGORY_FALLBACK:
        return CATEGORY_FALLBACK[category]

    return "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80"


# ---------- Helpers ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))

        user = users.find_one({"username": session["user"]})

        if not user or user.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("index"))

        return f(*args, **kwargs)

    return wrapper


def current_user():
    if "user" in session:
        return users.find_one({"username": session["user"]})

    return None


def get_active_ads(position=None, ad_type=None):
    q = {"active": True}

    if position:
        q["position"] = position

    if ad_type:
        q["type"] = ad_type

    return list(
        ads.find(q).sort("created_at", -1)
    )


# ---------- Seed demo articles ----------
def seed_articles():
    if articles.count_documents({}) > 0:
        return

    demo = [
        # ---------- CISA / Government ----------
        {
            "title": "CISA Recommends Decoy Tactics Against Hackers",
            "category": "Technology",
            "subcategory": "Hackers",
            "summary": "Lures & Tripwires: Cyber defenders are recommended to deploy deceptive tactics, traps and bait to detect intrusions & confuse malicious actors.",
            "content": "CISA has published new guidance on deception technology — honeypots, honey credentials and decoys that lure attackers into revealing themselves...",
            "author": "Editorial Team",
            "date": datetime(2026, 9, 28),
            "tags": ["cisa", "deception", "defense"],
        },
        {
            "title": "CISA Adds 5 New CVEs To Known Exploited Vulnerabilities",
            "category": "Government",
            "subcategory": "Advisories",
            "summary": "The catalog now includes actively exploited flaws in edge devices, VPN appliances and file transfer tools.",
            "content": "CISA has added five new vulnerabilities to its Known Exploited Vulnerabilities catalog. Federal agencies are required to patch within two weeks...",
            "author": "News Desk",
            "date": datetime(2026, 9, 26),
            "tags": ["cisa", "cve", "advisory"],
        },

        # ---------- Breach / Data Leak ----------
        {
            "title": "ShinyHunters Claims Breach Of FBI Systems",
            "category": "Technology",
            "subcategory": "Hackers",
            "summary": "Hackers Issue A Public Threat: The notorious gang claim to have stolen agent & applicant records via a hiring portal in an apparent revenge attack.",
            "content": "The ShinyHunters group claims to have compromised a third-party hiring portal used by the FBI...",
            "author": "Editorial Team",
            "date": datetime(2026, 9, 23),
            "tags": ["shinyhunters", "breach", "fbi"],
        },
        {
            "title": "Major Healthcare Provider Leaks 4 Million Patient Records",
            "category": "News",
            "subcategory": "Breach",
            "summary": "An exposed misconfigured cloud bucket contained sensitive medical and insurance data for millions of patients.",
            "content": "A leading healthcare provider has disclosed a data breach affecting over four million patients after researchers discovered an unsecured cloud storage bucket...",
            "author": "News Desk",
            "date": datetime(2026, 9, 22),
            "tags": ["breach", "data leak", "healthcare"],
        },
        {
            "title": "Insider Threat Exposed Customer Database At Telecom Giant",
            "category": "Business",
            "subcategory": "Insider",
            "summary": "A former employee exfiltrated subscriber records weeks before resigning, according to court filings.",
            "content": "A telecom company has confirmed that a former employee accessed and copied customer records prior to leaving the organization...",
            "author": "Business Desk",
            "date": datetime(2026, 9, 21),
            "tags": ["breach", "insider", "data leak"],
        },

        # ---------- Ransomware ----------
        {
            "title": "Ransomware Gangs Shift To Data-Only Extortion",
            "category": "Intelligence",
            "subcategory": "Ransomware",
            "summary": "New wave of attacks skips encryption entirely, focusing on exfiltration and public leaks to pressure victims into paying.",
            "content": "A growing number of ransomware operators are abandoning encryption in favor of pure data-theft extortion...",
            "author": "Analyst Desk",
            "date": datetime(2026, 9, 20),
            "tags": ["ransomware", "extortion"],
        },
        {
            "title": "Ransomware Attack Forces Regional Hospital To Divert Patients",
            "category": "News",
            "subcategory": "Ransomware",
            "summary": "Emergency rooms are turning away non-critical cases as staff revert to pen and paper after encryption of key systems.",
            "content": "A regional hospital network has been forced to divert patients to neighboring facilities following a ransomware attack that crippled its electronic health record systems...",
            "author": "News Desk",
            "date": datetime(2026, 9, 19),
            "tags": ["ransomware", "healthcare", "attack"],
        },
        {
            "title": "LockBit Successor Emerges With New Double-Extortion Tactic",
            "category": "Intelligence",
            "subcategory": "Ransomware",
            "summary": "A new group calling itself 'RansomCartel' is targeting manufacturing firms across Europe and North America.",
            "content": "Researchers have identified a new ransomware operation that appears to have inherited tooling and infrastructure from the disrupted LockBit group...",
            "author": "Threat Research",
            "date": datetime(2026, 9, 17),
            "tags": ["ransomware", "extortion", "malware"],
        },

        # ---------- APT ----------
        {
            "title": "APT29 Uses Novel Credential Harvesting Tactic",
            "category": "Intelligence",
            "subcategory": "APT",
            "summary": "The Russian-linked group has been observed abusing OAuth device-code flows to silently harvest credentials at scale.",
            "content": "Researchers observed APT29 leveraging the OAuth 2.0 device authorization grant to trick users...",
            "author": "Threat Research",
            "date": datetime(2026, 9, 18),
            "tags": ["apt29", "oauth", "apt"],
        },
        {
            "title": "APT41 Targets Supply Chain Of Software Vendors",
            "category": "Intelligence",
            "subcategory": "APT",
            "summary": "Chinese state-linked actors compromise build pipelines to inject backdoors into signed updates.",
            "content": "Mandiant and other vendors have tracked APT41 activity against software supply chains, focusing on compromise of CI/CD pipelines...",
            "author": "Threat Research",
            "date": datetime(2026, 9, 16),
            "tags": ["apt", "supply chain", "malware"],
        },
        {
            "title": "Lazarus Group Shifts Focus To Crypto Exchange Wallets",
            "category": "Intelligence",
            "subcategory": "APT",
            "summary": "North Korean operators are targeting DeFi platforms and hot wallets with custom macOS malware.",
            "content": "Lazarus Group has been observed deploying a new macOS implant targeting cryptocurrency exchanges and their developers...",
            "author": "Analyst Desk",
            "date": datetime(2026, 9, 14),
            "tags": ["apt", "malware", "crypto"],
        },

        # ---------- Zero-Day / Vulnerability ----------
        {
            "title": "New Zero-Day In Popular VPN Appliance Under Attack",
            "category": "News",
            "subcategory": "Vulnerabilities",
            "summary": "Vendor rushes out emergency patch after reports of active exploitation in the wild.",
            "content": "A critical authentication bypass vulnerability has been discovered in a widely deployed VPN appliance...",
            "author": "News Desk",
            "date": datetime(2026, 9, 15),
            "tags": ["zero-day", "vpn", "vulnerability"],
        },
        {
            "title": "Critical Zero-Day In Enterprise Email Gateway Exploited",
            "category": "News",
            "subcategory": "Vulnerabilities",
            "summary": "Attackers are chaining two flaws to achieve pre-auth RCE on internet-facing mail servers.",
            "content": "Researchers have observed active exploitation of a critical zero-day in a widely deployed enterprise email gateway...",
            "author": "News Desk",
            "date": datetime(2026, 9, 13),
            "tags": ["zero-day", "cve", "vulnerability"],
        },

        # ---------- Phishing ----------
        {
            "title": "Phishing Campaign Abuses Cloudflare Pages To Host Fake Logins",
            "category": "News",
            "subcategory": "Phishing",
            "summary": "Attackers are hosting pixel-perfect credential harvesting pages on trusted CDN domains to bypass email filters.",
            "content": "A large-scale phishing campaign is abusing Cloudflare Pages to host fake Microsoft 365 and Google login pages...",
            "author": "News Desk",
            "date": datetime(2026, 9, 12),
            "tags": ["phishing", "email", "credential"],
        },
        {
            "title": "QR-Code Phishing ('Quishing') Rises 300% In Enterprise Inboxes",
            "category": "Intelligence",
            "subcategory": "Phishing",
            "summary": "Attackers embed QR codes in PDFs to bypass URL scanning and trick users into scanning with personal phones.",
            "content": "Quishing attacks — phishing via QR codes — have surged dramatically as attackers look for ways around traditional email security controls...",
            "author": "Threat Research",
            "date": datetime(2026, 9, 11),
            "tags": ["phishing", "email", "quishing"],
        },

        # ---------- Malware ----------
        {
            "title": "New Info-Stealer Harvests Browser Sessions And Crypto Wallets",
            "category": "Intelligence",
            "subcategory": "Malware",
            "summary": "The malware, tracked as 'Vidar-X', is distributed via fake software cracks and malicious ads.",
            "content": "A new information-stealing malware family has been observed harvesting browser session tokens, saved passwords and cryptocurrency wallet files...",
            "author": "Threat Research",
            "date": datetime(2026, 9, 9),
            "tags": ["malware", "credential", "crypto"],
        },
        {
            "title": "Linux Botnet Expands To Target IoT Devices Worldwide",
            "category": "Intelligence",
            "subcategory": "Botnet",
            "summary": "A new variant of Mirai is exploiting default credentials on routers and smart cameras.",
            "content": "Researchers have tracked a new Linux botnet variant building a large DDoS-capable network of compromised IoT devices...",
            "author": "Analyst Desk",
            "date": datetime(2026, 9, 8),
            "tags": ["malware", "botnet", "iot"],
        },

        # ---------- Jobs ----------
        {
            "title": "Cyber Security Jobs Grow 12% Year Over Year",
            "category": "Jobs",
            "subcategory": "Market",
            "summary": "Demand for threat analysts, detection engineers and CTI specialists continues to outpace supply.",
            "content": "The cybersecurity job market continues its upward trajectory...",
            "author": "Careers Desk",
            "date": datetime(2026, 9, 10),
            "tags": ["jobs", "careers"],
        },
        {
            "title": "CTI Analyst Named Among Top 10 Fastest-Growing Tech Roles",
            "category": "Jobs",
            "subcategory": "Careers",
            "summary": "Cyber Threat Intelligence roles see 40% salary growth over three years as demand outpaces supply.",
            "content": "A new industry report ranks Cyber Threat Intelligence Analyst among the top ten fastest-growing tech roles globally...",
            "author": "Careers Desk",
            "date": datetime(2026, 9, 7),
            "tags": ["jobs", "careers", "intelligence"],
        },
    ]

    # Auto-assign relevant images based on title/keywords
    for a in demo:
        a["image"] = pick_image(
            a["title"],
            a["category"],
            a.get("tags", [])
        )

    articles.insert_many(demo)


def seed_ads():
    """Insert a couple of demo ads on first run."""
    if ads.count_documents({}) > 0:
        return

    ads.insert_many([
        {
            "title": "CyberJobs",
            "subtitle": "CyberSecurityJobs.com",
            "body": "",
            "link": "https://example.com",
            "type": "sponsor",
            "position": "sidebar",
            "active": True,
            "created_at": datetime.utcnow(),
            "created_by": "system",
        },
        {
            "title": "Clayden Law",
            "subtitle": "Cybersecurity legal specialists",
            "body": "Advise global businesses on IT, data privacy & cyber law.",
            "link": "https://example.com",
            "type": "directory",
            "position": "sidebar",
            "active": True,
            "created_at": datetime.utcnow(),
            "created_by": "system",
        },
    ])


# ---------- Public routes ----------
@app.route("/")
def index():
    seed_articles()
    seed_ads()

    q = request.args.get("q", "").strip()
    category = request.args.get("cat", "").strip()
    tag = request.args.get("tag", "").strip()

    query = {}

    if category:
        query["category"] = category

    if tag:
        query["tags"] = tag

    if q:
        query["$text"] = {"$search": q}

    cursor = articles.find(query).sort("date", -1)

    all_articles = list(cursor)

    featured = all_articles[0] if all_articles else None
    rest = all_articles[1:]

    categories_list = articles.distinct("category")

    return render_template(
        "index.html",
        featured=featured,
        articles=rest,
        categories=categories_list,
        active_category=category,
        active_tag=tag,
        query=q,
        user=session.get("user"),
        me=current_user(),
        sponsor_ads=get_active_ads(
            position="sidebar",
            ad_type="sponsor"
        ),
        directory_ads=get_active_ads(
            position="sidebar",
            ad_type="directory"
        ),
    )


@app.route("/article/<id>")
def article(id):
    doc = articles.find_one({
        "_id": ObjectId(id)
    })

    if not doc:
        flash("Article not found.", "danger")
        return redirect(url_for("index"))

    related = list(
        articles.find({
            "_id": {
                "$ne": doc["_id"]
            }
        }).limit(4)
    )

    return render_template(
        "article.html",
        article=doc,
        related=related,
        user=session.get("user"),
        me=current_user(),
        sponsor_ads=get_active_ads(
            position="sidebar",
            ad_type="sponsor"
        ),
        directory_ads=get_active_ads(
            position="sidebar",
            ad_type="directory"
        ),
    )


# ---------- Auth ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = users.find_one({
            "username": username
        })

        if user and check_password_hash(
            user["password"],
            password
        ):
            session["user"] = username

            # NEW: store role in session
            session["role"] = user.get("role", "user")

            flash("Welcome back!", "success")

            # NEW: Admin goes directly to admin dashboard
            if user.get("role") == "admin":
                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(
                url_for("index")
            )

        flash("Invalid credentials.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash(
                "Username and password required.",
                "danger"
            )

        elif users.find_one({
            "username": username
        }):
            flash(
                "Username already taken.",
                "danger"
            )

        else:
            # First user becomes admin
            role = (
                "admin"
                if users.count_documents({}) == 0
                else "user"
            )

            users.insert_one({
                "username": username,
                "password": generate_password_hash(password),
                "role": role,
                "created_at": datetime.utcnow(),
            })

            flash(
                f"Account created ({role}). Please log in.",
                "success"
            )

            return redirect(
                url_for("login")
            )

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)

    flash("Logged out.", "info")

    return redirect(
        url_for("index")
    )


# ---------- Content ----------
@app.route("/indicators")
@login_required
def indicators_list():
    q = request.args.get("q", "").strip()

    query = (
        {"$text": {"$search": q}}
        if q
        else {}
    )

    return render_template(
        "indicators.html",
        indicators=list(
            indicators.find(query).sort(
                "created_at",
                -1
            )
        ),
        query=q,
        user=session.get("user"),
        me=current_user(),
    )


# CHANGED: Admin only
@app.route("/add", methods=["GET", "POST"])
@admin_required
def add():
    if request.method == "POST":
        kind = request.form.get(
            "kind",
            "indicator"
        )

        if kind == "article":
            title = request.form[
                "title"
            ].strip()

            category = request.form.get(
                "category",
                "News"
            )

            tags = [
                t.strip()
                for t in request.form.get(
                    "tags",
                    ""
                ).split(",")
                if t.strip()
            ]

            articles.insert_one({
                "title": title,
                "category": category,
                "subcategory": request.form.get(
                    "subcategory",
                    ""
                ),
                "summary": request.form.get(
                    "summary",
                    ""
                ).strip(),
                "content": request.form.get(
                    "content",
                    ""
                ).strip(),
                "author": session.get(
                    "user"
                ),
                "image": pick_image(
                    title,
                    category,
                    tags,
                    custom=request.form.get(
                        "image",
                        ""
                    ),
                ),
                "date": datetime.utcnow(),
                "tags": tags,
            })

            flash(
                "Article published.",
                "success"
            )

            return redirect(
                url_for("index")
            )

        else:
            indicators.insert_one({
                "type": request.form["type"],
                "value": request.form[
                    "value"
                ].strip(),
                "description": request.form.get(
                    "description",
                    ""
                ).strip(),
                "tags": [
                    t.strip()
                    for t in request.form.get(
                        "tags",
                        ""
                    ).split(",")
                    if t.strip()
                ],
                "severity": request.form.get(
                    "severity",
                    "medium"
                ),
                "tlp": request.form.get(
                    "tlp",
                    "WHITE"
                ),
                "created_at": datetime.utcnow(),
                "created_by": session.get(
                    "user"
                ),
            })

            flash(
                "Indicator added.",
                "success"
            )

            return redirect(
                url_for("add")
            )

    return render_template(
        "add.html",
        user=session.get("user"),
        me=current_user()
    )


@app.route("/delete/<id>")
@login_required
def delete(id):
    indicators.delete_one({
        "_id": ObjectId(id)
    })

    flash(
        "Indicator deleted.",
        "info"
    )

    return redirect(
        url_for("indicators_list")
    )


# ---------- ADMIN DASHBOARD ----------
# NEW
@app.route("/admin")
@admin_required
def admin_dashboard():

    return render_template(
        "admin_dashboard.html",

        user=session.get("user"),

        me=current_user(),

        categories=list(
            categories.find().sort(
                "name",
                1
            )
        ),

        article_count=articles.count_documents({}),

        indicator_count=indicators.count_documents({}),

        user_count=users.count_documents({}),

        ad_count=ads.count_documents({}),
    )


# ---------- CATEGORIES (admin only) ----------
# NEW
@app.route("/admin/categories")
@admin_required
def categories_manager():

    all_categories = list(
        categories.find().sort(
            "name",
            1
        )
    )

    return render_template(
        "categories.html",

        categories=all_categories,

        user=session.get("user"),

        me=current_user()
    )


# NEW
@app.route(
    "/admin/categories/new",
    methods=["POST"]
)
@admin_required
def category_new():

    name = request.form.get(
        "name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    if not name:
        flash(
            "Category name is required.",
            "danger"
        )

        return redirect(
            url_for(
                "categories_manager"
            )
        )

    if categories.find_one({
        "name": name
    }):
        flash(
            "Category already exists.",
            "warning"
        )

        return redirect(
            url_for(
                "categories_manager"
            )
        )

    categories.insert_one({
        "name": name,
        "description": description,
        "created_at": datetime.utcnow(),
        "created_by": session.get(
            "user"
        )
    })

    flash(
        "Category created successfully.",
        "success"
    )

    return redirect(
        url_for(
            "categories_manager"
        )
    )


# NEW
@app.route(
    "/admin/categories/delete/<id>"
)
@admin_required
def category_delete(id):

    try:
        category = categories.find_one({
            "_id": ObjectId(id)
        })

        if not category:
            flash(
                "Category not found.",
                "warning"
            )

            return redirect(
                url_for(
                    "categories_manager"
                )
            )

        categories.delete_one({
            "_id": ObjectId(id)
        })

        flash(
            "Category deleted.",
            "info"
        )

    except Exception:
        flash(
            "Invalid category ID.",
            "danger"
        )

    return redirect(
        url_for(
            "categories_manager"
        )
    )


# ---------- ADS (admin only) ----------
@app.route("/ads")
@admin_required
def ads_manager():
    all_ads = list(
        ads.find().sort(
            "created_at",
            -1
        )
    )

    return render_template(
        "ads.html",
        ads=all_ads,
        user=session.get("user"),
        me=current_user()
    )


@app.route("/ads/new", methods=["POST"])
@admin_required
def ads_new():
    ads.insert_one({
        "title": request.form[
            "title"
        ].strip(),

        "subtitle": request.form.get(
            "subtitle",
            ""
        ).strip(),

        "body": request.form.get(
            "body",
            ""
        ).strip(),

        "link": request.form.get(
            "link",
            ""
        ).strip(),

        "image": request.form.get(
            "image",
            ""
        ).strip(),

        "type": request.form.get(
            "type",
            "sponsor"
        ),

        "position": request.form.get(
            "position",
            "sidebar"
        ),

        "active": True,

        "created_at": datetime.utcnow(),

        "created_by": session.get(
            "user"
        ),
    })

    flash(
        "Ad created.",
        "success"
    )

    return redirect(
        url_for("ads_manager")
    )


@app.route("/ads/toggle/<id>")
@admin_required
def ads_toggle(id):

    ad = ads.find_one({
        "_id": ObjectId(id)
    })

    if ad:
        ads.update_one(
            {
                "_id": ad["_id"]
            },
            {
                "$set": {
                    "active": not ad.get(
                        "active",
                        True
                    )
                }
            }
        )

    return redirect(
        url_for("ads_manager")
    )


@app.route("/ads/delete/<id>")
@admin_required
def ads_delete(id):

    ads.delete_one({
        "_id": ObjectId(id)
    })

    flash(
        "Ad deleted.",
        "info"
    )

    return redirect(
        url_for("ads_manager")
    )


# ---------- API ----------
@app.route("/api/indicators")
def api_indicators():

    docs = list(
        indicators.find().sort(
            "created_at",
            -1
        )
    )

    for d in docs:
        d["_id"] = str(
            d["_id"]
        )

        d["created_at"] = (
            d["created_at"].isoformat()
        )

    return jsonify(docs)
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/editorial-policy")
def editorial_policy():
    return render_template("editorial_policy.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")



if __name__ == "__main__":
    app.run(debug=True)
"""
每日新闻摘要 — NewsAPI 拉取脚本
用法: NEWSAPI_KEY=xxx python fetch_news.py
输出: data/news.json

策略：拉取多国头条新闻（us + 其他），本地按关键词分类到5个栏目，去重。
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("NEWSAPI_KEY", "")
TOP_URL = "https://newsapi.org/v2/top-headlines"

# Countries with good free-tier coverage
COUNTRIES = ["us", "gb", "sg", "jp", "hk"]

# Keywords for categorization
CATEGORY_RULES = {
    "politics": {
        "keywords": [
            "president", "trump", "congress", "senate", "white house", "election",
            "democrat", "republican", "biden", "parliament", "vote", "party",
            "policy", "law", "government", "supreme court", "political",
            "politics", "governor", "minister", "campaign",
        ],
    },
    "economy": {
        "keywords": [
            "stock", "market", "wall street", "economy", "trade", "tariff",
            "gdp", "inflation", "fed", "federal reserve", "rate", "bank",
            "crypto", "bitcoin", "finance", "invest", "dollar", "oil", "gold",
            "recession", "job", "business", "earnings", "revenue", "debt",
        ],
    },
    "military": {
        "keywords": [
            "military", "war", "missile", "navy", "army", "air force",
            "defense", "pentagon", "nato", "drone", "weapon", "troop",
            "naval", "fighter", "attack", "strike", "nuclear", "security",
            "combat", "invasion", "conflict", "gaza", "ukraine", "israel",
        ],
    },
    "tech": {
        "keywords": [
            "ai", "apple", "google", "microsoft", "meta", "amazon", "tesla",
            "spacex", "nvidia", "intel", "chip", "tech", "startup", "robot",
            "semiconductor", "data", "software", "app", "iphone", "android",
            "satellite", "5g", "quantum", "battery", "ev", "electric vehicle",
            "openai", "chatgpt", "silicon valley", "cyber",
        ],
    },
    "world": {
        "keywords": [
            "china", "xi", "beijing", "russia", "putin", "uk", "british",
            "europe", "eu", "france", "germany", "japan", "korea", "india",
            "iran", "middle east", "africa", "australia", "canada", "mexico",
            "united nations", "un", "g7", "g20", "summit", "diplomat",
            "foreign", "embassy", "sanction", "refugee", "climate",
        ],
    },
}

# Domains to always exclude
SPAM_DOMAINS = {
    "pypi.org", "financialpost.com", "xataka.com.mx", "xataka.com",
    "prnewswire.com", "globenewswire.com", "businesswire.com",
    "accesswire.com", "einpresswire.com",
}

CATEGORY_NAMES_ZH = {
    "politics": "政治", "economy": "经济", "military": "军事",
    "tech": "科技", "world": "国际",
}


def fetch_country_headlines(country_code):
    """Fetch top headlines for a given country."""
    params = {"country": country_code, "pageSize": 80, "apiKey": API_KEY}
    url = f"{TOP_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "ok":
        print(f"    {country_code}: {data.get('message', '?')}", file=sys.stderr)
        return []
    return data.get("articles", [])


def classify_article(article):
    """Return (category, score) tuple for best match."""
    text = (
        (article.get("title") or "") + " " +
        (article.get("description") or "")
    ).lower()
    best_cat, best_score = None, 0
    for cat, rules in CATEGORY_RULES.items():
        score = sum(1 for kw in rules["keywords"] if kw in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    return best_cat, best_score


def main():
    if not API_KEY:
        print("ERROR: NEWSAPI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    # Fetch from multiple countries
    all_articles = []
    seen_titles = set()

    for cc in COUNTRIES:
        print(f"Fetching country={cc}...")
        try:
            articles = fetch_country_headlines(cc)
            print(f"  Got {len(articles)} articles")
            for a in articles:
                key = a.get("title", "")[:80].lower()
                domain = a.get("url", "").split("/")[2] if a.get("url") else ""
                if key not in seen_titles and domain not in SPAM_DOMAINS:
                    seen_titles.add(key)
                    all_articles.append(a)
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)

    print(f"\nTotal unique articles: {len(all_articles)}")

    # Classify into categories
    categories = {k: [] for k in CATEGORY_RULES}
    unclassified = []

    for a in all_articles:
        cat, score = classify_article(a)
        if cat and score > 0 and len(categories[cat]) < 5:
            categories[cat].append(a)
        else:
            unclassified.append(a)

    # Fill empty categories from unclassified pool
    for cat in categories:
        while len(categories[cat]) < 3 and unclassified:
            categories[cat].append(unclassified.pop(0))

    result = {"updatedAt": now.strftime("%Y-%m-%d %H:%M"), "categories": categories}

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {out_path}")
    for cat in CATEGORY_RULES:
        arts = categories[cat]
        print(f"  {CATEGORY_NAMES_ZH[cat]}: {len(arts)} articles")
        for a in arts:
            print(f"    [{a.get('source',{}).get('name','?')}] {a.get('title','?')[:70]}")


if __name__ == "__main__":
    main()

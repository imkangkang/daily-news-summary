"""
每日新闻摘要 — NewsAPI 拉取脚本
用法: NEWSAPI_KEY=xxx python fetch_news.py
输出: data/news.json
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("NEWSAPI_KEY", "")
HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"

# Map our categories to API calls
# top-headlines supports: country + category (business/technology/general/entertainment/health/science/sports)
# For other keywords, use 'everything' endpoint with date range
CATEGORIES_CONFIG = {
    "politics":  {"endpoint": "everything",  "q": "政治 OR 政策 OR 两会 OR 国务院 OR 习近平", "language": "zh", "sortBy": "publishedAt", "pageSize": 5},
    "economy":   {"endpoint": "top-headlines", "country": "cn", "category": "business", "pageSize": 5},
    "military":  {"endpoint": "everything",  "q": "军事 OR 国防 OR 军队 OR 解放军", "language": "zh", "sortBy": "publishedAt", "pageSize": 5},
    "tech":      {"endpoint": "top-headlines", "country": "cn", "category": "technology", "pageSize": 5},
    "world":     {"endpoint": "everything",  "q": "国际 OR 外交 OR 联合国 OR 中美 OR G20 OR G7", "language": "zh", "sortBy": "publishedAt", "pageSize": 5},
}


def fetch_headlines(params):
    """Call top-headlines endpoint."""
    qs = urllib.parse.urlencode({**params, "apiKey": API_KEY})
    url = f"{HEADLINES_URL}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "ok":
        print(f"    API error: {data.get('message', 'unknown')}", file=sys.stderr)
        return []
    return data.get("articles", [])


def fetch_everything(params):
    """Call everything endpoint with date range (yesterday to today)."""
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=2)  # free tier needs 24h+ old articles
    from_date = yesterday.strftime("%Y-%m-%d")

    qs = urllib.parse.urlencode({**params, "apiKey": API_KEY, "from": from_date})
    url = f"{EVERYTHING_URL}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "ok":
        print(f"    API error: {data.get('message', 'unknown')}", file=sys.stderr)
        return []
    return data.get("articles", [])


def fetch_category(name, config):
    """Fetch articles for a single category."""
    ep = config.get("endpoint", "top-headlines")
    params = {k: v for k, v in config.items() if k != "endpoint"}

    if ep == "everything":
        return fetch_everything(params)
    else:
        return fetch_headlines(params)


def main():
    if not API_KEY:
        print("ERROR: NEWSAPI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    result = {
        "updatedAt": now.strftime("%Y-%m-%d %H:%M"),
        "categories": {}
    }

    for key, config in CATEGORIES_CONFIG.items():
        print(f"Fetching: {key} ({config.get('endpoint', 'top-headlines')})...")
        try:
            articles = fetch_category(key, config)
            result["categories"][key] = articles
            print(f"  Got {len(articles)} articles")
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)
            result["categories"][key] = []

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "news.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path} ({len(result['categories'])} categories)")


if __name__ == "__main__":
    main()

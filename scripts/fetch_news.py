"""
每日新闻摘要 — NewsAPI 拉取脚本
用法: NEWSAPI_KEY=xxx python fetch_news.py
输出: data/news.json
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("NEWSAPI_KEY", "")
BASE_URL = "https://newsapi.org/v2/top-headlines"

CATEGORIES = {
    "politics":  {"q": "政治", "language": "zh", "country": "cn", "pageSize": 5},
    "economy":   {"q": "经济 OR 金融", "language": "zh", "country": "cn", "pageSize": 5},
    "military":  {"q": "军事 OR 国防", "language": "zh", "country": "cn", "pageSize": 5},
    "tech":      {"q": "科技 OR 互联网 OR AI", "language": "zh", "country": "cn", "pageSize": 5},
    "world":     {"q": "国际 OR 外交", "language": "zh", "country": "cn", "pageSize": 5},
}

def fetch_category(name, params):
    qs = urllib.parse.urlencode({**params, "apiKey": API_KEY})
    url = f"{BASE_URL}?{qs}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            print(f"  [{name}] API error: {data.get('message', 'unknown')}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"  [{name}] Request failed: {e}", file=sys.stderr)
        return []

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

    for key, params in CATEGORIES.items():
        print(f"Fetching: {key}...")
        articles = fetch_category(key, params)
        result["categories"][key] = articles
        print(f"  Got {len(articles)} articles")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "news.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path} ({len(result['categories'])} categories)")

if __name__ == "__main__":
    main()

"""
每日新闻摘要 — NewsAPI 拉取脚本
用法: NEWSAPI_KEY=xxx python fetch_news.py
输出: data/news.json
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("NEWSAPI_KEY", "")
EVERYTHING_URL = "https://newsapi.org/v2/everything"

# Keyword queries per category (Chinese-language sources, sorted by publish date)
CATEGORIES = {
    "politics":  "政治 OR 政策 OR 习近平 OR 国务院 OR 人大 OR 外交部",
    "economy":   "经济 OR 股市 OR GDP OR 央行 OR 贸易 OR 房地产",
    "military":  "军事 OR 国防部 OR 军演 OR 导弹 OR 航母 OR 解放军",
    "tech":      "科技 OR AI OR 芯片 OR 5G OR 互联网 OR 量子",
    "world":     "国际 OR 外交 OR 中美 OR 欧盟 OR 北约 OR G20",
}


def fetch_articles(keyword_query):
    """Fetch articles from NewsAPI everything endpoint."""
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=2)
    from_date = two_days_ago.strftime("%Y-%m-%d")

    params = {
        "q": keyword_query,
        "language": "zh",
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": API_KEY,
    }
    url = f"{EVERYTHING_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "ok":
        print(f"    API error: {data.get('message', 'unknown')}", file=sys.stderr)
        return []
    return data.get("articles", [])


def main():
    if not API_KEY:
        print("ERROR: NEWSAPI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    categories_data = {}
    for key, query in CATEGORIES.items():
        print(f"Fetching: {key}...")
        try:
            articles = fetch_articles(query)
            categories_data[key] = articles
            print(f"  Got {len(articles)} articles")
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)
            categories_data[key] = []

    result = {"updatedAt": now.strftime("%Y-%m-%d %H:%M"), "categories": categories_data}

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path} ({len(categories_data)} categories)")

    # Show sample titles
    for key in categories_data:
        arts = categories_data[key]
        if arts:
            print(f"  [{key}] {arts[0].get('title', '?')[:70]}")


if __name__ == "__main__":
    main()

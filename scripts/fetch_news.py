"""
每日新闻摘要 — 天行数据(TianAPI) 拉取脚本
用法: TIANAPI_KEY=xxx python fetch_news.py
输出: data/news.json
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("TIANAPI_KEY", "")
BASE_URL = "https://apis.tianapi.com/generalnews/index"

# Categories with Chinese keyword search
CATEGORIES = {
    "politics":  "政治",
    "economy":   "经济",
    "military":  "军事",
    "tech":      "科技",
    "world":     "国际",
}

CATEGORY_NAMES = {
    "politics": "政治", "economy": "经济", "military": "军事",
    "tech": "科技", "world": "国际",
}


def fetch_category(keyword):
    """Fetch news from TianAPI generalnews endpoint with keyword search."""
    params = {
        "key": API_KEY,
        "num": 6,
        "word": keyword,
        "form": 1,
        "page": 0,
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    if data.get("code") != 200:
        raise RuntimeError(f"API error {data.get('code')}: {data.get('msg', 'unknown')}")

    # Normalize to our standard article format
    articles = []
    for item in data.get("result", {}).get("list", []):
        articles.append({
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "url": item.get("url", ""),
            "source": {"name": item.get("source", "未知来源")},
            "publishedAt": item.get("ctime", ""),
            "image": item.get("picUrl", ""),
        })
    return articles


def main():
    if not API_KEY:
        print("ERROR: TIANAPI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    categories = {}
    total = 0

    for key, keyword in CATEGORIES.items():
        name = CATEGORY_NAMES[key]
        print(f"Fetching: {name} ({key})...")
        try:
            articles = fetch_category(keyword)
            categories[key] = articles[:5]
            total += len(categories[key])
            print(f"  Got {len(articles)} articles, kept {len(categories[key])}")
            if articles:
                print(f"  Sample: {articles[0].get('title', '?')[:70]}")
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)
            categories[key] = []

    result = {"updatedAt": now.strftime("%Y-%m-%d %H:%M"), "categories": categories}

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {out_path}")
    print(f"Total: {total} articles across {len(categories)} categories")
    for key in CATEGORIES:
        print(f"  {CATEGORY_NAMES[key]}: {len(categories[key])} articles")


if __name__ == "__main__":
    main()

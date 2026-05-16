"""
每日新闻摘要 — NewsAPI 拉取脚本
用法: NEWSAPI_KEY=xxx python fetch_news.py
输出: data/news.json

使用 everything 端点拉取全球新闻，本地按关键词分类到5个栏目。
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("NEWSAPI_KEY", "")
EVERYTHING_URL = "https://newsapi.org/v2/everything"

# Broad queries per category (English for better free-tier coverage)
CATEGORY_QUERIES = {
    "politics":  "politics OR government OR election OR president OR parliament OR policy",
    "economy":   "economy OR stock OR market OR GDP OR inflation OR trade OR finance",
    "military":  "military OR defense OR war OR missile OR navy OR army OR NATO",
    "tech":      "technology OR AI OR chip OR semiconductor OR robotics OR quantum",
    "world":     "international OR diplomacy OR UN OR NATO OR G20 OR summit OR foreign",
}

# Chinese display names
CATEGORY_NAMES_ZH = {
    "politics": "政治", "economy": "经济", "military": "军事",
    "tech": "科技", "world": "国际",
}

# Keywords for local re-categorization refinement (check article content)
CHINESE_HINTS = {
    "politics": ["政治", "政府", "选举", "总统", "国会", "政策"],
    "economy":  ["经济", "金融", "市场", "股票", "贸易", "投资"],
    "military": ["军事", "国防", "武器", "军队", "导弹", "战争"],
    "tech":     ["科技", "AI", "芯片", "苹果", "谷歌", "微软", "特斯拉"],
    "world":    ["国际", "外交", "联合", "欧", "亚洲", "非洲", "中东"],
}


def fetch_articles(query):
    """Fetch articles from NewsAPI everything endpoint."""
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=2)
    from_date = two_days_ago.strftime("%Y-%m-%d")

    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": 8,
        "apiKey": API_KEY,
    }
    url = f"{EVERYTHING_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "ok":
        raise RuntimeError(data.get("message", "unknown error"))
    return data.get("articles", [])


def main():
    if not API_KEY:
        print("ERROR: NEWSAPI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    categories = {}
    total = 0

    for key, query in CATEGORY_QUERIES.items():
        print(f"Fetching: {CATEGORY_NAMES_ZH[key]} ({key})...")
        try:
            articles = fetch_articles(query)
            # Take only 5 per category
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
    for key in CATEGORY_QUERIES:
        print(f"  {CATEGORY_NAMES_ZH[key]}: {len(categories[key])} articles")


if __name__ == "__main__":
    main()

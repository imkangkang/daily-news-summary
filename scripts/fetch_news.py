"""
每日新闻摘要 — NewsAPI 拉取脚本
用法: NEWSAPI_KEY=xxx python fetch_news.py
输出: data/news.json

策略：一次性拉取所有中国头条（country=cn），在本地按关键词分类到5个栏目。
如果 country=cn 返回空，fallback 到 english 源用 everything endpoint。
"""
import json, os, sys, re, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("NEWSAPI_KEY", "")
TOP_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"

# Keywords for local categorization (lowercase matching)
CATEGORY_KEYWORDS = {
    "politics":  ["政治", "习近平", "国务院", "人大", "外交部", "政策", "选举", "政府", "主席",
                  "国会", "白宫", "总统", "民主", "共和党", "议会", "立法"],
    "economy":   ["经济", "股市", "GDP", "央行", "贸易", "房地产", "金融", "通胀", "加息",
                  "人民币", "A股", "投资", "关税", "消费", "市场", "企业"],
    "military":  ["军事", "国防", "军演", "导弹", "航母", "解放军", "军队", "武器",
                  "战区", "海军", "空军", "陆军", "北约", "核", "作战"],
    "tech":      ["科技", "AI", "人工智能", "芯片", "5G", "互联网", "量子", "半导体",
                  "华为", "苹果", "特斯拉", "新能源", "卫星", "机器人", "自动驾驶"],
    "world":     ["国际", "外交", "中美", "欧盟", "北约", "G20", "G7", "联合", "国", "制裁",
                  "俄乌", "中东", "日韩", "英国", "法国", "德国", "日本", "韩国", "印度"],
}


def fetch_top_headlines():
    """Fetch Chinese top headlines."""
    params = {"country": "cn", "pageSize": 100, "apiKey": API_KEY}
    url = f"{TOP_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "ok":
        raise RuntimeError(f"API error: {data.get('message', 'unknown')}")
    return data.get("articles", [])


def fetch_everything_fallback():
    """Fallback: fetch from everything endpoint without language filter."""
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=2)
    from_date = two_days_ago.strftime("%Y-%m-%d")

    all_articles = []
    queries = ["politics", "economy", "military", "technology", "world"]
    for q in queries:
        params = {
            "q": q, "from": from_date, "sortBy": "publishedAt",
            "pageSize": 20, "apiKey": API_KEY,
        }
        url = f"{EVERYTHING_URL}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DailyNewsBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") == "ok":
                all_articles.extend(data.get("articles", []))
        except Exception:
            pass
    return all_articles


def categorize(articles):
    """Sort articles into categories by keyword matching."""
    result = {k: [] for k in CATEGORY_KEYWORDS}
    for a in articles:
        text = (a.get("title", "") + " " + a.get("description", "")).lower()
        best_cat, best_score = None, 0
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > best_score:
                best_score = score
                best_cat = cat
        if best_cat and len(result[best_cat]) < 6:
            result[best_cat].append(a)
    return result


def main():
    if not API_KEY:
        print("ERROR: NEWSAPI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Try Chinese headlines first
    print("Fetching Chinese top headlines...")
    try:
        articles = fetch_top_headlines()
        print(f"  Got {len(articles)} articles from top-headlines")
    except Exception as e:
        print(f"  Failed: {e}")
        print("  Falling back to everything endpoint...")
        articles = fetch_everything_fallback()
        print(f"  Got {len(articles)} articles from fallback")

    if not articles:
        print("ERROR: No articles fetched", file=sys.stderr)
        sys.exit(1)

    # Categorize
    categories = categorize(articles)

    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    # Ensure each category has at least something
    for key in categories:
        if not categories[key] and articles:
            # Assign uncategorized articles to empty categories
            for a in articles:
                if a not in sum(categories.values(), []):
                    categories[key].append(a)
                    if len(categories[key]) >= 3:
                        break

    result = {"updatedAt": now.strftime("%Y-%m-%d %H:%M"), "categories": categories}

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {out_path}")
    for key in categories:
        arts = categories[key]
        count = len(arts)
        sample = arts[0].get('title', '?')[:60] if arts else '(empty)'
        print(f"  [{key}] {count} articles | {sample}")


if __name__ == "__main__":
    main()

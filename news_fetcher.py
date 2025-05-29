import feedparser

def fetch_latest_news(rss_feeds):
    news_items = []
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary,
            })
    return news_items

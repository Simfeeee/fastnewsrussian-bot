import os
import logging
import feedparser
import telegram
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import pytz

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")

bot = telegram.Bot(token=TOKEN)
logging.basicConfig(level=logging.INFO)

FEEDS = [
    "https://lenta.ru/rss",
    "https://www.kommersant.ru/RSS/news.xml",
    "https://www.rbc.ru/static/rss/news.rss"
]

posted_links = set()

def extract_image(entry):
    media_content = entry.get('media_content', [])
    if media_content and 'url' in media_content[0]:
        return media_content[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if link.type and link.type.startswith("image/"):
                return link.href
    return None

def fetch_news():
    logging.info("Fetching news...")
    news_items = []
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if entry.link not in posted_links:
                posted_links.add(entry.link)
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if hasattr(entry, "summary") else "",
                    "image": extract_image(entry),
                    "published": entry.published if hasattr(entry, "published") else ""
                })
    return news_items[:3]

def create_caption(item):
    title = item['title'].strip()
    summary = item['summary'].strip()
    if len(summary) > 300:
        summary = summary[:297] + "..."
    caption = f"🗞️ {title}\n\n🤔 {summary}\n\n✉ Fast News Russia"
    return caption

def post_digest():
    logging.info("Posting stylized news...")
    news = fetch_news()
    if not news:
        logging.info("No new news found.")
        return

    for item in news:
        caption = create_caption(item)
        try:
            if item['image']:
                bot.send_photo(chat_id=CHANNEL, photo=item['image'], caption=caption, parse_mode=telegram.ParseMode.HTML)
            else:
                bot.send_message(chat_id=CHANNEL, text=caption, parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            logging.error(f"Error posting item: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(post_digest, "interval", hours=1)
    post_digest()
    scheduler.start()
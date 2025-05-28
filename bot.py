
import os
import time
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
                    "published": entry.published if hasattr(entry, "published") else ""
                })
    return news_items[:5]  # ÑÐ¾Ð»ÑÐºÐ¾ 5 ÑÐ²ÐµÐ¶Ð¸Ñ Ð½Ð¾Ð²Ð¾ÑÑÐµÐ¹

def post_digest():
    logging.info("Posting news digest...")
    news = fetch_news()
    if not news:
        logging.info("No new news found.")
        return

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    message = f"ðï¸ <b>ÐÐ°Ð¹Ð´Ð¶ÐµÑÑ Ð½Ð¾Ð²Ð¾ÑÑÐµÐ¹ Ð Ð¾ÑÑÐ¸Ð¸ â {now}</b>\n\n"
    for item in news:
        title = item['title'].strip()
        summary = item['summary'].strip()
        if len(summary) > 350:
            summary = summary[:347] + "..."
        message += f"ð <b>{title}</b>\n<i>{summary}</i>\n\n"

    bot.send_message(chat_id=CHANNEL, text=message, parse_mode=telegram.ParseMode.HTML)

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(post_digest, "interval", hours=1)
    post_digest()  # ÐÐµÑÐ²ÑÐ¹ Ð·Ð°Ð¿ÑÑÐº ÑÑÐ°Ð·Ñ
    scheduler.start()

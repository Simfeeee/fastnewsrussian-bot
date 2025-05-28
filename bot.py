
import os
import time
import logging
import feedparser
import telegram
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

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
    return news_items[:5]  # только 5 свежих новостей

def post_digest():
    logging.info("Posting news digest...")
    news = fetch_news()
    if not news:
        logging.info("No new news found.")
        return

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    message = f"🗞️ <b>Дайджест новостей России — {now}</b>\n\n"
    for item in news:
        message += f"• <b>{item['title']}</b>\n{item['link']}\n\n"

    bot.send_message(chat_id=CHANNEL, text=message, parse_mode=telegram.ParseMode.HTML)

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(post_digest, "interval", hours=1)
    post_digest()  # Первый запуск сразу
    scheduler.start()
    Fix pytz import and timezone config

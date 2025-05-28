import os
import json
import html
import time
import logging
import threading
import feedparser
import openai
import pytz
from datetime import datetime
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from dotenv import load_dotenv
from smartgen import generate_smart_reaction
from generate_image import generate_image_for_news

# === Настройки окружения ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# === Логгирование ===
import sys
sys.stdout.reconfigure(line_buffering=True)
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# === Flask app (для Render) ===
app = Flask(__name__)
@app.route("/")
def home():
    return "FastNews AI is alive"

# === Telegram Bot ===
bot = Bot(token=TELEGRAM_TOKEN)
posted_titles = set()

# === RSS источники ===
FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.kommersant.ru/RSS/news.xml",
    "https://ria.ru/export/rss2/world/index.xml",
    "https://www.rbc.ru/static/rss/news.rus.rbc.ru/news.ru/mainnews.rss",
    "http://rss.cnn.com/rss/edition.rss",
    "http://feeds.reuters.com/reuters/topNews"
]

# === Перевод ===
def translate_to_russian(text):
    try:
        prompt = f"Переведи на русский: {text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.warning(f"[Перевод] Ошибка: {e}")
        return text

# === Публикация новостей ===
def fetch_and_post_news():
    logging.info("🔄 Начинаем сбор новостей...")
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            url = entry.get("link", "")

            if title in posted_titles:
                continue

            # Перевод
            title_ru = translate_to_russian(title)
            summary_ru = translate_to_russian(summary)

            # Генерация реакции
            reaction_json = generate_smart_reaction(title_ru, summary_ru)
            try:
                reaction = json.loads(reaction_json)
            except Exception as e:
                logging.warning(f"[ИИ] Ошибка парсинга реакции: {e}")
                continue

            annotation = reaction.get("annotation", "")
            meme_text = reaction.get("meme_text", "")
            category = reaction.get("category", "")
            region = reaction.get("region", "")

            # Генерация изображения
            image_path = generate_image_for_news(title_ru, category)

            caption = f"<b>📰 {html.escape(title_ru)}</b>\n\n"
            if annotation:
                caption += f"{annotation}\n\n"
            caption += f"📎 <a href='{url}'>Читать полностью</a>\n"
            if category:
                caption += f"🏷 {category} | {region}\n"
            if meme_text:
                caption += f"🤖 {meme_text}"

            try:
                if image_path:
                    bot.send_photo(chat_id=TELEGRAM_CHANNEL, photo=open(image_path, 'rb'), caption=caption, parse_mode='HTML')
                else:
                    bot.send_message(chat_id=TELEGRAM_CHANNEL, text=caption, parse_mode='HTML')
                posted_titles.add(title)
                logging.info("✅ Новость опубликована")
            except Exception as e:
                logging.warning(f"❌ Ошибка при публикации: {e}")

# === Планировщик ===
scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Moscow"))
scheduler.add_job(fetch_and_post_news, "interval", minutes=10)

# === Запуск Flask + планировщик ===
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    scheduler.start()
    fetch_and_post_news()
    while True:
        time.sleep(60)
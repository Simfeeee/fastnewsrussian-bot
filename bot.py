import os
import json
import logging
import feedparser
import openai
import html
import threading
import pytz
import time
from datetime import datetime
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot, InputMediaPhoto
from dotenv import load_dotenv
from smartgen import generate_smart_reaction

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@yourchannel")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Логгер
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)

# Flask для Render
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is alive!"

# Новости
FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "https://www.theguardian.com/world/rss",
    "https://www.france24.com/en/rss",
    "https://www.dw.com/en/top-stories/s-9097?maca=en-rss-en-all-1573-rdf",
    "https://www3.nhk.or.jp/nhkworld/en/news/feed/rss.xml"
]

posted_titles = set()

def translate_to_russian(text):
    try:
        prompt = f"Переведи на русский: {text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.warning(f"Translation failed: {e}")
        return text

def fetch_and_post_news():
    global posted_titles
    logging.info("🔄 Начинаем проверку лент...")
    for feed_url in FEEDS:
        logging.info(f"📰 Чтение ленты: {feed_url}")
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            logging.warning(f"❌ Нет записей в ленте: {feed_url}")
            continue
        for entry in feed.entries[:3]:
            title = translate_to_russian(entry.title)
            summary = translate_to_russian(entry.summary)
            url = entry.link

            logging.info(f"📌 Новость: {title}")

            if title in posted_titles:
                logging.info("⏩ Уже публиковали, пропускаем")
                continue

            reaction_json = generate_smart_reaction(title, summary)
            if not reaction_json:
                logging.warning("❌ Не удалось сгенерировать аннотацию")
                continue

            try:
                reaction = json.loads(reaction_json)
                annotation = reaction.get("annotation", "")
                meme_text = reaction.get("meme_text", "")
                category = reaction.get("category", "")
                logging.info(f"🧠 Аннотация: {annotation}")
                logging.info(f"🏷 Категория: {category}")
            except Exception as e:
                logging.warning(f"❌ Ошибка разбора JSON от smartgen: {e}")
                annotation = ""
                meme_text = ""
                category = ""

            caption = ""
            caption += f"<b>📰 {html.escape(title)}</b>\n\n"
            if annotation:
                caption += f"{html.escape(annotation)}\n\n"
            caption += f"📎 <a href='{url}'>Читать полностью</a>\n"
            if category:
                caption += f"🏷 Категория: <i>{html.escape(category)}</i>\n"
            if meme_text:
                caption += f"🤡 Мем: <i>{html.escape(meme_text)}</i>"

            try:
                bot.send_message(chat_id=CHANNEL, text=caption, parse_mode='HTML', disable_web_page_preview=False)
                posted_titles.add(title)
                logging.info("✅ Опубликовано успешно")
            except Exception as e:
                logging.warning(f"❌ Ошибка при публикации: {e}")

# Планировщик с таймзоной
scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Moscow"))
scheduler.add_job(fetch_and_post_news, "interval", minutes=10)

# Flask и запуск в фоне
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    scheduler.start()
    while True:
        time.sleep(60)
import os
import json
import logging
import feedparser
import openai
import html
import threading
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
def run_flask():
    app.run(host="0.0.0.0", port=10000)
threading.Thread(target=run_flask).start()

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
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            title = translate_to_russian(entry.title)
            summary = translate_to_russian(entry.summary)
            url = entry.link
            if title in posted_titles:
                continue

            reaction_json = generate_smart_reaction(title, summary)
            if not reaction_json:
                continue

            try:
                reaction = json.loads(reaction_json)
                annotation = reaction.get("annotation", "")
                meme_text = reaction.get("meme_text", "")
                category = reaction.get("category", "")
            except Exception as e:
                logging.warning(f"Parsing smartgen failed: {e}")
                annotation = ""
                meme_text = ""
                category = ""

            caption = f"<b>📰 {html.escape(title)}</b>

"
            if annotation:
                caption += f"{html.escape(annotation)}

"
            caption += f"📎 <a href='{url}'>Читать полностью</a>
"
            if category:
                caption += f"🏷 Категория: <i>{html.escape(category)}</i>
"
            if meme_text:
                caption += f"
🤡 Мем: <i>{html.escape(meme_text)}</i>"

            try:
                bot.send_message(chat_id=CHANNEL, text=caption, parse_mode='HTML', disable_web_page_preview=False)
                posted_titles.add(title)
                logging.info(f"Posted: {title}")
            except Exception as e:
                logging.warning(f"Telegram post failed: {e}")

# Планировщик
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_post_news, "interval", minutes=10)
scheduler.start()
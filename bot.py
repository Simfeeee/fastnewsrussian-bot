import os
import logging
import feedparser
import telegram
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import pytz
import openai

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bot = telegram.Bot(token=TOKEN)
logging.basicConfig(level=logging.INFO)

FEEDS = [
    "https://lenta.ru/rss",
    "https://www.kommersant.ru/RSS/news.xml",
    "https://www.rbc.ru/static/rss/news.rss"
]

CATEGORY_KEYWORDS = {
    "Политика": ["путин", "президент", "госдума", "санкции", "германия", "власть", "мерц", "байден", "закон"],
    "Происшествия": ["взрыв", "пожар", "авария", "убийство", "происшествие", "нападение", "теракт"],
    "Экономика": ["курс", "доллар", "экономика", "цены", "нефть", "газ", "инфляция"],
    "Технологии": ["технологии", "искусственный интеллект", "ИИ", "роскосмос", "стартап", "интернет"]
}

def extract_image(entry):
    media_content = entry.get('media_content', [])
    if media_content and 'url' in media_content[0]:
        return media_content[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if link.type and link.type.startswith("image/"):
                return link.href
    return None

def detect_category(text):
    text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "Общество"

def fetch_news():
    news_items = []
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.strip()
            if title in posted_links:
                continue
            posted_links.add(title)
            news_items.append({
                "title": title,
                "summary": entry.summary.strip() if hasattr(entry, "summary") else "",
                "image": extract_image(entry),
            })
    return news_items[:1]

def generate_ironic_comment(text):
    try:
        prompt = f"Сделай ироничный, саркастичный или смешной комментарий к следующей новости:
"{text}""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.9
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.warning(f"OpenAI error: {e}")
        return "🤔 Без комментариев, но вы всё поняли..."

posted_links = set()

def create_caption(item):
    category = detect_category(item['title'])
    emoji = {
        "Политика": "📣",
        "Происшествия": "🚨",
        "Экономика": "💰",
        "Технологии": "🤖",
        "Общество": "📰"
    }.get(category, "📰")

    ironic_comment = generate_ironic_comment(item['title'])

    caption = f"{emoji} <b>[{category}]</b>\n\n{item['title']}\n\n🧠 <i>{ironic_comment}</i>"
    return caption

def post_digest():
    news = fetch_news()
    if not news:
        logging.info("No fresh news.")
        return

    for item in news:
        caption = create_caption(item)
        try:
            if item['image']:
                bot.send_photo(chat_id=CHANNEL, photo=item['image'], caption=caption, parse_mode=telegram.ParseMode.HTML)
            else:
                bot.send_message(chat_id=CHANNEL, text=caption, parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            logging.error(f"Error posting news: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(post_digest, "interval", minutes=7)
    post_digest()
    scheduler.start()
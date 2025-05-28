import os
import logging
import json
import random
import feedparser
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, Updater
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
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

DB_PATH = "reactions_db.json"

CATEGORY_KEYWORDS = {
    "Политика": ["путин", "санкции", "госдума", "мерц", "закон", "байден"],
    "Происшествия": ["взрыв", "убийство", "пожар", "теракт", "ДТП", "катастрофа"],
    "Экономика": ["курс", "нефть", "газ", "экономика", "доллар", "инфляция"],
    "Технологии": ["ИИ", "технологии", "стартап", "искусственный интеллект", "роскосмос"]
}

REGIONS = {
    "Москва": ["москва", "московский", "москве"],
    "Санкт-Петербург": ["петербург", "спб", "санкт-петербург"],
    "Сибирь": ["новосибирск", "томск", "омск", "красноярск"],
    "Урал": ["екатеринбург", "челябинск", "пермь", "урал"],
    "Кавказ": ["дагестан", "чечня", "грозный", "кавказ"],
    "Дальний Восток": ["владивосток", "хабаровск", "сахалин", "дальний восток"]
}

INTERESTING_KEYWORDS = [
    "взорвал", "обрушил", "запретил", "ввёл", "объявил", "арест", "катастрофа",
    "сенсация", "историческое", "удивительно", "рекорд", "впервые", "неожиданно"
]

PROMPTS = [
    "Придумай ироничную, умную и лаконичную реакцию на новость: \"{title}\"",
    "Сделай саркастичный комментарий как будто новость — это абсурд: \"{title}\"",
    "Если бы эту новость обсуждали в интернете, как бы звучал саркастичный ответ: \"{title}\"",
    "Представь, что ты публикуешь это в Telegram с колким комментарием: \"{title}\"",
    "Напиши мемный, меткий, ироничный комментарий по новости: \"{title}\""
]

posted_titles = set()

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

def detect_region(text):
    text = text.lower()
    for region, keywords in REGIONS.items():
        if any(kw in text for kw in keywords):
            return region
    return "Россия"

def is_interesting(title):
    lower_title = title.lower()
    return any(word in lower_title for word in INTERESTING_KEYWORDS)

def fetch_news():
    news_items = []
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.strip()
            if title in posted_titles or not is_interesting(title):
                continue
            posted_titles.add(title)
            news_items.append({
                "title": title,
                "summary": entry.summary.strip() if hasattr(entry, "summary") else "",
                "image": extract_image(entry),
            })
    return news_items[:1]

def generate_comment(title):
    try:
        prompt_template = random.choice(PROMPTS)
        prompt = prompt_template.format(title=title)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=70,
            temperature=0.95
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.warning(f"OpenAI error: {e}")
        return "🤔 Ну и ну..."

def generate_meme_idea(title):
    try:
        prompt = (
            f"На основе этой новости придумай идею для смешного мема. "
            f"Опиши коротко, какую сцену или шаблон мема можно использовать и какая надпись будет.\n"
            f"Новость: \"{title}\""
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.95
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.warning(f"OpenAI meme idea error: {e}")
        return ""

def create_caption(item):
    category = detect_category(item['title'])
    region = detect_region(item['title'] + " " + item['summary'])
    emoji = {
        "Политика": "📣",
        "Происшествия": "🚨",
        "Экономика": "💰",
        "Технологии": "🤖",
        "Общество": "📰"
    }.get(category, "📰")

    comment = generate_comment(item['title'])
    meme = generate_meme_idea(item['title'])

    caption_parts = [
        f"{emoji} <b>[{category} | {region}]</b>",
        item['title'],
        f"🧠 <i>{comment}</i>"
    ]
    if meme:
        caption_parts.append(f"💬 <i>Идея для мема:</i> {meme}")

    caption = "\n\n".join(caption_parts)
    return caption

def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def post_digest(context=None):
    news = fetch_news()
    if not news:
        logging.info("No fresh news.")
        return

    db = load_db()

    for item in news:
        caption = create_caption(item)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👍", callback_data="like"),
             InlineKeyboardButton("😂", callback_data="funny"),
             InlineKeyboardButton("😡", callback_data="angry")]
        ])
        try:
            msg = None
            if item['image']:
                msg = bot.send_photo(chat_id=CHANNEL, photo=item['image'], caption=caption,
                                     parse_mode=telegram.ParseMode.HTML, reply_markup=keyboard)
            else:
                msg = bot.send_message(chat_id=CHANNEL, text=caption,
                                       parse_mode=telegram.ParseMode.HTML, reply_markup=keyboard)

            if msg:
                db[str(msg.message_id)] = {
                    "title": item['title'],
                    "likes": 0,
                    "funny": 0,
                    "angry": 0
                }
                save_db(db)

        except Exception as e:
            logging.error(f"Error posting news: {e}")

def handle_reaction(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    reaction = query.data
    message_id = str(query.message.message_id)

    db = load_db()
    if message_id in db:
        db[message_id][reaction] += 1
        save_db(db)

    reaction_responses = {
        "like": ["🔥 Вот это зашло!", "👍 Спасибо за оценку!", "🙌 Рад, что понравилось!"],
        "funny": ["😂 Ну хоть повеселили!", "Юмор в каждой строчке 😅", "Ха-ха, да, абсурд!"],
        "angry": ["😡 Согласен, бесит!", "🤬 Это уже перебор...", "Бомбит не по-детски 😤"]
    }

    text = random.choice(reaction_responses.get(reaction, ["Спасибо за реакцию!"]))
    try:
        query.message.reply_text(text)
    except Exception as e:
        logging.warning(f"Could not send reaction message: {e}")

def post_top_news():
    db = load_db()
    scored = []

    for msg_id, data in db.items():
        total = data.get("likes", 0) + data.get("funny", 0) + data.get("angry", 0)
        if total > 0:
            scored.append({
                "title": data["title"],
                "likes": data["likes"],
                "funny": data["funny"],
                "angry": data["angry"],
                "score": total
            })

    top_news = sorted(scored, key=lambda x: x["score"], reverse=True)[:3]
    if not top_news:
        return

    message = "🏆 <b>Топ-3 новостей за день:</b>\n"
    medals = ["1️⃣", "2️⃣", "3️⃣"]
    for i, item in enumerate(top_news):
        message += f"\n{medals[i]} {item['title']} — 👍{item['likes']} 😂{item['funny']} 😡{item['angry']}"
    bot.send_message(chat_id=CHANNEL, text=message, parse_mode=telegram.ParseMode.HTML)

def start_bot():
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(post_digest, "interval", minutes=7)
    scheduler.add_job(post_top_news, "cron", hour=21, minute=0)
    scheduler.start()

    updater = Updater(TOKEN, use_context=True)
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_reaction))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    post_digest()
    start_bot()
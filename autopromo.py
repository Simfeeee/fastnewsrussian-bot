import logging
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)

# Список целевых каналов и админов (можно расширить)
TARGETS = [
    {"channel": "@techreview", "admin": "@adminuser1"},
    {"channel": "@politicsdaily", "admin": "@admin_politics"},
    {"channel": "@newsdailyru", "admin": "@editor_name"},
]

PROMO_MESSAGE = (
    "👋 Привет!

"
    "Я представляю канал @fastnewsrussian — публикуем самые интересные, переведённые и ироничные новости со всего мира 🌍

"
    "Предлагаем взаимный пиар или партнёрство. Готовы обсудить любые форматы 😊"
)

def run_autopromo():
    logging.info("🚀 Автопромо запущено")

    for target in TARGETS:
        admin = target.get("admin")
        if not admin or not admin.startswith("@"):
            logging.warning(f"❌ Пропущен: нет валидного admin в {target}")
            continue

        try:
            logging.info(f"✉ Отправка админу {admin}")
            bot.send_message(chat_id=admin, text=PROMO_MESSAGE)
            logging.info(f"✅ Сообщение успешно отправлено: {admin}")
        except TelegramError as e:
            logging.warning(f"⚠ Не удалось отправить {admin}: {e}")

if __name__ == "__main__":
    run_autopromo()
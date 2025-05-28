import json
import random
import logging
from telegram import Bot

TELEGRAM_TOKEN = "YOUR_TOKEN"
CHANNEL = "@yourchannel"
bot = Bot(token=TELEGRAM_TOKEN)

# Предустановленный список целевых каналов
TARGET_CHANNELS = [
    {"username": "@newsdaily", "admin_id": None},
    {"username": "@russianinsight", "admin_id": None},
    {"username": "@tech_radar", "admin_id": None}
]

PROMO_TEXT_TEMPLATE = (
    "Привет! 👋 Я админ новостного канала {my_channel}. "
    "Мы ищем партнёров для кросс-промо. "
    "У нас интересные посты и активная аудитория. "
    "Готовы обменяться постами? 🚀"
)

def send_promo_message(channel_data):
    try:
        promo_text = PROMO_TEXT_TEMPLATE.format(my_channel=CHANNEL)
        if channel_data["admin_id"]:
            bot.send_message(chat_id=channel_data["admin_id"], text=promo_text)
        else:
            # Предполагаем отправку по username (если доступно)
            bot.send_message(chat_id=channel_data["username"], text=promo_text)
        logging.info(f"Sent promo to {channel_data['username']}")
        return True
    except Exception as e:
        logging.warning(f"Failed to send promo to {channel_data['username']}: {e}")
        return False

def run_autopromo():
    partners = []
    for ch in TARGET_CHANNELS:
        success = send_promo_message(ch)
        if success:
            partners.append({"channel": ch["username"], "text": f"🤝 Поддержи партнёров: {ch['username']}"})

    # Сохраняем в partners.json
    with open("partners.json", "w", encoding="utf-8") as f:
        json.dump(partners, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_autopromo()
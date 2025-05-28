import requests
import re
import logging

def extract_admins_from_channel(username):
    url = f"https://t.me/{username.lstrip('@')}"
    logging.info(f"🌐 Получение описания канала: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text

        # Ищем @username в тексте страницы (грубо, но эффективно)
        admins = set(re.findall(r'@\w{5,32}', html))
        return list(admins)
    except Exception as e:
        logging.warning(f"❌ Не удалось получить описание канала {username}: {e}")
        return []

# Пример запуска
if __name__ == "__main__":
    test_channels = ["techreview", "politicsdaily"]
    for channel in test_channels:
        admins = extract_admins_from_channel(channel)
        print(f"🔍 {channel}: {admins}")
import openai
import os
import logging
import random
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

FALLBACK_REACTIONS = [
    {
        "annotation": "🤷 Похоже, очередной виток абсурда.",
        "meme_text": "А мы говорили...",
        "category": "общество",
        "region": "мир"
    },
    {
        "annotation": "🔥 Ну что ж, всё идёт по плану. Почти.",
        "meme_text": "Грустно, но не удивительно",
        "category": "политика",
        "region": "Россия"
    },
    {
        "annotation": "💼 Классика жанра — кто-то снова удивил.",
        "meme_text": "Никогда такого не было и вот опять",
        "category": "экономика",
        "region": "Европа"
    },
    {
        "annotation": "🧠 Видимо, они так видят.",
        "meme_text": "Гении или безумцы?",
        "category": "технологии",
        "region": "США"
    }
]

def generate_smart_reaction(title, summary):
    prompt = f"""
Ты — остроумный редактор новостного Telegram-канала. Придумай саркастичную, ироничную или шутливую аннотацию к следующей новости. Также укажи предполагаемую категорию и регион.

Заголовок: "{title}"
Краткое описание: "{summary}"

Ответ верни строго в JSON-формате:
{{
  "annotation": "...",
  "meme_text": "...",
  "category": "...",
  "region": "..."
}}
"""
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.9,
        )
        return completion["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.warning(f"[ИИ-аннотация] Ошибка генерации: {e}")
        reaction = random.choice(FALLBACK_REACTIONS)
        logging.info("[ИИ-аннотация] Используется fallback-аннотация.")
        import json
        return json.dumps(reaction, ensure_ascii=False)
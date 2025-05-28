import openai
import os
import logging
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
        return None
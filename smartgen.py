import openai
import logging

def generate_smart_reaction(title, summary):
    try:
        prompt = f"""
Ты — саркастичный, умный, немного ироничный комментатор новостей.
Вот новость:
Заголовок: {title}
Краткое содержание: {summary}

Сделай следующее:
1. Короткую, но колкую ироничную аннотацию (1–2 предложения)
2. Мем-фразу — как бы ты подписал мем по этой новости
3. Одним словом определи категорию: Политика, Технологии, Война, Экономика, Общество, Культура

Ответ в формате JSON:
{{
  "annotation": "...",
  "meme_text": "...",
  "category": "..."
}}
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=300
        )
        result = response["choices"][0]["message"]["content"]
        return result
    except Exception as e:
        logging.warning(f"SmartGen error: {e}")
        return None
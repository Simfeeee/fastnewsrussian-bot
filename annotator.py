import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def generate_annotation(title, summary):
    prompt = f"Придумай ироничную подпись к новости:\nЗаголовок: {title}\nСодержание: {summary}\n\nПодпись:"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60
    )
    return response.choices[0].message.content.strip()

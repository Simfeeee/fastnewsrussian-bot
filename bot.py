from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# bot.py (упрощённый блок с добавленным переводом и международными фидами)

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

def translate_to_russian(text):
    try:
        prompt = f"Переведи на русский: {text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.warning(f"Translation error: {e}")
        return text

threading.Thread(target=run_flask).start()
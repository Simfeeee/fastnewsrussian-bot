import os
import logging
from PIL import Image, ImageDraw, ImageFont
from uuid import uuid4

# Заглушка генерации изображения (можно заменить на DALL·E, Stable Diffusion и т.п.)
def generate_image_for_news(title, category):
    try:
        # Генерация простой картинки с текстом
        img = Image.new("RGB", (1024, 512), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)

        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 36)

        draw.text((50, 200), f"{category.upper()}:
{title}", fill=(255, 255, 255), font=font)

        filename = f"/tmp/{uuid4().hex}.jpg"
        img.save(filename, format="JPEG")
        return filename
    except Exception as e:
        logging.warning(f"[Генерация изображения] Ошибка: {e}")
        return None
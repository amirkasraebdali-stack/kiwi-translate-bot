import re
import os
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from deep_translator import GoogleTranslator

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]

SOURCE_CHAT = -1001106437375
DEST_CHAT = -1003817622977
SOURCE_USERNAME = "f1_sports"

SIGNATURE = "\n\n🏁 𝗞𝗶𝘄𝗶 𝗙𝗼𝗿𝗺𝘂𝗹𝗮 🥝 \n ‌🅺\n ❖ @Kiwi_Formula ❖"

PROMO_PATTERNS = [
    r"Дублируем все посты.*",
    r"Скачайте приложение.*",
    r"Подпишись(?:те)? на .*",
    r"@\w+",
    r"https?://\S+",
    r"t\.me/\S+",
    r"\[.*?\]\(.*?\)",
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    for pattern in PROMO_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def translate_to_fa(text: str) -> str:
    if not text:
        return ""
    try:
        return GoogleTranslator(source="auto", target="fa").translate(text)
    except Exception as e:
        print(f"خطای ترجمه: {e}")
        return text

def build_caption(text: str) -> str:
    if not text:
        return SIGNATURE
    return f"<b>{text}</b>{SIGNATURE}"

user = Client("kiwi_user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
bot = Client("kiwi_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@user.on_message(filters.chat(SOURCE_CHAT))
async def copy_handler(client: Client, message: Message):
    file_path = None
    try:
        raw_text = message.caption or message.text or ""
        cleaned = clean_text(raw_text)
        translated = translate_to_fa(cleaned) if cleaned else ""
        final_caption = build_caption(translated)

        if message.photo:
            file_path = await client.download_media(message.photo.file_id)
            await bot.send_photo(DEST_CHAT, photo=file_path, caption=final_caption, parse_mode="html")
        elif message.video:
            file_path = await client.download_media(message.video.file_id)
            await bot.send_video(DEST_CHAT, video=file_path, caption=final_caption, parse_mode="html")
        elif message.text:
            await bot.send_message(DEST_CHAT, text=final_caption, parse_mode="html")
    except Exception as e:
        print(f"خطا در ارسال پیام {message.id}: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

bot.start()
user.start()
try:
    user.join_chat(SOURCE_USERNAME)
except Exception as e:
    print(f"جوین نشد یا از قبل عضو است: {e}")
print("ربات فعال است...")
idle()
user.stop()
bot.stop()

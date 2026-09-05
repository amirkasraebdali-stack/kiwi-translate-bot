import re
import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
import translators as ts

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

F1_NAMES = {
    "Ферстаппен": "ورستپن", "Хэмилтон": "همیلتون", "Леклер": "لکلرک",
    "Норрис": "نوریس", "Расселл": "راسل", "Сайнс": "ساینز",
    "Пиастри": "پیاستری", "Перес": "پرز", "Алонсо": "آلونسو",
    "Стролл": "استرول", "Окон": "اوکان", "Гасли": "گاسلی",
    "Албон": "آلبون", "Сарджент": "سارجنت", "Колапинто": "کولاپینتو",
    "Цунода": "سونودا", "Райкконен": "رایکونن", "Боттас": "بوتاس",
    "Дзоу": "ژو", "Хюлькенберг": "هولکنبرگ", "Магнуссен": "ماگنوسن",
    "Риккардо": "ریکاردو", "Лоусон": "لاوسون", "Бирман": "بیرمن",
    "Антонелли": "آنتونلی", "Хадьяр": "حجار", "Дуэн": "دوهان",
    "Ред Булл": "ردبول", "Феррари": "فراری", "Мерседес": "مرسدس",
    "Макларен": "مک‌لارن", "Астон Мартин": "استون مارتین", "Альпин": "الپین",
    "Уильямс": "ویلیامز", "Хаас": "هاس", "Заубер": "زاوبر",
    "Кик Заубер": "کیک زاوبر", "Рейсинг Буллз": "ریسینگ بولز",
    "Виза Кэш Апп": "ویزا کش اپ", "Хорнер": "هورنر", "Тото Вольфф": "توتو ولف",
    "Вольфф": "ولف", "Виссер": "واسور", "Васер": "واسور", "Браун": "براون",
    "Домиканс": "دومنیکالی", "Доменикали": "دومنیکالی", "Монца": "مونزا",
    "Сильверстоун": "سیلورستون", "Спа": "اسپا", "Монако": "موناکو",
    "Сузука": "سوزوکا", "Интерлагос": "اینترلاگوس", "Абу-Даби": "ابوظبی",
    "Бахрейн": "بحرین", "Джидда": "جده", "Мельбурн": "ملبورن",
    "Имола": "ایمولا", "Барселона": "بارسلونا", "Ред Булл Ринг": "ردبول رینگ",
    "Будапешт": "بوداپست", "Зандворт": "زاندورت", "Баку": "باکو",
    "Сингапур": "سنگاپور", "Остин": "آستین", "Мехико": "مکزیکوسیتی",
    "Лас-Вегас": "لاس‌وگاس", "Лусаил": "لوسیل", "Катар": "قطر",
    "Шанхай": "شانگهای", "Майами": "میامی", "пит-стоп": "پیت استاپ",
    "квалификация": "کوالیفای", "болид": "خودرو", "гонка": "مسابقه",
    "чемпионат": "قهرمانی", "подиум": "سکو", "поул-позиция": "پول پوزیشن",
    "штраф": "جریمه", "сход": "کناره‌گیری", "обгон": "سبقت",
    "шины": "لاستیک", "дождь": "باران",
    "гонщик": "راننده", "гонщика": "راننده", "гонщику": "راننده",
    "гонщиков": "رانندگان", "гонщики": "رانندگان",
    "пилот": "راننده", "пилота": "راننده", "пилоту": "راننده",
    "пилотов": "رانندگان", "пилоты": "رانندگان",
}

def protect_names(text: str):
    placeholders = {}
    idx = 0
    for ru_name in sorted(F1_NAMES.keys(), key=len, reverse=True):
        if ru_name in text:
            placeholder = f"XNM{idx}X"
            text = text.replace(ru_name, placeholder)
            placeholders[placeholder] = F1_NAMES[ru_name]
            idx += 1
    return text, placeholders

def restore_names(text: str, placeholders: dict) -> str:
    for placeholder, name in placeholders.items():
        text = text.replace(placeholder, name)
    return text

def clean_text(text: str) -> str:
    if not text:
        return ""
    for pattern in PROMO_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def translate_to_fa(text: str) -> str:
    if not text:
        return ""
    protected_text, placeholders = protect_names(text)
    for name in ["bing", "google", "alibaba"]:
        try:
            result = ts.translate_text(protected_text, translator=name, from_language="ru", to_language="fa")
            if result:
                return restore_names(result, placeholders)
        except Exception as e:
            print(f"خطای ترجمه با {name}: {e}")
    return text

def build_caption(text: str) -> str:
    if not text:
        return SIGNATURE
    return f"{text}{SIGNATURE}"

user = Client("kiwi_user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
bot = Client("kiwi_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

media_group_buffer = {}

async def process_single_message(message: Message):
    for attempt in range(3):
        file_path = None
        try:
            raw_text = message.caption or message.text or ""
            cleaned = clean_text(raw_text)
            translated = translate_to_fa(cleaned) if cleaned else ""
            final_caption = build_caption(translated)

            if message.photo:
                file_path = await message.download()
                await bot.send_photo(DEST_CHAT, photo=file_path, caption=final_caption)
            elif message.video:
                file_path = await message.download()
                await bot.send_video(DEST_CHAT, video=file_path, caption=final_caption)
            elif message.text:
                await bot.send_message(DEST_CHAT, text=final_caption)

            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            print(f"پیام {message.id} با موفقیت ارسال شد.")
            return
        except Exception as e:
            print(f"خطا در ارسال پیام {message.id} (تلاش {attempt+1}): {e}")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            await asyncio.sleep(5)
    print(f"پیام {message.id} پس از ۳ تلاش ناموفق ماند.")

async def process_media_group(gid):
    await asyncio.sleep(2)
    messages = media_group_buffer.pop(gid, [])
    if not messages:
        return
    messages.sort(key=lambda m: m.id)

    caption_text = ""
    for m in messages:
        if m.caption:
            caption_text = m.caption
            break

    cleaned = clean_text(caption_text)
    translated = translate_to_fa(cleaned) if cleaned else ""
    final_caption = build_caption(translated)

    for attempt in range(3):
        media_list = []
        file_paths = []
        try:
            for i, m in enumerate(messages):
                cap = final_caption if i == 0 else None
                if m.photo:
                    fp = await m.download()
                    file_paths.append(fp)
                    media_list.append(InputMediaPhoto(fp, caption=cap))
                elif m.video:
                    fp = await m.download()
                    file_paths.append(fp)
                    media_list.append(InputMediaVideo(fp, caption=cap))

            if media_list:
                await bot.send_media_group(DEST_CHAT, media_list)

            for fp in file_paths:
                if os.path.exists(fp):
                    os.remove(fp)
            print(f"آلبوم {gid} با موفقیت ارسال شد.")
            return
        except Exception as e:
            print(f"خطا در ارسال آلبوم (تلاش {attempt+1}): {e}")
            for fp in file_paths:
                if os.path.exists(fp):
                    os.remove(fp)
            await asyncio.sleep(5)
    print(f"آلبوم {gid} پس از ۳ تلاش ناموفق ماند.")

@user.on_message(filters.chat(SOURCE_CHAT))
async def copy_handler(client: Client, message: Message):
    print(f"### پیام جدید دریافت شد: id={message.id} ###")
    if message.media_group_id:
        gid = message.media_group_id
        if gid not in media_group_buffer:
            media_group_buffer[gid] = []
            asyncio.create_task(process_media_group(gid))
        media_group_buffer[gid].append(message)
        return
    asyncio.create_task(process_single_message(message))

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

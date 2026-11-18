import re
import os
import time
import asyncio
import threading
import requests
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
import translators as ts

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

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
    "Ред Булл": "رد بول", "Феррари": "فراری", "Мерседес": "مرسدس",
    "Макларен": "مک‌لارن", "Астон Мартин": "استون مارتین", "Альпин": "آلپاین",
    "Уильямс": "ویلیامز", "Хаас": "هاس", "Заубер": "زاوبر",
    "Кик Заубер": "کیک زاوبر", "Рейсинг Буллз": "ریسینگ بولز",
    "Виза Кэш Апп": "ویزا کش اپ", "Хорнер": "هورنر", "Тото Вольфф": "توتو ولف",
    "Вольфф": "ولف", "Виссер": "واسور", "Васер": "واسور", "Браун": "براون",
    "Домиканс": "دومنیکالی", "Доменикали": "دومنیکالی", "Монца": "مونزا",
    "Сильверстоун": "سیلورستون", "Спа": "اسپا", "Монако": "موناکو",
    "Сузука": "سوزوکا", "Интерлагос": "اینترلاگوس", "Абу-Даби": "ابوظبی",
    "Бахрейн": "بحرین", "Джидда": "جده", "Мельбурн": "ملبورن",
    "Имола": "ایمولا", "Барселона": "بارسلونا", "Ред Булл Ринг": "رد بول رینگ",
    "Будапешт": "بوداپست", "Зандворт": "زاندورت", "Баку": "باکو",
    "Сингапур": "سنگاپور", "Остин": "آستین", "Мехико": "مکزیکوسیتی",
    "Лас-Вегас": "لاس‌وگاس", "Лусаил": "لوسیل", "Катар": "قطر",
    "Шанхай": "شانگهای", "Майами": "میامی", "пит-стоп": "پیت استاپ",
    "квалификация": "کوالیفای", "квалификации": "کوالیفای",
    "квалификацию": "کوالیفای", "квалификаций": "کوالیفای",
    "болид": "خودرو", "гонка": "مسابقه",
    "чемпионат": "قهرمانی", "подиум": "سکو",
    "поул-позиция": "پول پوزیشن", "поул-позиции": "پول پوزیشن",
    "поул": "پول پوزیشن", "пол-позиция": "پول پوزیشن", "пол-позиции": "پول پوزیشن",
    "штраф": "جریمه", "сход": "کناره‌گیری", "обгон": "سبقت",
    "шины": "لاستیک", "дождь": "باران",
    "гонщик": "راننده", "гонщика": "راننده", "гонщику": "راننده",
    "гонщиков": "رانندگان", "гонщики": "رانندگان",
    "пилот": "راننده", "пилота": "راننده", "пилоту": "راننده",
    "пилотов": "رانندگان", "пилоты": "رانندگان",
}

SYSTEM_PROMPT = (
    "تو سردبیر و مترجم حرفه‌ای یک کانال خبری فرمول یک به زبان فارسی هستی. "
    "متن روسی را به فارسی روان، طبیعی و خبری بازنویسی کن، نه ترجمه کلمه‌به‌کلمه. "
    "جمله‌ها باید کوتاه، تمیز و مثل خبرگزاری‌های ورزشی فارسی باشند. "
    "«гонщик» و «пилот» در این متن‌ها یعنی «راننده»، نه خلبان. "
    "عدد، رکورد، زمان و نام‌ها را دقیق نگه دار و چیزی اضافه یا حذف نکن. "
    "اگر فهرست معادل‌ها داده شد، همان املا را عیناً به‌کار ببر. "
    "ساختار خط‌ها و پاراگراف‌ها را حفظ کن. "
    "فقط متن نهایی فارسی را بنویس، بدون توضیح، مقدمه یا گیومه اضافه."
)

def build_glossary(text: str) -> str:
    return "\n".join(f"{ru} = {fa}" for ru, fa in F1_NAMES.items() if ru in text)

def clean_text(text: str) -> str:
    if not text:
        return ""
    for pattern in PROMO_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def translate_groq(text: str) -> str:
    if not GROQ_API_KEY:
        return ""
    glossary = build_glossary(text)
    user_text = text
    if glossary:
        user_text = f"فهرست معادل‌ها:\n{glossary}\n\nمتن:\n{text}"
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    url = "https://api.groq.com/openai/v1/chat/completions"
    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if r.status_code == 200:
                result = r.json()["choices"][0]["message"]["content"].strip()
                return result
            print(f"خطای Groq {r.status_code}: {r.text[:300]}")
            if r.status_code in (429, 500, 503):
                time.sleep(4 * (attempt + 1))
                continue
            return ""
        except Exception as e:
            print(f"خطای Groq (تلاش {attempt+1}): {e}")
            time.sleep(3)
    return ""

def translate_fallback(text: str) -> str:
    placeholders = {}
    idx = 0
    protected = text
    for ru in sorted(F1_NAMES.keys(), key=len, reverse=True):
        if ru in protected:
            ph = f"XNM{idx}X"
            protected = protected.replace(ru, ph)
            placeholders[ph] = F1_NAMES[ru]
            idx += 1
    for name in ["bing", "google", "alibaba"]:
        try:
            result = ts.translate_text(protected, translator=name, from_language="ru", to_language="fa")
            if result:
                for ph, fa in placeholders.items():
                    result = result.replace(ph, fa)
                return result
        except Exception as e:
            print(f"خطای ترجمه با {name}: {e}")
    return text

def translate_to_fa(text: str) -> str:
    if not text:
        return ""
    result = translate_groq(text)
    if result:
        return result
    print("Groq جواب نداد، ترجمه جایگزین استفاده شد.")
    return translate_fallback(text)

def build_caption(text: str) -> str:
    if not text:
        return SIGNATURE
    return f"{text}{SIGNATURE}"

user = Client("kiwi_user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
bot = Client("kiwi_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

media_group_buffer = {}

async def process_single_message(message: Message):
    raw_text = message.caption or message.text or ""
    cleaned = clean_text(raw_text)
    translated = await asyncio.to_thread(translate_to_fa, cleaned) if cleaned else ""
    final_caption = build_caption(translated)

    for attempt in range(3):
        file_path = None
        try:
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
    translated = await asyncio.to_thread(translate_to_fa, cleaned) if cleaned else ""
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

threading.Thread(target=run_web, daemon=True).start()

bot.start()
user.start()
try:
    user.join_chat(SOURCE_USERNAME)
except Exception as e:
    print(f"جوین نشد یا از قبل عضو است: {e}")
print(f"ربات فعال است... مدل ترجمه: {GROQ_MODEL}")
idle()
user.stop()
bot.stop()

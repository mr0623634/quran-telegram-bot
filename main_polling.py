#!/usr/bin/env python3
"""
بوت تيليجرام للقرآن الكريم كامل (114 سورة - 6236 آية)
المصدر: AlQuran Cloud API - https://api.alquran.cloud
يعتمد على مكتبة requests فقط (بدون python-telegram-bot) ليعمل بثبات.

التشغيل:
    pip install -r requirements.txt
    cp .env.example .env   # وحط التوكن بتاعك
    python main.py
التوكن بتجيبه من @BotFather على تيليجرام: /newbot
"""
import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API = "https://api.alquran.cloud/v1"
TG = f"https://api.telegram.org/bot{TOKEN}"
MAX_LEN = 4000
session = requests.Session()
session.headers.update({"User-Agent": "QuranBot/1.0"})


def tg(method, data=None, files=None, timeout=60):
    r = session.post(f"{TG}/{method}", data=data, files=files, timeout=timeout)
    r.raise_for_status()
    return r.json()["result"]


def get_json(url, timeout=20):
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()["data"]


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        import json
        payload["reply_markup"] = json.dumps(reply_markup)
    return tg("sendMessage", data=payload)


def send_long(chat_id, text, reply_markup=None):
    parts, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > MAX_LEN:
            parts.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        parts.append(cur)
    for i, part in enumerate(parts):
        send_message(chat_id, part,
                     reply_markup=reply_markup if i == len(parts) - 1 else None)


def send_audio(chat_id, audio_url, caption):
    return tg("sendAudio", data={"chat_id": chat_id, "audio": audio_url, "caption": caption})


def keyboard(rows):
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows]}


def send_surah(chat_id, num):
    try:
        n = int(num)
        if not 1 <= n <= 114:
            raise ValueError
    except ValueError:
        send_message(chat_id, "رقم السورة لازم يكون من 1 لـ 114.")
        return
    send_message(chat_id, "⏳ جاري تحميل السورة...")
    try:
        s = get_json(f"{API}/surah/{n}")
    except Exception as e:
        send_message(chat_id, f"حصل خطأ في التحميل، حاول تاني. ({e})")
        return
    header = f"📖 {s['name']} — {s['englishName']}\nعدد الآيات: {s['numberOfAyahs']} • {s['revelationType']}\n\n"
    body = "\n".join(f"﴿{a['numberInSurah']}﴾ {a['text'].strip()}" for a in s["ayahs"])
    send_long(chat_id, header + body)


def random_ayah(chat_id):
    n = random.randint(1, 6236)
    try:
        d = get_json(f"{API}/ayah/{n}")
        send_message(chat_id, f"🎲 ﴿{d['text'].strip()}﴾\n\n— سورة {d['surah']['name']}، آية {d['numberInSurah']}")
    except Exception:
        send_message(chat_id, "حصل خطأ، حاول تاني.")


def start_text():
    return (
        "🕌 أهلاً بك في بوت القرآن الكريم\n\n"
        "القرآن كامل: 114 سورة، 6236 آية.\n\n"
        "الأوامر:\n"
        "• /surah رقم السورة — مثال: /surah 2\n"
        "• /ayah رقم السورة:رقم الآية — مثال: /ayah 2:255 (آية الكرسي)\n"
        "• /juz رقم الجزء — مثال: /juz 30\n"
        "• /random — آية عشوائية\n"
        "• /search كلمة — مثال: /search الرحمن\n"
        "• /audio رقم السورة:رقم الآية — صوت الآية بصوت العفاسي\n\n"
        "أو اكتب اسم السورة أو رقمها مباشرة في الشات."
    )


def start_kb():
    return keyboard([
        [("📖 قائمة السور", "list:0")],
        [("🎲 آية عشوائية", "random")],
        [("🔍 بحث في القرآن", "help_search")],
    ])


def list_surahs(chat_id, page):
    surahs = get_json(f"{API}/meta")["surahs"]["references"]
    per, start = 19, page * 19
    rows = []
    row = []
    for s in surahs[start:start + per]:
        row.append((f"{s['number']}. {s['name']}", f"s:{s['number']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(("◀️ السابق", f"list:{page - 1}"))
    if start + per < 114:
        nav.append(("التالي ▶️", f"list:{page + 1}"))
    if nav:
        rows.append(nav)
    send_message(chat_id, "📖 اختر سورة:", reply_markup=keyboard(rows))


def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()
    if not text:
        return
    parts = text.split()
    cmd, args = parts[0], parts[1:]

    if cmd == "/start":
        send_message(chat_id, start_text(), reply_markup=start_kb())
    elif cmd == "/surah":
        if not args:
            send_message(chat_id, "اكتب رقم السورة، مثال: /surah 36")
        else:
            send_surah(chat_id, args[0])
    elif cmd == "/ayah":
        if not args or ":" not in args[0]:
            send_message(chat_id, "الصيغة: /ayah 2:255")
            return
        s, a = args[0].split(":", 1)
        try:
            d = get_json(f"{API}/ayah/{s}:{a}")
            send_message(chat_id, f"﴿{d['text'].strip()}﴾\n\n— سورة {d['surah']['name']}، آية {d['numberInSurah']}")
        except Exception:
            send_message(chat_id, "الآية غير موجودة، تأكد من الرقم. مثال: /ayah 2:255")
    elif cmd == "/juz":
        if not args:
            send_message(chat_id, "اكتب رقم الجزء من 1 لـ 30، مثال: /juz 30")
            return
        try:
            n = int(args[0])
            if not 1 <= n <= 30:
                raise ValueError
            d = get_json(f"{API}/juz/{n}")
            ayahs = d["ayahs"]
            out = f"📖 الجزء {n} — {len(ayahs)} آية\n\n"
            out += "\n".join(f"﴿{a['numberInSurah']}﴾ {a['text'].strip()}  — {a['surah']['name']}" for a in ayahs)
            send_long(chat_id, out)
        except ValueError:
            send_message(chat_id, "رقم الجزء لازم يكون من 1 لـ 30.")
        except Exception as e:
            send_message(chat_id, f"حصل خطأ، حاول تاني. ({e})")
    elif cmd == "/random":
        random_ayah(chat_id)
    elif cmd == "/search":
        if not args:
            send_message(chat_id, "اكتب كلمة للبحث، مثال: /search الرحمن")
            return
        q = " ".join(args)
        try:
            d = get_json(f"{API}/search/{q}")
            matches = d.get("matches", [])[:5]
            if not matches:
                send_message(chat_id, "مفيش نتائج للكلمة دي.")
                return
            out = f"🔍 نتائج البحث عن «{q}» — {d.get('count', len(matches))} نتيجة (أول 5):\n\n"
            for m in matches:
                out += f"﴿{m['text'].strip()}﴾\n— سورة {m['surah']['name']}، آية {m['numberInSurah']}\n\n"
            send_long(chat_id, out)
        except Exception:
            send_message(chat_id, "حصل خطأ في البحث، حاول تاني.")
    elif cmd == "/audio":
        if not args or ":" not in args[0]:
            send_message(chat_id, "الصيغة: /audio 2:255")
            return
        s, a = args[0].split(":", 1)
        try:
            d = get_json(f"{API}/ayah/{s}:{a}/ar.alafasy")
            send_audio(chat_id, d["audio"], f"🎧 سورة {d['surah']['name']}، آية {d['numberInSurah']} — بصوت مشاري العفاسي")
        except Exception:
            send_message(chat_id, "مش قادر أجيب الصوت، تأكد من الرقم.")
    elif text.isdigit():
        send_surah(chat_id, text)
    else:
        try:
            surahs = get_json(f"{API}/meta")["surahs"]["references"]
            for s in surahs:
                if text in s["name"] or text.lower() in s["englishName"].lower():
                    send_surah(chat_id, str(s["number"]))
                    return
        except Exception:
            pass
        send_message(chat_id, "اكتب رقم السورة (1-114) أو اسمها، أو استخدم /start لعرض الأوامر.")


def handle_callback(query):
    chat_id = query["message"]["chat"]["id"]
    data = query["data"]
    tg("answerCallbackQuery", data={"callback_query_id": query["id"]})
    if data == "random":
        random_ayah(chat_id)
    elif data == "help_search":
        send_message(chat_id, "اكتب: /search الكلمة — مثال: /search الرحمن")
    elif data.startswith("list:"):
        list_surahs(chat_id, int(data.split(":")[1]))
    elif data.startswith("s:"):
        send_surah(chat_id, data.split(":")[1])


def main():
    if not TOKEN:
        raise SystemExit("❌ حط التوكن في ملف .env — شوف README.md")
    me = tg("getMe", timeout=30)
    print(f"✅ بوت القرآن شغال... @{me['username']}", flush=True)
    offset = None
    while True:
        try:
            data = {"timeout": 30}
            if offset:
                data["offset"] = offset
            updates = tg("getUpdates", data=data, timeout=60)
            for u in updates:
                offset = u["update_id"] + 1
                if "message" in u:
                    handle_message(u["message"])
                elif "callback_query" in u:
                    handle_callback(u["callback_query"])
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            print(f"⚠️ خطأ في الاتصال، إعادة المحاولة... ({e})", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()

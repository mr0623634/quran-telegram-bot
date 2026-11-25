"""نسخة Webhook من بوت القرآن للاستضافة على Vercel (Serverless).
بعد النشر، فعّل الـ webhook بالأمر:
  curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-app>.vercel.app/api/webhook"
أو شغّل: python set_webhook.py https://<your-app>.vercel.app/api/webhook
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify  # noqa: E402
import main_polling as bot  # noqa: E402

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "bot": "Quran Bot", "status": "running"})


@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True) or {}
    try:
        if "message" in update:
            bot.handle_message(update["message"])
        elif "callback_query" in update:
            bot.handle_callback(update["callback_query"])
    except Exception as e:
        print(f"webhook error: {e}", flush=True)
    return jsonify({"ok": True})


# Vercel يتوقع app على مستوى الملف

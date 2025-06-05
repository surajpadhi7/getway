import hashlib
import time
import random
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔐 Config
BOT_TOKEN = '7910867581:AAFk5K2UCcO0ZDcNwYId9wLYw3kxUWzgSbM'
MERCHANT_NO = 'mer553833'
SECRET_KEY = 'f760332dcb1dd887d4079754b52fdb2b'
NOTIFY_URL = 'https://yourdomain.com/api/webhook1'  # Update to your real webhook

# 🔑 Signature function (same as PHP style)
def generate_signature(params, key):
    sorted_params = dict(sorted((k, v) for k, v in params.items() if v and k != 'sign'))
    sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params.items()]) + key
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

# 💳 Create payment link
def create_payment_link(amount):
    order_no = f"PAYIN{int(time.time())}{random.randint(1111,9999)}"
    payload = {
        "merchantNo": MERCHANT_NO,
        "orderNo": order_no,
        "orderAmt": str(amount),
        "firstName": "John",
        "lastName": "Tom",
        "payEmail": "john.tom@gmail.com",
        "payPhone": "02012345678",
        "productCode": "90001",
        "notifyUrl": NOTIFY_URL
    }
    payload["sign"] = generate_signature(payload, SECRET_KEY)

    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post("https://api.fast-vip.com/api/payGate/payOrder", headers=headers, data=json.dumps(payload))
        res = response.json()

        if response.status_code != 200:
            return f"❌ API Error (HTTP {response.status_code}):\n{response.text}"

        if res.get("code") != "200":
            return f"❌ Gateway Error:\nCode: {res.get('code')}\nMsg: {res.get('msg')}\nDetails: {json.dumps(res.get('data'), indent=2)}"

        if res.get("data") and res["data"].get("payUrl"):
            return f"✅ Payment Link:\n{res['data']['payUrl']}"
        else:
            return f"❌ Unexpected response:\n{json.dumps(res, indent=2)}"

    except Exception as e:
        return f"❌ Exception occurred:\n{str(e)}"

# 🚀 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the OTT Payment Bot!\n\n"
        "💰 Please enter the amount you want to pay (e.g., 200, 400):"
    )

# 🧾 Amount handler
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
        if amount < 10:
            await update.message.reply_text("⚠️ Minimum amount should be ₹10.")
            return

        await update.message.reply_text("⏳ Generating payment link, please wait...")
        link_message = create_payment_link(amount)
        await update.message.reply_text(link_message)

    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (e.g., 100, 200).")

# ✅ Run bot
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    print("🤖 Telegram Payment Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    run_bot()

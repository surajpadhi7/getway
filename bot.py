import hashlib
import time
import random
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
BOT_TOKEN = '7752562013:AAFfaikf_QZFy5TEGiSP0ahinz0t7ZXgIX0'
MERCHANT_NO = 'mer553833'
SECRET_KEY = 'f760332dcb1dd887d4079754b52fdb2b'
NOTIFY_URL = 'https://yourdomain.com/api/webhook1'  # Update this

# Signature function (same as PHP logic)
def generate_signature(params, key):
    sorted_params = dict(sorted((k, v) for k, v in params.items() if v and k != 'sign'))
    sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params.items()]) + key
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

# Payment link generator
def create_payment_link(amount):
    order_no = f"PAYIN{int(time.time())}{random.randint(1111,9999)}"
    payload = {
        "merchantNo": MERCHANT_NO,
        "orderNo": order_no,
        "orderAmt": str(amount),
        "firstName": "john",
        "lastName": "tom",
        "payEmail": "john.tom@gmail.com",
        "payPhone": "02012345678",
        "productCode": "80001",
        "notifyUrl": NOTIFY_URL
    }
    payload["sign"] = generate_signature(payload, SECRET_KEY)

    headers = {'Content-Type': 'application/json'}
    response = requests.post("https://api.fast-vip.com/api/payGate/payOrder", headers=headers, data=json.dumps(payload))

    try:
        res = response.json()
        if res.get("data") and res["data"].get("payUrl"):
            return res["data"]["payUrl"]
        else:
            return f"❌ Failed to get payment link: {res.get('msg', 'Unknown error')}"
    except Exception as e:
        return f"❌ Error parsing response: {str(e)}"

# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Please enter the amount (e.g., 200):")

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        await update.message.reply_text("⏳ Generating payment link...")
        link = create_payment_link(amount)
        await update.message.reply_text(f"✅ Pay using this link:\n{link}")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (e.g., 100, 200).")

# Main bot setup
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_amount))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    run_bot()

import json
import time
import random
import hashlib
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ====== CONFIG ======
TOKEN = '7910867581:AAFk5K2UCcO0ZDcNwYId9wLYw3kxUWzgSbM'
ADMIN_CHAT_ID = '6148224523'

MERCHANT_NO = 'mer553833'
SECRET_KEY = 'f760332dcb1dd887d4079754b52fdb2b'
PAYMENT_URL = 'https://api.fast-vip.com/api/payGate/payOrder'
CALLBACK_URL = 'https://yourdomain.com/api/webhook1'

OTT_PLATFORMS = {
    "Netflix": {"6": 500, "12": 900},
    "Prime Video": {"6": 400, "12": 800},
    "Disney+ Hotstar": {"6": 300, "12": 600},
    "Hulu": {"6": 350, "12": 700}
}


# ====== SIGN GENERATION ======
def generate_sign(params, secret_key):
    try:
        sorted_items = sorted((k, v) for k, v in params.items() if v and k != 'sign')
        sign_str = '&'.join(f"{k}={v}" for k, v in sorted_items)
        sign_str += secret_key
        return hashlib.md5(sign_str.encode()).hexdigest()
    except Exception as e:
        print("Signature Error:", e)
        return ''


# ====== PAYMENT LINK GENERATOR ======
def generate_payment_link(platform, amount):
    order_no = "PAYIN" + str(int(time.time())) + str(random.randint(100, 999))
    payload = {
        "merchantNo": MERCHANT_NO,
        "orderNo": order_no,
        "orderAmt": str(amount),
        "firstName": "john",
        "lastName": "tom",
        "payEmail": "john.tom@gmail.com",
        "payPhone": "02012345678",
        "productCode": "80001",
        "notifyUrl": CALLBACK_URL
    }
    payload["sign"] = generate_sign(payload, SECRET_KEY)

    try:
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(PAYMENT_URL, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        print("Response:", response_data)

        if response_data.get("code") == 200 and "data" in response_data:
            return response_data["data"].get("payUrl")
        else:
            print("Payment Failed:", response_data)
            return None
    except Exception as e:
        print("Error:", e)
        return None


# ====== START COMMAND ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(platform, callback_data=platform)] for platform in OTT_PLATFORMS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select OTT Platform:", reply_markup=reply_markup)


# ====== PLATFORM SELECTION ======
async def handle_ott_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    platform = query.data
    keyboard = [
        [
            InlineKeyboardButton(f"6 Months - ₹{OTT_PLATFORMS[platform]['6']}", callback_data=f"{platform}_6"),
            InlineKeyboardButton(f"12 Months - ₹{OTT_PLATFORMS[platform]['12']}", callback_data=f"{platform}_12")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"You selected {platform}. Choose a plan:", reply_markup=reply_markup)


# ====== PLAN SELECTION ======
async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected = query.data
    platform, duration = selected.split("_")
    amount = OTT_PLATFORMS[platform][duration]

    payment_link = generate_payment_link(platform, amount)
    if payment_link:
        await query.edit_message_text(
            f"You selected {platform} ({duration} months).\n\nClick below to pay:\n{payment_link}"
        )
    else:
        await query.edit_message_text("❌ Failed to generate payment link. Try again later.")


# ====== CALLBACK / MANUAL COMMAND FOR SUCCESS NOTIFICATION ======
async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text.split()
    if len(data) < 3:
        await update.message.reply_text("Invalid format. Use: /callback Netflix 6 500")
        return

    platform, duration, amount = data[0], data[1], data[2]

    message = (
        f"✅ Payment Received!\n"
        f"📺 Platform: {platform}\n"
        f"🕒 Duration: {duration} months\n"
        f"💰 Amount: ₹{amount}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)


# ====== MAIN ======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_ott_selection, pattern='^(Netflix|Prime Video|Disney\+ Hotstar|Hulu)$'))
    app.add_handler(CallbackQueryHandler(handle_plan_selection, pattern='^(.*)_(6|12)$'))
    app.add_handler(CommandHandler("callback", payment_callback))  # Manual trigger

    print("🤖 Bot is running...")
    app.run_polling()


# ENTRY POINT
if _name_ == '_main_':
    main()

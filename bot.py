from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import hashlib, time, random, requests, threading

# Configuration
BOT_TOKEN = "7910867581:AAFk5K2UCcO0ZDcNwYId9wLYw3kxUWzgSbM"
MERCHANT_NO = "mer553833"
SIGN_KEY = "f760332dcb1dd887d4079754b52fdb2b"
PRODUCT_CODE = "80001"
NOTIFY_URL = "https://yourdomain.com/callback"  # change to your webhook URL

OTT_OPTIONS = ["Disney+", "Hotstar", "Netflix", "Zee5"]
PRICES = [200, 400, 600, 800]

# Flask app for webhook
flask_app = Flask(__name__)

@flask_app.route("/callback", methods=["POST"])
def payment_callback():
    data = request.get_json() or request.form
    with open("callback_data.txt", "a") as f:
        f.write(str(data) + "\n")
    return "OK"

# Signature function (PHP-style)
def create_signature(params: dict, key: str) -> str:
    sorted_items = sorted((k, v) for k, v in params.items() if k != "sign" and v)
    base = "&".join(f"{k}={v}" for k, v in sorted_items)
    return hashlib.md5((base + key).encode()).hexdigest()

# Payment request generator
def generate_payment_link(user, platform, price):
    order_no = f"PAYIN{int(time.time())}{random.randint(100,999)}"
    params = {
        "merchantNo": MERCHANT_NO,
        "orderNo": order_no,
        "orderAmt": str(price),
        "firstName": user.first_name or "TG",
        "lastName": "User",
        "payEmail": f"{order_no}@demo.com",
        "payPhone": "9999999999",
        "productCode": PRODUCT_CODE,
        "notifyUrl": NOTIFY_URL
    }
    params["sign"] = create_signature(params, SIGN_KEY)
    response = requests.post("https://api.fast-vip.com/api/payGate/payOrder", json=params)
    return response.json()

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"ott_{name}")] for name in OTT_OPTIONS]
    await update.message.reply_text("Select OTT Platform:", reply_markup=InlineKeyboardMarkup(keyboard))

async def ott_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data.split("_")[1]
    context.user_data["platform"] = platform
    keyboard = [[InlineKeyboardButton(f"₹{p}", callback_data=f"price_{p}")] for p in PRICES]
    await query.edit_message_text(f"Selected: {platform}\nNow choose price:", reply_markup=InlineKeyboardMarkup(keyboard))

async def price_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    price = int(query.data.split("_")[1])
    platform = context.user_data.get("platform", "Unknown")

    user = query.from_user
    response = generate_payment_link(user, platform, price)

    if response.get("data") and response["data"].get("payUrl"):
        pay_url = response["data"]["payUrl"]
        await query.edit_message_text(
            f"✅ *Platform:* {platform}\n💰 *Price:* ₹{price}\n\n👉 [Click here to Pay]({pay_url})",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("❌ Failed to create payment link.")

# --- Launch Telegram Bot & Flask together ---
def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ott_selected, pattern="^ott_"))
    app.add_handler(CallbackQueryHandler(price_selected, pattern="^price_"))
    app.run_polling()

# --- Run Both Together ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()

import logging
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- CONFIGURATION ---
BOT_TOKEN = "7603128499:AAHrUje-z46qOmqcGJ89GGFaCiR4toVxGA8"
FASTPAY_API_URL = "https://api.fast-vip.com/api/payGate/payOrder"
MERCHANT_ID = "mer553833"
MERCHANT_KEY = "f760332dcb1dd887d4079754b52fdb2b"
NOTIFY_URL = "https://yourdomain.com/callback"  # Replace with your actual callback URL
RETURN_URL = "https://t.me/ott_heree"

logging.basicConfig(level=logging.INFO)

# --- HELPER FUNCTIONS ---
def generate_order_id():
    return "OTT" + ''.join(random.choices(string.digits + string.ascii_lowercase, k=12))

def create_signature(data: dict, key: str) -> str:
    import hashlib
    sorted_items = sorted((k, str(v)) for k, v in data.items() if v and k != "sign")
    sign_string = "&".join(f"{k}={v}" for k, v in sorted_items) + key
    return hashlib.md5(sign_string.encode()).hexdigest().upper()

def create_payment_link(amount: str) -> str:
    order_id = generate_order_id()
    payload = {
        "merchantNo": MERCHANT_ID,
        "orderAmount": amount,
        "orderNo": order_id,
        "notifyUrl": NOTIFY_URL,
        "returnUrl": RETURN_URL,
        "payType": "BANK",  # You can change to 'QR' or 'UPI' if available
        "productName": "OTT Purchase"
    }
    payload["sign"] = create_signature(payload, MERCHANT_KEY)
    logging.info(f"📦 Payload: {payload}")
    try:
        response = requests.post(FASTPAY_API_URL, json=payload, timeout=10)
        response_data = response.json()
        logging.info(f"📨 FastPay Response: {response_data}")
        if response_data.get("code") == 200 and response_data.get("data"):
            return response_data["data"].get("payUrl") or "❌ Payment URL not returned"
        return f"❌ FastPay Error: {response_data.get('msg', 'Unknown error')}"
    except Exception as e:
        logging.error(f"Request Exception: {str(e)}")
        return f"❌ Request Error: {str(e)}"

# --- TELEGRAM BOT HANDLERS ---
ASK_AMOUNT = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /pay to start payment.")

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Kitna pay karna hai? Amount bhejo.")
    return ASK_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text.strip()
    if not amount.isdigit():
        await update.message.reply_text("❌ Sirf number bhejo, jaise 500")
        return ASK_AMOUNT
    link = create_payment_link(amount)
    await update.message.reply_text(f"✅ Payment link generated:
{link}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# --- MAIN ---
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("pay", pay_command)],
    states={ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)]},
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)

if __name__ == '__main__':
    app.run_polling()

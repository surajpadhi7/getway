import logging
import string
import random
import hashlib
import httpx
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your credentials
BOT_TOKEN = "7603128499:AAHrUje-z46qOmqcGJ89GGFaCiR4toVxGA8"
MERCHANT_NO = "mer553833"
MERCHANT_KEY = "f760332dcb1dd887d4079754b52fdb2b"
PAYMENT_URL = "https://api.fast-vip.com/api/payGate/payOrder"
NOTIFY_URL = "https://yourdomain.com/callback"  # replace with your actual domain
RETURN_URL = "https://t.me/ott_heree"

ASK_AMOUNT = 1

# Utility to generate a random order number
def generate_order_no():
    return "OTT" + ''.join(random.choices(string.digits, k=13))

# Utility to generate sign using MD5
def generate_sign(payload: dict) -> str:
    keys = sorted(payload)
    sign_str = ""
    for key in keys:
        if payload[key] is not None and payload[key] != "":
            sign_str += f"{key}={payload[key]}&"
    sign_str += f"key={MERCHANT_KEY}"
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

# Start command
def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Welcome! Use /pay to make a payment.")

# Pay command handler
async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("💰 Kitna pay karna hai? Amount bhejo (e.g. 500)")
    return ASK_AMOUNT

# Receive amount and call FastPay
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = update.message.text.strip()
    if not amount.isdigit():
        await update.message.reply_text("❌ Amount sahi format me bhejo (sirf number)")
        return ConversationHandler.END

    order_no = generate_order_no()
    payload = {
        "merchantNo": MERCHANT_NO,
        "orderAmount": amount,
        "orderNo": order_no,
        "notifyUrl": NOTIFY_URL,
        "returnUrl": RETURN_URL,
        "payType": "BANK",
        "productName": "OTT Purchase"
    }
    payload["sign"] = generate_sign(payload)

    logger.info(f"\n📦 Payload: {payload}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(PAYMENT_URL, json=payload)
            res_json = response.json()
            logger.info(f"📨 FastPay Response: {res_json}")

            if res_json.get("code") == 200 and res_json.get("data"):
                pay_link = res_json["data"].get("payUrl")
                await update.message.reply_text(f"✅ Payment link generated:\n{pay_link}")
            else:
                await update.message.reply_text("❌ FastPay error. Please try again later.")
    except Exception as e:
        logger.error(f"❌ Request Error: {e}")
        await update.message.reply_text("❌ Server error. Contact admin.")

    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# Main
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("pay", pay_command)],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("🚀 Bot started")
    app.run_polling()

import logging
import hashlib
import uuid
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import requests

try:
    ip = requests.get("https://api.ipify.org").text
    print("🌐 Server Public IP:", ip)
except Exception as e:
    print("❌ IP fetch error:", str(e))


# ====== CONFIGURATION ======
BOT_TOKEN = "7603128499:AAHrUje-z46qOmqcGJ89GGFaCiR4toVxGA8"
MERCHANT_ID = "mer553833"
MERCHANT_KEY = "f760332dcb1dd887d4079754b52fdb2b"
PAY_URL = "https://api.fast-vip.com/api/payGate/payOrder"
RETURN_URL = "https://t.me/ott_heree"
NOTIFY_URL = "https://yourdomain.com/callback"  # Update this when you set webhook

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASK_AMOUNT = range(1)
pending_orders = {}

# === SIGN GENERATOR ===
def generate_sign(data: dict, key: str):
    sorted_data = sorted(data.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_data]) + f"&key={key}"
    return hashlib.md5(sign_str.encode()).hexdigest().upper()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome bhai! Type /pay to start a payment.")

# === /pay ===
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Bhai kitna pay karna hai? (Number me bhej)")

    return ASK_AMOUNT

# === Receive Amount and Create Real Payment Link ===
async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    try:
        amount = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Bhai sirf number bhejna. Example: 500")
        return ASK_AMOUNT

    order_no = f"OTT{int(time.time())}{str(uuid.uuid4())[:6]}"
    payload = {
        "merchantNo": MERCHANT_ID,
        "orderAmount": str(amount),
        "orderNo": order_no,
        "notifyUrl": NOTIFY_URL,
        "returnUrl": RETURN_URL,
        "payType": "BANK",  # ✅ Use "BANK" or whatever is enabled in your merchant
        "productName": "OTT Purchase"
    }
    payload["sign"] = generate_sign(payload, MERCHANT_KEY)

    print("\n📦 Payload:", payload)

    try:
        res = requests.post(PAY_URL, json=payload)
        res_json = res.json()
        print("📨 FastPay Response:", res_json)

        if res_json.get("code") == "200" and res_json.get("data"):
            pay_link = res_json["data"].get("payUrl")
            if not pay_link:
                await update.message.reply_text("❌ Link missing from FastPay response.")
                return ConversationHandler.END

            pending_orders[user_id] = {
                "order_id": order_no,
                "amount": amount
            }

            await update.message.reply_text(
                f"✅ Bhai yeh raha tera real payment link:\n\n"
                f"🧾 Order ID: `{order_no}`\n"
                f"💰 Amount: ₹{amount}\n"
                f"🔗 [Pay Now]({pay_link})\n\n"
                f"📩 *Payment karne ke baad likh:* `payment done`",
                parse_mode="Markdown", disable_web_page_preview=True
            )
            return ConversationHandler.END
        else:
            msg = res_json.get("msg") or "FastPay internal error"
            await update.message.reply_text(f"❌ FastPay Error: {msg}")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Request Error: {str(e)}")
        return ConversationHandler.END

# === "payment done" Handler ===
async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.lower()
    if "payment done" in text and user_id in pending_orders:
        order = pending_orders[user_id]
        await update.message.reply_text(
            f"✅ ₹{order['amount']} Payment Received Bhai!\n"
            f"🧾 Order ID: {order['order_id']}\n🎉 Thank you!"
        )
        del pending_orders[user_id]

# === Cancel ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Payment cancelled.")
    return ConversationHandler.END

# === MAIN ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("pay", pay)],
        states={ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("payment done"), check_payment))

    print("✅ Bot is running in LIVE mode...")
    app.run_polling()

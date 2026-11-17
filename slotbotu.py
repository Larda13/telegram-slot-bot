import asyncio
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER İÇİN MİNİ WEB SUNUCUSU (PORT DOLDURUCU) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Web sunucusunu ayrı bir arka plan thread'inde başlatıyoruz (Asenkronu bozmasın diye)
t = Thread(target=run_web_server)
t.daemon = True
t.start()

# --- 2. TELEGRAM BOT AYARLARI ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_data_db = {}

WINNING_VALUES = {
    1: {"name": "🍒 ÜÇLÜ BAR", "multiplier": 5},
    22: {"name": "🍇 ÜÇLÜ ÜZÜM", "multiplier": 10},
    43: {"name": "🍋 ÜÇLÜ LİMON", "multiplier": 15},
    64: {"name": "🎰 JACKPOT (777)", "multiplier": 50}
}

def get_user(user_id):
    if user_id not in user_data_db:
        user_data_db[user_id] = {"balance": 100}
    return user_data_db[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id)
    await update.message.reply_text(
        f"Merhaba **{user.first_name}**! Ekonomili Slot Botuna hoş geldin. 🎰\n\n"
        "Komutlar:\n"
        "💰 /bakiye - Bakiyeni gösterir\n"
        "🎁 /gunluk - Günlük 50 Coin alırsın\n"
        "📉 /iflasiyasa - Bakiyen 0'lanınca 50 Coin destek alırsın\n"
        "🎰 /slot [miktar] - Slot çevirirsin (Örn: /slot 10)",
        parse_mode="Markdown"
    )

async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    await update.message.reply_text(f"💰 Güncel Bakiyen: **{data['balance']} Coin**", parse_mode="Markdown")

async def gunluk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    data['balance'] += 50
    await update.message.reply_text(f"🎁 Günlük ödülün alındı! +50 Coin.\n💰 Yeni Bakiyen: **{data['balance']} Coin**", parse_mode="Markdown")

async def iflasiyasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    if data['balance'] <= 0:
        data['balance'] = 50
        await update.message.reply_text("📉 İflas ettin ama devlet yardım eli uzattı! +50 Coin aldın.", parse_mode="Markdown")
    else:
        await update.message.reply_text("😎 Bakiyen bitmemiş ki, ne iflası! Zengin sayılırsın.", parse_mode="Markdown")

async def play_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)

    if not context.args:
        await update.message.reply_text("⚠️ Lütfen bir bahis miktarı gir. Örnek: `/slot 10`", parse_mode="Markdown")
        return

    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Lütfen geçerli bir sayı gir.", parse_mode="Markdown")
        return

    if bet <= 0:
        await update.message.reply_text("⚠️ Bahis 0'dan büyük olmalıdır.", parse_mode="Markdown")
        return

    if data['balance'] < bet:
        await update.message.reply_text(f"❌ Yetersiz bakiye! Mevcut bakiyen: {data['balance']} Coin", parse_mode="Markdown")
        return

    data['balance'] -= bet
    msg = await update.message.reply_dice(emoji="🎰")
    slot_value = msg.dice.value

    await asyncio.sleep(2)

    if slot_value in WINNING_VALUES:
        reward_info = WINNING_VALUES[slot_value]
        win_amount = bet * reward_info["multiplier"]
        data["balance"] += win_amount
        result_text = (
            f"🔥 **{user.first_name} KAZANDI!** ({reward_info['name']})\n"
            f"🎁 Kazanç: **+{win_amount} Coin**\n"
            f"💰 Güncel Bakiye: **{data['balance']} Coin**"
        )
    else:
        result_text = (
            f"❌ **{user.first_name}**, maalesef tutmadı (-{bet} Coin).\n"
            f"💰 Kalan Bakiye: **{data['balance']} Coin**"
        )

    await update.message.reply_text(result_text, parse_mode="Markdown")

if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    
    async def main():
        application = ApplicationBuilder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("bakiye", bakiye))
        application.add_handler(CommandHandler("gunluk", gunluk))
        application.add_handler(CommandHandler("iflasiyasa", iflasiyasa))
        application.add_handler(CommandHandler("slot", play_slot))
        
        print("Ekonomili Slot Botu başlatılıyor...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        # Botun kapanmaması için sonsuz döngü
        await asyncio.Event().wait()

    asyncio.run(main())

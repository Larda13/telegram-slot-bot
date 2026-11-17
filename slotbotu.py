import asyncio
import logging
import random
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Oyuncuların bakiyelerini tutacağımız hafıza (Sözlük)
user_data_db = {}

# Telegram slot (🎰) kazanan değerleri ve çarpanları
WINNING_VALUES = {
    1: {"name": "🍒 ÜÇLÜ BAR", "multiplier": 5},      # Bahsin 5 katı
    22: {"name": "🍇 ÜÇLÜ ÜZÜM", "multiplier": 10},  # Bahsin 10 katı
    43: {"name": "🍋 ÜÇLÜ LİMON", "multiplier": 15}, # Bahsin 15 katı
    64: {"name": "🎰 JACKPOT (777)", "multiplier": 50} # Bahsin 50 katı
}

def get_user(user_id):
    """Kullanıcı veritabanında yoksa başlangıç bakiyesiyle (100 Coin) ekle"""
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
    # Basitlik olması açısından direkt ekliyoruz
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

    # Bahis miktarını kontrol et
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

    # Bakiyeden bahsi düş
    data['balance'] -= bet

    # Telegram'ın resmi animasyonlu slot zarını at
    msg = await update.message.reply_dice(emoji="🎰")
    slot_value = msg.dice.value

    # Kısa bir bekleme (zar animasyonu tamamlansın diye)
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
        
        print("Ekonomili Slot Botu çalışıyor...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

    asyncio.run(main())

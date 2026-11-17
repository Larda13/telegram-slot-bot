import asyncio
import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Oyuncuların bakiyelerini tutacağımız hafıza (Sözlük)
user_data_db = {}

# Telegram slot (🎰) kazanan değerleri ve çarpanları
WINNING_VALUES = {
    1: {"name": "🍫 ÜÇLÜ BAR", "multiplier": 5},     # Bahsin 5 katı
    22: {"name": "🍇 ÜÇLÜ ÜZÜM", "multiplier": 10}, # Bahsin 10 katı
    43: {"name": "🍋 ÜÇLÜ LİMON", "multiplier": 15},# Bahsin 15 katı
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
        f"🎰 **Slot Kumarhanesine Hoş Geldin, {user.first_name}!**\n\n"
        f"💰 Başlangıç bakiyen: **100 Coin**\n"
        f"🎮 Komutlar:\n"
        f"• `/bakiye` - Cüzdanını kontrol et\n"
        f"• `/slot [bahis]` - Slot çevir (Örn: `/slot 10`)\n"
        f"• `/gunluk` - Günlük ücretsiz **100 Coin** al\n"
        f"• `/iflasiyasa` - Parın bittiyse cüzi yardım al (30 Coin)",
        parse_mode="Markdown"
    )

async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    await update.message.reply_text(f"💳 Cüzdanın: **{data['balance']} Coin** 🪙", parse_mode="Markdown")

async def gunluk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    
    # Günlük ödülü 100 coin yaptık
    data["balance"] += 100
    await update.message.reply_text(
        f"🎁 Günlük 100 Coin ödülün hesabına eklendi, **{user.first_name}**!\n"
        f"💰 Yeni bakiyen: **{data['balance']} Coin** 🎉",
        parse_mode="Markdown"
    )

async def iflasiyasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    
    if data["balance"] > 20:
        await update.message.reply_text("Eyvah! Paran henüz tamamen bitmemiş. Bakiyen 20 coin'in altındayken bu komutu kullanabilirsin.")
        return
    
    # İflas yardım sandığı (30 coin)
    data["balance"] += 30
    await update.message.reply_text(
        f"🚑 İflas yardım sandığından cüzi bir miktar (30 Coin) bağışlandı!\n"
        f"💰 Yeni bakiyen: **{data['balance']} Coin**. Akıllı harca!",
        parse_mode="Markdown"
    )

async def play_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    
    args = context.args
    bet = 10
    if args:
        try:
            bet = int(args[0])
        except ValueError:
            pass
            
    if bet <= 0:
        await update.message.reply_text("Geçersiz bahis miktarı!")
        return

    if data["balance"] < bet:
        await update.message.reply_text(
            f"❌ Yetersiz bakiye! Cüzdanında {data['balance']} Coin var.\n"
            f"Yardım almak için `/iflasiyasa` yazabilirsin.",
            parse_mode="Markdown"
        )
        return

    # Bahis ücretini hesaptan düş
    data["balance"] -= bet

    # Slot makinesini gönder
    dice_message = await update.message.reply_dice(emoji="🎰")
    slot_value = dice_message.dice.value

    # Animasyonun durması için 2 saniye bekle
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

import asyncio

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

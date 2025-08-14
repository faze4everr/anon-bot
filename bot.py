import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from datetime import datetime

# Logger sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Muhim sozlamalar (Render yoki lokal muhitta ENV dan o‘qiladi)
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
ACCESS_KEY = os.environ.get("ACCESS_KEY", "f217t599u11O21")

# Javob rejimi saqlash uchun
reply_mode = {}  # {admin_id: user_id}

# O‘zbekcha oy nomlari
UZBEK_MONTHS = {
    1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel",
    5: "may", 6: "iyun", 7: "iyul", 8: "avgust",
    9: "sentabr", 10: "oktabr", 11: "noyabr", 12: "dekabr"
}

def format_date_uz(dt: datetime):
    oy_nomi = UZBEK_MONTHS[dt.month]
    return f"{dt.year}-yil {dt.day}-{oy_nomi}, {dt.strftime('%H:%M')}"

class AnonymousBot:
    def __init__(self, token: str, admin_id: int, access_key: str):
        self.token = token
        self.admin_id = admin_id
        self.access_key = access_key
        self.application = Application.builder().token(token).build()
        self.authorized_users = set()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if context.args:
            provided_key = context.args[0]
            if provided_key == self.access_key:
                self.authorized_users.add(user_id)
                await update.message.reply_text(
                    "🔒 *Anonim Xabar Botiga xush kelibsiz!*\n\n"
                    "Siz endi menga anonim xabar yuborishingiz mumkin.\n"
                    "Shunchaki xabaringizni yozib yuboring — men uni *admin*ga jo‘nataman.\n\n"
                    "📋 *Qo‘llab-quvvatlanadigan turlar:*\n"
                    "• Matn xabarlari\n"
                    "• Rasm va videolar\n"
                    "• Hujjat va fayllar\n"
                    "• Ovozli va audio xabarlar\n"
                    "• Stikerlar",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Yaroqsiz maxfiy kalit.\nIltimos, to‘g‘ri taklif havolasidan foydalaning.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "🔒 *Ruxsat talab qilinadi*\n\n"
                "Bu botdan foydalanish uchun maxsus taklif havolasi kerak.\n"
                "Agar havolangiz bo‘lmasa, bot egasiga murojaat qiling.",
                parse_mode='Markdown'
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.authorized_users:
            await update.message.reply_text(
                "🔒 Avval /start buyrug‘i va maxfiy kalit bilan kirishingiz kerak.",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_text(
            "📋 *Botdan foydalanish yo‘riqnomasi:*\n\n"
            "• Xabaringizni yozing va yuboring\n"
            "• U anonim tarzda admin ga yetkaziladi\n"
            "• Ruxsat etilgan turlar: matn, rasm, video, hujjat, ovozli\n"
            "• /start — xush kelibsiz xabarini qayta ko‘rish",
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.message
        user_id = user.id

        if user_id == self.admin_id and self.admin_id in reply_mode:
            target_user_id = reply_mode[self.admin_id]
            try:
                await context.bot.send_message(chat_id=target_user_id, text=message.text or "")
                await message.reply_text(
                    "✅ Javobingiz yuborildi.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⏹ Javobni to‘xtatish", callback_data="stop_reply")]
                    ])
                )
            except Exception as e:
                logger.error(f"Javob yuborishda xato: {e}")
                await message.reply_text("❌ Xatolik yuz berdi. Javob yuborilmadi.")
            return

        if user_id == self.admin_id:
            await message.reply_text("👋 Salom admin! Siz yuborgan xabarlar o‘zingizga jo‘natilmaydi.")
            return

        if user_id not in self.authorized_users:
            await message.reply_text(
                "🔒 Sizda ruxsat yo‘q.\nIltimos, maxsus havola orqali botga kiring.",
                parse_mode='Markdown'
            )
            return

        sana = format_date_uz(message.date)
        user_info = (
            "📨 *Yangi anonim xabar*\n\n"
            f"*Ismi:* {user.first_name or 'Noma’lum'} {user.last_name or ''}\n"
            f"*Foydalanuvchi nomi:* @{user.username or 'Yo‘q'}\n"
            f"*ID:* `{user_id}`\n"
            f"*Sana:* {sana}\n\n"
            "*Xabar:*"
        )

        try:
            if message.text:
                await context.bot.send_message(
                    chat_id=self.admin_id,
                    text=user_info + f"\n{message.text}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✉ Javob berish", callback_data=f"reply_{user_id}")]
                    ])
                )
            elif message.photo:
                await context.bot.send_message(
                    chat_id=self.admin_id, text=user_info, parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✉ Javob berish", callback_data=f"reply_{user_id}")]
                    ])
                )
                await context.bot.send_photo(
                    chat_id=self.admin_id, photo=message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            else:
                await context.bot.send_message(
                    chat_id=self.admin_id,
                    text=user_info + "\n*[Qo‘llab-quvvatlanmagan tur]*",
                    parse_mode='Markdown'
                )

            await message.reply_text("✅ Xabaringiz anonim tarzda yuborildi.")

        except Exception as e:
            logger.error(f"Xabar yuborishda xato: {e}")
            await message.reply_text("❌ Kechirasiz, xabar yuborishda xato yuz berdi.")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data.startswith("reply_"):
            target_user_id = int(query.data.split("_")[1])
            reply_mode[self.admin_id] = target_user_id
            await query.edit_message_reply_markup()
            await query.message.reply_text(
                "✏ Endi ushbu foydalanuvchiga javob yuborishingiz mumkin.\n"
                "Javobingizni yozib yuboring."
            )
        elif query.data == "stop_reply":
            if self.admin_id in reply_mode:
                del reply_mode[self.admin_id]
                await query.message.reply_text("⏹ Javob rejimi to‘xtatildi.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Xato: {context.error}")

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_error_handler(self.error_handler)

    def run(self):
        self.setup_handlers()
        print("🤖 Bot ishga tushmoqda...")
        self.application.run_polling(drop_pending_updates=True)

def main():
    bot = AnonymousBot(BOT_TOKEN, ADMIN_CHAT_ID, ACCESS_KEY)
    bot.run()

if __name__ == "__main__":
    main()

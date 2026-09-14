import os
import asyncio
import threading
import http.server
import socketserver
import logging
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "8938997589:AAHac3AbBUvhxTBTq6nj8UQkV-2K2MUB-qc"
ADMIN_CHAT_ID = -1003958495436

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

STATE_VERIFY_ID = 1

# Fungsi Web Server untuk Render
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Bot KPPbNB is Alive!")
        def log_message(self, format, *args):
            return

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
            print(f"Web server aktif di port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server note: {e}")

# Fungsi Membaca Fail ahli.csv
def baca_data_ahli(no_pekerja_dicari):
    try:
        if not os.path.exists("ahli.csv"):
            return None
        with open("ahli.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["no_pekerja"].strip() == str(no_pekerja_dicari).strip():
                    return {
                        "nama": row["nama"].strip(),
                        "lokasi": row["lokasi"].strip()
                    }
    except Exception as e:
        logging.error(f"Ralat baca CSV: {e}")
    return None

# Menu Utama Sementara
def get_main_keyboard():
    keyboard = [[InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]]
    return InlineKeyboardMarkup(keyboard)

# Langkah 1: Mula bot minta No Pekerja
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔐 *PENGESAHAN KEAHLIAN KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Selamat datang ke Bot Rasmi KPPbNB BERNAS.\n\n"
        "👉 Sila masukkan *Nombor Pekerja* sah anda untuk meneruskan:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    return STATE_VERIFY_ID

# Langkah 2: Semak No Pekerja & Hantar Notis ke Group jika Gagal
async def verify_employee_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emp_id = update.message.text.strip()
    user = update.effective_user

    data_ahli = baca_data_ahli(emp_id)

    if data_ahli:
        context.user_data['emp_id'] = emp_id
        context.user_data['nama'] = data_ahli['nama']
        context.user_data['lokasi'] = data_ahli['lokasi']
        context.user_data['verified'] = True
        
        welcome_text = (
            f"Hi *{data_ahli['nama']}*! 👋\n\n"
            "✅ *PENGESAHAN BERJAYA!*\n"
            "Keahlian anda disahkan aktif. Sila pilih perkhidmatan di bawah:"
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        return ConversationHandler.END
    else:
        # Notifikasi amaran ke Group Aduan KPPbNB
        notis_admin = (
            "🚨 *PERCUBAAN AKSES BOT TIDAK SAH*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Nama Telegram:* {user.full_name} (@{user.username or 'Tiada'})\n"
            f"🆔 *Telegram ID:* `{user.id}`\n"
            f"🔢 *No. Pekerja Dimasukkan:* `{emp_id}`\n"
            "⚠️ *Status:* Gagal disahkan (Tiada dalam fail CSV induk)."
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notis_admin, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Gagal hantar notis keselamatan ke group: {e}")

        error_text = (
            "❌ *RALAT: NOMBOR PEKERJA TIDAK DIJUMPAI*\n\n"
            "Nombor pekerja anda tiada dalam rekod keahlian aktif KPPbNB.\n"
            "Notifikasi kegagalan telah disalurkan kepada pihak pentadbir.\n\n"
            "📞 Sila hubungi Setiausaha Agung (Pn. Farah Aqilah: aqilah@bernas.com.my) untuk bantuan.\n\n"
            "Sila cuba masukkan semula Nombor Pekerja yang sah:"
        )
        await update.message.reply_text(error_text, parse_mode='Markdown')
        return STATE_VERIFY_ID

# Main Runner
async def async_main():
    threading.Thread(target=run_web_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    verify_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_VERIFY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_employee_id)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(verify_conv)

    async with app:
        await app.start()
        await app.updater.start_polling()
        print("Bot Asas KPPbNB LIVE!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()

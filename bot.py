import os
import asyncio
import threading
import http.server
import socketserver
import logging
import csv
import time
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

# Fungsi Semak Adakah Sesi Masih Aktif (< 15 Minit / 900 Saat)
def is_session_active(context: ContextTypes.DEFAULT_TYPE) -> bool:
    verified = context.user_data.get('verified', False)
    last_active = context.user_data.get('last_active', 0)
    if verified and (time.time() - last_active < 900):
        context.user_data['last_active'] = time.time()  # Perbarui masa aktif setiap kali berinteraksi
        return True
    return False

# ==================== KEYBOARD MENU UTAMA ====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Akta & Peraturan", callback_data='menu_akta'),
         InlineKeyboardButton("📋 CA7", callback_data='menu_ca')],
        [InlineKeyboardButton("🧮 Kiraan OT & Elaun", callback_data='menu_kiraan'),
         InlineKeyboardButton("📝 Laporan / Aduan", callback_data='menu_aduan')],
        [InlineKeyboardButton("📢 Hebahan Kesatuan", callback_data='menu_hebahan'),
         InlineKeyboardButton("📚 Dokumen Kesatuan", callback_data='menu_dokumen')],
        [InlineKeyboardButton("👤 Profil Saya", callback_data='menu_profil'),
         InlineKeyboardButton("☎️ Hubungi Kesatuan", callback_data='menu_hubungi')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]])

# Langkah 1: Mula bot minta No Pekerja (Semak Sesi 15 Minit)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_session_active(context):
        nama = context.user_data.get('nama', 'Ahli')
        text = f"Hi kembali, *{nama}*! 👋\n\nSesi anda masih aktif. Sila pilih perkhidmatan di bawah:"
        if update.message:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        return ConversationHandler.END

    text = (
        "🔐 *PENGESAHAN KEAHLIAN KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Sesi anda telah tamat tempoh (selepas 15 minit) atau belum disahkan.\n\n"
        "👉 Sila masukkan *Nombor Pekerja* sah anda untuk meneruskan:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    return STATE_VERIFY_ID

# Langkah 2: Semak No Pekerja & Set Masa Sesi Aktif
async def verify_employee_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emp_id = update.message.text.strip()
    user = update.effective_user

    data_ahli = baca_data_ahli(emp_id)

    if data_ahli:
        context.user_data['emp_id'] = emp_id
        context.user_data['nama'] = data_ahli['nama']
        context.user_data['lokasi'] = data_ahli['lokasi']
        context.user_data['verified'] = True
        context.user_data['last_active'] = time.time()  # Rekod masa mula log masuk
        
        welcome_text = (
            f"Hi *{data_ahli['nama']}*! 👋\n\n"
            "✅ *PENGESAHAN BERJAYA!*\n"
            "Keahlian anda disahkan aktif. Sila pilih perkhidmatan di bawah:"
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        return ConversationHandler.END
    else:
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

# Handler Callback untuk Butang Menu Utama (Kemas kini masa aktif sesi)
async def handle_menu_utama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_session_active(context):
        await query.message.reply_text("🔐 Sesi anda telah tamat tempoh selepas 15 minit tidak aktif. Sila taip /start semula.")
        return

    nama = context.user_data.get('nama', 'Ahli')
    text = f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:"
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())

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
    app.add_handler(CallbackQueryHandler(handle_menu_utama, pattern='^menu_utama$'))

    async with app:
        await app.start()
        await app.updater.start_polling()
        print("Bot KPPbNB LIVE dengan Timeout Sesi 15 Minit!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()
def get_akta_keyboard():
    keyboard = [
        [InlineKeyboardButton("⏰ Waktu Bekerja (Sek 60A)", callback_data='akta_waktu'),
         InlineKeyboardButton("🧮 Kerja Lebih Masa (OT)", callback_data='akta_ot')],
        [InlineKeyboardButton("🏖️ Cuti Bergaji & Cuti Am", callback_data='akta_cuti'),
         InlineKeyboardButton("🏥 Cuti Sakit & Wad (Sek 60F)", callback_data='akta_mc')],
        [InlineKeyboardButton("💰 Pembayaran & Potongan Gaji", callback_data='akta_gaji'),
         InlineKeyboardButton("⚠️ AWOL & Disiplin (Sek 14/15)", callback_data='akta_awol')],
        [InlineKeyboardButton("🚪 Penamatan Kontrak & Faedah", callback_data='akta_tamat'),
         InlineKeyboardButton("🦺 Keselamatan & Hak OSHA", callback_data='akta_osha')],
        [InlineKeyboardButton("🛡️ Skim Bencana PERKESO", callback_data='akta_perkeso')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ca_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 Gaji, Bonus & Pelarasan", callback_data='ca_gaji'),
         InlineKeyboardButton("⏰ Waktu Bekerja (Art 29)", callback_data='ca_waktu_kerja')],
        [InlineKeyboardButton("🧮 Kerja Lebih Masa (Art 30 & 31)", callback_data='ca_ot')],
        [InlineKeyboardButton("🍱 Elaun Makan Gaji ≥RM4k (Art 64.3)", callback_data='ca_elaun_4k_menu')],
        [InlineKeyboardButton("🏖️ Cuti Tahunan, Haji & Ehsan", callback_data='ca_cuti'),
         InlineKeyboardButton("🚗 Perbatuan (Mileage) & Elaun", callback_data='ca_elaun')],
        [InlineKeyboardButton("🏥 Faedah Rawatan & Hospital", callback_data='ca_perubatan'),
         InlineKeyboardButton("👨‍👩‍👧 Kebajikan & Beras", callback_data='ca_kebajikan')],
        [InlineKeyboardButton("📊 Struktur Tangga Gaji (T & S)", callback_data='ca_gred')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_elaun_4k_keyboard():
    keyboard = [
        [InlineKeyboardButton("📍 Panduan Zon A", callback_data='art64_zona'),
         InlineKeyboardButton("📍 Panduan Zon B", callback_data='art64_zonb')],
        [InlineKeyboardButton("🔄 Panduan Staf Syif", callback_data='art64_syif')],
        [InlineKeyboardButton("🔙 Kembali ke Menu CA7", callback_data='menu_ca')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== MODUL AKTA & PERATURAN ====================
async def handle_akta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_akta':
        text = "📖 *1. AKTA & PERATURAN KERJA MALAYSIA*\n\nPilih topik statutori di bawah untuk rujukan terperinci:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_waktu':
        text = (
            "⏰ *AKTA KERJA 1955: WAKTU BEKERJA (SEKSYEN 60A)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Ketetapan Undang-undang:*\n"
            "• Had maksimum waktu kerja biasa ialah *45 jam seminggu*.\n"
            "• Pekerja tidak boleh diarahkan bekerja lebih daripada *8 jam sehari* tanpa dikira sebagai OT.\n"
            "• Masa rehat minimum wajib diberikan sekurang-kurangnya *30 minit* bagi setiap 5 jam kerja berterusan.\n\n"
            "📌 *Rujukan Bandingan CA-7 BERNAS (Artikel 29):*\n"
            "• Purata 39 jam seminggu bagi bukan syif dan 42 jam seminggu bagi pekerja syif."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_ot':
        text = (
            "🧮 *AKTA KERJA 1955: KERJA LEBIH MASA / OT (SEKSYEN 60A)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Kadar Bayaran Rasmi Akta:*\n"
            "• *Hari Bekerja Biasa:* 1.5x daripada kadar gaji sejam.\n"
            "• *Hari Rehat:* 2.0x | *Cuti Am:* 3.0x.\n"
            "• Had maksimum OT: *104 jam sebulan*."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_cuti':
        text = (
            "🏖️ *AKTA KERJA 1955: KELAYAKAN CUTI BERGAJI (SEKSYEN 60E)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Kelebihan CA-7 BERNAS (Artikel 44):*\n"
            "  👉 Khidmat < 2 tahun: *18 hari*\n"
            "  👉 Khidmat 2 - 5 tahun: *22 hari*\n"
            "  👉 Khidmat > 5 tahun: *24 hari*"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_mc':
        text = (
            "🏥 *AKTA KERJA 1955: CUTI SAKIT & WAD (SEKSYEN 60F)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 Cuti Masuk Wad diasingkan sehingga *60 hari setahun*.\n"
            "📌 Wajib maklumkan kepada majikan dalam tempoh *48 jam*."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_gaji':
        text = (
            "💰 *AKTA KERJA 1955: PEMBAYARAN GAJI (SEK 19 & 24)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 Gaji wajib dibayar selewat-lewatnya pada *hari ke-7* selepas tamat tempoh sebulan kerja."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_awol':
        text = (
            "⚠️ *AWOL & DISIPLIN (SEK 14 & 15)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 Tidak hadir >2 hari berturut-turut tanpa alasan dikira pecah kontrak. Siasatan adil wajib dijalankan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_tamat':
        text = (
            "🚪 *PENAMATAN KONTRAK & NOTIS (SEK 12)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 Notis mengikut tempoh perkhidmatan (4 minggu hingga 8 minggu)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_osha':
        text = (
            "🦺 *OSHA 1994 (SEKSYEN 26A)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 Hak pekerja menolak kerja berisiko tinggi atau bahaya ketara di tempat kerja."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_perkeso':
        text = (
            "🛡️ *PERKESO (SKIM BENCANA PEKERJAAN)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 Melindungi kemalangan di tempat kerja serta kemalangan perjalanan pergi/balik bertugas."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

# ==================== MODUL CA-7 ====================
async def handle_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_ca':
        text = "📋 *2. PERJANJIAN BERSAMA KE-7 (CA-7)*\nPilih klausa perjanjian:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_gaji':
        text = "💰 *CA-7: GAJI & BONUS (ART 25 & 26)*\n• Kenaikan tahunan berdasarkan prestasi + Bonus 1 bulan gaji asas."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_waktu_kerja':
        text = "⏰ *CA-7: WAKTU BEKERJA (ART 29)*\n• Bukan syif 39 jam | Syif 42 jam seminggu."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_ot':
        text = "🧮 *CA-7: OT & CUTI GANTIAN (ART 30 & 31)*\n• Kelayakan Gred T & S bawah RM4,000."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_elaun_4k_menu':
        text = "🍱 *CA-7: ELAUN MAKAN GAJI ≥ RM4,000*\nPilih zon anda:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())
    elif data in ['art64_zona', 'art64_zonb', 'art64_syif']:
        text = "🍱 *ARTIKEL 64.3: ELAUN MAKAN*\n• 2-5 jam: RM25 | >5 jam: RM50."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_cuti':
        text = "🏖️ *CA-7: CUTI KHAS*\n• Haji: 54 hari | Bersalin: 98 hari | Paterniti: 7 hari."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_elaun':
        text = "🚗 *CA-7: ELAUN*\n• Kereta: RM0.75/km | Motor: RM0.50/km | Luar Stesen: RM115/hari."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_perubatan':
        text = "🏥 *CA-7: PERUBATAN*\n• Pesakit Luar: RM3,500 | Wad (2027): RM45,000/individu."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_kebajikan':
        text = "👨‍👩‍👧 *CA-7: KEBAJIKAN*\n• Beras: 2 kampit (10kg)/bulan | Insurans: 36 bulan gaji."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_gred':
        text = (
            "📊 *CA-7: STRUKTUR TANGGA GAJI (LAMPIRAN I)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔧 *Gred T (Teknikal):* T1 (RM1.7k-2.8k) hingga T5 (RM3.0k-6.3k)\n"
            "💼 *Gred S (Sokongan):* S1 (RM1.7k-2.8k) hingga S5 (RM2.8k-5.4k)"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

# ==================== MODUL LAIN (DOKUMEN, PROFIL, HUBUNGI) ====================
async def handle_other_menus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_dokumen':
        text = "📚 *PUSAT DOKUMEN & MUAT TURUN KESATUAN*\nPilih dokumen rasmi:"
        keyboard = [
            [InlineKeyboardButton("📄 Borang Kilanan Rasmi", url=URL_KILANAN)],
            [InlineKeyboardButton("📘 Buku CA-1", url=URL_CA1), InlineKeyboardButton("📗 Buku CA-2", url=URL_CA2)],
            [InlineKeyboardButton("📙 Buku CA-3", url=URL_CA3), InlineKeyboardButton("📕 Buku CA-4", url=URL_CA4)],
            [InlineKeyboardButton("📒 Buku CA-5", url=URL_CA5), InlineKeyboardButton("📓 Buku CA-6", url=URL_CA6)],
            [InlineKeyboardButton("📜 Buku Akta Kerja", url=URL_AKTA)],
            [InlineKeyboardButton("⚖️ Buku Tatatertib BERNAS Edisi 5", url=URL_TATATERTIB)],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
        ]
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'menu_hebahan':
        text = "📢 *HEBAHAN KESATUAN*\n• Perjanjian Bersama CA-7 berkuatkuasa bagi tahun 2026 – 2028."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_profil':
        emp_id = context.user_data.get('emp_id', 'Tidak Diketahui')
        nama = context.user_data.get('nama', 'Belum Disahkan')
        lokasi = context.user_data.get('lokasi', 'Tidak Diketahui')
        text = (
            "👤 *PROFIL AHLI KESATUAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Nama: *{nama}*\n"
            f"No. Pekerja: `{emp_id}`\n"
            f"Lokasi: *{lokasi}*\n"
            "Status: 🟢 *Aktif (Disahkan)*"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_hubungi':
        text = (
            "☎️ *HUBUNGI KESATUAN (KPPbNB)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏛️ No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah.\n\n"
            "📌 *Pimpinan Utama:*\n"
            "• Presiden: En. Syahibudil Assaufi\n"
            "• Setiausaha Agung: Pn. Farah Aqilah\n"
            "• Bendahari: En. Khairul Faiz"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_utama':
        nama = context.user_data.get('nama', 'Ahli')
        text = f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())

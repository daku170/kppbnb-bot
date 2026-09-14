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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN belum ditetapkan dalam Environment Variables")
ADMIN_CHAT_ID = -1003958495436

# Pautan Dokumen Google Drive & SharePoint
URL_KILANAN = "https://drive.google.com/file/d/1KLmiSGJcnV_Wmcwkfyj6LZ17KGdJp92w/view?usp=drive_link"
URL_CA1 = "https://drive.google.com/file/d/1s0KkAqdb2i2XMAg8HgoEvh0tWhiTMcYB/view?usp=drive_link"
URL_CA2 = "https://drive.google.com/file/d/1piIG4_2V8o0ZpQhpvf6pUo9kJutKUKXr/view?usp=drive_link"
URL_CA3 = "https://drive.google.com/file/d/1ZyaSF0CoaY_jrgCS8C2I53kTVC1qb__X/view?usp=drive_link"
URL_CA4 = "https://drive.google.com/file/d/1Hro24UiRlpAP7xQpQ_iuo0iyAMszorFt/view?usp=drive_link"
URL_CA5 = "https://drive.google.com/file/d/1Z41lso7fi3GlVG_UvGpncUkIndN1GaL3/view?usp=drive_link"
URL_CA6 = "https://drive.google.com/file/d/19kQw-6Klinuq1ErF-raLs8-9xoosYroi/view?usp=drive_link"
URL_AKTA = "https://drive.google.com/file/d/1zR2l8JhjjP5udVwnpaq9v_iVuZrreJ-g/view?usp=sharing"
URL_TATATERTIB = "https://padiberasnasional.sharepoint.com/sites/RiCentre/Prosedur%20Operasi%20Standard%20HR/Forms/AllItems.aspx?id=%2Fsites%2FRiCentre%2FProsedur%20Operasi%20Standard%20HR%2FHRD%2DIR%2D50%2DSOP%2D01%2DE%20PERATURAN%20DAN%20PROSEDUR%20TATATERTIB%20BAGI%20BERNAS%20EDISI%20KELIMA%2Epdf&parent=%2Fsites%2FRiCentre%2FProsedur%20Operasi%20Standard%20HR"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

STATE_VERIFY_ID = 1
STATE_OT_ZONE = 2
STATE_OT_DAY = 3
STATE_OT_SALARY = 4
STATE_OT_HOURS = 5
STATE_ADUAN_JENIS = 6
STATE_ADUAN_KETERANGAN = 7
STATE_MINAT_NAMA = 8
STATE_MINAT_PEKERJA = 9
STATE_MINAT_LOKASI = 10
STATE_MINAT_JAWATAN = 11
STATE_MINAT_TELEFON = 12
STATE_MINAT_EMAIL = 13
STATE_MINAT_PERTANYAAN = 14
STATE_SAHABAT_SOALAN = 15

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
        context.user_data['last_active'] = time.time()
        return True
    return False

# ==================== KEYBOARDS ====================
def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Saya Ahli KPPbNB", callback_data='start_ahli')],
        [InlineKeyboardButton("🤝 Berminat Menjadi Ahli", callback_data='minat_ahli')]
    ])

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Akta & Peraturan", callback_data='menu_akta'),
         InlineKeyboardButton("📋 CA7", callback_data='menu_ca')],
        [InlineKeyboardButton("🧮 Kiraan OT & Elaun", callback_data='menu_kiraan'),
         InlineKeyboardButton("📝 Laporan / Aduan", callback_data='menu_aduan')],
        [InlineKeyboardButton("🤝 Sahabat KPPbNB", callback_data='menu_sahabat')],
        [InlineKeyboardButton("📢 Hebahan Kesatuan", callback_data='menu_hebahan'),
         InlineKeyboardButton("📚 Dokumen Kesatuan", callback_data='menu_dokumen')],
        [InlineKeyboardButton("👤 Profil Saya", callback_data='menu_profil'),
         InlineKeyboardButton("☎️ Hubungi Kesatuan", callback_data='menu_hubungi')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]])

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
        [InlineKeyboardButton("💰 Gaji & Kenaikan Gaji", callback_data='ca_gaji'),
         InlineKeyboardButton("⏰ Waktu Kerja & OT", callback_data='ca_waktu_ot')],
        [InlineKeyboardButton("🏖️ Cuti", callback_data='ca_cuti'),
         InlineKeyboardButton("🏥 Perubatan", callback_data='ca_perubatan')],
        [InlineKeyboardButton("📈 Kenaikan Pangkat & Gred", callback_data='ca_pangkat'),
         InlineKeyboardButton("🚫 Ketidakhadiran / AWOL", callback_data='ca_awol')],
        [InlineKeyboardButton("📊 Struktur Tangga Gaji S & T", callback_data='ca_gred')],
        [InlineKeyboardButton("⚖️ Disiplin", callback_data='ca_disiplin'),
         InlineKeyboardButton("🚗 Elaun", callback_data='ca_elaun')],
        [InlineKeyboardButton("🦺 Keselamatan & Kemalangan", callback_data='ca_keselamatan'),
         InlineKeyboardButton("👥 Kesatuan", callback_data='ca_kesatuan')],
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

# ==================== HANDLERS PENGESAHAN ====================
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
        "👋 *SELAMAT DATANG KE BOT KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Sila pilih pilihan di bawah untuk meneruskan:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_start_keyboard())
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_start_keyboard())
    return ConversationHandler.END

async def handle_start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'start_ahli':
        await query.message.reply_text(
            "🔐 *PENGESAHAN KEAHLIAN KPPbNB*\n\n👉 Sila masukkan *Nombor Pekerja* sah anda:",
            parse_mode='Markdown'
        )
        return STATE_VERIFY_ID
    context.user_data.clear()
    await query.message.reply_text(
        "🤝 *BERMINAT MENJADI AHLI KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Terima kasih kerana berminat untuk menyertai Kesatuan.\n\n"
        "Maklumat ini akan digunakan oleh pihak Kesatuan untuk menghubungi anda dan menerangkan proses keahlian.\n\n"
        "👤 Sila masukkan *nama penuh*:", parse_mode='Markdown'
    )
    return STATE_MINAT_NAMA

async def minat_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_nama'] = update.message.text.strip()
    await update.message.reply_text("🆔 Sila masukkan *No. Pekerja*:", parse_mode='Markdown')
    return STATE_MINAT_PEKERJA

async def minat_pekerja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_pekerja'] = update.message.text.strip()
    await update.message.reply_text("🏢 Sila masukkan *lokasi / tempat bertugas*:", parse_mode='Markdown')
    return STATE_MINAT_LOKASI

async def minat_lokasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_lokasi'] = update.message.text.strip()
    await update.message.reply_text("💼 Sila masukkan *jawatan / gred*:", parse_mode='Markdown')
    return STATE_MINAT_JAWATAN

async def minat_jawatan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_jawatan'] = update.message.text.strip()
    await update.message.reply_text("📱 Sila masukkan *No. Telefon*:", parse_mode='Markdown')
    return STATE_MINAT_TELEFON

async def minat_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_telefon'] = update.message.text.strip()
    await update.message.reply_text("📧 Sila masukkan *Email*:", parse_mode='Markdown')
    return STATE_MINAT_EMAIL

async def minat_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_email'] = update.message.text.strip()
    await update.message.reply_text("💬 Jika ada, nyatakan *pertanyaan / sebab berminat*. Jika tiada, taip `Tiada`.", parse_mode='Markdown')
    return STATE_MINAT_PERTANYAAN

async def minat_pertanyaan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['minat_pertanyaan'] = update.message.text.strip()
    user = update.effective_user
    masa = time.strftime('%d/%m/%Y %H:%M:%S')
    text = (
        "🤝 *MINAT MENJADI AHLI KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Nama:* {context.user_data.get('minat_nama')}\n"
        f"🆔 *No. Pekerja:* {context.user_data.get('minat_pekerja')}\n"
        f"🏢 *Lokasi:* {context.user_data.get('minat_lokasi')}\n"
        f"💼 *Jawatan/Gred:* {context.user_data.get('minat_jawatan')}\n"
        f"📱 *Telefon:* {context.user_data.get('minat_telefon')}\n"
        f"📧 *Email:* {context.user_data.get('minat_email')}\n"
        f"💬 *Pertanyaan/Sebab:* {context.user_data.get('minat_pertanyaan')}\n\n"
        f"🕐 *Tarikh/Masa:* {masa}\n"
        f"🆔 *Telegram ID:* `{user.id}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *Tindakan:* Sila hubungi pemohon untuk penerangan lanjut."
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode='Markdown')
        await update.message.reply_text(
            "✅ *TERIMA KASIH!*\n\nMaklumat minat anda telah dihantar kepada pihak Kesatuan. Pihak KPPbNB akan menghubungi anda untuk penerangan lanjut.",
            parse_mode='Markdown', reply_markup=get_start_keyboard()
        )
    except Exception as e:
        logging.error(f"Gagal hantar minat ke group: {e}")
        await update.message.reply_text("❌ Maklumat tidak dapat dihantar buat masa ini. Sila hubungi pihak Kesatuan.", reply_markup=get_start_keyboard())
    return ConversationHandler.END

async def verify_employee_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emp_id = update.message.text.strip()
    user = update.effective_user

    data_ahli = baca_data_ahli(emp_id)

    if data_ahli:
        context.user_data['emp_id'] = emp_id
        context.user_data['nama'] = data_ahli['nama']
        context.user_data['lokasi'] = data_ahli['lokasi']
        context.user_data['verified'] = True
        context.user_data['last_active'] = time.time()
        
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
            "Nombor pekerja anda tiada dalam rekod fail CSV kesatuan.\n\n"
            "📞 Sila hubungi Setiausaha Agung (Pn. Farah Aqilah: aqilah@bernas.com.my) untuk bantuan.\n\n"
            "Sila cuba masukkan semula Nombor Pekerja yang sah:"
        )
        await update.message.reply_text(error_text, parse_mode='Markdown')
        return STATE_VERIFY_ID

# ==================== MODUL AKTA & PERATURAN ====================
async def handle_akta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_akta':
        text = (
            "📖 *1. AKTA & PERATURAN KERJA MALAYSIA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Pilih topik di bawah untuk rujukan hak minimum di bawah undang-undang "
            "serta perbandingan dengan CA-7 BERNAS:"
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_waktu':
        text = (
            "⏰ *AKTA KERJA 1955: WAKTU BEKERJA (SEKSYEN 60A)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *APA AKTA TETAPKAN*\n"
            "• Waktu kerja biasa tidak melebihi *45 jam seminggu*.\n"
            "• Waktu kerja harian tertakluk kepada had yang ditetapkan di bawah Seksyen 60A.\n"
            "• Pekerja berhak mendapat waktu rehat yang ditetapkan apabila bekerja secara berterusan.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 29*\n"
            "• Pekerja bukan syif: *39 jam seminggu*.\n"
            "• Pekerja syif: purata *42 jam seminggu*.\n"
            "• Sebarang perubahan jadual waktu bekerja, setakat yang praktik, "
            "hendaklah dimaklumkan kepada Kesatuan dan pekerja terlibat sekurang-kurangnya "
            "*3 hari sebelum* perubahan berkuat kuasa.\n\n"
            "🟢 *KELEBIHAN CA-7*\n"
            "CA-7 menetapkan waktu bekerja mingguan yang khusus untuk pekerja BERNAS."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_ot':
        text = (
            "🧮 *AKTA KERJA 1955: KERJA LEBIH MASA / OT*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *APA AKTA TETAPKAN*\n"
            "• Hari bekerja biasa: *1.5 × kadar gaji sejam*.\n"
            "• Hari rehat: *2.0 × kadar gaji sejam*.\n"
            "• Hari cuti am: *3.0 × kadar gaji sejam*.\n"
            "• Had kerja lebih masa adalah tertakluk kepada peraturan had OT yang berkuat kuasa.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 30 & 31*\n"
            "• OT dilakukan atas permintaan BERNAS dengan persetujuan pekerja; "
            "pekerja tidak boleh menolak tanpa alasan munasabah.\n"
            "• Hari bekerja biasa: formula CA-7 menggunakan *Gaji Bulanan ÷ 26 × 1.5* "
            "dan kadar jam kerja biasa.\n"
            "• Jika pekerja dipanggil dari rumah untuk OT sebelum atau selepas waktu kerja, "
            "BERNAS hendaklah membayar OT tersebut.\n"
            "• CA-7 membenarkan sehingga *104 jam sebulan*; OT pada hari rehat/cuti umum "
            "tidak termasuk dalam had tersebut, tertakluk kepada peraturan berkenaan.\n"
            "• OT boleh digantikan dengan cuti gantian: *6–8 jam = 1 hari*; "
            "*4–5 jam = 1/2 hari*, dan boleh dikumpulkan sehingga 6 bulan.\n\n"
            "🟢 *KELEBIHAN CA-7*\n"
            "Kemudahan cuti gantian OT dinyatakan secara khusus dalam CA-7."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_cuti':
        text = (
            "🏖️ *AKTA KERJA 1955: CUTI TAHUNAN (SEKSYEN 60E)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *MINIMUM DI BAWAH AKTA*\n"
            "• Kurang 2 tahun: *8 hari setahun*.\n"
            "• 2 hingga kurang 5 tahun: *12 hari setahun*.\n"
            "• 5 tahun dan ke atas: *16 hari setahun*.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 44*\n"
            "• Kurang 2 tahun: *18 hari*.\n"
            "• 2 hingga 5 tahun: *22 hari*.\n"
            "• Lebih 5 tahun: *24 hari*.\n\n"
            "🟢 *KELEBIHAN CA-7*\n"
            "Kelayakan cuti tahunan CA-7 adalah lebih tinggi daripada minimum Akta.\n"
            "• Baki cuti tertentu boleh dilanjutkan sehingga *30 Jun* tahun berikutnya, "
            "tertakluk kepada syarat CA-7.\n"
            "• Jika cuti sakit berlaku ketika cuti tahunan, hari yang dilindungi cuti sakit "
            "tidak dianggap telah menggunakan cuti tahunan."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_mc':
        text = (
            "🏥 *AKTA KERJA 1955: CUTI SAKIT & HOSPITALISASI (SEKSYEN 60F)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *MINIMUM DI BAWAH AKTA*\n"
            "• Kurang 2 tahun: *14 hari* cuti sakit.\n"
            "• 2 hingga kurang 5 tahun: *18 hari*.\n"
            "• 5 tahun dan ke atas: *22 hari*.\n"
            "• Jika hospitalisasi diperlukan: sehingga *60 hari* setahun, tertakluk kepada Akta.\n"
            "• Pekerja hendaklah memaklumkan majikan mengenai ketidakhadiran kerana sakit "
            "dalam tempoh yang ditetapkan undang-undang.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 47*\n"
            "• Cuti sakit biasa: *22 hari setahun*.\n"
            "• Jika perlu dimasukkan ke hospital: *60 hari setahun* berdasarkan pengesahan "
            "Doktor Pakar Panel BERNAS.\n\n"
            "⭐ *CA-7 – ARTIKEL 46: KEMALANGAN PERUSAHAAN*\n"
            "• Kemalangan perusahaan yang bukan kerana kecuaian sendiri boleh dipertimbangkan "
            "untuk cuti sakit bergaji penuh sehingga pekerja benar-benar sembuh, "
            "berdasarkan kes dan laporan doktor pakar.\n"
            "• Cuti ini tidak dikira sebagai cuti sakit biasa."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_gaji':
        text = (
            "💰 *AKTA KERJA 1955: PEMBAYARAN GAJI (SEKSYEN 19)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *APA AKTA TETAPKAN*\n"
            "• Gaji hendaklah dibayar *tidak lewat daripada hari ke-7* selepas tamat tempoh upah.\n\n"
            "⭐ *CA-7 BERNAS*\n"
            "• Takrif gaji dalam CA-7 dirujuk bersama peruntukan Akta Kerja 1955.\n\n"
            "🟡 *KESIMPULAN*\n"
            "Bagi perkara yang tiada faedah khusus lebih baik dalam CA-7, "
            "minimum undang-undang terpakai."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_awol':
        text = (
            "⚠️ *AWOL / KETIDAKHADIRAN – SEKSYEN 15(2) & DISIPLIN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *APA AKTA TETAPKAN*\n"
            "• Jika pekerja tidak hadir *lebih daripada 2 hari bekerja berturut-turut* "
            "tanpa kebenaran, ia boleh dianggap sebagai pelanggaran kontrak.\n"
            "• Pengecualian: pekerja mempunyai alasan munasabah dan telah memaklumkan, "
            "atau cuba memaklumkan, majikan pada peluang terawal.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 28*\n"
            "• CA-7 turut menetapkan peruntukan ketidakhadiran lebih daripada 2 hari "
            "bekerja berturut-turut tanpa kebenaran, tertakluk kepada alasan munasabah "
            "dan kewajipan memaklumkan BERNAS.\n\n"
            "📌 *NOTA DISIPLIN*\n"
            "Isu AWOL boleh membawa kepada tindakan tatatertib. Proses dan hukuman "
            "hendaklah dirujuk kepada peruntukan disiplin yang berkuat kuasa."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_tamat':
        text = (
            "🚪 *PENAMATAN KONTRAK & NOTIS – SEKSYEN 12*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *MINIMUM DI BAWAH AKTA*\n"
            "• Kurang 2 tahun: *4 minggu notis*.\n"
            "• 2 hingga kurang 5 tahun: *6 minggu notis*.\n"
            "• 5 tahun dan ke atas: *8 minggu notis*.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 27*\n"
            "• Kurang 2 tahun: *4 minggu*.\n"
            "• 2 hingga 5 tahun: *6 minggu*.\n"
            "• Lebih 5 tahun: *8 minggu*.\n\n"
            "🟡 *KESIMPULAN*\n"
            "Kadar notis CA-7 adalah selaras dengan tempoh minimum yang dinyatakan "
            "dalam Akta."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_osha':
        text = (
            "🦺 *OSHA 1994 – SEKSYEN 26A*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *HAK PEKERJA*\n"
            "• Pekerja mempunyai hak untuk menjauhkan diri daripada bahaya serius dan "
            "hampir pasti berlaku selepas memaklumkan majikan mengenai bahaya tersebut "
            "dan majikan gagal mengambil tindakan untuk menghapuskan bahaya.\n"
            "• Pekerja tidak boleh didiskriminasi kerana menggunakan hak tersebut.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 69*\n"
            "• CA-7 mempunyai peruntukan khusus mengenai *Jawatankuasa Keselamatan, "
            "Kesihatan Pekerjaan dan Persekitaran*.\n\n"
            "⚠️ *PENTING*\n"
            "Hak di bawah Seksyen 26A bukan bermaksud pekerja boleh menolak sebarang "
            "kerja yang dirasakan berisiko. Syarat dan keadaan yang ditetapkan undang-undang "
            "perlu dipenuhi."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

    elif data == 'akta_perkeso':
        text = (
            "🛡️ *PERKESO – SKIM BENCANA PEKERJAAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *PERLINDUNGAN*\n"
            "• Meliputi kemalangan yang berlaku akibat pekerjaan serta perlindungan "
            "yang berkaitan di bawah skim bencana pekerjaan, tertakluk kepada syarat PERKESO.\n"
            "• Kemalangan perjalanan pergi dan balik kerja juga boleh dilindungi "
            "tertakluk kepada syarat undang-undang.\n\n"
            "⭐ *CA-7 BERNAS – ARTIKEL 42*\n"
            "• Pekerja yang terlibat dalam kemalangan perusahaan menerima pampasan "
            "mengikut peruntukan dan kelulusan Akta Keselamatan Sosial Pekerja 1969.\n\n"
            "⭐ *CA-7 – ARTIKEL 46*\n"
            "• Kemalangan perusahaan yang bukan kerana kecuaian sendiri boleh dipertimbangkan "
            "untuk cuti sakit bergaji penuh sehingga sembuh, tertakluk kepada syarat CA-7."
        )
        await query.message.reply_text(
            text, parse_mode='Markdown', reply_markup=get_akta_keyboard()
        )

# ==================== KIRAAN OT CA-7 ====================
def get_ot_zone_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇲🇾 Zon A — Isnin–Jumaat", callback_data='ot_zon_a')],
        [InlineKeyboardButton("🇲🇾 Zon B — Ahad–Khamis", callback_data='ot_zon_b')],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_ot_day_keyboard(zone):
    if zone == 'A':
        keyboard = [
            [InlineKeyboardButton("📅 Hari Bekerja (Isnin–Jumaat)", callback_data='ot_hari_biasa')],
            [InlineKeyboardButton("🛌 Hari Rehat (Sabtu/Ahad)", callback_data='ot_hari_rehat')],
            [InlineKeyboardButton("🎉 Cuti Am", callback_data='ot_cuti_am')],
            [InlineKeyboardButton("🔙 Pilih Zon", callback_data='menu_kiraan')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📅 Hari Bekerja (Ahad–Rabu)", callback_data='ot_hari_biasa_8')],
            [InlineKeyboardButton("📅 Khamis (8am–4pm)", callback_data='ot_hari_biasa_7')],
            [InlineKeyboardButton("🛌 Hari Rehat (Jumaat/Sabtu)", callback_data='ot_hari_rehat')],
            [InlineKeyboardButton("🎉 Cuti Am", callback_data='ot_cuti_am')],
            [InlineKeyboardButton("🔙 Pilih Zon", callback_data='menu_kiraan')]
        ]
    return InlineKeyboardMarkup(keyboard)


async def handle_ot_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_kiraan':
        context.user_data.pop('ot_zone', None)
        context.user_data.pop('ot_day_hours', None)
        text = (
            "🧮 *KIRAAN ANGGARAN BAYARAN OT — CA-7*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Sila pilih zon waktu bekerja kerana hari rehat berbeza mengikut jadual CA-7.\n\n"
            "🇲🇾 *Zon A:* Isnin–Jumaat\n"
            "• Waktu biasa: 8.30 pagi–5.30 petang\n"
            "• Rehat: 1.00–2.00 petang\n"
            "• Jumaat: rehat 12.30 tengah hari–2.30 petang\n\n"
            "🇲🇾 *Zon B:* Ahad–Khamis\n"
            "• Ahad–Rabu: 8.00 pagi–5.00 petang\n"
            "• Khamis: 8.00 pagi–4.00 petang\n"
            "• Waktu rehat: 1.00–2.00 petang\n\n"
            "📌 *Nota:* Ini ialah anggaran berdasarkan formula CA-7 Artikel 31."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ot_zone_keyboard())
        return STATE_OT_ZONE

    if data in ('ot_zon_a', 'ot_zon_b'):
        zone = 'A' if data == 'ot_zon_a' else 'B'
        context.user_data['ot_zone'] = zone
        context.user_data.pop('ot_day_hours', None)
        if zone == 'A':
            text = (
                "🇲🇾 *ZON A — ISNIN HINGGA JUMAAT*\n\n"
                "Sila pilih hari OT:\n"
                "• Hari bekerja biasa\n"
                "• Hari rehat\n"
                "• Cuti am\n\n"
                "Artikel 29 CA-7 menetapkan waktu biasa 8.30 pagi–5.30 petang, dengan waktu makan 1.00–2.00 petang; Jumaat 12.30–2.30 petang."
            )
        else:
            text = (
                "🇲🇾 *ZON B — AHAD HINGGA KHAMIS*\n\n"
                "Sila pilih hari OT:\n"
                "• Ahad–Rabu (8 jam kerja biasa)\n"
                "• Khamis (7 jam kerja biasa)\n"
                "• Hari rehat\n"
                "• Cuti am\n\n"
                "Artikel 29 CA-7 menetapkan Ahad–Rabu 8.00 pagi–5.00 petang dan Khamis 8.00 pagi–4.00 petang, dengan waktu makan 1.00–2.00 petang."
            )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ot_day_keyboard(zone))
        return STATE_OT_DAY

    if data in ('ot_hari_biasa', 'ot_hari_biasa_8', 'ot_hari_biasa_7'):
        if data == 'ot_hari_biasa_7':
            context.user_data['ot_day_hours'] = 7
        else:
            context.user_data['ot_day_hours'] = 8
        context.user_data['ot_day_type'] = 'Hari bekerja biasa'
    elif data == 'ot_hari_rehat':
        context.user_data['ot_day_type'] = 'Hari rehat'
        context.user_data['ot_day_hours'] = None
    elif data == 'ot_cuti_am':
        context.user_data['ot_day_type'] = 'Cuti am'
        context.user_data['ot_day_hours'] = None

    # Hari rehat dan cuti am turut melalui kiraan, menggunakan kadar berkanun
    # yang dirujuk oleh CA-7 Artikel 31.2. Gaji harian = gaji bulanan / 26.
    # Hari rehat: <= 1/2 jam biasa = 0.5 hari; >1/2 hingga jam biasa = 1 hari;
    # lebihan jam = 2x kadar sejam. Cuti am: jam biasa = 2 hari; lebihan jam = 3x kadar sejam.
    # Untuk kedua-duanya, pengguna masih masukkan gaji dan jumlah jam bekerja.

    await query.message.reply_text(
        "💰 *Masukkan gaji bulanan asas (RM)*\n\n"
        "Contoh: `3000`",
        parse_mode='Markdown'
    )
    return STATE_OT_SALARY


async def ot_get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        salary = float(update.message.text.replace(',', '').strip())
        if salary <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Masukkan jumlah gaji yang sah. Contoh: `3000`", parse_mode='Markdown')
        return STATE_OT_SALARY

    context.user_data['ot_salary'] = salary
    await update.message.reply_text(
        "⏱️ *Masukkan jumlah jam OT*\n\n"
        "Contoh: `4` atau `4.5`",
        parse_mode='Markdown'
    )
    return STATE_OT_HOURS


async def ot_get_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = float(update.message.text.replace(',', '').strip())
        if hours <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Masukkan jumlah jam OT yang sah. Contoh: `4.5`", parse_mode='Markdown')
        return STATE_OT_HOURS

    salary = context.user_data.get('ot_salary', 0)
    zone = context.user_data.get('ot_zone', 'A')
    day_type = context.user_data.get('ot_day_type', 'Hari bekerja biasa')

    # Hari bekerja biasa menggunakan jam biasa mengikut zon.
    # Hari rehat/cuti am menggunakan jam biasa 8 jam secara default;
    # Khamis Zon B kekal 7 jam jika pengguna memilih hari bekerja Khamis.
    normal_hours = context.user_data.get('ot_day_hours') or 8
    hourly_rate = salary / (26 * normal_hours)
    daily_rate = salary / 26

    if day_type == 'Hari rehat':
        half_day_hours = normal_hours / 2
        if hours <= half_day_hours:
            estimate = daily_rate * 0.5
            rate_desc = f"≤ {half_day_hours:g} jam = 0.5 × gaji harian"
        elif hours <= normal_hours:
            estimate = daily_rate
            rate_desc = f"> {half_day_hours:g} hingga {normal_hours:g} jam = 1 × gaji harian"
        else:
            excess_hours = hours - normal_hours
            estimate = daily_rate + (excess_hours * hourly_rate * 2)
            rate_desc = f"{normal_hours:g} jam pertama = 1 × gaji harian; lebihan = 2 × kadar sejam"
        formula_text = (
            f"Gaji harian = RM{salary:,.2f} ÷ 26 = *RM{daily_rate:,.2f}*\n"
            f"Kadar sejam = RM{salary:,.2f} ÷ (26 × {normal_hours:g}) = *RM{hourly_rate:,.2f}/jam*\n"
            f"Kadar hari rehat: *{rate_desc}*"
        )
        note = "📌 Kiraan hari rehat dibuat mengikut kadar yang dirujuk di bawah Akta Kerja 1955."
    elif day_type == 'Cuti am':
        if hours <= normal_hours:
            estimate = daily_rate * 2
            rate_desc = f"sehingga {normal_hours:g} jam = 2 × gaji harian"
        else:
            excess_hours = hours - normal_hours
            estimate = (daily_rate * 2) + (excess_hours * hourly_rate * 3)
            rate_desc = f"{normal_hours:g} jam pertama = 2 × gaji harian; lebihan = 3 × kadar sejam"
        formula_text = (
            f"Gaji harian = RM{salary:,.2f} ÷ 26 = *RM{daily_rate:,.2f}*\n"
            f"Kadar sejam = RM{salary:,.2f} ÷ (26 × {normal_hours:g}) = *RM{hourly_rate:,.2f}/jam*\n"
            f"Kadar cuti am: *{rate_desc}*"
        )
        note = "📌 Kiraan cuti am dibuat mengikut kadar yang dirujuk di bawah Akta Kerja 1955."
    else:
        ot_rate = hourly_rate * 1.5
        estimate = ot_rate * hours
        formula_text = (
            f"Kadar sejam = RM{salary:,.2f} ÷ (26 × {normal_hours:g}) = *RM{hourly_rate:,.2f}/jam*\n"
            f"Kadar OT hari bekerja biasa = RM{hourly_rate:,.2f} × 1.5 = *RM{ot_rate:,.2f}/jam*"
        )
        note = "📌 Berdasarkan formula CA-7 Artikel 31.1."

    zone_text = 'Zon A — Isnin–Jumaat' if zone == 'A' else 'Zon B — Ahad–Khamis'
    text = (
        "🧮 *ANGGARAN BAYARAN OT CA-7*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Zon: *{zone_text}*\n"
        f"📅 Jenis hari: *{day_type}*\n"
        f"💰 Gaji asas: *RM{salary:,.2f}*\n"
        f"⏱️ Jam bekerja/OT: *{hours:g} jam*\n"
        f"🕐 Jam kerja biasa: *{normal_hours:g} jam/hari*\n\n"
        f"{formula_text}\n\n"
        f"💵 *Anggaran bayaran = RM{estimate:,.2f}*\n\n"
        f"{note}\n"
        "⚠️ Jumlah sebenar tertakluk kepada rekod payroll dan kelayakan tuntutan."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Kira Semula OT", callback_data='menu_kiraan')],
        [InlineKeyboardButton("📋 Menu CA-7", callback_data='menu_ca')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ])
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    return ConversationHandler.END

# ==================== MODUL CA-7 ====================
async def handle_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_ca':
        text = (
            "📋 *PERJANJIAN BERSAMA KE-7 (CA-7)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 Berkuat kuasa: *1 Januari 2026 – 31 Disember 2028*\n\n"
            "Rujukan ringkas perkara penting CA-7. Pilih topik di bawah:"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gaji':
        text = (
            "💰 *CA-7: GAJI & KENAIKAN GAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 25 – Kenaikan Gaji Tahunan*\n"
            "• Pekerja yang telah disahkan layak dipertimbangkan untuk kenaikan pada 1 Januari.\n"
            "• Kenaikan mengambil kira prestasi, prestasi kumpulan/syarikat, keupayaan kewangan dan faktor berkaitan.\n"
            "• Prestasi *Memenuhi Jangkaan dan ke atas*: *3.5% + merit*.\n"
            "• *Di Bawah Jangkaan / Tidak Memuaskan*: *2%*.\n"
            "• Pekerja di gaji maksimum boleh dipertimbangkan EIP tertakluk prestasi; tidak kumulatif.\n\n"
            "📌 *Artikel 26 – Bonus*\n"
            "• Bonus kontraktual: *1 bulan gaji*.\n"
            "• Tertakluk kepada syarat pengesahan, tempoh perkhidmatan dan status disiplin.\n\n"
            "📌 *Artikel 74 – Semakan Gaji*\n"
            "• Dokumen CA-7 menyatakan gaji bulanan ahli Kesatuan diselaraskan *lima peratus (4.5%)*. Wording ini dikekalkan seperti naskhah CA-7 untuk rujukan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_waktu_ot':
        text = (
            "⏰ *CA-7: WAKTU KERJA & KERJA LEBIH MASA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 29 – Waktu Bekerja*\n"
            "• Pekerja bukan syif: purata *39 jam seminggu*.\n"
            "• Pekerja syif: purata *42 jam seminggu*.\n"
            "• Perubahan jadual waktu bekerja hendaklah, setakat yang praktik, dimaklumkan sekurang-kurangnya 3 hari sebelum berkuat kuasa.\n\n"
            "📌 *Artikel 30 – Kerja Lebih Masa*\n"
            "• OT dilakukan atas permintaan BERNAS dengan persetujuan pekerja.\n"
            "• Pekerja tidak boleh menolak tanpa alasan munasabah.\n\n"
            "📌 *Artikel 31 – Bayaran OT*\n"
            "• Hari kerja biasa: *1.5 × kadar jam biasa*.\n"
            "• Had OT: sehingga *104 jam sebulan* bagi bulan berkenaan, tidak termasuk OT hari rehat/cuti umum seperti diperuntukkan.\n"
            "• OT boleh diganti cuti: *6–8 jam = 1 hari*; *4–5 jam = ½ hari*, tertakluk syarat CA-7."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧮 Kira Anggaran Bayaran OT", callback_data='menu_kiraan')],
            [InlineKeyboardButton("🔙 Kembali CA-7", callback_data='menu_ca')]
        ])
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)

    elif data == 'ca_cuti':
        text = (
            "🏖️ *CA-7: CUTI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 44 – Cuti Tahunan*\n"
            "• <2 tahun: *18 hari*.\n"
            "• 2–5 tahun: *22 hari*.\n"
            "• >5 tahun: *24 hari*.\n\n"
            "📌 *Artikel 47 – Cuti Sakit*\n"
            "• Tanpa hospital: *22 hari setahun*.\n"
            "• Hospital: *60 hari setahun*, tertakluk syarat CA-7.\n\n"
            "📌 *Artikel 49 – Bersalin*: *98 hari berturut-turut* bergaji penuh, maksimum 5 kelahiran hidup.\n"
            "📌 *Artikel 50 – Ehsan*: *3 hari bekerja* bagi kematian ahli keluarga yang ditetapkan; terdapat juga kelayakan menjaga/mengiringi tanggungan ke hospital.\n"
            "📌 *Artikel 52 – Paterniti*: *7 hari berturut-turut* bergaji penuh bagi pekerja lelaki yang memenuhi syarat; 3 hari jika tempoh perkhidmatan kurang 1 tahun.\n"
            "📌 *Artikel 55 – Haji/Umrah*: *54 hari berturut-turut* bergaji penuh, sekali sepanjang perkhidmatan, tertakluk syarat kelayakan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_perubatan':
        text = (
            "🏥 *CA-7: PERUBATAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 58 – Tanggungan*\n"
            "• Meliputi tanggungan yang ditetapkan seperti pasangan sah, anak dan kategori ibu/bapa/anak OKU tertakluk syarat CA-7.\n\n"
            "📌 *Artikel 59 – Rawatan Pesakit Luar*\n"
            "• Had tahunan: *RM3,500*.\n"
            "• Termasuk peruntukan tertentu untuk pergigian/cermin mata bagi pekerja.\n"
            "• Rawatan pakar lazimnya memerlukan rujukan panel.\n\n"
            "📌 *Artikel 60 – Rawatan Hospital*\n"
            "• Sehingga 31 Disember 2026: *RM35,000 setahun/individu*.\n"
            "• Mulai 1 Januari 2027: *RM45,000 setahun/individu*.\n"
            "• Bilik & makan: *RM150 sehari*.\n"
            "• Lebihan daripada had ditanggung pekerja, tertakluk syarat CA-7."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_pangkat':
        text = (
            "📈 *CA-7: KENAIKAN PANGKAT & GRED*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 33 – Kenaikan Pangkat*\n"
            "• Kekosongan boleh diisi melalui sumber yang sesuai.\n"
            "• Keutamaan dasar ialah memberi peluang kepada pekerja BERNAS yang sesuai, berpengalaman dan berkebolehan.\n"
            "• Kekosongan dalaman hendaklah dihebahkan kepada pekerja.\n"
            "• Kenaikan pangkat boleh dipertimbangkan berdasarkan kecekapan, prestasi, tanggungjawab dan kekosongan yang diluluskan.\n"
            "• Jika tiada calon dalaman yang sesuai, pengambilan luar boleh dibuat.\n\n"
            "📌 *Nota:* Kelayakan sebenar tetap tertakluk kepada syarat jawatan, prosedur kenaikan pangkat dan kekosongan yang diluluskan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gred':
        text = (
            "📊 *CA-7: STRUKTUR TANGGA GAJI S & T*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*🔷 KUMPULAN T — TEKNIKAL*\n"
            "• *T1* – Juruteknik Rendah: RM1,700 – RM2,800\n"
            "• *T2* – Juruteknik I / Pembantu Makmal I: RM1,900 – RM3,200\n"
            "• *T3* – Juruteknik II / Penjaga Jentera I / Juru Dandang I / Pembantu Makmal II: RM2,100 – RM4,000\n"
            "• *T4* – Juruteknik III / Penjaga Jentera II / Juru Dandang II / Penyelia Kejuruteraan I / Penyelia Operasi I / Penyelia Makmal I: RM2,600 – RM5,200\n"
            "• *T5* – Penyelia Kejuruteraan II / Penyelia Operasi II / Penyelia Makmal II: RM3,000 – RM6,300\n\n"
            "*🔶 KUMPULAN S — SOKONGAN*\n"
            "• *S1* – Operator Pengeluaran / Pembantu Tadbir Rendah: RM1,700 – RM2,800\n"
            "• *S2* – Pembantu Tadbir I / Pemandu I / Operator Ladang: RM1,900 – RM3,000\n"
            "• *S3* – Pembantu Tadbir II / Pemandu II: RM2,100 – RM3,600\n"
            "• *S4* – Penyelia I / Pembantu Tadbir III: RM2,400 – RM4,500\n"
            "• *S5* – Penyelia II: RM2,800 – RM5,400\n\n"
            "📌 *Nota:* Struktur di atas adalah berdasarkan jadual gred jawatan dalam CA-7. Kelayakan seseorang pekerja kepada gred/jawatan tertentu tetap tertakluk kepada syarat jawatan dan peruntukan CA-7."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_awol':
        text = (
            "🚫 *CA-7: KETIDAKHADIRAN / AWOL*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 28 – Ketidakhadiran*\n"
            "• Ketidakhadiran lebih daripada *2 hari bekerja berturut-turut* tanpa kebenaran terlebih dahulu boleh dianggap sebagai pelanggaran.\n"
            "• Pengecualian boleh dipertimbangkan jika pekerja mempunyai alasan munasabah dan telah memaklumkan atau cuba memaklumkan BERNAS seawal mungkin.\n"
            "• Artikel ini merujuk kepada peruntukan *Seksyen 15(2) Akta Kerja 1955*.\n\n"
            "⚠️ Jika berlaku masalah ketidakhadiran, simpan bukti komunikasi dan dokumen sokongan untuk rujukan Kesatuan/HR."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_disiplin':
        text = (
            "⚖️ *CA-7: DISIPLIN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 73*\n"
            "• Peraturan dan prosedur tatatertib BERNAS yang sedang digunakan terus terpakai kepada pekerja yang dikenakan tindakan disiplin.\n\n"
            "📌 *Artikel 26 – Bonus*\n"
            "• Status tindakan disiplin boleh memberi kesan kepada bayaran bonus mengikut syarat CA-7.\n\n"
            "💡 *Jika menerima surat tunjuk sebab/tindakan disiplin:* simpan surat, bukti dan jawapan yang dihantar serta dapatkan pandangan Kesatuan sebelum membuat keputusan lanjut."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_elaun':
        text = (
            "🚗 *CA-7: ELAUN & TUNTUTAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 62 – Penempatan Semula / Secondment*\n"
            "• Elaun boleh dipertimbangkan berdasarkan tempoh, lokasi, tujuan dan kesan kepada pekerja/keluarga.\n"
            "• Elaun makan: berdasarkan bilangan sebenar ahli keluarga yang tinggal bersama pekerja, termasuk seorang orang gaji, bagi *3 hari sebelum + 5 hari selepas* pertukaran.\n"
            "• Penginapan: berdasarkan ahli keluarga, maksimum *3 bilik*, dengan resit.\n"
            "• Jika tidak tuntut hotel: Elaun Lojing *RM100/malam* untuk pekerja sahaja bagi tempoh 3 hari sebelum + 5 hari selepas pertukaran.\n\n"
            "📌 *Artikel 63 – Elaun Perjalanan*\n"
            "• Kereta sendiri: *RM0.75/km*.\n"
            "• Motorsikal: *RM0.50/km*.\n"
            "• Tol, parkir & feri: *boleh dituntut balik* dengan resit (atau pengesahan Ketua Bahagian jika resit hilang/tiada).\n"
            "• Pengangkutan awam/teksi: *tambang semasa*.\n\n"
            "📌 *Artikel 64 – Elaun Makan*\n"
            "• Tugas rasmi >50 km dan *8 jam atau lebih*: *RM115 sehari*.\n"
            "• Jika makan disediakan: Sarapan *20% (RM23)*, Tengahari *40% (RM46)*, Malam *40% (RM46)*.\n"
            "• Gaji *RM4,000 ke atas* dan tidak layak OT: kerja hari biasa >2–5 jam = *RM25*; >5 jam = *RM50*.\n"
            "• Hari rehat/cuti am: >4–8 jam = *RM25* atau ½ hari cuti gantian; >8 jam = *RM50* atau 1 hari cuti gantian.\n\n"
            "📌 *Artikel 65 – Penginapan Hotel*\n"
            "• Tuntutan hotel: penginapan standard setaraf *4 bintang, twin sharing*, dengan resit.\n"
            "• Jika tidak tuntut hotel: *Elaun Lojing RM100 semalam* tanpa resit.\n\n"
            "📌 *Artikel 71 – Chargeman*: *RM300 sebulan* jika mempunyai sijil kelayakan dan menjalankan tugas sebagai Chargeman.\n"
            "📌 *Artikel 72 – Syif*: *RM6.50* (4pm–12am) dan *RM7.00* (12am–8am); bagi syif 8pm–8am = *RM7.00*, mengikut jadual/lokasi CA-7."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_keselamatan':
        text = (
            "🦺 *CA-7: KESELAMATAN & KEMALANGAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 42 – Kemalangan Pekerjaan*\n"
            "• Pampasan kemalangan perusahaan adalah mengikut peruntukan dan kelulusan Akta Keselamatan Sosial Pekerja 1969.\n\n"
            "📌 *Artikel 46 – Kemalangan Industri*\n"
            "• Cuti sakit bergaji penuh boleh dipertimbangkan sehingga pulih bagi kemalangan industri yang bukan disebabkan kecuaian sendiri, tertakluk laporan doktor pakar dan syarat CA-7.\n\n"
            "📌 *Artikel 69 – Jawatankuasa Keselamatan, Kesihatan Pekerjaan & Persekitaran*\n"
            "• BERNAS hendaklah mewujudkan jawatankuasa sejajar dengan Akta Keselamatan dan Kesihatan Pekerjaan 1994.\n"
            "• Jawatankuasa diwakili pihak BERNAS dan Kesatuan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_kesatuan':
        text = (
            "👥 *CA-7: KESATUAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 11 – Pengiktirafan Kesatuan*\n"
            "• Pekerja bukan eksekutif yang tidak dikecualikan di bawah CA-7 diiktiraf layak menjadi ahli Kesatuan.\n"
            "• BERNAS mengiktiraf hak Kesatuan mewakili ahlinya dalam perkara berkaitan terma dan syarat perkhidmatan.\n\n"
            "📌 *Artikel 23 – Yuran Kesatuan*\n"
            "• Potongan yuran melalui gaji dilaksanakan tertakluk kepada syarat dan notis yang ditetapkan.\n"
            "• Pengeluaran persetujuan potongan memerlukan *2 bulan notis bertulis*.\n\n"
            "📌 *Artikel 21 – Cuti Tugas Kesatuan*\n"
            "• Kemudahan berkaitan tugas Kesatuan adalah tertakluk kepada peruntukan CA-7 dan kelulusan yang ditetapkan.\n\n"
            "📌 *Rujukan:* Jika berlaku pertikaian berkaitan tafsiran/pelaksanaan CA-7, rujuk Kesatuan untuk tindakan dan saluran yang bersesuaian."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

# ==================== MODUL LAPORAN / ADUAN ====================
def get_aduan_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚠️ Isu Pekerjaan", callback_data='aduan_isu')],
        [InlineKeyboardButton("💰 Gaji / Elaun / OT", callback_data='aduan_gaji')],
        [InlineKeyboardButton("👥 Kebajikan / Perkhidmatan", callback_data='aduan_kebajikan')],
        [InlineKeyboardButton("🦺 Keselamatan / Tempat Kerja", callback_data='aduan_keselamatan')],
        [InlineKeyboardButton("📋 Lain-lain", callback_data='aduan_lain')],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_aduan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not is_session_active(context):
        await query.message.reply_text(
            "🔐 *Sesi anda telah tamat.*\n\nSila tekan /start untuk pengesahan semula.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    if data == 'menu_aduan':
        text = (
            "📝 *LAPORAN / ADUAN KPPbNB*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Saluran ini digunakan untuk ahli melaporkan isu, masalah atau perkara berkaitan pekerjaan kepada Kesatuan.\n\n"
            "📌 Pilih kategori laporan/aduan di bawah:"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_aduan_keyboard())
        return STATE_ADUAN_JENIS

    jenis_map = {
        'aduan_isu': 'Isu Pekerjaan',
        'aduan_gaji': 'Gaji / Elaun / OT',
        'aduan_kebajikan': 'Kebajikan / Perkhidmatan',
        'aduan_keselamatan': 'Keselamatan / Tempat Kerja',
        'aduan_lain': 'Lain-lain'
    }

    if data in jenis_map:
        context.user_data['aduan_jenis'] = jenis_map[data]
        await query.message.reply_text(
            f"📝 *Kategori:* {jenis_map[data]}\n\n"
            "Sila taip *keterangan aduan/laporan* dengan jelas.\n\n"
            "Contoh:\n"
            "• Tarikh kejadian\n"
            "• Lokasi\n"
            "• Apa yang berlaku\n"
            "• Tindakan yang telah diambil (jika ada)\n"
            "• Apa bantuan/tindakan yang diperlukan daripada Kesatuan",
            parse_mode='Markdown'
        )
        return STATE_ADUAN_KETERANGAN

    if data == 'menu_utama':
        nama = context.user_data.get('nama', 'Ahli')
        await query.message.reply_text(
            f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:",
            parse_mode='Markdown', reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    return STATE_ADUAN_JENIS

async def terima_aduan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_session_active(context):
        await update.message.reply_text(
            "🔐 *Sesi anda telah tamat.*\n\nSila tekan /start untuk pengesahan semula.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    keterangan = update.message.text.strip()
    if not keterangan:
        await update.message.reply_text("❌ Sila masukkan keterangan aduan.")
        return STATE_ADUAN_KETERANGAN

    context.user_data['aduan_keterangan'] = keterangan
    jenis = context.user_data.get('aduan_jenis', 'Lain-lain')
    nama = context.user_data.get('nama', 'Tidak Diketahui')
    emp_id = context.user_data.get('emp_id', 'Tidak Diketahui')
    lokasi = context.user_data.get('lokasi', 'Tidak Diketahui')
    user = update.effective_user
    masa = time.strftime('%d/%m/%Y %H:%M:%S')

    text = (
        "📨 *LAPORAN / ADUAN BAHARU*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Nama:* {nama}\n"
        f"🔢 *No. Pekerja:* `{emp_id}`\n"
        f"📍 *Lokasi:* {lokasi}\n"
        f"📂 *Kategori:* {jenis}\n"
        f"🕐 *Masa Laporan:* {masa}\n\n"
        "📄 *Keterangan:*\n"
        f"{keterangan}\n\n"
        f"🆔 *Telegram ID:* `{user.id}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *Untuk tindakan / semakan AJK KPPbNB*"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode='Markdown')
        await update.message.reply_text(
            "✅ *LAPORAN BERJAYA DIHANTAR*\n\n"
            "Aduan anda telah dihantar terus ke *Group Aduan KPPbNB* untuk semakan dan tindakan AJK.\n\n"
            "📌 Jika perkara ini memerlukan proses kilanan rasmi, pihak Kesatuan akan memaklumkan tindakan seterusnya.",
            parse_mode='Markdown', reply_markup=get_back_button()
        )
    except Exception as e:
        logging.error(f"Gagal hantar laporan/aduan ke group: {e}")
        await update.message.reply_text(
            "❌ *Laporan tidak dapat dihantar buat masa ini.*\n\nSila cuba semula atau hubungi pihak Kesatuan.",
            parse_mode='Markdown', reply_markup=get_back_button()
        )

    context.user_data.pop('aduan_jenis', None)
    context.user_data.pop('aduan_keterangan', None)
    return ConversationHandler.END

# ==================== MODUL SAHABAT KPPbNB ====================
# Modul ini berdiri sendiri dan tidak mengubah fungsi CA7, OT, Aduan, Ahli dll.
# Memerlukan environment variable OPENAI_API_KEY untuk jawapan AI.

SAHABAT_SYSTEM_PROMPT = """
Anda ialah Sahabat KPPbNB, pembantu digital rasmi untuk ahli Kesatuan Pekerja-Pekerja
Padiberas Nasional Berhad (KPPbNB).

Tugas anda:
1. Bantu ahli memahami CA-7, Akta/Peraturan kerja dan isu hubungan perusahaan.
2. Jawab dalam Bahasa Malaysia yang mudah, ringkas dan mesra.
3. Utamakan maklumat CA-7 yang diberikan dalam konteks. Jangan reka nombor artikel,
   kadar, tempoh atau hak yang tiada dalam konteks.
4. Jika maklumat tidak cukup atau isu memerlukan tafsiran/keputusan rasmi, nyatakan
   bahawa Sahabat hanya memberi panduan umum dan rujuk pegawai Kesatuan.
5. Isu serius seperti surat tunjuk sebab, amaran, siasatan disiplin, demotion,
   penamatan/dismissal, pertikaian kompleks atau tafsiran CA-7 hendaklah dirujuk
   kepada pegawai Kesatuan dan jangan buat keputusan bagi pihak Kesatuan.
6. Rujukan pegawai:
   - Isu strategik/pertikaian umum/keputusan Kesatuan: Bro Syahibudil
   - Kilanan, disiplin, surat tunjuk sebab, hubungan perusahaan, keahlian: Sis Farah
   - Gaji, elaun, OT dan kewangan: Bro Khairul
   - Jika tidak pasti: rujuk Setiausaha Agung.
7. Jika soalan berkaitan kiraan OT, arahkan ahli menggunakan menu Kiraan OT & Elaun
   kerana modul tersebut mempunyai pengiraan khusus CA-7.
8. Jangan mendakwa sebagai peguam atau membuat keputusan rasmi bagi KPPbNB.
"""


def _sahabat_baca_ca7():
    # Fail CA7 txt sedia ada digunakan sebagai sumber rujukan tambahan.
    candidates = ["ca7_kppbnb.txt", "/mnt/data/ca7_kppbnb.txt"]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                # Hadkan saiz supaya permintaan API tidak terlalu besar.
                return text[:60000]
        except Exception as e:
            logging.error(f"Gagal baca sumber CA7 untuk Sahabat: {e}")
    return ""

async def _sahabat_tanya_ai(soalan: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return (
            "⚠️ *Sahabat KPPbNB belum diaktifkan sepenuhnya.*\n\n"
            "Sila tetapkan `OPENAI_API_KEY` pada Environment Variables server bot.\n\n"
            "Buat masa ini, gunakan menu *📖 Akta & Peraturan* dan *📋 CA7* untuk rujukan."
        )

    ca7 = _sahabat_baca_ca7()
    prompt = (
        "SUMBER CA-7 KPPbNB:\n"
        + (ca7 if ca7 else "Sumber CA-7 tidak dapat dibaca sekarang.")
        + "\n\nSOALAN AHLI:\n"
        + soalan
    )

    try:
        import json
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "model": os.environ.get("SAHABAT_MODEL", "gpt-5.6-luna"),
            "instructions": SAHABAT_SYSTEM_PROMPT,
            "input": prompt,
            "max_output_tokens": 700
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )

        loop = asyncio.get_running_loop()
        def call_api():
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))

        data = await loop.run_in_executor(None, call_api)
        answer = data.get("output_text", "").strip()

        if not answer:
            # Fallback jika struktur output tidak menyediakan output_text.
            parts = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        parts.append(content.get("text", ""))
            answer = "\n".join(parts).strip()

        return answer or "Maaf, Sahabat tidak dapat memberikan jawapan sekarang. Sila cuba semula."

    except Exception as e:
        logging.error(f"Ralat Sahabat KPPbNB: {e}")
        return (
            "❌ *Sahabat tidak dapat memproses soalan buat masa ini.*\n\n"
            "Sila cuba semula sebentar lagi atau hubungi pihak Kesatuan."
        )

async def handle_sahabat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_session_active(context):
        await query.message.reply_text(
            "🔐 *Sesi anda telah tamat.*\n\nSila tekan /start untuk pengesahan semula.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    if query.data == 'menu_utama':
        nama = context.user_data.get('nama', 'Ahli')
        await query.message.reply_text(
            f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:",
            parse_mode='Markdown', reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    await query.message.reply_text(
        "🤝 *SAHABAT KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Saya boleh bantu hg faham perkara berkaitan *CA-7, Akta & Peraturan Kerja, "
        "OT, gaji, elaun, cuti, disiplin, kilanan dan hubungan perusahaan*.\n\n"
        "👉 Taip soalan hg dengan bahasa biasa. Contoh:\n"
        "• Saya kena surat tunjuk sebab, apa saya perlu buat?\n"
        "• Berapa kadar OT saya?\n"
        "• Kalau bos suruh kerja hari rehat macam mana?\n"
        "• Macam mana proses kilanan?\n\n"
        "⚠️ Untuk kes serius, Sahabat akan cadangkan pegawai Kesatuan yang sesuai.\n\n"
        "Taip *menu* untuk kembali ke Menu Utama.",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
        ])
    )
    return STATE_SAHABAT_SOALAN

async def sahabat_soalan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_session_active(context):
        await update.message.reply_text(
            "🔐 *Sesi anda telah tamat.*\n\nSila tekan /start untuk pengesahan semula.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    soalan = update.message.text.strip()
    if not soalan:
        return STATE_SAHABAT_SOALAN

    if soalan.lower() in {"menu", "menu utama", "keluar", "exit"}:
        nama = context.user_data.get('nama', 'Ahli')
        await update.message.reply_text(
            f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:",
            parse_mode='Markdown', reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text("🤔 Sahabat sedang semak soalan hg...", parse_mode='Markdown')
    jawapan = await _sahabat_tanya_ai(soalan)
    await update.message.reply_text(
        "🤝 *Sahabat KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        + jawapan,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')],
            [InlineKeyboardButton("🤝 Tanya Lagi", callback_data='menu_sahabat')]
        ])
    )
    return STATE_SAHABAT_SOALAN

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
            "🤝 *Bro & Sis Kesatuan*\n\n"
            "🏛️ No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah.\n\n"
            "👤 *Bro Syahibudil Assaufi bin Abdul Kudus*\n"
            "Presiden\n"
            "📧 syahibudil@bernas.com.my\n\n"
            "👩 *Sis Farah Aqilah binti Bardzan*\n"
            "Setiausaha Agung\n"
            "📧 aqilah@bernas.com.my\n\n"
            "👤 *Bro Khairul Faiz bin Ramizan*\n"
            "Bendahari\n"
            "📧 khairulfaiz@bernas.com.my\n\n"
            "📧 *Email Kesatuan:* kppbnb@gmail.com"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_utama':
        nama = context.user_data.get('nama', 'Ahli')
        text = f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# ==================== MAIN ====================
async def async_main():
    threading.Thread(target=run_web_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    start_choice_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(handle_start_choice, pattern='^(start_ahli|minat_ahli)$')],
        states={
            STATE_VERIFY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_employee_id)],
            STATE_MINAT_NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_nama)],
            STATE_MINAT_PEKERJA: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_pekerja)],
            STATE_MINAT_LOKASI: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_lokasi)],
            STATE_MINAT_JAWATAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_jawatan)],
            STATE_MINAT_TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_telefon)],
            STATE_MINAT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_email)],
            STATE_MINAT_PERTANYAAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, minat_pertanyaan)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(start_choice_conv)

    verify_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_VERIFY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_employee_id)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(verify_conv)

    ot_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_ot_calculator, pattern='^(menu_kiraan|ot_zon_a|ot_zon_b|ot_hari_biasa|ot_hari_biasa_8|ot_hari_biasa_7|ot_hari_rehat|ot_cuti_am)$')],
        states={
            STATE_OT_ZONE: [CallbackQueryHandler(handle_ot_calculator, pattern='^(ot_zon_a|ot_zon_b)$')],
            STATE_OT_DAY: [CallbackQueryHandler(handle_ot_calculator, pattern='^(ot_hari_biasa|ot_hari_biasa_8|ot_hari_biasa_7|ot_hari_rehat|ot_cuti_am)$')],
            STATE_OT_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ot_get_salary)],
            STATE_OT_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ot_get_hours)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(ot_conv)

    aduan_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                handle_aduan,
                pattern='^(menu_aduan|aduan_isu|aduan_gaji|aduan_kebajikan|aduan_keselamatan|aduan_lain|menu_utama)$'
            )
        ],
        states={
            STATE_ADUAN_JENIS: [
                CallbackQueryHandler(
                    handle_aduan,
                    pattern='^(aduan_isu|aduan_gaji|aduan_kebajikan|aduan_keselamatan|aduan_lain|menu_utama)$'
                )
            ],
            STATE_ADUAN_KETERANGAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, terima_aduan)
            ]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    app.add_handler(aduan_conv)

    sahabat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_sahabat, pattern='^(menu_sahabat|menu_utama)$')],
        states={
            STATE_SAHABAT_SOALAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sahabat_soalan),
                CallbackQueryHandler(handle_sahabat, pattern='^(menu_sahabat|menu_utama)$')
            ]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    app.add_handler(sahabat_conv)
    app.add_handler(CallbackQueryHandler(handle_akta, pattern='^(menu_akta|akta_)'))
    app.add_handler(CallbackQueryHandler(handle_ca, pattern='^(menu_ca|ca_|art64_)'))
    app.add_handler(CallbackQueryHandler(handle_other_menus, pattern='^menu_(dokumen|hebahan|profil|hubungi|utama)$'))

    async with app:
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.start()
        await app.updater.start_polling()
        print("Bot KPPbNB LIVE penuh dari awal sampai akhir!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()
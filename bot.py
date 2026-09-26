import os
import asyncio
import threading
import http.server
import socketserver
import logging
import csv
import time
import json
from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo
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

# ==================== AUDIT SAHABAT & STATISTIK ====================
# Fungsi tambahan sahaja: tidak mengubah aliran fungsi bot sedia ada.
STATS_FILE = "sahabat_stats.json"
MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")

def _load_sahabat_stats():
    default = {"date": datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d"), "questions": 0, "users": []}
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == default["date"]:
                data.setdefault("questions", 0)
                data.setdefault("users", [])
                return data
    except Exception as e:
        logging.warning(f"Gagal baca statistik Sahabat: {e}")
    return default

SAHABAT_STATS = _load_sahabat_stats()

def _save_sahabat_stats():
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(SAHABAT_STATS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Gagal simpan statistik Sahabat: {e}")

def _rekod_penggunaan_sahabat(user_id):
    today = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")
    if SAHABAT_STATS.get("date") != today:
        SAHABAT_STATS.clear()
        SAHABAT_STATS.update({"date": today, "questions": 0, "users": []})
    SAHABAT_STATS["questions"] = int(SAHABAT_STATS.get("questions", 0)) + 1
    uid = str(user_id)
    if uid not in SAHABAT_STATS.setdefault("users", []):
        SAHABAT_STATS["users"].append(uid)
    _save_sahabat_stats()

def _ahli_audit_text(update, context):
    user = update.effective_user
    nama = context.user_data.get("nama", "Tidak dipadankan")
    emp_id = context.user_data.get("emp_id", "Tidak dipadankan")
    lokasi = context.user_data.get("lokasi", "Tidak dipadankan")
    telegram_id = user.id if user else "Tidak diketahui"
    return nama, emp_id, lokasi, telegram_id

async def _hantar_audit_sahabat(update, context, soalan, jawapan):
    """Hantar salinan soalan+jawapan Sahabat ke Group Aduan admin sahaja."""
    try:
        nama, emp_id, lokasi, telegram_id = _ahli_audit_text(update, context)
        masa = datetime.now(MALAYSIA_TZ).strftime("%d/%m/%Y %H:%M:%S")
        belum_padanan = not context.user_data.get("verified", False) or not context.user_data.get("emp_id")
        status = "⚠️ AHLI BELUM DIPADANKAN" if belum_padanan else "🔎 UNTUK SEMAKAN ADMIN"
        text = (
            "🤖 SEMAKAN JAWAPAN SAHABAT KPPbNB\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Nama: {nama}\n"
            f"🆔 No. Ahli: {emp_id}\n"
            f"📍 Lokasi: {lokasi}\n"
            f"📱 Telegram ID: {telegram_id}\n"
            f"🕐 Masa: {masa}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "❓ SOALAN AHLI\n"
            f"{soalan}\n\n"
            "🤖 JAWAPAN SAHABAT\n"
            f"{jawapan}\n\n"
            "📚 Rujukan: Berdasarkan sumber yang digunakan oleh Sahabat\n"
            f"{status}"
        )
        # Telegram had mesej 4096 aksara; pecahkan tanpa mengubah kandungan.
        for i in range(0, len(text), 3900):
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text[i:i+3900])
    except Exception as e:
        logging.error(f"Gagal hantar audit Sahabat ke group: {e}")

def _next_0001_malaysia():
    now = datetime.now(MALAYSIA_TZ)
    target = now.replace(hour=0, minute=1, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target

async def _laporan_penggunaan_harian(app):
    """Hantar statistik Sahabat setiap hari pada 00:01 waktu Malaysia."""
    while True:
        target = _next_0001_malaysia()
        await asyncio.sleep(max(1, (target - datetime.now(MALAYSIA_TZ)).total_seconds()))
        try:
            today = datetime.now(MALAYSIA_TZ)
            report_date = (today - timedelta(days=1)).strftime("%d/%m/%Y")
            questions = int(SAHABAT_STATS.get("questions", 0))
            users = len(SAHABAT_STATS.get("users", []))
            report = (
                "📊 LAPORAN PENGGUNAAN SAHABAT KPPbNB\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 Tarikh: {report_date}\n"
                f"👥 Pengguna unik: {users} orang\n"
                f"💬 Jumlah soalan Sahabat: {questions}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📌 Laporan ini untuk kegunaan dalaman admin Kesatuan."
            )
            await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=report)
        except Exception as e:
            logging.error(f"Gagal hantar laporan penggunaan harian: {e}")
        finally:
            # Mula kiraan hari baru selepas laporan dihantar.
            new_date = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")
            SAHABAT_STATS.clear()
            SAHABAT_STATS.update({"date": new_date, "questions": 0, "users": []})
            _save_sahabat_stats()


# Pautan Dokumen Google Drive & SharePoint
URL_KILANAN = "https://drive.google.com/file/d/1KLmiSGJcnV_Wmcwkfyj6LZ17KGdJp92w/view?usp=drive_link"
URL_CA1 = "https://drive.google.com/file/d/1s0KkAqdb2i2XMAg8HgoEvh0tWhiTMcYB/view?usp=drive_link"
URL_CA2 = "https://drive.google.com/file/d/1piIG4_2V8o0ZpQhpvf6pUo9kJutKUKXr/view?usp=drive_link"
URL_CA3 = "https://drive.google.com/file/d/1ZyaSF0CoaY_jrgCS8C2I53kTVC1qb__X/view?usp=drive_link"
URL_CA4 = "https://drive.google.com/file/d/1Hro24UiRlpAP7xQpQ_iuo0iyAMszorFt/view?usp=drive_link"
URL_CA5 = "https://drive.google.com/file/d/1Z41lso7fi3GlVG_UvGpncUkIndN1GaL3/view?usp=drive_link"
URL_CA6 = "https://drive.google.com/file/d/19kQw-6Klinuq1ErF-raLs8-9xoosYroi/view?usp=drive_link"
URL_CA7 = "https://drive.google.com/file/d/1m6bYX3iSczFeJccdKdM9V_acjggw9M00/view?usp=drive_link"
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
            "• Pekerja disahkan layak menerima kenaikan pada 1 Januari sehingga capai maksimum gaji.\n"
            "• Penilaian *Memenuhi Jangkaan dan ke atas*: *3.5% + merit*.\n"
            "• *Di Bawah Jangkaan / Tidak Memuaskan*: *1.5%*.\n"
            "• Kenaikan pertama selepas disahkan: pro rata mengikut bulan perkhidmatan hingga 31 Disember.\n"
            "• Gaji maksimum boleh dipertimbang EIP mengikut prestasi; EIP tidak kumulatif.\n\n"
            "📌 *Artikel 26 – Bonus*\n"
            "• Bonus kontraktual: *1 bulan gaji* bagi pekerja yang disahkan pada atau sebelum 31 Disember.\n"
            "• Belum cukup 1 tahun perkhidmatan: bonus pro rata.\n"
            "• Cuti tanpa gaji termasuk AWOL boleh menyebabkan bonus dikira pro rata.\n"
            "• Bonus tidak dibayar dalam keadaan tatatertib tertentu/berhenti/ditamatkan seperti syarat Artikel 26.\n\n"
            "📌 *Artikel 74 – Semakan Gaji*\n"
            "• Gaji bulanan ahli Kesatuan sahaja diselaraskan sebanyak *4.5%* berdasarkan ketetapan yang digunakan oleh bot."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_waktu_ot':
        text = (
            "⏰ *CA-7: WAKTU KERJA & KERJA LEBIH MASA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 29 – Waktu Bekerja*\n"
            "• Pekerja syif: purata *42 jam seminggu*.\n"
            "• Pekerja lain: *39 jam seminggu*.\n"
            "• Jadual: 2 syif 12 jam atau 3 syif 8 jam; perubahan jadual setakat yang praktik dimaklumkan sekurang-kurangnya 3 hari sebelum berkuat kuasa.\n\n"
            "📌 *Artikel 30 – Kerja Lebih Masa*\n"
            "• OT atas permintaan BERNAS dengan persetujuan pekerja.\n"
            "• Pekerja tidak boleh menolak tanpa alasan munasabah.\n\n"
            "📌 *Artikel 31 – Bayaran OT*\n"
            "• Hari kerja biasa: gaji bulanan × 1.5 × jumlah jam kerja ÷ (26 × jumlah jam kerja biasa).\n"
            "• Had OT: *104 jam sebulan*, tidak termasuk OT hari rehat/cuti umum seperti diperuntukkan.\n"
            "• Cuti gantian: *6–8 jam = 1 hari*; *4–5 jam = ½ hari*, dan boleh dikumpulkan dalam 6 bulan pada tahun berkenaan, tertakluk syarat.\n"
            "• Jika memilih cuti gantian, tidak boleh membuat tuntutan OT bagi jam yang sama."
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
            "📌 *Artikel 43 – Cuti Am*: Cuti bergaji penuh pada cuti am yang diwartakan Kerajaan Persekutuan/Negeri; ada gantian jika jatuh hari rehat atau tambahan jika bertembung cuti tahunan.\n\n"
            "📌 *Artikel 44 – Cuti Tahunan*\n"
            "• <2 tahun: *18 hari* setahun.\n"
            "• 2–5 tahun: *22 hari* setahun.\n"
            "• >5 tahun: *24 hari* setahun.\n"
            "• Baki boleh dilanjutkan hingga 30 Jun tahun berikutnya sehingga 50% daripada kelayakan, tertakluk syarat/kelulusan.\n\n"
            "📌 *Artikel 47 – Cuti Sakit*: *22 hari* setahun tanpa hospital; *60 hari* setahun jika perlu hospital, tertakluk syarat.\n"
            "📌 *Artikel 48 – Sakit Berpanjangan*: 6 bulan gaji penuh + 6 bulan separuh gaji + 6 bulan tanpa gaji, tertakluk rawatan/perakuan.\n"
            "📌 *Artikel 49 – Bersalin*: *98 hari berturut-turut* bergaji penuh, maksimum 5 kelahiran hidup.\n"
            "📌 *Artikel 50 – Ehsan*: antaranya 3 hari bekerja bagi kematian keluarga terdekat dan maksimum 5 hari setahun untuk menjaga/mengiringi keluarga di hospital.\n"
            "📌 *Artikel 51 – Perkahwinan*: *4 hari bekerja* untuk perkahwinan sah pertama, tertakluk syarat.\n"
            "📌 *Artikel 52 – Paterniti*: *7 hari* bagi pekerja lelaki yang telah berkhidmat ≥1 tahun; *3 hari* jika kurang 1 tahun, maksimum 5 kelahiran.\n"
            "📌 *Artikel 55 – Haji/Umrah*: *54 hari berturut-turut* bergaji penuh, sekali sepanjang perkhidmatan, tertakluk syarat kelayakan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_perubatan':
        text = (
            "🏥 *CA-7: PERUBATAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 58 – Faedah Perubatan & Tanggungan*\n"
            "• Tanggungan pesakit luar termasuk pasangan sah, anak ≤19 tahun yang tidak belajar/tidak berkahwin, anak IPT sepenuh masa hingga 23 tahun, anak tiri, anak angkat sah, ibu bapa kandung bagi pekerja yang dilantik sebelum 1/1/2023, dan anak kurang upaya tanpa had umur dengan dokumen sokongan.\n"
            "• Rawatan bersalin termasuk sebelum/selepas bersalin sehingga 5 kali sepanjang perkhidmatan.\n\n"
            "📌 *Artikel 59 – Pesakit Luar*\n"
            "• Had: *RM3,500 setahun*.\n"
            "• Dalam had itu, *RM1,000* untuk pergigian, cermin mata dan rawatan berkala pekerja.\n"
            "• Rawatan pakar biasanya memerlukan rujukan Doktor Panel.\n\n"
            "📌 *Artikel 60 – Pesakit Dalam*\n"
            "• Sehingga 31/12/2026: *RM35,000 setahun* untuk pekerja dan tanggungan; BERNAS boleh pertimbang kes tertentu sehingga RM200,000.\n"
            "• Mulai 1/1/2027: *RM45,000 setahun bagi setiap individu* yang layak.\n"
            "• Room & Board: *RM150 sehari* mulai 1/1/2027.\n"
            "• Kelayakan tanggungan berubah mulai 1/1/2027 seperti diperuntukkan Artikel 60.1A."
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
            "📌 *Artikel 57 – Elaun Dobi*\n"
            "• Tugas rasmi luar kawasan melebihi 3 hari berturut-turut: *RM20 sehari*, dengan resit rasmi. Dobi layan diri tidak dibenarkan untuk tuntutan.\n\n"
            "📌 *Artikel 62 – Penempatan Semula / Secondment*\n"
            "• Boleh dipertimbangkan selepas persetujuan pekerja & majikan, berdasarkan tempoh, lokasi, tujuan dan kesan kepada pekerja/keluarga.\n"
            "• Makan/penginapan untuk tempoh 3 hari sebelum + 5 hari selepas pertukaran; penginapan maksimum 3 bilik dengan resit.\n"
            "• Jika tidak tuntut hotel: lojing tanpa resit untuk pekerja sahaja.\n\n"
            "📌 *Artikel 63 – Elaun Perjalanan*\n"
            "• Kereta: *RM0.75/km*.\n"
            "• Motosikal: *RM0.50/km*.\n"
            "• Tol, parkir & feri: tuntutan dengan resit; tiada/hilang resit boleh dipertimbangkan dengan pengesahan Ketua Bahagian.\n"
            "• Pengangkutan awam/teksi: tambang semasa.\n\n"
            "📌 *Artikel 64 – Elaun Makan*\n"
            "• Tugas rasmi >50 km dan ≥8 jam: *RM115 sehari*.\n"
            "• Sarapan 20% (RM23), tengah hari 40% (RM46), malam 40% (RM46) jika sebahagian makan disediakan.\n"
            "• Gaji ≥RM4,000 dan tidak layak OT: >2–5 jam = RM25; >5 jam = RM50 pada hari bekerja.\n"
            "• Hari rehat/cuti am: >4–8 jam = RM25 atau ½ hari cuti gantian; >8 jam = RM50 atau 1 hari cuti gantian.\n\n"
            "📌 *Artikel 65 – Hotel*\n"
            "• Hotel setaraf *4 bintang, twin sharing* dengan resit; lojing tanpa resit *RM100 semalam*.\n"
            "• Tuntutan hotel tidak dibayar melebihi 3 bulan berturut-turut.\n\n"
            "📌 *Artikel 67 – Sumbangan Beras*: *2 kampit Beras Super Tempatan sekurang-kurangnya 15% (1 kampit 10kg)* atau nilai bersamaan, setiap bulan.\n"
            "📌 *Artikel 71 – Chargeman*: *RM300 sebulan* jika mempunyai sijil dan menjalankan tugas sebagai Chargeman.\n"
            "📌 *Artikel 72 – Syif*: *RM6.50* (4pm–12am), *RM7.00* (12am–8am), dan *RM7.00* (8pm–8am)."
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
# Memerlukan environment variable GEMINI_API_KEY untuk jawapan AI.

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
9. Pastikan jawapan SENTIASA lengkap dan tidak terhenti di tengah ayat. Sebelum menghantar,
   semak bahawa ayat terakhir telah selesai.
10. Untuk soalan fakta mudah, jawab terus dengan fakta utama dahulu. Jika sesuai, gunakan
    2-4 poin ringkas.
11. WAJIB nyatakan nombor ARTIKEL CA-7 yang menjadi rujukan jika jawapan berkaitan CA-7.
    Jika lebih daripada satu artikel digunakan, nyatakan semua artikel yang berkaitan.
12. Selepas jawapan, WAJIB letakkan bahagian:
    "📚 Rujukan CA-7: Artikel XX"
    dan kemudian:
    "🔎 Semakan lanjut: Ahli disaran semak naskhah CA-7 dan rujuk pegawai Kesatuan
    jika melibatkan tafsiran, kes individu atau pertikaian."
13. JANGAN gunakan format Markdown seperti **tebal**, __tebal__, _italic_, atau [link].
    Jawapan mesti dalam teks biasa supaya paparan Telegram kemas dan tidak rosak.
14. Gaya jawapan:
    - Jawab ringkas tetapi padat.
    - Utamakan bullet bernombor atau bullet pendek.
    - Untuk prosedur, gunakan langkah 1, 2, 3 dan seterusnya.
    - Elakkan perenggan yang panjang.
    - Sasarkan 3-7 point utama jika sesuai.
    - Jawab terus soalan ahli tanpa mukadimah panjang.
    - Pastikan setiap ayat lengkap dan jangan terhenti di tengah ayat.
15. Jika hasil carian dokumen tidak benar-benar berkaitan dengan soalan ahli,
    JANGAN gunakan maklumat tersebut untuk menjawab. Jangan padankan soalan
    dengan topik yang hampir sama secara paksa.
16. Jika sumber tidak mengandungi jawapan yang tepat atau Sahabat tidak dapat
    memastikan jawapan dengan tepat, jangan reka atau gunakan pengetahuan umum.
    Gunakan ayat:
    "🤝 Maaf, soalan ni agak mencabar untuk Sahabat jawab dengan tepat.
    Elok rujuk dengan pakar kita untuk jawapan yang lebih tepat. 👍"
"""


def _sahabat_baca_ca7():
    """Baca keseluruhan teks CA-7 tanpa memotong pada 60,000 aksara."""
    candidates = [
        "ca7_kppbnb.txt",
        "/app/ca7_kppbnb.txt",
        "/mnt/data/ca7_kppbnb.txt",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logging.error(f"Gagal baca sumber CA7 untuk Sahabat: {e}")
    return ""



def _sahabat_baca_akta():
    """Baca naskhah Akta Kerja 1955 yang dibekalkan oleh KPPbNB."""
    candidates = [
        "akta_kerja_1955.txt",
        "/app/akta_kerja_1955.txt",
        "/mnt/data/akta_kerja_1955.txt",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logging.error(f"Gagal baca sumber Akta Kerja 1955: {e}")
    return ""


def _sahabat_akta_is_requested(soalan: str) -> bool:
    """Kenal pasti apabila ahli secara jelas meminta rujukan Akta Kerja 1955."""
    import re
    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    akta_terms = [
        "akta kerja", "akta 265", "employment act", "employment act 1955",
        "akta buruh", "di bawah akta", "bawah akta", "ikut akta",
        "mengikut akta", "minimum akta", "hak minimum", "seksyen ", "sek ",
    ]
    return any(term in q for term in akta_terms)


def _sahabat_akta_compare_requested(soalan: str) -> bool:
    import re
    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    return ("akta" in q and any(x in q for x in ["ca-7", "ca7", "perjanjian bersama", "collective agreement", "banding", "beza", "compare"]))


def _sahabat_akta_section_text(akta: str, section_no: str, max_chars: int = 12000) -> str:
    """Ambil bahagian seksyen terakhir yang sepadan, mengelak entri TOC."""
    import re
    if not akta:
        return ""
    pat = re.compile(rf"(?im)^\s*{re.escape(section_no)}\.\s+[^\n]+")
    matches = list(pat.finditer(akta))
    if not matches:
        return ""
    start = matches[-1].start()
    # Cari heading seksyen seterusnya yang lazim dalam naskhah sebenar.
    next_pat = re.compile(r"(?im)^\s*(\d+[A-Z]?)\.\s+[^\n]+")
    nexts = [m for m in next_pat.finditer(akta, matches[-1].end()) if m.start() > start]
    end = nexts[0].start() if nexts else len(akta)
    body = akta[start:end].strip()
    return body[:max_chars]


def _sahabat_jawapan_akta_pantas(soalan: str):
    """Jawapan pantas untuk soalan Akta Kerja 1955 yang jelas."""
    import re
    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    akta = _sahabat_baca_akta()
    if not akta or not _sahabat_akta_is_requested(q):
        return None

    # Soalan senarai cuti dalam Akta: jawab terus, tanpa memanggil Gemini.
    if ("jenis cuti" in q or "senarai cuti" in q or "cuti apa" in q or
        "cuti dalam akta" in q or "cuti dlm akta" in q):
        return (
            "⚖️ Akta Kerja 1955 (Akta 265) – peruntukan utama berkaitan cuti:\n"
            "• Seksyen 37–44 – Cuti bersalin / maternity dan bayaran elaun bersalin.\n"
            "• Seksyen 60D – Hari kelepasan am.\n"
            "• Seksyen 60E – Cuti tahunan.\n"
            "• Seksyen 60F – Cuti sakit dan hospitalisasi.\n"
            "• Seksyen 60FA – Cuti paterniti.\n\n"
            "📌 Untuk kelayakan, tempoh dan syarat setiap cuti, Sahabat akan rujuk seksyen berkenaan dalam naskhah Akta."
        )

    # Nombor seksyen disebut secara jelas.
    m = re.search(r"\b(?:seksyen|sek\.?|section)\s*(\d+[A-Z]?)\b", q, re.I)
    if m:
        sec = m.group(1).upper()
        body = _sahabat_akta_section_text(akta, sec)
        if body:
            return "⚖️ Akta Kerja 1955 – Seksyen " + sec + "\n\n" + body

    section_keywords = [
        ("60FA", ["paterniti", "paternity", "cuti bapa", "cuti ayah"]),
        ("60F", ["cuti sakit", "sakit", "mc", "hospitalisasi", "hospital"]),
        ("60E", ["cuti tahunan", "annual leave"]),
        ("60D", ["cuti am", "cuti umum", "public holiday", "hari kelepasan am"]),
        ("60A", ["waktu kerja", "jam kerja", "kerja lebih masa", "ot", "overtime", "waktu bekerja"]),
        ("60C", ["kerja syif", "shift work", "syif"]),
        ("37", ["cuti bersalin", "maternity", "bersalin"]),
        ("15", ["tak hadir", "tidak hadir", "ketidakhadiran", "awol"]),
        ("19", ["bayaran gaji", "gaji dibayar", "hari ke-7", "gaji"]),
    ]
    for sec, kws in section_keywords:
        if any(k in q for k in kws):
            body = _sahabat_akta_section_text(akta, sec)
            if body:
                return "⚖️ Akta Kerja 1955 – Seksyen " + sec + "\n\n" + body
    return None


def _sahabat_pilih_akta_rujukan(soalan: str, akta: str) -> str:
    """Pilih petikan Akta Kerja 1955 yang berkaitan dengan soalan."""
    import re
    if not akta:
        return ""
    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    m = re.search(r"\b(?:seksyen|sek\.?|section)\s*(\d+[A-Z]?)\b", q, re.I)
    if m:
        body = _sahabat_akta_section_text(akta, m.group(1).upper())
        if body:
            return body
    keys = [
        ("60FA", ["paterniti", "paternity", "cuti bapa"]),
        ("60F", ["cuti sakit", "mc", "hospitalisasi", "hospital"]),
        ("60E", ["cuti tahunan", "annual leave"]),
        ("60D", ["cuti am", "cuti umum", "public holiday"]),
        ("60A", ["waktu kerja", "kerja lebih masa", "overtime", "ot"]),
        ("60C", ["syif", "shift"]),
        ("37", ["cuti bersalin", "maternity", "bersalin"]),
        ("15", ["ketidakhadiran", "tidak hadir", "awol"]),
        ("19", ["bayaran gaji", "gaji dibayar"]),
    ]
    for sec, kws in keys:
        if any(k in q for k in kws):
            body = _sahabat_akta_section_text(akta, sec)
            if body:
                return body
    # Untuk soalan Akta umum, beri TOC/peruntukan utama sebagai konteks.
    return (
        "AKTA KERJA 1955 (AKTA 265)\n"
        "Seksyen berkaitan: 37–44 (maternity), 59–60 (rest day), 60A (hours/OT), "
        "60C (shift), 60D (holidays), 60E (annual leave), 60F (sick leave), "
        "60FA (paternity), 7 dan 7A (more favourable conditions/collective agreement)."
    )


def _sahabat_ca7_sections(ca7: str):
    """Pecahkan CA-7 MASTER kepada 74 artikel secara automatik."""
    import re
    if not ca7:
        return []
    matches = list(re.finditer(r"(?im)^ARTIKEL\s+(\d+)\s*[–-]\s*([^\n]+)", ca7))
    sections = []
    for i, m in enumerate(matches):
        no = int(m.group(1))
        if no < 1 or no > 74:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(ca7)
        body = ca7[m.start():end].strip()
        sections.append((no, m.group(2).strip(), body))
    sections.sort(key=lambda x: x[0])
    return sections


def _sahabat_ringkas_artikel(body: str, max_chars: int = 1500) -> str:
    """Paparkan petikan ringkas daripada naskhah sebenar tanpa mereka fakta."""
    import re
    text = re.sub(r"\n\s*Wakil Padiberas Nasional Berhad.*?(?=\n|$)", "", body, flags=re.I)
    text = text.replace("[JADUAL]", "\n").replace("[/JADUAL]", "\n")
    text = re.sub(r"\n{2,}", "\n", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    # Jangan potong di tengah perkataan jika boleh.
    cut = cut.rsplit(" ", 1)[0]
    return cut + "\n… Untuk syarat lengkap, rujuk naskhah CA-7."


# ==================== CA-7 NUMERIC MASTER / ANGKA TERKUNCI ====================
# Dibina daripada naskhah CA-7 yang telah disemak. Nilai di sini digunakan
# sebagai kunci untuk soalan yang meminta kadar, hari, RM, peratus, tempoh,
# gred/gaji dan angka lain supaya Gemini tidak menggantikan angka sumber.
CA7_NUMERIC_MASTER_TEXT = "CA-7 NUMERIC MASTER KPPbNB — RUJUKAN ANGKA TERKUNCI\nSumber: Perjanjian Bersama Yang Ke-Tujuh KPPbNB-BERNAS, berkuat kuasa 1.1.2026–31.12.2028.\nArahan: Nilai angka di bawah ialah nilai terkunci untuk jawapan bot. Jangan tukar, bulatkan, meneka atau menggantikan dengan angka lain.\n\nArtikel 3: 1 Januari 2026 – 31 Disember 2028.\nArtikel 15: Level 1 = 7 hari bekerja; Level 2 = 7 hari bekerja; Level 3 perbincangan = 14 hari; Level 4 = 60 hari; aduan awal dalam 7 hari dari kejadian.\nArtikel 18: Permohonan aktiviti kesatuan sekurang-kurangnya 10 hari sebelum aktiviti.\nArtikel 21: Cuti tugas kesatuan 7 hari setahun bagi setiap Exco; maksimum 3 Exco pada satu masa.\nArtikel 23: Penarikan persetujuan potongan yuran memerlukan notis bertulis 2 bulan.\nArtikel 25: Memenuhi Jangkaan dan ke atas = 3.5% + merit; Di Bawah Jangkaan/Tidak Memuaskan = 1.5%; EIP tidak kumulatif.\nArtikel 26: Bonus = 1 bulan gaji; perkhidmatan kurang 1 tahun = prorata; disahkan selewat-lewatnya 31 Disember setiap tahun.\nArtikel 27: Notis <2 tahun = 4 minggu; 2–5 tahun = 6 minggu; >5 tahun = 8 minggu.\nArtikel 28: Tidak hadir lebih 2 hari bekerja berturut-turut tanpa kebenaran awal, kecuali alasan munasabah/notifikasi seperti diperuntukkan.\nArtikel 29: Syif purata 42 jam/minggu; bukan syif 39 jam/minggu; 2 syif = 12 jam/syif; 3 syif = 8 jam/syif; rehat 30 minit bagi setiap 5 jam kerja berterusan jika OT dijadualkan; perubahan jadual dimaklumkan sekurang-kurangnya 3 hari.\nArtikel 31: OT hari kerja biasa = 1.5 × kadar jam biasa; had OT = 104 jam/bulan; cuti gantian 6–8 jam = 1 hari; 4–5 jam = 1/2 hari; cuti gantian boleh dikumpul dalam 6 bulan tahun berkenaan.\nArtikel 34: Tempoh memangku >28 hari berturut-turut; cuti tahunan/sakit 14 hari atau lebih berturut-turut semasa memangku = tiada elaun; elaun 15%–25% daripada gaji permulaan gred yang ditanggung.\nArtikel 35: Tempoh memangku maksimum 6 bulan.\nArtikel 36: Persaraan pilihan lelaki 50 tahun; wajib 60 tahun; wanita pilihan 45 tahun; wajib 60 tahun.\nArtikel 37: Caruman majikan/faedah persaraan >20 tahun = 18%; >10 hingga 20 tahun = 16%; <10 tahun = 13%. Ini peruntukan CA-7 dan berbeza daripada kadar statutori KWSP biasa.\nArtikel 38: Pekerja tetap dengan tempoh perkhidmatan <1 tahun tidak layak di bawah skim faedah retrenchment tersebut.\nArtikel 40: Insurans = 36 bulan × gaji terakhir.\nArtikel 44: Cuti tahunan <2 tahun = 18 hari/tahun; 2–5 tahun = 22 hari/tahun; >5 tahun = 24 hari/tahun; bawa ke hadapan sehingga 30 Jun tahun berikutnya; maksimum carry-forward = 50% kelayakan sebenar.\nArtikel 45: Cuti tanpa gaji maksimum 3 bulan sepanjang perkhidmatan.\nArtikel 47: Cuti sakit tanpa hospital = 22 hari/tahun; jika perlu hospital = 60 hari/tahun.\nArtikel 48: Cuti sakit berpanjangan: 6 bulan pertama gaji penuh; 6 bulan kedua separuh gaji; 6 bulan ketiga tanpa gaji.\nArtikel 49: Cuti bersalin = 98 hari berturut-turut; maksimum 5 kelahiran hidup; keguguran sebelum minggu 22 = cuti sakit biasa; boleh bermula pada/selepas minggu 28; cuti tanpa gaji selepas bersalin = 90 hari.\nArtikel 50: Kematian keluarga = 3 hari bekerja; menjaga/mengiringi pasangan/anak/ibu bapa di hospital = maksimum 5 hari bekerja/tahun; bencana alam = 2 hari bekerja; kuarantin anak = 3 hari; bantuan pengurusan pengebumian = RM1,000.\nArtikel 51: Cuti kahwin = 4 hari bekerja berturut-turut; permohonan sekurang-kurangnya 1 minggu sebelum cuti.\nArtikel 52: Paterniti ≥1 tahun perkhidmatan = 7 hari berturut-turut; <1 tahun = 3 hari berturut-turut; maksimum 5 kelahiran; notis sekurang-kurangnya 30 hari sebelum kelahiran isteri.\nArtikel 53: Cuti khas maksimum 30 hari dalam satu tahun kalendar.\nArtikel 55: Haji/Umrah = 54 hari berturut-turut, maksimum keseluruhan dan sekali sahaja; pekerja kontrak ≥1 tahun; pekerja tetap ≥3 tahun dan telah disahkan.\nArtikel 56: Cuti peperiksaan = 1 hari pada hari peperiksaan; cuti belajar = 2 hari bagi setiap peperiksaan; maksimum 5 hari/tahun; jika 2 atau lebih peperiksaan pada hari sama, 2 hari cuti belajar boleh diberi dalam seminggu sebelum peperiksaan.\nArtikel 57: Dobi = RM20/hari; tugas rasmi luar kawasan >3 hari berturut-turut; resit diperlukan; dobi layan diri tidak boleh dituntut.\nArtikel 58: Anak ≤19 tahun jika tidak belajar/tidak berkahwin; anak pendidikan tinggi sepenuh masa sehingga 23 tahun; anak tiri/anak angkat sah; ibu bapa kandung bagi pekerja dilantik sebelum 1 Januari 2023; anak OKU tiada had umur; rawatan bersalin maksimum 5 kali sepanjang perkhidmatan.\nArtikel 59: Pesakit luar = RM3,500/tahun; dalam jumlah itu RM1,000 untuk pergigian, cermin mata dan rawatan berkala, bagi pekerja sendiri.\nArtikel 60: Sehingga 31 Disember 2026 = RM35,000/tahun untuk pekerja + tanggungan; BERNAS boleh mempertimbangkan kes sehingga RM200,000; mulai 1 Januari 2027 = RM45,000/tahun bagi setiap individu yang layak; bilik & makan = RM150/hari; mulai 2027 anak biasa ≤17 tahun jika tidak belajar/tidak berkahwin; anak pendidikan tinggi sepenuh masa sehingga 23 tahun.\nArtikel 61: Bersalin normal pekerja = RM3,000; Caesarean pekerja di hospital swasta = RM6,000; isteri pekerja normal = RM3,000; isteri Caesarean = RM6,000.\nArtikel 62: Makan = 3 hari sebelum + 5 hari selepas; hotel = 3 hari sebelum + 5 hari selepas; maksimum 3 bilik; jika tiada tuntutan hotel, lojing untuk pekerja sahaja bagi tempoh 3 + 5 hari.\nArtikel 63: Kereta = RM0.75/km; motosikal = RM0.50/km; tol/parkir/feri dibayar balik tertakluk resit/pengesahan.\nArtikel 64: Tugas rasmi >50 km dan 8 jam atau lebih; elaun makan RM115/hari; sarapan 20%=RM23; makan tengah hari 40%=RM46; makan malam 40%=RM46; gaji RM4,000+ tanpa OT: hari bekerja >2–5 jam=RM25; >5 jam=RM50; hari rehat/cuti umum >4–8 jam=RM25 atau 1/2 hari gantian; >8 jam=RM50 atau 1 hari gantian.\nArtikel 65: Hotel standard 4 bintang; twin sharing; lojing tanpa resit RM100/malam; hotel maksimum 3 bulan berturut-turut.\nArtikel 66: Operasi = 4 T-shirt + 2 seluar + 1 pasang kasut keselamatan; pejabat = 1 baju BERNAS.\nArtikel 67: 2 pek beras Super Tempatan; minimum 15%; 1 pek = 10kg; bulanan.\nArtikel 71: Elaun Chargeman = RM300/bulan.\nArtikel 72: 8 pagi–4 petang = RM0.00; 4 petang–12 malam = RM6.50; 12 malam–8 pagi = RM7.00; 2 syif 8 pagi–8 malam = RM0.00; 2 syif 8 malam–8 pagi = RM7.00.\nArtikel 74: Pelarasan gaji ahli Kesatuan = 4.5%. Jangan gunakan 5% sebagai kadar jawapan. Lampiran I: T5 RM3,000–6,300; T4 RM2,600–5,200; T3 RM2,100–4,000; T2 RM1,900–3,200; T1 RM1,700–2,800; S5 RM2,800–5,400; S4 RM2,400–4,500; S3 RM2,100–3,600; S2 RM1,900–3,000; S1 RM1,700–2,800.\n\nLOCK KHAS:\n- Artikel 25.5(b) = 1.5%, bukan 2%.\n- Artikel 74.1 = 4.5% sebagai angka yang digunakan bot; jangan paparkan 5%.\n- Artikel 60 berubah pada 1 Januari 2027: RM35,000 pekerja+tanggungan sehingga 31/12/2026, kemudian RM45,000 seorang yang layak.\n"


def _sahabat_numeric_master_by_article(no: int):
    import re
    m = re.search(rf"(?m)^Artikel {no}: (.+)$", CA7_NUMERIC_MASTER_TEXT)
    return m.group(1).strip() if m else None


def _sahabat_numeric_query(soalan: str) -> bool:
    q = (soalan or "").lower()
    markers = [
        "berapa", "kadar", "rate", "rm", "%", "peratus", "hari", "jam",
        "tahun", "bulan", "minggu", "minggu", "tempoh", "umur", "gaji",
        "minimum", "maksimum", "layak", "kelayakan", "notis", "caruman",
        "elaun", "mileage", "km", "kg", "syif", "shift", "increment",
        "kenaikan", "potongan", "bawa ke hadapan", "carry forward"
    ]
    return any(x in q for x in markers)


def _sahabat_numeric_grade_answer(soalan: str):
    import re
    q = (soalan or "").lower()
    if not any(x in q for x in ["gred", "gaji", "minimum", "maksimum", "tangga"]):
        return None
    m = re.search(r"\b([st][1-5])\b", q)
    if not m:
        return None
    g = m.group(1).upper()
    # Nilai Lampiran I dikunci terus.
    grades = {
        "T5":"RM3,000–6,300", "T4":"RM2,600–5,200", "T3":"RM2,100–4,000",
        "T2":"RM1,900–3,200", "T1":"RM1,700–2,800",
        "S5":"RM2,800–5,400", "S4":"RM2,400–4,500", "S3":"RM2,100–3,600",
        "S2":"RM1,900–3,000", "S1":"RM1,700–2,800"
    }
    if g in grades:
        return f"📌 Artikel 74 – Lampiran I, Gred {g}\n• Julat gaji: {grades[g]}."
    return None


def _sahabat_numeric_quick_answer(soalan: str, sections):
    import re
    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    if not _sahabat_numeric_query(q):
        return None

    grade = _sahabat_numeric_grade_answer(q)
    if grade:
        return grade

    # Jika ahli menyebut Artikel N, guna angka terkunci artikel itu.
    m = re.search(r"\b(?:artikel|art\.|article)\s*[-:]?\s*(\d{1,2})\b", q)
    if m:
        no = int(m.group(1))
        value = _sahabat_numeric_master_by_article(no)
        if value:
            return f"📌 Artikel {no} – Angka CA-7 terkunci\n• {value}"

    # Untuk soalan topik tanpa nombor artikel, skor topik seperti Quick Answer sedia ada.
    scores = []
    for no, title, body in sections:
        score = 0
        for kw in CA7_TOPIC_MAP.get(no, []):
            if kw in q:
                score += 12 if (" " in kw or "%" in kw) else 7
        title_words = [w for w in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", title.lower()) if len(w) >= 5]
        score += min(6, sum(1 for w in title_words if w in q))
        scores.append((score, no, title))
    scores.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    if not scores or scores[0][0] < 12:
        return None
    if len(scores) > 1 and scores[0][0] == scores[1][0] and scores[0][0] < 18:
        return None

    no = scores[0][1]
    value = _sahabat_numeric_master_by_article(no)
    if value:
        return f"📌 Artikel {no} – {scores[0][2]}\n• {value}"
    return None


CA7_TOPIC_MAP = {1: ['pihak terikat', 'pihak-pihak', 'siapa terikat'],
 2: ['objektif perjanjian', 'tujuan perjanjian'],
 3: ['tempoh ca7', 'tempoh perjanjian', 'tarikh kuatkuasa', 'berkuatkuasa'],
 4: ['pemakaian perjanjian', 'siapa terpakai', 'terpakai kepada'],
 5: ['naskah sahih', 'naskah sah'],
 6: ['salinan perjanjian', 'salinan naskah'],
 7: ['perundangan', 'undang-undang dalam ca7'],
 8: ['tafsiran', 'definisi', 'maksud'],
 9: ['ikatan perjanjian'],
 10: ['pengiktirafan bernas'],
 11: ['pengiktirafan kesatuan', 'skop kesatuan', 'pengiktirafan union'],
 12: ['keharmonian perusahaan', 'industrial harmony'],
 13: ['penyelesaian muktamad', 'final settlement'],
 14: ['timbangtara', 'arbitration'],
 15: ['kilanan', 'aduan', 'grievance', 'proses kilanan'],
 16: ['keahlian kesatuan', 'ahli kesatuan', 'syarat ahli'],
 17: ['tugas rasmi kesatuan', 'tugas rasmi'],
 18: ['aktiviti kesatuan'],
 19: ['jaminan', 'guarantee'],
 20: ['produktiviti', 'prestasi'],
 21: ['cuti kesatuan', 'cuti atas tugas kesatuan'],
 22: ['papan kenyataan kesatuan', 'noticeboard kesatuan'],
 23: ['yuran kesatuan', 'potongan yuran'],
 24: ['kwsp', 'perkeso', 'sip', 'caruman kwsp', 'caruman perkeso'],
 25: ['kenaikan gaji tahunan', 'increment', 'annual increment', '3.5%', '1.5%', 'merit', 'eip'],
 26: ['bonus', 'bonus kontraktual'],
 27: ['notis berhenti', 'notis penamatan', 'letak jawatan', 'perletakan jawatan'],
 28: ['ketidakhadiran', 'tidak hadir', 'absent', 'awol'],
 29: ['waktu kerja', 'waktu bekerja', 'jam bekerja', '39 jam', '42 jam', 'jadual kerja'],
 30: ['kerja lebih masa', 'ot', 'overtime', 'persetujuan ot'],
 31: ['bayaran ot', 'kadar ot', 'kiraan ot', '104 jam', 'formula ot'],
 32: ['keperluan tugas', 'giliran kerja', 'kerja hujung minggu'],
 33: ['kenaikan pangkat', 'naik pangkat', 'promosi', 'gred jawatan'],
 34: ['elaun memangku', 'tanggungan kerja', 'menanggung kerja'],
 35: ['tempoh memangku', 'berapa lama memangku'],
 36: ['umur persaraan', 'persaraan wajib', 'persaraan pilihan'],
 37: ['faedah persaraan', 'caruman majikan', 'caruman majikan kwsp', '13%', '16%', '18%'],
 38: ['retrenchment', 'lebihan pekerja', 'faedah penamatan', 'pemberhentian kerana lebihan'],
 39: ['hilang upaya pekerjaan', 'disability', 'insurans hilang upaya'],
 40: ['faedah kematian', 'insurans hayat', 'gtl', 'gpa', 'pampasan kematian'],
 41: ['skim pemisahan sukarela', 'vss', 'pemisahan sukarela'],
 42: ['kemalangan kerja', 'kemalangan perusahaan', 'gantirugi kecederaan'],
 43: ['cuti am', 'cuti umum', 'public holiday'],
 44: ['cuti tahunan', 'annual leave', '18 hari', '22 hari', '24 hari'],
 45: ['cuti tanpa gaji', 'unpaid leave'],
 46: ['kemalangan perusahaan', 'cuti sakit kemalangan'],
 47: ['cuti sakit', 'mc', 'sick leave'],
 48: ['cuti sakit berpanjangan', 'long sick leave', 'penyakit kronik'],
 49: ['cuti bersalin', 'maternity', '98 hari'],
 50: ['cuti ehsan', 'kematian keluarga', 'bencana alam', 'jaga ibu bapa hospital'],
 51: ['cuti perkahwinan', 'cuti kahwin'],
 52: ['cuti paterniti', 'paternity', 'cuti bapa'],
 53: ['cuti khas', 'special leave'],
 54: ['cuti kuarantin', 'quarantine'],
 55: ['haji', 'umrah', 'cuti haji', 'cuti umrah'],
 56: ['cuti belajar', 'cuti peperiksaan', 'peperiksaan'],
 57: ['elaun dobi', 'dobi', 'laundry allowance'],
 58: ['faedah perubatan', 'panel rawatan', 'tanggungan perubatan', 'ibu bapa perubatan'],
 59: ['pesakit luar', 'outpatient', 'klinik panel', 'rm3500', 'pergigian', 'cermin mata'],
 60: ['pesakit dalam', 'inpatient', 'hospital', 'rm35000', 'rm45000', 'room board'],
 61: ['rawatan bersalin', 'kos bersalin', 'medical maternity'],
 62: ['penempatan semula', 'secondment', 'pinjaman sementara', 'relocation', 'lojing penempatan'],
 63: ['elaun perjalanan', 'mileage', 'km', 'kereta sendiri', 'motosikal', 'tol', 'parkir', 'parking', 'feri'],
 64: ['elaun makan', 'rm115', 'sarapan', 'tengahari', 'makan malam'],
 65: ['penginapan hotel', 'hotel', 'twin sharing', '4 bintang', 'lojing'],
 66: ['pakaian seragam', 'uniform', 'safety shoes', 'kasut keselamatan'],
 67: ['sumbangan beras', 'subsidi beras', 'beras'],
 68: ['anugerah cadangan', 'cadangan', 'insentif cadangan'],
 69: ['jawatankuasa keselamatan', 'keselamatan kesihatan pekerjaan', 'jkkp', 'persekitaran'],
 70: ['lesen memandu', 'lesen pemandu'],
 71: ['chargeman', 'elaun chargeman'],
 72: ['elaun syif', 'syif', 'shift allowance'],
 73: ['disiplin', 'tatatertib', 'tindakan disiplin'],
 74: ['semakan gaji', 'pelarasan gaji', '4.5%', 'lima peratus', 'gaji ahli kesatuan']}


def _sahabat_jawapan_pantas(soalan: str):
    """Quick Answer CA-7 berasaskan MASTER SOURCE 74 artikel.
    - Soalan 'Artikel N' terus mengambil Artikel N.
    - Soalan topik menggunakan padanan kata kunci berkeyakinan tinggi.
    - Jika padanan tidak cukup jelas, pulangkan None supaya Gemini semak konteks.
    """
    import re
    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    ca7 = _sahabat_baca_ca7()
    sections = _sahabat_ca7_sections(ca7)
    if not sections:
        return None

    by_no = {n: (title, body) for n, title, body in sections}

    # Angka CA-7 dikunci sebelum padanan AI/keyword biasa.
    numeric_answer = _sahabat_numeric_quick_answer(soalan, sections)
    if numeric_answer:
        return numeric_answer

    # KWSP: gabungkan rujukan CA-7 + kadar KWSP. Jangan berhenti pada Artikel 24.
    # Artikel 24 = CA-7 tidak menetapkan kadar potongan pekerja.
    # Artikel 37 = kadar Caruman Majikan KWSP mengikut tempoh perkhidmatan.
    # Rujukan KWSP semasa: pekerja warganegara bawah 60 tahun lazimnya 11%;
    # syer majikan 13% bagi upah RM5,000 dan ke bawah, 12% bagi melebihi RM5,000.
    if "kwsp" in q or "kumpulan wang simpanan pekerja" in q:
        years = None
        ym = re.search(r"(?:kerja|khidmat|perkhidmatan|servis)?\s*(\d{1,2})\s*tahun", q)
        if ym:
            years = int(ym.group(1))

        # Kadar CA-7 Artikel 37 (caruman majikan untuk faedah persaraan).
        ca7_rate = None
        if years is not None:
            if years > 20:
                ca7_rate = "18%"
            elif years > 10:
                ca7_rate = "16%"
            else:
                ca7_rate = "13%"

        # Jika soalan jelas meminta potongan/syer pekerja, beri syer pekerja
        # bersama syer majikan dan CA-7, bukan jawapan Artikel 24 sahaja.
        if any(x in q for x in ["potongan", "pekerja", "majikan", "berapa", "kadar", "peratus", "%", "gaji"]):
            return (
                "📌 KWSP – Rujukan KWSP + CA-7\n"
                "• Syer pekerja KWSP: rujuk Jadual Ketiga KWSP. Bagi pekerja warganegara Malaysia bawah 60 tahun, kadar berkanun ialah 11%.\n"
                "• Syer majikan KWSP: bagi pekerja warganegara Malaysia bawah 60 tahun, 13% untuk upah RM5,000 dan ke bawah; 12% untuk upah melebihi RM5,000. Jumlah RM sebenar hendaklah ikut jadual caruman KWSP, bukan semata-mata darab peratus bagi julat upah biasa.\n"
                + (f"• CA-7 Artikel 37 – tempoh perkhidmatan {years} tahun: caruman majikan untuk faedah persaraan ialah {ca7_rate}.\n" if years is not None else "• CA-7 Artikel 37 – caruman majikan untuk faedah persaraan: <10 tahun = 13%; >10 hingga 20 tahun = 16%; >20 tahun = 18%.\n")
                + "• Artikel 24 CA-7 tidak menetapkan peratus potongan pekerja; kadar potongan pekerja dirujuk kepada ketetapan/Jadual KWSP.\n\n"
                "Jika nak kira JUMLAH RM potongan pekerja dan caruman majikan, beri gaji/upah bulanan dan umur supaya Sahabat boleh semak julat Jadual KWSP."
            )

    # 1) Permintaan Artikel N — paling tepat dan tidak bergantung kepada AI.
    m = re.search(r"\b(?:artikel|art\.|article)\s*[-:]?\s*(\d{1,2})\b", q)
    if m:
        no = int(m.group(1))
        if no in by_no:
            title, body = by_no[no]
            return f"📌 Artikel {no} – {title}\n\n" + _sahabat_ringkas_artikel(body)

    # Struktur gred Lampiran I dalam Artikel 74.
    gm = re.search(r"\b([st][1-5])\b", q)
    if gm and any(x in q for x in ["gred", "gaji", "minimum", "maksimum", "tangga", "berapa"]):
        gred = gm.group(1).upper()
        if 74 in by_no:
            body74 = by_no[74][1]
            for line in body74.splitlines():
                if re.search(rf"\b{re.escape(gred)}(?:\(T\))?\b", line, flags=re.I) and "|" in line:
                    return f"📌 Artikel 74 – Lampiran I, Gred {gred}\n{line.strip()}"
            return f"📌 Artikel 74 – Lampiran I\nSila rujuk jadual gred {gred} dalam naskhah CA-7."

    # 2) Soalan umum tentang JENIS CUTI dalam CA-7 — jawab terus daripada
    # MASTER SOURCE supaya tidak perlu menunggu Gemini untuk soalan senarai.
    # Artikel cuti utama ialah 43 hingga 56; Artikel 21 ialah cuti kesatuan.
    cuti_umum_markers = [
        "jenis cuti", "senarai cuti", "cuti dalam ca", "cuti dlm ca",
        "cuti dalam ca7", "cuti dlm ca7", "cuti apa ada",
        "apa jenis cuti", "jenis-jenis cuti", "jenis2 cuti",
        "senarai jenis cuti", "cuti yang ada dalam ca"
    ]
    if any(marker in q for marker in cuti_umum_markers):
        nombor_cuti = [21, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56]
        lines = ["🏖️ Jenis Cuti / Peruntukan Berkaitan Cuti Dalam CA-7", ""]
        for no in nombor_cuti:
            if no in by_no:
                title = by_no[no][0].strip()
                lines.append(f"• Artikel {no} – {title}")
        lines.append("")
        lines.append("📌 Untuk kelayakan, tempoh dan syarat setiap cuti, rujuk artikel berkenaan dalam CA-7.")
        return "\n".join(lines)

    # 3) Soalan fakta yang kita tahu CA-7 sendiri tidak menyatakan kadar.
    if ("kwsp" in q or "kumpulan wang simpanan pekerja" in q) and any(
        x in q for x in ["potongan", "berapa peratus", "berapa %", "kadar pekerja", "percent", "%"]
    ):
        return (
            "📌 Artikel 24 CA-7 menyatakan BERNAS akan mencarum kepada KWSP, PERKESO dan SIP "
            "atau badan berkanun yang diwajibkan kerajaan.\n"
            "• Artikel 24 tidak menyatakan peratus potongan/caruman pekerja.\n"
            "• Jadi, jangan gunakan Artikel 24 untuk mendakwa satu peratus tertentu."
        )

    # 4) Kadar khusus yang boleh dijawab terus daripada naskhah.
    if ("syif" in q or "shift" in q) and any(x in q for x in ["berapa", "kadar", "rate", "rm", "4 petang", "12 malam", "8 malam"]):
        return (
            "📌 Artikel 72 – Elaun Syif\n"
            "• 8.00 pagi–4.00 petang: RM0.00\n"
            "• 4.00 petang–12.00 malam: RM6.50\n"
            "• 12.00 malam–8.00 pagi: RM7.00\n"
            "• 8.00 malam–8.00 pagi: RM7.00\n"
            "Rujukan: Artikel 72 CA-7."
        )

    if ("chargeman" in q) and any(x in q for x in ["elaun", "berapa", "rm", "kadar"]):
        return "📌 Artikel 71 – Elaun Chargeman\nBERNAS membayar RM300 sebulan kepada pekerja yang mempunyai sijil kelayakan Chargeman dan menjalankan tugas sebagai Chargeman."

    if any(x in q for x in ["mileage", "elaun perjalanan", "berapa sen", "per km", "per kilometer", "kereta sendiri", "motosikal"]) and any(x in q for x in ["berapa", "kadar", "rate", "rm", "sen", "km"]):
        return (
            "📌 Artikel 63 – Elaun Perjalanan\n"
            "• Kereta sendiri: RM0.75/km.\n"
            "• Motosikal: RM0.50/km.\n"
            "• Tol, parkir dan feri boleh dibayar balik tertakluk resit/pengesahan Ketua Bahagian jika tiada resit.\n"
            "• Pengangkutan awam termasuk teksi: tambang semasa."
        )

    if ("cuti tahunan" in q or "annual leave" in q) and any(x in q for x in ["berapa", "hari", "kelayakan", "layak"]):
        return (
            "📌 Artikel 44 – Cuti Tahunan\n"
            "• Kurang 2 tahun: 18 hari setahun.\n"
            "• 2 hingga 5 tahun: 22 hari setahun.\n"
            "• Lebih 5 tahun: 24 hari setahun.\n"
            "• Kelayakan dikira secara prorata."
        )

    if ("ot" in q or "kerja lebih masa" in q or "overtime" in q) and any(x in q for x in ["104", "had", "maksimum", "berapa jam"]):
        return (
            "📌 Artikel 31.4 – Had OT\n"
            "• Sehingga 104 jam sebulan.\n"
            "• Had ini tidak termasuk OT pada hari rehat atau cuti umum yang diwartakan seperti dinyatakan dalam Peraturan-Peraturan Kerja (Had Kerja Lebih Masa) 1980."
        )

    if ("ot" in q or "kerja lebih masa" in q or "overtime" in q) and any(x in q for x in ["kadar", "formula", "cara kira", "macam mana kira", "bayaran", "1.5"]):
        return (
            "📌 Artikel 31.1 – Bayaran OT hari kerja biasa\n"
            "Formula: gaji bulanan × 1.5 × jumlah jam kerja ÷ (26 × jumlah jam kerja biasa).\n"
            "• Untuk kiraan kes tertentu, gunakan menu 🧮 Kiraan OT & Elaun."
        )

    if ("semakan gaji" in q or "pelarasan gaji" in q or "4.5%" in q or "lima peratus" in q) and "gaji" in q:
        return (
            "📌 Artikel 74.1 – Semakan Gaji\n"
            "• Gaji bulanan ahli Kesatuan sahaja diselaraskan sebanyak 4.5%."
        )

    # 5) Padanan topik untuk semua 74 artikel.
    scores = []
    for no, title, body in sections:
        score = 0
        for kw in CA7_TOPIC_MAP.get(no, []):
            if kw in q:
                # Frasa khusus diberi berat lebih tinggi.
                score += 12 if " " in kw or "%" in kw else 7
        # Tajuk artikel hanya sebagai sokongan, bukan padanan tunggal untuk kata umum.
        title_words = [w for w in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", title.lower()) if len(w) >= 5]
        score += min(6, sum(1 for w in title_words if w in q))
        scores.append((score, no, title, body))

    scores.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    if not scores or scores[0][0] < 12:
        return None

    # Elak jawapan salah apabila dua artikel hampir sama kuat.
    if len(scores) > 1 and scores[0][0] == scores[1][0] and scores[0][0] < 18:
        return None

    _, no, title, body = scores[0]
    return f"📌 Artikel {no} – {title}\n\n" + _sahabat_ringkas_artikel(body)





def _sahabat_pilih_rujukan(soalan: str, ca7: str) -> str:
    """Pilih petikan artikel CA-7 yang paling berkaitan.
    Sumber mesti datang daripada MASTER SOURCE tempatan.
    """
    import re
    sections = _sahabat_ca7_sections(ca7)
    if not sections:
        return ""

    q = re.sub(r"\s+", " ", (soalan or "").lower().strip())
    by_no = {n: (title, body) for n, title, body in sections}

    # Jika ahli menyebut nombor artikel, pilih artikel itu dahulu.
    m = re.search(r"\b(?:artikel|art\.|article)\s*[-:]?\s*(\d{1,2})\b", q)
    if m and int(m.group(1)) in by_no:
        no = int(m.group(1))
        return by_no[no][1][:12000]

    scores = []
    for no, title, body in sections:
        score = 0
        for kw in CA7_TOPIC_MAP.get(no, []):
            if kw in q:
                score += 12 if (" " in kw or "%" in kw) else 7
        # Padanan tajuk hanya sebagai sokongan.
        for word in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", title.lower()):
            if len(word) >= 5 and word in q:
                score += 2
        scores.append((score, no, body))

    scores.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    selected = [x for x in scores[:2] if x[0] >= 12]

    # Jika dua topik hampir sama kuat, beri kedua-duanya supaya Gemini tidak
    # membuat padanan paksa.
    if len(selected) == 2 and selected[0][0] == selected[1][0]:
        return "\n\n====================\n\n".join(x[2][:10000] for x in selected)

    if selected:
        return selected[0][2][:12000]

    return ""
def _sahabat_kemas_jawapan(jawapan: str, source_label: str = "CA-7") -> str:
    """Kemas jawapan Gemini supaya Telegram memaparkan teks biasa yang kemas.
    Tambah rujukan artikel dan peringatan semakan lanjut secara konsisten.
    """
    import re
    text = (jawapan or "").strip()
    if not text:
        return text

    # Buang markdown yang biasa Gemini keluarkan kerana mesej akhir dihantar
    # tanpa parse_mode untuk elakkan Telegram BadRequest akibat markdown rosak.
    text = text.replace("```", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.S)
    text = re.sub(r"__(.*?)__", r"\1", text, flags=re.S)
    text = re.sub(r"(?<!\*)\*(?!\s)(.*?)(?<!\s)\*(?!\*)", r"\1", text, flags=re.S)
    text = re.sub(r"(?<!\w)_(.*?)(?<!\w)_", r"\1", text, flags=re.S)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Elak AI menambah label yang berulang.
    text = re.sub(r"^\s*(Jawapan|Jawapan AI)\s*:\s*", "", text, flags=re.I)

    # Cari semua nombor artikel yang dinyatakan oleh AI.
    articles = []
    for m in re.finditer(r"\b(?:artikel|art\.)\s*(\d{1,2})(?:\.\d+)?\b", text, flags=re.I):
        no = int(m.group(1))
        if 1 <= no <= 74 and no not in articles:
            articles.append(no)

    # Buang bahagian rujukan/semakan lama jika AI sudah menghasilkan sendiri,
    # kemudian bina footer standard supaya format sentiasa sama.
    text = re.sub(r"\n*📚\s*Rujukan CA-7:.*?(?=\n|$)", "", text, flags=re.I)
    text = re.sub(r"\n*🔎\s*Semakan lanjut:.*$", "", text, flags=re.I | re.S).strip()

    if source_label == "Akta Kerja 1955":
        text = re.sub(r"\n*📚\s*Rujukan CA-7:.*?(?=\n|$)", "", text, flags=re.I)
        text = re.sub(r"\n*🔎\s*Semakan lanjut:.*$", "", text, flags=re.I | re.S).strip()
        text += (
            "\n\n📚 Rujukan: Akta Kerja 1955 (Akta 265)"
            "\n🔎 Semakan lanjut: Rujuk seksyen penuh dalam naskhah Akta yang dibekalkan dan pegawai Kesatuan jika melibatkan tafsiran, kes individu atau pertikaian."
        )
        return text

    if articles:
        ref = ", ".join(f"Artikel {n}" for n in articles)
    else:
        ref = "Artikel berkaitan CA-7 (sila semak naskhah CA-7)"

    text += (
        "\n\n📚 Rujukan CA-7: " + ref +
        "\n🔎 Semakan lanjut: Ahli disaran semak naskhah CA-7 dan rujuk pegawai Kesatuan "
        "jika melibatkan tafsiran, kes individu atau pertikaian."
    )
    return text


async def _sahabat_tanya_ai(soalan: str) -> str:
    # Soalan fakta mudah dijawab terus daripada CA-7/Akta tanpa memanggil AI.
    # Ini mengelakkan kelewatan untuk FAQ biasa dan memastikan sumber yang diminta digunakan.
    akta_requested = _sahabat_akta_is_requested(soalan)
    compare_requested = _sahabat_akta_compare_requested(soalan)

    if akta_requested and not compare_requested:
        akta_quick = _sahabat_jawapan_akta_pantas(soalan)
        if akta_quick:
            return _sahabat_kemas_jawapan(akta_quick, source_label="Akta Kerja 1955")

    if not akta_requested:
        quick_answer = _sahabat_jawapan_pantas(soalan)
        if quick_answer:
            return _sahabat_kemas_jawapan(quick_answer)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return (
            "⚠️ *Sahabat KPPbNB belum diaktifkan sepenuhnya.*\n\n"
            "Sila tetapkan `GEMINI_API_KEY` pada Environment Variables server bot.\n\n"
            "Buat masa ini, gunakan menu *📖 Akta & Peraturan* dan *📋 CA7* untuk rujukan."
        )

    try:
        import json
        import urllib.request
        import urllib.error

        # Jika File Search Store telah disediakan, Sahabat akan mencari seluruh
        # dokumen CA-7 secara semantik. Ini mengelakkan kebergantungan kepada
        # petikan/keyword atau had 60,000 aksara.
        store_name = os.environ.get("GEMINI_FILE_SEARCH_STORE", "").strip()
        model = "gemini-3.6-flash"

        if store_name:
            # File Search kekal digunakan, tetapi MASTER SOURCE tempatan turut
            # dihantar sebagai rujukan utama supaya data menu/Quick Answer dan
            # jawapan AI tidak bercanggah jika store lama masih mengandungi
            # versi CA-7 terdahulu.
            ca7 = _sahabat_baca_ca7()
            akta = _sahabat_baca_akta()
            rujukan_master = _sahabat_pilih_rujukan(soalan, ca7) if not akta_requested else ""
            rujukan_akta = _sahabat_pilih_akta_rujukan(soalan, akta) if akta_requested else ""
            numeric_lock = (CA7_NUMERIC_MASTER_TEXT if (not akta_requested and _sahabat_numeric_query(soalan)) else "")
            if compare_requested:
                input_ahli = (
                    "SUMBER CA-7 KPPbNB (UTAMA UNTUK PERJANJIAN):\n"
                    + (rujukan_master or "Sumber CA-7 berkaitan tidak ditemui dalam petikan tempatan.")
                    + "\n\nSUMBER AKTA KERJA 1955 (UTAMA UNTUK UNDANG-UNDANG):\n"
                    + (rujukan_akta or "Sumber Akta berkaitan tidak ditemui dalam petikan tempatan.")
                    + "\n\nSOALAN AHLI:\n" + soalan
                )
            elif akta_requested:
                input_ahli = (
                    "SUMBER AKTA KERJA 1955 (UTAMA):\n"
                    + (rujukan_akta or "Sumber Akta berkaitan tidak ditemui dalam petikan tempatan.")
                    + "\n\nSOALAN AHLI:\n" + soalan
                )
            elif rujukan_master:
                input_ahli = (
                    "MASTER SOURCE CA-7 KPPbNB (UTAMA):\n" + rujukan_master
                    + (("\n\nNUMERIC MASTER CA-7 (ANGKA TERKUNCI):\n" + numeric_lock) if numeric_lock else "")
                    + "\n\nSOALAN AHLI:\n" + soalan
                )
            else:
                input_ahli = soalan

            payload_obj = {
                "model": model,
                "input": input_ahli,
                "system_instruction": SAHABAT_SYSTEM_PROMPT + "\n\n"
                    "Untuk soalan CA-7, utamakan petikan MASTER SOURCE CA-7 yang diberikan bersama soalan. "
                    "Untuk soalan yang menyebut Akta Kerja 1955/Akta 265/Seksyen, utamakan petikan SUMBER AKTA KERJA 1955 yang diberikan. "
                    "Jika soalan meminta perbandingan, bezakan dengan jelas CA-7 dan Akta tanpa mencampurkan hak/syarat. "
                    "File Search ialah sumber sokongan. Jangan reka atau teka fakta. "
                    "ANGKA TERKUNCI: jika soalan meminta angka CA-7, utamakan NUMERIC MASTER CA-7. "
                    "Artikel 25.5(b) = 1.5%, bukan 2%. Artikel 74.1 = 4.5% sebagai angka jawapan bot. "
                    "Jangan menggantikan angka terkunci dengan angka lain daripada memori/model. "
                    "Jangan paparkan 5% untuk Artikel 74.1. "
                    "Jawab ringkas tetapi lengkap. Gunakan 3-7 point pendek jika sesuai. "
                    "Sasaran maksimum kira-kira 150 perkataan. Jangan berhenti di tengah ayat. "
                    "Jika sumber tidak cukup, gunakan mesej rujuk pakar yang ditetapkan.",
                "tools": [{
                    "type": "file_search",
                    "file_search_store_names": [store_name],
                    "top_k": 2
                }],
                "store": False,
                "generation_config": {
                    "thinking_level":"low",
                    "temperature": 0.2,
                    "max_output_tokens": 1200
                }
            }
            payload = json.dumps(payload_obj).encode("utf-8")
            url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        else:
            # Fallback: rujukan tempatan sedia ada jika File Search Store belum
            # ditetapkan. Fungsi bot lain tidak terjejas.
            ca7 = _sahabat_baca_ca7()
            akta = _sahabat_baca_akta()
            rujukan = _sahabat_pilih_rujukan(soalan, ca7) if not akta_requested else ""
            rujukan_akta = _sahabat_pilih_akta_rujukan(soalan, akta) if akta_requested else ""
            numeric_lock = (CA7_NUMERIC_MASTER_TEXT if (not akta_requested and _sahabat_numeric_query(soalan)) else "")
            if compare_requested:
                source_instruction = (
                    "SUMBER CA-7 KPPbNB:\n" + (rujukan or "Tidak ditemui.")
                    + "\n\nSUMBER AKTA KERJA 1955:\n" + (rujukan_akta or "Tidak ditemui.")
                )
            elif akta_requested:
                source_instruction = "SUMBER AKTA KERJA 1955:\n" + (rujukan_akta or "Tidak ditemui.")
            else:
                source_instruction = "PETIKAN CA-7 YANG RELEVAN:\n" + (rujukan or "Sumber CA-7 tidak dapat dibaca sekarang.")
            payload = json.dumps({
                "systemInstruction": {
                    "parts": [{"text": SAHABAT_SYSTEM_PROMPT + "\n\nANGKA TERKUNCI CA-7: Artikel 25.5(b)=1.5%; Artikel 74.1=4.5%. Untuk soalan angka, utamakan NUMERIC MASTER CA-7 yang dibekalkan. Jangan reka atau tukar angka."}]
                },
                "contents": [{
                    "role": "user",
                    "parts": [{"text": (
                        "ARAHAN RUJUKAN:\n"
                        "Jawab berdasarkan sumber yang diberikan di bawah. Jika soalan menyebut Akta Kerja 1955/Akta 265/Seksyen, utamakan sumber Akta. Jika soalan menyebut CA-7, utamakan CA-7. Jika membandingkan kedua-duanya, bezakan sumber dengan jelas. Jangan reka kadar, nombor seksyen/artikel, syarat atau hak yang tidak terdapat dalam rujukan. "
                        "Jika rujukan tidak cukup untuk menjawab, nyatakan dengan jelas bahawa "
                        "maklumat tidak ditemui dalam petikan yang dipilih dan cadangkan menu CA-7 "
                        "atau pegawai Kesatuan yang sesuai.\n\n"
                        + source_instruction
                        + (("\n\nNUMERIC MASTER CA-7 (ANGKA TERKUNCI):\n" + numeric_lock) if numeric_lock else "")
                        + "\n\nSOALAN AHLI:\n" + soalan
                    + "\n\nPENTING: Jawab ringkas tetapi lengkap dalam 3-7 point jika sesuai. Sasaran maksimum kira-kira 150 perkataan. Jangan berhenti di tengah ayat."
                    )}]
                }],
                "generationConfig": {
                    "thinkingConfig": {
        "thinkingLevel": "low"
    },
    "temperature": 0.3,
    "maxOutputTokens": 1200
                }
            }).encode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            method="POST"
        )

        loop = asyncio.get_running_loop()

        def call_api(request):
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))

        # File Search: guna satu model sahaja supaya tidak menunggu model sandaran.
        if store_name:
            payload_obj["model"] = model
            try_payload = json.dumps(payload_obj).encode("utf-8")
            try_req = urllib.request.Request(
                url,
                data=try_payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                },
                method="POST"
            )
            data = await loop.run_in_executor(None, call_api, try_req)
            logging.info(f"Sahabat Gemini berjaya menggunakan model {model}")
        else:
            data = await loop.run_in_executor(None, call_api, req)

        answer = ""
        if store_name:
            # Interactions API returns model output inside steps[].content[].
            for step in data.get("steps", []):
                if step.get("type") == "model_output":
                    for block in step.get("content", []):
                        if block.get("type") == "text" and block.get("text"):
                            answer += block["text"] + "\n"
        else:
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                answer = "\n".join(
                    part.get("text", "") for part in parts if part.get("text")
                )

        return (_sahabat_kemas_jawapan(answer, source_label="Akta Kerja 1955") if akta_requested and not compare_requested else _sahabat_kemas_jawapan(answer)) if answer.strip() else "Maaf, Sahabat tidak dapat memberikan jawapan sekarang. Sila cuba semula."

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
            logging.error(f"Sahabat Gemini HTTP {e.code}: {body[:2000]}")
        except Exception:
            pass
        if e.code == 404:
            return "⚠️ Sumber File Search Sahabat tidak dijumpai. Sila semak `GEMINI_FILE_SEARCH_STORE` di Render."
        if e.code in (401, 403):
            return "⚠️ GEMINI_API_KEY tidak sah atau tiada akses kepada Gemini API."
        if e.code == 429:
            return "⚠️ Had penggunaan Gemini API telah dicapai. Sila cuba semula kemudian."
        return "⚠️ Sahabat tidak dapat menghubungi Gemini sekarang. Sila cuba semula."
    except TimeoutError as e:
        logging.warning(f"Sahabat Gemini timeout: {e}")
        return (
            "🤝 Maaf, Sahabat mengambil masa terlalu lama untuk mendapatkan jawapan. "
            "Elok cuba semula atau rujuk dengan pakar kita untuk jawapan yang lebih tepat. 👍"
        )
    except Exception as e:
        logging.exception(f"Sahabat Gemini gagal: {e}")
        return "⚠️ Sahabat mengalami masalah teknikal. Sila cuba semula."

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
        "Saya boleh bantu faham perkara berkaitan *CA-7, Akta & Peraturan Kerja, "
        "OT, gaji, elaun, cuti, disiplin, kilanan dan hubungan perusahaan*.\n\n"
        "👉 Taip soalan dengan bahasa biasa. Contoh:\n"
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

    # Rekod penggunaan hanya apabila ahli benar-benar menghantar soalan kepada Sahabat.
    _rekod_penggunaan_sahabat(update.effective_user.id)

    await update.message.reply_text("🤝 Sahabat tengah buka buku sat, cari jawapan… 📖", parse_mode='Markdown')
    jawapan = await _sahabat_tanya_ai(soalan)
    await update.message.reply_text(
        "🤝 Sahabat KPPbNB\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        + jawapan,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')],
            [InlineKeyboardButton("🤝 Tanya Lagi", callback_data='menu_sahabat')]
        ])
    )

    # Salinan audit dihantar ke Group Aduan admin sahaja.
    # Jika penghantaran gagal, jawapan kepada ahli tetap tidak terganggu.
    await _hantar_audit_sahabat(update, context, soalan, jawapan)
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
            [InlineKeyboardButton("📘 Buku CA-7", url=URL_CA7)],
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

        # Laporan penggunaan harian 00:01 pagi waktu Malaysia.
        asyncio.create_task(_laporan_penggunaan_harian(app))

        print("Bot KPPbNB LIVE penuh dari awal sampai akhir!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()

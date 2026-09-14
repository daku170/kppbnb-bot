import os
import asyncio
import threading
import http.server
import socketserver
import logging
import random
import csv
import time
from datetime import datetime
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
GROQ_API_KEY = "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"

# ID Rasmi GROUP ADUAN KPPbNB
ADMIN_CHAT_ID = -1003958495436

# Pautan Spesifik Dokumen Google Drive & SharePoint
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
STATE_UPDATE_LOCATION = 2

# Fungsi Membaca Data Ahli dari Fail CSV
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

# Fungsi Semak Adakah Sesi Masih Aktif (< 15 Minit)
def is_session_active(context: ContextTypes.DEFAULT_TYPE) -> bool:
    verified = context.user_data.get('verified', False)
    last_active = context.user_data.get('last_active', 0)
    # 15 minit = 900 saat
    if verified and (time.time() - last_active < 900):
        context.user_data['last_active'] = time.time()  # Perbarui masa aktif
        return True
    return False

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

# ==================== ENJIN AI GROQ ====================

AI_SYSTEM_PROMPT = """
Anda adalah Penasihat Pintar Kesatuan Pekerja-pekerja Padiberas Nasional Berhad (KPPbNB BERNAS Semenanjung Malaysia).
Moto Kesatuan: Bersatu, Berdisiplin, Berjaya.
Tugas anda adalah menjawab soalan ahli berkaitan hak pekerja, kepimpinan kesatuan, undang-undang perburuhan dan Perjanjian Bersama Ke-7 (CA-7) BERNAS dengan tepat, tegas, mesra, dan profesional.
"""

def query_groq_ai(user_question: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY.strip())
    except Exception as err_init:
        return f"⚠️ Ralat Inisialisasi Groq: {str(err_init)}"

    candidate_models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    last_err = ""

    for m in candidate_models:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user", "content": user_question}
                ],
                model=m,
                temperature=0.3,
                max_tokens=850
            )
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
        except Exception as e:
            last_err = str(e)
            continue

    return f"⚠️ Ralat Groq: {last_err[:180]}"

# ==================== KEYBOARDS ====================

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

def get_profile_keyboard():
    keyboard = [
        [InlineKeyboardButton("📍 Kemas Kini Lokasi (Update Location)", callback_data='update_location_start')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

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

def get_kiraan_keyboard():
    keyboard = [
        [InlineKeyboardButton("🧮 Kira Kerja Lebih Masa (Art 31)", callback_data='calc_start_ot')],
        [InlineKeyboardButton("🍱 Semak Elaun Makan Gaji ≥RM4k (Art 64.3)", callback_data='ca_elaun_4k_menu')],
        [InlineKeyboardButton("🚗 Kira Tuntutan Mileage (Art 63)", callback_data='calc_start_mileage')],
        [InlineKeyboardButton("💼 Semak Cuti Gantian (Art 31.5)", callback_data='grade_s')],
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

# ==================== HANDLERS PENGESAHAN & LOKASI ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Semak sama ada sesi masih aktif (< 15 minit)
    if is_session_active(context):
        nama = context.user_data.get('nama', 'Ahli')
        text = f"Hi kembali, *{nama}*! 👋\n\nAnda sudah disahkan sebelum ini. Sila pilih perkhidmatan di bawah:"
        if update.message:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        return ConversationHandler.END

    # Jika sudah lebih 15 minit atau belum pernah sah, minta nombor pekerja
    text = (
        "🔐 *PENGESAHAN KEAHLIAN KPPbNB*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Sesi anda telah tamat tempoh atau belum disahkan.\n\n"
        "👉 Sila masukkan *Nombor Pekerja* sah anda untuk meneruskan:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    return STATE_VERIFY_ID

async def verify_employee_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emp_id = update.message.text.strip()
    user = update.effective_user

    data_ahli = baca_data_ahli(emp_id)

    if data_ahli:
        context.user_data['emp_id'] = emp_id
        context.user_data['nama'] = data_ahli['nama']
        context.user_data['lokasi'] = data_ahli['lokasi']
        context.user_data['verified'] = True
        context.user_data['last_active'] = time.time()  # Rekod masa mula aktif
        
        welcome_text = (
            f"Hi *{data_ahli['nama']}*! 👋\n\n"
            "✅ *PENGESAHAN BERJAYA!*\n"
            "Keahlian anda disahkan aktif.\n\n"
            "🤖 *Pusat Maklumat & Perkhidmatan Ahli KPPbNB*\n"
            "💬 Anda boleh taip soalan di ruangan ini atau pilih perkhidmatan di bawah:"
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
            "Nombor pekerja yang anda masukkan tiada dalam rekod fail CSV kesatuan.\n\n"
            "📞 Sila berhubung terus dengan Setiausaha Agung Kesatuan untuk pendaftaran:\n"
            "• *Nama:* Pn. Farah Aqilah Binti Bardzan\n"
            "• *Emel SU:* `aqilah@bernas.com.my`\n\n"
            "Sila cuba masukkan semula Nombor Pekerja yang sah:"
        )
        await update.message.reply_text(error_text, parse_mode='Markdown')
        return STATE_VERIFY_ID

async def start_update_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "📍 *KEMAS KINI LOKASI / KOMPLEKS*\n\nSila taip nama Lokasi atau Kompleks baharu anda yang betul:"
    await query.message.reply_text(text, parse_mode='Markdown')
    return STATE_UPDATE_LOCATION

async def receive_new_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_loc = update.message.text.strip()
    emp_id = context.user_data.get('emp_id', 'Tidak Diketahui')
    nama = context.user_data.get('nama', 'Ahli')
    user = update.effective_user

    context.user_data['lokasi'] = new_loc
    context.user_data['last_active'] = time.time()  # Kemas kini masa aktif

    notis_group = (
        "📍 *NOTIFIKASI KEMAS KINI LOKASI AHLI*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Nama Ahli:* {nama}\n"
        f"🔢 *No. Pekerja:* `{emp_id}`\n"
        f"🏢 *Lokasi Baharu Dikemas Kini:* *{new_loc}*\n"
        f"💬 *Username Telegram:* @{user.username or 'Tiada'}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notis_group, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Gagal hantar notis lokasi ke group: {e}")

    await update.message.reply_text(
        f"✅ Lokasi anda telah berjaya dikemas kini kepada: *{new_loc}*.\nNotifikasi telah dihantar kepada pihak pentadbir kesatuan.",
        parse_mode='Markdown',
        reply_markup=get_back_button()
    )
    return ConversationHandler.END

# ==================== MODUL UTAMA ====================

async def handle_akta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_akta':
        text = "📖 *1. AKTA & PERATURAN KERJA MALAYSIA*\n\nPilih topik berkaitan:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_waktu':
        text = "⏰ *AKTA KERJA 1955: WAKTU BEKERJA*\n• Had maksimum: 45 jam seminggu (Pindaan 2022)."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_ot':
        text = "🧮 *AKTA KERJA 1955: OT*\n• Hari Biasa: 1.5x | Rehat: 2.0x | Cuti Am: 3.0x (Maks 104 jam/bulan)."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_cuti':
        text = "🏖️ *AKTA KERJA 1955: CUTI*\n• Cuti Tahunan CA-7: 18 hingga 24 hari mengikut perkhidmatan."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_mc':
        text = "🏥 *AKTA KERJA 1955: MC & WAD*\n• Cuti Masuk Wad: Hingga 60 hari setahun."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_gaji':
        text = "💰 *AKTA KERJA 1955: GAJI*\n• Gaji dibayar selewat-lewatnya hari ke-7 selepas tamat tempoh upah."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_awol':
        text = "⚠️ *AWOL & DISIPLIN*\n• Tidak hadir >2 hari berturut-turut tanpa alasan dikira pecah kontrak."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_tamat':
        text = "🚪 *PENAMATAN KERJA*\n• Mengikut tempoh notis Seksyen 12 Akta Kerja dan Artikel 38 CA-7."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_osha':
        text = "🦺 *OSHA 1994*\n• Seksyen 26A: Hak pekerja menolak kerja bahaya."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())
    elif data == 'akta_perkeso':
        text = "🛡️ *PERKESO*\n• Meliputi kemalangan kerja dan perjalanan pergi/balik bertugas."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

async def handle_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_ca':
        text = "📋 *2. PERJANJIAN BERSAMA KE-7 (CA-7)*\nPilih klausa:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_gaji':
        text = "💰 *CA-7: GAJI & BONUS*\n• Kenaikan Tahunan: 3.5% + Merit | Bonus: 1 bulan gaji asas."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_waktu_kerja':
        text = "⏰ *CA-7: WAKTU BEKERJA (ART 29)*\n• Bukan Syif: 39 jam | Syif: 42 jam seminggu."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_ot':
        text = "🧮 *CA-7: OT & CUTI GANTIAN*\n• Kelayakan Gred T & S bawah RM4,000 mengikut Artikel 31."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())
    elif data == 'ca_elaun_4k_menu':
        text = "🍱 *CA-7: ELAUN MAKAN GAJI ≥ RM4,000*\nPilih zon anda:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())
    elif data in ['art64_zona', 'art64_zonb', 'art64_syif']:
        text = "🍱 *ARTIKEL 64.3: ELAUN MAKAN*\n• 2-5 jam: RM25 | >5 jam: RM50 (atau pilihan Cuti Gantian)."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())
    elif data == 'ca_cuti':
        text = "🏖️ *CA-7: CUTI*\n• Tahunan: 18-24 hari | Haji: 54 hari | Bersalin: 98 hari."
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
        text = "📊 *LAMPIRAN I: TANGGA GAJI*\n• Merangkumi Gred T (Teknikal) dan Gred S (Sokongan)."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

async def handle_other_menus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['last_active'] = time.time()
    data = query.data

    if data == 'menu_dokumen':
        text = "📚 *PUSAT DOKUMEN & MUAT TURUN KESATUAN*\nSila pilih dokumen:"
        keyboard = [
            [InlineKeyboardButton("📄 Borang Kilanan Rasmi", url=URL_KILANAN)],
            [InlineKeyboardButton("📘 Buku CA-1", url=URL_CA1), InlineKeyboardButton("📗 Buku CA-2", url=URL_CA2)],
            [InlineKeyboardButton("📙 Buku CA-3", url=URL_CA3), InlineKeyboardButton("📕 Buku CA-4", url=URL_CA4)],
            [InlineKeyboardButton("📒 Buku CA-5", url=URL_CA5), InlineKeyboardButton("📓 Buku CA-6", url=URL_CA6)],
            [InlineKeyboardButton("📜 Buku Akta Kerja & Rujukan", url=URL_AKTA)],
            [InlineKeyboardButton("⚖️ Buku Tatatertib BERNAS Edisi 5", url=URL_TATATERTIB)],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
        ]
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'menu_hebahan':
        text = "📢 *HEBAHAN KESATUAN*\n• CA-7 berkuatkuasa 2026-2028."
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
            f"Lokasi / Kompleks: *{lokasi}*\n"
            "Status Keahlian: 🟢 *Aktif (Disahkan)*"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_profile_keyboard())
    elif data == 'menu_hubungi':
        text = (
            "☎️ *HUBUNGI KESATUAN (KPPbNB)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏛️ *Ibu Pejabat:*\n"
            "No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah.\n\n"
            "📌 *Pimpinan Rasmi:*\n"
            "• *Presiden:* En. Syahibudil Assaufi (`syahibudil@bernas.com.my`)\n"
            "• *Setiausaha Agung:* Pn. Farah Aqilah (`aqilah@bernas.com.my`)\n"
            "• *Bendahari:* En. Khairul Faiz (`khairulfaiz@bernas.com.my`)"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_utama':
        nama = context.user_data.get('nama', 'Ahli')
        text = f"🏠 *MENU UTAMA KPPbNB*\n\nSelamat kembali, *{nama}*.\nSila pilih perkhidmatan di bawah:"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    
    # Semak adakah sesi aktif
    if not is_session_active(context):
        await update.message.reply_text("🔐 Sesi anda telah tamat tempoh atau belum disahkan. Sila taip /start semula.")
        return

    context.user_data['last_active'] = time.time()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    loop = asyncio.get_running_loop()
    ai_raw = await loop.run_in_executor(None, query_groq_ai, update.message.text.strip())
    response = f"🤖 *JAWAPAN AI*\n\n{ai_raw.replace('**', '*')}\n\n💡 *Rujuk Exco untuk kepastian rasmi.*"
    await update.message.reply_text(response, parse_mode='Markdown', reply_markup=get_back_button())

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# ==================== MAIN ====================

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

    location_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_update_location, pattern='^update_location_start$')],
        states={
            STATE_UPDATE_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_location)]
        },
        fallbacks=[CallbackQueryHandler(cancel_handler, pattern='^menu_utama$'), CommandHandler("start", start)]
    )

    app.add_handler(verify_conv)
    app.add_handler(location_conv)
    
    app.add_handler(CallbackQueryHandler(handle_akta, pattern='^(menu_akta|akta_)'))
    app.add_handler(CallbackQueryHandler(handle_ca, pattern='^(menu_ca|ca_|art64_)'))
    app.add_handler(CallbackQueryHandler(handle_other_menus, pattern='^menu_(dokumen|hebahan|profil|hubungi|utama)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat))

    async with app:
        await app.start()
        await app.updater.start_polling()
        print("Bot KPPbNB LIVE dengan Sistem Timeout Sesi 15 Minit!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()

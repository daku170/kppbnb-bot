import os
import asyncio
import threading
import http.server
import socketserver
import logging
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

STATE_GRADE, STATE_SCHEDULE, STATE_DAY_TYPE, STATE_SALARY, STATE_HOURS, STATE_GRED_S_HOURS = range(6)

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

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🧮 Semakan OT & Cuti Gantian", callback_data='menu_kalkulator')],
        [InlineKeyboardButton("📑 Perjanjian Bersama (CA-7)", callback_data='menu_ca')],
        [InlineKeyboardButton("⚖️ Akta Kerja & Peraturan", callback_data='menu_akta')],
        [InlineKeyboardButton("🤝 Tuntutan Kebajikan", callback_data='menu_kebajikan')],
        [InlineKeyboardButton("⚠️ Aduan & Masalah Kerja", callback_data='menu_aduan')],
        [InlineKeyboardButton("📢 Info Terkini Kesatuan", callback_data='menu_info')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ca_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 Gaji, Bonus & Pelarasan", callback_data='ca_gaji')],
        [InlineKeyboardButton("⏰ Waktu Kerja & Bayaran OT", callback_data='ca_ot')],
        [InlineKeyboardButton("🏖️ Kemudahan Cuti Bergaji", callback_data='ca_cuti')],
        [InlineKeyboardButton("🏥 Rawatan Perubatan & Hospital", callback_data='ca_perubatan')],
        [InlineKeyboardButton("💵 Elaun-Elaun & Sumbangan Beras", callback_data='ca_elaun')],
        [InlineKeyboardButton("🛡️ Insurans, KWSP & Pampasan", callback_data='ca_pampasan')],
        [InlineKeyboardButton("🔙 Kembali ke Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_akta_keyboard():
    keyboard = [
        [InlineKeyboardButton("📘 AWOL, Disiplin & Show Cause", callback_data='akta_awol')],
        [InlineKeyboardButton("⏰ Had Waktu Kerja 45 Jam & OT (Termasuk Gaji >RM4k)", callback_data='akta_waktu')],
        [InlineKeyboardButton("🏥 Peraturan Cuti Sakit (MC) & Wad", callback_data='akta_mc')],
        [InlineKeyboardButton("🦺 OSHA: Hak Tolak Kerja Bahaya", callback_data='akta_osha')],
        [InlineKeyboardButton("🛡️ PERKESO: Kemalangan Perjalanan", callback_data='akta_perkeso')],
        [InlineKeyboardButton("🔙 Kembali ke Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_ca_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Senarai CA", callback_data='menu_ca')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_akta_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Senarai Akta", callback_data='menu_akta')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== START HANDLER ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🌾 *SELAMAT DATANG KE BOT RASMI KPPbNB*\n"
        "_Kesatuan Pekerja-pekerja Padiberas Nasional Berhad (BERNAS) Semenanjung Malaysia_\n\n"
        "Sila pilih menu di bawah untuk semakan maklumat, pengiraan OT/Cuti Gantian, hak akta, kebajikan dan aduan:"
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# ==================== MODUL KALKULATOR OT & CUTI GANTIAN ====================

async def start_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔧 Gred T (Teknikal/Operasi) - Bayaran Tunai", callback_data='grade_t')],
        [InlineKeyboardButton("💼 Gred S (Sokongan/Admin) - Cuti Gantian & Elaun", callback_data='grade_s')],
        [InlineKeyboardButton("🔙 Batal & Menu Utama", callback_data='menu_utama')]
    ]
    text = (
        "🧮 *SEMAKAN KERJA LEBIH MASA (OT) & CUTI GANTIAN*\n"
        "_(Selaras Artikel 31 CA-7 & Akta Kerja 1955)_\n\n"
        "Sila pilih **Kategori Gred** jawatan anda:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_GRADE

async def calc_grade_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'grade_s':
        text = (
            "💼 *KATEGORI GRED S (SOKONGAN / PENTADBIRAN)*\n"
            "_(Artikel 31.5 CA-7 - Cuti Gantian & Tuntutan Elaun)_\n\n"
            "Bagi Gred S, kerja lebih masa layak digantikan dengan **Cuti Gantian (Time-Off-In-Lieu)** serta tuntutan **Elaun-Elaun Berkaitan**.\n\n"
            "👉 Sila taip **Jumlah Jam Kerja Lebih Masa** yang dilakukan:\n"
            "_Contoh: 4 atau 8_"
        )
        await query.edit_message_text(text, parse_mode='Markdown')
        return STATE_GRED_S_HOURS

    # Jika Gred T dipilih:
    keyboard = [
        [InlineKeyboardButton("📍 Zon A (Kedah, Kelantan, Trg, Johor)", callback_data='sch_zona')],
        [InlineKeyboardButton("📍 Zon B (P.Pinang, Perak, Selangor, dll)", callback_data='sch_zonb')],
        [InlineKeyboardButton("🔄 Pekerja Syif (Ikut Giliran)", callback_data='sch_syif')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_utama')]
    ]
    text = (
        "🔧 *KATEGORI GRED T (TEKNIKAL & OPERASI)*\n"
        "_(Layak Tuntutan OT Tunai Termasuk Bergaji >RM4k Selaras CA-7)_\n\n"
        "Sila pilih *Zon Lokasi / Jadual Kerja* anda:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_SCHEDULE

# Aliran Gred S (Cuti Gantian + Elaun)
async def calc_gred_s_hours_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    try:
        hours = float(msg)
        if hours <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ Sila masukkan angka jam yang sah (contoh: 4 atau 8):")
        return STATE_GRED_S_HOURS

    # Pengiraan Cuti Gantian Artikel 31.5
    if hours >= 6:
        cuti_desc = "*1 Hari Penuh Cuti Gantian*"
    elif hours >= 4:
        cuti_desc = "*1/2 Hari Cuti Gantian (Half Day)*"
    else:
        cuti_desc = f"*{hours} Jam* (Boleh dikumpul sehingga mencukupi 4 atau 6-8 jam untuk cuti gantian)"

    result_text = (
        "💼 *KEPUTUSAN KELAYAKAN CUTI GANTIAN & ELAUN (GRED S)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ *Masa Bertugas:* {hours} Jam\n"
        f"🏖️ *Kelayakan Cuti Gantian (Art 31.5):* {cuti_desc}\n"
        "_(Cuti gantian boleh dikumpul dan digunakan dalam tempoh 6 bulan)_\n\n"
        "💰 *ELAUN-ELAUN YANG TETAP LAYAK DITUNTUT:*\n"
        "Walaupun tidak menuntut OT tunai, anda **TETAP LAYAK** menuntut elaun berikut sekiranya memenuhi syarat tugas:\n\n"
        "1️⃣ *Elaun Makan Lebih Masa:* Layak dituntut jika bertugas lebih masa berterusan atau dipanggil tugas luar.\n"
        "2️⃣ *Tuntutan Perbatuan (Mileage - Art 63):* Jika dipanggil bertugas (Call-out):\n"
        "   • Kereta: *RM0.75 / km*\n"
        "   • Motosikal: *RM0.50 / km*\n"
        "   • Tol & Parking: Tuntutan berasaskan resit sebenar.\n"
        "3️⃣ *Elaun Panggilan Bertugas (Call-Out / Standby):* Bayaran minimum khas bagi yang dipanggil kecemasan di luar jadual kerja biasa.\n"
        "4️⃣ *Elaun Syif (Art 72):* RM6.50 (Syif 2) / RM7.00 (Syif 3) jika menggantikan syif operasi fizikal.\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "_Pastikan borang tuntutan perbatuan/elaun dan rekod perakam waktu dikemukakan kepada penyelia._"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Kira Semula", callback_data='menu_kalkulator')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    await update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# Aliran Gred T (OT Tunai)
async def calc_schedule_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    if choice == 'sch_zona':
        context.user_data['normal_hours'] = 7.8
        context.user_data['zone_name'] = "Zon A (Ahad - Khamis)"
        keyboard = [
            [InlineKeyboardButton("1️⃣ Hari Biasa (Ahad - Khamis) [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("2️⃣ Hari Jumaat (Off Day) [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("3️⃣ Hari Sabtu (Rest Day) [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("4️⃣ Hari Kelepasan Am (Cuti Umum) [3.0x]", callback_data='day_ph')],
            [InlineKeyboardButton("🔙 Batal", callback_data='menu_utama')]
        ]
    elif choice == 'sch_zonb':
        context.user_data['normal_hours'] = 7.8
        context.user_data['zone_name'] = "Zon B (Isnin - Jumaat)"
        keyboard = [
            [InlineKeyboardButton("1️⃣ Hari Biasa (Isnin - Jumaat) [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("2️⃣ Hari Sabtu (Off Day) [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("3️⃣ Hari Ahad (Rest Day) [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("4️⃣ Hari Kelepasan Am (Cuti Umum) [3.0x]", callback_data='day_ph')],
            [InlineKeyboardButton("🔙 Batal", callback_data='menu_utama')]
        ]
    else:
        context.user_data['normal_hours'] = 8.0
        context.user_data['zone_name'] = "Pekerja Syif"
        keyboard = [
            [InlineKeyboardButton("1️⃣ Hari Kerja Syif Biasa [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("2️⃣ Hari Kelepasan Syif (Off Day) [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("3️⃣ Hari Rehat Syif (Rest Day) [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("4️⃣ Hari Kelepasan Am (Cuti Umum) [3.0x]", callback_data='day_ph')],
            [InlineKeyboardButton("🔙 Batal", callback_data='menu_utama')]
        ]

    text = (
        f"✅ *Jadual Dipilih:* {context.user_data['zone_name']}\n\n"
        "Sila pilih *Jenis Hari* anda melakukan kerja OT:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_DAY_TYPE

async def calc_day_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day_type = query.data
    context.user_data['day_type'] = day_type
    
    label_map = {
        'day_normal': 'Hari Kerja Biasa (Kadar 1.5x)',
        'day_offday': 'Hari Kelepasan / Off Day (Kadar 1.5x)',
        'day_rest': 'Hari Rehat / Rest Day (Kadar 2.0x)',
        'day_ph': 'Hari Kelepasan Am / Cuti Umum (Kadar 3.0x)'
    }
    context.user_data['day_label'] = label_map.get(day_type, '')

    text = (
        f"📌 *Kategori Hari:* {context.user_data['day_label']}\n\n"
        "👉 Sila taip **Gaji Pokok Bulanan** anda (Nombor sahaja tanpa perkataan RM):\n"
        "_Contoh: 2400 atau 4300_"
    )
    await query.edit_message_text(text, parse_mode='Markdown')
    return STATE_SALARY

async def calc_salary_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().replace("RM", "").replace(",", "")
    try:
        salary = float(msg)
        if salary <= 0:
            raise ValueError()
        context.user_data['salary'] = salary
    except ValueError:
        await update.message.reply_text("⚠️ Sila masukkan angka gaji yang sah (contoh: 2400 atau 4300):")
        return STATE_SALARY

    text = (
        f"💵 *Gaji Pokok:* RM {salary:,.2f}\n\n"
        "👉 Sila taip **Jumlah Jam OT** yang dilakukan:\n"
        "_Contoh: 3.5 atau 4_"
    )
    await update.message.reply_text(text, parse_mode='Markdown')
    return STATE_HOURS

async def calc_hours_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    try:
        hours = float(msg)
        if hours <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ Sila masukkan angka jam yang sah (contoh: 4 atau 2.5):")
        return STATE_HOURS

    salary = context.user_data['salary']
    normal_hours = context.user_data['normal_hours']
    day_type = context.user_data['day_type']
    day_label = context.user_data['day_label']
    zone_name = context.user_data['zone_name']

    orp = salary / 26.0
    hrp = orp / normal_hours

    if day_type in ['day_normal', 'day_offday']:
        rate_multiplier = 1.5
    elif day_type == 'day_rest':
        rate_multiplier = 2.0
    else:  # day_ph
        rate_multiplier = 3.0

    total_ot = rate_multiplier * hrp * hours
    formula_desc = f"{rate_multiplier} × (RM {hrp:.2f}/jam) × {hours} jam"

    extra_note = ""
    if salary > 4000:
        extra_note = "\n\n💡 _Nota Gaji >RM4k: Layak menuntut bayaran OT selaras Artikel 31 & Lampiran I Perjanjian Bersama (CA-7) KPPbNB._"

    result_text = (
        "📊 *KEPUTUSAN PENGIRAAN OT TUNAI (GRED T)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Zon / Jadual:* {zone_name}\n"
        f"💵 *Gaji Pokok:* RM {salary:,.2f}\n"
        f"📅 *Kategori Hari:* {day_label}\n"
        f"⏱️ *Masa OT:* {hours} Jam\n\n"
        f"📌 *Kadar Gaji Sejam (HRP):* RM {hrp:.2f}\n"
        f"📐 *Formula:* {formula_desc}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *ANGGARAN BAYARAN OT: RM {total_ot:,.2f}*\n"
        "━━━━━━━━━━━━━━━━━━━━"
        f"{extra_note}\n\n"
        "_Nota: Tuntutan OT tertakluk kepada pengesahan perakam waktu dan kelulusan majikan mengikut Artikel 31 CA-7._"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Kira Semula", callback_data='menu_kalkulator')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    await update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def calc_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# ==================== HANDLER MENU LAIN ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_utama':
        await start(update, context)

    # 1. MENU PERJANJIAN BERSAMA (CA-7)
    elif data == 'menu_ca':
        text = (
            "📑 *PERJANJIAN BERSAMA KE-7 (2026 – 2028)*\n"
            "_Antara BERNAS & KPPbNB (No Pendaftaran 923)_\n\n"
            "Sila pilih kategori artikel yang ingin disemak:"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gaji':
        text = (
            "💰 *GAJI, BONUS & PELARASAN GAJI*\n\n"
            "📌 *Kenaikan Gaji Tahunan (Artikel 25):*\n"
            "• Prestasi Memenuhi Jangkaan & ke atas: *3.5% + Merit*\n"
            "• Prestasi Di Bawah Jangkaan / Tidak Memuaskan: *2.0%*\n"
            "• Dibayar setiap 1 Januari selepas disahkan jawatan.\n\n"
            "📌 *Bonus Kontraktual (Artikel 26):*\n"
            "• Bayaran *1 bulan gaji* kepada pekerja tetap yang disahkan pada atau sebelum 31 Disember.\n\n"
            "📌 *Semakan & Pelarasan Gaji (Artikel 74):*\n"
            "• Gaji bulanan diselaraskan sebanyak *4.5%* untuk ahli kesatuan.\n"
            "• Pelarasan khas bagi kakitangan terkesan Perintah Gaji Minima.\n\n"
            "📌 *Struktur Tangga Gaji (Lampiran I):*\n"
            "• *T5(T) Penyelia II:* RM3,000 - RM6,300\n"
            "• *T4(T) Penjaga Jentera II/Juruteknik III:* RM2,600 - RM5,200\n"
            "• *T3(T) Penjaga Jentera I/Juruteknik II:* RM2,100 - RM4,000\n"
            "• *T2(T) Juruteknik I:* RM1,900 - RM3,200\n"
            "• *T1(T) Juruteknik Rendah:* RM1,700 - RM2,800"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_ca_keyboard())

    elif data == 'ca_ot':
        text = (
            "⏰ *WAKTU KERJA & KERJA LEBIH MASA (OT)*\n\n"
            "📌 *Waktu Bekerja (Artikel 29):*\n"
            "• *Bukan Syif:* Purata 39 jam seminggu.\n"
            "• *Kerja Syif:* Purata 42 jam seminggu (Maksimum 45 jam mengikut Akta Kerja).\n\n"
            "📌 *Formula Bayaran OT Gred T (Artikel 31):*\n"
            "• *(Gaji Bulanan / 26) × 1.5 × (Jam OT / Jam Kerja Biasa)*\n"
            "• Had maksimum OT sebulan: *104 jam* (tidak termasuk OT hari rehat/cuti am).\n"
            "• *Pekerja Bergaji >RM4,000 (Gred T):* Tetap layak menuntut bayaran OT selagi dalam skop gred CA-7.\n\n"
            "📌 *Cuti Gantian Gred S (Artikel 31.5):*\n"
            "• 6 - 8 jam kerja OT = *1 hari cuti gantian*\n"
            "• ≤ 4 - 5 jam kerja OT = *1/2 hari cuti gantian*\n"
            "• Boleh dikumpul dan diguna dalam tempoh 6 bulan.\n"
            "• *Elaun Layak Dituntut:* Elaun makan kerja lebih masa, mileage (perjalanan) RM0.75/km kereta, RM0.50/km motor, tol dan elaun panggilan bertugas (call-out)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_ca_keyboard())

    elif data == 'ca_cuti':
        text = (
            "🏖️ *KEMUDAHAN CUTI BERGAJI*\n\n"
            "📌 *Cuti Tahunan (Artikel 44):*\n"
            "• < 2 tahun khidmat: *18 hari*\n"
            "• 2 hingga 5 tahun: *22 hari*\n"
            "• > 5 tahun khidmat: *24 hari*\n"
            "_(Boleh bawa 50% baki cuti sehingga 30 Jun tahun berikutnya)_\n\n"
            "📌 *Cuti Sakit & Hospital (Artikel 47 & 48):*\n"
            "• Sakit biasa (Klinik Panel/Kerajaan): *22 hari setahun*\n"
            "• Kemasukan Wad/Hospital: *60 hari setahun*\n"
            "• Sakit Berpanjangan: 6 bulan pertama (Gaji Penuh), 6 bulan kedua (Separuh Gaji), 6 bulan ketiga (Tanpa Gaji).\n\n"
            "📌 *Cuti Khas & Ehsan:*\n"
            "• *Bersalin (Artikel 49):* 98 hari (Gaji Penuh, maks 5 kelahiran) + pilihan 90 hari Cuti Tanpa Gaji.\n"
            "• *Paterniti (Artikel 52):* 7 hari (khidmat ≥ 1 thn) / 3 hari (khidmat < 1 thn).\n"
            "• *Kematian Keluarga Terdekat (Artikel 50):* 3 hari bekerja + *Bantuan Pengebumian RM1,000*.\n"
            "• *Perkahwinan Sah Pertama (Artikel 51):* 4 hari bekerja.\n"
            "• *Haji / Umrah (Artikel 55):* 54 hari bergaji penuh (sekali sepanjang khidmat)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_ca_keyboard())

    elif data == 'ca_perubatan':
        text = (
            "🏥 *FAEDAH RAWATAN PERUBATAN (Artikel 58, 59 & 60)*\n\n"
            "📌 *Rawatan Pesakit Luar (Outpatient - Artikel 59):*\n"
            "• Had kelayakan: *RM3,500 setahun* (Pekerja & Tanggungan sah).\n"
            "• Termasuk had *RM1,000* untuk pergigian, cermin mata & rawatan berkala sendiri.\n\n"
            "📌 *Rawatan Pesakit Dalam / Wad (Hospitalization - Artikel 60):*\n"
            "• *Tahun 2026:* Had RM35,000 setahun sekeluarga.\n"
            "• *Mulai 1 Jan 2027:* Had *RM45,000 setahun bagi setiap individu* (Pekerja & setiap tanggungan).\n"
            "• Kelayakan Bilik & Penginapan: *RM150 sehari*.\n\n"
            "📌 *Rawatan Bersalin (Artikel 61):*\n"
            "• Bersalin Normal: Had *RM3,000*\n"
            "• Pembedahan Caesarean: Had *RM6,000* (Swasta) / Ditanggung Penuh (Hospital Kerajaan)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_ca_keyboard())

    elif data == 'ca_elaun':
        text = (
            "💵 *ELAUN-ELAUN & SUMBANGAN KHAS*\n\n"
            "📌 *Elaun Chargeman (Artikel 71):*\n"
            "• *RM300.00 sebulan* bagi yang memiliki perakuan kelayakan dan menjalankan tugas.\n\n"
            "📌 *Elaun Syif (Artikel 72):*\n"
            "• Syif 2 (4.00 ptg - 12.00 mlm): *RM6.50*\n"
            "• Syif 3 (12.00 mlm - 8.00 pagi): *RM7.00*\n"
            "• Syif Malam (12 jam: 8.00 mlm - 8.00 pagi): *RM7.00*\n\n"
            "📌 *Tugas Luar Kawasan (Outstation) & Call-Out:*\n"
            "• *Elaun Perjalanan (Art 63):* Kereta (RM0.75/km), Motor (RM0.50/km) + Tol/Parking berasaskan resit.\n"
            "• *Elaun Makan (Art 64):* RM115.00 sehari (melebihi 50km & > 8 jam).\n"
            "• *Penginapan Hotel (Art 65):* Hotel 4 Bintang (Twin Sharing) atau *Elaun Lojing RM100.00 semalam* (tanpa resit).\n"
            "• *Elaun Dobi (Art 57):* RM20.00 sehari (tugas luar > 3 hari berturut-turut).\n\n"
            "📌 *Sumbangan Beras (Artikel 67):*\n"
            "• *2 kampit (10kg)* Beras Super Tempatan setiap bulan kepada semua pekerja."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_ca_keyboard())

    elif data == 'ca_pampasan':
        text = (
            "🛡️ *INSURANS, KWSP & PAMPASAN PEKERJA*\n\n"
            "📌 *Caruman Tambahan KWSP Majikan (Artikel 37.2):*\n"
            "• Khidmat > 20 tahun: *18%*\n"
            "• Khidmat 10 hingga 20 tahun: *16%*\n"
            "• Khidmat < 10 tahun: *13%*\n\n"
            "📌 *Insurans GTL & GPA (Artikel 40):*\n"
            "• Pampasan Kematian / Hilang Upaya Kekal semasa perkhidmatan:\n"
            "  👉 *36 bulan × Gaji Pokok Terakhir*\n\n"
            "📌 *Faedah Penamatan / Retrenchment (Artikel 38):*\n"
            "• Pelaksanaan mengikut prinsip *LIFO (Last In First Out)* berasaskan formula syarikat dan Akta Kerja."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_ca_keyboard())

    # 2. SUB-MENU AKTA & PERATURAN
    elif data == 'menu_akta':
        text = (
            "⚖️ *PANDUAN AKTA KERJA & PERATURAN PERHUBUNGAN PERUSAHAAN*\n\n"
            "Sila pilih topik perundangan di bawah untuk rujukan seksyen, hak pekerja dan tindakan yang perlu diambil:"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_awol':
        text = (
            "⚖️ *PANDUAN PERUNDANGAN: KETIDAKHADIRAN (AWOL) & TATATERTIB*\n\n"
            "📌 *1. Takrifan & Implikasi Undang-Undang*\n"
            "• *Seksyen 15(2) Akta Kerja 1955:* Pekerja disifatkan telah memungkiri kontrak perkhidmatan (*breach of contract*) jika tidak hadir bertugas selama **melebihi 2 hari bekerja berturut-turut** tanpa cuti awal yang diluluskan.\n"
            "• *Beban Pembuktian:* Tindakan terbatal jika pekerja mempunyai **alasan munasabah** dan telah mengambil langkah munasabah memberitahu/cuba memberitahu majikan pada masa terawal semasa ketiadaannya.\n\n"
            "📌 *2. Prosedur Siasatan & Hak Pekerja (Seksyen 14)*\n"
            "• *Kewajipan Due Inquiry:* Majikan tidak boleh buang pekerja secara melulu tanpa siasatan dalaman yang adil.\n"
            "• *Surat Tunjuk Sebab (Show Cause):* Pekerja berhak menerima perincian pertuduhan bertulis dan diberi tempoh munasabah (3-7 hari) untuk menjawab.\n"
            "• *Gantung Kerja Siasatan (Sek 14(2)):* Tempoh maksimum **14 hari** dengan bayaran sekurang-kurangnya **50% gaji pokok**.\n\n"
            "📌 *3. Hak Kesatuan (KPPbNB) & SOP Tindakan*\n"
            "1️⃣ Simpan bukti kukuh (slip MC, rekod perubatan, salinan mesej kepada penyelia).\n"
            "2️⃣ Jangan tandatangan dokumen pengakuan salah terburu-buru.\n"
            "3️⃣ Kemukakan salinan surat kepada AJK Kesatuan Cawangan untuk bimbingan jawapan rasmi."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_akta_keyboard())

    elif data == 'akta_waktu':
        text = (
            "⏰ *PANDUAN PERUNDANGAN: HAD WAKTU BEKERJA & BAYARAN OT*\n\n"
            "📌 *1. Had Waktu Kerja Statutori (Seksyen 60A Akta Kerja)*\n"
            "• *Maksimum Jam Seminggu:* **45 jam seminggu** (Pindaan 2022).\n"
            "• *Maksimum Jam Sehari:* Tidak melebihi **8 jam sehari** (atau 9 jam bagi kerja 5 hari seminggu).\n"
            "• *Waktu Rehat Wajib:* Tidak boleh bekerja berterusan melebihi **5 jam** tanpa rehat sekurang-kurangnya 30 minit.\n"
            "• *Had Maksimum OT Bulanan:* **104 jam sebulan** (tidak termasuk kerja pada Hari Rehat & Cuti Am).\n\n"
            "📌 *2. Isu Pekerja Bergaji Melebihi RM4,000/Bulan*\n"
            "• *Di Bawah Akta Kerja 1955 (Jadual Pertama Pindaan 2022):* Hak OT statutori dihadkan kepada pekerja bergaji $\le$RM4,000 sebulan (kecuali pekerja buruh manual/jentera).\n"
            "• *Perlindungan Di Bawah CA-7 BERNAS:* **Semua pekerja dalam skop kesatuan** (termasuk Gred T5 Penyelia II & T4 Chargeman dengan tangga gaji sehingga RM6,300) **tetap layak mendapat bayaran OT sepenuhnya** mengikut formula Artikel 31 CA-7!\n\n"
            "📌 *3. Gred S & Cuti Gantian (Artikel 31.5)*\n"
            "• Kakitangan Gred S layak menuntut Cuti Gantian serta elaun berkaitan (Elaun Makan Lebih Masa, Perbatuan/Mileage Kereta RM0.75/km Motor RM0.50/km, dan Call-out)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_akta_keyboard())

    elif data == 'akta_mc':
        text = (
            "🏥 *PANDUAN PERUNDANGAN: CUTI SAKIT & KEMASUKAN WAD (HOSPITAL)*\n\n"
            "📌 *1. Peruntukan Minimum Seksyen 60F Akta Kerja 1955*\n"
            "• Pindaan 2022 telah **mengasingkan sepenuhnya** kelayakan Cuti Sakit biasa dan Cuti Hospitalisasi (Wad):\n"
            "  👉 Kelayakan Masuk Wad: **60 hari setahun** tanpa menolak baki cuti sakit biasa.\n\n"
            "📌 *2. Faedah Lebih Baik Di Bawah CA-7 BERNAS (Artikel 47 & 48)*\n"
            "• *Cuti Sakit Biasa:* **22 hari setahun** (berbanding hanya 14-22 hari dalam akta minimum mengikut tempoh khidmat).\n"
            "• *Sakit Berpanjangan (Prolonged Illness):* Dilindungi sehingga 18 bulan (6 bln Gaji Penuh, 6 bln Separuh Gaji, 6 bln Tanpa Gaji).\n\n"
            "📌 *3. Syarat Sah MC & Kewajipan Pekerja*\n"
            "• MC wajib dikeluarkan oleh Pengamal Perubatan Berdaftar (Klinik Panel BERNAS atau Hospital/Klinik Kerajaan).\n"
            "• Pekerja **wajib memaklumkan majikan dalam tempoh 48 jam** dari tarikh MC bermula. Kegagalan memaklumkan boleh dianggap sebagai ketidakhadiran tanpa izin."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_akta_keyboard())

    elif data == 'akta_osha':
        text = (
            "🦺 *PANDUAN PERUNDANGAN: KESELAMATAN TEMPAT KERJA & HAK TOLAK KERJA BAHAYA*\n\n"
            "📌 *1. Hak Menolak Melakukan Kerja Bahaya (Seksyen 26A OSHA 1994 - Pindaan 2022)*\n"
            "• Pekerja mempunyai **hak di sisi undang-undang** untuk mengasingkan diri (*remove himself*) daripada tempat kerja sekiranya mempunyai alasan munasabah bahawa terdapat bahaya maut atau kecederaan parah yang pasti berlaku (*imminent danger*).\n"
            "• Majikan **dilarang sama sekali mendiskriminasi, mengambil tindakan disiplin, atau memotong gaji** pekerja yang menggunakan hak ini.\n\n"
            "📌 *2. Kewajipan Pekerja (Seksyen 24 OSHA 1994)*\n"
            "• Memakai dan menggunakan PPE (kasut keselamatan, topi keselamatan, dll.) yang dibekalkan oleh majikan sepanjang masa bertugas.\n"
            "• Mematuhi semua arahan dan SOP keselamatan di tapak kilang, gudang dan bengkel.\n\n"
            "📌 *3. Peranan Jawatankuasa Keselamatan Kesatuan (Artikel 69 CA-7)*\n"
            "• Sebarang ketidakpatuhan keselamatan jentera atau fasiliti elektrik/mekanikal boleh dilaporkan terus kepada Wakil Kesatuan dalam Jawatankuasa OSH."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_akta_keyboard())

    elif data == 'akta_perkeso':
        text = (
            "🛡️ *PANDUAN PERUNDANGAN: TUNTUTAN PERKESO (SOCSO) & KEMALANGAN*\n\n"
            "📌 *1. Skim Bencana Pekerjaan (Akta 4 - Akta Keselamatan Sosial Pekerja 1969)*\n"
            "• *Bencana Semasa Kerja:* Kemalangan yang berlaku semasa menjalankan tugas rasmi di kilang/gudang/pejabat.\n"
            "• *Bencana Perjalanan (Pergi/Balik Kerja):* Meliputi laluan biasa antara tempat kediaman dengan tempat kerja, atau perjalanan yang ada kaitan dengan tugas rasmi.\n\n"
            "📌 *2. Faedah Hilang Upaya Sementara (MC Kemalangan)*\n"
            "• PERKESO membayar elaun ganti rugi harian sebanyak **80% daripada purata gaji harian** sepanjang tempoh MC akibat kemalangan kerja.\n\n"
            "📌 *3. Dokumen Wajib Untuk Tuntutan Kemalangan Perjalanan*\n"
            "1️⃣ Laporan Polis (dibuat dalam tempoh 24 jam selepas kejadian).\n"
            "2️⃣ Peta lakaran laluan perjalanan (menunjukkan tempat kemalangan berada di laluan biasa pergi/balik kerja).\n"
            "3️⃣ Salinan Kad Pengenalan & Slip Gaji 6 bulan terakhir.\n"
            "4️⃣ Sijil Cuti Sakit asal (MC) dan Borang 34 PERKESO yang disahkan majikan/kesatuan."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_akta_keyboard())

    # 3. MENU ADUAN & PERATURAN KILANAN
    elif data == 'menu_aduan':
        text = (
            "⚠️ *SALURAN ADUAN & TATACARA KILANAN (ARTIKEL 15)*\n\n"
            "Jika anda menghadapi sebarang pertikaian atau ketidakadilan di tempat kerja, patuhi 4 peringkat rasmi ini:\n\n"
            "1️⃣ *Peringkat 1 (Aduan Awal):*\n"
            "• Bincang terus dengan Penyelia / Pegawai Atasan dalam tempoh *7 hari* dari tarikh kejadian. Tindakan perlu diselesaikan dalam 7 hari bekerja.\n\n"
            "2️⃣ *Peringkat 2 (Borang Rasmi Lampiran II):*\n"
            "• Jika gagal di Peringkat 1, kemukakan aduan bertulis guna *Borang Kilanan* kepada Pengurus. Anda berhak diwakili AJK Kesatuan. Tindakan dalam 7 hari bekerja.\n\n"
            "3️⃣ *Peringkat 3 (Rujukan HQ & Kesatuan):*\n"
            "• Dibawa ke Jabatan HR Ibu Pejabat bersama Kesatuan (Mesyuarat wajib dalam tempoh 14 hari).\n\n"
            "4️⃣ *Peringkat 4 (Pengurusan Tertinggi / JPP):*\n"
            "• Rujukan kepada Pengurusan Tertinggi BERNAS (60 hari) sebelum dibawa ke Kementerian Sumber Manusia (JPP/Mahkamah Perusahaan).\n\n"
            "📞 *Hubungi Exco Kesatuan:* Sila maklumkan kepada Setiausaha / AJK Cawangan jika perlukan wakil kesatuan."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_main_keyboard())

    # 4. MENU KEBAJIKAN
    elif data == 'menu_kebajikan':
        text = (
            "🤝 *TABUNG KEBAJIKAN AHLI KESATUAN (KPPbNB)*\n\n"
            "Faedah kebajikan khas untuk ahli berdaftar KPPbNB:\n"
            "• 🎁 *Sumbangan Perkahwinan Ahli*\n"
            "• 🎓 *Insentif Kecemerlangan Anak Ahli (SPM/STPM/Universiti)*\n"
            "• 🌧️ *Bantuan Bencana Alam & Kecemasan*\n"
            "• 🕊️ *Khairat Kematian Ahli & Tanggungan*\n\n"
            "📝 *Cara Memohon:* Dapatkan borang kebajikan melalui Bendahari/Setiausaha Cawangan berserta dokumen sokongan (resit/sijil berkaitan)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_main_keyboard())

    # 5. MENU INFO TERKINI
    elif data == 'menu_info':
        text = (
            "📢 *INFO TERKINI & MAKLUMAN KESATUAN*\n\n"
            "• 📌 Pelaksanaan Perjanjian Bersama Ke-7 (CA-7) berkuatkuasa *1 Jan 2026 - 31 Dis 2028*.\n"
            "• 📌 Pastikan caruman yuran bulanan kesatuan dipotong secara tepat melalui slip gaji.\n"
            "• 📌 Makluman tarikh Mesyuarat Agung Dwi-Tahunan (AGM) akan dipaparkan di Papan Kenyataan Kesatuan di setiap Kompleks/Gudang BERNAS.\n\n"
            "_Sentiasa bersatu demi kebajikan dan keharmonian warga kerja BERNAS!_"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_main_keyboard())

# ==================== MAIN EXECUTION ====================

async def async_main():
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Bot KPPbNB sedang dijalankan...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    calc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_calc, pattern='^menu_kalkulator$')],
        states={
            STATE_GRADE: [
                CallbackQueryHandler(calc_grade_selected, pattern='^grade_')
            ],
            STATE_SCHEDULE: [
                CallbackQueryHandler(calc_schedule_selected, pattern='^sch_')
            ],
            STATE_DAY_TYPE: [
                CallbackQueryHandler(calc_day_type_selected, pattern='^day_')
            ],
            STATE_SALARY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, calc_salary_received)
            ],
            STATE_HOURS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, calc_hours_received)
            ],
            STATE_GRED_S_HOURS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, calc_gred_s_hours_received)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(calc_cancel, pattern='^menu_utama$'),
            CommandHandler("start", start)
        ]
    )
    
    app.add_handler(calc_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    async with app:
        await app.start()
        await app.updater.start_polling()
        print("Bot KPPbNB LIVE dan bersedia menerima arahan!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()

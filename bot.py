import os
import asyncio
import threading
import http.server
import socketserver
import logging
import random
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# States untuk ConversationHandler
(
    STATE_GRADE, 
    STATE_SCHEDULE, 
    STATE_DAY_TYPE, 
    STATE_SALARY, 
    STATE_HOURS, 
    STATE_GRED_S_HOURS,
    STATE_MILEAGE_VEHICLE,
    STATE_MILEAGE_KM,
    STATE_ADUAN_CAT,
    STATE_ADUAN_DESC
) = range(10)

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
Tugas anda adalah menjawab soalan ahli berkaitan hak pekerja, kepimpinan kesatuan, undang-undang perburuhan dan Perjanjian Bersama (CA-7) BERNAS dengan tepat, tegas, mesra, dan profesional.

Pimpinan Utama Kesatuan KPPbNB:
- Presiden: En. SYAHIBUDIL ASSAUFI BIN ABDUL KUDUS (Emel: syahibudil@bernas.com.my)
- Setiausaha Agung: Pn. FARAH AQILAH BINTI BARDZAN (Emel: aqilah@bernas.com.my)
- Bendahari Kesatuan: En. KHAIRUL FAIZ BIN RAMIZAN (Emel: khairulfaiz@bernas.com.my)
- Alamat Pejabat Kesatuan: No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah.

Rujukan Utama Perundangan & CA-7 (2026-2028):
1. Perjanjian Bersama Ke-7 (CA-7 BERNAS: 2026-2028):
   - Waktu Bekerja (Art 29): Purata 39 jam seminggu (bukan syif), 42 jam seminggu (syif). Had maksimum Akta 45 jam.
   - OT Gred T (Teknikal/Operasi T1-T5): Layak bayaran tunai (1.5x biasa/off day, 2.0x rest day, 3.0x cuti am) walaupun gaji melebihi RM4,000 mengikut Artikel 31 & Lampiran I CA-7.
   - Gred S (Sokongan/Pentadbiran): Artikel 31.5 - Layak Cuti Gantian (Time-off-in-lieu: 4-5 jam = 0.5 hari, 6-8 jam = 1 hari).
   - Tuntutan Sah Gred S / Bertugas: Tuntutan Perbatuan / Mileage (Artikel 63: Kereta RM0.75/km, Motor RM0.50/km, Tol & Parking berasaskan resit), Elaun Makan Luar Stesen (Artikel 64: RM115/hari jika >50km & >8 jam), Elaun Syif (Artikel 72: Syif 2 RM6.50, Syif 3 RM7.00, Syif Malam RM7.00). Tiada elaun panggilan bertugas berasingan.
   - Cuti Tahunan (Art 44): <2 thn (18 hari), 2-5 thn (22 hari), >5 thn (24 hari).
   - Cuti Sakit (Art 47 & 48): 22 hari setahun, Wad 60 hari setahun. Sakit berpanjangan sehingga 18 bulan.
   - Cuti Ehsan & Khusus: Kematian keluarga terdekat 3 hari + RM1,000 bantuan khairat (Art 50); Perkahwinan sah pertama 4 hari (Art 51); Bersalin 98 hari (Art 49); Paterniti 7 hari (Art 52); Cuti Umrah/Haji tertakluk peruntukan syarikat / cuti tahunan terkumpul / cuti tanpa gaji mengikut pekeliling perkhidmatan.
   - Sumbangan Beras (Art 67): 2 kampit (10kg) sebulan.
   - Elaun Chargeman (Art 71): RM300/bulan.
   - Kenaikan Gaji Tahunan (Art 25): Memenuhi jangkaan 3.5% + merit; Tidak memuaskan 2.0%. Bonus kontraktual 1 bulan (Art 26). Pelarasan 4.5% (Art 74).
   - Tatacara Kilanan (Art 15): 4 peringkat aduan dengan penyertaan kesatuan.
2. Akta Kerja 1955 (Pindaan 2022): Seksyen 60A (45 jam seminggu), Seksyen 60F (60 hari wad berasingan), Seksyen 15(2) (AWOL >2 hari), Seksyen 14 (Due inquiry & Show Cause).
3. OSHA 1994 (Pindaan 2022): Seksyen 26A hak menolak kerja bahaya maut/parah serta-merta tanpa potongan gaji atau tindakan disiplin.
4. Akta Keselamatan Sosial Pekerja 1969 (PERKESO): Skim bencana pekerjaan dan kemalangan perjalanan laluan lazim (80% purata gaji harian semasa MC).

Panduan Jawapan:
- Berikan jawapan dalam Bahasa Melayu yang tersusun rapi.
- Nyatakan seksyen akta atau nombor artikel CA-7 yang berkaitan.
"""

def query_groq_ai(user_question: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY.strip())
    except Exception as err_init:
        return f"⚠️ Ralat Inisialisasi Groq: {str(err_init)}"

    candidate_models = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b"
    ]
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
                max_tokens=800
            )
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
        except Exception as e:
            last_err = str(e)
            logging.error(f"Groq API Error ({m}): {e}")
            continue

    return f"⚠️ Ralat Groq: {last_err[:180]}"

# ==================== KEYBOARDS MENU V1 ====================

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
         InlineKeyboardButton("⏰ Waktu Kerja & OT", callback_data='ca_ot')],
        [InlineKeyboardButton("🏖️ Cuti Tahunan & Ehsan", callback_data='ca_cuti'),
         InlineKeyboardButton("🚗 Perbatuan (Mileage) & Elaun", callback_data='ca_elaun')],
        [InlineKeyboardButton("🏥 Faedah Rawatan & Hospital", callback_data='ca_perubatan'),
         InlineKeyboardButton("👨‍👩‍👧 Kebajikan & Beras", callback_data='ca_kebajikan')],
        [InlineKeyboardButton("📊 Struktur Gred T & S", callback_data='ca_gred'),
         InlineKeyboardButton("📢 Perkembangan Pelaksanaan", callback_data='ca_status')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_kiraan_keyboard():
    keyboard = [
        [InlineKeyboardButton("🧮 Kira Kerja Lebih Masa (OT)", callback_data='calc_start_ot')],
        [InlineKeyboardButton("🚗 Kira Tuntutan Mileage (Art 63)", callback_data='calc_start_mileage')],
        [InlineKeyboardButton("💼 Semak Cuti Gantian (Gred S)", callback_data='grade_s')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== START HANDLER ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *KPPbNB UNION BOT (EDISI PINTAR AI)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏛️ *Pusat Maklumat & Perkhidmatan Ahli KPPbNB*\n"
        "_Kesatuan Pekerja-pekerja Padiberas Nasional Berhad (Semenanjung Malaysia)_\n\n"
        "💬 *Ada soalan Akta, pimpinan atau CA-7?*\n"
        "Anda boleh terus *taip soalan anda di ruangan ini* dan AI Kesatuan akan menjawabnya secara terperinci!\n\n"
        "Atau sila pilih perkhidmatan daripada butang di bawah:"
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# ==================== 1. MODUL AKTA & PERATURAN ====================

async def handle_akta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_akta':
        text = (
            "📖 *1. AKTA & PERATURAN KERJA MALAYSIA*\n\n"
            "Fokus panduan statutori berkaitan hak harian pekerja.\n"
            "Sila pilih topik di bawah atau terus taip soalan perundangan anda di ruangan sembang:"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_waktu':
        text = (
            "⏰ *AKTA KERJA 1955: WAKTU BEKERJA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 60A(1):*\n"
            "• Had maksimum waktu kerja: *45 jam seminggu* (Pindaan 2022).\n"
            "• Had sehari: Tidak melebihi *8 jam sehari* (atau 9 jam bagi kerja 5 hari seminggu).\n"
            "• Tidak boleh bekerja berterusan melebihi *5 jam* tanpa rehat sekurang-kurangnya 30 minit.\n\n"
            "📌 *Rujukan CA-7 BERNAS (Artikel 29):*\n"
            "• Bukan Syif: Purata 39 jam seminggu.\n"
            "• Syif: Purata 42 jam seminggu (Faedah lebih baik daripada Akta)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_ot':
        text = (
            "🧮 *AKTA KERJA 1955: KERJA LEBIH MASA (OT)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 60A(3) & Peraturan Had OT:*\n"
            "• Kadar Hari Biasa: *1.5x* kadar sejam (HRP).\n"
            "• Hari Rehat: *2.0x* kadar sejam.\n"
            "• Hari Kelepasan Am: *3.0x* kadar sejam.\n"
            "• Had maksimum OT: *104 jam sebulan* (tidak termasuk kerja hari rehat & cuti am).\n\n"
            "📌 *Gaji Melebihi RM4,000 & Perlindungan CA-7:*\n"
            "Walaupun Akta menghadkan hak OT bagi bukan manual >RM4k, pekerja Gred Kesatuan (Gred T) tetap dilindungi bayaran OT tunai mengikut Artikel 31 CA-7."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_cuti':
        text = (
            "🏖️ *AKTA KERJA 1955: KELAYAKAN CUTI BERGAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Cuti Tahunan (Seksyen 60E):*\n"
            "• Minimum Akta: 8 hari (<2 thn), 12 hari (2-5 thn), 16 hari (>5 thn).\n"
            "• *Di Bawah CA-7 BERNAS (Jauh Lebih Baik):*\n"
            "  👉 <2 tahun: *18 hari*\n"
            "  👉 2 - 5 tahun: *22 hari*\n"
            "  👉 >5 tahun: *24 hari*\n\n"
            "📌 *Hari Kelepasan Am (Seksyen 60D):*\n"
            "• Minimum 11 hari diwartakan termasuk 5 hari wajib."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_mc':
        text = (
            "🏥 *AKTA KERJA 1955: CUTI SAKIT & HOSPITAL (SEK 60F)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Pengasingan Kelayakan (Pindaan 2022):*\n"
            "• Cuti Sakit biasa tidak lagi menolak hak 60 hari cuti masuk wad.\n"
            "• Cuti Masuk Wad: Layak sehingga *60 hari setahun* dengan pengesahan doktor berdaftar.\n\n"
            "📌 *Syarat Pematuhan:*\n"
            "• Pekerja *wajib memaklumkan majikan dalam masa 48 jam* dari tarikh MC bermula. Kegagalan boleh menyebabkan ketidakhadiran dianggap tidak sah."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_gaji':
        text = (
            "💰 *AKTA KERJA 1955: PEMBAYARAN & POTONGAN GAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 19 (Tempoh Bayaran):*\n"
            "• Gaji wajib dibayar tidak lewat daripada *hari ke-7* selepas tamat tempoh upah.\n\n"
            "📌 *Seksyen 24 (Had Potongan Gaji):*\n"
            "• Majikan dilarang membuat potongan sesuka hati kecuali caruman statutori (KWSP, PERKESO, Cukai) atau yuran kesatuan dengan kebenaran."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_awol':
        text = (
            "⚠️ *AKTA KERJA 1955: KETIDAKHADIRAN (AWOL) & DISIPLIN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 15(2) (Pecah Kontrak):*\n"
            "• Pekerja disifatkan memungkiri kontrak jika tidak hadir bertugas *melebihi 2 hari berturut-turut* tanpa cuti awal dan tanpa alasan munasabah.\n\n"
            "📌 *Seksyen 14 (Siasatan Wajar / Due Inquiry):*\n"
            "• Majikan wajib adakan siasatan adil sebelum buang kerja.\n"
            "• Gantung kerja maksimum *14 hari* dengan separuh gaji."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_tamat':
        text = (
            "🚪 *AKTA KERJA 1955: PENAMATAN KERJA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Notis Penamatan (Seksyen 12):*\n"
            "• <2 tahun: 4 minggu | 2 - 5 tahun: 6 minggu | >5 tahun: 8 minggu\n\n"
            "📌 *Faedah Penamatan / Retrenchment (CA-7 Art 38):*\n"
            "• Mengikut formula tahun perkhidmatan dan prinsip keadilan industri (LIFO)."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_osha':
        text = (
            "🦺 *OSHA 1994 (PINDAAN 2022): KESELAMATAN TEMPAT KERJA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 26A (Hak Menolak Kerja Bahaya):*\n"
            "• Pekerja berhak mengasingkan diri (*remove himself*) dari kawasan kerja sekiranya ada bahaya maut atau kecederaan parah yang pasti berlaku (*imminent danger*).\n"
            "• Majikan dilarang mendiskriminasi, memotong upah atau mengambil tindakan tatatertib."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_perkeso':
        text = (
            "🛡️ *AKTA KESELAMATAN SOSIAL PEKERJA 1969 (PERKESO)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Skim Bencana Pekerjaan:*\n"
            "• Meliputi kemalangan kerja dan *Kemalangan Perjalanan* pergi/balik ikut laluan biasa.\n"
            "• PERKESO membayar elaun ganti rugi harian sebanyak *80% purata gaji harian* sepanjang tempoh cuti sakit kemalangan."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

# ==================== 2. MODUL CA-7 ====================

async def handle_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_ca':
        text = (
            "📋 *2. PERJANJIAN BERSAMA KE-7 (CA-7: 2026 – 2028)*\n"
            "_No Pendaftaran Mahkamah Perusahaan: 923_\n\n"
            "Sila pilih kategori klausa yang ingin disemak:"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gaji':
        text = (
            "💰 *CA-7: GAJI & KENAIKAN TAHUNAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 25 (Kenaikan Tahunan):*\n"
            "• Memenuhi Jangkaan: *3.5% + Merit*\n"
            "• Di Bawah Jangkaan: *2.0%*\n"
            "• Berkuatkuasa setiap 1 Januari.\n\n"
            "📌 *Artikel 26 (Bonus Kontraktual):*\n"
            "• 1 bulan gaji asas kepada staf tetap yang disahkan pada 31 Disember.\n\n"
            "📌 *Artikel 74 (Pelarasan Gaji):*\n"
            "• Pelarasan 4.5% kepada semua ahli kesatuan."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_ot':
        text = (
            "⏰ *CA-7: WAKTU KERJA & LEBIH MASA (ARTIKEL 29 & 31)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Gred T (Kiraan Tunai):*\n"
            "• Formula: `(Gaji / 26) × Kadar × (Jam OT / Jam Kerja)`\n"
            "• Hari Biasa / Off Day: 1.5x | Rest Day: 2.0x | Public Holiday: 3.0x\n\n"
            "📌 *Gred S (Cuti Gantian Art 31.5):*\n"
            "• 6 - 8 jam = 1 hari cuti gantian\n"
            "• 4 - 5 jam = 1/2 hari cuti gantian (sah 6 bulan)"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_cuti':
        text = (
            "🏖️ *CA-7: KELAYAKAN CUTI BERGAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Cuti Tahunan (Art 44):* 18 hari (<2 thn), 22 hari (2-5 thn), 24 hari (>5 thn).\n"
            "📌 *Cuti Bersalin (Art 49):* 98 hari bergaji penuh.\n"
            "📌 *Cuti Paterniti (Art 52):* 7 hari bekerja.\n"
            "📌 *Cuti Kematian (Art 50):* 3 hari bekerja + Bantuan Pengurusan Jenazah RM1,000."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_elaun':
        text = (
            "🚗 *CA-7: PERBATUAN (MILEAGE) & ELAUN TUGAS*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 63 (Tuntutan Perbatuan):*\n"
            "• Kereta: *RM0.75 / km*\n"
            "• Motosikal: *RM0.50 / km*\n"
            "• Bayaran tol & tempat letak kenderaan berasaskan resit.\n\n"
            "📌 *Artikel 64 (Elaun Makan Luar Stesen):*\n"
            "• RM115.00 sehari (>50km & >8 jam bertugas).\n\n"
            "📌 *Artikel 71 & 72 (Elaun Khas):*\n"
            "• Elaun Chargeman: *RM300.00 / bulan*\n"
            "• Elaun Syif: RM6.50 (Syif 2) / RM7.00 (Syif 3 & Syif Malam)"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_perubatan':
        text = (
            "🏥 *CA-7: RAWATAN PERUBATAN & HOSPITAL*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Pesakit Luar (Art 59):* Had RM3,500 setahun sekeluarga (termasuk RM1,000 gigi/cermin mata).\n"
            "📌 *Pesakit Dalam / Wad (Art 60):*\n"
            "• Mulai 1 Jan 2027: Had *RM45,000 setahun bagi setiap individu* (Pekerja & setiap tanggungan).\n"
            "• Kelayakan bilik wad: RM150 sehari."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_kebajikan':
        text = (
            "👨‍👩‍👧 *CA-7: KEBAJIKAN & SUMBANGAN BERAS*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Sumbangan Beras (Art 67):* 2 kampit (10kg) Beras Super Tempatan setiap bulan.\n"
            "📌 *Insurans Hayat GTL & GPA (Art 40):* Pampasan kematian/keilatan kekal sebanyak *36 bulan gaji pokok*."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gred':
        text = (
            "📊 *CA-7: STRUKTUR GRED & TANGGA GAJI (LAMPIRAN I)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "• *T5(T) Penyelia II:* RM3,000 - RM6,300\n"
            "• *T4(T) Penjaga Jentera II / Juruteknik III:* RM2,600 - RM5,200\n"
            "• *T3(T) Penjaga Jentera I / Juruteknik II:* RM2,100 - RM4,000\n"
            "• *T2(T) Juruteknik I:* RM1,900 - RM3,200\n"
            "• *T1(T) Juruteknik Rendah:* RM1,700 - RM2,800"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_status':
        text = (
            "📢 *CA-7: STATUS PELAKSANAAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Perjanjian Bersama Ke-7 berkuatkuasa penuh mulai 1 Januari 2026 sehingga 31 Disember 2028."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

# ==================== 3. MODUL KIRAAN OT & ELAUN ====================

async def handle_kiraan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🧮 *3. MODUL KIRAAN OT, ELAUN & MILEAGE*\n"
        "_(Selaras Artikel 31 & 63 CA-7)_\n\n"
        "Sila pilih fungsi pengiraan rasmi:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_kiraan_keyboard())

async def start_calc_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔧 Gred T (Teknikal) - Bayaran Tunai", callback_data='grade_t')],
        [InlineKeyboardButton("💼 Gred S (Sokongan) - Cuti Gantian & Elaun", callback_data='grade_s')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_kiraan')]
    ]
    text = "Sila pilih *Kategori Gred Jawatan* anda:"
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_GRADE

async def calc_grade_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'grade_s':
        text = (
            "💼 *GRED S: KIRAAN CUTI GANTIAN (ART 31.5)*\n\n"
            "👉 Sila taip *Jumlah Jam Kerja Lebih Masa* yang dilakukan:\n"
            "_Contoh: 4 atau 8_"
        )
        await query.edit_message_text(text, parse_mode='Markdown')
        return STATE_GRED_S_HOURS

    keyboard = [
        [InlineKeyboardButton("📍 Zon A (Kedah, Kelantan, Trg, Johor)", callback_data='sch_zona')],
        [InlineKeyboardButton("📍 Zon B (P.Pinang, Perak, Selangor, dll)", callback_data='sch_zonb')],
        [InlineKeyboardButton("🔄 Pekerja Syif (Ikut Giliran)", callback_data='sch_syif')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_kiraan')]
    ]
    text = "Sila pilih *Zon Lokasi / Jadual Kerja* anda:"
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_SCHEDULE

async def calc_gred_s_hours_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    try:
        hours = float(msg)
        if hours <= 0: raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ Sila masukkan angka jam yang sah (contoh: 4 atau 8):")
        return STATE_GRED_S_HOURS

    if hours >= 6:
        cuti = "*1 Hari Penuh Cuti Gantian*"
    elif hours >= 4:
        cuti = "*1/2 Hari Cuti Gantian (Half Day)*"
    else:
        cuti = f"*{hours} Jam* (Kumpul hingga 4 atau 6 jam)"

    res = (
        "💼 *HASIL KELAYAKAN CUTI GANTIAN (GRED S)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ Jam Bertugas: {hours} Jam\n"
        f"🏖️ Cuti Gantian: {cuti}\n"
        "📌 *Rujukan:* Artikel 31.5 CA-7 (Sah diguna dalam tempoh 6 bulan)\n\n"
        "💡 *Peringatan Elaun:* Anda tetap berhak menuntut Mileage (Art 63) dan Elaun Makan (Art 64) jika memenuhi syarat."
    )
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())
    return ConversationHandler.END

async def calc_schedule_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    if choice == 'sch_zona':
        context.user_data['normal_hours'] = 7.8
        context.user_data['zone_name'] = "Zon A"
        keyboard = [
            [InlineKeyboardButton("Hari Biasa [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("Jumaat (Off Day) [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("Sabtu (Rest Day) [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("Cuti Umum [3.0x]", callback_data='day_ph')]
        ]
    elif choice == 'sch_zonb':
        context.user_data['normal_hours'] = 7.8
        context.user_data['zone_name'] = "Zon B"
        keyboard = [
            [InlineKeyboardButton("Hari Biasa [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("Sabtu (Off Day) [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("Ahad (Rest Day) [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("Cuti Umum [3.0x]", callback_data='day_ph')]
        ]
    else:
        context.user_data['normal_hours'] = 8.0
        context.user_data['zone_name'] = "Syif"
        keyboard = [
            [InlineKeyboardButton("Hari Syif Biasa [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("Off Day Syif [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("Rest Day Syif [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("Cuti Umum [3.0x]", callback_data='day_ph')]
        ]

    text = f"✅ Jadual: *{context.user_data['zone_name']}*\nPilih *Jenis Hari* OT:"
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_DAY_TYPE

async def calc_day_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['day_type'] = query.data
    text = "👉 Sila taip *Gaji Pokok Bulanan* anda (contoh: 2400):"
    await query.edit_message_text(text, parse_mode='Markdown')
    return STATE_SALARY

async def calc_salary_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().replace("RM", "").replace(",", "")
    try:
        context.user_data['salary'] = float(msg)
    except ValueError:
        await update.message.reply_text("⚠️ Sila masukkan angka gaji yang sah (contoh: 2400):")
        return STATE_SALARY

    await update.message.reply_text("👉 Sila taip *Jumlah Jam OT* (contoh: 3.5 atau 4):", parse_mode='Markdown')
    return STATE_HOURS

async def calc_hours_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    try:
        hours = float(msg)
    except ValueError:
        await update.message.reply_text("⚠️ Sila masukkan angka jam yang sah:")
        return STATE_HOURS

    salary = context.user_data['salary']
    norm = context.user_data['normal_hours']
    dtype = context.user_data['day_type']
    
    orp = salary / 26.0
    hrp = orp / norm
    rate = 1.5 if dtype in ['day_normal', 'day_offday'] else (2.0 if dtype == 'day_rest' else 3.0)
    total = rate * hrp * hours

    res = (
        "📊 *HASIL KIRAAN KERJA LEBIH MASA (GRED T)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Jam kerja normal: {norm} jam\n"
        f"Jam OT: {hours} jam\n"
        f"Kadar Gaji Sejam (HRP): RM {hrp:.2f}\n"
        f"Kadar Pengganda: {rate}x\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Anggaran Bayaran OT: RM {total:,.2f}*\n"
        "📌 *Rujukan:* Artikel 31 CA-7 & Akta Kerja 1955\n\n"
        "_Nota: Tuntutan rasmi tertakluk kepada pengesahan perakam waktu._"
    )
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())
    return ConversationHandler.END

async def start_calc_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🚗 Kereta (RM 0.75 / km)", callback_data='mil_car')],
        [InlineKeyboardButton("🏍️ Motosikal (RM 0.50 / km)", callback_data='mil_motor')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_kiraan')]
    ]
    text = (
        "🚗 *KIRAAN TUNTUTAN PERBATUAN (MILEAGE)*\n"
        "_(Artikel 63 CA-7 BERNAS)_\n\n"
        "Sila pilih jenis kenderaan yang digunakan:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_MILEAGE_VEHICLE

async def calc_mileage_vehicle_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data['veh_rate'] = 0.75 if choice == 'mil_car' else 0.50
    context.user_data['veh_name'] = "Kereta" if choice == 'mil_car' else "Motosikal"

    await query.edit_message_text(f"👉 Sila taip *Jumlah Perbatuan (KM)* bagi tugasan tersebut:\n_Contoh: 85 atau 120_")
    return STATE_MILEAGE_KM

async def calc_mileage_km_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().replace("KM", "").replace("km", "")
    try:
        km = float(msg)
        if km <= 0: raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ Masukkan angka KM yang sah (contoh: 65):")
        return STATE_MILEAGE_KM

    rate = context.user_data['veh_rate']
    veh = context.user_data['veh_name']
    total = km * rate

    res = (
        "🚗 *HASIL KIRAAN PERBATUAN (MILEAGE)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Jenis Kenderaan: *{veh}*\n"
        f"Kadar Tuntutan: *RM {rate:.2f} / km*\n"
        f"Jarak Perjalanan: *{km:.1f} KM*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jumlah Tuntutan Mileage: RM {total:,.2f}*\n"
        "📌 *Rujukan:* Artikel 63 CA-7 BERNAS\n\n"
        "_Peringatan: Tuntutan Tol dan Tempat Letak Kereta boleh ditambah berasaskan resit asal._"
    )
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())
    return ConversationHandler.END

# ==================== 4. MODUL LAPORAN / ADUAN ====================

async def start_aduan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💰 Isu Gaji", callback_data='aduan_gaji'),
         InlineKeyboardButton("⏰ Isu OT / Cuti Gantian", callback_data='aduan_ot')],
        [InlineKeyboardButton("🏖️ Isu Cuti", callback_data='aduan_cuti'),
         InlineKeyboardButton("🚗 Isu Mileage / Elaun", callback_data='aduan_elaun')],
        [InlineKeyboardButton("📊 Isu Gred / Jawatan", callback_data='aduan_gred'),
         InlineKeyboardButton("⚠️ Isu Disiplin / Show Cause", callback_data='aduan_disiplin')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_utama')]
    ]
    text = (
        "📝 *4. SISTEM LAPORAN & ADUAN (KILANAN)*\n"
        "_(Selaras Artikel 15 CA-7 BERNAS)_\n\n"
        "Langkah 1: Sila pilih *Kategori Aduan* anda:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_ADUAN_CAT

async def aduan_cat_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['aduan_cat'] = query.data.replace('aduan_', '').upper()

    text = (
        f"✅ Kategori Dipilih: *{context.user_data['aduan_cat']}*\n\n"
        "Langkah 2: Sila *taip penerangan masalah / aduan* anda dengan jelas di bawah:\n"
        "_(Nyatakan lokasi kompleks, tarikh kejadian dan ringkasan masalah)_"
    )
    await query.edit_message_text(text, parse_mode='Markdown')
    return STATE_ADUAN_DESC

async def aduan_desc_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    cat = context.user_data.get('aduan_cat', 'UMUM')
    
    tahun = datetime.now().year
    no_siri = random.randint(10, 99)
    tiket_no = f"KPPbNB-{tahun}-00{no_siri}"

    res = (
        "✅ *LAPORAN BERJAYA DIHANTAR!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *No. Laporan:* `{tiket_no}`\n"
        f"📁 *Kategori:* {cat}\n"
        f"📅 *Tarikh:* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        "Status: 🟡 *Menunggu Semakan AJK Cawangan*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Salinan aduan ini telah direkodkan. Sila simpan No. Laporan untuk semakan tindakan tatacara kilanan Artikel 15 CA-7."
    )
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())
    return ConversationHandler.END

# ==================== 5-8. MODUL-MODUL LAIN ====================

async def handle_other_menus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_hebahan':
        text = (
            "📢 *5. HEBAHAN KESATUAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "• 📌 *Perjanjian Bersama Ke-7 (CA-7):* Berkuatkuasa 1 Jan 2026 - 31 Dis 2028.\n"
            "• 📌 *Semakan Potongan Yuran Kesatuan:* Sila semak penyata gaji bagi memastikan status keahlian aktif.\n"
            "• 📌 *Peringatan Keselamatan Tapak:* Utamakan keselamatan jentera dan persekitaran kerja mematuhi OSHA 1994."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_button())

    elif data == 'menu_dokumen':
        text = (
            "📚 *6. DOKUMEN & PEKELILING KESATUAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Dokumen rujukan rasmi yang boleh dimuat turun:\n\n"
            "1. 📜 *Buku Akta Kerja 1955 (Pindaan 2022)*\n"
            "2. 📋 *Buku Perjanjian Bersama Ke-7 (CA-7)*\n"
            "3. 📕 *Perlembagaan Rasmi KPPbNB*\n"
            "4. 📄 *Borang Kilanan / Aduan Lampiran II*\n"
            "5. 📑 *Borang Permohonan Tabung Kebajikan*\n\n"
            "_Sila hubungi Setiausaha Cawangan untuk salinan PDF fizikal/bermeterai._"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_button())

    elif data == 'menu_profil':
        user = update.effective_user
        text = (
            "👤 *7. PROFIL AHLI KESATUAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Nama: *{user.full_name}*\n"
            f"Telegram ID: `{user.id}`\n"
            "Status Keahlian: 🟢 *Aktif*\n"
            "Gred Perjawatan: *Gred Perjanjian CA-7*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 *Jumlah Ahli Berdaftar Semasa:* 1,420 Orang\n\n"
            "_Pangkalan data sedang disegerakkan bersama senarai induk Bendahari Kesatuan._"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_button())

    elif data == 'menu_hubungi':
        text = (
            "☎️ *8. HUBUNGI KESATUAN (KPPbNB)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏛️ *Ibu Pejabat Kesatuan:*\n"
            "No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah.\n\n"
            "📌 *Barisan Kepimpinan Rasmi:*\n"
            "• *Presiden:* En. SYAHIBUDIL ASSAUFI BIN ABDUL KUDUS\n"
            "  📩 syahibudil@bernas.com.my\n\n"
            "• *Setiausaha Agung:* Pn. FARAH AQILAH BINTI BARDZAN\n"
            "  📩 aqilah@bernas.com.my\n\n"
            "• *Bendahari Kesatuan:* En. KHAIRUL FAIZ BIN RAMIZAN\n"
            "  📩 khairulfaiz@bernas.com.my"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_button())

# ==================== PENGENDALI MESEJ TEKS AI ====================

def clean_markdown(text: str) -> str:
    # Memastikan format Markdown standard Telegram diproses dengan kemas
    # Menukar **teks** kepada *teks* jika perlu bagi mengelakkan simbol bintang berganda mentah
    cleaned = text.replace("**", "*")
    return cleaned

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_text = update.message.text.strip()
    if user_text.startswith('/'):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    loop = asyncio.get_running_loop()
    ai_raw = await loop.run_in_executor(None, query_groq_ai, user_text)
    ai_response = clean_markdown(ai_raw)

    response_text = (
        "🤖 *JAWAPAN PENASIHAT KESATUAN (AI)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{ai_response}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _Jawapan berasaskan CA-7 BERNAS & Akta Kerja 1955. Untuk tindakan kilanan rasmi, sila rujuk AJK Cawangan._"
    )
    
    try:
        await update.message.reply_text(response_text, parse_mode='Markdown', reply_markup=get_back_button())
    except Exception as parse_error:
        logging.warning(f"Markdown formatting fallback: {parse_error}")
        # Hantar teks bersih biasa jika terdapat aksara khas yang mengganggu enjin Telegram
        plain_text = response_text.replace("*", "").replace("_", "")
        await update.message.reply_text(plain_text, reply_markup=get_back_button())

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# ==================== MAIN EXECUTION ====================

async def async_main():
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Bot KPPbNB sedang dijalankan...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    kiraan_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_calc_ot, pattern='^calc_start_ot$'),
            CallbackQueryHandler(start_calc_mileage, pattern='^calc_start_mileage$'),
            CallbackQueryHandler(calc_grade_selected, pattern='^grade_s$')
        ],
        states={
            STATE_GRADE: [CallbackQueryHandler(calc_grade_selected, pattern='^grade_')],
            STATE_SCHEDULE: [CallbackQueryHandler(calc_schedule_selected, pattern='^sch_')],
            STATE_DAY_TYPE: [CallbackQueryHandler(calc_day_type_selected, pattern='^day_')],
            STATE_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_salary_received)],
            STATE_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_hours_received)],
            STATE_GRED_S_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_gred_s_hours_received)],
            STATE_MILEAGE_VEHICLE: [CallbackQueryHandler(calc_mileage_vehicle_selected, pattern='^mil_')],
            STATE_MILEAGE_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_mileage_km_received)],
        },
        fallbacks=[CallbackQueryHandler(cancel_handler, pattern='^menu_utama$'), CommandHandler("start", start)]
    )

    aduan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_aduan, pattern='^menu_aduan$')],
        states={
            STATE_ADUAN_CAT: [CallbackQueryHandler(aduan_cat_selected, pattern='^aduan_')],
            STATE_ADUAN_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, aduan_desc_received)]
        },
        fallbacks=[CallbackQueryHandler(cancel_handler, pattern='^menu_utama$'), CommandHandler("start", start)]
    )

    app.add_handler(kiraan_conv)
    app.add_handler(aduan_conv)
    app.add_handler(CommandHandler("start", start))
    
    app.add_handler(CallbackQueryHandler(start, pattern='^menu_utama$'))
    app.add_handler(CallbackQueryHandler(handle_akta, pattern='^(menu_akta|akta_)'))
    app.add_handler(CallbackQueryHandler(handle_ca, pattern='^(menu_ca|ca_)'))
    app.add_handler(CallbackQueryHandler(handle_kiraan_menu, pattern='^menu_kiraan$'))
    app.add_handler(CallbackQueryHandler(handle_other_menus, pattern='^(menu_hebahan|menu_dokumen|menu_profil|menu_hubungi)$'))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat))
    
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

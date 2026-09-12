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

# Telegram Chat ID Admin (En. Khairul Faiz)
# Bila dah dapat ID Group (cth: "-1002345678901"), gantikan nombor di bawah ini
ADMIN_CHAT_ID = "33746692"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
Tugas anda adalah menjawab soalan ahli berkaitan hak pekerja, kepimpinan kesatuan, undang-undang perburuhan dan Perjanjian Bersama Ke-7 (CA-7) BERNAS dengan tepat, tegas, mesra, dan profesional.

Pimpinan Utama Kesatuan KPPbNB:
- Presiden: En. SYAHIBUDIL ASSAUFI BIN ABDUL KUDUS (Emel: syahibudil@bernas.com.my)
- Setiausaha Agung: Pn. FARAH AQILAH BINTI BARDZAN (Emel: aqilah@bernas.com.my)
- Bendahari Kesatuan: En. KHAIRUL FAIZ BIN RAMIZAN (Emel: khairulfaiz@bernas.com.my)
- Alamat Pejabat Kesatuan: No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah Darul Aman.

Rujukan Terperinci CA-7 BERNAS (2026-2028):
1. Waktu Bekerja (Artikel 29):
   - Bukan Syif: Purata 39 jam seminggu.
     * Hari Bekerja Isnin - Jumaat (Ibu Pejabat & Luar Ibu Pejabat): 8.30 pagi - 5.30 petang (Waktu makan: 1.00 - 2.00 petang; Jumaat: 12.30 tengah hari - 2.30 petang).
     * Hari Bekerja Ahad - Khamis (Zon A): Ahad - Rabu 8.00 pagi - 5.00 petang; Khamis 8.00 pagi - 4.00 petang (Waktu makan: 1.00 - 2.00 petang).
   - Kerja Syif: Purata 42 jam seminggu.
     * 2 Syif (12 jam/syif): Syif Pertama (8.00 pagi - 8.00 malam), Syif Kedua (8.00 malam - 8.00 pagi).
     * 3 Syif (8 jam/syif): Syif Pertama (8.00 pagi - 4.00 petang), Syif Kedua (4.00 petang - 12.00 tengah malam), Syif Ketiga (12.00 tengah malam - 8.00 pagi).
     * Waktu Rehat Syif: Tambahan 30 minit rehat diberi bagi setiap 5 jam kerja berterusan jika OT dijadualkan.
     * Notis Pertukaran Jadual: Dimaklumkan sekurang-kurangnya 3 hari sebelum tarikh berkuat kuasa.

2. Kerja Lebih Masa & Bayaran (Artikel 30 & 31):
   - Artikel 30: Dilakukan atas permintaan majikan dengan persetujuan pekerja (tidak boleh tolak tanpa alasan munasabah).
   - Had Masa: Maksimum 104 jam sebulan (tidak termasuk kerja hari rehat & cuti umum).
   - Kiraan Lebih Masa (Gred T & Gred S [Gaji Bawah RM4,000]):
     * Formula: (Gaji / 26) × Kadar × (Jam OT / Jam Kerja Normal)
     * Kadar: Hari Biasa & Off Day (1.5x), Rest Day (2.0x), Cuti Kelepasan Am (3.0x).
   - Cuti Gantian (Artikel 31.5): Terpakai untuk Gred T dan Gred S sebagai ganti bayaran tunai.
     * 6 - 8 jam = 1 hari cuti gantian.
     * 4 - 5 jam = 1/2 hari cuti gantian.
     * Boleh dikumpul dalam tempoh 6 bulan pada tahun berkenaan.

3. Elaun Makan Lebih Masa Gaji ≥ RM4,000 (Artikel 64.3):
   - Terpakai bagi pekerja bergaji RM4,000 ke atas yang tidak layak bayaran lebih masa.
   - Hari Bekerja Biasa (Zon A: Ahad-Khamis | Zon B: Isnin-Jumaat):
     * 2 hingga 5 jam: RM25.00
     * Melebihi 5 jam: RM50.00
   - Hari Rehat, Off Day & Cuti Am (Zon A: Jumaat & Sabtu | Zon B: Sabtu & Ahad | PH):
     * Pilihan: Cuti Gantian ATAU Elaun Makan.
     * 4 hingga 8 jam: RM25.00 atau 1/2 hari cuti gantian.
     * Melebihi 8 jam: RM50.00 atau 1 hari cuti gantian.

4. Struktur Gred & Tangga Gaji (Lampiran I):
   - Gred T (Teknikal): T1 (RM1,700 - RM2,800) hingga T5 (RM3,000 - RM6,300).
   - Gred S (Sokongan): S1 (RM1,700 - RM2,800) hingga S5 (RM2,800 - RM5,400).

5. Cuti & Faedah Lain:
   - Cuti Tahunan (Art 44): <2 thn (18 hari), 2-5 thn (22 hari), >5 thn (24 hari).
   - Cuti Haji/Umrah (Art 55): 54 hari bergaji penuh sekali sepanjang perkhidmatan.
   - Cuti Bersalin (Art 49): 98 hari bergaji penuh. Pilihan tambahan 90 hari cuti tanpa gaji menjaga anak.
   - Cuti Paterniti (Art 52): 7 hari (khidmat >1 thn) / 3 hari (<1 thn).
   - Cuti Sakit (Art 47): 22 hari klinik, 60 hari hospital.
   - Sumbangan Beras (Art 67): 2 kampit (10kg) sebulan.
   - Insurans Kematian/Hilang Upaya (Art 40): 36 bulan gaji terakhir (GTL & GPA).
   - Elaun Perjalanan (Art 63): Kereta RM0.75/km, Motor RM0.50/km. Elaun Makan Luar Stesen: RM115/hari (Art 64.1).

Panduan Jawapan:
- Berikan jawapan dalam Bahasa Melayu yang tersusun rapi dan jelas mengikut zon jika berkaitan.
- Nyatakan nombor artikel CA-7 atau seksyen akta yang berkaitan.
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
                max_tokens=850
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
        [InlineKeyboardButton("📍 Panduan Zon A (Kedah, Kelantan, Trg, Johor)", callback_data='art64_zona')],
        [InlineKeyboardButton("📍 Panduan Zon B (P.Pinang, Perak, Selangor, dll)", callback_data='art64_zonb')],
        [InlineKeyboardButton("🔄 Panduan Staf Giliran Syif", callback_data='art64_syif')],
        [InlineKeyboardButton("🔙 Kembali ke Menu CA7", callback_data='menu_ca')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== START HANDLER ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *KPPbNB UNION BOT (EDISI PINTAR AI)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏛️ *Pusat Maklumat & Perkhidmatan Ahli KPPbNB*\n"
        "_Kesatuan Pekerja-pekerja Padiberas Nasional Berhad (Semenanjung Malaysia)_\n\n"
        "💬 *Ada soalan Akta, pimpinan, waktu kerja atau CA-7?*\n"
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
            "📌 *Pekerja Gaji Melebihi RM4,000 (CA-7 Art 31 & 64.3):*\n"
            "• Gred T: Dilindungi bayaran Artikel 31.\n"
            "• Pekerja bukan penerima OT: Layak menuntut *Elaun Makan Lebih Masa* di bawah Artikel 64.3."
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
            "Sila pilih klausa yang ingin disemak:"
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

    elif data == 'ca_waktu_kerja':
        text = (
            "⏰ *CA-7: WAKTU BEKERJA (ARTIKEL 29)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 *1. BUKAN SYIF (Purata 39 Jam Seminggu):*\n\n"
            "📍 *Isnin hingga Jumaat (Ibu Pejabat & Luar Ibu Pejabat):*\n"
            "• Waktu Kerja: 8.30 pagi – 5.30 petang\n"
            "• Rehat: 1.00 – 2.00 petang (Jumaat: 12.30 t/hari – 2.30 petang)\n\n"
            "📍 *Ahad hingga Khamis (Zon A):*\n"
            "• Ahad – Rabu: 8.00 pagi – 5.00 petang (Rehat: 1.00 – 2.00 petang)\n"
            "• Khamis: 8.00 pagi – 4.00 petang (Rehat: 1.00 – 2.00 petang)\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔄 *2. PEKERJA SYIF (Purata 42 Jam Seminggu):*\n\n"
            "📍 *Sistem 2 Syif (12 jam/syif):*\n"
            "• Syif 1: 8.00 pagi – 8.00 malam\n"
            "• Syif 2: 8.00 malam – 8.00 pagi\n\n"
            "📍 *Sistem 3 Syif (8 jam/syif):*\n"
            "• Syif 1: 8.00 pagi – 4.00 petang\n"
            "• Syif 2: 4.00 petang – 12.00 tengah malam\n"
            "• Syif 3: 12.00 tengah malam – 8.00 pagi\n\n"
            "📌 *Peraturan Rehat & Notis:* Tambahan rehat 30 minit diberi bagi setiap 5 jam kerja berterusan jika OT dijadualkan. Notis pertukaran jadual sekurang-kurangnya 3 hari sebelum kuat kuasa."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_ot':
        text = (
            "🧮 *CA-7: KERJA LEBIH MASA & CUTI GANTIAN (ARTIKEL 30 & 31)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 30 (Keperluan Tugas):*\n"
            "• Dilakukan atas permintaan BERNAS dengan persetujuan pekerja (tidak boleh tolak tanpa alasan munasabah).\n\n"
            "📌 *Had Maksimum OT (Art 31.4):*\n"
            "• Had 104 jam sebulan (tidak termasuk kerja hari rehat & cuti umum).\n\n"
            "📌 *Kiraan Lebih Masa (Gred T & Gred S [Gaji Bawah RM4,000]):*\n"
            "• Formula: `(Gaji / 26) × Kadar × (Jam OT / Jam Kerja Normal)`\n"
            "• Hari Biasa / Off Day: 1.5x\n"
            "• Rest Day: 2.0x\n"
            "• Hari Kelepasan Am: 3.0x\n\n"
            "📌 *Cuti Gantian (Gred T & Gred S - Art 31.5):*\n"
            "• 6 - 8 jam bekerja = 1 hari cuti gantian\n"
            "• 4 - 5 jam bekerja = 1/2 hari cuti gantian\n"
            "*(Sah dikumpulkan dalam tempoh 6 bulan. Pekerja yang memilih cuti gantian tidak layak membuat tuntutan bayaran lebih masa)*\n\n"
            "💡 *Pekerja Gaji RM4,000 Ke Atas:* Layak menuntut *Elaun Makan Lebih Masa* di bawah Artikel 64.3."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_elaun_4k_menu':
        text = (
            "🍱 *CA-7: ELAUN MAKAN LEBIH MASA GAJI ≥ RM4,000 (ARTIKEL 64.3)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Bagi staf bergaji RM4,000 ke atas yang tidak layak bayaran lebih masa, pelaksanaan terbahagi mengikut zon kerja:\n\n"
            "Sila pilih zon anda untuk melihat ketetapan hari bekerja dan hari rehat yang tepat:"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'art64_zona':
        text = (
            "📍 *ARTIKEL 64.3: ZON A (Kedah, Kelantan, Terengganu, Johor)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 *1. Hari Bekerja Biasa (Ahad hingga Khamis):*\n"
            "• Kerja lebih masa 2 hingga 5 jam: **RM25.00**\n"
            "• Kerja lebih masa melebihi 5 jam: **RM50.00**\n\n"
            "🏖️ *2. Jumaat (Off Day), Sabtu (Rest Day) & Cuti Am:*\n"
            "Pekerja boleh **memilih** sama ada:\n"
            "👉 *Pilihan A (Elaun Makan Tunai):*\n"
            "• Bertugas 4 hingga 8 jam: **RM25.00**\n"
            "• Bertugas melebihi 8 jam: **RM50.00**\n\n"
            "👉 *Pilihan B (Cuti Gantian):*\n"
            "• Bertugas 4 hingga 8 jam: **1/2 Hari Cuti Gantian**\n"
            "• Bertugas melebihi 8 jam: **1 Hari Penuh Cuti Gantian**"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'art64_zonb':
        text = (
            "📍 *ARTIKEL 64.3: ZON B (P.Pinang, Perak, Selangor, KL, dll)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 *1. Hari Bekerja Biasa (Isnin hingga Jumaat):*\n"
            "• Kerja lebih masa 2 hingga 5 jam: **RM25.00**\n"
            "• Kerja lebih masa melebihi 5 jam: **RM50.00**\n\n"
            "🏖️ *2. Sabtu (Off Day), Ahad (Rest Day) & Cuti Am:*\n"
            "Pekerja boleh **memilih** sama ada:\n"
            "👉 *Pilihan A (Elaun Makan Tunai):*\n"
            "• Bertugas 4 hingga 8 jam: **RM25.00**\n"
            "• Bertugas melebihi 8 jam: **RM50.00**\n\n"
            "👉 *Pilihan B (Cuti Gantian):*\n"
            "• Bertugas 4 hingga 8 jam: **1/2 Hari Cuti Gantian**\n"
            "• Bertugas melebihi 8 jam: **1 Hari Penuh Cuti Gantian**"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'art64_syif':
        text = (
            "🔄 *ARTIKEL 64.3: PEKERJA SYIF*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 *1. Hari Bertugas Syif Biasa (Mengikut Jadual):*\n"
            "• Kerja lebih masa 2 hingga 5 jam: **RM25.00**\n"
            "• Kerja lebih masa melebihi 5 jam: **RM50.00**\n\n"
            "🏖️ *2. Hari Off Day Syif, Rest Day Syif & Cuti Am:*\n"
            "Pekerja boleh **memilih** sama ada:\n"
            "👉 *Pilihan A (Elaun Makan Tunai):*\n"
            "• Bertugas 4 hingga 8 jam: **RM25.00**\n"
            "• Bertugas melebihi 8 jam: **RM50.00**\n\n"
            "👉 *Pilihan B (Cuti Gantian):*\n"
            "• Bertugas 4 hingga 8 jam: **1/2 Hari Cuti Gantian**\n"
            "• Bertugas melebihi 8 jam: **1 Hari Penuh Cuti Gantian**"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'ca_cuti':
        text = (
            "🏖️ *CA-7: KELAYAKAN CUTI BERGAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Cuti Tahunan (Art 44):* 18 hari (<2 thn), 22 hari (2-5 thn), 24 hari (>5 thn).\n"
            "📌 *Cuti Haji & Umrah (Art 55):* 54 hari bergaji penuh sekali sepanjang perkhidmatan.\n"
            "📌 *Cuti Bersalin (Art 49):* 98 hari bergaji penuh (sehingga 5 kelahiran).\n"
            "📌 *Cuti Paterniti (Art 52):* 7 hari berturut-turut (khidmat >1 thn) / 3 hari (<1 thn).\n"
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
            "• Bayaran tol, parkir & feri berasaskan resit.\n\n"
            "📌 *Artikel 64.1 (Elaun Makan Luar Stesen):*\n"
            "• RM115.00 sehari (>50km & >8 jam bertugas).\n\n"
            "📌 *Artikel 64.3 (Elaun Makan Gaji ≥ RM4k):*\n"
            "• Hari biasa: RM25 (2-5 jam) / RM50 (>5 jam)\n"
            "• Cuti/Rehat: RM25 atau 0.5 hari cuti / RM50 atau 1 hari cuti\n\n"
            "📌 *Artikel 57 & 71:*\n"
            "• Elaun Dobi: RM20.00 sehari (luar kawasan >3 hari)\n"
            "• Elaun Chargeman: *RM300.00 / bulan*"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_perubatan':
        text = (
            "🏥 *CA-7: RAWATAN PERUBATAN & HOSPITAL*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Pesakit Luar (Art 59):* Had RM3,500 setahun sekeluarga (termasuk RM1,000 gigi/cermin mata/rawatan berkala).\n"
            "📌 *Pesakit Dalam / Wad (Art 60):*\n"
            "• Sehingga 31 Disember 2026: Had RM35,000 setahun sekeluarga.\n"
            "• Mulai 1 Jan 2027 (Art 60.2A): Had *RM45,000 setahun bagi setiap individu* (Pekerja & setiap orang tanggungan yang layak). Kelayakan bilik wad: RM150 sehari."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_kebajikan':
        text = (
            "👨‍👩‍👧 *CA-7: KEBAJIKAN & SUMBANGAN BERAS*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Sumbangan Beras (Art 67):* 2 kampit (10kg) Beras Super Tempatan setiap bulan berterusan sehingga tamat perkhidmatan.\n"
            "📌 *Insurans Hayat GTL & GPA (Art 40):* Pampasan kematian/keilatan kekal sebanyak *36 bulan gaji pokok terakhir*."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gred':
        text = (
            "📊 *STRUKTUR TANGGA GAJI & GRED (LAMPIRAN I CA-7)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔧 *KATEGORI TEKNIKAL (GRED T):*\n"
            "• *T5(T):* RM3,000 - RM6,300\n"
            "  _Penyelia Kejuruteraan II, Penyelia Operasi II, Penyelia Makmal II_\n"
            "• *T4(T):* RM2,600 - RM5,200\n"
            "  _Penyelia Kejuruteraan I, Penyelia Operasi I, Penjaga Jentera II, Juru Dandang II, Penyelia Makmal I, Juruteknik III_\n"
            "• *T3(T):* RM2,100 - RM4,000\n"
            "  _Juruteknik II, Penjaga Jentera I, Juru Dandang I, Pembantu Makmal II_\n"
            "• *T2(T):* RM1,900 - RM3,200\n"
            "  _Juruteknik I, Pembantu Makmal I_\n"
            "• *T1(T):* RM1,700 - RM2,800\n"
            "  _Juruteknik Rendah_\n\n"
            "💼 *KATEGORI SOKONGAN / BUKAN TEKNIKAL (GRED S):*\n"
            "• *S5:* RM2,800 - RM5,400\n"
            "  _Penyelia II_\n"
            "• *S4:* RM2,400 - RM4,500\n"
            "  _Penyelia I, Pembantu Tadbir III_\n"
            "• *S3:* RM2,100 - RM3,600\n"
            "  _Pembantu Tadbir II, Pemandu II_\n"
            "• *S2:* RM1,900 - RM3,000\n"
            "  _Pembantu Tadbir I, Pemandu I, Operator Ladang_\n"
            "• *S1:* RM1,700 - RM2,800\n"
            "  _Operator Pengeluaran, Pembantu Tadbir Rendah_"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

# ==================== 3. MODUL KIRAAN OT & ELAUN ====================

async def handle_kiraan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🧮 *3. MODUL KIRAAN OT, ELAUN & MILEAGE*\n"
        "_(Selaras Artikel 31, 63 & 64.3 CA-7)_\n\n"
        "Sila pilih fungsi pengiraan rasmi:"
    )
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_kiraan_keyboard())

async def start_calc_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔧 Gred T (Teknikal)", callback_data='grade_t')],
        [InlineKeyboardButton("💼 Gred S (Gaji Bawah RM4,000)", callback_data='grade_s_under4k')],
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
            "💼 *KIRAAN CUTI GANTIAN (ARTIKEL 31.5)*\n"
            "_(Terpakai untuk Gred T & Gred S)_\n\n"
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
        "💼 *HASIL KELAYAKAN CUTI GANTIAN (GRED T & S)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ Jam Bertugas: {hours} Jam\n"
        f"🏖️ Cuti Gantian (Art 31.5): {cuti}\n"
        "📌 *Syarat CA-7:* Sah dikumpulkan dalam tempoh enam (6) bulan.\n\n"
        "🍱 *Bagi Staf Gaji RM4,000 ke atas (Artikel 64.3):*\n"
        "• Hari biasa: RM25 (2-5 jam) | RM50 (>5 jam)\n"
        "• Hari rehat/cuti am: Pilihan Cuti Gantian atau Tunai RM25 (4-8 jam) / RM50 (>8 jam)"
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
            [InlineKeyboardButton("Hari Biasa (Ahad-Khamis) [1.5x]", callback_data='day_normal')],
            [InlineKeyboardButton("Jumaat (Off Day) [1.5x]", callback_data='day_offday')],
            [InlineKeyboardButton("Sabtu (Rest Day) [2.0x]", callback_data='day_rest')],
            [InlineKeyboardButton("Cuti Umum [3.0x]", callback_data='day_ph')]
        ]
    elif choice == 'sch_zonb':
        context.user_data['normal_hours'] = 7.8
        context.user_data['zone_name'] = "Zon B"
        keyboard = [
            [InlineKeyboardButton("Hari Biasa (Isnin-Jumaat) [1.5x]", callback_data='day_normal')],
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
        "📊 *HASIL KIRAAN LEBIH MASA (ARTIKEL 31)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Jam kerja normal: {norm} jam\n"
        f"Jam OT: {hours} jam\n"
        f"Kadar Gaji Sejam (HRP): RM {hrp:.2f}\n"
        f"Kadar Pengganda: {rate}x\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Anggaran Bayaran Lebih Masa: RM {total:,.2f}*\n"
        "📌 *Rujukan:* Artikel 31 CA-7 BERNAS & Akta Kerja 1955\n\n"
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
    pengadu = update.effective_user
    
    tahun = datetime.now().year
    no_siri = random.randint(10, 99)
    tiket_no = f"KPPbNB-{tahun}-00{no_siri}"
    masa_lapor = datetime.now().strftime('%d/%m/%Y %H:%M')

    # 1. Hantar pengesahan kepada ahli
    res = (
        "✅ *LAPORAN BERJAYA DIHANTAR!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *No. Laporan:* `{tiket_no}`\n"
        f"📁 *Kategori:* {cat}\n"
        f"📅 *Tarikh:* {masa_lapor}\n"
        "Status: 🟡 *Menunggu Semakan AJK Kesatuan*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Notifikasi rasmi telah dihantar kepada Bendahari Kesatuan. Sila simpan No. Laporan untuk rujukan tatacara kilanan Artikel 15 CA-7."
    )
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())

    # 2. Hantar notifikasi terus ke Telegram En. Khairul Faiz (33746692)
    notis_admin = (
        "🚨 *NOTIFIKASI ADUAN BARU MASUK (KPPbNB)*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *No. Tiket:* `{tiket_no}`\n"
        f"👤 *Nama Pengadu:* {pengadu.full_name} (@{pengadu.username if pengadu.username else 'Tiada Username'})\n"
        f"🆔 *Telegram ID:* `{pengadu.id}`\n"
        f"📁 *Kategori:* {cat}\n"
        f"📅 *Masa:* {masa_lapor}\n\n"
        f"📝 *Butiran Aduan:*\n_{desc}_\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *Tindakan:* Sila rujuk Prosedur Kilanan Artikel 15 CA-7 untuk siasatan lanjut."
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=notis_admin,
            parse_mode='Markdown'
        )
    except Exception as err:
        logging.error(f"Gagal hantar notis ke admin ({ADMIN_CHAT_ID}): {err}")

    return ConversationHandler.END

# ==================== PENGESAN ID GROUP AUTOMATIK ====================

async def group_id_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Jika mesej datang dari mana-mana Group atau Supergroup
    if update.effective_chat and update.effective_chat.type in ['group', 'supergroup']:
        group_id = update.effective_chat.id
        group_title = update.effective_chat.title
        logging.info(f"==> GROUP DETECTED! Nama Group: '{group_title}', ID Group: {group_id}")
        
        # Hantar terus mesej ke telefon Faiz supaya tak payah cari-cari lagi
        try:
            await context.bot.send_message(
                chat_id="33746692",
                text=f"📢 *ID GROUP DIKESAN!*\n\nNama Group: *{group_title}*\nID Group: `{group_id}`\n\n_Salin nombor ID di atas untuk dimasukkan ke ADMIN_CHAT_ID!_",
                parse_mode='Markdown'
            )
        except Exception:
            pass

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
            "No 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah Darul Aman.\n\n"
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
        logging.warning(f"Markdown fallback: {parse_error}")
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
    app.add_handler(CallbackQueryHandler(handle_ca, pattern='^(menu_ca|ca_|art64_)'))
    app.add_handler(CallbackQueryHandler(handle_kiraan_menu, pattern='^menu_kiraan$'))
    app.add_handler(CallbackQueryHandler(handle_other_menus, pattern='^(menu_hebahan|menu_dokumen|menu_profil|menu_hubungi)$'))
    
    # Pengesan ID Group Automatik
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, group_id_tracker))
    
    # Pengendali chat peribadi AI
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

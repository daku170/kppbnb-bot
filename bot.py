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

Takrifan Jadual Hari Mengikut Zon di BERNAS (Artikel 29 & 64.3):
1. Zon A (Kedah, Kelantan, Terengganu, Johor):
   - Hari Bekerja Biasa: Ahad hingga Khamis (8.00 pagi - 5.00 ptg; Khamis hingga 4.00 ptg).
   - Off Day: Jumaat.
   - Rest Day: Sabtu.
2. Zon B (Pulau Pinang, Perak, Selangor, KL, Pahang, Melaka, N. Sembilan):
   - Hari Bekerja Biasa: Isnin hingga Jumaat (8.30 pagi - 5.30 ptg).
   - Off Day: Sabtu.
   - Rest Day: Ahad.
3. Pekerja Syif:
   - Hari Biasa, Off Day dan Rest Day ditentukan mengikut jadual giliran roaster rasmi kompleks.

Ketetapan Kerja Lebih Masa & Cuti Gantian (Artikel 29 & 31 CA-7):
- Waktu Bekerja (Art 29): 39 jam seminggu (bukan syif), 42 jam seminggu (syif).
- Kiraan Lebih Masa (Gred T & Gred S [Gaji Bawah RM4,000]):
  * Formula: (Gaji / 26) × Kadar × (Jam OT / Jam Kerja Normal)
  * Kadar: Hari Biasa & Off Day (1.5x), Rest Day (2.0x), Cuti Kelepasan Am (3.0x).
- Cuti Gantian (Artikel 31.5): Terpakai untuk Gred T dan Gred S sebagai ganti bayaran tunai.
  * 6 - 8 jam = 1 hari cuti gantian.
  * 4 - 5 jam = 1/2 hari cuti gantian.
  * Boleh dikumpul dalam tempoh 6 bulan pada tahun berkenaan.

Ketetapan Artikel 64.3 (Elaun Makan Lebih Masa Gaji ≥ RM4,000):
- Terpakai bagi staf bergaji RM4,000 ke atas yang tidak layak bayaran lebih masa.
- Hari Bekerja Biasa (Zon A: Ahad-Khamis | Zon B: Isnin-Jumaat):
  * 2 hingga 5 jam: RM25.00
  * Melebihi 5 jam: RM50.00
- Hari Rehat, Off Day & Cuti Am (Zon A: Jumaat & Sabtu | Zon B: Sabtu & Ahad | PH):
  * Pilihan: Cuti Gantian ATAU Elaun Makan.
  * 4 hingga 8 jam: RM25.00 atau 1/2 hari cuti gantian.
  * Melebihi 8 jam: RM50.00 atau 1 hari cuti gantian.

Struktur Gred & Tangga Gaji (Lampiran I):
- Gred T (Teknikal): T1 (RM1,700 - RM2,800) hingga T5 (RM3,000 - RM6,300).
- Gred S (Sokongan): S1 (RM1,700 - RM2,800) hingga S5 (RM2,800 - RM5,400).

Cuti & Faedah Lain:
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
- PENTING: Jika soalan yang dikemukakan di luar bidang maklumat di atas, terlampau khusus, atau anda tidak pasti jawapannya mengikut CA-7, jangan reka jawapan. Sila jawab dengan jelas: "Maaf, maklumat terperinci mengenai perkara ini tiada dalam rekod saya. Sila rujuk dengan Exco atau barisan pimpinan kesatuan untuk kepastian lanjut."
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
        [InlineKeyboardButton("📍 Panduan Zon A", callback_data='art64_zona'),
         InlineKeyboardButton("📍 Panduan Zon B", callback_data='art64_zonb')],
        [InlineKeyboardButton("🔄 Panduan Staf Syif", callback_data='art64_syif')],
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
        await update.callback_query.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# ==================== 1. MODUL AKTA & PERATURAN (LENGKAP) ====================

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
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

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
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

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
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

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
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_mc':
        text = (
            "🏥 *AKTA KERJA 1955: CUTI SAKIT & HOSPITAL (SEK 60F)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Pengasingan Kelayakan (Pindaan 2022):*\n"
            "• Cuti Sakit biasa tidak lagi menolak hak 60 hari cuti masuk wad.\n"
            "• Cuti Masuk Wad: Layak sehingga *60 hari setahun* dengan pengesahan doktor berdaftar.\n\n"
            "📌 *Syarat Pematuhan:*\n"
            "• Pekerja *wajib memaklumkan majikan dalam masa 48 jam* dari tarikh MC bermula."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_gaji':
        text = (
            "💰 *AKTA KERJA 1955: PEMBAYARAN & POTONGAN GAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 19 (Tempoh Bayaran):*\n"
            "• Gaji wajib dibayar tidak lewat daripada *hari ke-7* selepas tamat tempoh upah.\n\n"
            "📌 *Seksyen 24 (Had Potongan Gaji):*\n"
            "• Majikan dilarang membuat potongan sesuka hati kecuali caruman statutori atau yuran kesatuan dengan kebenaran."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_awol':
        text = (
            "⚠️ *AKTA KERJA 1955: KETIDAKHADIRAN (AWOL) & DISIPLIN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 15(2) (Pecah Kontrak):*\n"
            "• Pekerja disifatkan memungkiri kontrak jika tidak hadir bertugas *melebihi 2 hari berturut-turut* tanpa cuti awal dan tanpa alasan munasabah.\n\n"
            "📌 *Seksyen 14 (Siasatan Wajar / Due Inquiry):*\n"
            "• Majikan wajib adakan siasatan adil sebelum buang kerja."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_tamat':
        text = (
            "🚪 *AKTA KERJA 1955: PENAMATAN KERJA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Notis Penamatan (Seksyen 12):*\n"
            "• <2 tahun: 4 minggu | 2 - 5 tahun: 6 minggu | >5 tahun: 8 minggu\n\n"
            "📌 *Faedah Penamatan / Retrenchment (CA-7 Art 38):*\n"
            "• Mengikut formula tahun perkhidmatan dan prinsip keadilan industri (LIFO)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_osha':
        text = (
            "🦺 *OSHA 1994 (PINDAAN 2022): KESELAMATAN TEMPAT KERJA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Seksyen 26A (Hak Menolak Kerja Bahaya):*\n"
            "• Pekerja berhak mengasingkan diri (*remove himself*) dari kawasan kerja sekiranya ada bahaya maut atau kecederaan parah yang pasti berlaku (*imminent danger*)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

    elif data == 'akta_perkeso':
        text = (
            "🛡️ *AKTA KESELAMATAN SOSIAL PEKERJA 1969 (PERKESO)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Skim Bencana Pekerjaan:*\n"
            "• Meliputi kemalangan kerja dan *Kemalangan Perjalanan* pergi/balik ikut laluan biasa.\n"
            "• PERKESO membayar elaun ganti rugi harian sebanyak *80% purata gaji harian*."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_akta_keyboard())

# ==================== 2. MODUL CA-7 (LENGKAP) ====================

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
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gaji':
        text = (
            "💰 *CA-7: GAJI & KENAIKAN TAHUNAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Artikel 25 (Kenaikan Tahunan):* Memenuhi Jangkaan (3.5% + Merit), Di Bawah Jangkaan (2.0%). Berkuatkuasa setiap 1 Januari.\n"
            "📌 *Artikel 26 (Bonus Kontraktual):* 1 bulan gaji asas kepada staf tetap yang disahkan pada 31 Disember.\n"
            "📌 *Artikel 74 (Pelarasan Gaji):* Pelarasan 4.5% kepada semua ahli kesatuan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_waktu_kerja':
        text = (
            "⏰ *CA-7: WAKTU BEKERJA (ARTIKEL 29)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 *1. BUKAN SYIF (Purata 39 Jam Seminggu):*\n"
            "• Isnin - Jumaat: 8.30 pagi – 5.30 petang (Rehat 1 jam).\n"
            "• Zon A (Ahad - Khamis): 8.00 pagi – 5.00 ptg (Khamis hingga 4.00 ptg).\n\n"
            "🔄 *2. PEKERJA SYIF (Purata 42 Jam Seminggu):*\n"
            "• Sistem 2 Syif (12 jam) atau 3 Syif (8 jam) mengikut giliran roaster rasmi kompleks."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_ot':
        text = (
            "🧮 *CA-7: KERJA LEBIH MASA & CUTI GANTIAN (ART 30 & 31)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Kiraan Lebih Masa (Gred T & S Bawah RM4k):*\n"
            "• Formula: `(Gaji / 26) × Kadar × (Jam OT / Jam Kerja Normal)`\n"
            "• Hari Biasa / Off Day: 1.5x | Rest Day: 2.0x | Cuti Am: 3.0x\n\n"
            "📌 *Cuti Gantian (Art 31.5):*\n"
            "• 6 - 8 jam = 1 hari cuti gantian | 4 - 5 jam = 1/2 hari.\n"
            "*(Sah dikumpul dalam tempoh 6 bulan)*"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_elaun_4k_menu':
        text = (
            "🍱 *CA-7: ELAUN MAKAN LEBIH MASA GAJI ≥ RM4,000 (ARTIKEL 64.3)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Sila pilih zon anda untuk melihat ketetapan hari bekerja dan hari rehat:"
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'art64_zona':
        text = (
            "📍 *ARTIKEL 64.3: ZON A (Kedah, Kelantan, Trg, Johor)*\n"
            "• Hari Bekerja (Ahad-Khamis): 2-5 jam (RM25), >5 jam (RM50).\n"
            "• Jumaat, Sabtu & Cuti Am: Pilihan Elaun Tunai (RM25/RM50) ATAU Cuti Gantian (0.5 / 1 hari)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'art64_zonb':
        text = (
            "📍 *ARTIKEL 64.3: ZON B (P.Pinang, Perak, Selangor, KL, dll)*\n"
            "• Hari Bekerja (Isnin-Jumaat): 2-5 jam (RM25), >5 jam (RM50).\n"
            "• Sabtu, Ahad & Cuti Am: Pilihan Elaun Tunai (RM25/RM50) ATAU Cuti Gantian (0.5 / 1 hari)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'art64_syif':
        text = (
            "🔄 *ARTIKEL 64.3: PEKERJA SYIF*\n"
            "• Hari Syif Biasa: 2-5 jam (RM25), >5 jam (RM50).\n"
            "• Hari Off Day / Rest Day Syif & Cuti Am: Pilihan Elaun Tunai ATAU Cuti Gantian."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_elaun_4k_keyboard())

    elif data == 'ca_cuti':
        text = (
            "🏖️ *CA-7: KELAYAKAN CUTI BERGAJI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Cuti Tahunan (Art 44):* 18 hari (<2 thn), 22 hari (2-5 thn), 24 hari (>5 thn).\n"
            "📌 *Cuti Haji & Umrah (Art 55):* 54 hari bergaji penuh (sekali seumur hidup).\n"
            "📌 *Cuti Bersalin (Art 49):* 98 hari bergaji penuh.\n"
            "📌 *Cuti Paterniti (Art 52):* 7 hari (khidmat >1 thn) / 3 hari (<1 thn)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_elaun':
        text = (
            "🚗 *CA-7: ELAUN & PERBATUAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Perbatuan (Art 63):* Kereta RM0.75/km, Motor RM0.50/km.\n"
            "📌 *Elaun Makan Luar Stesen (Art 64.1):* RM115.00 sehari.\n"
            "📌 *Elaun Chargeman (Art 71):* RM300.00 sebulan."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_perubatan':
        text = (
            "🏥 *CA-7: RAWATAN PERUBATAN & HOSPITAL*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Pesakit Luar (Art 59):* Had RM3,500 setahun sekeluarga.\n"
            "📌 *Pesakit Dalam / Wad (Art 60.2A - Mulai 1 Jan 2027):* Had *RM45,000 setahun bagi setiap individu* (Pekerja & tanggungan). Kelayakan bilik wad: RM150 sehari."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_kebajikan':
        text = (
            "👨‍👩‍👧 *CA-7: KEBAJIKAN & SUMBANGAN BERAS*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Sumbangan Beras (Art 67):* 2 kampit (10kg) sebulan berterusan.\n"
            "📌 *Insurans GTL & GPA (Art 40):* Pampasan 36 bulan gaji pokok terakhir."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

    elif data == 'ca_gred':
        text = (
            "📊 *STRUKTUR TANGGA GAJI (LAMPIRAN I)*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔧 *Gred T (Teknikal):* T1 (RM1.7k-2.8k) hingga T5 (RM3.0k-6.3k).\n"
            "💼 *Gred S (Sokongan):* S1 (RM1.7k-2.8k) hingga S5 (RM2.8k-5.4k)."
        )
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_ca_keyboard())

# ==================== 3. MODUL KIRAAN ====================

async def handle_kiraan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🧮 *MODUL KIRAAN OT & ELAUN*\nSila pilih fungsi pengiraan rasmi:"
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_kiraan_keyboard())

async def start_calc_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📍 Zon A", callback_data='sch_zona'), InlineKeyboardButton("📍 Zon B", callback_data='sch_zonb')],
        [InlineKeyboardButton("🔄 Syif", callback_data='sch_syif')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_kiraan')]
    ]
    await query.message.reply_text("Sila pilih Zon / Jadual Kerja anda:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_SCHEDULE

async def calc_schedule_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data['normal_hours'] = 7.8 if choice != 'sch_syif' else 8.0
    keyboard = [
        [InlineKeyboardButton("Hari Biasa [1.5x]", callback_data='day_normal')],
        [InlineKeyboardButton("Hari Rehat / Off Day [1.5x / 2.0x]", callback_data='day_rest')],
        [InlineKeyboardButton("Cuti Umum [3.0x]", callback_data='day_ph')]
    ]
    await query.message.reply_text("Pilih Jenis Hari OT:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_DAY_TYPE

async def calc_day_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['day_type'] = query.data
    await query.message.reply_text("Sila taip Gaji Pokok Bulanan anda (contoh: 2400):")
    return STATE_SALARY

async def calc_salary_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['salary'] = float(update.message.text.strip().replace("RM", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("⚠️ Masukkan angka gaji yang sah:")
        return STATE_SALARY
    await update.message.reply_text("Sila taip Jumlah Jam OT (contoh: 4):")
    return STATE_HOURS

async def calc_hours_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Masukkan angka jam yang sah:")
        return STATE_HOURS

    sal = context.user_data['salary']
    norm = context.user_data['normal_hours']
    rate = 2.0 if 'rest' in context.user_data['day_type'] else (3.0 if 'ph' in context.user_data['day_type'] else 1.5)
    total = rate * (sal / 26.0 / norm) * hours

    res = f"📊 *HASIL KIRAAN OT*\nAnggaran Bayaran: *RM {total:,.2f}*\n*(Tertakluk kepada pengesahan perakam waktu)*"
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())
    return ConversationHandler.END

async def start_calc_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🚗 Kereta (RM0.75/km)", callback_data='mil_car')],
        [InlineKeyboardButton("🏍️ Motor (RM0.50/km)", callback_data='mil_motor')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_kiraan')]
    ]
    await query.message.reply_text("Pilih jenis kenderaan:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_MILEAGE_VEHICLE

async def calc_mileage_vehicle_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['veh_rate'] = 0.75 if query.data == 'mil_car' else 0.50
    await query.message.reply_text("Sila taip jumlah perbatuan dalam KM (contoh: 75):")
    return STATE_MILEAGE_KM

async def calc_mileage_km_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Masukkan angka KM yang sah:")
        return STATE_MILEAGE_KM
    total = km * context.user_data['veh_rate']
    res = f"🚗 *HASIL KIRAAN MILEAGE*\nJumlah Tuntutan: *RM {total:,.2f}*"
    await update.message.reply_text(res, parse_mode='Markdown', reply_markup=get_back_button())
    return ConversationHandler.END

# ==================== 4. MODUL ADUAN ====================

async def start_aduan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("💰 Isu Gaji", callback_data='aduan_gaji'), InlineKeyboardButton("⏰ Isu OT", callback_data='aduan_ot')],
        [InlineKeyboardButton("🏖️ Isu Cuti", callback_data='aduan_cuti'), InlineKeyboardButton("🚗 Isu Elaun", callback_data='aduan_elaun')],
        [InlineKeyboardButton("⚠️ Disiplin / Lain-lain", callback_data='aduan_lain')],
        [InlineKeyboardButton("🔙 Batal", callback_data='menu_utama')]
    ]
    await query.message.reply_text("📝 Pilih Kategori Aduan:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_ADUAN_CAT

async def aduan_cat_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['aduan_cat'] = query.data.replace('aduan_', '').upper()
    await query.message.reply_text("Sila taip penerangan ringkas aduan anda:")
    return STATE_ADUAN_DESC

async def aduan_desc_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    cat = context.user_data.get('aduan_cat', 'UMUM')
    user = update.effective_user
    tiket = f"KPPbNB-{datetime.now().year}-{random.randint(10,99)}"

    await update.message.reply_text(
        f"✅ *ADUAN DITERIMA*\nNo Tiket: `{tiket}`\n\nNotifikasi rasmi telah diterima, Exco Kesatuan akan hubungi anda semula terima kasih.",
        parse_mode='Markdown', reply_markup=get_back_button()
    )

    notis = f"🚨 *ADUAN BARU*\nTiket: `{tiket}`\nDari: {user.full_name} (@{user.username or 'Tiada'})\nKategori: {cat}\n\nButiran:\n_{desc}_"
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notis, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Gagal hantar ke group: {e}")

    return ConversationHandler.END

# ==================== 5. MODUL DOKUMEN & LAIN-LAIN ====================

async def handle_other_menus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_dokumen':
        text = "📚 *PUSAT DOKUMEN & MUAT TURUN KESATUAN*\nSila pilih dokumen atau borang yang ingin dimuat turun:"
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
        text = "📢 *HEBAHAN KESATUAN*\n• CA-7 berkuatkuasa 2026-2028.\n• Pastikan semakan yuran kesatuan teratur."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_profil':
        user = update.effective_user
        text = f"👤 *PROFIL AHLI*\nNama: {user.full_name}\nStatus: Aktif"
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())
    elif data == 'menu_hubungi':
        text = "☎️ *HUBUNGI KESATUAN*\nNo 2190 KM20 Jalan Kodiang, 06000 Jitra, Kedah."
        await query.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'):
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    loop = asyncio.get_running_loop()
    ai_raw = await loop.run_in_executor(None, query_groq_ai, update.message.text.strip())
    response = f"🤖 *JAWAPAN AI*\n\n{ai_raw.replace('**', '*')}\n\n💡 *Untuk tindakan rasmi, rujuk Exco.*"
    await update.message.reply_text(response, parse_mode='Markdown', reply_markup=get_back_button())

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# ==================== MAIN ====================

async def async_main():
    threading.Thread(target=run_web_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    kiraan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_calc_ot, pattern='^calc_start_ot$'), CallbackQueryHandler(start_calc_mileage, pattern='^calc_start_mileage$')],
        states={
            STATE_SCHEDULE: [CallbackQueryHandler(calc_schedule_selected, pattern='^sch_')],
            STATE_DAY_TYPE: [CallbackQueryHandler(calc_day_type_selected, pattern='^day_')],
            STATE_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_salary_received)],
            STATE_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_hours_received)],
            STATE_MILEAGE_VEHICLE: [CallbackQueryHandler(calc_mileage_vehicle_selected, pattern='^mil_')],
            STATE_MILEAGE_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_mileage_km_received)]
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
    app.add_handler(CallbackQueryHandler(handle_other_menus, pattern='^menu_(dokumen|hebahan|profil|hubungi)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat))

    async with app:
        await app.start()
        await app.updater.start_polling()
        print("Bot KPPbNB LIVE!")
        while True:
            await asyncio.sleep(3600)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()

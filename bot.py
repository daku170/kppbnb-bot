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

    app.add_handler(verify_conv)
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

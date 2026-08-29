import os
import asyncio
import threading
import http.server
import socketserver
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8938997589:AAHac3AbBUvhxTBTq6nj8UQkV-2K2MUB-qc"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

def get_main_keyboard():
    keyboard = [
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

def get_back_to_ca_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Senarai CA", callback_data='menu_ca')],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Menu Utama", callback_data='menu_utama')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🌾 *SELAMAT DATANG KE BOT RASMI KPPbNB*\n"
        "_Kesatuan Pekerja-pekerja Padiberas Nasional Berhad (BERNAS) Semenanjung Malaysia_\n\n"
        "Sila pilih menu di bawah untuk semakan maklumat, hak pekerja, kebajikan dan aduan:"
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_utama':
        await start(update, context)

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
            "📌 *Formula Bayaran OT (Artikel 31):*\n"
            "• *(Gaji Bulanan / 26) × 1.5 × (Jam OT / Jam Kerja Biasa)*\n"
            "• Had maksimum OT sebulan: *104 jam* (tidak termasuk OT hari rehat/cuti am).\n\n"
            "📌 *Cuti Gantian Lebih Masa (Artikel 31.5):*\n"
            "• 6 - 8 jam kerja OT = *1 hari cuti gantian*\n"
            "• ≤ 4 - 5 jam kerja OT = *1/2 hari cuti gantian*\n"
            "• Boleh dikumpul dan diguna dalam tempoh 6 bulan."
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
            "📌 *Tugas Luar Kawasan (Outstation):*\n"
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

    elif data == 'menu_akta':
        text = (
            "⚖️ *AKTA KERJA 1955 & PERATURAN PERHUBUNGAN PERUSAHAAN*\n\n"
            "📌 *Akta Kerja 1955 (Pindaan 2022):*\n"
            "• Waktu kerja mingguan maksimum: *45 jam*.\n"
            "• Seksyen 60A: Had bayaran kerja lebih masa (OT).\n"
            "• Seksyen 15(2): Ketidakhadiran berterusan > 2 hari tanpa cuti/alasan munasabah adalah pecah kontrak (AWOL).\n\n"
            "📌 *Akta Kesatuan Sekerja 1959 & APP 1967:*\n"
            "• Perlindungan hak pekerja menyertai aktiviti kesatuan sekerja tanpa diskriminasi majikan.\n"
            "• Hak perundingan kolektif (Collective Bargaining) di bawah pengiktirafan rasmi."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_main_keyboard())

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

    elif data == 'menu_info':
        text = (
            "📢 *INFO TERKINI & MAKLUMAN KESATUAN*\n\n"
            "• 📌 Pelaksanaan Perjanjian Bersama Ke-7 (CA-7) berkuatkuasa *1 Jan 2026 - 31 Dis 2028*.\n"
            "• 📌 Pastikan caruman yuran bulanan kesatuan dipotong secara tepat melalui slip gaji.\n"
            "• 📌 Makluman tarikh Mesyuarat Agung Dwi-Tahunan (AGM) akan dipaparkan di Papan Kenyataan Kesatuan di setiap Kompleks/Gudang BERNAS.\n\n"
            "_Sentiasa bersatu demi kebajikan dan keharmonian warga kerja BERNAS!_"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_to_main_keyboard())

async def async_main():
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Bot KPPbNB sedang dijalankan...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
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

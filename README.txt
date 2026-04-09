============================================================
   README — AL DRIP STORE | BOT RAMASHOP QRIS
============================================================

INSTALL LIBRARY (Terminal Pydroid 3)
──────────────────────────────────────
pip install pyTelegramBotAPI requests


STRUKTUR FILE
──────────────────────────────────────
bot_negro/
├── config.py     ← ⚙️  ISI INI DULU sebelum jalankan
├── database.py   ← 🗄️  SQLite (otomatis dibuat)
├── ramashop.py   ← 💳  Integrasi Ramashop API
├── bot.py        ← 🤖  File utama — jalankan ini
└── store.db      ← 📦  Database (dibuat otomatis)


SETUP (Urutan Wajib)
──────────────────────────────────────
1. Buka config.py, isi:

   BOT_TOKEN       = "xxx"   ← dari @BotFather
   ADMIN_ID        = 123456  ← dari @userinfobot
   ADMIN_USERNAME  = "nama"  ← username kamu (tanpa @)
   CHANNEL_LINK    = "https://t.me/..."
   RAMASHOP_API_KEY = "rg_xxx..."  ← dari dashboard ramashop

   ⚠️ Setelah screenshot tadi, REGENERATE API KEY di ramashop!

2. Simpan semua file ke satu folder di HP:
   /storage/emulated/0/Download/bot_negro/

3. Buka Pydroid 3 → install library:
   Pip → ketik "pyTelegramBotAPI" → Install
   Pip → ketik "requests" → Install

4. Buka bot.py di Pydroid → klik ▶ Run


PERINTAH ADMIN (Chat di Telegram)
──────────────────────────────────────
/addkey NEG_1D  KEY-001,KEY-002,KEY-003
/addkey NEG_7D  WEEK-001,WEEK-002
/addkey NEG_30D MONTH-001

/stok    → Lihat jumlah stok semua produk
/saldo   → Cek saldo Ramashop kamu


PRODUCT ID
──────────────────────────────────────
NEG_1D  → NEGRO PREMIUM 1 Hari  (Rp 5.000)
NEG_7D  → NEGRO PREMIUM 7 Hari  (Rp 25.000)
NEG_30D → NEGRO PREMIUM 30 Hari (Rp 75.000)

Ganti harga di config.py sesuai keinginan!


ALUR PEMBELIAN OTOMATIS
──────────────────────────────────────
User klik NEGRO PREMIUM
  → Pilih durasi
  → Bot buat QRIS via Ramashop API
  → Invoice + gambar QR dikirim ke user
  → User scan QRIS, bayar TEPAT nominal yang tertera
    (ada kode unik, misal Rp 10.073 bukan Rp 10.000)
  → Bot polling cek status tiap 15 detik
  → Status SUCCESS → key otomatis terkirim ✅
  → Admin dapat notif masuk 🔔


KEUNGGULAN vs Tripay
──────────────────────────────────────
✅ Tanpa KTP / verifikasi perusahaan
✅ Tanpa webhook — tidak perlu ngrok / server
✅ Pure polling — cocok untuk Pydroid 3 di HP
✅ Langsung aktif setelah daftar


CATATAN
──────────────────────────────────────
- Bot jalan selama Pydroid 3 aktif & HP tidak sleep
- Saldo Ramashop harus cukup untuk memproses deposit
- User harus bayar TEPAT nominal (termasuk kode unik)
  agar sistem Ramashop bisa mencocokkan transaksi
- Cache Ramashop ±5 detik, jangan polling < 10 detik


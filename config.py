# ============================================================
#   CONFIG.PY — AL DRIP STORE
#   Ganti semua nilai sebelum menjalankan bot!
# ============================================================

# ── TELEGRAM ─────────────────────────────────────────────────
BOT_TOKEN       = "8606886906:AAGMI8mBn5ZE7QIjtdPQGRqLjHwPr9qO8nw"        # Dari @BotFather
ADMIN_ID        = 8672508764     # ID Telegram kamu (cek @userinfobot)
ADMIN_USERNAME  = "aldripclient" # Tanpa @
CHANNEL_LINK    = "https://t.me/assistantreseller"
CHANNEL_ID      = "@assistantreseller"  # ← Username channel (dengan @) atau ID angka channel

# ── RAMASHOP ─────────────────────────────────────────────────
RAMASHOP_API_KEY = "rg_ccf88c8cd8d5d1e17f68d10fde8210"  # Dari dashboard ramashop.my.id
RAMASHOP_BASE    = "https://ramashop.my.id/api/public"

# ════════════════════════════════════════════════════════════
#   LINK APK / FILE — UPDATE DI SINI SETIAP ADA VERSI BARU
# ════════════════════════════════════════════════════════════
RW_APK_LINK    = "https://linkmu.com/room-wangi-apk"   # ← GANTI LINK APK ROOM WANGI
RW_APK_VERSI   = "v1.0"                                # ← GANTI VERSI (contoh: v1.1, v2.0)
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
#   GAMBAR PRODUK — GANTI LINK DI BAWAH DENGAN GAMBAR KAMU
#
#   Cara upload gambar:
#   1. Kirim gambar ke bot kamu di Telegram
#   2. Forward pesan gambar itu ke @getidsbot
#   3. Copy "File ID" yang diberikan @getidsbot
#   4. Tempel File ID di bawah (lebih stabil dari link biasa)
#
#   Atau bisa juga pakai link gambar langsung:
#   Contoh: "https://i.imgur.com/contoh.jpg"
# ════════════════════════════════════════════════════════════

GAMBAR_NECRO  = "https://i.imgur.com/GANTI_INI.jpg"   # ← GANTI GAMBAR NECRO
GAMBAR_DRIP   = "https://i.imgur.com/GANTI_INI.jpg"   # ← GANTI GAMBAR DRIP CLIENT
GAMBAR_RW     = "https://i.imgur.com/GANTI_INI.jpg"   # ← GANTI GAMBAR ROOM WANGI

# ════════════════════════════════════════════════════════════

# ── PRODUK ───────────────────────────────────────────────────
PRODUCTS = {
    # ── NECRO ──────────────────────────────────────────────
    "NECRO_1D": {
        "nama"  : "NECRO",
        "durasi": "1 Hari",
        "harga" : 20000,
        "emoji" : "💀"
    },
    "NECRO_2D": {
        "nama"  : "NECRO",
        "durasi": "2 Hari",
        "harga" : 30000,
        "emoji" : "💀"
    },
    "NECRO_3D": {
        "nama"  : "NECRO",
        "durasi": "3 Hari",
        "harga" : 40000,
        "emoji" : "💀"
    },
    "NECRO_7D": {
        "nama"  : "NECRO",
        "durasi": "7 Hari",
        "harga" : 60000,
        "emoji" : "💀"
    },
    "NECRO_30D": {
        "nama"  : "NECRO",
        "durasi": "30 Hari",
        "harga" : 140000,
        "emoji" : "💀"
    },

    # ── DRIP CLIENT ────────────────────────────────────────
    "DRIP_1D": {
        "nama"  : "DRIP CLIENT",
        "durasi": "1 Hari",
        "harga" : 20000,
        "emoji" : "💧"
    },
    "DRIP_3D": {
        "nama"  : "DRIP CLIENT",
        "durasi": "3 Hari",
        "harga" : 30000,
        "emoji" : "💧"
    },
    "DRIP_7D": {
        "nama"  : "DRIP CLIENT",
        "durasi": "7 Hari",
        "harga" : 60000,
        "emoji" : "💧"
    },
    "DRIP_15D": {
        "nama"  : "DRIP CLIENT",
        "durasi": "15 Hari",
        "harga" : 100000,
        "emoji" : "💧"
    },
    "DRIP_30D": {
        "nama"  : "DRIP CLIENT",
        "durasi": "30 Hari",
        "harga" : 140000,
        "emoji" : "💧"
    },

    # ── ROOM WANGI (RW) ────────────────────────────────────
    "RW_7D": {
        "nama"  : "ROOM WANGI",
        "durasi": "7 Hari",
        "harga" : 50000,
        "emoji" : "🌸"
    },
}

# Interval polling cek pembayaran (detik)
CHECK_INTERVAL = 15

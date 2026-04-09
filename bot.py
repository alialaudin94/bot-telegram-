# ============================================================
#   BOT.PY — AL DRIP STORE | NEGRO PREMIUM BOT
#   Payment : Ramashop QRIS (ramashop.my.id)
#   Database: SQLite
#   Library : pyTelegramBotAPI
# ============================================================

import telebot
import threading
import time

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config   import (BOT_TOKEN, ADMIN_ID, ADMIN_USERNAME,
                      CHANNEL_LINK, CHANNEL_ID, PRODUCTS, CHECK_INTERVAL,
                      RW_APK_LINK, RW_APK_VERSI,
                      GAMBAR_NECRO, GAMBAR_DRIP, GAMBAR_RW)
from database import (init_db, add_stock, get_stock_count, get_stock_sold,
                      set_stock_tersedia, set_stock_terjual, take_stock,
                      create_transaction, set_message_id, get_pending,
                      get_transaction, mark_paid, mark_expired,
                      get_total_transaksi)
from ramashop import create_deposit, check_status, get_balance

# ── Init ──────────────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
init_db()

# ── Session rahasia — user yang sudah unlock ──────────────────
_unlocked_users: set = set()


# ═════════════════════════════════════════════════════════════
#   HELPER
# ═════════════════════════════════════════════════════════════

def rp(amount: int) -> str:
    """Format angka ke Rupiah."""
    return f"Rp {amount:,}".replace(",", ".")


def notif_channel(product: dict, trx: dict, username: str):
    """Kirim notifikasi pembelian baru ke channel."""
    from datetime import datetime
    import pytz

    try:
        wib  = pytz.timezone("Asia/Jakarta")
        now  = datetime.now(wib).strftime("%d/%m/%Y, %H.%M.%S")
    except Exception:
        now  = trx.get("paid_at", "-")

    total = get_total_transaksi()
    buyer = f"@{username}" if username else "(tanpa username)"

    try:
        bot.send_message(
            CHANNEL_ID,
            f"🛒 <b>PEMBELIAN BARU!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Status  : <b>PAID REALTIME</b>\n"
            f"🕐 WIB     : {now}\n"
            f"👤 Buyer   : <b>{buyer}</b>\n"
            f"📦 Paket   : {product['nama']} {product['durasi']}\n"
            f"💰 Harga   : {rp(trx['amount'])}\n"
            f"🔖 TRX     : <code>{trx['deposit_id']}</code>\n"
            f"📊 Total TRX: <b>{total}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[CHANNEL NOTIF ERROR] {e}")


# ── Keyboard ─────────────────────────────────────────────────

def kb_main() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("💀 NECRO",       callback_data="catalog:NECRO"))
    kb.row(InlineKeyboardButton("💧 DRIP CLIENT", callback_data="catalog:DRIP"))
    kb.row(InlineKeyboardButton("🌸 ROOM WANGI",  callback_data="catalog:RW"))
    kb.row(
        InlineKeyboardButton("📞 HUBUNGI ADMIN", url=f"https://t.me/{ADMIN_USERNAME}"),
        InlineKeyboardButton("🔄 MUAT ULANG",    callback_data="start"),
    )
    kb.row(InlineKeyboardButton("📢 CHANNEL", url=CHANNEL_LINK))
    return kb


def kb_catalog(prefix: str = "") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for pid, p in PRODUCTS.items():
        if prefix and not pid.startswith(prefix):
            continue
        # Tombol hanya nama + durasi (info stok sudah ada di teks pesan)
        label = f"{p['emoji']} {p['durasi']} Key 🔑"
        kb.row(InlineKeyboardButton(label, callback_data=f"buy:{pid}"))
    kb.row(InlineKeyboardButton("🔙 Kembali", callback_data="start"))
    return kb


def teks_catalog(prefix: str = "") -> str:
    """Buat teks daftar produk bergaya Evil King Store."""
    lines = ["— { 📦 LIST PRODUK 📦 } —\n"]
    for pid, p in PRODUCTS.items():
        if prefix and not pid.startswith(prefix):
            continue
        if pid.startswith("RW_"):
            lines.append(
                f"— {{ {p['emoji']} {p['nama']} {p['durasi']} }} —\n"
                f"  • 💰 Harga          : <b>{rp(p['harga'])}</b>\n"
                f"  • 📦 Stok Tersedia : <b>∞ (APK)</b>\n"
                "────────────────────────"
            )
        else:
            tersedia = get_stock_count(pid)
            terjual  = get_stock_sold(pid)
            stok_label = f"<b>{tersedia}</b>" if tersedia > 0 else "<b>⚠️ HABIS</b>"
            lines.append(
                f"— {{ {p['emoji']} {p['durasi']} Key 🔑 }} —\n"
                f"  • 💰 Harga          : <b>{rp(p['harga'])}</b>\n"
                f"  • 📦 Stok Tersedia : {stok_label}\n"
                f"  • ⚡ Stok Terjual   : <b>{terjual}</b>\n"
                "────────────────────────"
            )
    return "\n".join(lines)


def kb_back() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("🏠 Menu Utama", callback_data="start"))
    return kb


# ── Teks ─────────────────────────────────────────────────────

WELCOME = (
    "╔═══════════════════════╗\n"
    "║  🖤  <b>AL DRIP STORE</b>   🖤  ║\n"
    "╚═══════════════════════╝\n\n"
    "Selamat datang! Pilih menu di bawah.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    "💀 Produk  : <b>NECRO</b>\n"
    "💧 Produk  : <b>DRIP CLIENT</b>\n"
    "🌸 Produk  : <b>ROOM WANGI</b>\n"
    "⚡ Delivery: <b>Otomatis</b>\n"
    "💳 Payment : <b>QRIS (scan semua app)</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━━"
)


def teks_invoice(trx: dict, status_label: str, product: dict) -> str:
    icons = {"PENDING": "⏳", "PAID": "✅", "EXPIRED": "❌"}
    icon  = icons.get(trx["status"], "❓")
    unique = trx["total_amount"] - trx["amount"]
    return (
        "┌──────────────────────┐\n"
        "│  🧾  <b>INVOICE PEMBAYARAN</b>  │\n"
        "└──────────────────────┘\n\n"
        f"📦 <b>Produk</b>    : {product['nama']} {product['durasi']}\n"
        f"💰 <b>Harga</b>     : {rp(trx['amount'])}\n"
        f"🔢 <b>Kode Unik</b> : +{unique} (sudah termasuk)\n"
        f"💳 <b>Bayar</b>     : <b>{rp(trx['total_amount'])}</b>\n"
        f"🔖 <b>Deposit ID</b>: <code>{trx['deposit_id']}</code>\n"
        f"📅 <b>Dibuat</b>    : {trx['created_at']}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Status : {icon} <b>{status_label}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📌 <i>Scan QRIS di bawah. Bot cek otomatis tiap 15 detik.</i>"
    )


# ═════════════════════════════════════════════════════════════
#   COMMAND: /start
# ═════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(msg.chat.id, WELCOME, reply_markup=kb_main())


# ═════════════════════════════════════════════════════════════
#   PERINTAH RAHASIA — KATA KUNCI UNLOCK
# ═════════════════════════════════════════════════════════════

@bot.message_handler(commands=["aligasukacewekfrendly"])
def cmd_unlock(msg):
    """Kata kunci rahasia untuk masuk mode admin tersembunyi."""
    uid = msg.from_user.id
    if uid != ADMIN_ID:
        return  # diam saja, tidak kasih tahu
    _unlocked_users.add(uid)
    daftar_pid = "\n".join(f"  • <code>{pid}</code>" for pid in PRODUCTS)
    bot.reply_to(
        msg,
        "🔓 <b>MODE RAHASIA AKTIF</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Perintah tersedia:\n\n"
        "1️⃣ <b>Set stok + terjual sekaligus:</b>\n"
        "   <code>/set PRODUCT_ID tersedia terjual</code>\n"
        "   Contoh: <code>/set NECRO_7D 10 99</code>\n\n"
        "2️⃣ <b>Set tersedia saja:</b>\n"
        "   <code>/setstok PRODUCT_ID jumlah</code>\n"
        "   Contoh: <code>/setstok NECRO_1D 5</code>\n\n"
        "3️⃣ <b>Set terjual saja:</b>\n"
        "   <code>/setterjual PRODUCT_ID jumlah</code>\n"
        "   Contoh: <code>/setterjual NECRO_1D 24</code>\n\n"
        "4️⃣ <b>Tambah produk sementara:</b>\n"
        "   <code>/addproduk ID NAMA DURASI HARGA EMOJI</code>\n"
        "   Contoh: <code>/addproduk NECRO_3D NECRO 3 Hari 40000 💀</code>\n\n"
        "5️⃣ <b>Cek semua stok:</b>\n"
        "   <code>/cekstok</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>Product ID tersedia:</b>\n"
        f"{daftar_pid}\n\n"
        "⚠️ <i>Sesi aktif sampai bot restart.</i>"
    )


@bot.message_handler(commands=["set"])
def cmd_set_both(msg):
    """Set tersedia DAN terjual sekaligus. Format: /set PRODUCT_ID tersedia terjual"""
    uid = msg.from_user.id
    if uid != ADMIN_ID:
        return  # diam saja, tidak kasih tahu

    parts = msg.text.split()
    if len(parts) < 4:
        return bot.reply_to(
            msg,
            "⚠️ Format salah!\n\n"
            "Gunakan: <code>/set PRODUCT_ID tersedia terjual</code>\n"
            "Contoh : <code>/set NECRO_7D 10 99</code>"
        )

    pid = parts[1].upper()
    if pid not in PRODUCTS:
        return bot.reply_to(
            msg,
            f"⚠️ Product ID <b>{pid}</b> tidak ditemukan.\n\n"
            "Product ID tersedia:\n" +
            "\n".join(f"• <code>{p}</code>" for p in PRODUCTS)
        )

    if not parts[2].isdigit() or not parts[3].isdigit():
        return bot.reply_to(msg, "⚠️ Angka tersedia dan terjual harus berupa angka bulat.")

    jml_tersedia = int(parts[2])
    jml_terjual  = int(parts[3])

    set_stock_tersedia(pid, jml_tersedia)
    set_stock_terjual(pid, jml_terjual)

    tersedia = get_stock_count(pid)
    terjual  = get_stock_sold(pid)
    p        = PRODUCTS[pid]

    bot.reply_to(
        msg,
        f"✅ <b>Stok berhasil diupdate!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Produk   : {p['emoji']} {p['nama']} {p['durasi']}\n"
        f"📦 Tersedia : <b>{tersedia}</b>\n"
        f"⚡ Terjual  : <b>{terjual}</b>"
    )


@bot.message_handler(commands=["cekstok"])
def cmd_cekstok_rahasia(msg):
    """Cek semua stok — khusus admin."""
    uid = msg.from_user.id
    if uid != ADMIN_ID:
        return

    lines = ["📦 <b>Stok Semua Produk:</b>\n"]
    for pid, p in PRODUCTS.items():
        if pid.startswith("RW_"):
            lines.append(f"• {p['emoji']} {p['nama']} {p['durasi']} : <b>APK</b>")
        else:
            tersedia = get_stock_count(pid)
            terjual  = get_stock_sold(pid)
            status   = "⚠️ HABIS" if tersedia == 0 else f"<b>{tersedia}</b>"
            lines.append(
                f"• {p['emoji']} {p['nama']} {p['durasi']}\n"
                f"   📦 Tersedia : {status}\n"
                f"   ⚡ Terjual  : <b>{terjual}</b>"
            )
    bot.reply_to(msg, "\n".join(lines))


@bot.message_handler(commands=["addproduk"])
def cmd_addproduk(msg):
    """
    Tambah produk baru sementara (sampai bot restart).
    Format: /addproduk PRODUCT_ID NAMA DURASI HARGA EMOJI
    Contoh: /addproduk NECRO_15D NECRO 15 Hari 80000 💀
    """
    uid = msg.from_user.id
    if uid != ADMIN_ID:
        return

    # Split teks setelah perintah
    parts = msg.text.split(maxsplit=5)
    if len(parts) < 6:
        return bot.reply_to(
            msg,
            "⚠️ Format salah!\n\n"
            "Gunakan: <code>/addproduk PRODUCT_ID NAMA DURASI HARGA EMOJI</code>\n\n"
            "Contoh:\n"
            "<code>/addproduk NECRO_15D NECRO 15 Hari 80000 💀</code>\n\n"
            "⚠️ DURASI ditulis dengan spasi (misal: <code>15 Hari</code>), "
            "jadi NAMA harus 1 kata."
        )

    pid    = parts[1].upper()
    nama   = parts[2]
    # parts[3] = "15", parts[4] = "Hari", parts[5] = emoji
    # Tapi karena split(maxsplit=5), parts[3..5] perlu diurai lagi
    sisa   = parts[3:]  # contoh: ["15", "Hari", "80000", "💀"]
    if len(sisa) < 3:
        return bot.reply_to(msg, "⚠️ Kurang lengkap. Pastikan: DURASI HARGA EMOJI")

    # Cari harga (angka) dari belakang sisa[:-1]
    emoji  = sisa[-1]
    harga_str = sisa[-2]
    durasi = " ".join(sisa[:-2])

    if not harga_str.isdigit():
        return bot.reply_to(msg, f"⚠️ Harga harus angka, dapat: <code>{harga_str}</code>")

    harga = int(harga_str)

    if pid in PRODUCTS:
        return bot.reply_to(msg, f"⚠️ Product ID <code>{pid}</code> sudah ada!")

    # Tambah ke PRODUCTS (sementara, sampai bot restart)
    PRODUCTS[pid] = {
        "nama"  : nama,
        "durasi": durasi,
        "harga" : harga,
        "emoji" : emoji
    }

    bot.reply_to(
        msg,
        f"✅ <b>Produk berhasil ditambahkan!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID     : <code>{pid}</code>\n"
        f"📦 Nama   : {emoji} {nama}\n"
        f"⏱ Durasi : {durasi}\n"
        f"💰 Harga  : {rp(harga)}\n\n"
        f"⚠️ <i>Produk ini aktif sampai bot direstart.\n"
        f"Untuk permanen, tambahkan manual di config.py</i>"
    )

@bot.message_handler(commands=["addkey"])
def cmd_addkey(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⛔ Bukan admin.")
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        return bot.reply_to(
            msg,
            "Format: <code>/addkey PRODUCT_ID key1,key2,...</code>\n\n"
            "Product ID tersedia:\n" +
            "\n".join(f"• <code>{pid}</code>" for pid in PRODUCTS)
        )
    pid = parts[1].upper()
    if pid not in PRODUCTS:
        return bot.reply_to(msg, f"⚠️ Product ID tidak valid.")
    keys  = parts[2].split(",")
    added = add_stock(pid, keys)
    total = get_stock_count(pid)
    bot.reply_to(
        msg,
        f"✅ Tambah <b>{added}</b> key ke <b>{pid}</b>\n"
        f"📦 Stok sekarang: <b>{total}</b>"
    )


@bot.message_handler(commands=["stok"])
def cmd_stok(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    lines = ["📦 <b>Stok Semua Produk:</b>\n"]
    for pid, p in PRODUCTS.items():
        if pid.startswith("RW_"):
            lines.append(f"• {p['emoji']} {p['nama']} {p['durasi']} : <b>APK (tidak pakai key)</b>")
        else:
            tersedia = get_stock_count(pid)
            terjual  = get_stock_sold(pid)
            status   = "⚠️ HABIS" if tersedia == 0 else f"<b>{tersedia}</b>"
            lines.append(
                f"• {p['emoji']} {p['nama']} {p['durasi']}\n"
                f"   📦 Tersedia : {status}\n"
                f"   ⚡ Terjual  : <b>{terjual}</b>"
            )
    bot.reply_to(msg, "\n".join(lines))


@bot.message_handler(commands=["setstok"])
def cmd_setstok(msg):
    if msg.from_user.id != ADMIN_ID:
        return  # diam saja

    parts = msg.text.split()
    if len(parts) < 3:
        daftar = "\n".join(f"• <code>{pid}</code>" for pid in PRODUCTS if not pid.startswith("RW_"))
        return bot.reply_to(
            msg,
            "📝 <b>Format:</b> <code>/setstok PRODUCT_ID jumlah</code>\n\n"
            "Contoh: <code>/setstok NECRO_7D 10</code>\n\n"
            "Product ID tersedia:\n" + daftar
        )

    pid    = parts[1].upper()
    if pid not in PRODUCTS or pid.startswith("RW_"):
        return bot.reply_to(msg, "⚠️ Product ID tidak valid atau produk ini tidak pakai stok key.")

    if not parts[2].isdigit():
        return bot.reply_to(msg, "⚠️ Jumlah harus angka. Contoh: <code>/setstok NECRO_7D 10</code>")

    jumlah = int(parts[2])
    set_stock_tersedia(pid, jumlah)

    tersedia = get_stock_count(pid)
    terjual  = get_stock_sold(pid)
    bot.reply_to(
        msg,
        f"✅ Stok <b>{pid}</b> berhasil diubah!\n\n"
        f"📦 Tersedia : <b>{tersedia}</b>\n"
        f"⚡ Terjual  : <b>{terjual}</b>"
    )


@bot.message_handler(commands=["setterjual"])
def cmd_setterjual(msg):
    if msg.from_user.id != ADMIN_ID:
        return  # diam saja

    parts = msg.text.split()
    if len(parts) < 3:
        daftar = "\n".join(f"• <code>{pid}</code>" for pid in PRODUCTS if not pid.startswith("RW_"))
        return bot.reply_to(
            msg,
            "📝 <b>Format:</b> <code>/setterjual PRODUCT_ID jumlah</code>\n\n"
            "Contoh: <code>/setterjual NECRO_7D 5</code>\n\n"
            "Product ID tersedia:\n" + daftar
        )

    pid = parts[1].upper()
    if pid not in PRODUCTS or pid.startswith("RW_"):
        return bot.reply_to(msg, "⚠️ Product ID tidak valid atau produk ini tidak pakai stok key.")

    if not parts[2].isdigit():
        return bot.reply_to(msg, "⚠️ Jumlah harus angka. Contoh: <code>/setterjual NECRO_7D 5</code>")

    jumlah = int(parts[2])
    set_stock_terjual(pid, jumlah)

    tersedia = get_stock_count(pid)
    terjual  = get_stock_sold(pid)
    bot.reply_to(
        msg,
        f"✅ Stok terjual <b>{pid}</b> berhasil diubah!\n\n"
        f"📦 Tersedia : <b>{tersedia}</b>\n"
        f"⚡ Terjual  : <b>{terjual}</b>"
    )


@bot.message_handler(commands=["saldo"])
def cmd_saldo(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    res = get_balance()
    if res["success"]:
        bot.reply_to(msg, f"💰 Saldo Ramashop: <b>{rp(res['balance'])}</b>")
    else:
        bot.reply_to(msg, f"❌ Gagal cek saldo: {res['error']}")


@bot.message_handler(commands=["testgambar"])
def cmd_testgambar(msg):
    """Test kirim semua gambar produk. Khusus admin."""
    if msg.from_user.id != ADMIN_ID:
        return
    gambar_list = [
        ("NECRO",       GAMBAR_NECRO),
        ("DRIP CLIENT", GAMBAR_DRIP),
        ("ROOM WANGI",  GAMBAR_RW),
    ]
    bot.reply_to(msg, "🔍 Testing semua gambar produk...")
    for nama, link in gambar_list:
        try:
            bot.send_photo(
                msg.chat.id,
                photo=link,
                caption=f"✅ <b>{nama}</b>\n<code>{link[:60]}...</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            bot.send_message(
                msg.chat.id,
                f"❌ <b>{nama}</b> GAGAL!\n"
                f"Link: <code>{link}</code>\n"
                f"Error: <code>{e}</code>",
                parse_mode="HTML"
            )


# ═════════════════════════════════════════════════════════════
#   CALLBACK HANDLER
# ═════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    data    = call.data
    chat_id = call.message.chat.id
    msg_id  = call.message.message_id

    if data == "start":
        try:
            bot.edit_message_text(WELCOME, chat_id, msg_id, reply_markup=kb_main())
        except Exception:
            bot.send_message(chat_id, WELCOME, reply_markup=kb_main())
        bot.answer_callback_query(call.id)

    elif data.startswith("catalog"):
        # data bisa "catalog:NECRO", "catalog:DRIP", "catalog:RW"
        parts  = data.split(":", 1)
        prefix = parts[1] if len(parts) > 1 else ""
        catalog_text = teks_catalog(prefix)
        bot.edit_message_text(
            catalog_text,
            chat_id, msg_id,
            reply_markup=kb_catalog(prefix)
        )
        bot.answer_callback_query(call.id)

    elif data.startswith("buy:"):
        pid = data.split(":", 1)[1]
        _process_purchase(call, pid)
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id)


def _process_purchase(call, product_id: str):
    user    = call.from_user
    chat_id = call.message.chat.id
    msg_id  = call.message.message_id

    if product_id not in PRODUCTS:
        return bot.answer_callback_query(call.id, "Produk tidak ditemukan.", show_alert=True)

    product = PRODUCTS[product_id]

    # Tentukan gambar berdasarkan produk
    GAMBAR_MAP = {
        "NECRO": GAMBAR_NECRO,
        "DRIP" : GAMBAR_DRIP,
        "RW"   : GAMBAR_RW,
    }
    prefix = product_id.split("_")[0]
    gambar = GAMBAR_MAP.get(prefix)

    # Cek stok (khusus non-RW)
    if not product_id.startswith("RW_") and get_stock_count(product_id) == 0:
        return bot.edit_message_text(
            "⚠️ Stok <b>habis</b> untuk produk ini.\n"
            "Silakan hubungi admin atau pilih produk lain.",
            chat_id, msg_id,
            reply_markup=kb_back()
        )

    # Kirim gambar produk sebelum loading
    if gambar and gambar != "https://i.imgur.com/GANTI_INI.jpg":
        try:
            bot.send_photo(
                chat_id,
                photo=gambar,
                caption=(
                    f"{product['emoji']} <b>{product['nama']}</b>\n"
                    f"⏱ Durasi : {product['durasi']}\n"
                    f"💰 Harga  : {rp(product['harga'])}\n\n"
                    "⏳ Sedang membuat QRIS..."
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            # Kirim pesan error gambar ke admin supaya bisa difix
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"⚠️ <b>Gagal kirim gambar!</b>\n"
                    f"Produk : {product_id}\n"
                    f"Error  : <code>{e}</code>\n\n"
                    "Cek link gambar di config.py"
                )
            except Exception:
                pass

    # Loading state
    bot.edit_message_text("⏳ Membuat QRIS, mohon tunggu...", chat_id, msg_id)

    # Buat deposit ke Ramashop
    result = create_deposit(product["harga"])

    if not result["success"]:
        return bot.edit_message_text(
            f"❌ Gagal membuat pembayaran:\n<code>{result['error']}</code>\n\n"
            "Coba lagi atau hubungi admin.",
            chat_id, msg_id,
            reply_markup=kb_back()
        )

    deposit_id   = result["deposit_id"]
    total_amount = result["total_amount"]
    qr_image     = result["qr_image"]
    username     = user.username or ""

    # Simpan ke DB
    create_transaction(
        deposit_id, user.id, username, product_id,
        product["harga"], total_amount, qr_image
    )

    # Tampilkan invoice teks
    trx      = get_transaction(deposit_id)
    inv_text = teks_invoice(trx, "PENDING — Menunggu Pembayaran", product)

    # Edit pesan lama jadi invoice teks
    bot.edit_message_text(inv_text, chat_id, msg_id, reply_markup=kb_back())

    # Kirim gambar QR sebagai pesan baru
    try:
        qr_msg = bot.send_photo(
            chat_id,
            photo=qr_image,
            caption=(
                f"💳 <b>Scan QRIS di atas</b>\n\n"
                f"Bayar tepat: <b>{rp(total_amount)}</b>\n"
                f"(termasuk kode unik agar terdeteksi otomatis)\n\n"
                f"⏱ <i>QRIS berlaku ±30 menit</i>"
            )
        )
        set_message_id(deposit_id, qr_msg.message_id)
    except Exception as e:
        # Kalau foto gagal, kirim sebagai teks
        bot.send_message(
            chat_id,
            f"💳 Bayar QRIS tepat <b>{rp(total_amount)}</b>\n"
            f"QR: {qr_image}",
            reply_markup=kb_back()
        )
        set_message_id(deposit_id, msg_id)

    # Notif admin
    bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Order Baru!</b>\n\n"
        f"👤 User   : @{username} (<code>{user.id}</code>)\n"
        f"📦 Produk : {product['nama']} {product['durasi']}\n"
        f"💰 Bayar  : {rp(total_amount)}\n"
        f"🔖 ID     : <code>{deposit_id}</code>"
    )


# ═════════════════════════════════════════════════════════════
#   BACKGROUND: POLLING CEK PEMBAYARAN
# ═════════════════════════════════════════════════════════════

def payment_checker():
    print(f"[CHECKER] Jalan, interval {CHECK_INTERVAL}s")
    while True:
        try:
            for trx in get_pending():
                deposit_id = trx["deposit_id"]
                product_id = trx["product_id"]
                user_id    = trx["user_id"]
                product    = PRODUCTS.get(product_id)
                if not product:
                    continue

                status = check_status(deposit_id)

                if status == "success":
                    mark_paid(deposit_id)

                    # ── Khusus ROOM WANGI: kirim APK link, tidak pakai stok key ──
                    if product_id.startswith("RW_"):
                        bot.send_message(
                            user_id,
                            f"🎉 <b>Pembayaran Berhasil!</b>\n\n"
                            f"📦 <b>Produk</b> : {product['nama']} {product['durasi']}\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📲 <b>Download APK ({RW_APK_VERSI}):</b>\n"
                            f"{RW_APK_LINK}\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"Terima kasih sudah beli di <b>AL Drip Store</b>! 🖤\n"
                            f"Ada kendala? Hubungi @{ADMIN_USERNAME}",
                            reply_markup=kb_main()
                        )
                        bot.send_message(
                            ADMIN_ID,
                            f"💰 <b>Bayar Masuk!</b>\n"
                            f"User   : <code>{user_id}</code>\n"
                            f"Produk : {product['nama']} {product['durasi']}\n"
                            f"ID     : <code>{deposit_id}</code>"
                        )
                        # Notif channel
                        notif_channel(product, get_transaction(deposit_id), trx.get("username", ""))
                        continue

                    # ── Produk lain (NECRO, DRIP): pakai stok key ──
                    key = take_stock(product_id, user_id)

                    # Kirim key ke user
                    if key:
                        bot.send_message(
                            user_id,
                            f"🎉 <b>Pembayaran Berhasil!</b>\n\n"
                            f"📦 <b>Produk</b> : {product['nama']} {product['durasi']}\n"
                            f"🔑 <b>KEY / LISENSI:</b>\n\n"
                            f"<code>{key}</code>\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"Terima kasih sudah beli di <b>AL Drip Store</b>! 🖤\n"
                            f"Ada kendala? Hubungi @{ADMIN_USERNAME}",
                            reply_markup=kb_main()
                        )
                    else:
                        # Stok habis mendadak
                        bot.send_message(
                            user_id,
                            "✅ Pembayaran diterima!\n\n"
                            "⚠️ Stok sedang habis, admin akan kirim produk manual segera.\n"
                            f"Hubungi @{ADMIN_USERNAME}"
                        )
                        bot.send_message(
                            ADMIN_ID,
                            f"🚨 <b>STOK HABIS!</b>\n"
                            f"User <code>{user_id}</code> sudah bayar!\n"
                            f"Produk: {product_id}\n"
                            f"ID: <code>{deposit_id}</code>\n\n"
                            "⚡ Kirim key manual sekarang!"
                        )

                    # Notif admin bayar masuk
                    bot.send_message(
                        ADMIN_ID,
                        f"💰 <b>Bayar Masuk!</b>\n"
                        f"User   : <code>{user_id}</code>\n"
                        f"Produk : {product['nama']} {product['durasi']}\n"
                        f"ID     : <code>{deposit_id}</code>"
                    )

                    # Notif channel
                    notif_channel(product, get_transaction(deposit_id), trx.get("username", ""))

                elif status in ("already",):
                    # Sudah diproses sebelumnya — tandai selesai
                    mark_paid(deposit_id)

                # 'pending' → lanjut tunggu
                # 'error'   → skip, coba lagi nanti

        except Exception as e:
            print(f"[CHECKER ERROR] {e}")

        time.sleep(CHECK_INTERVAL)


# ═════════════════════════════════════════════════════════════
#   MAIN
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Mulai thread background checker
    t = threading.Thread(target=payment_checker, daemon=True)
    t.start()

    print("=" * 46)
    print("  🖤  AL DRIP STORE BOT — AKTIF")
    print("  Payment: Ramashop QRIS (Polling)")
    print("  Tidak perlu webhook / ngrok!")
    print("=" * 46)

    bot.infinity_polling(timeout=30, long_polling_timeout=30)

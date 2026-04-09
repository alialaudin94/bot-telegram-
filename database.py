# ============================================================
#   DATABASE.PY — SQLite Manager
# ============================================================

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur  = conn.cursor()

    # Stok produk — tiap baris = 1 key/lisensi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT    NOT NULL,
            key_value  TEXT    NOT NULL,
            is_used    INTEGER NOT NULL DEFAULT 0,
            used_at    TEXT,
            used_by    INTEGER
        )
    """)

    # Override angka stok display (tersedia & terjual) — terpisah dari key
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_override (
            product_id TEXT PRIMARY KEY,
            tersedia   INTEGER NOT NULL DEFAULT 0,
            terjual    INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Transaksi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            deposit_id  TEXT    NOT NULL UNIQUE,
            user_id     INTEGER NOT NULL,
            username    TEXT,
            product_id  TEXT    NOT NULL,
            amount      INTEGER NOT NULL,
            total_amount INTEGER NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'PENDING',
            qr_image    TEXT,
            message_id  INTEGER,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            paid_at     TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Siap.")


# ── STOCK ────────────────────────────────────────────────────

def add_stock(product_id: str, keys: list) -> int:
    conn  = get_conn()
    cur   = conn.cursor()
    added = 0
    for k in keys:
        k = k.strip()
        if k:
            cur.execute(
                "INSERT INTO stock (product_id, key_value) VALUES (?,?)",
                (product_id, k)
            )
            added += 1
    conn.commit()
    conn.close()
    return added


def get_stock_count(product_id: str) -> int:
    conn = get_conn()
    cur  = conn.cursor()
    # Cek override dulu
    cur.execute("SELECT tersedia FROM stock_override WHERE product_id=?", (product_id,))
    row = cur.fetchone()
    if row is not None:
        n = row[0]
        conn.close()
        return n
    # Fallback: hitung dari tabel stock
    cur.execute(
        "SELECT COUNT(*) FROM stock WHERE product_id=? AND is_used=0",
        (product_id,)
    )
    n = cur.fetchone()[0]
    conn.close()
    return n


def get_stock_sold(product_id: str) -> int:
    """Hitung jumlah key yang sudah terjual (is_used=1)."""
    conn = get_conn()
    cur  = conn.cursor()
    # Cek override dulu
    cur.execute("SELECT terjual FROM stock_override WHERE product_id=?", (product_id,))
    row = cur.fetchone()
    if row is not None:
        n = row[0]
        conn.close()
        return n
    # Fallback: hitung dari tabel stock
    cur.execute(
        "SELECT COUNT(*) FROM stock WHERE product_id=? AND is_used=1",
        (product_id,)
    )
    n = cur.fetchone()[0]
    conn.close()
    return n


def set_stock_tersedia(product_id: str, jumlah: int):
    conn = get_conn()
    cur  = conn.cursor()
    # Cek apakah sudah ada di override
    cur.execute("SELECT product_id FROM stock_override WHERE product_id=?", (product_id,))
    if cur.fetchone():
        cur.execute(
            "UPDATE stock_override SET tersedia=? WHERE product_id=?",
            (jumlah, product_id)
        )
    else:
        # Ambil terjual existing dulu (dari stock asli)
        cur.execute(
            "SELECT COUNT(*) FROM stock WHERE product_id=? AND is_used=1",
            (product_id,)
        )
        terjual = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO stock_override (product_id, tersedia, terjual) VALUES (?,?,?)",
            (product_id, jumlah, terjual)
        )
    conn.commit()
    conn.close()


def set_stock_terjual(product_id: str, jumlah: int):
    conn = get_conn()
    cur  = conn.cursor()
    # Cek apakah sudah ada di override
    cur.execute("SELECT product_id FROM stock_override WHERE product_id=?", (product_id,))
    if cur.fetchone():
        cur.execute(
            "UPDATE stock_override SET terjual=? WHERE product_id=?",
            (jumlah, product_id)
        )
    else:
        # Ambil tersedia existing dulu (dari stock asli)
        cur.execute(
            "SELECT COUNT(*) FROM stock WHERE product_id=? AND is_used=0",
            (product_id,)
        )
        tersedia = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO stock_override (product_id, tersedia, terjual) VALUES (?,?,?)",
            (product_id, tersedia, jumlah)
        )
    conn.commit()
    conn.close()


def take_stock(product_id: str, user_id: int):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id, key_value FROM stock WHERE product_id=? AND is_used=0 LIMIT 1",
        (product_id,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    cur.execute(
        "UPDATE stock SET is_used=1, used_at=datetime('now','localtime'), used_by=? WHERE id=?",
        (user_id, row["id"])
    )
    # Sinkronkan override jika ada
    cur.execute("SELECT tersedia, terjual FROM stock_override WHERE product_id=?", (product_id,))
    ov = cur.fetchone()
    if ov:
        new_tersedia = max(0, ov[0] - 1)
        new_terjual  = ov[1] + 1
        cur.execute(
            "UPDATE stock_override SET tersedia=?, terjual=? WHERE product_id=?",
            (new_tersedia, new_terjual, product_id)
        )
    conn.commit()
    conn.close()
    return row["key_value"]


# ── TRANSACTIONS ─────────────────────────────────────────────

def create_transaction(deposit_id, user_id, username,
                       product_id, amount, total_amount, qr_image):
    conn = get_conn()
    conn.execute(
        """INSERT INTO transactions
           (deposit_id, user_id, username, product_id,
            amount, total_amount, qr_image)
           VALUES (?,?,?,?,?,?,?)""",
        (deposit_id, user_id, username, product_id,
         amount, total_amount, qr_image)
    )
    conn.commit()
    conn.close()


def set_message_id(deposit_id: str, message_id: int):
    conn = get_conn()
    conn.execute(
        "UPDATE transactions SET message_id=? WHERE deposit_id=?",
        (message_id, deposit_id)
    )
    conn.commit()
    conn.close()


def get_pending():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE status='PENDING'")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_transaction(deposit_id: str):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE deposit_id=?", (deposit_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_paid(deposit_id: str):
    conn = get_conn()
    conn.execute(
        "UPDATE transactions SET status='PAID', paid_at=datetime('now','localtime') WHERE deposit_id=?",
        (deposit_id,)
    )
    conn.commit()
    conn.close()


def mark_expired(deposit_id: str):
    conn = get_conn()
    conn.execute(
        "UPDATE transactions SET status='EXPIRED' WHERE deposit_id=?",
        (deposit_id,)
    )
    conn.commit()
    conn.close()


def get_total_transaksi() -> int:
    """Hitung total semua transaksi yang sudah PAID."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM transactions WHERE status='PAID'")
    n = cur.fetchone()[0]
    conn.close()
    return n
  

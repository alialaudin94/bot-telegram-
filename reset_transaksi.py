import sqlite3
import os

DB_PATH = "/storage/emulated/0/Download/Updated_Store_FIXED/store.db"

if not os.path.exists(DB_PATH):
    print("❌ File store.db tidak ditemukan!")
else:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM transactions")
    total = cur.fetchone()[0]
    print(f"Data sebelum reset: {total} transaksi")

    konfirmasi = input("Yakin mau hapus semua? Ketik 'YA' untuk lanjut: ")

    if konfirmasi.strip().upper() == "YA":
        cur.execute("DELETE FROM transactions")
        conn.commit()
        print("✅ Semua transaksi berhasil dihapus!")
        print("📊 Dashboard sekarang akan menampilkan angka 0.")
    else:
        print("❌ Dibatalkan.")

    conn.close()

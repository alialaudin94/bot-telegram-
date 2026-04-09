import os
import sys
import sqlite3
import subprocess
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_DIR    = "/storage/emulated/0/Download/Updated_Store_FIXED"
BOT_SCRIPT = os.path.join(BOT_DIR, "bot.py")
DB_PATH    = os.path.join(BOT_DIR, "store.db")      # ← store.db bukan orders.db
LOG_PATH   = os.path.join(BOT_DIR, "bot.log")

# ── STATE ─────────────────────────────────────────────────────────────────────
bot_process = None
bot_lock    = threading.Lock()

# ── BOT CONTROL ───────────────────────────────────────────────────────────────
def is_running():
    global bot_process
    return bot_process is not None and bot_process.poll() is None

def start_bot():
    global bot_process
    with bot_lock:
        if is_running():
            return False, "Bot sudah berjalan"
        try:
            log_file = open(LOG_PATH, "a")
            bot_process = subprocess.Popen(
                [sys.executable, BOT_SCRIPT],
                cwd=BOT_DIR,
                stdout=log_file,
                stderr=log_file
            )
            return True, f"Bot started (PID {bot_process.pid})"
        except Exception as e:
            return False, str(e)

def stop_bot():
    global bot_process
    with bot_lock:
        if not is_running():
            return False, "Bot tidak sedang berjalan"
        bot_process.terminate()
        bot_process.wait(timeout=5)
        bot_process = None
        return True, "Bot dihentikan"

# ── DB HELPERS ────────────────────────────────────────────────────────────────
def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except:
        return None

def get_stats():
    conn = get_conn()
    if not conn:
        return {"total": 0, "pending": 0, "paid": 0, "expired": 0, "today": 0, "omset": 0}
    try:
        cur   = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cur.execute("SELECT COUNT(*) FROM transactions")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE status='PENDING'")
        pending = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE status='PAID'")
        paid = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE status='EXPIRED'")
        expired = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE created_at LIKE ?", (f"{today}%",))
        today_count = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE status='PAID'")
        omset = cur.fetchone()[0]

        conn.close()
        return {"total": total, "pending": pending, "paid": paid,
                "expired": expired, "today": today_count, "omset": omset}
    except:
        return {"total": 0, "pending": 0, "paid": 0, "expired": 0, "today": 0, "omset": 0}

def get_orders(limit=20):
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT deposit_id, user_id, username, product_id,
                   amount, total_amount, status, created_at, paid_at
            FROM transactions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except:
        return []

def get_logs(lines=60):
    if not os.path.exists(LOG_PATH):
        return "Belum ada log."
    try:
        with open(LOG_PATH, "r", errors="replace") as f:
            all_lines = f.readlines()
            return "".join(all_lines[-lines:])
    except:
        return "Gagal membaca log."

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status")
def api_status():
    stats = get_stats()
    return jsonify({
        "running": is_running(),
        "pid": bot_process.pid if is_running() else None,
        **stats
    })

@app.route("/api/start", methods=["POST"])
def api_start():
    ok, msg = start_bot()
    return jsonify({"ok": ok, "msg": msg})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    ok, msg = stop_bot()
    return jsonify({"ok": ok, "msg": msg})

@app.route("/api/orders")
def api_orders():
    return jsonify(get_orders())

@app.route("/api/logs")
def api_logs():
    return jsonify({"log": get_logs()})

@app.route("/api/clear_log", methods=["POST"])
def api_clear_log():
    try:
        open(LOG_PATH, "w").close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>AL DRIP BOT PANEL</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
  :root{
    --bg:#0a0a0f;--panel:#12121a;--border:#1e1e2e;
    --accent:#00e5ff;--accent2:#ff4d6d;--green:#00ff88;
    --yellow:#ffd166;--purple:#c084fc;--text:#e0e0f0;--muted:#555570;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Space Mono',monospace;min-height:100vh;
       background-image:radial-gradient(ellipse at 10% 0%,rgba(0,229,255,.06) 0%,transparent 60%),
                        radial-gradient(ellipse at 90% 100%,rgba(255,77,109,.05) 0%,transparent 60%)}
  header{padding:20px 16px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px}
  .logo{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;
        background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .logo span{display:block;font-size:.65rem;font-weight:400;color:var(--muted);-webkit-text-fill-color:var(--muted);margin-top:-2px}
  .dot{width:10px;height:10px;border-radius:50%;background:var(--muted);margin-left:auto;transition:.3s}
  .dot.on{background:var(--green);box-shadow:0 0 8px var(--green)}
  main{padding:16px;display:flex;flex-direction:column;gap:14px;max-width:520px;margin:auto}
  .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
  .stat{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
  .stat-label{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
  .stat-val{font-size:1.8rem;font-weight:700;font-family:'Syne',sans-serif;margin-top:4px}
  .stat-val.green{color:var(--green)}.stat-val.yellow{color:var(--yellow)}
  .stat-val.red{color:var(--accent2)}.stat-val.blue{color:var(--accent)}.stat-val.purple{color:var(--purple)}
  .omset{grid-column:span 2;background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
  .omset .stat-label{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
  .omset .stat-val{font-size:1.4rem;color:var(--green)}
  .control{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px}
  .control h3{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px}
  .btns{display:flex;gap:10px}
  button{flex:1;padding:12px;border:none;border-radius:8px;font-family:'Space Mono',monospace;
         font-size:.85rem;cursor:pointer;font-weight:700;letter-spacing:.05em;transition:.2s}
  #btnStart{background:var(--green);color:#000}#btnStart:hover{opacity:.85}
  #btnStop{background:var(--accent2);color:#fff}#btnStop:hover{opacity:.85}
  button:disabled{opacity:.35;cursor:not-allowed}
  .status-bar{margin-top:10px;font-size:.75rem;padding:8px 12px;border-radius:6px;
              background:rgba(255,255,255,.04);color:var(--muted);min-height:34px}
  .status-bar.ok{color:var(--green)}.status-bar.err{color:var(--accent2)}
  .section{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px}
  .section-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
  .section-head h3{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
  .small-btn{background:none;border:1px solid var(--border);color:var(--muted);
             padding:4px 10px;font-size:.7rem;border-radius:6px;flex:none}
  .small-btn:hover{border-color:var(--accent);color:var(--accent)}
  .order-list{display:flex;flex-direction:column;gap:8px;max-height:300px;overflow-y:auto}
  .order-card{background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
  .order-top{display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted)}
  .order-name{font-size:.88rem;margin:4px 0 4px;color:var(--text)}
  .order-bot{display:flex;justify-content:space-between;align-items:center}
  .badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.62rem;font-weight:700;text-transform:uppercase}
  .badge.PENDING{background:rgba(255,209,102,.15);color:var(--yellow)}
  .badge.PAID{background:rgba(0,255,136,.15);color:var(--green)}
  .badge.EXPIRED{background:rgba(255,77,109,.15);color:var(--accent2)}
  .price{font-size:.8rem;color:var(--purple);font-weight:700}
  .empty{color:var(--muted);font-size:.8rem;text-align:center;padding:20px 0}
  .log-box{background:#080810;border:1px solid var(--border);border-radius:8px;padding:10px;
           font-size:.68rem;line-height:1.7;max-height:220px;overflow-y:auto;
           white-space:pre-wrap;color:#8888aa;margin-top:10px}
  .danger-btn{background:none;border:1px solid var(--border);color:var(--muted);
              padding:4px 10px;font-size:.7rem;border-radius:6px;flex:none}
  .danger-btn:hover{border-color:var(--accent2);color:var(--accent2)}
</style>
</head>
<body>
<header>
  <div><div class="logo">AL DRIP BOT<span>AL DRIP STORE Control Panel</span></div></div>
  <div class="dot" id="statusDot"></div>
</header>
<main>
  <div class="stats">
    <div class="stat"><div class="stat-label">Total Order</div><div class="stat-val blue" id="sTotal">—</div></div>
    <div class="stat"><div class="stat-label">Hari Ini</div><div class="stat-val green" id="sToday">—</div></div>
    <div class="stat"><div class="stat-label">⏳ Pending</div><div class="stat-val yellow" id="sPending">—</div></div>
    <div class="stat"><div class="stat-label">✅ Lunas</div><div class="stat-val green" id="sPaid">—</div></div>
    <div class="stat"><div class="stat-label">❌ Expired</div><div class="stat-val red" id="sExpired">—</div></div>
    <div class="omset"><div class="stat-label">💰 Total Omset (PAID)</div><div class="stat-val" id="sOmset">—</div></div>
  </div>

  <div class="control">
    <h3>⚡ Kontrol Bot</h3>
    <div class="btns">
      <button id="btnStart" onclick="startBot()">▶ START</button>
      <button id="btnStop" onclick="stopBot()">■ STOP</button>
    </div>
    <div class="status-bar" id="statusMsg">Memuat status...</div>
  </div>

  <div class="section">
    <div class="section-head">
      <h3>📦 Transaksi Terbaru</h3>
      <button class="small-btn" onclick="loadOrders()">↻ Refresh</button>
    </div>
    <div class="order-list" id="orderList"><div class="empty">Memuat...</div></div>
  </div>

  <div class="section">
    <div class="section-head">
      <h3>📋 Log Bot</h3>
      <button class="danger-btn" onclick="clearLog()">🗑 Hapus</button>
    </div>
    <button class="small-btn" style="width:100%;margin-bottom:8px" onclick="loadLogs()">↻ Muat Log</button>
    <div class="log-box" id="logBox">Klik "Muat Log" untuk melihat log.</div>
  </div>
</main>

<script>
function rp(n){return'Rp'+Number(n).toLocaleString('id-ID')}

async function fetchStatus(){
  try{
    const d=await(await fetch('/api/status')).json();
    document.getElementById('statusDot').className='dot'+(d.running?' on':'');
    const msg=document.getElementById('statusMsg');
    msg.className='status-bar'+(d.running?' ok':' err');
    msg.textContent=d.running?`✅ Bot berjalan (PID ${d.pid})`:'⛔ Bot tidak aktif';
    document.getElementById('sTotal').textContent=d.total;
    document.getElementById('sToday').textContent=d.today;
    document.getElementById('sPending').textContent=d.pending;
    document.getElementById('sPaid').textContent=d.paid;
    document.getElementById('sExpired').textContent=d.expired;
    document.getElementById('sOmset').textContent=rp(d.omset);
  }catch(e){
    document.getElementById('statusMsg').textContent='❌ Gagal konek ke server';
  }
}

async function startBot(){
  document.getElementById('statusMsg').textContent='Memulai bot...';
  const d=await(await fetch('/api/start',{method:'POST'})).json();
  const msg=document.getElementById('statusMsg');
  msg.className='status-bar'+(d.ok?' ok':' err');
  msg.textContent=(d.ok?'✅ ':'❌ ')+d.msg;
  setTimeout(fetchStatus,1500);
}

async function stopBot(){
  document.getElementById('statusMsg').textContent='Menghentikan bot...';
  const d=await(await fetch('/api/stop',{method:'POST'})).json();
  const msg=document.getElementById('statusMsg');
  msg.className='status-bar'+(d.ok?' ok':' err');
  msg.textContent=(d.ok?'✅ ':'❌ ')+d.msg;
  setTimeout(fetchStatus,1000);
}

async function loadOrders(){
  const orders=await(await fetch('/api/orders')).json();
  const list=document.getElementById('orderList');
  if(!orders.length){list.innerHTML='<div class="empty">Belum ada transaksi</div>';return;}
  list.innerHTML=orders.map(o=>{
    const user=o.username?'@'+o.username:'ID: '+o.user_id;
    const tgl=o.created_at?o.created_at.slice(0,16):'—';
    const status=o.status||'PENDING';
    return `<div class="order-card">
      <div class="order-top"><span>${user}</span><span>${tgl}</span></div>
      <div class="order-name">${o.product_id||'—'}</div>
      <div class="order-bot">
        <span class="badge ${status}">${status}</span>
        <span class="price">${rp(o.total_amount||0)}</span>
      </div>
    </div>`;
  }).join('');
}

async function loadLogs(){
  const d=await(await fetch('/api/logs')).json();
  const box=document.getElementById('logBox');
  box.textContent=d.log;
  box.scrollTop=box.scrollHeight;
}

async function clearLog(){
  if(!confirm('Hapus semua log?'))return;
  await fetch('/api/clear_log',{method:'POST'});
  document.getElementById('logBox').textContent='Log dihapus.';
}

fetchStatus();
loadOrders();
setInterval(fetchStatus,10000);
setInterval(loadOrders,15000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("="*50)
    print("  AL DRIP BOT PANEL")
    print("  Buka browser: http://127.0.0.1:5000")
    print("="*50)
    app.run(host="0.0.0.0", port=5000, debug=False)

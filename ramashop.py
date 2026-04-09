# ============================================================
#   RAMASHOP.PY — Integrasi Ramashop Payment Gateway
#   Docs: https://ramashop.my.id/docs.html
# ============================================================

import requests
from config import RAMASHOP_API_KEY, RAMASHOP_BASE

HEADERS = {
    "X-API-Key"   : RAMASHOP_API_KEY,
    "Content-Type": "application/json"
}


def create_deposit(amount: int) -> dict:
    """
    Buat QRIS baru via Ramashop.
    Return dict:
      success=True  → deposit_id, qr_image, total_amount, message
      success=False → error
    """
    try:
        resp = requests.post(
            f"{RAMASHOP_BASE}/deposit/create",
            json={"amount": amount, "method": "qris"},
            headers=HEADERS,
            timeout=15
        )
        data = resp.json()

        if data.get("success"):
            d = data["data"]
            return {
                "success"     : True,
                "deposit_id"  : d["depositId"],
                "qr_image"    : d["qrImage"],       # URL gambar QR
                "qr_string"   : d.get("qrString",""),
                "total_amount": d["totalAmount"],    # harga + kode unik
                "unique_code" : d.get("uniqueCode", 0),
                "message"     : d.get("message", ""),
                "expired_at"  : d.get("expiredAt", ""),
            }
        else:
            return {
                "success": False,
                "error"  : data.get("message", "Gagal membuat deposit.")
            }

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def check_status(deposit_id: str) -> str:
    """
    Cek status deposit.
    Return: 'success' | 'pending' | 'already' | 'error'
    """
    try:
        resp = requests.get(
            f"{RAMASHOP_BASE}/deposit/status/{deposit_id}",
            headers=HEADERS,
            timeout=10
        )
        data = resp.json()

        if data.get("status") or data.get("success"):
            inner = data.get("data", {})
            return inner.get("status", "pending").lower()
        return "error"

    except requests.exceptions.RequestException:
        return "error"


def get_balance() -> dict:
    """Cek saldo Ramashop. Return {'success', 'balance'/'error'}."""
    try:
        resp = requests.get(
            f"{RAMASHOP_BASE}/balance",
            headers=HEADERS,
            timeout=10
        )
        data = resp.json()
        if data.get("success"):
            return {"success": True, "balance": data["data"]["balance"]}
        return {"success": False, "error": data.get("message", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}
          

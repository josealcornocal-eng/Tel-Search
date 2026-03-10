from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

BASE_URL   = "http://103.195.103.177:5000"
HEADERS    = {"X-API-KEY": "103.195.103.177"}
TIMEOUT    = 30
REINTENTOS = 3

# ─── Cache en memoria ─────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 300

def cache_get(key):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None

def cache_set(key, data):
    _cache[key] = {"data": data, "ts": time.time()}

# ─── Fetch con reintentos ─────────────────────────────────
def fetch(tel: str):
    url = f"{BASE_URL}/tel/{tel}"
    for intento in range(REINTENTOS):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json(), 200
            return None, r.status_code
        except requests.exceptions.RequestException:
            if intento == REINTENTOS - 1:
                return None, 503
            time.sleep(0.3)

# ─── Endpoint ─────────────────────────────────────────────

@app.route("/tel/<string:tel>", methods=["GET"])
def buscar_por_tel(tel):
    cached = cache_get(tel)
    if cached:
        return jsonify({"ok": True, "data": cached}), 200

    data, status = fetch(tel)
    if data:
        cache_set(tel, data)
        return jsonify({"ok": True, "data": data}), 200
    return jsonify({"ok": False, "mensaje": "No se encontraron resultados"}), status

# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)

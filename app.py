from fastapi import FastAPI
from pydantic import BaseModel, Field
import sqlite3, time
import os, json, time, sqlite3, math, statistics as stats
import google.generativeai as genai
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi import HTTPException
from urllib.parse import quote


GEMINI_KEY = os.getenv("GEMINI_API_KEY")  # <-- nama env var
gmodel = None
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    gmodel = genai.GenerativeModel("gemini-1.5-flash")
else:
    gmodel = None

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# Serve the Volttrack frontend under /vol (allow index.html default)
app.mount("/vol", StaticFiles(directory="vol/frontend", html=True), name="vol")

DB = "sensor.db"

# Pemetaan multi-database per sungai/kelas
RIVER_DBS = {
    "buaran": "buaran.db",
    "cakung": "cakung.db",
    "cilliwung": "cilliwung.db",
    "kalimalang": "kalimalang.db",
    "sunter": "sunter.db",
}

VALID_RIVERS = set(RIVER_DBS.keys())

def norm_cls(val: str | None) -> str | None:
    if not val:
        return None
    v = val.strip().lower()
    # toleransi salah ketik umum
    fixes = {"ciliwung": "cilliwung", "cillliwung": "cilliwung"}
    v = fixes.get(v, v)
    return v if v in VALID_RIVERS else None

def home_page():
    return FileResponse("static/index.html")



# model JSON dari ESP32
class SensorIn(BaseModel):
    voltage: float
    temp: float
    humid: float
    ts: int | None = None
    ampere: float | None = None
    power: float | None = None
    co2e: float | None = None
    # kelas sungai; menerima key JSON "class" juga
    cls: str | None = Field(default=None, alias="class")

# bikin tabel kalau belum ada
def _ensure_table_and_columns(dbfile: str):
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()
    # Buat tabel jika belum ada (dengan kolom lengkap baru)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS sensor(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER,
            voltage REAL,
            temp REAL,
            humid REAL,
            ampere REAL,
            power REAL,
            co2e REAL
        )"""
    )
    conn.commit()
    # Tambahkan kolom baru jika DB lama belum punya
    cur.execute("PRAGMA table_info(sensor)")
    cols = {row[1] for row in cur.fetchall()}
    for col, decl in (
        ("ampere", "REAL"),
        ("power", "REAL"),
        ("co2e", "REAL"),
    ):
        if col not in cols:
            try:
                cur.execute(f"ALTER TABLE sensor ADD COLUMN {col} {decl}")
                conn.commit()
            except Exception:
                pass
    conn.close()


def init_db():
    # DB pusat lama tetap dibuat untuk kompatibilitas (prediction, dll)
    _ensure_table_and_columns(DB)

    # Buat tabel untuk setiap DB sungai
    for dbfile in RIVER_DBS.values():
        _ensure_table_and_columns(dbfile)

init_db()

# Redirect root to Volt frontend index
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/vol/index.html")

# Health check
@app.get("/api/health")
def health():
    return {"ok": True}

# endpoint ESP32 POST data ke sini
def _insert_reading(dbfile: str, ts: int, d: SensorIn):
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sensor(ts, voltage, temp, humid, ampere, power, co2e) VALUES(?,?,?,?,?,?,?)",
        (ts, d.voltage, d.temp, d.humid, d.ampere, d.power, d.co2e),
    )
    conn.commit(); conn.close()

@app.post("/esp32")
def receive(d: SensorIn):
    """Terima data dan tentukan DB berdasarkan field 'class' (alias cls)."""
    ts = d.ts or int(time.time())
    cls = norm_cls(d.cls)
    if not cls:
        # fallback: simpan di DB pusat lama juga agar tidak hilang
        _insert_reading(DB, ts, d)
        return {"ok": True, "ts": ts, "note": "No class specified; stored in sensor.db"}
    _insert_reading(RIVER_DBS[cls], ts, d)
    return {"ok": True, "ts": ts, "class": cls}

@app.post("/esp32/{cls}")
def receive_to(cls: str, d: SensorIn):
    """Endpoint alternatif: kelas di path, mis. /esp32/buaran"""
    ts = d.ts or int(time.time())
    c = norm_cls(cls)
    if not c:
        raise HTTPException(status_code=400, detail="Unknown class")
    _insert_reading(RIVER_DBS[c], ts, d)
    return {"ok": True, "ts": ts, "class": c}

# endpoint website ambil data
@app.get("/api/data")
def get_data(cls: str | None = None, limit: int = 20):
    """
    Ambil data sensor.
    - Jika 'cls' diisi (buaran/cakung/cilliwung/kalimalang/sunter) -> ambil dari DB tersebut.
    - Jika kosong -> gabungkan data terbaru dari semua DB dan urutkan DESC, batasi 'limit'.
    """
    def read_from(dbfile: str, lim: int):
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        cur.execute(
            "SELECT ts, voltage, temp, humid, ampere, power, co2e FROM sensor ORDER BY ts DESC LIMIT ?",
            (lim,),
        )
        rows = cur.fetchall(); conn.close()
        return rows

    c = norm_cls(cls) if cls else None
    if c:
        rows = read_from(RIVER_DBS[c], limit)
        return [
            {"ts": r[0], "voltage": r[1], "temp": r[2], "humid": r[3],
             "ampere": r[4], "power": r[5], "co2e": r[6], "class": c}
            for r in rows
        ]

    # gabungkan dari semua DB
    combined = []
    for cname, dbfile in RIVER_DBS.items():
        for r in read_from(dbfile, limit):
            combined.append((r[0], r[1], r[2], r[3], r[4] if len(r)>4 else None, r[5] if len(r)>5 else None, r[6] if len(r)>6 else None, cname))
    combined.sort(key=lambda x: x[0], reverse=True)
    combined = combined[:limit]
    return [
        {"ts": r[0], "voltage": r[1], "temp": r[2], "humid": r[3],
         "ampere": r[4], "power": r[5], "co2e": r[6], "class": r[7]}
        for r in combined
    ]

def ensure_tables():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS prediction(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        text TEXT
    )""")
    conn.commit(); conn.close()
ensure_tables()

def db(query, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(query, params)
    out = cur.fetchall() if fetch else None
    conn.commit(); conn.close()
    return out

# Simple demo login to support Volt frontend
@app.post("/auth/login")
def auth_login(payload: dict):
    user = payload.get("username")
    pwd = payload.get("password")
    if user == "galapaksi81" and pwd == "123":
        return {"user": {"username": user}}
    raise HTTPException(status_code=401, detail="Login gagal")

@app.get("/get/response_old")
def get_response():
    if not gmodel:
        return {"ok": False, "error": "Set GEMINI_API_KEY in environment first."}

    # ambil 12 data terakhir (≈1 menit kalau kirim tiap 5 detik)
    rows = db("SELECT ts, voltage, temp, humid FROM sensor ORDER BY ts DESC LIMIT 12", fetch=True)
    if not rows:
        return {"ok": False, "error": "No sensor data yet."}
    rows = rows[::-1]  # urut lama→baru

    prompt = f"""
    You are an IoT time-series assistant. Given recent (ts, voltage, temp, humid) rows:
    {json.dumps(rows)}
    Return a concise JSON with keys:
      - description: short textual analysis (<=2 sentences)
      - next_voltage: numeric prediction 1 minute ahead
      - confidence: low/medium/high
    Only return JSON.
    """

    resp = gmodel.generate_content(prompt)
    text = resp.text.strip()

    # simpan ke DB sebagai teks mentah (bisa JSON)
    db("INSERT INTO prediction(ts, text) VALUES(?, ?)", (int(time.time()), text))
    return {"ok": True, "prediction": text}


# New multi-river response with 12-step prediction per river
@app.get("/get/response")
def get_response_multi():
    if not gmodel:
        return {"ok": False, "error": "Set GEMINI_API_KEY in environment first."}

    def read_recent(dbfile: str, n: int = 12):
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        cur.execute(
            "SELECT ts, voltage, temp, humid FROM sensor ORDER BY ts DESC LIMIT ?",
            (n,),
        )
        rows = cur.fetchall(); conn.close()
        return rows[::-1]

    rivers_payload = { name: read_recent(dbfile, 12) for name, dbfile in RIVER_DBS.items() }
    if not any(rivers_payload.values()):
        return {"ok": False, "error": "No sensor data yet across rivers."}

    prompt = f"""
    Anda adalah asisten analisis time-series IoT. Anda menerima data sensor terbaru untuk beberapa sungai.
    Setiap baris adalah [ts, voltage, temp, humid]. Data per sungai (tertua -> terbaru):
    {json.dumps(rivers_payload)}

    Keluarkan SATU objek JSON dengan tepat 5 key: buaran, cakung, cilliwung, kalimalang, sunter.
    Untuk setiap key berikan objek:
      - analysis: ringkasan dalam bahasa Indonesia (1 kalimat) dan saran (1 kalimat) yang saran berupa (jika voltage 0 maka saran ganti lumpur), (jika voltage sekitar 50-80 maka saran menambahkan substrat), (jika voltage terlihat ingin turun ke 0 maka saran lumpur sebaiknya diganti dalam beberapa jam), (jika voltage terlihat naik turun maka saran pengecekan kabel yang ada)
      - next_voltage: array berisi 12 prediksi tegangan untuk 12 jam ke depan (1 nilai per jam, panjang 12)
      - confidence: salah satu dari low, medium, high

    Panduan prediksi:
      - Hindari deret datar/konstan (misalnya semua 0) kecuali 12 jam terakhir memang datar atau perangkat OFF.
      - Cerminkan tren/variasi terakhir secara halus; fluktuasi kecil diperbolehkan; nilai harus >= 0.
      - Jika nilai terakhir 0 karena downtime, boleh mendekati 0 namun beri dinamika kecil bila pemulihan mungkin.

    Gunakan format tanggal/waktu manusia untuk teks pada analysis (contoh: "17 Jan 2025 14.30"), jangan menulis epoch.
    Hanya kirim JSON murni (tanpa blok kode). Jika suatu sungai tidak punya data, tetap kirim key tersebut dengan
    next_voltage: [], analysis: "no data", confidence: "low".
    """

    resp = gmodel.generate_content(prompt)
    text = resp.text.strip()

    # Post-process: if model returned overly flat predictions, add slight variation based on recent trend
    try:
        parsed = json.loads(text)
        adjusted = {}
        for cname, series in rivers_payload.items():
            node = (parsed or {}).get(cname) or {}
            nxt = node.get("next_voltage") if isinstance(node, dict) else None
            if not isinstance(nxt, list):
                adjusted[cname] = node
                continue
            # recent stats
            recent_vals = [float(r[1]) for r in series[-12:]] if series else []
            last_v = recent_vals[-1] if recent_vals else 0.0
            recent_var = 0.0
            if len(set(recent_vals)) > 1:
                try:
                    recent_var = stats.pstdev(recent_vals)
                except Exception:
                    recent_var = 0.0
            flat_pred = len(nxt) == 12 and len(set(round(float(x), 4) for x in nxt)) <= 1
            if flat_pred and (recent_var > 0.0 or last_v > 0.0):
                base = last_v if last_v > 0 else (recent_vals[-1] if recent_vals else 0.0)
                amp = max(0.03 * (max(recent_vals) if recent_vals else 1.0), 0.05)
                new_seq = []
                for i in range(12):
                    # small smooth fluctuation around base, slightly decaying
                    val = max(0.0, base * (0.98 + 0.02 * math.sin((i+1) * math.pi/4)) - 0.005 * i)
                    new_seq.append(round(val, 3))
                node["next_voltage"] = new_seq
            else:
                # ensure numeric and non-negative
                node["next_voltage"] = [max(0.0, float(x)) for x in nxt[:12]]
            adjusted[cname] = node
        # keep structure for any missing rivers
        for cname in RIVER_DBS.keys():
            adjusted.setdefault(cname, {"analysis":"no data","next_voltage":[],"confidence":"low"})
        text = json.dumps(adjusted)
    except Exception:
        # keep original text if parsing failed
        pass

    db("INSERT INTO prediction(ts, text) VALUES(?, ?)", (int(time.time()), text))
    return {"ok": True, "prediction": text}

@app.get("/api/prediction/latest")
def latest_prediction():
    row = db("SELECT ts, text FROM prediction ORDER BY ts DESC LIMIT 1", fetch=True)
    if not row:
        return {"ok": False, "error": "No prediction yet."}
    ts, text = row[0]
    # coba parse JSON; kalau gagal, kirim sebagai plain text
    try:
        parsed = json.loads(text)
        return {"ok": True, "ts": ts, "data": parsed}
    except Exception:
        return {"ok": True, "ts": ts, "text": text}


# Endpoint sederhana untuk memicu popup notifikasi di dashboard
@app.get("/notify")
def notify(msg: str | None = None):
    """
    Arahkan ke /vol/dashboard.html dengan query ?notif=...
    Contoh:
      - /notify            -> tampilkan pesan default
      - /notify?msg=Halo   -> tampilkan pesan kustom
    """
    target = "/vol/dashboard.html"
    if msg:
        target += f"?notif={quote(msg)}"
    else:
        target += "?notif=1"
    return RedirectResponse(url=target)

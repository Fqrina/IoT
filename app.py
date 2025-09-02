from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3, time
import os, json, time, sqlite3
import google.generativeai as genai
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse



GEMINI_KEY = os.getenv("GEMINI_API_KEY")  # <-- nama env var
gmodel = None
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    gmodel = genai.GenerativeModel("gemini-1.5-flash")
else:
    gmodel = None

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

DB = "sensor.db"
def home_page():
    return FileResponse("static/index.html")

# model JSON dari ESP32
class SensorIn(BaseModel):
    voltage: float
    temp: float
    humid: float
    ts: int | None = None

# bikin tabel kalau belum ada
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sensor(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        voltage REAL,
        temp REAL,
        humid REAL
    )""")
    conn.commit(); conn.close()

init_db()

@app.get("/", response_class=FileResponse)
def root():
    return "static/index.html"


@app.get("/")
def home():
    return {"message": "Hello from ESP32 backend!"}

# endpoint ESP32 POST data ke sini
@app.post("/esp32")
def receive(d: SensorIn):
    ts = d.ts or int(time.time())
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO sensor(ts, voltage, temp, humid) VALUES(?,?,?,?)",
                (ts, d.voltage, d.temp, d.humid))
    conn.commit(); conn.close()
    return {"ok": True, "ts": ts}

# endpoint website ambil data
@app.get("/api/data")
def get_data():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT ts, voltage, temp, humid FROM sensor ORDER BY ts DESC LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    return [{"ts": r[0], "voltage": r[1], "temp": r[2], "humid": r[3]} for r in rows]

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

@app.get("/get/response")
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
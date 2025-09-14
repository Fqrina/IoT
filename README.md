# Galapaksi — IoT ESP32 REST API

Repositori ini berisi source code backend (REST API) juga frontend untuk website proyek IoT berbasis ESP32. Backend menggunakan FastAPI untuk menerima data sensor (tegangan, suhu, kelembapan) dari ESP32, menyimpan ke SQLite, dan menyediakan endpoint untuk membaca data. Integrasi analitik/prediksi AI. Frontend berisi kode yang menunjukkan website

## Tim
- Nama tim: Galapaksi
- Anggota: Raihana, Faiq, Gendis, Raffa

## Struktur Singkat
- `app.py`: Aplikasi FastAPI (endpoint REST, akses database).
- `requirements.txt`: Dependensi Python.
- `static/`: Website uji coba (sementara untuk testing; isi akan berubah ke depan).
- `sensor.db`: Database SQLite lokal (dibuat otomatis saat aplikasi berjalan).

## Menjalankan Secara Lokal
- Prasyarat: Python 3.10+
- Install dependency: `pip install -r requirements.txt`
- (Opsional) Set kunci Gemini jika ingin fitur AI:
  - Windows: `set GEMINI_API_KEY=your_key_here`
- Jalankan server: `uvicorn app:app --reload --port 5000`
- Akses: `http://127.0.0.1:5000`

## Endpoint Utama
- `POST /esp32` — ESP32 mengirim data sensor: `{"ts":1758199600,"voltage":0.0,"temp":25.6,"humid":64.0,"ampere":0.0,"power":0.0,"co2e":0.0,"class":"sunter"},`
- `GET /api/data` — Ambil 20 data terbaru dari database.
- `GET /get/response` — Ringkasan + prediksi AI (perlu `GEMINI_API_KEY`).
- `GET /api/prediction/latest` — Ambil prediksi terakhir yang tersimpan.


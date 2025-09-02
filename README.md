# Galapaksi — IoT ESP32 REST API

Repositori ini berisi source code backend (REST API) untuk proyek IoT berbasis ESP32. Backend menggunakan FastAPI untuk menerima data sensor (tegangan, suhu, kelembapan) dari ESP32, menyimpan ke SQLite, dan menyediakan endpoint untuk membaca data. Integrasi analitik/prediksi AI (Gemini) bersifat opsional.

## Tim
- Nama tim: Galapaksi
- Anggota: Raihana, Faiq, Gendis, Rafa

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
- `POST /esp32` — ESP32 mengirim data sensor: `{ "voltage": 3.7, "temp": 28.5, "humid": 60.2, "ts": 1717290000 }`
- `GET /api/data` — Ambil 20 data terbaru dari database.
- `GET /get/response` — Ringkasan + prediksi AI (perlu `GEMINI_API_KEY`).
- `GET /api/prediction/latest` — Ambil prediksi terakhir yang tersimpan.

## Catatan
- Folder `static/` saat ini hanya untuk test website dan akan berubah/ditingkatkan ke depan.
- Untuk kebutuhan lomba saat ini, fokus repositori adalah REST API sebagai backend untuk ESP32.


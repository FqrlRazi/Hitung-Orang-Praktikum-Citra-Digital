# Hitung Orang dari Citra

Demo penghitungan objek pada foto dengan latar terkendali menggunakan Python,
OpenCV, FastAPI, HTML, Tailwind CSS, dan JavaScript.

## Struktur

```text
projectAkhir/
├── backend/
│   ├── models/face_detection_yunet_2023mar.onnx
│   └── app/
│       ├── __init__.py
│       ├── image_processing.py
│       └── main.py
├── frontend/
│   ├── css/style.css
│   ├── js/app.js
│   └── index.html
└── requirements.txt
```

## Menjalankan aplikasi

Jalankan perintah berikut di Bash dari folder `projectAkhir`:

```bash
cd /d/prakCitraDigital/projectAkhir
source .venv/Scripts/activate
python -m uvicorn backend.app.main:app --reload
```

Buka `http://127.0.0.1:8000`. Dokumentasi API tersedia di
`http://127.0.0.1:8000/docs`.

Tailwind CSS dimuat dari CDN, jadi perlu koneksi internet untuk styling Tailwind.

## Cara kerja

Warna median dari pita di tepi gambar dipakai sebagai perkiraan warna latar.
Jarak warna CIELAB menentukan mask foreground. Gaussian blur dan operasi
morfologi opening/closing membersihkan mask sebelum kontur eksternal ditemukan.
Jika terdeteksi setidaknya dua wajah, model YuNet OpenCV memberikan hitungan dan
kotak wajah agar posisi deteksi tampak jelas. Jika tidak, aplikasi memakai
kontur hasil segmentasi latar. Sensitivitas warna dan batas luas kontur memakai
nilai bawaan agar pengguna cukup mengunggah foto dan menjalankan analisis.
Wajah yang tertutup atau membelakangi kamera mungkin tidak terdeteksi; sistem
ini tetap demo pengolahan citra, bukan model deteksi orang serbaguna.

Di hasil website, **Deteksi wajah** menampilkan kotak dari YuNet. **Mask latar**
menampilkan hasil threshold warna seluruh gambar (putih = foreground, hitam =
latar); mask ini bukan segmentasi bentuk wajah dan tidak menentukan kotak wajah.

Model YuNet disertakan di `backend/models/face_detection_yunet_2023mar.onnx`
dan bersumber dari [OpenCV Zoo](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet).

## Metode segmentasi dan analisis kontur

Sistem menggunakan perkiraan latar dari median piksel tepi, konversi citra ke
ruang warna CIELAB, pengukuran jarak warna, threshold warna, Gaussian blur,
serta operasi morfologi opening dan closing. Kontur eksternal kemudian
dievaluasi berdasarkan luas, batas persegi, jumlah sisi pendekatan poligon,
circularity, dan rasio aspek.

Setiap kontur diklasifikasikan berdasarkan poligon, circularity, convexity
defects, dan rasio aspek kontur. Kategori yang dapat ditampilkan mencakup
segitiga, hati, kotak, persegi panjang, segi lima, segi enam, bulat, oval,
lonjong, dan mendatar. Untuk deteksi wajah, bentuk diambil dari kontur piksel
di dalam kotak YuNet dan bukan dari bentuk kotak itu sendiri.
Informasi metode, warna latar, jumlah objek, bentuk, ukuran, dan rasio aspek
ditampilkan sebagai laporan pendeteksian pada website.

## Unduh laporan PDF

Setelah analisis berhasil, tombol **Unduh PDF** membuat file PDF berisi:

- citra hasil deteksi dengan kotak YuNet atau kontur;
- mask segmentasi foreground dan latar;
- metode segmentasi dan deteksi;
- warna latar perkiraan;
- tabel nomor objek, bentuk kontur, ukuran, rasio aspek, dan sumber bentuk.
- confidence deteksi wajah dan skor kecocokan bentuk kontur.

## Dashboard dan histori

Setiap analisis disimpan sebagai histori non-SQL dalam folder `data/history`.
Dashboard tersedia di `http://127.0.0.1:8000/dashboard.html` dan menampilkan
total analisis, rata-rata jumlah hasil, jumlah riwayat berbasis wajah, serta
tautan PDF untuk tiap record. PDF histori menyertakan rata-rata confidence wajah
atau skor kecocokan bentuk, perbandingan dengan record sebelumnya yang memakai
metode sama, dan citra hasil. Perbandingan skor antarcitra bukan ukuran akurasi
model karena isi dan kualitas citra dapat berbeda.

## Deployment Vercel

Project menggunakan konfigurasi FastAPI pada `pyproject.toml`:

```toml
[tool.vercel]
entrypoint = "backend.app.main:app"
```

Dependency runtime juga dicantumkan pada bagian `[project].dependencies` di
file tersebut agar Vercel memasang FastAPI, OpenCV, NumPy, dan ReportLab saat
build. Frontend disajikan dari mount `StaticFiles` dengan `html=True`.

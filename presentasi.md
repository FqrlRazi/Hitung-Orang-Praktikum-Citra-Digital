# Presentasi Proyek Akhir

## Sistem Penghitungan Wajah pada Citra Menggunakan Segmentasi Warna, Morfologi, Analisis Kontur, dan Deteksi Wajah

**Nama:** [Nama]  
**NIM:** [NIM]  
**Mata kuliah:** Pengolahan Citra Digital  
**Dosen:** [Nama dosen]

---

## Slide 1 - Judul

### Sistem Penghitungan Wajah pada Citra Menggunakan Segmentasi Warna, Morfologi, Analisis Kontur, dan Deteksi Wajah

- Implementasi berbasis website
- Python dan OpenCV
- FastAPI, HTML, Tailwind CSS, dan JavaScript
- Model deteksi wajah YuNet

**Narasi:**  
“Pada proyek ini, saya membangun aplikasi web yang dapat menerima foto, mendeteksi wajah, menghitung hasil deteksi, menampilkan mask latar dan mask wajah, serta membuat laporan PDF.”

---

## Slide 2 - Latar Belakang

- Penghitungan wajah atau orang pada foto kelompok dapat memakan waktu jika dilakukan secara manual.
- Pengolahan citra dapat membantu memisahkan objek dari latar dan menganalisis karakteristik citra.
- Segmentasi berbasis warna cocok untuk gambar dengan latar terkendali.
- Deteksi wajah menggunakan model dapat memberikan posisi wajah yang lebih jelas.
- Project ini menggabungkan metode pengolahan citra tradisional dan deteksi wajah modern.

**Narasi:**  
“Project ini tidak hanya menghitung objek, tetapi juga mendemonstrasikan alur pengolahan citra mulai dari input gambar sampai visualisasi dan laporan hasil.”

---

## Slide 3 - Rumusan Masalah dan Tujuan

### Rumusan masalah

- Bagaimana memisahkan objek dan latar pada citra?
- Bagaimana mengambil dan mengklasifikasikan kontur hasil segmentasi?
- Bagaimana mendeteksi dan menghitung wajah pada foto?
- Bagaimana menampilkan dan mengunduh hasil analisis melalui website?

### Tujuan

- Menerima gambar JPG, PNG, atau WebP.
- Membuat mask segmentasi latar.
- Membuat mask kotak wajah.
- Menghitung wajah atau kontur.
- Menampilkan hasil bentuk, ukuran, dan rasio aspek.
- Menghasilkan laporan PDF.

---

## Slide 4 - Batasan Sistem

- Gambar dibatasi maksimal 10 MB.
- Resolusi maksimum backend adalah 25 megapiksel.
- Sistem menggunakan pengaturan bawaan sensitivitas warna dan luas kontur.
- Segmentasi paling cocok untuk latar rata dan pencahayaan relatif merata.
- YuNet mendeteksi wajah yang terlihat. Wajah tertutup, miring, terlalu kecil, atau membelakangi kamera dapat terlewat.
- Project merupakan prototipe demonstrasi, bukan sistem pengawasan atau deteksi orang serbaguna.

**Narasi:**  
“Kriteria ini penting agar hasil tidak disalahartikan sebagai akurasi mutlak untuk semua jenis foto.”

---

## Slide 5 - Teknologi yang Digunakan

| Komponen | Teknologi |
|---|---|
| Bahasa pemrosesan | Python |
| Pengolahan citra | OpenCV dan NumPy |
| Backend dan API | FastAPI |
| Deteksi wajah | YuNet FaceDetectorYN |
| Frontend | HTML, Tailwind CSS, JavaScript |
| Laporan | ReportLab |
| Deployment | Uvicorn dan konfigurasi Vercel |

Model YuNet disimpan sebagai:

`backend/models/face_detection_yunet_2023mar.onnx`

---

## Slide 6 - Alur Kerja Aplikasi

1. Pengguna membuka halaman web.
2. Pengguna memilih atau menyeret gambar ke area unggah.
3. Frontend mengirim gambar ke endpoint `/api/analyze`.
4. Backend membaca dan memvalidasi gambar.
5. Warna latar diperkirakan dari piksel tepi gambar.
6. Segmentasi CIELAB membentuk mask foreground dan latar.
7. Mask dibersihkan menggunakan blur dan morfologi.
8. Kontur dianalisis dan diklasifikasikan.
9. YuNet mendeteksi wajah.
10. Website menampilkan visual hasil, tiga pilihan mask, dan ringkasan.

---

## Slide 7 - Segmentasi Warna CIELAB

### Proses

- Piksel pada pita tepi citra dikumpulkan.
- Nilai median pita tepi dipakai sebagai perkiraan warna latar.
- Citra dikonversi dari BGR ke ruang warna CIELAB.
- Jarak Euclidean dihitung antara setiap piksel dan warna latar perkiraan.
- Piksel yang jaraknya melewati batas sensitivitas menjadi foreground.
- Pixel lain menjadi latar.

### Hasil mask

- Putih: area foreground.
- Hitam: area latar.

**Narasi:**  
“Mask ini menunjukkan pembagian foreground dan latar berdasarkan perbedaan warna. Mask ini bukan mask wajah.”

---

## Slide 8 - Gaussian Blur dan Morfologi

Setelah threshold:

1. Gaussian blur berukuran 5 x 5 menghaluskan noise mask.
2. Threshold kedua membuat mask kembali menjadi citra biner.
3. Opening menggunakan kernel elips 3 x 3 menghilangkan noise kecil.
4. Closing menggunakan kernel elips 7 x 7 menutup lubang atau celah kecil.
5. Komponen yang bersentuhan diproses tambahan dengan watershed.

**Penting:**  
Proses opening/closing menjaga dan membersihkan batas objek. Hasil morfologi kemudian dipakai untuk ekstraksi kontur.

---

## Slide 9 - Pemisahan dan Analisis Kontur

- Kontur eksternal diambil menggunakan `findContours`.
- Kontur yang luasnya kurang dari batas minimum dibuang.
- `boundingRect` menghasilkan ukuran kotak objek.
- Pendekatan poligon menghitung jumlah sisi.
- Circularity mengukur kedekatan bentuk dengan lingkaran.
- Rasio aspek dihitung dari lebar dibagi tinggi.
- Ellipse roundness dan convexity defects digunakan pada beberapa klasifikasi.

Bentuk yang dapat ditampilkan antara lain:

- Segitiga
- Hati
- Kotak
- Persegi panjang
- Segi lima
- Segi enam
- Bulat
- Oval
- Lonjong
- Mendatar
- Tegak

**Narasi:**  
“Bentuk yang ditampilkan berasal dari bentuk kontur, bukan hanya dari nama kotak deteksi.”

---

## Slide 10 - Deteksi Wajah YuNet

- Citra diperkecil secara proporsional jika ukuran maksimum melebihi 1.200 piksel.
- Model YuNet melalui `cv2.FaceDetectorYN` mendeteksi wajah.
- Ambang deteksi yang dipakai adalah 0.7.
- Kotak hasil dikembalikan ke skala citra asli.
- Jika terdeteksi minimal dua wajah, hasil utama memakai deteksi wajah.
- Jika wajah kurang dari dua, aplikasi memakai hasil kontur eksternal.

**Narasi:**  
“Perbedaan minimum dua wajah bukan pembatas deteksi untuk satu wajah. Kondisi ini dipakai agar mode YuNet dipilih pada foto yang diduga sebagai foto kelompok.”

---

## Slide 11 - Mask Wajah dan Bentuk dalam Kotak Wajah

Mask wajah dibuat sebagai citra hitam berukuran sama dengan input.

- Setiap kotak hasil YuNet diisi warna putih.
- Semua area di luar kotak berwarna hitam.
- Mask ini disebut **Mask kotak wajah**.

Untuk mode wajah, sistem juga menganalisis area piksel di dalam kotak:

- Area kotak diperluas sekitar 10%.
- Area dipilih berdasarkan warna HSV dan YCrCb.
- Morphology close dan open membersihkan mask kulit.
- Kontur kulit terbesar dianalisis untuk mendapatkan bentuk, circularity, dan rasio aspek.

**Penting:**  
Mask kotak wajah menunjukkan lokasi deteksi. Ini bukan segmentasi wajah pixel yang sempurna.

---

## Slide 12 - Arsitektur Aplikasi

```text
Frontend
index.html
css/style.css
js/app.js
        |
        | POST /api/analyze
        | POST /api/report/pdf
        v
Backend FastAPI
main.py
image_processing.py
        |
        v
OpenCV + YuNet ONNX
```

- `index.html`: struktur tampilan.
- `style.css`: gaya visual.
- `app.js`: unggah, validasi, panggilan API, tab visualisasi, dan unduh PDF.
- `main.py`: endpoint API, validasi format dan ukuran, serta servis frontend.
- `image_processing.py`: seluruh pemrosesan citra dan pembuatan PDF.

---

## Slide 13 - Endpoint dan Layanan Backend

### Endpoint aplikasi

- `GET /api/health`: memeriksa status layanan.
- `POST /api/analyze`: menerima gambar dan mengirim hasil analisis.
- `POST /api/report/pdf`: menerima gambar dan menghasilkan laporan PDF.
- `/docs`: dokumentasi otomatis FastAPI.
- `/`: halaman frontend.

### Format respons analisis

- Jumlah deteksi
- Metode deteksi
- Metode segmentasi
- Citra anotasi
- Mask latar
- Mask kotak wajah
- Ukuran citra
- Warna latar perkiraan
- Tabel deteksi dan kontur

---

## Slide 14 - Antarmuka dan Fitur Website

Fitur utama:

- Pemilihan file melalui tombol atau drag-and-drop.
- Pratinjau gambar.
- Validasi JPG, PNG, dan WebP.
- Pembatasan ukuran maksimal 10 MB.
- Tombol analisis dan status proses.
- Jumlah wajah atau objek.
- Ringkasan metode segmentasi dan deteksi.
- Ringkasan warna latar perkiraan.
- Tabel bentuk, ukuran, rasio aspek, dan sumber bentuk.
- Unduh laporan PDF.

Website menyediakan tiga visualisasi:

1. **Deteksi wajah atau kontur**
2. **Mask latar**
3. **Mask wajah**

---

## Slide 15 - Isi Laporan PDF

Laporan PDF berisi:

- Judul laporan.
- Jumlah hasil.
- Metode deteksi.
- Metode segmentasi.
- Ukuran citra.
- Warna latar perkiraan dalam RGB.
- Citra hasil deteksi.
- Mask latar.
- Mask kotak wajah.
- Tabel nomor, bentuk, ukuran, rasio aspek, dan sumber bentuk.

Laporan dibuat dengan ReportLab setelah backend menjalankan analisis ulang pada gambar yang dipilih.

---

## Slide 16 - Perbandingan Hasil dan Peran Masing-masing

| Visual | Sumber | Artinya |
|---|---|---|
| Deteksi wajah | YuNet | Kotak area wajah |
| Deteksi kontur | Segmentasi latar | Kotak area kontur foreground |
| Mask latar | Perbedaan warna CIELAB | Area foreground dan latar |
| Mask wajah | Kotak hasil YuNet | Area kotak dianggap wajah |
| Bentuk kontur | Poligon, circularity, rasio aspek | Karakteristik bentuk objek |

Ketiga proses utama pada project benar-benar digunakan:

- Segmentasi warna membentuk mask foreground.
- Morfologi membersihkan dan memproses mask.
- Analisis kontur menghitung dan mengklasifikasikan objek.

YuNet merupakan lapisan deteksi wajah tambahan yang dipakai sebagai hasil utama pada foto dengan minimal dua wajah.

---

## Slide 17 - Pengujian

Pengujian yang dapat ditunjukkan:

- Pengujian format gambar yang diterima.
- Pengujian penolakan file melebihi 10 MB.
- Pengujian citra satu siluet.
- Pengujian dua siluet terpisah.
- Pengujian dua siluet yang bersentuhan.
- Pengujian beberapa foto dengan wajah terlihat.
- Pengujian endpoint analisis.
- Pengujian pembuatan laporan PDF.
- Pengujian ketiga visualisasi pada website.

**Penting:**  
Pengujian contoh menunjukkan fungsi sistem, tetapi belum menggantikan pengujian akurasi memakai dataset berlabel.

---

## Slide 18 - Kelebihan

- Antarmuka sederhana dan responsif.
- Menghubungkan pengolahan citra tradisional dengan deteksi wajah modern.
- Menampilkan proses secara bertahap.
- Memisahkan mask latar dan mask wajah.
- Menyediakan laporan PDF yang dapat diunduh.
- Backend dan frontend dipisahkan melalui API.
- Sistem dapat berjalan pada website lokal dan dapat dikonfigurasi untuk Vercel.

---

## Slide 19 - Kekurangan dan Keterbatasan

- Mask latar sensitif terhadap variasi warna dan pencahayaan.
- Latar kompleks dapat menghasilkan foreground yang salah.
- Kontur yang menyatu dapat mewakili lebih dari satu orang.
- Wajah kecil, miring, tertutup, atau membelakangi kamera dapat gagal.
- Mask wajah berupa kotak, bukan masker piksel wajah presisi.
- Deteksi kulit dapat terpengaruh warna latar atau pencahayaan.
- Belum ada pengukuran akurasi pada dataset besar.

---

## Slide 20 - Kesimpulan

- Aplikasi berhasil mengimplementasikan segmentasi warna CIELAB.
- Gaussian blur, opening, closing, dan watershed digunakan untuk memproses mask.
- Kontur eksternal diekstraksi, disaring, dan diklasifikasikan.
- YuNet mendeteksi wajah dan menghasilkan kotak pada citra.
- Mask latar dan mask kotak wajah ditampilkan sebagai visual yang berbeda.
- Website menampilkan jumlah, bentuk, ukuran, rasio aspek, dan warna latar.
- Sistem dapat mengunduh laporan PDF berisi hasil lengkap.

---

## Slide 21 - Pengembangan Selanjutnya

- Menambah pemisahan objek yang saling bertumpuk.
- Membandingkan beberapa metode segmentasi.
- Menambah model segmentasi wajah berbasis piksel.
- Membuat dataset uji berlabel jumlah wajah.
- Mengukur akurasi, presisi, recall, dan mean absolute error.
- Menambahkan indikator keyakinan atau kualitas deteksi.
- Menyediakan unduhan mask PNG.
- Menambah opsi sensitivitas pada antarmuka.

---

## Pertanyaan yang Mungkin Ditanyakan

### Mengapa ada dua jenis mask?

Mask latar menggambarkan segmentasi warna seluruh citra, sedangkan mask wajah terdiri atas kotak putih hasil deteksi YuNet.

### Apakah kotak wajah adalah mask wajah yang presisi?

Belum. Mask wajah saat ini adalah mask kotak/bounding box, bukan siluet kulit atau wajah per piksel.

### Mengapa hasil utama bisa berasal dari kontur atau wajah?

Jika YuNet mendeteksi minimal dua wajah, hasilnya memakai hitungan dan kotak wajah. Jika tidak, sistem memakai kontur foreground yang lolos penyaringan.

### Mengapa menghitung setidaknya dua wajah untuk memakai YuNet?

YuNet tetap mendeteksi satu wajah. Namun pada project ini, dua deteksi digunakan sebagai pemicu mode wajah supaya citra tunggal tidak otomatis dianggap sebagai hasil deteksi orang.

### Apakah sistem sudah menghitung orang dengan akurat?

Belum dapat dinyatakan akurat untuk semua citra. Sistem merupakan prototipe dan perlu diuji pada dataset berlabel.

### Apa fungsi laporan PDF?

PDF merekap hasil deteksi, visual mask, metode, warna latar, dan tabel karakteristik kontur atau wajah agar dapat digunakan sebagai laporan.

**Penutup:**  
“Demikian presentasi project Sistem Penghitungan Wajah pada Citra. Terima kasih atas perhatian dan saya siap menjawab pertanyaan.”

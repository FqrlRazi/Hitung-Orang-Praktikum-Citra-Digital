Read
Completed with input: {
"path": "D:\\prakCitraDigital\\projectAkhir\\README.md"
}

Read , lines 1 to 285
Completed with input: {
"path": "D:\\prakCitraDigital\\projectAkhir\\backend\\app\\image_processing.py",
"view_range": [
1,
285
]
}

Read
Completed with input: {
"path": "D:\\prakCitraDigital\\projectAkhir\\backend\\app\\main.py"
}

Read , lines 1 to 220
Completed with input: {
"path": "D:\\prakCitraDigital\\projectAkhir\\frontend\\index.html",
"view_range": [
1,
220
]
}

Aku belum bisa menyimpan file langsung dari mode ini, tapi ini draf yang bisa kamu salin ke `presentasi.md`. Isinya mengikuti implementasi sekarang—termasuk perbedaan antara deteksi wajah dan mask segmentasi.

````markdown
# Presentasi Proyek Akhir

## Sistem Penghitungan Orang pada Citra Menggunakan Segmentasi dan Analisis Kontur dengan Latar Terkendali

**Nama:** [Nama kamu]  
**NIM:** [NIM]  
**Mata kuliah:** Pengolahan Citra Digital  
**Dosen:** [Nama dosen]

---

## Slide 1 — Judul

**Sistem Penghitungan Orang pada Citra Menggunakan Segmentasi dan Analisis Kontur dengan Latar Terkendali**

- Implementasi berbasis website
- Python, OpenCV, FastAPI, HTML, Tailwind CSS, dan JavaScript

**Narasi:**  
“Pada proyek ini, saya membuat aplikasi web untuk mengunggah foto dan menampilkan hasil penghitungan orang beserta visualisasi proses pengolahan citranya.”

---

## Slide 2 — Latar Belakang

- Menghitung orang secara manual pada foto kelompok bisa memakan waktu.
- Pengolahan citra dapat digunakan untuk memisahkan objek dari latar dan menganalisis bentuk objek.
- Sistem berbasis kontur bekerja lebih baik pada latar yang terkendali.
- Foto nyata dapat memiliki latar yang kompleks atau orang yang saling menutupi.

**Narasi:**  
“Saya memilih topik ini untuk menerapkan konsep segmentasi dan analisis kontur pada masalah yang mudah dipahami, yaitu menghitung orang dari citra.”

---

## Slide 3 — Tujuan dan Batasan

### Tujuan

- Menerima gambar melalui halaman web.
- Menampilkan hasil deteksi dan mask segmentasi.
- Menghitung objek menggunakan kontur, dengan deteksi wajah sebagai koreksi untuk foto yang sesuai.

### Batasan

- Metode kontur mengasumsikan latar dan objek cukup berbeda.
- YuNet mendeteksi wajah yang terlihat; wajah tertutup atau membelakangi kamera dapat terlewat.
- Sistem ini merupakan demonstrasi pengolahan citra, bukan sistem pengawasan atau detektor orang untuk semua kondisi.

**Narasi:**  
“Targetnya adalah demonstrasi konsep pengolahan citra, bukan mengklaim hasil selalu akurat untuk semua jenis foto.”

---

## Slide 4 — Alur Sistem

1. Pengguna memilih atau mengunggah gambar.
2. Backend membaca gambar menggunakan OpenCV.
3. Warna median di tepi gambar dipakai untuk memperkirakan warna latar.
4. Jarak warna CIELAB digunakan untuk membentuk mask foreground.
5. Gaussian blur dan operasi morfologi membersihkan mask.
6. Kontur eksternal dianalisis untuk menghitung objek.
7. Jika YuNet mendeteksi sedikitnya dua wajah, kotak wajah dan hitungannya dipakai untuk hasil deteksi.
8. Website menampilkan jumlah, kotak deteksi, dan mask latar.

**Narasi:**  
“Segmentasi dan deteksi wajah adalah proses yang berbeda. Mask menunjukkan area foreground dan latar. Kotak wajah berasal dari model YuNet.”

---

## Slide 5 — Metode Pengolahan Citra

### Segmentasi dan kontur

- Mengestimasi latar dari piksel di tepi gambar.
- Menghitung perbedaan warna dalam ruang warna CIELAB.
- Membuat citra biner: foreground dan latar.
- Membersihkan mask menggunakan operasi morfologi.
- Mengambil kontur eksternal untuk menghitung objek.

### Deteksi wajah

- Menggunakan model YuNet melalui OpenCV.
- Menandai wajah dengan kotak pada citra asli.
- Digunakan sebagai koreksi hitungan saat beberapa wajah terdeteksi.

**Catatan:**  
Mask segmentasi latar bukan mask wajah. Mask ini tidak menunjukkan bentuk wajah secara khusus.

---

## Slide 6 — Arsitektur Aplikasi

```text
frontend/
├── index.html
├── css/style.css
└── js/app.js

backend/
├── app/
│   ├── main.py
│   └── image_processing.py
└── models/
    └── face_detection_yunet_2023mar.onnx
```
````

- **HTML, Tailwind CSS, dan JavaScript:** antarmuka dan unggah gambar.
- **FastAPI:** endpoint untuk menerima gambar dan mengirim hasil.
- **Python dan OpenCV:** segmentasi, kontur, deteksi wajah, dan anotasi.

**Narasi:**  
“Frontend dan backend dipisahkan. Browser mengirim gambar ke API FastAPI, lalu backend mengembalikan hasil untuk ditampilkan.”

---

## Slide 7 — Demo Aplikasi

1. Buka website di browser.
2. Pilih foto.
3. Klik **Mulai analisis**.
4. Tunjukkan jumlah hasil deteksi.
5. Pilih tab **Deteksi wajah** untuk melihat kotak dari YuNet.
6. Pilih tab **Mask latar** untuk melihat foreground putih dan latar hitam.
7. Jelaskan bahwa kedua visualisasi itu menunjukkan hal yang berbeda.

**Narasi:**  
“Pada foto kelompok ini, kotak hijau menunjukkan wajah yang dideteksi. Mask hitam-putih menunjukkan hasil segmentasi warna seluruh gambar, bukan segmentasi wajah.”

---

## Slide 8 — Pengujian dan Hasil

Pengujian fungsi dilakukan pada:

- Citra sintetis dengan dua objek terpisah.
- Citra sintetis dengan dua siluet yang bersentuhan.
- Citra sintetis dengan satu siluet.
- Beberapa contoh foto dengan jumlah wajah yang terlihat berbeda.

**Penting:**  
Hasil contoh tersebut menunjukkan fungsi pada beberapa masukan, bukan pengukuran akurasi menyeluruh. Untuk menyatakan akurasi, perlu dataset uji, label jumlah orang yang benar, dan pengukuran seperti akurasi hitung atau MAE.

---

## Slide 9 — Kelebihan dan Kekurangan

### Kelebihan

- Antarmuka sederhana: unggah gambar lalu analisis.
- Memperlihatkan hasil visual, tidak hanya angka.
- Memisahkan implementasi frontend dan backend.
- Menggabungkan materi segmentasi, morfologi, kontur, dan deteksi wajah.

### Kekurangan

- Hasil segmentasi warna sensitif terhadap variasi latar dan pencahayaan.
- Kontur yang menyatu dapat mewakili beberapa orang sekaligus.
- Deteksi wajah dapat gagal jika wajah kecil, miring, tertutup, atau membelakangi kamera.
- Belum dievaluasi pada dataset besar dengan ground truth.

---

## Slide 10 — Kesimpulan dan Pengembangan

### Kesimpulan

- Aplikasi berhasil menghubungkan website dengan backend FastAPI dan OpenCV.
- Segmentasi dan kontur dapat digunakan untuk menghitung objek pada kondisi yang sesuai.
- Deteksi wajah membantu memberi kotak yang lebih relevan pada foto kelompok dengan wajah terlihat.
- Mask segmentasi latar dan kotak deteksi wajah adalah dua hasil yang berbeda.

### Pengembangan berikutnya

- Menguji lebih banyak foto dengan variasi kondisi.
- Membuat dataset dan mengukur akurasi secara sistematis.
- Mengevaluasi metode pemisahan objek yang saling tumpang tindih.
- Menambahkan penjelasan dan indikator kualitas hasil di antarmuka.

**Penutup:**  
“Demikian presentasi proyek saya. Terima kasih. Saya siap menerima pertanyaan dan saran.”

---

## Pertanyaan yang Mungkin Ditanyakan

### Mengapa jumlah orang dan jumlah wajah bisa berbeda?

Karena sistem dapat gagal mendeteksi wajah yang tertutup, membelakangi kamera, atau terlalu kecil. Kontur juga bisa menggabungkan objek yang bersentuhan.

### Apakah mask hitam-putih menunjukkan wajah?

Tidak. Mask menunjukkan foreground dan latar berdasarkan perbedaan warna. Kotak deteksi wajah berasal dari YuNet.

### Mengapa menggunakan latar terkendali?

Perbedaan warna objek dan latar membuat segmentasi berbasis threshold lebih sederhana dan lebih mudah dianalisis.

### Apakah sistem ini sudah akurat untuk semua foto?

Belum. Sistem merupakan prototipe dan masih perlu diuji dengan dataset berlabel serta berbagai kondisi foto.

### Apa fungsi FastAPI?

FastAPI menyediakan endpoint agar frontend dapat mengirim gambar ke backend dan menerima hasil analisis.

### Apa fungsi analisis kontur?

Kontur merepresentasikan batas area pada citra biner. Kontur yang lolos penyaringan digunakan sebagai objek untuk dihitung.

```

```

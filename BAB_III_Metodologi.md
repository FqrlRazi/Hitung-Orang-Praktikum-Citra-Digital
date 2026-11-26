# BAB III
# METODOLOGI PENELITIAN DAN PERANCANGAN SISTEM

## 3.1 Metode Pengembangan

Proyek ini menggunakan pendekatan pengembangan sistem secara bertahap. Tahapan
dimulai dari identifikasi kebutuhan, perancangan alur dan arsitektur, implementasi
pengolahan citra dan aplikasi web, kemudian pengujian fungsional. Pendekatan ini
dipilih agar setiap bagian, mulai dari pembacaan citra sampai penyimpanan histori,
dapat diperiksa secara terpisah sebelum digunakan sebagai satu sistem.

Tahapan pengembangan yang dilakukan adalah sebagai berikut.

1. **Identifikasi kebutuhan**: menetapkan format citra, batas ukuran, hasil yang
   ditampilkan, kebutuhan histori, serta laporan PDF.
2. **Perancangan sistem**: merancang alur analisis, antarmuka, API, dan struktur
   data histori.
3. **Implementasi**: membuat frontend, backend, pemrosesan citra, pembuatan PDF,
   dan penyimpanan record.
4. **Pengujian**: menguji proses segmentasi dan penghitungan, validasi input,
   endpoint, histori, dan pembuatan laporan.
5. **Evaluasi**: mencatat keterbatasan hasil serta menentukan pengembangan
   selanjutnya.

## 3.2 Analisis Kebutuhan

### 3.2.1 Kebutuhan Fungsional

Kebutuhan fungsional sistem adalah:

1. Sistem menerima citra berformat JPG/JPEG, PNG, atau WebP.
2. Sistem menolak citra dengan ukuran lebih dari 10 MB dan citra yang resolusinya
   melebihi 25 megapiksel.
3. Sistem memperkirakan warna latar, membentuk mask foreground, dan membersihkan
   mask sebelum ekstraksi kontur.
4. Sistem mendeteksi wajah menggunakan model YuNet dan menentukan hasil utama
   berdasarkan jumlah wajah yang terdeteksi.
5. Sistem menampilkan jumlah hasil, metode deteksi, dimensi citra, visualisasi
   anotasi, mask latar, dan mask kotak wajah.
6. Sistem menyimpan metadata analisis beserta citra sumber dan citra hasil.
7. Sistem menyediakan dashboard untuk melihat statistik dan daftar histori.
8. Sistem dapat menghasilkan laporan PDF dari citra yang sedang dianalisis
   maupun dari record yang tersimpan.
9. PDF histori menyajikan rata-rata confidence wajah atau skor kecocokan bentuk
   dan perbandingan dengan record sebelumnya yang memiliki metode deteksi sama.

### 3.2.2 Kebutuhan Nonfungsional

1. Antarmuka dapat digunakan melalui peramban dan mendukung pemilihan file atau
   drag-and-drop.
2. Backend memvalidasi format, ukuran file, dan resolusi citra sebelum atau
   selama pemrosesan.
3. Gambar keluaran disimpan dalam format PNG untuk visualisasi hasil.
4. Penyimpanan lokal digunakan saat pengembangan. Pada Vercel, data histori
   disimpan pada private Vercel Blob agar tidak bergantung pada filesystem
   sementara.
5. Informasi confidence ditampilkan sebagai skor keluaran detektor, bukan
   sebagai klaim akurasi sistem.

### 3.2.3 Perangkat dan Perangkat Lunak

Perangkat lunak yang digunakan dalam pengembangan meliputi:

| Komponen | Perangkat lunak/teknologi |
|---|---|
| Bahasa pemrograman | Python |
| Pengolahan citra | OpenCV dan NumPy |
| Backend dan API | FastAPI |
| Antarmuka | HTML, Tailwind CSS, dan JavaScript |
| Pembuatan laporan | ReportLab |
| Penyimpanan deployment | Vercel Blob |
| Model deteksi wajah | YuNet FaceDetectorYN |
| Server pengembangan | Uvicorn |

Spesifikasi perangkat keras yang digunakan untuk menjalankan dan menguji aplikasi
dicantumkan sesuai perangkat aktual:

| Komponen | Spesifikasi |
|---|---|
| Prosesor | [isi sesuai perangkat yang digunakan] |
| Memori | [isi sesuai perangkat yang digunakan] |
| Sistem operasi | [isi sesuai perangkat yang digunakan] |
| Peramban | [isi nama dan versi peramban] |

## 3.3 Perancangan Sistem

### 3.3.1 Arsitektur Sistem

Sistem terdiri atas antarmuka frontend, backend FastAPI, modul pemrosesan citra,
model YuNet, dan penyimpanan histori. Frontend mengirim citra ke backend melalui
API. Backend memvalidasi dan menganalisis citra, lalu menyimpan record dan citra
hasil. Frontend menampilkan ringkasan hasil dan mengambil visualisasi dari
endpoint histori. Dashboard meminta daftar record dan menyediakan unduhan PDF
untuk setiap record.

```text
Pengguna
   |
   v
Frontend: index.html / app.js
   | unggah citra
   v
Backend FastAPI
   |-- validasi dan analisis citra
   |       |-- segmentasi, morfologi, kontur
   |       |-- deteksi wajah YuNet
   |-- penyimpanan record dan gambar
   |       |-- lokal: data/history
   |       `-- deployment: private Vercel Blob
   `-- API hasil, histori, gambar, dan PDF
           |
           +--> halaman hasil analisis
           `--> dashboard.html / dashboard.js
```

### 3.3.2 Perancangan Alur Analisis

Alur analisis satu citra dirancang sebagai berikut:

```text
Mulai
  |
Pilih atau tarik file citra
  |
Validasi format dan ukuran file
  |
Baca citra dan validasi resolusi
  |
Perkirakan warna latar dari piksel tepi
  |
Konversi ke CIELAB dan bentuk mask foreground
  |
Blur, threshold ulang, opening, dan closing
  |
Pisahkan komponen lebar yang berpotensi menyatu
  |
Ekstraksi dan klasifikasi kontur
  |
Deteksi wajah dengan YuNet
  |
Jika wajah >= 2: gunakan deteksi wajah sebagai hasil utama
Jika wajah < 2: gunakan hasil kontur sebagai hasil utama
  |
Buat citra anotasi dan mask kotak wajah
  |
Simpan record dan citra
  |
Tampilkan ringkasan, visualisasi, dan histori
  |
Selesai
```

### 3.3.3 Perancangan Antarmuka

Antarmuka utama menyediakan area pemilihan atau drag-and-drop citra, pratinjau,
tombol analisis, ringkasan jumlah hasil, visualisasi, serta tabel analisis.
Pengguna dapat memilih tampilan deteksi wajah/kontur, mask latar, atau mask
kotak wajah. Halaman dashboard menampilkan jumlah record, rata-rata hasil,
jumlah analisis dengan metode wajah, dan daftar histori dengan tombol **Unduh
PDF**.

## 3.4 Metode Pemrosesan Citra

### 3.4.1 Validasi dan Pembacaan Citra

Backend menerima file melalui endpoint `POST /api/analyze`. Format yang
diterima adalah JPEG, PNG, dan WebP, dengan batas unggahan 10 MB. Citra dibaca
menggunakan OpenCV. Jika file tidak dapat dibaca sebagai citra atau resolusinya
lebih dari 25 megapiksel, proses dihentikan dengan pesan kesalahan.

### 3.4.2 Estimasi Latar dan Segmentasi Warna

Sistem mengambil piksel pada pita tepi citra. Lebar pita ditentukan dari sekitar
seperdua puluh dimensi terkecil citra, dengan nilai minimum satu piksel. Nilai
median piksel tepi digunakan sebagai perkiraan warna latar.

Citra dan warna latar perkiraan dikonversi dari BGR ke CIELAB. Jarak warna setiap
piksel terhadap warna latar dihitung. Threshold dengan sensitivitas bawaan 35
digunakan untuk membentuk mask biner: piksel yang perbedaannya melebihi ambang
ditandai sebagai foreground, sedangkan piksel lain dianggap sebagai latar.

### 3.4.3 Pembersihan Mask dan Pemisahan Komponen

Mask hasil threshold diproses dengan Gaussian blur berukuran 5 × 5, lalu
di-threshold kembali. Operasi opening memakai kernel elips 3 × 3 untuk
mengurangi noise kecil, sedangkan closing memakai kernel elips 7 × 7 untuk
menutup celah kecil.

Komponen foreground yang lebar diperiksa lebih lanjut menggunakan transformasi
jarak dan watershed. Pemisahan dilakukan secara selektif jika ditemukan
puncak-puncak interior yang cukup jelas dan ukuran tiap wilayah hasil pemisahan
memenuhi batas minimum. Langkah ini dimaksudkan untuk membantu memisahkan
komponen yang menyatu, bukan menjamin semua objek yang bersentuhan selalu dapat
dipisahkan.

### 3.4.4 Ekstraksi dan Klasifikasi Kontur

Kontur eksternal diperoleh menggunakan `findContours`. Kontur dengan luas di
bawah batas minimum dibuang. Batas minimum ditetapkan sebesar 0,5% dari luas
total citra pada nilai bawaan sistem. Untuk setiap kontur yang lolos, sistem
menghitung bounding box, luas, circularity, dan rasio aspek. Pendekatan poligon
digunakan untuk menghitung jumlah titik/sisi, sementara ukuran dan geometri
kontur digunakan untuk mengklasifikasikan bentuk.

Bentuk kontur yang dapat diberikan antara lain segitiga, kotak, persegi panjang,
segi lima, segi enam, bulat, oval, lonjong, mendatar, dan tegak. Sistem juga
menghasilkan skor kecocokan bentuk berbasis ciri kontur. Skor ini adalah skor
heuristik, bukan nilai akurasi model terhadap label kebenaran.

### 3.4.5 Deteksi Wajah dengan YuNet

Model YuNet dimuat dari file ONNX yang disertakan pada project. Jika sisi
terpanjang citra melebihi 1.200 piksel, citra diperkecil secara proporsional
untuk proses deteksi. Parameter detektor yang digunakan adalah confidence
threshold 0,7, non-maximum suppression threshold 0,3, dan batas maksimum 5.000
deteksi. Koordinat kotak wajah dikembalikan ke skala citra asal.

Confidence wajah dari detektor dikonversi ke persentase. Jika YuNet menemukan
minimal dua wajah, hasil utama menggunakan deteksi wajah. Jika jumlahnya kurang
dari dua, hasil utama menggunakan kontur foreground. Mask kotak wajah tetap
dibentuk dari kotak deteksi YuNet yang ditemukan.

Untuk memperoleh karakteristik bentuk pada mode wajah, sistem menganalisis
area di sekitar kotak deteksi. Area tersebut dibatasi menggunakan elips dan
mask warna HSV serta YCrCb, kemudian dibersihkan dengan operasi morfologi.
Kontur terbesar dari mask tersebut dianalisis untuk mendapatkan bentuk dan
ciri geometrinya. Hasil ini bukan segmentasi wajah per piksel yang presisi.

### 3.4.6 Pembuatan Visualisasi dan Ringkasan

Sistem menggambar kotak dan nomor urut deteksi pada salinan citra asli.
Keluaran analisis mencakup citra anotasi, mask foreground/latar, mask kotak
wajah, jumlah hasil, metode deteksi, ukuran citra, warna latar perkiraan, dan
data deteksi. Citra keluaran dikodekan sebagai PNG untuk ditampilkan atau
disimpan.

## 3.5 Perancangan API dan Penyimpanan Data

### 3.5.1 Endpoint API

| Metode dan endpoint | Kegunaan |
|---|---|
| `GET /api/health` | Memeriksa status aplikasi |
| `POST /api/analyze` | Memvalidasi dan menganalisis citra, lalu menyimpan record |
| `POST /api/report/pdf` | Menghasilkan PDF dari citra yang dikirim |
| `GET /api/history` | Mengambil daftar record histori |
| `GET /api/history/{record_id}` | Mengambil detail satu record |
| `GET /api/history/{record_id}/image/{image_name}` | Mengambil citra sumber atau hasil yang tersimpan |
| `GET /api/history/{record_id}/report/pdf` | Menghasilkan PDF dari data record histori |

Permintaan analisis menggunakan `multipart/form-data`. Respons JSON analisis
memuat ringkasan dan identitas record. PDF dikirim sebagai respons
`application/pdf`.

### 3.5.2 Struktur Data Record

Setiap record menyimpan informasi berikut:

| Atribut | Keterangan |
|---|---|
| `id` | Identitas unik record |
| `created_at` | Waktu analisis dalam format ISO |
| `file_name` | Nama file sumber |
| `count` | Jumlah deteksi hasil utama |
| `detection_method` | Metode hasil utama: wajah atau kontur |
| `segmentation_method` | Keterangan metode segmentasi |
| `image_width`, `image_height` | Dimensi citra |
| `background_color` | Perkiraan warna latar dalam RGB |
| `detections` | Daftar hasil deteksi utama dan cirinya |
| `contour_detections` | Daftar hasil kontur |
| `files` | Referensi gambar asli, anotasi, mask, dan mask wajah |

### 3.5.3 Strategi Penyimpanan

Pada lingkungan lokal, metadata record disimpan dalam
`data/history/records.json`, sedangkan gambar disimpan sebagai file pada folder
`data/history`. Pada deployment Vercel, metadata dan gambar disimpan pada
private Vercel Blob. Koneksi Blob pada project Vercel menggunakan mekanisme OIDC
dan `BLOB_STORE_ID`. PDF histori dibuat saat diminta dari metadata dan gambar
yang tersimpan, sehingga file PDF tidak perlu disimpan sebagai record
permanen.

## 3.6 Rancangan Pengujian

Pengujian dilakukan untuk memeriksa fungsi utama sistem. Pengujian unit
pemrosesan citra menggunakan siluet sintetis yang dibentuk pada mask. Pengujian
integrasi memeriksa respons API, penyimpanan, pembacaan gambar, dan pembuatan
PDF. Hasil aktual dan bukti pengujian dicatat pada Bab IV.

| No. | Skenario | Hasil yang diharapkan |
|---:|---|---|
| 1 | Citra JPEG, PNG, atau WebP yang dapat dibaca | Citra diterima dan proses analisis berjalan |
| 2 | Format file tidak didukung | API mengembalikan status penolakan dan pesan yang sesuai |
| 3 | File lebih besar dari 10 MB | API mengembalikan status payload terlalu besar |
| 4 | Citra tidak dapat dibaca atau resolusi melebihi 25 MP | Analisis dihentikan dengan pesan validasi |
| 5 | Satu siluet sintetis | Sistem menghasilkan satu deteksi kontur |
| 6 | Dua siluet sintetis terpisah | Sistem menghasilkan dua deteksi |
| 7 | Dua siluet sintetis bersentuhan | Pemisahan watershed menghasilkan dua deteksi pada skenario uji |
| 8 | Citra berisi minimal dua wajah yang dapat dikenali | Metode hasil utama menggunakan YuNet dan kotak wajah |
| 9 | Citra berisi kurang dari dua wajah terdeteksi | Metode hasil utama menggunakan kontur |
| 10 | Mengakses histori dan gambar record | Record serta gambar yang tersimpan dapat diambil |
| 11 | Mengunduh PDF histori | PDF memuat hasil record dan ringkasan perbandingan skor |
| 12 | Menjalankan pada Vercel dengan Blob terhubung | Metadata dan gambar dapat disimpan serta dibaca dari Blob |

Pengujian fungsional tidak sama dengan pengujian akurasi. Untuk mengukur
akurasi penghitungan secara kuantitatif, diperlukan dataset citra dengan jumlah
wajah/orang sebenarnya sebagai ground truth. Dataset tersebut dan metrik
evaluasinya perlu dijelaskan pada Bab IV apabila pengukuran dilakukan.

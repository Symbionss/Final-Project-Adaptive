## 1. **Clone repositori** atau salin *source code* proyek ini ke dalam server utama Anda.
   ```bash
   git clone https://github.com/Symbionss/Final-Project-Adaptive
   cd Final-Project-Adaptive
   ```

2. **Jalankan Docker Compose** untuk build dan menjalankan semua service (Ryu, Web Django, Exporter, Prometheus, node-exporter, Grafana).
   ```bash
   docker-compose up -d --build
   ```

3. **Verifikasi Container**
   Pastikan semua container berhasil berjalan.
   ```bash
   docker-compose ps
   ```

4. **Keterbukaan Port (Firewall)**
   Pastikan *firewall* / *Security Group* server cloud Anda (misalnya AWS, GCP, atau VPS lokal) mengizinkan lalu lintas akses jaringan terbuka pada port berikut TCP:
   - **`6653`** (Komunikasi OpenFlow dari Mininet ke Ryu)
   - **`8080`** (Ryu REST API)
   - **`5000`** (Web Dashboard)
   - **`3000`** (Akses Grafana Dashboard)
   - **`9090`** (Akses Prometheus)

1. Siapkan file skrip topologi Mininet Anda (misalnya `topo_linear.py`). Pastikan pada di dalam skrip `topo_linear.py`, alamat **RemoteController** di-set menuju IP Publik (atau IP lokal) dari Server Utama Anda:
   ```python
   # Contoh cuplikan kode di dalam script mininet Python Anda
   net.addController('c0', controller=RemoteController, ip='103.183.74.87', port=6653)
   ```

2. Jalankan topologi menggunakan akses root (`sudo`):
   ```bash
   sudo python3 topo_linear.py
   ```

3. Mininet dan OVS akan otomatis terhubung melalui *OpenFlow handshake* ke Ryu Controller yang berjalan di Docker Server Utama.

---

## 🌐 Langkah 3: Mengakses Layanan (Akses Web dan Monitoring)

Setelah Controller dan Mininet saling tersambung, Anda dapat membuka browser dan mengakses berbagai fitur yang ada di arsitektur ini melalui tautan berikut:

1. **Web Dashboard SDN (Django)**
   - **URL:** `http://<IP_SERVER_UTAMA>:5000/`
   - Berfungsi untuk melihat topologi, melakukan manajemen L3 (memutus jaringan / *failover* / *disable* *port*), dsb.

2. **Grafana Monitoring Dashboard**
   - **URL:** `http://<IP_SERVER_UTAMA>:3000/`
   - **User Default:** `admin` | **Password:** `admin123`
   - Disini Anda dapat mengimpor data metrik jaringan (jumlah *switch*, aliran paket, kondisi *hardware server*, dsb) yang telah ditarik dengan Prometheus.

3. **Prometheus Metrics Database**
   - **URL:** `http://<IP_SERVER_UTAMA>:9090/`
   - Berfungsi memantau _endpoint_ *scrape target* (*exporter* & *node-exporter*) apakah berstatus `UP` secara keseluruhan.

4. **Ryu Controller (REST API Raw)**
   - **URL:** `http://<IP_SERVER_UTAMA>:8080/stats/switches` (contoh)
   - *Backend API* JSON, biasanya untuk ditarik (*hit*) datanya oleh aplikasi lain (seperti *Exporter* maupun *Web Dashboard*).

---

## 🛠 Menghentikan Layanan (Tear Down)

Jika Anda sudah selesai melakukan uji coba jaringan, berikut langkah untuk menghentikan _Service_:

1. **Mematikan Topologi Mininet**
   Pada terminal VM Mininet (Environment 2), ketik perintah: `exit` atau tekan `CTRL+C`, lalu bersihkan sisa konfigurasi OVS dengan perintah:
   ```bash
   sudo mn -c
   ```

2. **Mematikan Server Utama (Docker)**
   Dari direktori proyek tempat di mana file `docker-compose.yaml` Anda berada, matikan serta hapus container yang berjalan sekaligus:
   ```bash
   docker-compose down
   ```
   *(Opsional)* Jika Anda ingin menghapus volume data persisten (misalnya data login & dashboard Grafana agar reset kembali):
   ```bash
   docker-compose down -v
   ```

---
*Dokumen dasar ini juga didukung dengan `Dokumentasi_Arsitektur.md` pada repositori ini jika kamu memerlukan pandangan/desain Sistem yang lebih komprehensif tingkat lanjut.*

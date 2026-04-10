## 1. Menyiapkan dan Masuk ke Direktori Proyek
Pastikan Anda sudah berada di dalam VM atau server (VM1) yang akan menjalankan Controller dan sistem monitoring. Masuk ke direktori lokasi project berada:
```bash
cd sdn_monitoring
```
Direktori ini berisi konfigurasi untuk menjalankan SDN Controller (Ryu), Web Dashboard (Django), database metric (Prometheus), visualisasi (Grafana), dan Exporter.

## 2. Memastikan Docker dan Docker Compose Terinstall
Sistem ini menggunakan Docker untuk menjalankan seluruh layanannya secara terisolasi. Jika belum terinstall, Anda bisa menginstallnya dengan command berikut:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```
Setelah instalasi berhasil:
- Ekosistem Docker siap digunakan.
- Seluruh layanan jaringan siap dijalankan menggunakan docker-compose yang sudah dikonfigurasi tanpa harus install setup manual satu-persatu.

## 3. Review Konfigurasi Port Layanan (Opsional)
Pastikan port tidak ada yang bentrok di dalam host VM1. Di dalam `docker-compose.yaml`, layanan yang akan berjalan dan port yang digunakan adalah:
- **Ryu Controller**: Port `6653` (OpenFlow tcp listen) & `8080` (REST API).
- **Web Dashboard (Django)**: Port `5000` (Penamaan container: flask).
- **Prometheus**: Port `9090`.
- **Grafana**: Port `3000`.
- **Ryu Exporter**: Port `9100`.
- **Node Exporter**: Port `9101`.

*Catatan: Pastikan IP public/private dari server/VM1 ini dicatat dan digunakan pada pembuatan topologi Mininet di VM2 (pada bagian `net.addController(ip='<IP_VM1>')`).*

## 4. Menjalankan Seluruh Sistem Monitoring (Build and Run)
Jalankan command ini di dalam direktori `sdn_monitoring` untuk mem-build app dan menyalakan semua services:
```bash
sudo docker-compose up -d --build
```
Proses ini akan mengunduh docker images origin, mem-build web app, dan menyalakan infrastruktur lengkap. Penanda `-d` (detached mode) digunakan agar container berjalan di background dan terminal bisa digunakan untuk hal lain.

## 5. Mengecek Status Container
Untuk memverifikasi environment berjalan dengan benar:
```bash
sudo docker-compose ps
```
Atau:
```bash
sudo docker ps
```
Command ini dilakukan untuk:
- Memastikan semua container (ryu, flask, prometheus, grafana, node-exporter, exporter) berstatus **Up**.
- Memastikan tidak ada container yang crash/restart berkali-kali.

## 6. Mengakses Dashboard Antarmuka Web
Jika semua komponen telah aktif, Anda dapat mengakses platform monitoring langsung melalui browser. *(Ganti `<IP_VM1>` dengan IP server/VM1 tempat docker ini berjalan)*:

### A. Web Dashboard Management (Django)
```text
http://<IP_VM1>:5000
```
- Merupakan dashboard utama untuk melihat topologi secara visual.
- Digunakan untuk kontrol jaringan (Cut/Restore link, Block/Unblock IP host).

### B. Grafana Analytics
```text
http://<IP_VM1>:3000
```
- Username Default: `admin`
- Password Default: `admin123`
- Digunakan untuk memantau analitik metrics lebih mendalam melalui grafik series untuk node dan network.

### C. Prometheus Data Source
```text
http://<IP_VM1>:9090
```
- Sistem di balik Grafana. Anda bisa melihat status target terhubung (exporter dan ryu metrics).

## 7. Melakukan Debugging & Log Tracing
### A. Mengecek Log Ryu Controller
Jika Mininet pada VM2 susah terhubung ke Controller VM1 atau gagal konek OpenFlow:
```bash
sudo docker logs ryu -f
```

### B. Mengecek Log Web Aplikasi
Jika terdapat error saat mengakses Web UI Dashboard, atau memantau hasil eksekusi request controller:
```bash
sudo docker logs flask -f
```
*(Gunakan `CTRL+C` untuk keluar dari live logs mode `-f`)*

## 8. Menghentikan Instalasi dan Environment
Jika Anda perlu memberhentikan service untuk debugging atau reset log monitoring:
```bash
sudo docker-compose down
```
Jika ingin menghapus seluruh system *termasuk membuang data database grafana* yang tersimpan di volume:
```bash
sudo docker-compose down -v
```




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

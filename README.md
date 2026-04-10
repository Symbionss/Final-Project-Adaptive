# Final-Project-Adaptive
# Deskripsi
Project ini merupakan implementasi Software Defined Networking (SDN) menggunakan Ryu Controller, Mininet, dan Open vSwitch (OVS) yang dijalankan pada lingkungan terpisah (VM dan cloud server). Sistem ini dirancang untuk mensimulasikan jaringan dengan kontrol terpusat serta mendukung monitoring secara real-time menggunakan Prometheus dan Grafana.

Topologi jaringan yang digunakan adalah linear topology dengan tiga switch utama (Edge–Core–Edge) yang menghubungkan dua subnet berbeda. Controller Ryu dikonfigurasi untuk mengelola jaringan dengan pendekatan hybrid antara Layer 2 switching dan Layer 3 switching, serta dilengkapi dengan mekanisme flow timeout dan backup link untuk meningkatkan keandalan jaringan.

Selain itu, proyek ini juga mencakup fitur monitoring berbasis web yang mampu menampilkan kondisi jaringan secara real-time, termasuk statistik bandwidth dan status node. Implementasi ini bertujuan untuk memberikan pemahaman praktis mengenai konsep SDN, manajemen flow, serta observability dalam jaringan modern.

# Anggota Kelompok
Apip
Kepin
Sion
Nopal

# Topologi soal
screenshots/topologi_soal.png

//Supaya gampang, anggap GitHub-mu minimal harus punya:
README.md
folder docs/
folder screenshots/
folder controller/
folder topology/
folder monitoring/
folder testing/

# Requirenment
Requirenments yang di butuhkan untuk project ini berupa:
- Ryu Controller untuk mengontrol jaringan
- Django sebagai sistem web basenya
- Grafana + Prometheus untuk visualisasi data
- Mininet untuk simulasi jaringan

# Arsitektur Sistem

# Implementasi 
## VM 1 – Control Plane (Cloud Server)
Berfungsi sebagai pusat kontrol jaringan
Menjalankan:
- Ryu Controller (dalam Docker container)
-Prometheus
- Grafana
- Django Web Server
  
## VM 2 – Data Plane
Berfungsi sebagai simulasi jaringan
Menjalankan:
- Mininet
- Open vSwitch (OVS)

# Topologi Jaringan
Menggunakan 3 switch dan 6 host dengan spesifikasi yang berbeda:
**Switch**
- S1 sebagai edge A
- S2 Sebagai core switch
- S3 sebagai edge B
(koneksi main link antar switch 100Mbps dengan
koneksi backup link antar switch 50Mbps) 
**Host**
- H1 H2 H3 terhubung pada edge A
- H4 H5 H6 terhubung pada edge B
(Koneksi link host dan switch 10Mpbs)

# Mekanisme Kerja Sistem
- Mininet membuat topologi jaringan di VM 2
- Switch (OVS) terhubung ke Ryu Controller di VM 1 melalui protokol OpenFlow
- Ryu Controller:
    <br> - Mengatur flow jaringan
    <br> - Mengumpulkan data traffic data dan dikirim ke Prometheus
- Grafana menampilkan data dalam bentuk dashboard
- Django menyediakan interface monitoring berbasis web

# Fitur Utama
Dengan beberapa fitur sebagai berikut
- Mengelola jaringan dari web interface
- Monitoring traffic real-time (latency, jitter, throughput)
- Visualisasi topologi jaringan
- Backup link untuk simulasi failover
- Grafana Dashboard

screenshots/web

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
  Penelitian ini mengunakan 2 buah virtual machine (VM) dengan sistem operasi Ubuntu 22.04 yang dimana VM 1 dialihkan ke hosting server dari provider IDCloudHost. Sedangkan VM2 berperan sebagai data plane yang menjalankan Mininet dan Open vSwitch  dengan spesifikasi yang sama. Kedua VM terhubung dalam satu jaringan internal yang sama dengan alamat IP 103.183.74.87 untuk VM 1 (Cloud Server) dan 192.168.56.20 untuk VM 2. Proses instalasi Docker dan Ryu sebagai controller dijalankan di VM 1 yang merupakan "penampung" dari controller yang dijalankan sebagai container Docker. Sedangkan pada VM 2, instalasi Mininet dan Open vSwitch yang berfungsi untuk membuat topologi  jaringan dengan melakukan pendekatan 3 switch (S) yaitu S1 sebagai Edge – A , S2 sebagai core, dan S3 sebagai Edge – B. Selanjutnya topologi akan memuat 6 host (H) yang terbagi atas 2 subnet dengan IP 10.0.1.0/24 untuk H1, H2, H5 yang terhubung dengan S1 dan IP 10.0.2.0/24 untuk H3,  H4,  H6 yang terhubung dengan S3.  Link antar switch menggunakan bandwidth 100mbps, sedangkan link host ke switch menggunakan 10mbps. Selain itu, disediakan backup link langsung antara S1 dan S3 dengan bandwidth setengah dari main link, yaitu 50mbps.
# Deployment

# Hasil

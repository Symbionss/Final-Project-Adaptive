1. Menginstall openvswitch dan mininet kedalam perangkat (vm2 ubuntu)
```
sudo apt install openvswitch-switch mininet -y
```
Setelah instalasi berhasil:
- Open vSwitch siap digunakan sebagai switch SDN
- Mininet bisa digunakan untuk membuat topologi jaringan virtual.

2. Membuat topology python.
```
sudo nano topologi.py
```
3. Isi file tersebut dengan command ini:
```
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink


class MyTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Subnet A di S1
        h1 = self.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.1.1/24', defaultRoute='via 10.0.1.254')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.1.2/24', defaultRoute='via 10.0.1.254')
        h5 = self.addHost('h5', mac='00:00:00:00:00:05', ip='10.0.1.5/24', defaultRoute='via 10.0.1.254')

        # Subnet B di S3
        h3 = self.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.2.3/24', defaultRoute='via 10.0.2.254')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.2.4/24', defaultRoute='via 10.0.2.254')
        h6 = self.addHost('h6', mac='00:00:00:00:00:06', ip='10.0.2.6/24', defaultRoute='via 10.0.2.254')

        # Host ke switch = 10 Mbps
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h5, s1, cls=TCLink, bw=10)

        self.addLink(h3, s3, cls=TCLink, bw=10)
        self.addLink(h4, s3, cls=TCLink, bw=10)
        self.addLink(h6, s3, cls=TCLink, bw=10)

        # Main link = 100 Mbps
        self.addLink(s1, s2, cls=TCLink, bw=100)
        self.addLink(s2, s3, cls=TCLink, bw=100)

        # Backup link = 50 Mbps
        self.addLink(s1, s2, cls=TCLink, bw=50)
        self.addLink(s2, s3, cls=TCLink, bw=50)


def run():
    topo = MyTopo()
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )

    net.addController(
        'c0',
        controller=RemoteController,
        ip='103.183.74.87',
        port=6653
    )

    net.start()

    for sw in ['s1', 's2', 's3']:
        net.get(sw).cmd(f'ovs-vsctl set bridge {sw} protocols=OpenFlow13')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
```
Ketika dijalankan, file ini akan otomatis membuat mininet switch dan host dengan link bandwidth dan ip yang berbeda masing", juga menghubungkan mininet ke ryu controller dimana pada bagian `net.addController(ip='')` masukan ip dari server/vm1 tempat beradanya ryu controllernya.

4. Jalankan topologi yang sudah dibuat.
```
sudo python3 topologi.py
```
5. Melakukan ping pada host didalam mininet.
```
mininet> pingall
mininet> h1 ping -c 3 h2
mininet> h1 ping -c 3 h6
```
6. Mengecek apakah server/vm1 sudah terkoneksi dengan vm2.
```
sh ovs-vsctl
```
Command ini dilakukan untuk:
- Memastikan switch sudah berhasil dibuat
- Mengecek apakah switch sudah terhubung ke controller
- Melihat struktur koneksi antar switch dan host

> Untuk keluar dari mininet gunakan command `mininet> exit`

7. Membuktikan 4 konsep logika controller dalam mininet.
```

```

8. Menghapus sisa environment mininet sebelumnya.
```
sudo mn -c 
```

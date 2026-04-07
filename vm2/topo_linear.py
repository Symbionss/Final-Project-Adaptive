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

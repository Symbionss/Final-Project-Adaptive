from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
import json
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp, ipv4, icmp, tcp, udp
from ryu.lib.packet import ether_types


class L3ICMPRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(L3ICMPRouter, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        wsgi.register(L3Controller, {'app': self})

        # Simpan datapath aktif untuk flush flow saat failover
        self.logger.info("CONTROLLER API AKTIF")
        self.datapaths = {}

        # Virtual gateway
        self.gw_ip_a = '10.0.1.254'
        self.gw_ip_b = '10.0.2.254'
        self.gw_mac_a = '00:00:00:00:01:fe'
        self.gw_mac_b = '00:00:00:00:02:fe'

        # MAC host (autoSetMacs=True)
        self.host_macs = {
            '10.0.1.1': '00:00:00:00:00:01',
            '10.0.1.2': '00:00:00:00:00:02',
            '10.0.1.5': '00:00:00:00:00:05',
            '10.0.2.3': '00:00:00:00:00:03',
            '10.0.2.4': '00:00:00:00:00:04',
            '10.0.2.6': '00:00:00:00:00:06',
        }

        # Host ports pada edge switch
        # s1: h1=1, h2=2, h5=3, s2-main=4, s2-backup=5
        # s2: s1-main=1, s3-main=2, s1-backup=3, s3-backup=4
        # s3: h3=1, h4=2, h6=3, s2-main=4, s2-backup=5
        self.host_ports = {
            1: {
                '10.0.1.1': 1,
                '10.0.1.2': 2,
                '10.0.1.5': 3,
            },
            3: {
                '10.0.2.3': 1,
                '10.0.2.4': 2,
                '10.0.2.6': 3,
            }
        }

        # Main dan backup link
        self.main_uplink_ports = {
            1: 4,  # s1 -> s2 main
            2: {
                '10.0.1.0/24': 1,  # s2 -> s1 main
                '10.0.2.0/24': 2,  # s2 -> s3 main
            },
            3: 4,  # s3 -> s2 main
        }

        self.backup_uplink_ports = {
            1: 5,  # s1 -> s2 backup
            2: {
                '10.0.1.0/24': 3,  # s2 -> s1 backup
                '10.0.2.0/24': 4,  # s2 -> s3 backup
            },
            3: 5,  # s3 -> s2 backup
        }

        # Status uplink: default pakai main
        self.main_link_up = {
            1: True,
            2: {
                '10.0.1.0/24': True,
                '10.0.2.0/24': True,
            },
            3: True,
        }

    # =========================
    # Datapath registry
    # =========================
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
                self.logger.info("REGISTER datapath dpid=%s", datapath.id)
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]
                self.logger.info("UNREGISTER datapath dpid=%s", datapath.id)

    # =========================
    # Flow helpers
    # =========================
    def add_flow(self, datapath, priority, match, actions,
                 buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions
            )
        ]

        if buffer_id is not None and buffer_id != ofproto.OFP_NO_BUFFER:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
                idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst,
                idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )

        datapath.send_msg(mod)

    def delete_dynamic_flows(self, datapath):
        """Hapus semua flow dinamis, sisakan table-miss dan flow prioritas sangat tinggi."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=0,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=parser.OFPMatch()
        )
        datapath.send_msg(mod)

        self.logger.info("DELETE dynamic flows on dpid=%s", datapath.id)

        # Pasang lagi table-miss
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]
        self.add_flow(datapath, 0, match, actions)

    def flush_all_dynamic_flows(self):
        for dpid, dp in self.datapaths.items():
            self.delete_dynamic_flows(dp)
        self.logger.info("FLUSH all datapaths complete")

    # =========================
    # Initial switch features
    # =========================
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.datapaths[datapath.id] = datapath

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]
        self.add_flow(datapath, 0, match, actions)

    # =========================
    # Backup link failover
    # =========================
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        reason = msg.reason
        port_no = msg.desc.port_no
        ofproto = datapath.ofproto

        link_down = bool(msg.desc.state & ofproto.OFPPS_LINK_DOWN)

        changed = False

        # s1
        if dpid == 1 and port_no == self.main_uplink_ports[1]:
            old = self.main_link_up[1]
            self.main_link_up[1] = not link_down
            changed = (old != self.main_link_up[1])

        # s2
        elif dpid == 2:
            if port_no == self.main_uplink_ports[2]['10.0.1.0/24']:
                old = self.main_link_up[2]['10.0.1.0/24']
                self.main_link_up[2]['10.0.1.0/24'] = not link_down
                changed = (old != self.main_link_up[2]['10.0.1.0/24'])
            elif port_no == self.main_uplink_ports[2]['10.0.2.0/24']:
                old = self.main_link_up[2]['10.0.2.0/24']
                self.main_link_up[2]['10.0.2.0/24'] = not link_down
                changed = (old != self.main_link_up[2]['10.0.2.0/24'])

        # s3
        elif dpid == 3 and port_no == self.main_uplink_ports[3]:
            old = self.main_link_up[3]
            self.main_link_up[3] = not link_down
            changed = (old != self.main_link_up[3])

        self.logger.info(
            "PORT_STATUS dpid=%s port=%s reason=%s link_down=%s changed=%s",
            dpid, port_no, reason, link_down, changed
        )

        if changed:
            self.logger.info("FAILOVER state updated: %s", self.main_link_up)
            self.flush_all_dynamic_flows()

    def active_uplink_port(self, dpid, subnet_key=None):
        if dpid == 1:
            return self.main_uplink_ports[1] if self.main_link_up[1] else self.backup_uplink_ports[1]

        if dpid == 2:
            if subnet_key is None:
                return None
            return (
                self.main_uplink_ports[2][subnet_key]
                if self.main_link_up[2][subnet_key]
                else self.backup_uplink_ports[2][subnet_key]
            )

        if dpid == 3:
            return self.main_uplink_ports[3] if self.main_link_up[3] else self.backup_uplink_ports[3]

        return None

    # =========================
    # Packet crafting
    # =========================
    def send_raw_packet(self, datapath, out_port, data):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=data
        )
        datapath.send_msg(out)

    def send_arp_reply(self, datapath, src_mac, src_ip, dst_mac, dst_ip, out_port):
        e = ethernet.ethernet(
            dst=dst_mac,
            src=src_mac,
            ethertype=ether_types.ETH_TYPE_ARP
        )
        a = arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=src_mac,
            src_ip=src_ip,
            dst_mac=dst_mac,
            dst_ip=dst_ip
        )

        p = packet.Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        self.send_raw_packet(datapath, out_port, p.data)

    # =========================
    # Forwarding logic
    # =========================
    def arp_target_port(self, dpid, dst_ip):
        if dpid == 1:
            if dst_ip in self.host_ports[1]:
                return self.host_ports[1][dst_ip]
            if dst_ip.startswith('10.0.2.'):
                return self.active_uplink_port(1)

        elif dpid == 2:
            if dst_ip.startswith('10.0.1.'):
                return self.active_uplink_port(2, '10.0.1.0/24')
            if dst_ip.startswith('10.0.2.'):
                return self.active_uplink_port(2, '10.0.2.0/24')

        elif dpid == 3:
            if dst_ip in self.host_ports[3]:
                return self.host_ports[3][dst_ip]
            if dst_ip.startswith('10.0.1.'):
                return self.active_uplink_port(3)

        return None

    def build_actions(self, parser, dpid, src_ip, dst_ip):
        # s1
        if dpid == 1:
            if dst_ip in self.host_ports[1]:
                if src_ip.startswith('10.0.1.'):
                    return [parser.OFPActionOutput(self.host_ports[1][dst_ip])]
                return [
                    parser.OFPActionSetField(eth_src=self.gw_mac_a),
                    parser.OFPActionSetField(eth_dst=self.host_macs[dst_ip]),
                    parser.OFPActionOutput(self.host_ports[1][dst_ip])
                ]

            if dst_ip.startswith('10.0.2.'):
                return [parser.OFPActionOutput(self.active_uplink_port(1))]

        # s2
        elif dpid == 2:
            if dst_ip.startswith('10.0.1.'):
                return [parser.OFPActionOutput(self.active_uplink_port(2, '10.0.1.0/24'))]
            if dst_ip.startswith('10.0.2.'):
                return [parser.OFPActionOutput(self.active_uplink_port(2, '10.0.2.0/24'))]

        # s3
        elif dpid == 3:
            if dst_ip in self.host_ports[3]:
                if src_ip.startswith('10.0.2.'):
                    return [parser.OFPActionOutput(self.host_ports[3][dst_ip])]
                return [
                    parser.OFPActionSetField(eth_src=self.gw_mac_b),
                    parser.OFPActionSetField(eth_dst=self.host_macs[dst_ip]),
                    parser.OFPActionOutput(self.host_ports[3][dst_ip])
                ]

            if dst_ip.startswith('10.0.1.'):
                return [parser.OFPActionOutput(self.active_uplink_port(3))]

        return None

    # =========================
    # Packet-In handler
    # =========================
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        # ---------- ARP ----------
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            if arp_pkt.opcode == arp.ARP_REQUEST:
                if arp_pkt.dst_ip == self.gw_ip_a:
                    self.send_arp_reply(
                        datapath,
                        self.gw_mac_a,
                        self.gw_ip_a,
                        arp_pkt.src_mac,
                        arp_pkt.src_ip,
                        in_port
                    )
                    return

                if arp_pkt.dst_ip == self.gw_ip_b:
                    self.send_arp_reply(
                        datapath,
                        self.gw_mac_b,
                        self.gw_ip_b,
                        arp_pkt.src_mac,
                        arp_pkt.src_ip,
                        in_port
                    )
                    return

            out_port = self.arp_target_port(dpid, arp_pkt.dst_ip)
            if out_port is not None:
                actions = [parser.OFPActionOutput(out_port)]
                data = msg.data

                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=in_port,
                    actions=actions,
                    data=data
                )
                datapath.send_msg(out)
            return

        # ---------- IPv4 ----------
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if not ip_pkt:
            return

        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst

        actions = self.build_actions(parser, dpid, src_ip, dst_ip)
        if actions is None:
            return

        # ---------- ICMP = Layer 3 ----------
        icmp_pkt = pkt.get_protocol(icmp.icmp)
        if icmp_pkt:
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=1,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip
            )

            self.add_flow(
                datapath=datapath,
                priority=10,
                match=match,
                actions=actions,
                buffer_id=msg.buffer_id,
                idle_timeout=30,
                hard_timeout=120
            )

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=data
            )
            datapath.send_msg(out)
            return

        # ---------- TCP ----------
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        if tcp_pkt:
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=6,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip,
                tcp_src=tcp_pkt.src_port,
                tcp_dst=tcp_pkt.dst_port
            )

            self.add_flow(
                datapath=datapath,
                priority=20,
                match=match,
                actions=actions,
                buffer_id=msg.buffer_id,
                idle_timeout=30,
                hard_timeout=120
            )

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=data
            )
            datapath.send_msg(out)
            return

        # ---------- UDP ----------
        udp_pkt = pkt.get_protocol(udp.udp)
        if udp_pkt:
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=17,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip,
                udp_src=udp_pkt.src_port,
                udp_dst=udp_pkt.dst_port
            )

            self.add_flow(
                datapath=datapath,
                priority=20,
                match=match,
                actions=actions,
                buffer_id=msg.buffer_id,
                idle_timeout=30,
                hard_timeout=120
            )

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=data
            )
            datapath.send_msg(out)
            return

class L3Controller(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(L3Controller, self).__init__(req, link, data, **config)
        self.app = data['app']

    @route('l3', '/block_ip', methods=['POST'])
    def block_ip(self, req, **kwargs):
        try:
            body = json.loads(req.body)
            ip = body.get('ip')

            if not ip:
                return Response(
                    content_type='application/json',
                    body=json.dumps({'error': 'IP tidak diberikan'})
                )

            for dp in self.app.datapaths.values():
                parser = dp.ofproto_parser

                self.app.logger.info(
                    "[API] BLOCK IP: %s di dpid %s" % (ip, dp.id)
                )

                match = parser.OFPMatch(
                    eth_type=0x0800,
                    ipv4_src=ip
                )

                actions = []  # DROP

                self.app.add_flow(
                    datapath=dp,
                    priority=100,
                    match=match,
                    actions=actions
                )

            return Response(
                content_type='application/json',
                body=json.dumps({'status': '%s blocked' % ip})
            )

        except Exception as e:
            return Response(
                content_type='application/json',
                body=json.dumps({'error': str(e)})
            )

    @route('l3', '/unblock_ip', methods=['POST'])
    def unblock_ip(self, req, **kwargs):
        try:
            body = json.loads(req.body)
            ip = body.get('ip')

            if not ip:
                return Response(
                    content_type='application/json',
                    body=json.dumps({'error': 'IP tidak diberikan'})
                )

            for dp in self.app.datapaths.values():
                parser = dp.ofproto_parser
                ofproto = dp.ofproto



                match = parser.OFPMatch(
                    eth_type=0x0800,
                    ipv4_src=ip
                )

                mod = parser.OFPFlowMod(
                    datapath=dp,
                    command=ofproto.OFPFC_DELETE,
                    out_port=ofproto.OFPP_ANY,
                    out_group=ofproto.OFPG_ANY,
                    match=match
                )

                dp.send_msg(mod)

            return Response(
                content_type='application/json',
                body=json.dumps({'status': '%s blocked' % ip})
            )

        except Exception as e:
            return Response(
                content_type='application/json',
                body=json.dumps({'error': str(e)})
            )
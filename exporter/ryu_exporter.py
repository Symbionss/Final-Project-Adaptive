from prometheus_client import start_http_server, Gauge
import requests
import time

# Basic metrics
flow_count   = Gauge('sdn_flow_count',   'Number of flows in switches')
switch_count = Gauge('sdn_switch_count', 'Number of switches')

# Per-port traffic metrics
port_tx_bytes   = Gauge('sdn_port_tx_bytes',   'TX bytes per port', ['dpid', 'port'])
port_rx_bytes   = Gauge('sdn_port_rx_bytes',   'RX bytes per port', ['dpid', 'port'])
port_tx_packets = Gauge('sdn_port_tx_packets', 'TX packets per port', ['dpid', 'port'])
port_rx_packets = Gauge('sdn_port_rx_packets', 'RX packets per port', ['dpid', 'port'])
port_tx_errors  = Gauge('sdn_port_tx_errors',  'TX errors per port', ['dpid', 'port'])
port_rx_dropped = Gauge('sdn_port_rx_dropped', 'RX dropped per port', ['dpid', 'port'])

RYU_REST = "http://ryu:8080"

def collect_metrics():
    try:
        r = requests.get(RYU_REST + "/stats/switches", timeout=5)
        switches = r.json()
        switch_count.set(len(switches))

        total_flows = 0
        for sw in switches:
            # Flow stats
            try:
                r_flow = requests.get(f"{RYU_REST}/stats/flow/{sw}", timeout=5)
                flows = r_flow.json()
                if str(sw) in flows:
                    total_flows += len(flows[str(sw)])
            except Exception:
                pass

            # Port stats
            try:
                r_port = requests.get(f"{RYU_REST}/stats/port/{sw}", timeout=5)
                port_data = r_port.json()
                dpid_str = str(sw)
                if dpid_str in port_data:
                    for p in port_data[dpid_str]:
                        port_no = str(p.get('port_no', '?'))
                        if port_no == '4294967294':  # Skip LOCAL port
                            continue
                        labels = {'dpid': dpid_str, 'port': port_no}
                        port_tx_bytes.labels(**labels).set(p.get('tx_bytes', 0))
                        port_rx_bytes.labels(**labels).set(p.get('rx_bytes', 0))
                        port_tx_packets.labels(**labels).set(p.get('tx_packets', 0))
                        port_rx_packets.labels(**labels).set(p.get('rx_packets', 0))
                        port_tx_errors.labels(**labels).set(p.get('tx_errors', 0))
                        port_rx_dropped.labels(**labels).set(p.get('rx_dropped', 0))
            except Exception as e:
                print(f"Port stats error sw{sw}:", e)

        flow_count.set(total_flows)
        print(f"Switches: {len(switches)}, Flows: {total_flows}")

    except Exception as e:
        print("Error collecting metrics:", e)


if __name__ == "__main__":
    start_http_server(9100)
    print("Exporter running on port 9100")
    while True:
        collect_metrics()
        time.sleep(5)
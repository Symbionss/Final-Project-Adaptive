from prometheus_client import start_http_server, Gauge
import requests
import time

flow_count = Gauge('sdn_flow_count', 'Number of flows in switches')
switch_count = Gauge('sdn_switch_count', 'Number of switches')

RYU_REST = "http://ryu:8080"

def collect_metrics():
    try:

        r = requests.get(RYU_REST + "/stats/switches")
        switches = r.json()

        print("Switch list:", switches)

        switch_count.set(len(switches))

        total_flows = 0

        for sw in switches:

            r = requests.get(f"{RYU_REST}/stats/flow/{sw}")
            flows = r.json()

            if str(sw) in flows:
                total_flows += len(flows[str(sw)])

        flow_count.set(total_flows)

        print("Total flows:", total_flows)

    except Exception as e:
        print("Error collecting metrics:", e)


if __name__ == "__main__":

    start_http_server(9100)

    print("Exporter running on port 9100")

    while True:
        collect_metrics()
        time.sleep(5)
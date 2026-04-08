import json
import re
import subprocess
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

RYU_API = settings.RYU_API

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def block_ip(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip')
            
            if not ip:
                return JsonResponse({'status': 'error', 'message': 'IP tidak diberikan'}, status=400)
                
            resp = requests.post(f'{RYU_API}/block_ip', json={'ip': ip}, timeout=5)
            
            return JsonResponse({
                'status': 'success',
                'action': 'block',
                'ip': ip,
                'ryu_response': resp.json()
            })
        except requests.exceptions.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Gagal ke Ryu: {str(e)}'}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def unblock_ip(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip')
            
            if not ip:
                return JsonResponse({'status': 'error', 'message': 'IP tidak diberikan'}, status=400)
                
            resp = requests.post(f'{RYU_API}/unblock_ip', json={'ip': ip}, timeout=5)
            
            return JsonResponse({
                'status': 'success',
                'action': 'unblock',
                'ip': ip,
                'ryu_response': resp.json()
            })
        except requests.exceptions.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Gagal ke Ryu: {str(e)}'}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def api_topology(request):
    """
    Fetch topology data from Ryu controller
    """
    try:
        switches_resp = requests.get(f'{RYU_API}/v1.0/topology/switches', timeout=5)
        links_resp = requests.get(f'{RYU_API}/v1.0/topology/links', timeout=5)
        hosts_resp = requests.get(f'{RYU_API}/v1.0/topology/hosts', timeout=5)
        
        return JsonResponse({
            'status': 'success',
            'switches': switches_resp.json() if switches_resp.status_code == 200 else [],
            'links': links_resp.json() if links_resp.status_code == 200 else [],
            'hosts': hosts_resp.json() if hosts_resp.status_code == 200 else []
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to connect to Ryu: {str(e)}',
            'switches': [],
            'links': [],
            'hosts': []
        }, status=500)

def api_traffic_stats(request):
    """
    Fetch port stats from Ryu controller to calculate traffic bytes.
    Queries switches 1, 2, and 3.
    """
    try:
        stats = {}
        for dpid in [1, 2, 3]:
            resp = requests.get(f'{RYU_API}/stats/port/{dpid}', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                # Ryu returns {"1": [{"port_no": 1, "tx_bytes": ..., "rx_bytes": ...}, ...]}
                str_dpid = str(dpid)
                if str_dpid in data:
                    stats[str_dpid] = {}
                    for port_stat in data[str_dpid]:
                        port_no = port_stat.get('port_no')
                        if port_no != 'LOCAL':
                            # Normalisasi DPID ke format panjang untuk konsistensi dengan UI (e.g. "0000000000000001")
                            dpid_hex = str(dpid).zfill(16)
                            port_hex = str(port_no).zfill(8)
                            tx = port_stat.get('tx_bytes', 0)
                            rx = port_stat.get('rx_bytes', 0)
                            
                            if dpid_hex not in stats:
                                stats[dpid_hex] = {}
                            stats[dpid_hex][port_hex] = {'tx': tx, 'rx': rx}

        return JsonResponse({
            'status': 'success',
            'stats': stats
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to fetch traffic stats: {str(e)}',
            'stats': {}
        }, status=500)

@csrf_exempt
def api_port_control(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dpid = int(data.get('dpid', 0))
            port_no = int(data.get('port_no', 0))
            action = data.get('action') # 'down' or 'up'
            
            if not dpid or not port_no or action not in ['up', 'down']:
                return JsonResponse({'status': 'error', 'message': 'Invalid parameters'}, status=400)
                
            config_val = 1 if action == 'down' else 0
            
            payload = {
                "dpid": dpid,
                "port_no": port_no,
                "config": config_val,
                "mask": 1
            }
            
            response = requests.post(f"{RYU_API}/stats/portdesc/modify", json=payload, timeout=5)
            response.raise_for_status()
            
            return JsonResponse({'status': 'success', 'message': f'Port {port_no} on Switch {dpid} set to {action.upper()}'})
        except requests.exceptions.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Ryu REST failure: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def api_ping_test(request):
    """
    Run a ping test between two hosts.
    Accepts JSON: { source: '10.0.0.1', destination: '10.0.0.2', count: 10 }
    Returns latency (min/avg/max), jitter, throughput, packet loss.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        source = data.get('source', '')
        destination = data.get('destination', '')
        count = int(data.get('count', 10))

        if not source or not destination:
            return JsonResponse({'status': 'error', 'message': 'Source and destination required'}, status=400)

        if count < 1 or count > 100:
            count = 10

        # Try ping via the system (works when Django runs on the same host as Mininet)
        # Use ping with count and specific packet size
        try:
            result = subprocess.run(
                ['ping', '-c', str(count), '-s', '64', '-W', '2', destination],
                capture_output=True, text=True, timeout=count * 3 + 10
            )
            raw_output = result.stdout + result.stderr
        except FileNotFoundError:
            # Windows fallback
            try:
                result = subprocess.run(
                    ['ping', '-n', str(count), '-l', '64', '-w', '2000', destination],
                    capture_output=True, text=True, timeout=count * 3 + 10
                )
                raw_output = result.stdout + result.stderr
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Ping command failed: {str(e)}',
                    'raw_output': ''
                })
        except subprocess.TimeoutExpired:
            return JsonResponse({
                'status': 'error',
                'message': 'Ping timed out',
                'raw_output': 'Command timed out'
            })

        # Parse ping output
        metrics = parse_ping_output(raw_output, count)

        return JsonResponse({
            'status': 'success',
            'metrics': metrics,
            'raw_output': raw_output
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def parse_ping_output(output, count):
    """
    Parse ping output to extract latency, throughput, jitter, and packet loss.
    Supports both Linux and Windows ping output formats.
    """
    metrics = {
        'min_latency': '0',
        'avg_latency': '0',
        'max_latency': '0',
        'jitter': '0',
        'throughput': '0',
        'packet_loss': '100',
        'packets_sent': str(count),
        'packets_received': '0'
    }

    if not output:
        return metrics

    # Linux format: rtt min/avg/max/mdev = 0.123/0.456/0.789/0.100 ms
    rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
    if rtt_match:
        metrics['min_latency'] = rtt_match.group(1)
        metrics['avg_latency'] = rtt_match.group(2)
        metrics['max_latency'] = rtt_match.group(3)
        metrics['jitter'] = rtt_match.group(4)

    # Windows format: Minimum = 1ms, Maximum = 5ms, Average = 3ms
    if not rtt_match:
        win_match = re.search(r'Minimum = (\d+)ms.*Maximum = (\d+)ms.*Average = (\d+)ms', output, re.DOTALL)
        if win_match:
            metrics['min_latency'] = win_match.group(1)
            metrics['max_latency'] = win_match.group(2)
            metrics['avg_latency'] = win_match.group(3)
            # Approximate jitter as (max - min) / 2
            jitter = (float(win_match.group(2)) - float(win_match.group(1))) / 2
            metrics['jitter'] = f'{jitter:.2f}'

    # Packet loss — Linux: "3 packets transmitted, 3 received, 0% packet loss"
    loss_match = re.search(r'(\d+)% packet loss', output)
    if loss_match:
        metrics['packet_loss'] = loss_match.group(1)

    # Windows: "(0% loss)"
    if not loss_match:
        win_loss = re.search(r'\((\d+)% loss\)', output)
        if win_loss:
            metrics['packet_loss'] = win_loss.group(1)

    # Packets received
    recv_match = re.search(r'(\d+) received', output)
    if recv_match:
        metrics['packets_received'] = recv_match.group(1)
    else:
        win_recv = re.search(r'Received = (\d+)', output)
        if win_recv:
            metrics['packets_received'] = win_recv.group(1)

    # Calculate throughput: (packets_received * packet_size) / avg_latency_total
    try:
        avg_lat = float(metrics['avg_latency'])
        received = int(metrics['packets_received'])
        if avg_lat > 0 and received > 0:
            packet_size_bytes = 64 + 28  # payload + IP/ICMP header
            total_bytes = received * packet_size_bytes
            total_time_sec = (avg_lat * received) / 1000.0
            if total_time_sec > 0:
                throughput_kbps = (total_bytes / 1024.0) / total_time_sec
                metrics['throughput'] = f'{throughput_kbps:.2f}'
    except (ValueError, ZeroDivisionError):
        pass

    return metrics


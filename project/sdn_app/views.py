import json
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

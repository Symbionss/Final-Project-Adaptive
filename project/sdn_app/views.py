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
        
        # Definisikan static hosts di sini untuk memastikan Vis.js selalu memunculkannya
        # sesuai dengan topo_linear.py (karena kalau 0% ping, Ryu REST tidak mendeteksinya secara dinamis)
        static_hosts = [
            {"mac": "00:00:00:00:00:01", "ipv4": ["10.0.1.1"], "port": {"dpid": "0000000000000001"}},
            {"mac": "00:00:00:00:00:02", "ipv4": ["10.0.1.2"], "port": {"dpid": "0000000000000001"}},
            {"mac": "00:00:00:00:00:05", "ipv4": ["10.0.1.5"], "port": {"dpid": "0000000000000001"}},
            {"mac": "00:00:00:00:00:03", "ipv4": ["10.0.2.3"], "port": {"dpid": "0000000000000003"}},
            {"mac": "00:00:00:00:00:04", "ipv4": ["10.0.2.4"], "port": {"dpid": "0000000000000003"}},
            {"mac": "00:00:00:00:00:06", "ipv4": ["10.0.2.6"], "port": {"dpid": "0000000000000003"}},
        ]
        
        dynamic_hosts = hosts_resp.json() if hosts_resp.status_code == 200 else []
        # Gabung tanpa duplikat berdasarkan MAC
        existing_macs = {h['mac'] for h in dynamic_hosts}
        for static_h in static_hosts:
            if static_h['mac'] not in existing_macs:
                dynamic_hosts.append(static_h)
        
        # Inject custom label or link styling indicator into switches data (optional but ensures visual matches)
        dynamic_switches = switches_resp.json() if switches_resp.status_code == 200 else []
        dynamic_links = links_resp.json() if links_resp.status_code == 200 else []

        # Ensure that static switches are also injected just in case the controller is totally blank
        if not dynamic_switches:
            dynamic_switches = [
                {"dpid": "0000000000000001"},
                {"dpid": "0000000000000002"},
                {"dpid": "0000000000000003"},
            ]
            dynamic_links = [
                {"src": {"dpid": "0000000000000001", "port_no": "00000004"}, "dst": {"dpid": "0000000000000002", "port_no": "00000001"}},
                {"src": {"dpid": "0000000000000001", "port_no": "00000005"}, "dst": {"dpid": "0000000000000002", "port_no": "00000003"}},  # backup
                {"src": {"dpid": "0000000000000002", "port_no": "00000002"}, "dst": {"dpid": "0000000000000003", "port_no": "00000004"}},
                {"src": {"dpid": "0000000000000002", "port_no": "00000004"}, "dst": {"dpid": "0000000000000003", "port_no": "00000005"}},  # backup
            ]

        return JsonResponse({
            'status': 'success',
            'switches': dynamic_switches,
            'links': dynamic_links,
            'hosts': dynamic_hosts
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to connect to Ryu: {str(e)}',
            'switches': [],
            'links': [],
            'hosts': []
        }, status=500)

from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Machine

def index(request):
    return render(request, 'remote/index.html')

@csrf_exempt
def machines_api(request):
    if request.method == 'GET':
        machines = Machine.objects.all().order_by('-created_at')
        data = []
        for m in machines:
            is_active = cache.get(f"guacd_session_{m.id}") is not None
            data.append({
                'id': m.id,
                'name': m.name,
                'protocol': m.protocol,
                'hostname': m.hostname,
                'port': m.port,
                'username': m.username,
                'is_active': is_active
                # Nigdy nie zwracamy haseł do frontendu!
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            machine = Machine.objects.create(
                name=body.get('name', f"Server {body.get('hostname')}"),
                protocol=body.get('protocol', 'ssh'),
                hostname=body.get('hostname'),
                port=body.get('port'),
                username=body.get('username'),
                password=body.get('password')
            )
            return JsonResponse({'status': 'success', 'id': machine.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def machine_detail_api(request, machine_id):
    if request.method == 'DELETE':
        try:
            machine = Machine.objects.get(id=machine_id)
            machine.delete()
            return JsonResponse({'status': 'success'})
        except Machine.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Machine not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def pdu_api(request):
    """
    Zaślepka (placeholder) dla integracji z listami zasilającymi (PDU).
    Tutaj inni programiści powinni zaimplementować sterowanie portami i pobieranie statusu.
    """
    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'data': [
                {'id': 1, 'name': 'PDU-1 Port 1', 'state': 'ON'},
                {'id': 2, 'name': 'PDU-1 Port 2', 'state': 'OFF'}
            ]
        })
    return JsonResponse({'status': 'error', 'message': 'Metoda nieobsługiwana'}, status=405)

@csrf_exempt
def cameras_api(request):
    """
    Zaślepka (placeholder) dla integracji ze strumieniami wideo (MediaMTX).
    Tutaj inni programiści powinni zaimplementować pobieranie listy kamer.
    """
    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'cameras': [
                {'id': 'cam1', 'name': 'Laboratorium 1 - Przód', 'stream_url': 'rtsp://...'},
                {'id': 'cam2', 'name': 'Laboratorium 1 - Tył', 'stream_url': 'rtsp://...'}
            ]
        })
    return JsonResponse({'status': 'error', 'message': 'Metoda nieobsługiwana'}, status=405)
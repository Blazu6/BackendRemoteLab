from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Machine, PDU, PDUOutletMapping
from .services.pdu_factory import get_pdu_driver

# USUNIĘTO KLASĘ DummyPDU - teraz używamy bazy danych!

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
    # Obsługa żądań GET (Pobieranie listy listw LUB stanów gniazdek i nazw)
    if request.method == 'GET':
        ip_param = request.GET.get('ip')
        
        # 1. Jeśli przekazano IP, odpytujemy sprzęt o stany portów oraz pobieramy nazwy własne
        if ip_param:
            try:
                # ZMIANA: Pobieramy prawdziwą listwę z bazy danych
                pdu_instance = PDU.objects.get(ip_address=ip_param)
                driver = get_pdu_driver(pdu_instance)
                
                statuses = {}
                port = 1
                while port <= 32:  
                    status = driver.get_status(port)
                    if status is not None:
                        statuses[port] = status
                        port += 1
                    else:
                        break  
                
                # Pobieramy zapisane nazwy własne gniazdek z bazy danych dla tego IP
                names_mapping = {
                    m.outlet_id: m.custom_name 
                    for m in PDUOutletMapping.objects.filter(pdu_ip=ip_param)
                }
                
                return JsonResponse({
                    'status': 'success', 
                    'statuses': statuses,
                    'names': names_mapping
                })
            except PDU.DoesNotExist:
                 return JsonResponse({'status': 'error', 'message': 'Listwa nie istnieje w bazie'}, status=404)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        # 2. Jeśli brak IP, zwracamy listę zapamiętanych listew z bazy danych
        else:
            pdus = PDU.objects.all().order_by('-created_at')
            data = [{'ip': p.ip_address, 'protocol': p.protocol} for p in pdus]
            return JsonResponse({'status': 'success', 'data': data})

    # Obsługa żądań POST (Włączanie/Wyłączanie, Zmiana nazwy LUB zapisywanie nowej listwy)
    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            
            # Wariant A1: Zmiana nazwy gniazdka (np. na "Toster")
            if body.get('action') == 'rename':
                ip = body.get('ip_address')
                outlet = body.get('outlet')
                name = body.get('name', '')

                if not all([ip, outlet is not None]):
                    return JsonResponse({'status': 'error', 'message': 'Brakuje danych do zmiany nazwy'}, status=400)

                PDUOutletMapping.objects.update_or_create(
                    pdu_ip=ip,
                    outlet_id=outlet,
                    defaults={'custom_name': name}
                )
                return JsonResponse({'status': 'success', 'message': 'Zmieniono nazwę gniazdka'})

            # Wariant A2: Kliknięcie przycisku ON/OFF na gniazdku
            elif 'action' in body:
                ip = body.get('ip_address')
                outlet = body.get('outlet')
                action = body.get('action')

                if not all([ip, outlet, action]):
                    return JsonResponse({'status': 'error', 'message': 'Brakuje danych w JSON'}, status=400)

                try:
                    # ZMIANA: Pobieramy prawdziwą listwę z bazy danych
                    pdu_instance = PDU.objects.get(ip_address=ip)
                    driver = get_pdu_driver(pdu_instance)

                    if action == 'ON':
                        success = driver.turn_on(outlet)
                    elif action == 'OFF':
                        success = driver.turn_off(outlet)
                    else:
                        return JsonResponse({'status': 'error', 'message': f'Nieznana akcja: {action}'}, status=400)

                    if success:
                        return JsonResponse({'status': 'success', 'message': f'Wykonano {action} na gniazdku {outlet}'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Sprzęt nie odpowiedział'}, status=500)
                except PDU.DoesNotExist:
                     return JsonResponse({'status': 'error', 'message': 'Listwa nie istnieje w bazie'}, status=404)

            # Wariant B: Zapisanie nowej listwy do bazy danych
            else:
                ip = body.get('ip_address')
                protocol = body.get('protocol', 'REST_JSON')
                
                # ZMIANA: Odbieramy hasło (credentials) wysłane z Vue.js
                credentials = body.get('credentials', '') 
                
                if not ip:
                    return JsonResponse({'status': 'error', 'message': 'Brak adresu IP'}, status=400)

                # ZMIANA: Używamy update_or_create żeby zaktualizować hasło (encrypt zrobi swoje!)
                PDU.objects.update_or_create(
                    ip_address=ip, 
                    defaults={
                        'protocol': protocol,
                        'credentials': credentials
                    }
                )
                return JsonResponse({'status': 'success', 'message': 'Zapisano listwę'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Błąd serwera: {str(e)}'}, status=500)

    # Obsługa żądań DELETE (Usuwanie listwy z bazy)
    elif request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            ip = body.get('ip_address')
            
            if not ip:
                return JsonResponse({'status': 'error', 'message': 'Brak adresu IP do usunięcia'}, status=400)
                
            deleted_count, _ = PDU.objects.filter(ip_address=ip).delete()
            # Przy okazji można też wyczyścić przypisane nazwy dla tego IP
            PDUOutletMapping.objects.filter(pdu_ip=ip).delete()
            
            if deleted_count > 0:
                return JsonResponse({'status': 'success', 'message': 'Usunięto listwę'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Nie znaleziono listwy'}, status=404)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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
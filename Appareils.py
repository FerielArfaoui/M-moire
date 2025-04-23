from influxdb import InfluxDBClient
from collections import defaultdict
from datetime import datetime

# Connexion à la base InfluxDB
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
client.switch_database('events')

# Phase 1: Nombre total d'événements par appareil
print("Phase 1 : Nombre total d'événements par appareil")
query_device_total_events = '''
SELECT COUNT("event_type") 
FROM "user_event" 
GROUP BY "device"
'''
result_device_total_events = client.query(query_device_total_events)

for serie in result_device_total_events.raw.get('series', []):
    device = serie['tags']['device']
    count = serie['values'][0][1]
    print(f"Appareil: {device} - Nombre total d'événements: {count}")

# Phase 2: Répartition des types d'événements par appareil
print("\nPhase 2 : Répartition des types d'événements par appareil")
query_device_event_types = '''
SELECT COUNT("event_type") 
FROM "user_event" 
GROUP BY "device", "event_type"
'''
result_device_event_types = client.query(query_device_event_types)

for serie in result_device_event_types.raw.get('series', []):
    device = serie['tags']['device']
    event_type = serie['tags']['event_type']
    count = serie['values'][0][1]
    print(f"Appareil: {device} - Type d'événement: {event_type} - Nombre: {count}")

# Phase 3: Durée totale d'utilisation par appareil
print("\nPhase 3 : Durée totale d'utilisation par appareil")
query_device_total_duration = '''
SELECT SUM("screen_duration") 
FROM "user_event" 
GROUP BY "device"
'''
result_device_total_duration = client.query(query_device_total_duration)

for serie in result_device_total_duration.raw.get('series', []):
    device = serie['tags']['device']
    total_duration = serie['values'][0][1]
    print(f"Appareil: {device} - Durée totale: {total_duration} secondes")

# Phase 4: Nombre moyen d'événements par appareil et session
print("\nPhase 4 : Nombre moyen d'événements par appareil et session")
query_device_avg_events = '''
SELECT MEAN("event_count") 
FROM (
    SELECT COUNT("event_type") AS event_count 
    FROM "user_event" 
    GROUP BY "device", "session_id"
) 
GROUP BY "device"
'''
result_device_avg_events = client.query(query_device_avg_events)

for serie in result_device_avg_events.raw.get('series', []):
    device = serie['tags']['device']
    avg_events = serie['values'][0][1]
    print(f"Appareil: {device} - Nombre moyen d'événements par session: {avg_events:.2f}")

# Phase 5: Nombre de sessions par appareil
print("\nPhase 5 : Nombre de sessions par appareil")
query_device_sessions = '''
SELECT COUNT("event_type") 
FROM "user_event" 
GROUP BY "device", "session_id"
'''
result_device_sessions = client.query(query_device_sessions)

sessions_per_device = defaultdict(set)

for serie in result_device_sessions.raw.get('series', []):
    device = serie['tags']['device']
    session = serie['tags'].get('session_id')
    if session:
        sessions_per_device[device].add(session)

for device, sessions in sessions_per_device.items():
    print(f"Appareil: {device} - Nombre de sessions: {len(sessions)}")

# Phase 6: Temps moyen passé par appareil
print("\nPhase 6 : Temps moyen passé par appareil")
query_device_avg_time = '''
SELECT MEAN("screen_duration") 
FROM "user_event" 
GROUP BY "device"
'''
result_device_avg_time = client.query(query_device_avg_time)

for serie in result_device_avg_time.raw.get('series', []):
    device = serie['tags']['device']
    avg_time = serie['values'][0][1]
    print(f"Appareil: {device} - Temps moyen passé: {avg_time:.2f} secondes")



# Fermer la connexion à la base InfluxDB
client.close()

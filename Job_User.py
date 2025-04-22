from influxdb import InfluxDBClient

# Connexion à InfluxDB v1
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123', database='events')

# 1. Nombre total d'événements par utilisateur
query_total_events = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user"'
total_events = client.query(query_total_events)

print("\nNombre total d'événements par utilisateur:")
for serie in total_events.raw.get('series', []):
    user = serie['tags']['user']
    count = serie['values'][0][1]
    print(f"Utilisateur: {user} - Événements totaux: {count}")

# 2. Répartition des types d'événements (click, scroll, view)
query_event_types = 'SELECT  COUNT("event_type") FROM "user_event" GROUP BY "user", "event_type"'
event_types = client.query(query_event_types)

print("\nRépartition des types d'événements par utilisateur:")
for serie in event_types.raw.get('series', []):
    user = serie['tags']['user']
    event_type = serie['tags']['event_type']
    count = serie['values'][0][1]
    print(f"Utilisateur: {user} - Type: {event_type} - Nombre: {count}")

# 3. Durée totale d'utilisation (somme de screen_duration)
query_duration = 'SELECT SUM("screen_duration") FROM "user_event" GROUP BY "user"'
total_duration = client.query(query_duration)

print("\nDurée totale d'utilisation par utilisateur (en secondes):")
for serie in total_duration.raw.get('series', []):
    user = serie['tags']['user']
    duration = serie['values'][0][1]
    print(f"Utilisateur: {user} - Durée totale: {duration:.2f}s")

# 4. Nombre moyen d'événements par session
query_avg_events = '''
SELECT MEAN("event_count") FROM (
    SELECT COUNT("event_type") AS event_count 
    FROM "user_event" 
    GROUP BY "user", "session_id"
) 
GROUP BY "user"
'''
avg_events = client.query(query_avg_events)

print("\nNombre moyen d'événements par session:")
for serie in avg_events.raw.get('series', []):
    user = serie['tags']['user']
    avg_count = serie['values'][0][1]
    print(f"Utilisateur: {user} - Moyenne/session: {avg_count:.2f}")

client.close()
      
     

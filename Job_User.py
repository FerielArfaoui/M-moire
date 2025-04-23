from influxdb import InfluxDBClient
from collections import defaultdict
from datetime import datetime, timezone

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

# 2. Répartition des types d'événements
query_event_types = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user", "event_type"'
event_types = client.query(query_event_types)

print("\nRépartition des types d'événements par utilisateur:")
for serie in event_types.raw.get('series', []):
    user = serie['tags']['user']
    event_type = serie['tags']['event_type']
    count = serie['values'][0][1]
    print(f"Utilisateur: {user} - Type: {event_type} - Nombre: {count}")

# 3. Durée totale d'utilisation
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

# 5. Nombre de sessions par utilisateur (simulé)
query_sessions = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user", "session_id"'
result_sessions = client.query(query_sessions)

sessions_per_user = defaultdict(set)
sessions_per_day = defaultdict(set)

for serie in result_sessions.raw.get('series', []):
    user = serie['tags'].get('user')
    session = serie['tags'].get('session_id')
    timestamp = serie['values'][0][0]

    if user and session:
        sessions_per_user[user].add(session)

    # Convertir en heure locale
    if timestamp:
        local_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone()
        local_date = local_dt.strftime("%Y-%m-%d")
        sessions_per_day[local_date].add(session)

print("\nNombre de sessions par utilisateur:")
for user, sessions in sessions_per_user.items():
    print(f"Utilisateur: {user} - Sessions: {len(sessions)}")

print("\nNombre de sessions par jour (heure locale système):")
for date, sessions in sorted(sessions_per_day.items()):
    print(f"{date} : {len(sessions)} sessions")

# 6. Nombre d'utilisateurs actifs par jour (simulé)
query_users = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user", time(1d)'
result_users = client.query(query_users)

active_users_per_day = defaultdict(set)
for serie in result_users.raw.get('series', []):
    user = serie['tags'].get('user')
    for value in serie['values']:
        timestamp = value[0]
        if timestamp:
            local_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone()
            local_date = local_dt.strftime("%Y-%m-%d")
            if user:
                active_users_per_day[local_date].add(user)

print("\nNombre d'utilisateurs actifs par jour (heure locale système):")
for date, users in sorted(active_users_per_day.items()):
    print(f"{date} : {len(users)} utilisateurs actifs")

client.close()

from influxdb import InfluxDBClient
from collections import defaultdict
from datetime import datetime
import psycopg2

# Connexion à InfluxDB v1
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123', database='events')

# Connexion à PostgreSQL
conn = psycopg2.connect(
    dbname="Agregation",
    user="postgres",
    password="admin123",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Création des tables si elles n'existent pas déjà
cur.execute("""
    CREATE TABLE IF NOT EXISTS total_events (
        "user" VARCHAR(255),
        event_count INT
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS event_types (
        "user" VARCHAR(255),
        event_type VARCHAR(255),
        event_count INT
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS total_duration (
        "user" VARCHAR(255),
        total_duration FLOAT
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS avg_events_per_session (
        "user" VARCHAR(255),
        avg_events FLOAT
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions_per_user (
        "user" VARCHAR(255),
        session_count INT
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions_per_day (
        date DATE,
        session_count INT
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS active_users_per_day (
        date DATE,
        active_user_count INT
    );
""")
conn.commit()

# 1. Nombre total d'événements par utilisateur
query_total_events = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user"'
total_events = client.query(query_total_events)

for serie in total_events.raw.get('series', []):
    user = serie['tags']['user']
    count = serie['values'][0][1]
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO total_events (\"user\", event_count) VALUES (%s, %s)", (user, count))
    print(f"Événements totaux insérés avec succès pour l'utilisateur: {user} - Événements: {count}")
conn.commit()

# 2. Répartition des types d'événements
query_event_types = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user", "event_type"'
event_types = client.query(query_event_types)

for serie in event_types.raw.get('series', []):
    user = serie['tags']['user']
    event_type = serie['tags']['event_type']
    count = serie['values'][0][1]
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO event_types (\"user\", event_type, event_count) VALUES (%s, %s, %s)", (user, event_type, count))
    print(f"Répartition des types d'événements insérée avec succès pour l'utilisateur: {user} - Type: {event_type} - Nombre: {count}")
conn.commit()

# 3. Durée totale d'utilisation
query_duration = 'SELECT SUM("screen_duration") FROM "user_event" GROUP BY "user"'
total_duration = client.query(query_duration)

for serie in total_duration.raw.get('series', []):
    user = serie['tags']['user']
    duration = serie['values'][0][1]
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO total_duration (\"user\", total_duration) VALUES (%s, %s)", (user, duration))
    print(f"Durée totale insérée avec succès pour l'utilisateur: {user} - Durée totale: {duration:.2f}")
conn.commit()

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

for serie in avg_events.raw.get('series', []):
    user = serie['tags']['user']
    avg_count = serie['values'][0][1]
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO avg_events_per_session (\"user\", avg_events) VALUES (%s, %s)", (user, avg_count))
    print(f"Moyenne d'événements par session insérée avec succès pour l'utilisateur: {user} - Moyenne: {avg_count:.2f}")
conn.commit()

# 5. Nombre de sessions par utilisateur (simulé)
query_sessions = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY "user", "session_id"'
result_sessions = client.query(query_sessions)

sessions_per_user = defaultdict(set)

for serie in result_sessions.raw.get('series', []):
    user = serie['tags'].get('user')
    session = serie['tags'].get('session_id')

    if user and session:
        sessions_per_user[user].add(session)

for user, sessions in sessions_per_user.items():
    session_count = len(sessions)
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO sessions_per_user (\"user\", session_count) VALUES (%s, %s)", (user, session_count))
    print(f"Nombre de sessions inséré avec succès pour l'utilisateur: {user} - Sessions: {session_count}")
conn.commit()

# 6. Nombre de sessions par jour (simulé)
query_sessions_per_day = 'SELECT COUNT("event_type") FROM "user_event" GROUP BY time(1d), "session_id"'
result_sessions_per_day = client.query(query_sessions_per_day)

sessions_per_day = defaultdict(set)

for serie in result_sessions_per_day.raw.get('series', []):
    timestamp = serie['values'][0][0]
    session = serie['tags'].get('session_id')

    if timestamp and session:
        local_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone()
        local_date = local_dt.strftime("%Y-%m-%d")
        sessions_per_day[local_date].add(session)

for date, sessions in sorted(sessions_per_day.items()):
    session_count = len(sessions)
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO sessions_per_day (date, session_count) VALUES (%s, %s)", (date, session_count))
    print(f"Nombre de sessions par jour inséré avec succès pour la date: {date} - Sessions: {session_count}")
conn.commit()

# 7. Nombre d'utilisateurs actifs par jour (simulé)
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

for date, users in sorted(active_users_per_day.items()):
    active_user_count = len(users)
    # Insertion dans PostgreSQL
    cur.execute("INSERT INTO active_users_per_day (date, active_user_count) VALUES (%s, %s)", (date, active_user_count))
    print(f"Nombre d'utilisateurs actifs inséré avec succès pour la date: {date} - Utilisateurs actifs: {active_user_count}")
conn.commit()

# Fermeture des connexions
cur.close()
conn.close()
client.close()


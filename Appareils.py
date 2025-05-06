from influxdb import InfluxDBClient
from collections import defaultdict
from datetime import datetime
import psycopg2

# Connexion à InfluxDB
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
client.switch_database('events')

# Connexion à PostgreSQL
pg_conn = psycopg2.connect(
    host="localhost",
    database="Agregation",
    user="postgres",
    password="admin123"
)
pg_cursor = pg_conn.cursor()

# Création de la table PostgreSQL
pg_cursor.execute("""
CREATE TABLE IF NOT EXISTS device_summary (
    device TEXT PRIMARY KEY,
    total_events INTEGER DEFAULT 0,
    click_events INTEGER DEFAULT 0,
    view_events INTEGER DEFAULT 0,
    scroll_events INTEGER DEFAULT 0,
    total_duration FLOAT DEFAULT 0,
    avg_events_per_session FLOAT DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    avg_time_per_event FLOAT DEFAULT 0,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
pg_conn.commit()

# Dictionnaire de stockage
summary = defaultdict(lambda: {
    'total_events': 0,
    'click_events': 0,
    'view_events': 0,
    'scroll_events': 0,
    'total_duration': 0.0,
    'avg_events_per_session': 0.0,
    'session_count': 0,
    'avg_time_per_event': 0.0
})

# Phase 1: Total événements
query = '''SELECT COUNT("event_type") FROM "user_event" GROUP BY "device"'''
res = client.query(query)
for serie in res.raw.get('series', []):
    device = serie['tags']['device']
    summary[device]['total_events'] = int(serie['values'][0][1])

# Phase 2: Événements par type
query = '''SELECT COUNT("event_type") FROM "user_event" GROUP BY "device", "event_type"'''
res = client.query(query)
for serie in res.raw.get('series', []):
    device = serie['tags']['device']
    event_type = serie['tags']['event_type']
    count = int(serie['values'][0][1])
    if event_type == 'click':
        summary[device]['click_events'] = count
    elif event_type == 'view':
        summary[device]['view_events'] = count
    elif event_type == 'scroll':
        summary[device]['scroll_events'] = count

# Phase 3: Durée totale
query = '''SELECT SUM("screen_duration") FROM "user_event" GROUP BY "device"'''
res = client.query(query)
for serie in res.raw.get('series', []):
    device = serie['tags']['device']
    duration = float(serie['values'][0][1] or 0)
    summary[device]['total_duration'] = duration

# Phase 4: Moyenne événements par session
query = '''
SELECT MEAN("event_count") FROM (
    SELECT COUNT("event_type") AS event_count 
    FROM "user_event" GROUP BY "device", "session_id"
) GROUP BY "device"
'''
res = client.query(query)
for serie in res.raw.get('series', []):
    device = serie['tags']['device']
    mean = float(serie['values'][0][1] or 0)
    summary[device]['avg_events_per_session'] = mean

# Phase 5: Nombre de sessions
query = '''SELECT COUNT("event_type") FROM "user_event" GROUP BY "device", "session_id"'''
res = client.query(query)
device_sessions = defaultdict(set)
for serie in res.raw.get('series', []):
    device = serie['tags']['device']
    session_id = serie['tags'].get('session_id')
    if session_id:
        device_sessions[device].add(session_id)
for device, sessions in device_sessions.items():
    summary[device]['session_count'] = len(sessions)

# Phase 6: Temps moyen passé
query = '''SELECT MEAN("screen_duration") FROM "user_event" GROUP BY "device"'''
res = client.query(query)
for serie in res.raw.get('series', []):
    device = serie['tags']['device']
    avg_time = float(serie['values'][0][1] or 0)
    summary[device]['avg_time_per_event'] = avg_time

# Insertion dans PostgreSQL
for device, data in summary.items():
    pg_cursor.execute("""
        INSERT INTO device_summary (
            device, total_events, click_events, view_events, scroll_events,
            total_duration, avg_events_per_session, session_count, avg_time_per_event, extraction_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (device) DO UPDATE SET
            total_events = EXCLUDED.total_events,
            click_events = EXCLUDED.click_events,
            view_events = EXCLUDED.view_events,
            scroll_events = EXCLUDED.scroll_events,
            total_duration = EXCLUDED.total_duration,
            avg_events_per_session = EXCLUDED.avg_events_per_session,
            session_count = EXCLUDED.session_count,
            avg_time_per_event = EXCLUDED.avg_time_per_event,
            extraction_date = EXCLUDED.extraction_date
    """, (
        device,
        data['total_events'],
        data['click_events'],
        data['view_events'],
        data['scroll_events'],
        data['total_duration'],
        data['avg_events_per_session'],
        data['session_count'],
        data['avg_time_per_event'],
        datetime.now()
    ))

pg_conn.commit()

# Fermeture
pg_cursor.close()
pg_conn.close()
client.close()

print(" Données enregistrées dans la table 'device_summary'")

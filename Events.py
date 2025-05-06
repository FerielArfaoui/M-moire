from influxdb import InfluxDBClient
import psycopg2
from datetime import datetime

# Connexion InfluxDB
influx_client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
influx_client.switch_database('events')

# Connexion PostgreSQL
pg_conn = psycopg2.connect(
    host="localhost",
    database="Agregation",
    user="postgres",
    password="admin123"
)
pg_cursor = pg_conn.cursor()

# Création de la table PostgreSQL si elle n'existe pas
pg_cursor.execute("""
CREATE TABLE IF NOT EXISTS event_summary (
    user_id TEXT,
    event_clicks INTEGER DEFAULT 0,
    event_views INTEGER DEFAULT 0,
    event_scrolls INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
pg_conn.commit()

# Types d'événements
event_types = ['click', 'scroll', 'view']
event_order = ['click', 'view', 'scroll']

# Dictionnaire des résultats
users = {}

# Récupérer les données depuis InfluxDB
for etype in event_order:
    query = f'SELECT COUNT("event_type") FROM "user_event" WHERE "event_type" = \'{etype}\' GROUP BY "user"'
    results = influx_client.query(query)

    for serie in results.raw.get('series', []):
        user_id = serie.get("tags", {}).get("user", "inconnu")
        count = serie.get("values", [[None, 0]])[0][1]

        if user_id not in users:
            users[user_id] = {}
        users[user_id][etype] = int(count)

# Insérer les résultats dans PostgreSQL
for user_id, events in users.items():
    clicks = events.get('click', 0)
    views = events.get('view', 0)
    scrolls = events.get('scroll', 0)

    pg_cursor.execute("""
        INSERT INTO event_summary (user_id, event_clicks, event_views, event_scrolls, total_views, extraction_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, clicks, views, scrolls, views, datetime.now()))

pg_conn.commit()

# Fermer les connexions
pg_cursor.close()
pg_conn.close()
influx_client.close()

print("Données insérées avec succès dans PostgreSQL.")

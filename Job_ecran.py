from influxdb import InfluxDBClient
import psycopg2

# Connexion à InfluxDB
influx_client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
influx_client.switch_database('events')

# Connexion à PostgreSQL
pg_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="Agregation",  
    user="postgres",
    password="admin123"
)
pg_cursor = pg_conn.cursor()

# Création de la table si elle n'existe pas
pg_cursor.execute("""
CREATE TABLE IF NOT EXISTS avg_screen_duration_per_user (
    user_id VARCHAR PRIMARY KEY,
    avg_screen_duration FLOAT
)
""")
pg_conn.commit()

# Requête vers InfluxDB : moyenne screen_duration par utilisateur
query = '''
SELECT MEAN("screen_duration") 
FROM "user_event" 
GROUP BY "user"
'''
results = influx_client.query(query)

# Insertion dans PostgreSQL
for serie in results.raw.get('series', []):
    user_id = serie['tags']['user']
    avg_duration = serie['values'][0][1]

    if avg_duration is not None:
        pg_cursor.execute("""
        INSERT INTO avg_screen_duration_per_user (user_id, avg_screen_duration)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET avg_screen_duration = EXCLUDED.avg_screen_duration
        """, (user_id, avg_duration))

# Commit et fermeture
pg_conn.commit()
pg_cursor.close()
pg_conn.close()
influx_client.close()

print("Données transférées dans PostgreSQL avec succès.")

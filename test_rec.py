from influxdb import InfluxDBClient
import pandas as pd
import psycopg2
import datetime

# Connexion à InfluxDB
client = InfluxDBClient(
    host='localhost',
    port=8087,
    username='Feriel',
    password='admin123',
    database='events'
)

# Récupération des données
query = "SELECT * FROM user_event"
results = client.query(query)
points = list(results.get_points())
df = pd.DataFrame(points)

# Connexion à PostgreSQL
pg_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="Trackingdb",
    user="postgres",
    password="admin123"
)
cursor = pg_conn.cursor()

# Création de la table si elle n'existe pas déjà
cursor.execute("""
CREATE TABLE IF NOT EXISTS recommendation_stats (
    id SERIAL PRIMARY KEY,
    metric_category TEXT,
    metric_name TEXT,
    value FLOAT,
    percentage FLOAT,
    date_calculated DATE
)
""")
pg_conn.commit()

today = datetime.date.today()

# 1. Top 5 types d'événements
top_event_types = df['event_type'].value_counts().head(5)
total_events = df['event_type'].count()
for event, count in top_event_types.items():
    percent = (count / total_events) * 100
    cursor.execute("""
        INSERT INTO recommendation_stats (metric_category, metric_name, value, percentage, date_calculated)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        'event_type',
        str(event),
        int(count),
        float(percent),
        today
    ))

# 2. Top 5 utilisateurs les plus actifs
top_users = df['user'].value_counts().head(5)
total_users_events = df['user'].count()
for user, count in top_users.items():
    percent = (count / total_users_events) * 100
    cursor.execute("""
        INSERT INTO recommendation_stats (metric_category, metric_name, value, percentage, date_calculated)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        'top_user',
        str(user),
        int(count),
        float(percent),
        today
    ))

# 3. Répartition des fabricants
manufacturer_counts = df['manufacturer'].value_counts()
total_manufacturers = manufacturer_counts.sum()
for manu, count in manufacturer_counts.items():
    percent = (count / total_manufacturers) * 100
    cursor.execute("""
        INSERT INTO recommendation_stats (metric_category, metric_name, value, percentage, date_calculated)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        'manufacturer',
        str(manu),
        int(count),
        float(percent),
        today
    ))

# 4. Temps d’écran moyen par système (OS)
avg_screen_by_system = df.groupby('system')['screen_duration'].mean()
for system, avg_time in avg_screen_by_system.items():
    cursor.execute("""
        INSERT INTO recommendation_stats (metric_category, metric_name, value, percentage, date_calculated)
        VALUES (%s, %s, %s, NULL, %s)
    """, (
        'system_avg_time',
        str(system),
        float(avg_time),
        today
    ))

# 5. Temps d’écran moyen par fabricant
avg_screen_by_manufacturer = df.groupby('manufacturer')['screen_duration'].mean()
for manu, avg_time in avg_screen_by_manufacturer.items():
    cursor.execute("""
        INSERT INTO recommendation_stats (metric_category, metric_name, value, percentage, date_calculated)
        VALUES (%s, %s, %s, NULL, %s)
    """, (
        'manufacturer_avg_time',
        str(manu),
        float(avg_time),
        today
    ))

# Commit et fermeture
pg_conn.commit()
cursor.close()
pg_conn.close()

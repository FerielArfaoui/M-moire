from influxdb import InfluxDBClient
import pandas as pd

# Connexion à InfluxDB
client = InfluxDBClient(
    host='localhost',
    port=8087,
    username='Feriel',
    password='admin123',
    database='events'  # à adapter selon ta base
)

# ⚠Adapter le nom de la mesure si ce n'est pas "user_event"
query = "SELECT * FROM user_event"
results = client.query(query)
points = list(results.get_points())

# Convertir en DataFrame
df = pd.DataFrame(points)

# 1. Top 5 types d'événements avec pourcentages
top_event_types = df['event_type'].value_counts().head(5)
total_events = df['event_type'].count()
print("\nTop 5 types d'événements :")
for event, count in top_event_types.items():
    percent = (count / total_events) * 100
    print(f"{event} : {count} ({percent:.2f}%)")

#  2. Top 5 utilisateurs les plus actifs avec pourcentages
top_users = df['user'].value_counts().head(5)
total_users_events = df['user'].count()
print("\n Top 5 utilisateurs les plus actifs :")
for user, count in top_users.items():
    percent = (count / total_users_events) * 100
    print(f"{user} : {count} ({percent:.2f}%)")

#  3. Répartition des fabricants avec pourcentages
manufacturer_counts = df['manufacturer'].value_counts()
total_manufacturers = manufacturer_counts.sum()
print("\n Répartition des fabricants :")
for manu, count in manufacturer_counts.items():
    percent = (count / total_manufacturers) * 100
    print(f"{manu} : {count} ({percent:.2f}%)")

#  4. Temps d’écran moyen par système (OS)
avg_screen_by_system = df.groupby('system')['screen_duration'].mean()
print("\n Temps d'écran moyen par système (OS) :")
print(avg_screen_by_system)

#  4b. Temps d’écran moyen par fabricant
avg_screen_by_manufacturer = df.groupby('manufacturer')['screen_duration'].mean()
print("\n Temps d'écran moyen par fabricant :")
print(avg_screen_by_manufacturer)



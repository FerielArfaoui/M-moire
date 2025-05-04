from influxdb import InfluxDBClient
import pandas as pd
from datetime import datetime, timedelta

# Connexion à InfluxDB
client = InfluxDBClient(
    host='localhost',
    port=8087,
    username='Feriel',
    password='admin123'
)
client.switch_database('events')

# Extraction des données depuis InfluxDB
result = client.query("SELECT * FROM user_event")
df = pd.DataFrame(result.get_points())

# Vérification
if df.empty:
    raise ValueError("Aucune donnée trouvée dans InfluxDB.")

# Conversion de la colonne 'time' en datetime si nécessaire
df['time'] = pd.to_datetime(df['time'])

# Rendre la colonne 'time' timezone-naive si elle est timezone-aware
df['time'] = df['time'].dt.tz_localize(None)

# Calcul du pourcentage global pour chaque type d'événement (Click, View, Scroll)
event_counts = df['event_type'].value_counts()
event_percentage = (event_counts / event_counts.sum()) * 100

# Afficher le pourcentage global
print("Pourcentage des types d'événements effectués par les utilisateurs :")
for event, percentage in event_percentage.items():
    print(f"{event} : {percentage:.2f}%")

# Analyse des événements pour la dernière semaine
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Rendre start_date timezone-naive si elle est timezone-aware
start_date = start_date.replace(tzinfo=None)

df_last_week = df[df['time'] >= start_date]

# Vérification si nous avons des données pour la dernière semaine
if df_last_week.empty:
    print(f"Aucune donnée pour la période du {start_date.date()} au {end_date.date()}.")
else:
    # Calcul du pourcentage des événements dans la dernière semaine
    event_counts_week = df_last_week['event_type'].value_counts()
    event_percentage_week = (event_counts_week / event_counts_week.sum()) * 100

    # Afficher le pourcentage pour la dernière semaine
    print(f"\nPourcentage des types d'événements dans la dernière semaine ({start_date.date()} - {end_date.date()}):")
    for event, percentage in event_percentage_week.items():
        print(f"{event} : {percentage:.2f}%")

    # Recommendation basée sur l'analyse
    if 'click' in event_percentage_week and event_percentage_week['click'] > max(event_percentage_week['view'], event_percentage_week['scroll']):
        print(" Recommandation : Les utilisateurs ont principalement fait des 'clicks', surveillez ce comportement.")
    elif 'view' in event_percentage_week and event_percentage_week['view'] > max(event_percentage_week['click'], event_percentage_week['scroll']):
        print(" Recommandation : Les utilisateurs ont principalement vu des pages, surveillez ce comportement.")
    elif 'scroll' in event_percentage_week and event_percentage_week['scroll'] > max(event_percentage_week['click'], event_percentage_week['view']):
        print(" Recommandation : Les utilisateurs ont principalement fait défiler les pages, surveillez ce comportement.")


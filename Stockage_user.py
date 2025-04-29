import psycopg2
import pandas as pd
from influxdb import InfluxDBClient

# Connexion à InfluxDB
client = InfluxDBClient(
    host='localhost',
    port=8087,
    username='Feriel',
    password='admin123'
)
client.switch_database('events')

# Requête InfluxQL pour récupérer les données
query = 'SELECT * FROM "user_event" LIMIT 1000'
result = client.query(query)

# Conversion des données InfluxDB en DataFrame
points = list(result.get_points(measurement='user_event'))
df = pd.DataFrame(points)

# Connexion à PostgreSQL
conn = psycopg2.connect(
    dbname="Trackingdb",  # Remplacez par le nom de votre base de données PostgreSQL
    user="postgres",   # Remplacez par votre nom d'utilisateur PostgreSQL
    password="admin123",  # Remplacez par votre mot de passe PostgreSQL
    host="localhost",       # Si PostgreSQL est sur un autre serveur, changez l'hôte
    port="5432"             # Le port par défaut pour PostgreSQL est 5432
)
cursor = conn.cursor()

# Insertion des données dans la table 'users' de PostgreSQL avec gestion des doublons
for index, row in df.iterrows():
    cursor.execute("""
        INSERT INTO users (user_id, screen_duration, device, system)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING  -- Ignorer l'insertion si le user_id existe déjà
    """, (
        row['user'],               # Utilisation de 'user' pour l'identifiant
        row.get('screen_duration', 0),  # Valeur par défaut si manquante
        row.get('device', ''),
        row.get('system', '')
    ))

# Commit et fermeture
conn.commit()
cursor.close()
conn.close()

print("Les données ont été insérées avec succès dans la table 'users'.")


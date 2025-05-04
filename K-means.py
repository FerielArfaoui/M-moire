from influxdb import InfluxDBClient
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import psycopg2

# Connexion à InfluxDB
client = InfluxDBClient(
    host='localhost',
    port=8087,
    username='Feriel',
    password='admin123'
)
client.switch_database('events')

# Requête InfluxQL
query = 'SELECT * FROM "user_event" LIMIT 1000'
result = client.query(query)
points = list(result.get_points(measurement='user_event'))
df = pd.DataFrame(points)

print("Dataframe initial récupéré :")
print(df.head())

# One-Hot Encoding
df_encoded = pd.get_dummies(df, columns=['event_type', 'manufacturer', 'system'])

# Colonnes attendues (au cas où elles n’existent pas)
expected_cols = [
    'event_type_click', 'event_type_scroll', 'event_type_view',
    'manufacturer_apple', 'manufacturer_google', 'manufacturer_oneplus', 'manufacturer_samsung',
    'system_android', 'system_ios'
]
for col in expected_cols:
    if col not in df_encoded.columns:
        df_encoded[col] = 0

# Agrégation par utilisateur
aggregation = df_encoded.groupby('user').agg({
    col: 'sum' for col in df_encoded.columns if col not in ['time', 'device', 'user']
})
aggregation['avg_screen_duration'] = df_encoded.groupby('user')['screen_duration'].mean()
aggregation.reset_index(inplace=True)

print("Données agrégées :")
print(aggregation.head())

# Standardisation
features = aggregation.drop(columns=['user'])
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Détection du nombre optimal de clusters
best_k = 2
best_score = -1
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(features_scaled)
    score = silhouette_score(features_scaled, labels)
    if score > best_score:
        best_k = k
        best_score = score

print(f"\nNombre optimal de clusters détecté automatiquement : {best_k}")
kmeans = KMeans(n_clusters=best_k, random_state=42)
aggregation['cluster'] = kmeans.fit_predict(features_scaled)

# Connexion à PostgreSQL
try:
    conn = psycopg2.connect(
        dbname="Trackingdb", user="postgres", password="admin123", host="localhost", port="5432"
    )
    cursor = conn.cursor()

    # Création de la table si elle n’existe pas
    create_table_query = """
    CREATE TABLE IF NOT EXISTS user_clusters (
        user_id TEXT PRIMARY KEY,
        cluster INTEGER,
        screen_duration DOUBLE PRECISION,
        event_type_click INTEGER,
        event_type_scroll INTEGER,
        event_type_view INTEGER,
        manufacturer_apple INTEGER,
        manufacturer_google INTEGER,
        manufacturer_oneplus INTEGER,
        manufacturer_samsung INTEGER,
        system_android INTEGER,
        system_ios INTEGER,
        avg_screen_duration DOUBLE PRECISION
    );
    """
    cursor.execute(create_table_query)
    conn.commit()

    # Requête d’insertion avec upsert (on conflict)
    insert_query = """
        INSERT INTO user_clusters (
            user_id, cluster, screen_duration, event_type_click, event_type_scroll, event_type_view,
            manufacturer_apple, manufacturer_google, manufacturer_oneplus, manufacturer_samsung,
            system_android, system_ios, avg_screen_duration
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            cluster = EXCLUDED.cluster,
            screen_duration = EXCLUDED.screen_duration,
            event_type_click = EXCLUDED.event_type_click,
            event_type_scroll = EXCLUDED.event_type_scroll,
            event_type_view = EXCLUDED.event_type_view,
            manufacturer_apple = EXCLUDED.manufacturer_apple,
            manufacturer_google = EXCLUDED.manufacturer_google,
            manufacturer_oneplus = EXCLUDED.manufacturer_oneplus,
            manufacturer_samsung = EXCLUDED.manufacturer_samsung,
            system_android = EXCLUDED.system_android,
            system_ios = EXCLUDED.system_ios,
            avg_screen_duration = EXCLUDED.avg_screen_duration
    """

    for _, row in aggregation.iterrows():
        values = (
            row['user'],
            row['cluster'],
            row.get('screen_duration', 0),
            row.get('event_type_click', 0),
            row.get('event_type_scroll', 0),
            row.get('event_type_view', 0),
            row.get('manufacturer_apple', 0),
            row.get('manufacturer_google', 0),
            row.get('manufacturer_oneplus', 0),
            row.get('manufacturer_samsung', 0),
            row.get('system_android', 0),
            row.get('system_ios', 0),
            row['avg_screen_duration']
        )
        print(f"Insertion : {values}")
        cursor.execute(insert_query, values)

    conn.commit()
    print(" Les résultats du clustering ont été insérés dans la table 'user_clusters'.")

except Exception as e:
    print(f" Erreur lors de l'insertion dans PostgreSQL : {e}")

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()

print("Nettoyage terminé.")


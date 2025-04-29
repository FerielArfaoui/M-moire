from influxdb import InfluxDBClient
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

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

# Conversion en DataFrame
points = list(result.get_points(measurement='user_event'))
df = pd.DataFrame(points)

# Affichage avant transformation
print("Avant One-Hot Encoding :")
print(df.head())

# One-Hot Encoding
df_encoded = pd.get_dummies(df, columns=['event_type', 'manufacturer', 'system'])

# Agrégation par utilisateur
aggregation = df_encoded.groupby('user').agg({
    col: 'sum' for col in df_encoded.columns if col not in ['time', 'device', 'user']
})
aggregation['avg_screen_duration'] = df_encoded.groupby('user')['screen_duration'].mean()
aggregation.reset_index(inplace=True)

print("\nDonnées agrégées par utilisateur :")
print(aggregation.head())

# Standardisation
features = aggregation.drop(columns=['user'])
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Phase de détection du nombre optimal de clusters
inertia = []
silhouette_scores = []
k_range = range(2, 11)
best_k = 2
best_score = -1

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(features_scaled)
    inertia.append(kmeans.inertia_)
    score = silhouette_score(features_scaled, labels)
    silhouette_scores.append(score)
    print(f"Silhouette score pour k={k}: {score:.4f}")
    if score > best_score:
        best_score = score
        best_k = k

# Affichage graphique (optionnel mais utile)
plt.figure(figsize=(12, 6))

# Elbow method
plt.subplot(1, 2, 1)
plt.plot(k_range, inertia, marker='o')
plt.title("Méthode du Coudé (Elbow Method)")
plt.xlabel("Nombre de clusters")
plt.ylabel("Inertie")

# Silhouette score
plt.subplot(1, 2, 2)
plt.plot(k_range, silhouette_scores, marker='o', color='orange')
plt.title("Score de Silhouette")
plt.xlabel("Nombre de clusters")
plt.ylabel("Silhouette Score")

plt.tight_layout()
plt.show()

# Appliquer K-Means avec le meilleur k
print(f"\n Nombre optimal de clusters détecté automatiquement : {best_k}")
kmeans = KMeans(n_clusters=best_k, random_state=42)
aggregation['cluster'] = kmeans.fit_predict(features_scaled)

# Affichage des résultats
print("\nDonnées après clustering :")
print(aggregation)

print("\nRésumé des clusters (moyenne par cluster) :")
print(aggregation.groupby('cluster').mean(numeric_only=True))

# Données par cluster
for cluster in range(best_k):
    print(f"\nDonnées pour le cluster {cluster} :")
    print(aggregation[aggregation['cluster'] == cluster])

# Distribution
for cluster in range(best_k):
    count = aggregation[aggregation['cluster'] == cluster].shape[0]
    print(f"Nombre d'utilisateurs dans le cluster {cluster} : {count}")


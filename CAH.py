from influxdb import InfluxDBClient
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA  # Pour réduction de dimension si nécessaire

# Style
plt.style.use('seaborn-v0_8')
sns.set_palette('tab10')


def plot_dendrogram(Z, threshold):
    plt.figure(figsize=(12, 6))

    # Configuration des couleurs
    dendrogram(
        Z,
        color_threshold=threshold,
        link_color_func=lambda k: 'b'  # Toutes les branches en bleu
    )

    plt.axhline(y=threshold, c='red', linestyle='--')
    plt.title(f'Dendrogramme CAH (seuil: {threshold:.2f})')
    plt.xlabel('Utilisateurs')
    plt.ylabel('Distance')
    plt.show()

def plot_clusters_2d(features_scaled, labels):
    # Réduction de dimension avec PCA (si plus de 2 dimensions)
    pca = PCA(n_components=2)
    features_2d = pca.fit_transform(features_scaled)

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        x=features_2d[:, 0],
        y=features_2d[:, 1],
        hue=labels,
        palette='viridis',
        s=100
    )
    plt.title("Clusters des utilisateurs (PCA - 2D)")
    plt.xlabel("Composante principale 1")
    plt.ylabel("Composante principale 2")
    plt.show()

try:
    # Connexion InfluxDB
    client = InfluxDBClient(
        host='localhost',
        port=8087,
        username='Feriel',
        password='admin123'
    )
    client.switch_database('events')

    # Extraction des données
    result = client.query("SELECT * FROM user_event")
    df = pd.DataFrame(result.get_points())

    if df.empty:
        raise ValueError("Aucune donnée dans InfluxDB.")

    # Encodage des colonnes catégorielles
    df_encoded = pd.get_dummies(df, columns=['event_type', 'manufacturer', 'system'])

    # Agrégation par utilisateur
    aggregation = df_encoded.groupby('user').agg({
        col: 'sum' for col in df_encoded.columns if col not in ['time', 'device', 'user']
    })
    aggregation['avg_screen_duration'] = df_encoded.groupby('user')['screen_duration'].mean()
    aggregation.reset_index(inplace=True)

    # Standardisation
    features = aggregation.drop(columns=['user'])
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Matrice de liaison
    Z = linkage(features_scaled, method='ward', optimal_ordering=True)

    # Seuil automatique pour couper le dendrogramme
    last_merges = Z[-10:, 2]
    threshold = last_merges[-1] + (last_merges[-1] - last_merges[-2]) * 0.5

    # Affichage du dendrogramme
    plot_dendrogram(Z, threshold)

    # Nombre de clusters détecté
    n_clusters = sum(Z[:, 2] > threshold) + 1

    # Clustering
    clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    aggregation['cluster'] = clustering.fit_predict(features_scaled)

    print(f"\nNombre de clusters: {n_clusters}")
    print("\nRépartition des clusters:")
    print(aggregation['cluster'].value_counts().sort_index())

    print("\nCaractéristiques moyennes des clusters :")
    print(aggregation.groupby('cluster').mean(numeric_only=True))

    # Visualisation des clusters en 2D (PCA)
    plot_clusters_2d(features_scaled, aggregation['cluster'])

except Exception as e:
    print(f"Erreur : {str(e)}")

finally:
    print("\nTraitement terminé")

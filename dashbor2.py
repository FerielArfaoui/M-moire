import dash
from dash import html, dcc
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import plotly.express as px

# Traduction des jours
days_translation = {
    'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
}

# Date actuelle
current_date = datetime.now().strftime("%d/%m/%Y")
current_day = days_translation.get(datetime.now().strftime("%A"), datetime.now().strftime("%A"))

# Connexion PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:admin123@localhost:5432/Trackingdb")

# Chargement des données
recommandation_stats_df = pd.read_sql("SELECT * FROM recommendation_stats", engine)
users_clusters_df = pd.read_sql("SELECT user_id, cluster, screen_duration FROM user_clusters", engine)

# Graphique : barres recommandation
if not recommandation_stats_df.empty:
    fig_reco = px.bar(
        recommandation_stats_df.melt(var_name="Statistique", value_name="Valeur"),
        x="Statistique", y="Valeur", title="Statistiques de Recommandation",
        color="Statistique",
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Pastel  # Couleurs personnalisées
    )
else:
    fig_reco = {}

# Graphique : pie clusters utilisateurs
if not users_clusters_df.empty:
    fig_clusters = px.pie(
        users_clusters_df,
        names='cluster',
        title="Répartition des Utilisateurs par Cluster",
        color_discrete_sequence=['#FFB6C1', '#ADD8E6']  # Palette personnalisée avec rose et bleu clair
    )
else:
    fig_clusters = {}

# Créer l'app Dash
app = dash.Dash(__name__)

# Layout avec 2 graphiques côte à côte
app.layout = html.Div(style={'backgroundColor': '#f0f0f0', 'padding': '20px'}, children=[

    # En-tête avec image, texte et date
    html.Div([
        # Colonne pour l'image (à gauche)
        html.Div(html.Img(src='assets/seg.png', style={'width': '150px', 'height': 'auto', 'margin': '0 20px'}),
                 style={'display': 'inline-block', 'verticalAlign': 'middle'}),

        # Colonne pour la phrase (au centre)
        html.Div('Tableau de Bord de Segmentation des Clients et Recommandations Personnalisées', style={
            'display': 'inline-block',
            'verticalAlign': 'middle',
            'fontSize': '24px',
            'fontWeight': 'bold',
            'padding': '10px',
            'backgroundColor': '#d3d3d3',
            'borderRadius': '10px',
            'flex': 1}),

        # Colonne pour la date (à droite)
        html.Div(f"{current_day} : {current_date}", style={
            'display': 'inline-block',
            'verticalAlign': 'middle',
            'fontSize': '18px',
            'padding': '10px',
            'marginLeft': '20px'})
    ], style={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

    # Conteneur des 2 graphiques côte à côte
    html.Div([
        html.Div([dcc.Graph(figure=fig_reco)], style={'width': '50%', 'padding': '10px'}),
        html.Div([dcc.Graph(figure=fig_clusters)], style={'width': '50%', 'padding': '10px'})
    ], style={'display': 'flex', 'justifyContent': 'space-between'})
])

# Lancement
if __name__ == '__main__':
    app.run(port=8051, debug=True)

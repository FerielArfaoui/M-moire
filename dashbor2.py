import dash
from dash import html, dcc
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import plotly.express as px

# Traduction des jours en français
days_translation = {
    'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
}

# Date actuelle
current_date = datetime.now().strftime("%d/%m/%Y")
current_day = days_translation.get(datetime.now().strftime("%A"), datetime.now().strftime("%A"))

# Connexion à PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:admin123@localhost:5432/Trackingdb")

# Chargement des données
recommandation_stats_df = pd.read_sql("SELECT * FROM recommendation_stats", engine)

clusters_df = pd.read_sql("""
    SELECT user_id, cluster_event_type, cluster_system, cluster_screen_duration, cluster_manufacturer 
    FROM user_clustering_results
""", engine)

# Couleurs pastel sans jaune
soft_colors = ['#FF6F61', '#5DADE2', '#AAB7B8', '#AF7AC5', '#58D68D', '#34495E']

# Couleurs spécifiques pour donut chart fabricant
donut_colors = ['#6A0DAD', '#9B59B6', '#8E44AD', '#BB8FCE', '#4A235A', '#D2B4DE', '#7D3C98']

# Couleurs modifiées pour "Répartition par Système" (pas de jaune)
system_colors = ['#5DADE2', '#AF7AC5', '#58D68D', '#FF6F61', '#34495E', '#AAB7B8']

# Fonctions de graphiques
def create_pie_chart(df, cluster_col, title, colors):
    if df.empty:
        return {}
    counts = df[cluster_col].value_counts().reset_index()
    counts.columns = [cluster_col, 'count']
    fig = px.pie(
        counts,
        names=cluster_col,
        values='count',
        title=title,
        color_discrete_sequence=colors,
        hole=0
    )
    fig.update_layout(legend_title_text='Cluster', height=300)
    return fig

def create_donut_chart(df, cluster_col, title, colors):
    if df.empty:
        return {}
    counts = df[cluster_col].value_counts().reset_index()
    counts.columns = [cluster_col, 'count']
    fig = px.pie(
        counts,
        names=cluster_col,
        values='count',
        title=title,
        color_discrete_sequence=colors,
        hole=0.4
    )
    fig.update_layout(legend_title_text='Cluster', height=300)
    return fig

def create_bar_chart(df, cluster_col, title, colors):
    if df.empty:
        return {}
    counts = df[cluster_col].value_counts().reset_index()
    counts.columns = [cluster_col, 'count']
    fig = px.bar(
        counts,
        x=cluster_col,
        y='count',
        title=title,
        color=cluster_col,
        color_discrete_sequence=colors
    )
    fig.update_layout(height=300)
    return fig

# Création des figures
fig_event_type = create_pie_chart(clusters_df, 'cluster_event_type', "Répartition par Type d'Événement", soft_colors)
fig_system = create_bar_chart(clusters_df, 'cluster_system', "Répartition par Système", system_colors)
fig_screen_duration = create_bar_chart(clusters_df, 'cluster_screen_duration', "Durée des Sessions (Cluster)", soft_colors)
fig_manufacturer = create_donut_chart(clusters_df, 'cluster_manufacturer', "Répartition par Fabricant", donut_colors)

# Graphe de recommandations
if not recommandation_stats_df.empty:
    reco_df = recommandation_stats_df.melt(var_name="Statistique", value_name="Valeur")
    fig_reco = px.bar(
        reco_df,
        x="Statistique",
        y="Valeur",
        title="Statistiques de Recommandation",
        color="Statistique",
        color_discrete_sequence=soft_colors
    )
    fig_reco.update_layout(height=300)
else:
    fig_reco = {}

# Initialisation Dash
app = dash.Dash(__name__)
app.title = "Dashboard Clustering & Recommandation"

# Layout
app.layout = html.Div(style={'backgroundColor': '#f9f9f9', 'padding': '15px'}, children=[

    html.Div([
        html.Div(html.Img(src='assets/seg.png', style={'width': '120px', 'height': 'auto'}),
                 style={'display': 'inline-block', 'verticalAlign': 'middle'}),

        html.Div('Tableau de Bord de Segmentation des Clients et Recommandations Personnalisées', style={
            'display': 'inline-block',
            'verticalAlign': 'middle',
            'fontSize': '20px',
            'fontWeight': 'bold',
            'padding': '10px 20px',
            'color': '#333333',
            'border': '2px solid #888888',
            'borderRadius': '10px',
            'backgroundColor': '#e6e6e6',
            'textAlign': 'center',
            'margin': '0 10px'
        }),

        html.Div(f"{current_day} : {current_date}", style={
            'display': 'inline-block',
            'verticalAlign': 'middle',
            'fontSize': '16px',
            'padding': '5px',
            'color': '#555555'})
    ], style={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

    html.Hr(),

    html.Div([dcc.Graph(figure=fig_reco)], style={'width': '100%', 'padding': '5px'}),

    html.Div([
        html.Div([dcc.Graph(figure=fig_event_type)], style={'width': '45%', 'display': 'inline-block', 'padding': '5px'}),
        html.Div([dcc.Graph(figure=fig_system)], style={'width': '45%', 'display': 'inline-block', 'padding': '5px'}),
        html.Div([dcc.Graph(figure=fig_screen_duration)], style={'width': '45%', 'display': 'inline-block', 'padding': '5px'}),
        html.Div([dcc.Graph(figure=fig_manufacturer)], style={'width': '45%', 'display': 'inline-block', 'padding': '5px'}),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})
])

# Lancement
if __name__ == '__main__':
    app.run(port=8051, debug=True)


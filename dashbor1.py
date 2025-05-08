import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px
from datetime import datetime
from sqlalchemy import create_engine

# Créer l'app Dash
app = dash.Dash(__name__)

# Paramètres de connexion à PostgreSQL
dbname = 'Agregation'
user = 'postgres'
password = 'admin123'
host = 'localhost'
port = '5432'

# Construire l'URL de connexion SQLAlchemy
connection_url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'

try:
    # Créer l'engine SQLAlchemy
    engine = create_engine(connection_url)
    conn = engine.connect()
    print("Connexion à la base de données réussie !")
except Exception as e:
    print(f"Erreur de connexion : {e}")
    conn = None

if conn:
    # Lire les tables via SQLAlchemy
    df_global = pd.read_sql("SELECT * FROM global_stats", conn)
    df_page = pd.read_sql("SELECT * FROM page_stats", conn)
    conn.close()

    # Date et jour
    current_date = datetime.now().strftime("%d/%m/%Y")
    current_day = datetime.now().strftime("%A")
    days_translation = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
    }
    current_day_fr = days_translation.get(current_day, current_day)

    # Graphique global_stats avec couleurs personnalisées
    fig_global = px.bar(df_global, x="status", y="count", text_auto=True,
                        title="Statistiques Globales",
                        labels={"status": "Statut", "count": "Nombre"},
                        color="status",
                        color_discrete_sequence=["#4CAF50", "#FF5722", "#2196F3", "#9C27B0"])
    fig_global.update_layout(plot_bgcolor="#fafafa", paper_bgcolor="#fafafa")

    # Pie chart page_stats avec le nombre et pourcentage
    df_page_agg = df_page.groupby('page')['count'].sum().reset_index()
    fig_page = px.pie(df_page_agg, names='page', values='count',
                      title="Répartition des Pages",
                      color_discrete_sequence=px.colors.sequential.RdBu)

    # Ajouter les nombres et pourcentages dans le pie chart
    fig_page.update_traces(textinfo='percent+label+value')

    fig_page.update_layout(plot_bgcolor="#fafafa", paper_bgcolor="#fafafa")

    # Layout Dash
    app.layout = html.Div(style={'backgroundColor': '#eaeaea', 'padding': '10px'}, children=[
        html.Div([
            html.Div(html.Img(src='assets/stat.jpg', style={'width': '120px', 'height': 'auto', 'margin': '0 10px'}),
                     style={'display': 'inline-block', 'verticalAlign': 'middle'}),

            html.Div('Tableau de bord des statistiques d\'abonnement', style={
                'display': 'inline-block',
                'verticalAlign': 'middle',
                'fontSize': '22px',
                'fontWeight': 'bold',
                'padding': '8px',
                'backgroundColor': '#cccccc',
                'borderRadius': '8px',
                'flex': 1}),

            html.Div(f"{current_day_fr} : {current_date}", style={
                'display': 'inline-block',
                'verticalAlign': 'middle',
                'fontSize': '16px',
                'padding': '8px',
                'marginLeft': '10px'})
        ], style={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

        html.Div([
            html.Div([
                html.H4("Graphique des Statistiques Globales", style={'textAlign': 'center'}),
                dcc.Graph(figure=fig_global, config={'displayModeBar': False})
            ], style={'width': '38%', 'display': 'inline-block', 'verticalAlign': 'top', 'backgroundColor': '#ffffff',
                      'padding': '10px', 'borderRadius': '10px', 'boxShadow': '2px 2px 8px rgba(0,0,0,0.1)'}),

            html.Div([
                html.H4("Répartition des Pages", style={'textAlign': 'center'}),  # Déplacer le titre en haut
                dcc.Graph(figure=fig_page, config={'displayModeBar': False})
            ], style={'width': '38%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%',
                      'backgroundColor': '#ffffff', 'padding': '10px', 'borderRadius': '10px',
                      'boxShadow': '2px 2px 8px rgba(0,0,0,0.1)'})
        ], style={'marginTop': '20px'})
    ])

    if __name__ == '__main__':
        app.run(debug=True)

else:
    print("Impossible de récupérer les données. Vérifie la connexion à la base de données.")


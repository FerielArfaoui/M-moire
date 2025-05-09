import dash
from dash import html, dcc, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import create_engine

# Créer l'app Dash
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

# Paramètres de connexion PostgreSQL
dbname = 'Agregation'
user = 'postgres'
password = 'admin123'
host = 'localhost'
port = '5432'

connection_url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'

try:
    engine = create_engine(connection_url)
    conn = engine.connect()
    print("Connexion réussie à PostgreSQL !")
except Exception as e:
    print(f"Erreur de connexion : {e}")
    conn = None

if conn:
    # Lire les tables
    df_global = pd.read_sql("SELECT * FROM global_stats", conn)
    df_page = pd.read_sql("SELECT * FROM page_stats", conn)
    df_active_users = pd.read_sql("SELECT * FROM active_users_per_day", conn)
    df_avg_events = pd.read_sql("SELECT * FROM avg_events_per_session", conn)
    df_avg_screen_duration = pd.read_sql("SELECT * FROM avg_screen_duration_per_user", conn)
    df_device_summary = pd.read_sql("SELECT * FROM device_summary", conn)
    df_event_summary = pd.read_sql("SELECT * FROM event_summary", conn)
    df_total_duration = pd.read_sql("SELECT * FROM total_duration", conn)
    conn.close()

    # Date et jour
    current_date = datetime.now().strftime("%d/%m/%Y")
    current_day = datetime.now().strftime("%A")
    days_translation = {'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi', 'Thursday': 'Jeudi',
                        'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'}
    current_day_fr = days_translation.get(current_day, current_day)

    # Créer les dates disponibles dans df_active_users
    available_dates = sorted(pd.to_datetime(df_active_users['date']).dt.date.unique())

    # Layout
    app.layout = html.Div(style={'backgroundColor': '#eaeaea', 'padding': '10px'}, children=[

        html.Div([
            html.Div(html.Img(src='assets/stat.jpg', style={'width': '120px', 'height': 'auto'}),
                     style={'display': 'inline-block', 'verticalAlign': 'middle'}),
            html.Div('Tableau de bord pour le suivi des utilisateurs sur des sites e-commerce', style={
                'display': 'inline-block', 'verticalAlign': 'middle',
                'fontSize': '24px', 'fontWeight': 'bold',
                'padding': '10px', 'backgroundColor': '#cccccc',
                'borderRadius': '8px'}),
            html.Div(f"{current_day_fr} : {current_date}", style={
                'display': 'inline-block', 'verticalAlign': 'middle',
                'fontSize': '20px', 'padding': '12px', 'marginLeft': '14px'})
        ], style={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

        html.Div([
            html.Div([
                html.H4("Filtre Date", style={'textAlign': 'center'}),
                dcc.DatePickerRange(
                    id='date-range',
                    min_date_allowed=min(available_dates),
                    max_date_allowed=max(available_dates),
                    start_date=min(available_dates),
                    end_date=max(available_dates),
                    display_format='DD/MM/YYYY'
                ),
                html.Br(),
                html.Br(),
                html.H5("Sélection rapide"),
                dcc.Dropdown(
                    id='quick-filter',
                    options=[
                        {'label': 'Aujourd\'hui', 'value': 'day'},
                        {'label': 'Cette Semaine', 'value': 'week'},
                        {'label': 'Ce Mois', 'value': 'month'},
                        {'label': 'Cette Année', 'value': 'year'}
                    ],
                    placeholder="Choisir une période"
                )
            ], style={'width': '10%', 'backgroundColor': '#fff', 'padding': '8px', 'borderRadius': '6px',
                      'display': 'inline-block', 'verticalAlign': 'top'}),

            html.Div([  # CONTENEUR PRINCIPAL DES GRAPHIQUES
                html.Div([
                    html.Div([
                        html.H4("Statistiques Globales", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_global', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),

                    html.Div([
                        html.H4("Répartition des Pages", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_page', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),

                    html.Div([
                        html.H4("Utilisateurs Actifs par Jour", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_active_users', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),

                    html.Div([
                        html.H4("Moyenne des Événements par Session", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_avg_events', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),
                ], style={'display': 'flex', 'gap': '1%', 'marginTop': '20px'}),

                html.Div([
                    html.Div([
                        html.H4("Durée Moyenne d’Écran par Utilisateur", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_avg_screen_duration', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),

                    html.Div([
                        html.H4("Résumé par Appareil", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_device_summary', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),

                    html.Div([
                        html.H4("Résumé des Événements par Utilisateur", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_event_summary', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),

                    html.Div([
                        html.H4("Durée Totale par Utilisateur", style={'textAlign': 'center'}),
                        dcc.Graph(id='fig_total_duration', config={'displayModeBar': False})
                    ], style={'width': '24%', 'backgroundColor': '#fff', 'padding': '10px', 'borderRadius': '10px'}),
                ], style={'display': 'flex', 'gap': '1%', 'marginTop': '20px'})
            ], style={'width': '83%', 'display': 'inline-block', 'marginLeft': '1%'})
        ])
    ])

    # CALLBACK
    @app.callback(
        Output('fig_global', 'figure'),
        Output('fig_page', 'figure'),
        Output('fig_active_users', 'figure'),
        Output('fig_avg_events', 'figure'),
        Output('fig_avg_screen_duration', 'figure'),
        Output('fig_device_summary', 'figure'),
        Output('fig_event_summary', 'figure'),
        Output('fig_total_duration', 'figure'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
        Input('quick-filter', 'value')
    )
    def update_graphs(start_date, end_date, quick_filter):
        # Appliquer filtre rapide
        now = datetime.now()
        if quick_filter == 'day':
            start_date = end_date = now.date()
        elif quick_filter == 'week':
            start_date = (now - pd.Timedelta(days=now.weekday())).date()
            end_date = now.date()
        elif quick_filter == 'month':
            start_date = now.replace(day=1).date()
            end_date = now.date()
        elif quick_filter == 'year':
            start_date = now.replace(month=1, day=1).date()
            end_date = now.date()

        # Filtrer les DataFrames
        filtered_active_users = df_active_users[
            (pd.to_datetime(df_active_users['date']).dt.date >= pd.to_datetime(start_date).date()) &
            (pd.to_datetime(df_active_users['date']).dt.date <= pd.to_datetime(end_date).date())
        ]

        filtered_global = df_global  # ajouter filtre si besoin
        filtered_page = df_page
        filtered_avg_events = df_avg_events
        filtered_avg_screen_duration = df_avg_screen_duration
        filtered_device_summary = df_device_summary
        filtered_event_summary = df_event_summary
        filtered_total_duration = df_total_duration

        # Graphiques
        fig_global = px.bar(filtered_global, x="status", y="count", text_auto=True, color="status",
                            title="Statistiques Globales", color_discrete_sequence=px.colors.qualitative.Set2)

        fig_page = px.pie(filtered_page.groupby('page')['count'].sum().reset_index(), names='page', values='count',
                          title="Répartition des Pages", color_discrete_sequence=px.colors.sequential.RdBu)
        fig_page.update_traces(textinfo='percent+label+value')

        fig_active_users = px.line(filtered_active_users, x='date', y='active_user_count', markers=True,
                                   title="Utilisateurs Actifs par Jour")

        fig_avg_events = px.bar(filtered_avg_events, x='user', y='avg_events', text_auto=True,
                                title="Moyenne des Événements par Session par Utilisateur")

        fig_avg_screen_duration = go.Figure()
        for user_id in filtered_avg_screen_duration['user_id'].unique():
            user_data = filtered_avg_screen_duration[filtered_avg_screen_duration['user_id'] == user_id]
            fig_avg_screen_duration.add_trace(go.Bar(x=[user_id], y=user_data['avg_screen_duration'], name=str(user_id)))
        fig_avg_screen_duration.update_layout(barmode='stack', title="Durée Moyenne d’Écran par Utilisateur",
                                              xaxis_title="Utilisateur", yaxis_title="Durée Moyenne (s)")

        fig_device_summary = go.Figure(go.Waterfall(
            x=filtered_device_summary['device'], y=filtered_device_summary['total_events'],
            textposition="outside", connector={"line": {"color": "rgb(63, 63, 63)"}}))
        fig_device_summary.update_layout(title="Résumé par Appareil")

        event_totals = filtered_event_summary[['event_clicks', 'event_views', 'event_scrolls']].sum()
        fig_event_summary = px.pie(names=event_totals.index, values=event_totals.values, hole=0.4,
                                   title="Résumé des Événements par Utilisateur")
        fig_event_summary.update_traces(textinfo='percent+label+value')

        fig_total_duration = px.bar(filtered_total_duration, x='user', y='total_duration', text_auto=True,
                                    title="Durée Totale par Utilisateur")

        return (fig_global, fig_page, fig_active_users, fig_avg_events, fig_avg_screen_duration,
                fig_device_summary, fig_event_summary, fig_total_duration)

    if __name__ == '__main__':
        app.run(debug=True)

else:
    print("Impossible de récupérer les données. Vérifie la connexion à la base de données.")


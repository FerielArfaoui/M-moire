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
current_date = datetime.now().strftime("%d/%m/%Y")
current_day = days_translation.get(datetime.now().strftime("%A"), datetime.now().strftime("%A"))

# Connexion à PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:admin123@localhost:5432/Trackingdb")

# Lecture des données
reco_df = pd.read_sql("SELECT * FROM recommendation_stats", engine)
clusters_df = pd.read_sql("""
    SELECT user_id, cluster_event_type, cluster_system, cluster_screen_duration, cluster_manufacturer 
    FROM user_clustering_results
""", engine)

# Couleurs
main_colors = ['#3498DB', '#1ABC9C', '#F39C12', '#9B59B6', '#E74C3C', '#34495E', '#FF6B6B', '#4ECDC4']


def create_graph_from_category(df, category):
    sub_df = df[df['metric_category'] == category]
    if sub_df.empty:
        return None

    fig = px.bar(
        sub_df,
        x='metric_name',
        y='value',
        color='metric_name',
        text='value',
        title=f"Recommandations - {category}",
        color_discrete_sequence=main_colors
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition="outside",
        textfont_size=12,
        textfont_color="black"
    )

    max_val = sub_df['value'].max()
    fig.update_yaxes(range=[0, max_val * 1.15])

    fig.update_layout(
        height=320,
        xaxis_title="Métriques",
        yaxis_title="Valeurs",
        showlegend=False,
        title_x=0.5,
        title_font_size=16,
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=60, b=50, l=50, r=50)
    )

    return fig


def create_pie_chart(df, cluster_col, title, colors):
    counts = df[cluster_col].value_counts().reset_index()
    counts.columns = [cluster_col, 'count']

    fig = px.pie(
        counts,
        names=cluster_col,
        values='count',
        title=title,
        color_discrete_sequence=colors
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label+value',
        textfont_size=12,
        pull=[0.05] * len(counts)
    )

    fig.update_layout(
        height=320,
        title_x=0.5,
        title_font_size=16,
        font=dict(size=12),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
        margin=dict(t=60, b=50, l=50, r=100)
    )

    return fig


def create_bar_chart(df, cluster_col, title, colors):
    counts = df[cluster_col].value_counts().reset_index()
    counts.columns = [cluster_col, 'count']

    fig = px.bar(
        counts,
        x=cluster_col,
        y='count',
        title=title,
        color=cluster_col,
        color_discrete_sequence=colors,
        text='count'
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition="outside",
        textfont_size=12,
        textfont_color="black"
    )

    max_val = counts['count'].max()
    fig.update_yaxes(range=[0, max_val * 1.15])

    fig.update_layout(
        height=320,
        showlegend=False,
        title_x=0.5,
        title_font_size=16,
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_title="Catégories",
        yaxis_title="Nombre d'utilisateurs",
        margin=dict(t=60, b=50, l=50, r=50)
    )

    return fig


def create_donut_chart(df, cluster_col, title, colors):
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

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label+value',
        textfont_size=12,
        pull=[0.03] * len(counts)
    )

    total_users = counts['count'].sum()
    fig.add_annotation(
        text=f"Total<br>{total_users}",
        x=0.5, y=0.5,
        font_size=16,
        showarrow=False
    )

    fig.update_layout(
        height=320,
        title_x=0.5,
        title_font_size=16,
        font=dict(size=12),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
        margin=dict(t=60, b=50, l=50, r=100)
    )

    return fig


def create_summary_cards(reco_df, clusters_df):
    total_recommendations = len(reco_df)
    total_users = len(clusters_df)
    avg_value = reco_df['value'].mean() if not reco_df.empty else 0

    return html.Div([
        html.Div([
            html.H3(f"{total_recommendations}", style={'color': '#3498DB'}),
            html.P("Total Recommandations")
        ], style=card_style),

        html.Div([
            html.H3(f"{total_users}", style={'color': '#1ABC9C'}),
            html.P("Utilisateurs Segmentés")
        ], style=card_style),

        html.Div([
            html.H3(f"{avg_value:.2f}", style={'color': '#F39C12'}),
            html.P("Valeur Moyenne")
        ], style=card_style)
    ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'})


card_style = {
    'backgroundColor': 'white',
    'padding': '20px',
    'borderRadius': '10px',
    'textAlign': 'center',
    'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
    'margin': '10px',
    'width': '200px'
}

# Génération des figures
categories = reco_df['metric_category'].unique()
reco_graphs = []
for category in categories:
    fig = create_graph_from_category(reco_df, category)
    if fig:
        reco_graphs.append(
            dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'width': '48%', 'margin': '10px'})
        )

fig_event_type = dcc.Graph(figure=create_pie_chart(clusters_df, 'cluster_event_type', "Répartition par Type d'Événement", main_colors), config={'displayModeBar': False}, style={'width': '48%', 'margin': '10px'})
fig_system = dcc.Graph(figure=create_bar_chart(clusters_df, 'cluster_system', "Répartition par Système", main_colors), config={'displayModeBar': False}, style={'width': '48%', 'margin': '10px'})
fig_screen_duration = dcc.Graph(figure=create_bar_chart(clusters_df, 'cluster_screen_duration', "Durée des Sessions", main_colors), config={'displayModeBar': False}, style={'width': '48%', 'margin': '10px'})
fig_manufacturer = dcc.Graph(figure=create_donut_chart(clusters_df, 'cluster_manufacturer', "Répartition par Fabricant", main_colors), config={'displayModeBar': False}, style={'width': '48%', 'margin': '10px'})

summary_cards = create_summary_cards(reco_df, clusters_df)

# Application Dash
app = dash.Dash(__name__)
app.title = "Dashboard Clustering & Recommandation"

app.layout = html.Div(style={
    'backgroundColor': '#f5f5f5',
    'padding': '20px',
    'fontFamily': 'Arial, sans-serif'
}, children=[
    html.Div([
        html.Div([html.Img(src='assets/seg.png', style={'width': '120px'})], style={'flex': '1'}),
        html.Div([
            html.H1('Tableau de Bord - Segmentation & Recommandation', style={'fontSize': '24px', 'color': '#2c3e50'}),
            html.P(f"{current_day} : {current_date}", style={'fontSize': '16px', 'color': '#7f8c8d'})
        ], style={'flex': '3', 'textAlign': 'center'}),
        html.Div(style={'flex': '1'})
    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '15px',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
        'marginBottom': '30px'
    }),

    summary_cards,

    html.Hr(style={'margin': '30px 0', 'border': '1px solid #ddd'}),

    html.H2("📊 Analyse des Recommandations", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.Div(reco_graphs, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

    html.Hr(style={'margin': '30px 0', 'border': '1px solid #ddd'}),

    html.H2("🎯 Segmentation des Utilisateurs", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.Div([fig_event_type, fig_system, fig_screen_duration, fig_manufacturer],
             style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

    html.Div([
        html.P(f"Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px'})
    ], style={'marginTop': '30px'})
])

if __name__ == '__main__':
    app.run(debug=True, port=8051)



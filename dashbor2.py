import dash
from dash import html
from datetime import datetime

# Créer l'app Dash
app = dash.Dash(__name__)

# Obtenir la date système et le jour de la semaine en français
current_date = datetime.now().strftime("%d/%m/%Y")
current_day = datetime.now().strftime("%A")

# Traduire le jour de la semaine en français
days_translation = {
    'Monday': 'Lundi',
    'Tuesday': 'Mardi',
    'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi',
    'Friday': 'Vendredi',
    'Saturday': 'Samedi',
    'Sunday': 'Dimanche'
}
current_day_fr = days_translation.get(current_day, current_day)

# Layout
app.layout = html.Div(style={'backgroundColor': '#f0f0f0', 'padding': '20px'}, children=[
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
        html.Div(f"{current_day_fr} : {current_date}", style={
            'display': 'inline-block',
            'verticalAlign': 'middle',
            'fontSize': '18px',
            'padding': '10px',
            'marginLeft': '20px'})
    ], style={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'})
])

# Changer le port du serveur
if __name__ == '__main__':
    app.run(port=8051)

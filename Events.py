from influxdb import InfluxDBClient

# Connexion à la base InfluxDB
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
client.switch_database('events')

# Liste des types d'événements à tester
event_types = ['click', 'scroll', 'view']
event_names = {"click": "click", "scroll": "scroll", "view": "view"}

# --- Répartition globale des événements par type ---
print("Répartition des événements par type :")
for event_type in event_types:
    query = f'SELECT COUNT("event_type") FROM "user_event" WHERE "event_type" = \'{event_type}\''
    result = client.query(query)

    try:
        count = result.raw['series'][0]['values'][0][1]
    except (KeyError, IndexError):
        count = 0  # Aucun résultat trouvé pour ce type

    nom = event_names.get(event_type, event_type)
    print(f"{nom} : {count}")

# Définir les types d'événements
event_names_fr = {"click": "click", "scroll": "scroll", "view": "view"}
event_order = ["click", "view", "scroll"]

# Initialiser un dictionnaire pour stocker les résultats
users = {}

# Requête pour chaque type d'événement
for etype in event_order:
    query = f'SELECT COUNT("event_type") FROM "user_event" WHERE "event_type" = \'{etype}\' GROUP BY "user"'
    results = client.query(query)

    # Récupérer les résultats de la requête
    for item in results.raw.get('series', []):
        user_id = item.get("tags", {}).get("user", "inconnu")
        count = item.get("values", [[None, 0]])[0][1]

        # Ajouter les résultats dans le dictionnaire
        if user_id not in users:
            users[user_id] = {}
        users[user_id][etype] = int(count)

# Afficher les résultats sous le format voulu
print("\nNombre total d'événements par type pour chaque utilisateur :")
for user_id, events in sorted(users.items()):
    parts = []
    for event in event_order:
        count = events.get(event, 0)
        parts.append(f"{count} {event_names_fr.get(event, f'{event}s')}")
    print(f"{user_id} : {', '.join(parts)}")

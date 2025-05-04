from influxdb import InfluxDBClient
from datetime import datetime, timedelta, timezone
import psycopg2
import matplotlib.pyplot as plt

# Connexion à InfluxDB
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
client.switch_database('subscribe')

# Connexion à PostgreSQL
try:
    conn = psycopg2.connect(
        dbname='Agregation',
        user='postgres',
        password='admin123',
        host='localhost',
        port=5432
    )
    print("Connexion réussie à PostgreSQL")
except Exception as e:
    print(f"Erreur de connexion à PostgreSQL : {e}")
cursor = conn.cursor()

# Statuts connus
status_list = ["completed", "abandoned", "in_progress", "blocked"]

def get_user_progression():
    """Récupère la progression maximale et le statut final de chaque utilisateur"""
    query = 'SELECT "status", "user", "page" FROM "user_subscription"'
    results = client.query(query)

    user_progress = {}
    for point in results.get_points():
        user_id = point['user']
        status = point['status']
        page = point['page']

        if user_id not in user_progress:
            user_progress[user_id] = {
                'max_page': page,
                'final_status': status
            }
        else:
            # Mettre à jour la page maximale
            if page > user_progress[user_id]['max_page']:
                user_progress[user_id]['max_page'] = page

            # Mettre à jour le statut final selon la priorité
            current_status = user_progress[user_id]['final_status']
            status_priority = {
                'completed': 4,
                'abandoned': 3,
                'in_progress': 2,
                'blocked': 1
            }
            if status_priority[status] > status_priority.get(current_status, 0):
                user_progress[user_id]['final_status'] = status

    return user_progress


def get_page_stats(user_progress):
    """Calcule les statistiques par page finale atteinte"""
    page_stats = {page: {status: 0 for status in status_list} for page in range(1, 8)}

    for user_data in user_progress.values():
        page = user_data['max_page']
        status = user_data['final_status']
        if 1 <= page <= 7 and status in status_list:
            page_stats[page][status] += 1

    return page_stats


def get_global_stats(user_progress):
    """Calcule les statistiques globales"""
    global_stats = {status: 0 for status in status_list}
    for user_data in user_progress.values():
        status = user_data['final_status']
        if status in global_stats:
            global_stats[status] += 1
    return global_stats


def get_daily_progression():
    """Calcule la progression quotidienne sur 7 jours"""
    daily_stats = []
    now = datetime.now(timezone.utc)

    for i in range(7):
        day = now - timedelta(days=i)
        query = f'''
            SELECT "user", "status", "page" 
            FROM "user_subscription" 
            WHERE time >= '{day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()}' 
            AND time < '{day.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()}'
        '''
        results = client.query(query)

        daily_users = {}
        for point in results.get_points():
            user_id = point['user']
            status = point['status']
            page = point['page']

            if user_id not in daily_users:
                daily_users[user_id] = {
                    'max_page': page,
                    'final_status': status
                }
            else:
                if page > daily_users[user_id]['max_page']:
                    daily_users[user_id]['max_page'] = page
                # Mise à jour du statut selon la priorité
                current_status = daily_users[user_id]['final_status']
                status_priority = {
                    'completed': 4,
                    'abandoned': 3,
                    'in_progress': 2,
                    'blocked': 1
                }
                if status_priority[status] > status_priority.get(current_status, 0):
                    daily_users[user_id]['final_status'] = status

        daily_stats.append((day.date(), daily_users))

    return reversed(daily_stats)


# Récupération des données
user_progress = get_user_progression()
global_stats = get_global_stats(user_progress)
page_stats = get_page_stats(user_progress)
daily_stats = get_daily_progression()

# Insertion des résultats dans PostgreSQL

# Insertion des statistiques globales
for status, count in global_stats.items():
    cursor.execute("""
        INSERT INTO global_stats (status, count)
        VALUES (%s, %s)
        """, (status, count))
    conn.commit()

# Insertion des statistiques par page finale
for page in range(1, 8):
    for status in status_list:
        count = page_stats[page][status]
        cursor.execute("""
            INSERT INTO page_stats (page, status, count)
            VALUES (%s, %s, %s)
            """, (page, status, count))
        conn.commit()

# Insertion des statistiques journalières
for date, users in daily_stats:
    for user_data in users.values():
        status = user_data['final_status']
        cursor.execute("""
            INSERT INTO daily_stats (date, status, count)
            VALUES (%s, %s, %s)
            """, (date, status, 1))  # Chaque utilisateur est compté une fois par statut et par jour
        conn.commit()



# Fermeture de la connexion PostgreSQL
cursor.close()
conn.close()


from influxdb import InfluxDBClient
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt

# Connexion à InfluxDB
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
client.switch_database('subscribe')

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

# Affichage des résultats
total_users = len(user_progress)
print(f"👥 Utilisateurs uniques: {total_users}\n")

print("📊 Statistiques globales:")
for status, count in global_stats.items():
    print(f"- {status.capitalize()}: {count} ({(count / total_users * 100):.1f}%)")

print("\n📈 Progression par page finale:")
for page in range(1, 8):
    print(f"\n➡️ Page {page}:")
    total = sum(page_stats[page].values())
    for status in status_list:
        count = page_stats[page][status]
        print(f"  - {status.capitalize()}: {count} ({(count / total * 100 if total > 0 else 0):.1f}%)")

print("\n📅 Statistiques journalières:")
for date, users in daily_stats:
    print(f"\n🗓️ {date}:")
    daily_total = len(users)
    stats = {status: 0 for status in status_list}
    for user_data in users.values():
        stats[user_data['final_status']] += 1

    for status in status_list:
        count = stats[status]
        print(f"  - {status.capitalize()}: {count} ({(count / daily_total * 100 if daily_total > 0 else 0):.1f}%)")

# Visualisation graphique
pages = list(range(1, 8))
status_data = {status: [page_stats[page][status] for page in pages] for status in status_list}

plt.figure(figsize=(12, 6))
bottom = [0] * 7

for status, color in zip(status_list, ['green', 'red', 'blue', 'orange']):
    plt.bar(pages, status_data[status], bottom=bottom, label=status.capitalize(), color=color)
    bottom = [i + j for i, j in zip(bottom, status_data[status])]

plt.title("Répartition des statuts par page finale atteinte")
plt.xlabel("Page finale atteinte")
plt.ylabel("Nombre d'utilisateurs")
plt.xticks(pages)
plt.legend()
plt.show()
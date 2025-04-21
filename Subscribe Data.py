import random
from influxdb import InfluxDBClient
from datetime import datetime, timedelta

# Connexion à InfluxDB
client = InfluxDBClient(host='localhost', port=8087, username='Feriel', password='admin123')
client.switch_database('subscribe')

# Paramètres
total_users = 2000
total_pages = 7
days_range = 7  # sur 7 jours
abandon_probability = 0.4  # 40% des users abandonnent
block_probability = 0.2  # 20% des users peuvent être bloqués


# Générer une date aléatoire sur 7 jours
def get_random_time_for_day(day_offset):
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    random_second = random.randint(0, 59)
    return now - timedelta(days=day_offset) + timedelta(hours=random_hour, minutes=random_minute, seconds=random_second)


# Générer les données
for user_id in range(1, total_users + 1):
    user_name = f"user{user_id}"
    abandon = random.random() < abandon_probability
    block = random.random() < block_probability  # Est-ce que l'utilisateur est bloqué ?

    abandon_page = random.randint(1, total_pages - 1) if abandon else None
    block_page = random.randint(1, total_pages - 1) if block else None
    day_offset = random.randint(0, days_range - 1)

    points = []

    for page in range(1, total_pages + 1):
        if block and page == block_page:
            status = "blocked"
        elif abandon and page == abandon_page:
            status = "abandoned"
        elif page == total_pages and not abandon:
            status = "completed"
        else:
            status = "in_progress"

        point = {
            "measurement": "user_subscription",
            "tags": {
                "user": user_name,
            },
            "time": get_random_time_for_day(day_offset).isoformat(),
            "fields": {
                "page": page,
                "status": status
            }
        }

        points.append(point)

        if status == "abandoned" or status == "blocked":
            break  # Si l'utilisateur abandonne ou est bloqué, pas de pages suivantes

    # Écriture dans InfluxDB
    client.write_points(points)

print("✅ 2000 utilisateurs simulés avec succès, avec abandon et blocage, et insérés dans la base 'subscribe'.")

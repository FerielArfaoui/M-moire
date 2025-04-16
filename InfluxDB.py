import http.server
import socketserver
import json
from influxdb import InfluxDBClient  # ✅ Pour InfluxDB v1
import time
import uuid
import random
import requests

# Port du serveur local
PORT = 4000

# Constantes
TOTAL_USERS = 50
MIN_SESSIONS_PER_USER = 5
MAX_SESSIONS_PER_USER = 10
PAGES = [f"Page_{i}" for i in range(1, 51)]

# Configuration InfluxDB v1
INFLUX_HOST = 'localhost'
INFLUX_PORT = 8087 # ⚠️ Assure-toi que c'est bien le port de ton InfluxDB v1
INFLUX_DBNAME = 'events'
INFLUX_USERNAME = 'Feriel'
INFLUX_PASSWORD = 'admin123'

client = InfluxDBClient(
    host=INFLUX_HOST,
    port=INFLUX_PORT,
    username=INFLUX_USERNAME,
    password=INFLUX_PASSWORD,
    database=INFLUX_DBNAME
)


def generate_fake_events():
    current_time = int(time.time())
    events = []

    for user_id in range(1, TOTAL_USERS + 1):
        user = f"user{user_id}"
        num_sessions = random.randint(MIN_SESSIONS_PER_USER, MAX_SESSIONS_PER_USER)

        for _ in range(num_sessions):
            session = f"session-{uuid.uuid4().hex[:6]}"
            num_navigations = random.randint(3, 8)

            for nav_id in range(num_navigations):
                event = {
                    "appInfo": {
                        "projectId": f"proj-{uuid.uuid4().hex[:6]}",
                        "projectName": f"Project_{random.randint(1, 100)}",
                        "versions": {
                            "appVersion": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                            "apiVersion": f"{random.randint(1, 5)}.{random.randint(0, 9)}"
                        },
                        "appInstalledTime": current_time - random.randint(10000, 50000)
                    },
                    "deviceInformation": {
                        "macAddress": ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)]),
                        "deviceModel": f"Device_{random.randint(100, 999)}",
                        "lastUpdateTime": current_time - random.randint(1000, 5000),
                        "manufacturer": random.choice(["Apple", "Samsung", "Google", "OnePlus"]),
                        "systemName": random.choice(["iOS", "Android"]),
                        "systemVersion": f"{random.randint(9, 16)}.{random.randint(0, 9)}"
                    },
                    "navigation": {
                        "previousScreenName": random.choice(PAGES),
                        "currentScreenName": random.choice(PAGES),
                        "navigationParams": {
                            "id": f"nav-{uuid.uuid4().hex[:6]}",
                            "type": random.choice(["menu", "button", "swipe"])
                        }
                    },
                    "eventInformation": {
                        "sessionId": session,
                        "eventId": f"event-{uuid.uuid4().hex[:6]}",
                        "eventData": {
                            "eventType": random.choice(["click", "view", "scroll"]),
                            "testId": f"test-{uuid.uuid4().hex[:6]}"
                        },
                        "ghTypes": {
                            "ghType": "userInteraction",
                            "ghSubType": random.choice(["navigation", "gesture", "tap"])
                        },
                        "timeInformation": {
                            "screenTimeInformation": {
                                "screenStartTime": current_time + (nav_id * 10),
                                "screenEndTime": current_time + (nav_id * 10) + 5
                            },
                            "sectionTimeInterval": {
                                "startTime": current_time + (nav_id * 10),
                                "stopTime": current_time + (nav_id * 10) + 5
                            }
                        }
                    },
                    "payload": {
                        "type": random.choice(["video", "article", "image"]),
                        "category": random.choice(["news", "sports", "entertainment"]),
                        "title": f"Title_{random.randint(1, 100)}",
                        "description": f"Description for event {nav_id + 1}",
                        "tags": [f"tag{random.randint(1, 5)}" for _ in range(random.randint(1, 3))],
                        "sectionTimeInterval": {
                            "startTime": current_time + (nav_id * 10),
                            "stopTime": current_time + (nav_id * 10) + 5
                        },
                        "metadata": {
                            "url": f"https://example.com/resource/{uuid.uuid4().hex[:6]}",
                            "format": random.choice(["mp4", "jpg", "png"]),
                            "language": random.choice(["en", "fr", "es"]),
                            "size": random.randint(500, 5000),
                            "rating": round(random.uniform(1, 5), 1),
                            "geo": {
                                "latitude": round(random.uniform(-90, 90), 6),
                                "longitude": round(random.uniform(-180, 180), 6)
                            }
                        }
                    },
                    "user": user
                }
                events.append(event)

    return events

def send_event_to_external_server(event):
    url = 'http://localhost:8084/events/events'
    headers = {
        'accept': '*/*',
        'hippo-api-version': '1.0.0',
        'Authorization': 'Bearer testtoken:feriel.arfaoui@yoterra.com',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=event, headers=headers)
        print(f"✅ Événement {event['eventInformation']['eventId']} envoyé - Statut: {response.status_code}")
        return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'envoi de l'événement {event['eventInformation']['eventId']}: {e}")
        return 500, str(e)

def write_event_to_influxdb(event):
    point = {
        "measurement": "user_event",
        "tags": {
            "user": event["user"],
            "device": event["deviceInformation"]["deviceModel"],
            "manufacturer": event["deviceInformation"]["manufacturer"],
            "system": event["deviceInformation"]["systemName"]
        },
        "fields": {
            "event_type": event["eventInformation"]["eventData"]["eventType"],
            "screen_duration": event["eventInformation"]["timeInformation"]["screenTimeInformation"]["screenEndTime"]
                               - event["eventInformation"]["timeInformation"]["screenTimeInformation"]["screenStartTime"]
        },
        "time": event["eventInformation"]["timeInformation"]["screenTimeInformation"]["screenStartTime"]
    }

    client.write_points([point])

class FakeDataHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/generate-fake-data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            self.wfile.write(json.dumps({"status": "Processing started"}).encode('utf-8'))

            events = generate_fake_events()
            print("\n🚀 Début de l'envoi des événements...\n")

            for event in events:
                send_event_to_external_server(event)
                write_event_to_influxdb(event)
                time.sleep(0.01)

            print("\n✅ Tous les événements ont été envoyés et stockés dans InfluxDB !\n")

        else:
            self.send_response(404)
            self.end_headers()

# Lancement du serveur
with socketserver.TCPServer(("", PORT), FakeDataHandler) as httpd:
    print(f"🌍 Serveur démarré sur http://localhost:{PORT}")
    print(f"🔗 Accédez à http://localhost:{PORT}/generate-fake-data pour lancer la génération")
    httpd.serve_forever()

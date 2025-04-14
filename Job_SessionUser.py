import pandas as pd
from influxdb_client import InfluxDBClient
import psycopg2
from datetime import datetime

class JobSessionAnalytics:
    def __init__(self):
        # Connexion InfluxDB
        self.influx_client = InfluxDBClient(
            url='http://localhost:8086',
            token='g9qIG9gnh3lykTb_TKZZipn33PGEsv7hnSSNVPRKWhT6pY0SPL4V_sGR7Is5bCswKyCwb42h_W_b1dePdp-NSw==',
            org='Zeus Labs'
        )
        self.bucket = 'events'

        # Connexion PostgreSQL
        self.pg_conn = psycopg2.connect(
            dbname="trackingdb",
            user="postgres",
            password="admin123",
            host="localhost",
            port="5432"
        )
        self.pg_cursor = self.pg_conn.cursor()

    def get_data_from_influx(self):
        query_api = self.influx_client.query_api()
        flux_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "event")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> keep(columns: ["user", "sessionId", "_time", "eventType", "appInfo.deviceType", "location.country"])
        '''
        df = query_api.query_data_frame(flux_query)
        df['_time'] = pd.to_datetime(df['_time'])
        return df.dropna()

    def store_to_postgres(self, df, table_name, columns):
        self.pg_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {", ".join([f"{col} TEXT" if i == 0 else f"{col} FLOAT" for i, col in enumerate(columns)])}
            )
        ''')
        self.pg_cursor.execute(f'DELETE FROM {table_name}')
        for _, row in df.iterrows():
            self.pg_cursor.execute(
                f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({", ".join(["%s"] * len(columns))})',
                tuple(row[col] for col in columns)
            )
        self.pg_conn.commit()

    def run(self):
        print("📥 Chargement des données depuis InfluxDB...")
        df = self.get_data_from_influx()

        # Durée de session
        print("📊 Calcul des durées de sessions...")
        session_durations = df.groupby(['user', 'sessionId'])['_time'].agg(['min', 'max']).reset_index()
        session_durations['duration_sec'] = (session_durations['max'] - session_durations['min']).dt.total_seconds()

        # 1️⃣ Nombre de sessions par utilisateur
        print("🔢 Nombre de sessions par utilisateur...")
        session_counts = session_durations.groupby('user')['sessionId'].nunique().reset_index()
        session_counts.columns = ['user', 'session_count']
        self.store_to_postgres(session_counts, 'session_count_per_user', ['user', 'session_count'])

        # 2️⃣ Durée moyenne des sessions
        print("⏱️ Durée moyenne des sessions...")
        avg_durations = session_durations.groupby('user')['duration_sec'].mean().reset_index()
        avg_durations.columns = ['user', 'avg_session_duration']
        self.store_to_postgres(avg_durations, 'avg_session_duration_per_user', ['user', 'avg_session_duration'])

        # 3️⃣ Nombre de sessions par jour
        print("📆 Sessions par période...")
        df['date'] = df['_time'].dt.date
        sessions_per_day = df.groupby('date')['sessionId'].nunique().reset_index()
        sessions_per_day.columns = ['date', 'session_count']
        sessions_per_day['date'] = sessions_per_day['date'].astype(str)
        self.store_to_postgres(sessions_per_day, 'sessions_per_day', ['date', 'session_count'])

        # 4️⃣ Session la plus longue / la plus courte
        print("📈 Sessions extrêmes...")
        max_min = session_durations.groupby('user')['duration_sec'].agg(['max', 'min']).reset_index()
        max_min.columns = ['user', 'max_session_duration', 'min_session_duration']
        self.store_to_postgres(max_min, 'extreme_session_durations', ['user', 'max_session_duration', 'min_session_duration'])

        # 5️⃣ Moyenne d’actions par session
        print("🖱️ Actions moyennes par session...")
        actions_per_session = df.groupby(['user', 'sessionId']).size().reset_index(name='action_count')
        avg_actions = actions_per_session.groupby('user')['action_count'].mean().reset_index()
        avg_actions.columns = ['user', 'avg_actions_per_session']
        self.store_to_postgres(avg_actions, 'avg_actions_per_session', ['user', 'avg_actions_per_session'])

        # 6️⃣ Répartition par device et pays
        print("🌍 Répartition technique et géographique...")
        geo_tech = df.groupby(['appInfo.deviceType', 'location.country'])['sessionId'].nunique().reset_index()
        geo_tech.columns = ['device_type', 'country', 'session_count']
        self.store_to_postgres(geo_tech, 'session_distribution_device_country', ['device_type', 'country', 'session_count'])

        print("✅ Résultats stockés dans PostgreSQL avec succès.")

# Classe main
class Main:
    def __init__(self):
        job = JobSessionAnalytics()
        job.run()

if __name__ == "__main__":
    Main()

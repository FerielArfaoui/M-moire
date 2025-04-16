import pandas as pd
from influxdb_client import InfluxDBClient
import psycopg2

class JobPageViewAggregation:
    def __init__(self):
        # Connexion InfluxDB
       # Connexion à InfluxDB v1
        self.influx_client = InfluxDBClient(
            host='localhost',
            port=8087
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
          |> keep(columns: ["user", "page", "appInfo.deviceType", "location.country", "_time", "duration"])
        '''
        tables = query_api.query_data_frame(flux_query)
        df = pd.concat(tables) if isinstance(tables, list) else tables
        return df.dropna()

    def store_to_postgres(self, df, table_name, columns):
        self.pg_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {", ".join([f"{col} TEXT" if i != len(columns)-1 else f"{col} INTEGER" for i, col in enumerate(columns)])}
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
        print("📥 Lecture des données InfluxDB...")
        df = self.get_data_from_influx()

        # 1️⃣ Nombre de pages vues par utilisateur
        print("📊 Job 1: Nombre de pages vues par utilisateur...")
        pages_per_user = df.groupby('user')['page'].nunique().reset_index()
        pages_per_user.columns = ['user', 'page_view_count']
        self.store_to_postgres(pages_per_user, 'pages_per_user', ['user', 'page_view_count'])

        # 2️⃣ Page la plus populaire
        print("📊 Job 2: Page la plus populaire...")
        popular_pages = df.groupby('page')['user'].nunique().reset_index()
        popular_pages.columns = ['page', 'user_count']
        popular_pages = popular_pages.sort_values(by='user_count', ascending=False).head(1)
        self.store_to_postgres(popular_pages, 'popular_pages', ['page', 'user_count'])

        # 3️⃣ Temps passé par page
        print("📊 Job 3: Temps passé par page...")
        df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
        time_per_page = df.groupby('page')['duration'].mean().reset_index()
        time_per_page.columns = ['page', 'avg_time_spent']
        self.store_to_postgres(time_per_page, 'time_per_page', ['page', 'avg_time_spent'])

        # 4️⃣ Nombre de pages vues par session
        print("📊 Job 4: Nombre de pages vues par session...")
        pages_per_session = df.groupby('session_id')['page'].nunique().reset_index()
        pages_per_session.columns = ['session_id', 'page_count']
        self.store_to_postgres(pages_per_session, 'pages_per_session', ['session_id', 'page_count'])

        # 5️⃣ Temps total par utilisateur sur toutes les pages
        print("📊 Job 5: Temps total passé par utilisateur...")
        total_time_per_user = df.groupby('user')['duration'].sum().reset_index()
        total_time_per_user.columns = ['user', 'total_time_spent']
        self.store_to_postgres(total_time_per_user, 'total_time_per_user', ['user', 'total_time_spent'])

        # 6️⃣ Pages les plus vues par type de device ou pays
        print("📊 Job 6: Pages les plus vues par device et pays...")
        pages_per_device_country = df.groupby(['page', 'appInfo.deviceType', 'location.country'])['user'].nunique().reset_index()
        pages_per_device_country.columns = ['page', 'device_type', 'country', 'user_count']
        pages_per_device_country = pages_per_device_country.sort_values(by='user_count', ascending=False).head(1)
        self.store_to_postgres(pages_per_device_country, 'pages_per_device_country', ['page', 'device_type', 'country', 'user_count'])

        # 7️⃣ Nombre de visiteurs uniques par page
        print("📊 Job 7: Nombre de visiteurs uniques par page...")
        unique_visitors_per_page = df.groupby('page')['user'].nunique().reset_index()
        unique_visitors_per_page.columns = ['page', 'unique_visitors']
        self.store_to_postgres(unique_visitors_per_page, 'unique_visitors_per_page', ['page', 'unique_visitors'])

        print("✅ Tous les résultats ont été stockés dans PostgreSQL.")

# Classe Main dédiée
class Main:
    def __init__(self):
        job = JobPageViewAggregation()
        job.run()

if __name__ == "__main__":
    Main()

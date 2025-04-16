import pandas as pd
from influxdb_client import InfluxDBClient
import psycopg2

class JobUserMetrics:
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

    def get_data(self):
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -60d)
          |> filter(fn: (r) => r["_measurement"] == "event")
          |> keep(columns: ["_time", "user"])
        '''
        tables = self.influx_client.query_api().query_data_frame(query)
        df = pd.concat(tables) if isinstance(tables, list) else tables
        df['_time'] = pd.to_datetime(df['_time'])
        df = df.dropna(subset=['user'])
        return df

    def aggregate(self, df):
        df['period'] = df['_time'].dt.to_period('D')  # tu peux changer à 'W' pour semaine

        # 1️⃣ Nombre total d'utilisateurs par période
        users_per_period = df.groupby('period')['user'].nunique().reset_index()
        users_per_period.columns = ['period', 'user_count']

        # 2️⃣ Nombre d’utilisateurs actifs par période (au moins une action)
        active_users = df.drop_duplicates(subset=['user', 'period'])

        # 3️⃣ Taux de rétention (user présent dans deux périodes consécutives)
        retention_data = []
        periods = sorted(df['period'].unique())

        for i in range(1, len(periods)):
            prev_users = set(df[df['period'] == periods[i - 1]]['user'])
            curr_users = set(df[df['period'] == periods[i]]['user'])

            if prev_users:
                retained = len(prev_users & curr_users)
                retention = retained / len(prev_users)
            else:
                retention = None

            retention_data.append({
                'period': str(periods[i]),
                'retention_rate': retention
            })

        retention_df = pd.DataFrame(retention_data)

        return users_per_period, retention_df

    def store_postgres(self, df, table_name, columns):
        self.pg_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns[0]} TEXT,
                {columns[1]} FLOAT
            )
        ''')
        self.pg_cursor.execute(f"DELETE FROM {table_name}")
        for _, row in df.iterrows():
            self.pg_cursor.execute(
                f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES (%s, %s)',
                tuple(row[col] for col in columns)
            )
        self.pg_conn.commit()

    def run(self):
        print("📥 Récupération des données InfluxDB...")
        df = self.get_data()

        print("📊 Calcul des agrégations utilisateurs...")
        users_per_period, retention_df = self.aggregate(df)

        print("🗃️ Enregistrement dans PostgreSQL...")
        self.store_postgres(users_per_period, 'users_per_period', ['period', 'user_count'])
        self.store_postgres(retention_df, 'retention_per_period', ['period', 'retention_rate'])

        print("✅ Job terminé.")

class Main:
    def __init__(self):
        job = JobUserMetrics()
        job.run()

if __name__ == "__main__":
    Main()

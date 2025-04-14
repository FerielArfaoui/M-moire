import pandas as pd
from influxdb_client import InfluxDBClient
import psycopg2

class JobProjectPhase:
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
          |> keep(columns: ["appInfo.projectId", "appInfo.projectName", "appInfo.cohortId", "user"])
        '''
        tables = query_api.query_data_frame(flux_query)
        df = pd.concat(tables) if isinstance(tables, list) else tables
        return df.dropna()

    def store_to_postgres(self, df, table_name, columns):
        self.pg_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {", ".join([f"{col} TEXT" if i == 0 else f"{col} INTEGER" for i, col in enumerate(columns)])}
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

        # Simuler company_id depuis projectId
        df['company_id'] = df['appInfo.projectId'].str[:6]

        # 1️⃣ Nombre de projets par company
        print("📊 Job 1: projets par company...")
        projects_per_company = df.groupby('company_id')['appInfo.projectId'].nunique().reset_index()
        projects_per_company.columns = ['company_id', 'project_count']
        self.store_to_postgres(projects_per_company, 'projects_per_company', ['company_id', 'project_count'])

        # 2️⃣ Nombre de cohorts par projet
        print("📊 Job 2: cohorts par projet...")
        cohorts_per_project = df.groupby('appInfo.projectId')['appInfo.cohortId'].nunique().reset_index()
        cohorts_per_project.columns = ['project_id', 'cohort_count']
        self.store_to_postgres(cohorts_per_project, 'cohorts_per_project', ['project_id', 'cohort_count'])

        # 3️⃣ Nombre d’utilisateurs par cohort
        print("📊 Job 3: users par cohort...")
        users_per_cohort = df.groupby('appInfo.cohortId')['user'].nunique().reset_index()
        users_per_cohort.columns = ['cohort_id', 'user_count']
        self.store_to_postgres(users_per_cohort, 'users_per_cohort', ['cohort_id', 'user_count'])

        # 4️⃣ Nombre total d’utilisateurs par projet
        print("📊 Job 4: users par projet...")
        users_per_project = df.groupby('appInfo.projectId')['user'].nunique().reset_index()
        users_per_project.columns = ['project_id', 'user_count']
        self.store_to_postgres(users_per_project, 'users_per_project', ['project_id', 'user_count'])

        # 5️⃣ Nombre total d’utilisateurs par company
        print("📊 Job 5: users par company...")
        users_per_company = df.groupby('company_id')['user'].nunique().reset_index()
        users_per_company.columns = ['company_id', 'user_count']
        self.store_to_postgres(users_per_company, 'users_per_company', ['company_id', 'user_count'])

        print("✅ Tous les résultats ont été stockés dans PostgreSQL.")

# Classe Main dédiée
class Main:
    def __init__(self):
        job = JobProjectPhase()
        job.run()

if __name__ == "__main__":
    Main()

# wait_for_db.py
import os, time
import psycopg2

DB = os.getenv("POSTGRES_DB", "hero_db")
USER = os.getenv("POSTGRES_USER", "hero_user")
PASSWORD = os.getenv("POSTGRES_PASSWORD", "hero_pass")
HOST = os.getenv("POSTGRES_HOST", "db")
PORT = int(os.getenv("POSTGRES_PORT", "5432"))

attempts = 30
for i in range(attempts):
    try:
        conn = psycopg2.connect(dbname=DB, user=USER, password=PASSWORD, host=HOST, port=PORT)
        conn.close()
        print("DB is ready")
        break
    except Exception as e:
        print(f"[{i+1}/{attempts}] DB not ready: {e}")
        time.sleep(2)
else:
    raise SystemExit("DB not ready after waiting")

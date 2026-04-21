import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))

cur = conn.cursor()
cur.execute("select version();")

print(cur.fetchone())

conn.close()
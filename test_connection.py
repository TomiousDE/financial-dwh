import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5433,
    database="financial_dwh",
    user="dwh_user",
    password="dwh_password",
    sslmode="disable"
)

print("Conexiune reușită!")
cur = conn.cursor()
cur.execute("SELECT current_database(), current_user;")
print(cur.fetchone())
conn.close()
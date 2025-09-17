import sqlite3

conn = sqlite3.connect("data/app.db")
cur = conn.cursor()

cur.execute("SELECT * FROM students LIMIT 5;")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()

# data/generate_fake_data.py

import sqlite3
import random

# Создаём подключение к базе
conn = sqlite3.connect("data/app.db")
cur = conn.cursor()

# Создаём таблицу студентов
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    major TEXT
);
""")

# Очистим таблицу перед вставкой
cur.execute("DELETE FROM students;")

# Генерация фейковых данных
names = ["Aigerim", "Serik", "Dias", "Alina", "Nursultan", "Dana", "Rustem", "Malika", "Adil", "Aruzhan"]
majors = ["Computer Science", "Mathematics", "Physics", "Economics", "Biology"]

for _ in range(20):
    name = random.choice(names)
    age = random.randint(17, 25)
    major = random.choice(majors)
    cur.execute("INSERT INTO students (name, age, major) VALUES (?, ?, ?)", (name, age, major))

conn.commit()
conn.close()

print("Fake data generated in data/app.db ✅")

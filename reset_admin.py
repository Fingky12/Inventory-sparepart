import sqlite3

conn = sqlite3.connect('database.db')
conn.execute("UPDATE users SET username='ongky', password='ong880141101' WHERE id=1")
conn.commit()
conn.close()
print("✅ Admin berhasil di-reset ke: admin / admin123")
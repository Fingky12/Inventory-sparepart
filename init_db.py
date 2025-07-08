import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('''
    CREATE TABLE IF NOT EXISTS spareparts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        stok INTEGER NOT NULL,
        satuan TEXT
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sparepart_id INTEGER,
        jumlah INTEGER,
        tipe TEXT, -- 'masuk' / 'keluar'
        tanggal TEXT,
        FOREIGN KEY (sparepart_id) REFERENCES spareparts(id)
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# Tambah admin default (username: admin, password: admin123)
try:
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("ongky", "ad8801"))
except:
    pass

conn.close()
print("Database created!")

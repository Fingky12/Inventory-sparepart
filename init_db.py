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

conn.close()
print("Database created!")

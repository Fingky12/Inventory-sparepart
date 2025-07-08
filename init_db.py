import sqlite3

conn = sqlite3.connect('database.db')

# Buat tabel spareparts
conn.execute('''
CREATE TABLE IF NOT EXISTS spareparts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    stok INTEGER NOT NULL,
    satuan TEXT NOT NULL,
    harga INTEGER NOT NULL
)
''')

# Buat tabel transaksi
conn.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sparepart_id INTEGER,
    jumlah INTEGER,
    tipe TEXT,
    tanggal TEXT
)
''')

# Buat tabel user
conn.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Tambah user admin default
try:
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("ong", "ongky41101"))
except:
    pass

conn.commit()
conn.close()

print("✅ Database berhasil dibuat " )

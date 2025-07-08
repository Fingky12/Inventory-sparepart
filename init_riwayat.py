import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS riwayat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sparepart_id INTEGER,
    jenis TEXT,
    jumlah INTEGER,
    tanggal TEXT,
    keterangan TEXT,
    FOREIGN KEY(sparepart_id) REFERENCES spareparts(id)
)
''')
conn.commit()
conn.close()

print("Tabel riwayat berhasil dibuat!")

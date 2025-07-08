from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db()
    parts = conn.execute('SELECT * FROM spareparts').fetchall()
    conn.close()
    return render_template('index.html', parts=parts)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        nama = request.form['nama']
        stok = request.form['stok']
        satuan = request.form['satuan']
        harga = request.form['harga']
        conn = get_db()
        conn.execute('INSERT INTO spareparts (nama, stok, satuan, harga) VALUES (?, ?, ?, ?)', (nama, stok, satuan, harga))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()
    if request.method == 'POST':
        nama = request.form['nama']
        stok = request.form['stok']
        satuan = request.form['satuan']
        harga = request.form['harga']
        conn.execute('UPDATE spareparts SET nama=?, stok=?, satuan=?, harga=? WHERE id=?', (nama, stok, satuan, harga, id))
        conn.commit()
        conn.close()
        return redirect('/')
    part = conn.execute('SELECT * FROM spareparts WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', part=part)

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    conn.execute('DELETE FROM spareparts WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

from datetime import datetime

@app.route('/transaction/<int:id>', methods=['GET', 'POST'])
def transaction(id):
    conn = get_db()
    part = conn.execute('SELECT * FROM spareparts WHERE id=?', (id,)).fetchone()
    error = None

    if request.method == 'POST':
        jumlah = int(request.form['jumlah'])
        tipe = request.form['tipe']
        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if tipe == 'keluar' and jumlah > part['stok']:
            error = f"❌ Stok tidak mencukupi! (Stok saat ini: {part['stok']})"
        else:
            # Hitung stok baru
            new_stok = part['stok'] + jumlah if tipe == 'masuk' else part['stok'] - jumlah

            # Simpan update
            conn.execute('UPDATE spareparts SET stok=? WHERE id=?', (new_stok, id))
            conn.execute('INSERT INTO transactions (sparepart_id, jumlah, tipe, tanggal) VALUES (?, ?, ?, ?)',
                         (id, jumlah, tipe, tanggal))
            conn.commit()
            conn.close()
            return redirect('/')

    conn.close()
    return render_template('/transaction.html', part=part, error=error)

@app.route('/history/<int:id>')
def history(id):
    conn = get_db()
    part = conn.execute('SELECT * FROM spareparts WHERE id=?', (id,)).fetchone()
    riwayat = conn.execute('SELECT * FROM transactions WHERE sparepart_id=? ORDER BY tanggal DESC', (id,)).fetchall()
    conn.close()
    return render_template('history.html', part=part, riwayat=riwayat)

@app.route('/quick-transaction', methods=['POST'])
def quick_transaction():
    conn = get_db()

    sparepart_id = int(request.form['sparepart_id'])
    jumlah = int(request.form['jumlah'])
    tipe = request.form['tipe']
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    part = conn.execute('SELECT * FROM spareparts WHERE id=?', (sparepart_id,)).fetchone()
    parts = conn.execute('SELECT * FROM spareparts').fetchall()

    if tipe == 'keluar' and jumlah > part['stok']:
        conn.close()
        return render_template('index.html', parts=parts,
                               error=f"❌ Stok tidak cukup! (Stok {part['nama']}: {part['stok']})")
    else:
        new_stok = part['stok'] + jumlah if tipe == 'masuk' else part['stok'] - jumlah
        conn.execute('UPDATE spareparts SET stok=? WHERE id=?', (new_stok, sparepart_id))
        conn.execute('INSERT INTO transactions (sparepart_id, jumlah, tipe, tanggal) VALUES (?, ?, ?, ?)',
                     (sparepart_id, jumlah, tipe, tanggal))
        conn.commit()
        conn.close()
        parts = get_db().execute('SELECT * FROM spareparts').fetchall()
        return render_template('index.html', parts=parts,
                               message=f"✅ Transaksi {tipe.upper()} berhasil untuk {part['nama']}")

@app.route('/dashboard')
def dashboard():
    conn = get_db()

    total_masuk = conn.execute("SELECT SUM(jumlah) FROM transactions WHERE tipe='masuk'").fetchone()[0] or 0
    total_keluar = conn.execute("SELECT SUM(jumlah) FROM transactions WHERE tipe='keluar'").fetchone()[0] or 0

    top_masuk = conn.execute('''
        SELECT s.nama, SUM(t.jumlah) AS total
        FROM transactions t
        JOIN spareparts s ON s.id = t.sparepart_id
        WHERE t.tipe = 'masuk'
        GROUP BY s.id
        ORDER BY total DESC
        LIMIT 5
    ''').fetchall()

    top_keluar = conn.execute('''
        SELECT s.nama, SUM(t.jumlah) AS total
        FROM transactions t
        JOIN spareparts s ON s.id = t.sparepart_id
        WHERE t.tipe = 'keluar'
        GROUP BY s.id
        ORDER BY total DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    masuk_labels = [row['nama'] for row in top_masuk]
    masuk_data = [row['total'] for row in top_masuk]

    keluar_labels = [row['nama'] for row in top_keluar]
    keluar_data = [row['total'] for row in top_keluar]

    return render_template('dashboard.html',
                           total_masuk=total_masuk,
                           total_keluar=total_keluar,
                           masuk_labels=masuk_labels,
                           masuk_data=masuk_data,
                           keluar_labels=keluar_labels,
                           keluar_data=keluar_data)


if __name__ == '__main__':
    app.run(debug=True)
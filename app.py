from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'rahasia-super-aman-🔥'

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_user():
    conn = get_db()
    username = session.get('username')  # ambil username aktif dari session
    if not username:
        return False
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user is not None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not is_valid_user():
            session.clear()  # hapus session
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        conn = get_db()
        username = request.form['username']
        password = request.form['password']
        user = conn.execute('SELECT * FROM users WHERE username=? AND password=?',
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            session['username'] = username  # simpan username aktif
            return redirect('/')
        else:
            error = "❌ Username atau password salah!"
    return render_template('login.html', error=error)
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
    
@app.route('/')
@login_required
def index():
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db()
    parts = conn.execute('SELECT * FROM spareparts').fetchall()
    conn.close()
    return render_template('index.html', parts=parts)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not session.get('logged_in'):
        return redirect('/login')
    if request.method == 'POST':
        nama = request.form['nama']
        stok = request.form['stok']
        satuan = request.form['satuan']
        harga = request.form['harga']
        conn = get_db()
        conn.execute('INSERT INTO spareparts (nama, stok, satuan, harga) VALUES (?, ?, ?, ?)',
                     (nama, stok, satuan, harga))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db()
    if request.method == 'POST':
        nama = request.form['nama']
        stok = request.form['stok']
        satuan = request.form['satuan']
        harga = request.form['harga']
        conn.execute('UPDATE spareparts SET nama=?, stok=?, satuan=?, harga=? WHERE id=?',
                     (nama, stok, satuan, harga, id))
        conn.commit()
        conn.close()
        return redirect('/')
    part = conn.execute('SELECT * FROM spareparts WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', part=part)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db()
    conn.execute('DELETE FROM spareparts WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/transaction/<int:id>', methods=['GET', 'POST'])
@login_required
def transaction(id):
    if not session.get('logged_in'):
        return redirect('/login')
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
            new_stok = part['stok'] + jumlah if tipe == 'masuk' else part['stok'] - jumlah
            conn.execute('UPDATE spareparts SET stok=? WHERE id=?', (new_stok, id))
            conn.execute('INSERT INTO transactions (sparepart_id, jumlah, tipe, tanggal) VALUES (?, ?, ?, ?)',
                         (id, jumlah, tipe, tanggal))
            conn.commit()
            conn.close()
            return redirect('/')

    conn.close()
    return render_template('transaction.html', part=part, error=error)

@app.route('/history/<int:id>')
@login_required
def history(id):
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db()
    part = conn.execute('SELECT * FROM spareparts WHERE id=?', (id,)).fetchone()
    riwayat = conn.execute('SELECT * FROM transactions WHERE sparepart_id=? ORDER BY tanggal DESC', (id,)).fetchall()
    conn.close()
    return render_template('history.html', part=part, riwayat=riwayat)

@app.route('/quick-transaction', methods=['POST'])
@login_required
def quick_transaction():
    if not session.get('logged_in'):
        return redirect('/login')
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
@login_required
def dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
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
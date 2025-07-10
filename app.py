from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime
from functools import wraps
from datetime import datetime

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

def simpan_log(username, aksi):
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 1. Simpan ke database
    conn = get_db()
    conn.execute("INSERT INTO log_aktivitas (username, aksi, waktu) VALUES (?, ?, ?)", (username, aksi, waktu))
    conn.commit()
    conn.close()
    # 2. Simpan ke file log
    with open("admin_log.log", "a") as f:
        f.write(f"[{waktu}] {username.upper()} - {aksi}\n")

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
            simpan_log(username, 'Login berhasil')
            return redirect('/')
        else:
            error = "❌ Username atau password salah!"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    simpan_log(session.get('username'), 'Logout')
    session.clear()
    return redirect('/login')

@app.route('/log-aktivitas')
@login_required
def log_aktivitas():
    conn = get_db()
    logs = conn.execute('SELECT * FROM log_aktivitas ORDER BY waktu DESC').fetchall()
    conn.close()
    return render_template('log_aktivitas.html', logs=logs)

@app.route('/ubah-password', methods=['GET', 'POST'])
@login_required
def ubah_password():
    message = error = None

    if request.method == 'POST':
        current_user = session.get('username')
        old_pw = request.form['old_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (current_user, old_pw)).fetchone()

        if not user:
            error = "❌ Password lama salah!"
        elif new_pw != confirm_pw:
            error = "❌ Konfirmasi password tidak cocok!"
        else:
            conn.execute("UPDATE users SET password=? WHERE username=?", (new_pw, current_user))
            conn.commit()
            message = "✅ Password berhasil diubah"

        conn.close()
        simpan_log(session['username'], "Ubah password admin")
    return render_template('ubah_password.html', message=message, error=error)

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
        simpan_log(session['username'], f"Tambah item: {nama} ({stok} {satuan})")
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
        simpan_log(session['username'], f"Edit item ID {id}: jadi {nama}, stok {stok}")
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
    simpan_log(session['username'], f"Hapus item ID {id}")
    return redirect('/')

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
        simpan_log(session['username'], f"Quick Transaksi {tipe} untuk ID {sparepart_id}: {jumlah}")
        parts = get_db().execute('SELECT * FROM spareparts').fetchall()
        return render_template('index.html', parts=parts,
                               message=f"✅ Transaksi {tipe.upper()} berhasil untuk {part['nama']}")

@app.route('/ambil', methods=['GET', 'POST'])
@login_required
def ambil():
    conn = get_db()
    parts = conn.execute("SELECT * FROM spareparts").fetchall()
    supir_list = conn.execute("SELECT * FROM supir_truk").fetchall()
      
    if request.method == 'POST':
        sparepart_id = request.form['sparepart_id']
        jumlah = int(request.form['jumlah'])
        supir_id = request.form['supir_id']
        keterangan = request.form['keterangan']
      
        # Ambil nama supir & nopol dari DB
        supir = conn.execute("SELECT * FROM supir_truk WHERE id = ?", (supir_id,)).fetchone()
        pengambil = f"{supir['nama_supir']} ({supir['nopol']})"
      
        # Update stok + simpan transaksi
        conn.execute("UPDATE spareparts SET stok = stok - ? WHERE id = ?", (jumlah, sparepart_id))
        tanggal = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO transactions (sparepart_id, jumlah, tipe, tanggal, pengambil, keterangan)
            VALUES (?, ?, 'keluar', ?, ?, ?)
        ''', (sparepart_id, jumlah, tanggal, pengambil, keterangan))
      
        conn.commit()
        conn.close()
        simpan_log(session['username'], f"Ambil sparepart ID {sparepart_id} oleh {pengambil} sebanyak {jumlah}")
        return redirect('/ambil')
      
    conn.close()
    return render_template('ambil.html', parts=parts, supir_list=supir_list)
    
@app.route('/riwayat-pengambilan')
@login_required
def riwayat_pengambilan():
    conn = get_db()
    rows = conn.execute('''
        SELECT t.*, s.nama FROM transactions t
        JOIN spareparts s ON t.sparepart_id = s.id
        WHERE t.tipe = 'keluar'
        ORDER BY t.tanggal DESC
    ''').fetchall()
    conn.close()
    return render_template('riwayat_pengambilan.html', rows=rows)


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

@app.route('/supir', methods=['GET', 'POST'])
@login_required
def supir():
    conn = get_db()

    if request.method == 'POST':
        nama = request.form['nama']
        nopol = request.form['nopol']
        conn.execute("INSERT INTO supir_truk (nama_supir, nopol) VALUES (?, ?)", (nama, nopol))
        conn.commit()
        simpan_log(session['username'], f"Tambah supir: {nama} - {nopol}")
        return redirect('/supir')

    data = conn.execute("SELECT * FROM supir_truk").fetchall()
    conn.close()
    return render_template('supir.html', data=data)

@app.route('/supir', methods=['GET', 'POST'])
@login_required
def tambah_supir():
    conn = get_db()
    if request.method == 'POST':
        nama = request.form['nama']
        nopol = request.form['nopol']
        conn.execute("INSERT INTO supir_truk (nama_supir, nopol) VALUES (?, ?)", (nama, nopol))
        conn.commit()
        conn.close()
        simpan_log(session['username'], f"Tambah supir: {nama} ({nopol})")
        return redirect('/supir')
    
    data = conn.execute("SELECT * FROM supir_truk").fetchall()
    conn.close()
    return render_template('supir.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, jsonify, redirect, url_for, json, request, session
import requests
import bcrypt
import mysql.connector
from collections import defaultdict

app = Flask(__name__)

# Fungsi untuk terhubung ke database MySQL
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",    # Ganti dengan host MySQL Anda
        user="root",         # Ganti dengan username MySQL Anda
        password="",         # Ganti dengan password MySQL Anda
        database="db_quran"  # Ganti dengan nama database Anda
    )
    return conn

# Middleware untuk memeriksa apakah pengguna sudah masuk
@app.before_request
def before_request():
    allowed_endpoints = ['login', 'register']
    if request.endpoint not in allowed_endpoints and 'email' not in session:
        return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST', 'DELETE'])
def index():
    api_url = 'https://al-quran-8d642.firebaseio.com/data.json?print=pretty'
    response = requests.get(api_url)
    all_data = response.json()

    if 'search' in request.args:
        search_query = request.args['search']
        search_results = [item for item in all_data if search_query.lower() in item['nama'].lower() or search_query.lower() in item['nomor']]
    else:
        search_results = None

    if request.method == 'POST':
        # Bagian untuk menambahkan favorit
        email = session.get('email')
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        user_id = cursor.fetchone()[0]
        surah_number = request.form['surah_number']
        surah_name = request.form['surah_name']
        
        cursor.execute('INSERT INTO favorites (user_id, surah_number, surah_name) VALUES (%s, %s, %s)', (user_id, surah_number, surah_name))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    elif request.method == 'GET':
        # Bagian untuk menampilkan daftar favorit
        email = session.get('email')
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, surah_number, surah_name FROM favorites WHERE user_id = (SELECT id FROM users WHERE email = %s)', (email,))
        favorites = cursor.fetchall()
        conn.close()
        
        favorites_list = [{'id': favorite[0], 'surah_number': favorite[1], 'surah_name': favorite[2]} for favorite in favorites]

        # sum(): Menghitung total nilai dari elemen-elemen dalam sebuah iterable, misalnya total nilai dari list of integers.
        # len(): Menghitung jumlah elemen dalam sebuah iterable, misalnya jumlah item dalam sebuah list.
        
        # Menghitung jumlah data surat favorit dalam database menggunakan len()
        num_favorites = len(favorites_list)
        # Menghitung jumlah total data favorit dalam database menggunakan sum()
        sum_favorites = sum(1 for _ in favorites_list)
        # Menghitung jumlah total surah_number favorit dalam database menggunakan sum()
        # sum_favorites = sum(favorite['surah_number'] for favorite in favorites_list)
        
        return render_template('index.html', favorites=favorites_list, data=all_data, search_results=search_results, num_favorites=num_favorites, sum_favorites=sum_favorites)

    elif request.method == 'DELETE':
        favorite_id = request.json['id']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE id = %s', (favorite_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})

@app.route('/register', methods=["GET", "POST"])    
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        nama = request.form.get('nama')
        email = request.form.get('email')
        password = request.form.get('password').encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (nama, email, password) VALUES (%s,%s,%s)', (nama, email, hash_password))
        conn.commit()
        session['nama'] = nama
        session['email'] = email
        return redirect(url_for("index"))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password').encode('utf-8')

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()

        if user is not None:
            hashed_password = user[3]
            if bcrypt.checkpw(password, hashed_password.encode('utf-8')):
                session['nama'] = user[1]
                session['email'] = user[2]
                return redirect(url_for("index"))
            else:
                return "Error: Password atau email salah"
        else:
            return "Error: Pengguna tidak ditemukan"
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return render_template("login.html")

@app.route("/surat/<int:nomor>", methods=['GET', 'POST'])
def surat(nomor):
    req = requests.get(f'https://api.npoint.io/99c279bb173a6e28359c/surat/{nomor}')
    surat = json.loads(req.content)
    return render_template('surat.html', surat=surat)

app.secret_key = 'apaajayangpentingjalan'
if __name__ == '__main__':
    app.run(debug=True)

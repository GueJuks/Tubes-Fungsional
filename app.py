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

@app.route('/', methods=['GET', 'POST', 'DELETE'])
def index():
    api_url = 'https://al-quran-8d642.firebaseio.com/data.json?print=pretty'
    response = requests.get(api_url)
    all_data = response.json()


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
        
        return render_template('index.html', favorites=favorites_list, data=all_data, num_favorites=num_favorites, sum_favorites=sum_favorites)

    elif request.method == 'DELETE':
        favorite_id = request.json['id']
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE id = %s', (favorite_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True)

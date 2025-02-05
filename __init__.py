from flask import Flask, render_template_string, render_template, jsonify, request, redirect, url_for, session
from flask import render_template
from flask import json
from urllib.request import urlopen
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)                                                                                                                  
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

def log_action(username, action):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (username, action) VALUES (?, ?)', (username, action))
    conn.commit()
    conn.close()

def est_authentifie():
    is_auth = session.get('authentifie')
    print(f"Debug: est_authentifie() returned {is_auth}")
    return is_auth

@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/lecture')
def lecture():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    log_action(session.get('username'), 'Accès à la page de lecture')
    return "<h2>Bravo, vous êtes authentifié</h2>"

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':  # password à cacher par la suite
            session['authentifie'] = True
            session['username'] = username
            log_action(username, 'Authentification réussie')
            return redirect(url_for('lecture'))
        else:
            log_action(username, 'Authentification échouée')
            return render_template('formulaire_authentification.html', error=True)
    return render_template('formulaire_authentification.html', error=False)

@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    if not est_authentifie():
        return redirect(url_for('authentification'))
    log_action(session.get('username'), f'Consultation de la fiche client {post_id}')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)

@app.route('/consultation/')
def ReadBDD():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    log_action(session.get('username'), 'Consultation de la base de données')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)

@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    return render_template('formulaire.html')

@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    nom = request.form['nom']
    prenom = request.form['prenom']
    log_action(session.get('username'), 'Enregistrement d\'un nouveau client')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)', (nom, prenom, "ICI"))
    conn.commit()
    conn.close()
    return redirect('/consultation/')

@app.route('/logs', methods=['GET'])
def logs():
    print(f"Debug: Session data: {session}")
    if not est_authentifie():
        print("Debug: User not authenticated, redirecting")
        return redirect(url_for('authentification'))
    print("Debug: User authenticated, fetching logs")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC')
    logs = cursor.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)


if __name__ == "__main__":
    app.run(debug=True)
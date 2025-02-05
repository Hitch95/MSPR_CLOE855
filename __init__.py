# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

def log_action(username, action, success):
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (username, ip, user_agent, action, success) VALUES (?, ?, ?, ?, ?)',
                   (username, ip, user_agent, action, success))
    conn.commit()
    conn.close()

def est_authentifie():
    return session.get('authentifie')

def detect_suspicious_activity():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Détecter plusieurs tentatives d'authentification échouées en moins de 5 minutes
    cursor.execute('''
        SELECT ip, COUNT(*) as failed_attempts
        FROM logs
        WHERE action = 'Authentification échouée'
        AND timestamp > datetime('now', '-5 minutes')
        GROUP BY ip
        HAVING failed_attempts >= 3
    ''')
    suspicious_ips = cursor.fetchall()
    conn.close()
    return suspicious_ips

@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/lecture')
def lecture():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    log_action(session.get('username'), 'Accès à la page de lecture', True)
    return "<h2>Bravo, vous êtes authentifié</h2>"

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':  # password à cacher par la suite
            session['authentifie'] = True
            session['username'] = username
            log_action(username, 'Authentification réussie', True)
            return redirect(url_for('lecture'))
        else:
            log_action(username, 'Authentification échouée', False)
            flash('Identifiants incorrects', 'error')
            return render_template('formulaire_authentification.html')
    
    # Détecter des activités suspectes
    suspicious_ips = detect_suspicious_activity()
    if suspicious_ips:
        for ip, _ in suspicious_ips:
            flash(f'Activité suspecte détectée depuis l\'IP {ip}', 'warning')
    
    return render_template('formulaire_authentification.html')

@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    if not est_authentifie():
        return redirect(url_for('authentification'))
    log_action(session.get('username'), f'Consultation de la fiche client {post_id}', True)
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
    log_action(session.get('username'), 'Consultation de la base de données', True)
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
    log_action(session.get('username'), 'Enregistrement d\'un nouveau client', True)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)', (nom, prenom, "ICI"))
    conn.commit()
    conn.close()
    return redirect('/consultation/')

@app.route('/logs')
def logs():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC')
    logs = cursor.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

if __name__ == "__main__":
    app.run(debug=True)
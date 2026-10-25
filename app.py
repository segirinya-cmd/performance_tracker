import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'football_tracker.db'

# Configure single-folder architecture
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
app.secret_key = 'grassroots-secure-secret-key-change-in-prod'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db()
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        # Seed initial default accounts for demonstration
        cursor = conn.cursor()
        users = [
            ('admin_user', generate_password_hash('admin123'), 'admin'),
            ('coach_ronald', generate_password_hash('coach123'), 'trainer'),
            ('scout_mike', generate_password_hash('scout123'), 'scout')
        ]
        cursor.executemany("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", users)
        
        # Seed test player dossier
        cursor.execute(
            "INSERT INTO players (full_name, date_of_birth, primary_position, preferred_foot) VALUES (?, ?, ?, ?)",
            ('Ronald Junior', '2008-04-12', 'Central Midfield', 'Right')
        )
        sample_player_id = cursor.lastrowid
        cursor.execute(
            """INSERT INTO performance_metrics 
               (player_id, recorded_by, session_date, sprint_30m_sec, agility_test_sec, passing_accuracy_pct, stamina_score, coach_rating, video_url)
               VALUES (?, 2, '2026-10-01', 4.15, 12.30, 82.5, 75.0, 7.8, 'https://youtube.com')""",
            (sample_player_id,)
        )
        conn.commit()
        conn.close()

def log_audit(action, user_id=None):
    uid = user_id or session.get('user_id')
    if uid:
        conn = get_db()
        conn.execute("INSERT INTO audit_logs (user_id, action) VALUES (?, ?)", (uid, action))
        conn.commit()
        conn.close()

# Role-Based Access Control (RBAC) Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Authentication required. Please sign in.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            log_audit(f"User {user['username']} logged in successfully.", user['id'])
            return redirect(url_for('dashboard'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    log_audit(f"User {session.get('username')} logged out.")
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    players = conn.execute("SELECT * FROM players ORDER BY full_name ASC").fetchall()
    audit_trail = []
    if session.get('role') == 'admin':
        audit_trail = conn.execute(
            """SELECT a.action, a.timestamp, u.username, u.role 
               FROM audit_logs a 
               LEFT JOIN users u ON a.user_id = u.id 
               ORDER BY a.timestamp DESC LIMIT 10"""
        ).fetchall()
    conn.close()
    return render_template('dashboard.html', players=players, audit_trail=audit_trail)

@app.route('/players/add', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'trainer')
def add_player():
    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        dob = request.form.get('date_of_birth', '').strip()
        position = request.form.get('primary_position', '').strip()
        foot = request.form.get('preferred_foot', '').strip()

        if not name or not dob or not position or not foot:
            flash("All player dossier fields are mandatory.", "warning")
            return redirect(url_for('add_player'))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO players (full_name, date_of_birth, primary_position, preferred_foot) VALUES (?, ?, ?, ?)",
            (name, dob, position, foot)
        )
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        log_audit(f"Created player profile: {name} (ID: {player_id})")
        flash(f"Player {name} successfully added.", "success")
        return redirect(url_for('dashboard'))
    return render_template('add_player.html')

@app.route('/players/<int:player_id>')
@login_required
def player_detail(player_id):
    conn = get_db()
    player = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    if not player:
        conn.close()
        abort(404)

    metrics = conn.execute(
        """SELECT m.*, u.username as coach_name 
           FROM performance_metrics m 
           JOIN users u ON m.recorded_by = u.id 
           WHERE m.player_id = ? 
           ORDER BY m.session_date DESC""",
        (player_id,)
    ).fetchall()
    conn.close()
    return render_template('player_detail.html', player=player, metrics=metrics)

@app.route('/players/<int:player_id>/record_metric', methods=['POST'])
@login_required
@roles_required('admin', 'trainer')
def record_metric(player_id):
    try:
        session_date = request.form.get('session_date')
        sprint = float(request.form.get('sprint_30m_sec'))
        agility = float(request.form.get('agility_test_sec'))
        passing = float(request.form.get('passing_accuracy_pct'))
        stamina = float(request.form.get('stamina_score'))
        rating = float(request.form.get('coach_rating'))
        video_url = request.form.get('video_url', '').strip()

        conn = get_db()
        conn.execute(
            """INSERT INTO performance_metrics 
               (player_id, recorded_by, session_date, sprint_30m_sec, agility_test_sec, passing_accuracy_pct, stamina_score, coach_rating, video_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (player_id, session['user_id'], session_date, sprint, agility, passing, stamina, rating, video_url)
        )
        conn.commit()
        conn.close()

        log_audit(f"Added telemetry row for Player ID: {player_id}")
        flash("Training metrics saved successfully.", "success")
    except (ValueError, TypeError):
        flash("Invalid metric input. Please confirm all numerical values.", "danger")

    return redirect(url_for('player_detail', player_id=player_id))

@app.errorhandler(403)
def forbidden_access(e):
    return render_template('login.html', error_override="Access Denied: Your account role does not have permission to execute this operation."), 403

if __name__ == '__main__':
    init_db()
    # Host on 0.0.0.0 to enable mobile testing over your local Wi-Fi network
    app.run(host='0.0.0.0', port=5000, debug=True)

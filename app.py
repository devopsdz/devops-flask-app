from flask import Flask, request, render_template, redirect, url_for, flash, session
import redis
from functools import wraps
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter
import logging
import sys
import os  # ✅ مضافة هنا

# ------------------ Logging Setup ------------------

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ Flask Setup ------------------

app = Flask(__name__)
admin_password = os.getenv('ADMIN_PASSWORD')

# ------------------ Prometheus Monitoring ------------------

metrics = PrometheusMetrics(app)

login_counter = Counter('login_attempts', 'Total login attempts')
reset_counter = Counter('reset_operations', 'Total reset operations')

# ------------------ Redis Setup ------------------

redis_url = os.getenv("REDIS_URL")
r = redis.Redis.from_url(redis_url)

# ------------------ Dummy Users ------------------

USERS = {
    "admin": admin_password
}

# ------------------ Login Required Decorator ------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ------------------ Routes ------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        if username:
            key = f"user:{username}"
            r.incr(key)
            visits = r.get(key)
            flash(f"Welcome {username}! You have visited {int(visits)} times.", "success")
            logger.info(f"User {username} visited. Total visits: {int(visits)}")
            return redirect(url_for('index'))
    return render_template('home.html')

@app.route('/reset', methods=['GET', 'POST'])
@login_required
def reset():
    if request.method == 'POST':
        username = request.form['username']
        if username:
            key = f"user:{username}"
            r.set(key, 0)
            flash(f"Visits reset for {username}.", "info")
            reset_counter.inc()
            logger.info(f"Visit count reset for user: {username}")
            return redirect(url_for('reset'))
    return render_template('reset.html')

@app.route('/stats')
@login_required
def stats():
    keys = r.keys('user:*')
    stats = {key.decode().split(':')[1]: int(r.get(key)) for key in keys}
    logger.info("Stats page accessed.")
    return render_template('stats.html', labels=list(stats.keys()), data=list(stats.values()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_counter.inc()
        user = request.form['username']
        pwd = request.form['password']
        logger.info(f"Login attempt by user: {user}")
        if USERS.get(user) == pwd:
            session['logged_in'] = True
            flash("Logged in successfully.", "success")
            logger.info(f"User {user} logged in successfully.")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", "danger")
            logger.warning(f"Failed login attempt for user: {user}")
    return render_template('login.html')

@app.route('/logout')
def logout():
    logger.info("User logged out.")
    session.pop('logged_in', None)
    flash("Logged out.", "info")
    return redirect(url_for('login'))

# ------------------ Main Entry Point ------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)

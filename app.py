from flask import Flask, request, render_template, redirect, url_for, flash, session
import redis
from functools import wraps
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter
import logging
import sys

# ------------------ Logging Setup ------------------

# Configure logging to output to standard output (stdout)
# Docker containers send logs to stdout, which Loki will collect
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Create a logger instance
logger = logging.getLogger(__name__)

# ------------------ Flask Setup ------------------

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session and flash messages

# ------------------ Prometheus Monitoring ------------------

# Integrate Prometheus metrics exporter with Flask
metrics = PrometheusMetrics(app)

# Define custom Prometheus counters
login_counter = Counter('login_attempts', 'Total login attempts')
reset_counter = Counter('reset_operations', 'Total reset operations')

# ------------------ Redis Setup ------------------

# Define the Redis connection URL (host inside Docker network)
app.config['REDIS_URL'] = "redis://redis-machine:6379"

# Connect to Redis using the URL
r = redis.Redis.from_url(app.config['REDIS_URL'])

# ------------------ Dummy Users ------------------

# Simple dictionary to simulate a user database
USERS = {
    "admin": "password123"
}

# ------------------ Login Required Decorator ------------------

# This decorator protects routes that require login
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
            r.incr(key)  # Increase the visit count
            visits = r.get(key)

            # Flash message to user
            flash(f"Welcome {username}! You have visited {int(visits)} times.", "success")

            # Log the visit event
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
            r.set(key, 0)  # Reset visit count to 0
            flash(f"Visits reset for {username}.", "info")

            # Increase Prometheus counter
            reset_counter.inc()

            # Log reset action
            logger.info(f"Visit count reset for user: {username}")

            return redirect(url_for('reset'))
    return render_template('reset.html')


@app.route('/stats')
@login_required
def stats():
    # Get all keys like user:*
    keys = r.keys('user:*')

    # Create dictionary of username -> visit count
    stats = {key.decode().split(':')[1]: int(r.get(key)) for key in keys}

    # Log stats access
    logger.info("Stats page accessed.")

    return render_template('stats.html', labels=list(stats.keys()), data=list(stats.values()))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_counter.inc()  # Increment Prometheus login counter

        user = request.form['username']
        pwd = request.form['password']

        # Log the login attempt
        logger.info(f"Login attempt by user: {user}")

        if USERS.get(user) == pwd:
            session['logged_in'] = True
            flash("Logged in successfully.", "success")

            # Log successful login
            logger.info(f"User {user} logged in successfully.")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", "danger")

            # Log failed login
            logger.warning(f"Failed login attempt for user: {user}")
    return render_template('login.html')


@app.route('/logout')
def logout():
    # Log logout
    logger.info("User logged out.")
    session.pop('logged_in', None)
    flash("Logged out.", "info")
    return redirect(url_for('login'))

# ------------------ Main Entry Point ------------------

if __name__ == '__main__':
    # Run the Flask app on 0.0.0.0 to allow external access inside Docker
    app.run(host='0.0.0.0', port=4000)


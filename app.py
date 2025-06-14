from flask import Flask, request, render_template, redirect, url_for, flash, session
import redis
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Redis setup
app.config['REDIS_URL'] = "redis://redis-machine:6379"
r = redis.Redis.from_url(app.config['REDIS_URL'])

# Dummy users
USERS = {
    "admin": "password123"
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        if username:
            key = f"user:{username}"
            r.incr(key)
            visits = r.get(key)
            flash(f"Welcome {username}! You have visited {int(visits)} times.", "success")
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
            return redirect(url_for('reset'))
    return render_template('reset.html')

@app.route('/stats')
@login_required
def stats():
    keys = r.keys('user:*')
    stats = {key.decode().split(':')[1]: int(r.get(key)) for key in keys}
    return render_template('stats.html', labels=list(stats.keys()), data=list(stats.values()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if USERS.get(user) == pwd:
            session['logged_in'] = True
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)

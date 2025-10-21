from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'fitness_secret_key'
activity_data = []

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- Database ----------
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE,
                     password TEXT)''')
    conn.close()

init_db()

# Model for activity logs
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    steps = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    workout_type = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # minutes
    sleep_hours = db.Column(db.Float)

# Create the database
with app.app_context():
    db.create_all()


# Route to log daily activity
@app.route('/log-activity', methods=['GET', 'POST'])
def log_activity():
    from datetime import date
    if request.method == 'POST':
        new_activity = {
            'date': str(date.today()),
            'steps': int(request.form['steps']),
            'calories': int(request.form['calories']),
            'workout_type': request.form['workout_type'],
            'duration': int(request.form['duration']),
            'sleep_hours': float(request.form['sleep_hours'])
        }
        activity_data.append(new_activity)
        return redirect(url_for('dashboard'))

    return render_template('log_activity.html')




# ---------- Routes ----------
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username,password) VALUES (?,?)',(username,password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "User already exists!"
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username=? AND password=?',(username,password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # Here you could add logic to send a reset email, check database, etc.
        flash(f"If an account exists for {email}, a reset link has been sent.")
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


@app.route('/dashboard', methods=['GET'])
def dashboard():
    global activity_data

    # --- Get filter inputs ---
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    filtered_data = activity_data

    # --- Filter data if user applied date range ---
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        filtered_data = [
            a for a in activity_data
            if datetime.strptime(a['date'], '%Y-%m-%d') >= start and datetime.strptime(a['date'], '%Y-%m-%d') <= end
        ]

    # --- If no data ---
    if not filtered_data:
        dates, steps, calories, sleep = [], [], [], []
    else:
        # Format date for better chart labels (DD-MM-YYYY)
        dates = [
            datetime.strptime(a['date'], '%Y-%m-%d').strftime('%d-%m-%Y')
            for a in filtered_data
        ]
        steps = [a['steps'] for a in filtered_data]
        calories = [a['calories'] for a in filtered_data]
        sleep = [a['sleep_hours'] for a in filtered_data]

    total_steps = sum(steps) if steps else 0
    avg_calories = round(sum(calories) / len(calories), 1) if calories else 0
    avg_sleep = round(sum(sleep) / len(sleep), 1) if sleep else 0

    return render_template(
        'dashboard.html',
        dates=dates,
        steps=steps,
        calories=calories,
        sleep=sleep,
        total_steps=total_steps,
        avg_calories=avg_calories,
        avg_sleep=avg_sleep
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

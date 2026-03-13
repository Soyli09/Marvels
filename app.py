from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crisis_hub_secure_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class CrisisReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='Standard')
    status = db.Column(db.String(20), default='Pending')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form.get('password'))
        new_user = User(username=request.form.get('username'), password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- PROTECTED CRISIS HUB ROUTES ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    reports = CrisisReport.query.order_by(CrisisReport.timestamp.desc()).all()
    return render_template('index.html', reports=reports)

@app.route('/report', methods=['POST'])
def create_report():
    if 'user_id' not in session: return redirect(url_for('login'))
    new_report = CrisisReport(
        category=request.form.get('category'),
        description=request.form.get('description'),
        urgency=request.form.get('urgency'),
        latitude=float(request.form.get('latitude')) if request.form.get('latitude') else None,
        longitude=float(request.form.get('longitude')) if request.form.get('longitude') else None
    )
    db.session.add(new_report)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    if 'user_id' not in session: return jsonify({"success": False}), 403
    report = CrisisReport.query.get_or_404(id)
    next_status = {"Pending": "Responding", "Responding": "Resolved"}
    report.status = next_status.get(report.status, report.status)
    db.session.commit()
    return jsonify({"success": True, "status": report.status})

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit_report(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    report = CrisisReport.query.get_or_404(id)
    if request.method == 'POST':
        report.category = request.form.get('category')
        report.description = request.form.get('description')
        report.urgency = request.form.get('urgency')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', report=report)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_report(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    report = CrisisReport.query.get_or_404(id)
    db.session.delete(report)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)

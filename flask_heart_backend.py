import os, pickle, numpy as np, pandas as pd, io, random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage

# -------------------- APP SETUP --------------------
app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(BASE, "store.db")
app.config['SECRET_KEY'] = "mysecret"
db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = "login"

# -------------------- MODELS --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)

class Heart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    bp = db.Column(db.Integer)
    cholesterol = db.Column(db.Integer)
    glucose = db.Column(db.Integer)
    result = db.Column(db.String(100))
    created = db.Column(db.DateTime, default=datetime.utcnow)

@login.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# -------------------- LOAD MODEL --------------------
model = pickle.load(open("Model/rf_classifier.pkl", "rb"))
scaler = pickle.load(open("Model/scaler.pkl", "rb"))

# -------------------- ROUTES --------------------
@app.route('/')
def home():
    return redirect(url_for("login"))

# ---------- REGISTER ----------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=u).first():
            flash("User exists")
            return redirect('/register')
        user = User(username=u, password=p)
        if User.query.count() == 0:
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        flash("Registered. Login now")
        return redirect('/login')
    return render_template("register.html")

# ---------- LOGIN ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            login_user(user)
            return redirect('/predict')
        flash("Wrong credentials")
    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# ---------- HEART PREDICTION ----------
@app.route('/predict', methods=['GET','POST'])
@login_required
def predict():
    result = ""

    if request.method == "POST":
        data = [
            int(request.form['age']),
            int(request.form['sex']),
            int(request.form['cp']),
            int(request.form['trestbps']),
            int(request.form['chol']),
            int(request.form['fbs']),
            int(request.form['restecg']),
            int(request.form['thalach']),
            int(request.form['exang']),
            float(request.form['oldpeak']),
            int(request.form['slope']),
            int(request.form['ca']),
            int(request.form['thal']),
            int(request.form['glucose'])
        ]

        final = scaler.transform([data])
        prediction = model.predict(final)[0]

        result = "❤️ Heart Disease Detected" if prediction==1 else "✅ Healthy Heart"

        record = Heart(
            user_id=current_user.id,
            age=data[0], gender=data[1], bp=data[3],
            cholesterol=data[4], glucose=data[13],
            result=result
        )

        db.session.add(record)
        db.session.commit()

    return render_template("index.html", result=result)


# ---------- PROFILE ----------
@app.route('/dashboard')
@login_required
def dashboard():
    records = Heart.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", records=records)

# ---------- ADMIN ----------
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return "Admin only"
    users = User.query.all()
    returns = Heart.query.all()
    return render_template('admin.html', users=users, records=returns)

# ---------- EXPORT ----------
@app.route('/export')
@login_required
def export():
    data = Heart.query.all() if current_user.is_admin else Heart.query.filter_by(user_id=current_user.id).all()
    df = pd.DataFrame([{
        "User": r.user_id,
        "Age": r.age,
        "BP": r.bp,
        "Chol": r.cholesterol,
        "Glucose": r.glucose,
        "Result": r.result
    } for r in data])

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="data.xlsx")

# -------------------- RUN --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

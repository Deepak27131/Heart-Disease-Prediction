import os, pickle, numpy as np, json
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

load_dotenv()

# -------------------- APP CONFIG --------------------
app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

app.config['SECRET_KEY'] = "heart_secure_key"

# ⚠ Serverless Safe SQLite (temporary storage only)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = "login"

# -------------------- AI SETUP --------------------
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
model_ai = None

if GENAI_API_KEY:
    try:
        genai.configure(api_key=GENAI_API_KEY)
        model_ai = genai.GenerativeModel('gemini-2.5-flash')
    except:
        model_ai = None

# -------------------- DATABASE MODELS --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

class Heart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    age = db.Column(db.Float)
    totChol = db.Column(db.Float)
    sysBP = db.Column(db.Float)
    result = db.Column(db.String(100))
    created = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# -------------------- ML MODEL LOADING --------------------
rf_model, scaler = None, None

def load_ml():
    global rf_model, scaler
    try:
        if os.path.exists("rf_classifier.pkl"):
            rf_model = pickle.load(open("rf_classifier.pkl", "rb"))
            scaler = pickle.load(open("scaler.pkl", "rb"))
    except:
        rf_model = None
        scaler = None

load_ml()

# -------------------- ROUTES --------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and check_password_hash(u.password, request.form['password']):
            login_user(u)
            return redirect('/dashboard')
        flash("Invalid Credentials")
    return render_template("auth.html", mode="login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash("User already exists")
            return redirect('/register')

        db.session.add(User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password'])
        ))
        db.session.commit()
        return redirect('/login')

    return render_template("auth.html", mode="reg")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    res = None

    if request.method == "POST":
        try:
            age = float(request.form['age'])
            chol = float(request.form['totChol'])
            bp = float(request.form['sysBP'])

            features = np.array([[age, chol, bp]])

            if rf_model and scaler:
                pred = rf_model.predict(scaler.transform(features))[0]
            else:
                score = 0
                if bp > 140: score += 2
                if chol > 240: score += 1
                pred = 1 if score >= 2 else 0

            res = "High Risk ⚠️" if pred == 1 else "Healthy ✅"

            db.session.add(Heart(
                user_id=current_user.id,
                age=age,
                totChol=chol,
                sysBP=bp,
                result=res
            ))
            db.session.commit()

        except Exception as e:
            flash(f"Error: {e}")

    history = Heart.query.filter_by(user_id=current_user.id).all()

    return render_template("dashboard.html",
                           result=res,
                           history=history)

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        q = request.json.get("query")
        if not model_ai:
            return jsonify({"response": "AI offline"})

        prompt = f"""
        Act as a Cardiologist.
        Respond ONLY in English.
        User Query: {q}
        """

        response = model_ai.generate_content(prompt)
        return jsonify({"response": response.text})

    except:
        return jsonify({"response": "AI Error"})

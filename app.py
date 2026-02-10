import os, pickle, numpy as np, pandas as pd, json
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

# --- CONFIG ---
app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(BASE, "store.db")
app.config['SECRET_KEY'] = "heart_secure_key"
db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = "login"

# --- AI SETUP ---
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
model_ai = None
if GENAI_API_KEY:
    try:
        genai.configure(api_key=GENAI_API_KEY)
        model_ai = genai.GenerativeModel('gemini-2.5-flash')
    except:
        pass


# --- DB MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)


class Heart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    # Features
    gender = db.Column(db.String(10))
    age = db.Column(db.Float)
    currentSmoker = db.Column(db.String(5))
    cigsPerDay = db.Column(db.Float)
    BPMeds = db.Column(db.String(5))
    prevalentStroke = db.Column(db.String(5))
    prevalentHyp = db.Column(db.String(5))
    diabetes = db.Column(db.String(5))
    totChol = db.Column(db.Float)
    sysBP = db.Column(db.Float)
    diaBP = db.Column(db.Float)
    BMI = db.Column(db.Float)
    heartRate = db.Column(db.Float)
    glucose = db.Column(db.Float)
    result = db.Column(db.String(100))
    created = db.Column(db.DateTime, default=datetime.utcnow)


@login.user_loader
def load_user(uid): return User.query.get(int(uid))


# --- ML LOADER ---
rf_model, scaler = None, None


def load_ml():
    global rf_model, scaler
    try:
        p_model = "rf_classifier.pkl" if os.path.exists("rf_classifier.pkl") else "Model/rf_classifier.pkl"
        p_scaler = "scaler.pkl" if os.path.exists("scaler.pkl") else "Model/scaler.pkl"
        if os.path.exists(p_model):
            rf_model = pickle.load(open(p_model, "rb"))
            scaler = pickle.load(open(p_scaler, "rb"))
    except:
        pass


load_ml()


# --- ROUTES ---
@app.route('/')
def home(): return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and check_password_hash(u.password, request.form['password']):
            u.last_login = datetime.utcnow()
            db.session.commit()
            login_user(u)
            return redirect('/dashboard')
        flash('Invalid Credentials')
    return render_template('auth.html', mode='login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            return redirect('/register')
        db.session.add(
            User(username=request.form['username'], password=generate_password_hash(request.form['password'])))
        db.session.commit()
        return redirect('/login')
    return render_template('auth.html', mode='reg')


@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect('/login')


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    res = None
    if request.method == "POST":
        try:
            f = request.form
            d = {
                'gender': f.get('gender'), 'age': float(f.get('age')),
                'currentSmoker': f.get('currentSmoker'), 'cigsPerDay': float(f.get('cigsPerDay', 0)),
                'BPMeds': f.get('BPMeds'), 'prevalentStroke': f.get('prevalentStroke'),
                'prevalentHyp': f.get('prevalentHyp'), 'diabetes': f.get('diabetes'),
                'totChol': float(f.get('totChol')), 'sysBP': float(f.get('sysBP')),
                'diaBP': float(f.get('diaBP')), 'BMI': float(f.get('BMI')),
                'heartRate': float(f.get('heartRate')), 'glucose': float(f.get('glucose'))
            }

            # Encode
            feats = np.array([[
                1 if d['gender'] == 'male' else 0, d['age'],
                1 if d['currentSmoker'] == 'yes' else 0, d['cigsPerDay'],
                1 if d['BPMeds'] == 'yes' else 0, 1 if d['prevalentStroke'] == 'yes' else 0,
                1 if d['prevalentHyp'] == 'yes' else 0, 1 if d['diabetes'] == 'yes' else 0,
                d['totChol'], d['sysBP'], d['diaBP'], d['BMI'], d['heartRate'], d['glucose']
            ]])

            if rf_model:
                pred = rf_model.predict(scaler.transform(feats))[0]
            else:
                score = 0
                if d['sysBP'] > 140: score += 2
                if d['totChol'] > 240: score += 1
                if d['diabetes'] == 'yes': score += 2
                pred = 1 if score >= 3 else 0

            res = "High Risk Detected ⚠️" if pred == 1 else "Heart is Healthy ✅"

            db.session.add(Heart(user_id=current_user.id, result=res, **d))
            db.session.commit()
            flash("Diagnosis Saved", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")


    # Fetch History
    hist = Heart.query.filter_by(user_id=current_user.id).order_by(Heart.created.desc()).all()
    latest = hist[0] if hist else None

    # Format data for graph
    dates = [h.created.strftime('%d-%b') for h in hist][::-1]
    bps = [h.sysBP for h in hist][::-1]
    chols = [h.totChol for h in hist][::-1]

    return render_template("dashboard.html",
                           user=current_user,
                           result=res,
                           history=hist,
                           latest=latest,
                           dates=json.dumps(dates),
                           bp_data=json.dumps(bps),
                           chol_data=json.dumps(chols))


@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        q = request.json.get('query')
        if not model_ai: return jsonify({'response': "AI offline.", 'type': 'text'})


        # New Prompt to handle specific data
        prompt = f"""
        Act as a Senior Cardiologist. 
        User Query: "{q}"

        If the query contains health data (BP, Cholesterol, etc.), analyze it specifically.

        CRITICAL INSTRUCTION: You MUST respond in ENGLISH only. Do not use any other language.

        Format your response as a valid JSON array of objects: 
        [
            {{"title": "Analysis/Advice Title", "detail": "Specific detail based on the data provided."}},
            {{"title": "Action Item", "detail": "What to do next."}}
        ]
        Do not use markdown.
        """

        res = model_ai.generate_content(prompt)
        txt = res.text.replace("```json", "").replace("```", "").strip()
        return jsonify({'response': txt, 'type': 'json'})
    except:
        return jsonify({'response': "AI Error.", 'type': 'text'})



if __name__ == "__main__":
    with app.app_context(): db.create_all()
    app.run(debug=False)
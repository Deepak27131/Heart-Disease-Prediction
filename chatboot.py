import os, pickle, numpy as np, pandas as pd, json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

# -------------------- APP CONFIGURATION --------------------
app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(BASE, "store.db")
app.config['SECRET_KEY'] = "supersecretkey123"
db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = "login"

# -------------------- GEMINI AI SETUP --------------------
# Apni API Key yahan daalein
GENAI_API_KEY = "AIzaSyBk01VZ8rXgDVfJgToPXj4E17mLsBprZqg"

model_ai = None
if GENAI_API_KEY:
    try:
        genai.configure(api_key=GENAI_API_KEY)
        model_ai = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini AI Connected Successfully")
    except Exception as e:
        print(f"⚠️ AI Connection Warning: {e}")


# -------------------- DATABASE MODELS --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)


class Heart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    # Features matching Framingham Dataset (14 inputs)
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
def load_user(uid):
    return User.query.get(int(uid))


# -------------------- LOAD ML MODEL --------------------
rf_model = None
scaler = None


def load_ml_assets():
    global rf_model, scaler
    try:
        # Check current directory or Model/ subdirectory
        if os.path.exists("rf_classifier.pkl"):
            rf_model = pickle.load(open("rf_classifier.pkl", "rb"))
            scaler = pickle.load(open("scaler.pkl", "rb"))
        elif os.path.exists("Model/rf_classifier.pkl"):
            rf_model = pickle.load(open("Model/rf_classifier.pkl", "rb"))
            scaler = pickle.load(open("Model/scaler.pkl", "rb"))

        if rf_model:
            print("✅ ML Model Loaded Successfully")
        else:
            print("⚠️ ML Files Not Found (Using Rule-Based Logic)")
    except Exception as e:
        print(f"⚠️ Error loading ML model: {e}")


load_ml_assets()


# -------------------- ROUTES --------------------

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for("login"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=u).first():
            flash("Username already taken")
            return redirect('/register')
        db.session.add(User(username=u, password=p))
        db.session.commit()
        return redirect('/login')
    return render_template("auth.html", mode="register")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect('/dashboard')
        flash("Invalid Username or Password")
    return render_template("auth.html", mode="login")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    prediction_result = None

    if request.method == "POST" and 'predict_btn' in request.form:
        try:
            f = request.form

            # 1. Capture Form Data
            male = f.get('gender', 'female')
            age = float(f.get('age', 0))
            currentSmoker = f.get('currentSmoker', 'no')
            cigsPerDay = float(f.get('cigsPerDay', 0))
            BPMeds = f.get('BPMeds', 'no')
            prevalentStroke = f.get('prevalentStroke', 'no')
            prevalentHyp = f.get('prevalentHyp', 'no')
            diabetes = f.get('diabetes', 'no')
            totChol = float(f.get('totChol', 0))
            sysBP = float(f.get('sysBP', 0))
            diaBP = float(f.get('diaBP', 0))
            BMI = float(f.get('BMI', 0))
            heartRate = float(f.get('heartRate', 0))
            glucose = float(f.get('glucose', 0))

            # 2. Encode Data for Model (1 = Yes/Male, 0 = No/Female)
            male_enc = 1 if male.lower() == "male" else 0
            smoker_enc = 1 if currentSmoker.lower() == "yes" else 0
            bpmeds_enc = 1 if BPMeds.lower() == "yes" else 0
            stroke_enc = 1 if prevalentStroke.lower() == "yes" else 0
            hyp_enc = 1 if prevalentHyp.lower() == "yes" else 0
            diab_enc = 1 if diabetes.lower() == "yes" else 0

            # Feature Array (Order must match Notebook training)
            features = np.array([[
                male_enc, age, smoker_enc, cigsPerDay, bpmeds_enc,
                stroke_enc, hyp_enc, diab_enc, totChol, sysBP,
                diaBP, BMI, heartRate, glucose
            ]])

            # 3. Predict
            if rf_model and scaler:
                scaled_features = scaler.transform(features)
                pred = rf_model.predict(scaled_features)[0]
            else:
                # Rule-Based Logic (Fallback)
                risk_score = 0
                if sysBP > 140 or diaBP > 90: risk_score += 2
                if totChol > 240: risk_score += 1
                if smoker_enc == 1: risk_score += 1
                if BMI > 30: risk_score += 1
                if glucose > 120: risk_score += 1
                if age > 60: risk_score += 1
                pred = 1 if risk_score >= 3 else 0

            prediction_result = "⚠️ High Risk of Heart Disease" if pred == 1 else "✅ Heart seems Healthy"

            # 4. Save Record
            rec = Heart(
                user_id=current_user.id,
                gender=male, age=age, currentSmoker=currentSmoker, cigsPerDay=cigsPerDay,
                BPMeds=BPMeds, prevalentStroke=prevalentStroke, prevalentHyp=prevalentHyp, diabetes=diabetes,
                totChol=totChol, sysBP=sysBP, diaBP=diaBP, BMI=BMI, heartRate=heartRate, glucose=glucose,
                result=prediction_result
            )
            db.session.add(rec)
            db.session.commit()
            flash("Report Generated Successfully", "success")

        except Exception as e:
            print(f"Error: {e}")
            flash(f"Input Error: {str(e)}", "danger")

    # Fetch Data for Graphs & History
    history = Heart.query.filter_by(user_id=current_user.id).order_by(Heart.created).all()

    dates = [r.created.strftime('%Y-%m-%d') for r in history]
    bp_data = [r.sysBP for r in history]
    chol_data = [r.totChol for r in history]

    return render_template("dashboard.html",
                           user=current_user,
                           result=prediction_result,
                           history=history,
                           dates=json.dumps(dates),
                           bp_data=json.dumps(bp_data),
                           chol_data=json.dumps(chol_data))


# -------------------- AI ENDPOINT --------------------
@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    data = request.json
    try:
        # Prompt for JSON Tips
        prompt = f"""Act as a Doctor. User asks: "{data.get('query')}". 
        Provide 3 specific health tips based on the query.
        Format strictly as JSON Array: [{{"title": "Tip Headline", "detail": "Tip Explanation"}}]. 
        No markdown blocks."""

        if model_ai:
            resp = model_ai.generate_content(prompt)
            text = resp.text.replace("```json", "").replace("```", "").strip()
            return jsonify({'response': text, 'type': 'json'})
        else:
            return jsonify({'response': "AI is not connected.", 'type': 'text'})
    except:
        return jsonify({'response': "Dr. AI is currently offline.", 'type': 'text'})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
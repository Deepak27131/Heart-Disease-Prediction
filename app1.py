from flask import Flask, request, render_template
import pickle
import numpy as np

app = Flask(__name__)

# Load model and scaler
model = pickle.load(open('Model/rf_classifier.pkl', 'rb'))
scaler = pickle.load(open('Model/scaler.pkl', 'rb'))

# Safe conversion functions
def safe_int(value, default=0):
    try:
        return int(value) if value.strip() != '' else default
    except:
        return default

def safe_float(value, default=0.0):
    try:
        return float(value) if value.strip() != '' else default
    except:
        return default

# Prediction function
def predict(model, scaler, male, age, currentSmoker, cigsPerDay, BPMeds,
            prevalentStroke, prevalentHyp, diabetes, totChol, sysBP,
            diaBP, BMI, heartRate, glucose):

    # Features array
    features = np.array([[male, age, currentSmoker, cigsPerDay, BPMeds,
                          prevalentStroke, prevalentHyp, diabetes,
                          totChol, sysBP, diaBP, BMI, heartRate, glucose]])

    # Scale the features
    scaled_features = scaler.transform(features)

    # Predict using the model
    result = model.predict(scaled_features)
    return result[0]

# Routes


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])

def predict_route():
    if request.method == 'POST':
        male = safe_int(request.form.get('gender'))
        age = safe_int(request.form.get('age'))
        currentSmoker = safe_int(request.form.get('currentSmoker'))
        cigsPerDay = safe_float(request.form.get('cigsPerDay'))
        BPMeds = safe_int(request.form.get('BPMeds'))
        prevalentStroke = safe_int(request.form.get('prevalentStroke'))
        prevalentHyp = safe_int(request.form.get('prevalentHyp'))
        diabetes = safe_int(request.form.get('diabetes'))
        totChol = safe_float(request.form.get('totChol'))
        sysBP = safe_float(request.form.get('sysBP'))
        diaBP = safe_float(request.form.get('diaBP'))
        BMI = safe_float(request.form.get('BMI'))
        heartRate = safe_float(request.form.get('heartRate'))
        glucose = safe_float(request.form.get('glucose'))

        prediction = predict(model, scaler, male, age, currentSmoker,
                             cigsPerDay, BPMeds, prevalentStroke,
                             prevalentHyp, diabetes, totChol, sysBP,
                             diaBP, BMI, heartRate, glucose)

        prediction_text = "The Patient has Heart Disease" if prediction == 1 else "The Patient has No Heart Disease"

        return render_template('index.html', prediction=prediction_text)

if __name__ == '__main__':
    app.run(debug=True)

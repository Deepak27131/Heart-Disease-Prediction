
import pandas as pd
import numpy as np
import pickle
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

try:
    # 1. Load Data
    print("Loading dataset...")
    df = pd.read_csv('datasets_4123_6408_framingham.csv')
    
    # 2. Preprocess
    # Drop NaNs just like typical training (assuming model was trained on clean data)
    print(f"Original shape: {df.shape}")
    df.dropna(inplace=True)
    print(f"Shape after dropping NaNs: {df.shape}")
    
    # Define features and target (TenYearCHD is usually the target in Framingham)
    target_col = 'TenYearCHD'
    
    if target_col not in df.columns:
        # Fallback if target column name is different, print columns to debug
        print(f"Error: Target column '{target_col}' not found. Available columns: {df.columns.tolist()}")
        exit()
        
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Ensure feature order matches app1.py expectation
    # app1.py order: male, age, currentSmoker, cigsPerDay, BPMeds, prevalentStroke, prevalentHyp, diabetes, totChol, sysBP, diaBP, BMI, heartRate, glucose
    expected_features = ['male', 'age', 'currentSmoker', 'cigsPerDay', 'BPMeds', 'prevalentStroke', 'prevalentHyp', 'diabetes', 'totChol', 'sysBP', 'diaBP', 'BMI', 'heartRate', 'glucose']
    
    # Reorder X columns just in case
    X = X[expected_features]
    
    # 3. Load Model and Scaler
    print("Loading model and scaler...")
    # Try local path or Model/ path
    try:
        model = pickle.load(open('Model/rf_classifier.pkl', 'rb'))
        scaler = pickle.load(open('Model/scaler.pkl', 'rb'))
    except FileNotFoundError:
        model = pickle.load(open('rf_classifier.pkl', 'rb'))
        scaler = pickle.load(open('scaler.pkl', 'rb'))
        
    # 4. Predict
    print("Scaling features...")
    X_scaled = scaler.transform(X)
    
    print("Predicting...")
    y_pred = model.predict(X_scaled)
    
    # 5. Evaluate
    acc = accuracy_score(y, y_pred)
    cm = confusion_matrix(y, y_pred)
    report = classification_report(y, y_pred)
    

    # Prediction Error (1 - Accuracy)
    error = 1 - acc
    
    with open('model_evaluation_results.txt', 'w') as f:
        f.write("="*50 + "\n")
        f.write(f"Model Accuracy: {acc:.4f} ({acc*100:.2f}%)\n")
        f.write("="*50 + "\n")
        f.write("\nConfusion Matrix:\n")
        f.write(str(cm) + "\n")
        f.write("\nClassification Report:\n")
        f.write(report + "\n")
        f.write(f"\nPrediction Error: {error:.4f}\n")
        
    print("Results saved to model_evaluation_results.txt")

except Exception as e:
    with open('model_evaluation_results.txt', 'w') as f:
        f.write(f"Error occurred: {e}")
    print(f"Error: {e}")

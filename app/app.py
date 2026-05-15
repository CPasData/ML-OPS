from flask import Flask, request, jsonify
import pandas as pd
import joblib

app = Flask(__name__)

#Cargamos el modelo
model = joblib.load("./models/random_forest_churn.pkl")

features = [
    "credit_score",
    "country",
    "age",
    "tenure",
    "balance",
    "producs_number",
    "credit_card",
    "active_member",
    "estimated_salary",
]

@app.route("/")
def home():
    return "<h1> Predictor de 'churn' en bancos tradicionales</h1>"

# --- 1. Ruta de estado (/health) --- 
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "churn-classifier"})

# --- 2. Ruta 
if __name__ == "__main__":
    app.run(debug=True, port= 5000)
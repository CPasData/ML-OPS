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
# Comprueba que la API está funcionando
# ===========================================================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "churn-classifier"})

# --- 2. Predicción por path --- 
# Recibe el credit_score del cliente en la URL
# Ejemplo: http://127.0.0.1:5000/api/v1/predict/650
# ===========================================================
@app.route('/api/v1/predict/<int:credit_score>', methods=['GET'])
def predict_credit_score(credit_score):
    #Creamos un cliente
    Cliente = pd.DataFrame([{
        'credit_score': credit_score, # Puntaje de credito del cliente
        'country': 'France',          # Pais del cliente
        'gender': 'Male',             # Genero del cliente
        'age': 38,                    # Edad del cliente
        'tenure': 5,                  # Años como cliente
        'balance': 76485.0,           # Saldo en cuenta
        'products_number': 1,         # Número de productos contratados
        'credit_card': 1,             # Si tiene tarjeta credito (1/0)
        'active_member': 1,           # Si es miembro activo (1/0)
        'estimated_salary': 100090.0  # Salario estimado     
    }])

    prediccion = model.predict(Cliente)[0]  # # modelo.predict(Cliente) --> devuelve un array -->, array([0])
    # Probabilidad de churn
    probabilidad = model.predict_proba(Cliente)[0][1] #modelo.predict_proba(Cliente) --> devuelve un array 2D--> array([[0.7588, 0.2412]])
    # Probabilidad de churn

    return jsonify({
        'credit_score': credit_score,
        'churn': int(prediccion),
        'resultado': 'Abandona el banco' if prediccion == 1 else 'Se queda',
        'probabilidad churn': round(float(probabilidad),4)
    })

# --- 3. Predicción por query --- 
# Recibe parámetros opcionales en la query string
# Ejemplo: http://127.0.0.1:5000/api/v1/predict/filter?age=45&country=Germany
# ===========================================================
@app.route('/api/v1/predict/filter', methods = ['GET'])
def predict_quey():
    # Parámetros
    age = request.args.get('age', 38, type= int)   # si no viene, usa 38 por defecto
    country = request.args.get('country','France') # si no viene, usa France
    balance = request.args.get('balance', 76485.0, type=float) # si  no viene, usa la media

    #Creamos un cliente
    Cliente = pd.DataFrame([{
        'credit_score': 550,          # Puntaje de credito del cliente
        'country': country,           # Pais del cliente (Parametro query)
        'gender': 'Male',             # Genero del cliente
        'age': age,                   # Edad del cliente (Parametro query)
        'tenure': 5,                  # Años como cliente
        'balance': balance,           # Saldo en cuenta (Parametro query)
        'products_number': 1,         # Número de productos contratados
        'credit_card': 1,             # Si tiene tarjeta credito (1/0)
        'active_member': 1,           # Si es miembro activo (1/0)
        'estimated_salary': 50090.0  # Salario estimado     
    }])

    prediccion = model.predict(Cliente)[0] # modelo.predict(Cliente) --> devuelve un array -->, array([0]) 
    # Probabilidad de churn
    probabilidad = model.predict_proba(Cliente)[0][1] # modelo.predict_proba(Cliente) --> devuelve un array 2D--> array([[0.7588, 0.2412]])

    return jsonify({
        "parametros_recibidos": {"age": age, "country": country, "balance": balance},
        "churn": int(prediccion),
        "resultado": "Abandona el banco" if prediccion == 1 else "Se queda",
        "probabilidad_churn": round(float(probabilidad), 4)
    })

# --- 3. Predicción por JSON --- 
# Recibe todos los datos del cliente en el cuerpo de la petición
# Es la ruta principal de predicción
# ===========================================================
@app.route('/api/v1/predict', methods=['POST'])
def predict():
    datos = request.get_json()   # recoge el JSON del cuerpo de la petición

    # Validación básica - comprobamos que llegaron datos
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400  # 400 = Bad Request

    cliente = pd.DataFrame([{
        'credit_score':     datos.get('credit_score', 650),
        'country':          datos.get('country', 'France'),
        'gender':           datos.get('gender', 'Male'),
        'age':              datos.get('age', 38),
        'tenure':           datos.get('tenure', 5),
        'balance':          datos.get('balance', 76485.0),
        'products_number':  datos.get('products_number', 1),
        'credit_card':      datos.get('credit_card', 1),
        'active_member':    datos.get('active_member', 1),
        'estimated_salary': datos.get('estimated_salary', 100090.0)
    }])

    prediccion = model.predict(cliente)[0]
    probabilidad = model.predict_proba(cliente)[0][1]

    return jsonify({
        "datos_recibidos": datos,
        "churn": int(prediccion),
        "resultado": "Abandona el banco" if prediccion == 1 else "Se queda",
        "probabilidad_churn": round(float(probabilidad), 4)
    })


# --- 5. Arranca el servidor Flask 
if __name__ == "__main__":
    app.run(debug=True, port= 5000)
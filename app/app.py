from flask import Flask, request, jsonify
from pathlib import Path
import pandas as pd
import joblib
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["JSON_AS_ASCII"] = False  # Para que los acentos se muestren bien

carpeta_script = Path(__file__).parent.absolute()  # Ruta absoluta de la carpeta donde está app.py

# -----------------------------------------------------------------------
# Ruta 0 - Home
# -----------------------------------------------------------------------

@app.route("/")
def home():
    return "<h1>Predictor de churn en bancos tradicionales</h1>"

# -----------------------------------------------------------------------
# ----Cargamos el modelo al arrancar la app (solo se carga una vez)
# -----------------------------------------------------------------------
model = joblib.load(carpeta_script / '..' / 'models' / 'random_forest_churn.pkl')

# -----------------------------------------------------------------------
# Creamos la BD y la tabla predicciones si no existen
# Se ejecuta solo una vez al arrancar la app
# -----------------------------------------------------------------------

def createdb():
    connection = sqlite3.connect(carpeta_script / 'churn.db')  # Crea el archivo .db si no existe
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_score INTEGER,
            country      TEXT,
            gender       TEXT,
            age          INTEGER,
            tenure       INTEGER,
            balance      REAL,
            products_number INTEGER,
            credit_card  INTEGER,
            active_member INTEGER,
            estimated_salary REAL,
            churn        INTEGER,
            resultado    TEXT,
            probabilidad REAL,
            fecha        TEXT
        )
    """)
    connection.commit()
    connection.close()

createdb()  # Llamamos a la función al arrancar la app

# -----------------------------------------------------------------------
# Manejo de errores
# -----------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    # 404 -> ruta no encontrada
    return jsonify({"error": "Ruta no encontrada", "codigo": 404}), 404

@app.errorhandler(500)
def server_error(e):
    # 500 -> error interno del servidor
    return jsonify({"error": "Error interno del servidor", "codigo": 500}), 500

# -----------------------------------------------------------------------
# Ruta 1 - de estado (/health) --- 
# Comprueba que la API está funcionando
# -----------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "Random Forest"})

# -----------------------------------------------------------------------
# Ruta 2 - Predicción por path 
# Recibe el credit_score del cliente en la URL
# Ejemplo: http://127.0.0.1:5000/api/v1/predict/650
# -----------------------------------------------------------------------

@app.route('/api/v1/predict/<int:credit_score>', methods=['GET'])
def predict_credit_score(credit_score):

    # Validación del rango de credit_score
    # if credit_score < 350 or credit_score > 850:
    #     return jsonify({"error": "credit_score debe estar entre 350 y 850"}), 400

    #Creamos un cliente
    Cliente = pd.DataFrame([{
        'credit_score': credit_score, # Puntaje de credito del cliente (Parámetro )
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
        'probabilidad_churn': round(float(probabilidad),4)
    })

# -----------------------------------------------------------------------
# Ruta 3 - Predicción por query
# Recibe parámetros opcionales en la query string
# Ejemplo: http://127.0.0.1:5000/api/v1/predict/filter?age=45&country=Germany&balance=76400
# -----------------------------------------------------------------------
@app.route('/api/v1/predict/filter', methods = ['GET'])
def predict_quey():
    # Parámetros
    age     = request.args.get('age', 38, type= int)   # si no viene, usa 38 por defecto
    country = request.args.get('country','France') # si no viene, usa France
    balance = request.args.get('balance', 76485.0, type=float) # si  no viene, usa la media

    # Validación de parámetros
    #paises_validos = ['France', 'Spain', 'Germany']
    #if country not in paises_validos:
    #    return jsonify({"error": f"country debe ser uno de {paises_validos}"}), 400

    #if age < 18 or age > 92:
    #    return jsonify({"error": "age debe estar entre 18 y 92"}), 400

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

# -----------------------------------------------------------------------
# Ruta 4 - Predicción por JSON + guarda en BD
# Recibe todos los datos del cliente en el cuerpo de la petición
# POST /api/v1/predict
# -----------------------------------------------------------------------

@app.route('/api/v1/predict', methods=['POST'])
def predict():
    datos = request.get_json()   # recoge el JSON del cuerpo de la petición

    # Validación básica - comprobamos que llegaron datos
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400  # 400 = Bad Request
    
    # Validación de campos obligatorios
    campos_obligatorios = ['credit_score', 'country', 'gender', 'age',
                           'tenure', 'balance', 'products_number',
                           'credit_card', 'active_member', 'estimated_salary']
    
    campos_faltantes = [c for c in campos_obligatorios if c not in datos]

    if campos_faltantes:
        return jsonify({"error": f"Faltan campos obligatorios: {campos_faltantes}"}), 400

    #Creamos un cliente
    cliente = pd.DataFrame([{
        'credit_score':     datos.get('credit_score'),
        'country':          datos.get('country'),
        'gender':           datos.get('gender'),
        'age':              datos.get('age'),
        'tenure':           datos.get('tenure'),
        'balance':          datos.get('balance'),
        'products_number':  datos.get('products_number'),
        'credit_card':      datos.get('credit_card'),
        'active_member':    datos.get('active_member'),
        'estimated_salary': datos.get('estimated_salary')
    }])

    prediccion = model.predict(cliente)[0]
    probabilidad = model.predict_proba(cliente)[0][1]

    # Guardar predicción en SQLite
    connection = sqlite3.connect(carpeta_script / 'churn.db')
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO predicciones 
        (credit_score, country, gender, age, tenure, balance,
         products_number, credit_card, active_member, estimated_salary,
         churn, resultado, probabilidad, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos.get('credit_score'),
        datos.get('country'),
        datos.get('gender'),
        datos.get('age'),
        datos.get('tenure'),
        datos.get('balance'),
        datos.get('products_number'),
        datos.get('credit_card'),
        datos.get('active_member'),
        datos.get('estimated_salary'),
        int(prediccion),
        'Abandona el banco' if prediccion == 1 else 'Se queda',
        round(float(probabilidad), 4),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    connection.commit()
    connection.close()

    return jsonify({
        "datos_recibidos": datos,
        "churn": int(prediccion),
        "resultado": "Abandona el banco" if prediccion == 1 else "Se queda",
        "probabilidad_churn": round(float(probabilidad), 4)
    })

# -----------------------------------------------------------------------
# Ruta 5 - Historial de predicciones
# Muestra todas las predicciones guardadas en la BD
# GET /api/v1/predicciones
# -----------------------------------------------------------------------

@app.route('/api/v1/predicciones', methods=['GET'])
def get_predicciones():
    connection = sqlite3.connect(carpeta_script / 'churn.db')
    cursor = connection.cursor()

    # fetchall() devuelve una lista de tuplas con todos los registros
    result = cursor.execute("SELECT * FROM predicciones").fetchall()
    connection.close()

    # Si no hay predicciones, devolvemos mensaje claro
    if not result:
        return jsonify({"mensaje": "No hay predicciones guardadas aún", "predicciones": []}), 200

    return jsonify({"total": len(result), "predicciones": result})

# -----------------------------------------------------------------------
# Ruta 6 - Contador de predicciones
# Cuenta cuántas predicciones se han guardado
# GET /api/v1/predicciones/count
# -----------------------------------------------------------------------
@app.route('/api/v1/predicciones/count', methods=['GET'])
def count_predicciones():
    connection = sqlite3.connect(carpeta_script / 'churn.db')
    cursor = connection.cursor()

    # fetchone() devuelve una sola tupla con el resultado
    result = cursor.execute("SELECT COUNT(*) FROM predicciones").fetchone()
    connection.close()

    return jsonify({"total_predicciones": result[0]})

# -----------------------------------------------------------------------
#  Arranca el servidor Flask 
# -----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port= 5000)


import streamlit as st
import requests
import pandas as pd

# ── Configuración ──────────────────────────────────────────────────────────────
API_URL = "https://ml-ops-iwax.onrender.com"
st.set_page_config(
    page_title="Bank Churn Prediction",
    page_icon="🏦",
    layout="centered",
)

# ── Estilos globales ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 750px; }
    .stButton > button {
        width: 100%;
        background-color: #1a1a2e;
        color: white;
        border: none;
        padding: 0.6rem;
        font-size: 1rem;
        border-radius: 8px;
        margin-top: 0.5rem;
    }
    .stButton > button:hover { background-color: #16213e; }
    .result-box {
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-top: 1rem;
    }
    .risk-alto  { background:#ffe5e5; border-left: 6px solid #e74c3c; }
    .risk-bajo  { background:#e8f8f0; border-left: 6px solid #2ecc71; }
    .big-number { font-size: 3rem; font-weight: 700; margin: 0; }
    .risk-label { font-size: 1.1rem; color: #555; margin-top: 4px; }
    .section-divider { border-top: 1px solid #e0e0e0; margin: 2rem 0 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Historial en sesión ────────────────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []

# ── Helper: mostrar resultado ──────────────────────────────────────────────────
def mostrar_resultado(result):
    prob  = result["probabilidad_churn"]
    churn = result["churn"]
    emoji = "🔴" if churn else "🟢"
    pct   = f"{prob * 100:.1f}%"
    label = "ABANDONA EL BANCO" if churn else "SE QUEDA"

    st.markdown(f"""
    <div class="result-box {'risk-alto' if churn else 'risk-bajo'}">
        <p class="big-number">{emoji} {pct}</p>
        <p class="risk-label">Predicción: <strong>{label}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Ver respuesta completa de la API"):
        st.json(result)

def guardar_historial(endpoint, payload, result):
    st.session_state.historial.append({
        "endpoint": endpoint,
        "payload":  payload,
        "churn":    result.get("churn"),
        "prob":     result.get("probabilidad_churn"),
    })

# ── Navegación lateral ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏦 Bank Churn")
    st.caption("Predicción de abandono bancario")
    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        ["🏠 Inicio", "📊 Predicción", "📋 Historial"],
        label_visibility="collapsed",
    )
    st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — INICIO
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "🏠 Inicio":
    st.title("🏦 Bank Churn Prediction App")
    st.markdown("""
    **¡Hola!** Si estás aquí es porque te preocupa la fidelidad de tus clientes.
    No te preocupes, estoy aquí para ayudarte. Esta app permite saber la probabilidad de abandono de un cliente. **Pruébame**
    """)

    st.markdown("---")
    st.subheader("Estado de la API")

    if st.button("🔄 Comprobar conexión con la API"):
        try:
            r = requests.get(f"{API_URL}/health", timeout=10)
            if r.status_code == 200:
                data = r.json()
                st.success("✅ API activa")
                st.markdown(f"**Modelo cargado:** `{data.get('model', 'desconocido')}`")
            else:
                st.error(f"⚠️ Respuesta inesperada: {r.status_code}")
        except requests.exceptions.Timeout:
            st.warning("⏳ Timeout — el servicio puede estar arrancando (plan gratuito). Espera 30 s e inténtalo de nuevo.")
        except Exception as e:
            st.error(f"❌ No se puede conectar: {e}")

    st.markdown("---")
    st.subheader("Endpoints disponibles")
    st.markdown("""
    | Método | Ruta | Descripción |
    |--------|------|-------------|
    | `GET`  | `/health` | Estado del servicio |
    | `GET`  | `/predict/<credit_score>` | Predicción rápida por credit score |
    | `GET`  | `/predict/filter` | Predicción con filtros por query params |
    | `POST` | `/predict` | Predicción completa con body JSON |
    | `GET`  | `/predicciones` | Historial de predicciones |
    | `GET`  | `/predicciones/count` | Contador total de predicciones |
    """)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — PREDICCIÓN
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📊 Predicción":
    st.title("📊 Predicción de 'churn'")

    # ── Sección 1: Por credit score (PATH) ────────────────────────────────────
    st.subheader("1 · Por Credit Score")
    st.caption("Medida numérica que estima el riesgo financiero, la capacidad de pago y la probabilidad de impago. \n"
    "Llama a `GET /api/v1/predict/<credit_score>`")

    credit_score = st.slider("Credit Score", 350, 850, 650, step=10)

    if st.button("Predecir por credit score"):
        with st.spinner("Consultando la API..."):
            try:
                r = requests.get(f"{API_URL}/api/v1/predict/{credit_score}", timeout=15)
                result = r.json()
                if r.status_code == 200:
                    mostrar_resultado(result)
                    guardar_historial(f"{API_URL}/api/v1/predict/{credit_score}", {"credit_score": credit_score}, result)
                else:
                    st.error(f"Error {r.status_code}: {result.get('error', 'desconocido')}")
            except requests.exceptions.Timeout:
                st.warning("⏳ La API tardó demasiado. Espera 30 s e inténtalo de nuevo.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Sección 2: Por filtros (QUERY PARAMS) ─────────────────────────────────
    st.subheader("2 · Por Filtros")
    st.caption("Llama a `GET /predict/filter?`")

    col1, col2 = st.columns(2)
    with col1:
        age     = st.slider("Edad", 18, 80, 40)
        balance = st.slider("Saldo (€)", 0, 250000, 50000, step=1000)
    with col2:
        country = st.selectbox("País", ["Spain", "Germany", "France"])

    if st.button("Predecir con filtros"):
        with st.spinner("Consultando la API..."):
            try:
                params = {"age": age, "country": country, "balance": balance}
                r = requests.get(f"{API_URL}/api/v1/predict/filter", params=params, timeout=15)
                result = r.json()
                if r.status_code == 200:
                    mostrar_resultado(result)
                    guardar_historial(f"{API_URL}/api/v1/predict/filter", params, result)
                else:
                    st.error(f"Error {r.status_code}: {result.get('error', 'desconocido')}")
            except requests.exceptions.Timeout:
                st.warning("⏳ La API tardó demasiado. Espera 30 s e inténtalo de nuevo.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Sección 3: Predicción completa (POST JSON) ────────────────────────────
    st.subheader("3 · Predicción Completa")
    st.caption("Llama a `POST /predict` con body JSON completo")

    col1, col2 = st.columns(2)
    with col1:
        cs2        = st.number_input("Credit Score",         300, 900,  650)
        age2       = st.number_input("Edad",                  18, 100,   35)
        tenure     = st.number_input("Años como cliente",      0,  10,    5)
        balance2   = st.number_input("Saldo (€)",             0.0, 300000.0, 50000.0, step=1000.0)
        n_products = st.selectbox("Número de productos",     [1, 2, 3, 4])
    with col2:
        has_cc     = st.selectbox("¿Tarjeta de crédito?",    [1, 0], format_func=lambda x: "Sí" if x else "No")
        is_active  = st.selectbox("¿Miembro activo?",        [1, 0], format_func=lambda x: "Sí" if x else "No")
        salary     = st.number_input("Salario estimado (€)", 0.0, 300000.0, 60000.0, step=1000.0)
        country2   = st.selectbox("País ",                   ["Spain", "Germany", "France"])
        gender     = st.selectbox("Género",                  ["Male", "Female"])

    if st.button("Predecir con formulario completo"):
        payload = {
            "credit_score":         cs2,
            "age":                  age2,
            "tenure":               tenure,
            "balance":              balance2,
            "products_number":      n_products,
            "credit_card":          has_cc,
            "active_member":        is_active,
            "estimated_salary":     salary,
            "country":              country2,
            "gender":               gender
        }
        with st.spinner("Consultando la API..."):
            try:
                r = requests.post(f"{API_URL}/api/v1/predict", json=payload, timeout=15)
                result = r.json()
                if r.status_code == 200:
                    mostrar_resultado(result)
                    guardar_historial(f"{API_URL}/api/v1/predict (POST)", payload, result)
                else:
                    st.error(f"Error {r.status_code}: {result.get('error', 'desconocido')}")
            except requests.exceptions.Timeout:
                st.warning("⏳ La API tardó demasiado. Espera 15 s e inténtalo de nuevo.")
            except Exception as e:
                st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — HISTORIAL
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📋 Historial":
    st.title("📋 Historial de Predicciones")

    # ── Sección 1: Predicciones de esta sesión + BD ───────────────────────────
    st.subheader("1 · Predicciones guardadas en la BD")
    st.caption("Llama a `GET /api/v1/predicciones`")

    # Carga automática al entrar — sin necesidad de botón
    try:
        import pandas as pd
        r = requests.get(f"{API_URL}/api/v1/predicciones", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data["total"] == 0:
                st.info("Aún no hay predicciones guardadas. Ve a Predicción y usa el formulario completo.")
            else:
                df = pd.DataFrame(data["predicciones"], columns=[
                    "id", "credit_score", "country", "gender", "age",
                    "tenure", "balance", "products_number", "credit_card",
                    "active_member", "estimated_salary", "churn",
                    "resultado", "probabilidad", "fecha"
                ])
                df["churn"] = df["churn"].map({1: "🔴 Abandona", 0: "🟢 Se queda"})
                df["probabilidad"] = df["probabilidad"].apply(lambda x: f"{x*100:.1f}%")
                st.dataframe(df[["id", "credit_score", "country", "age",
                                "churn", "probabilidad", "fecha"]],
                            use_container_width=True)
    except Exception as e:
        st.error(f"Error cargando BD: {e}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Sección 2: Predicciones de esta sesión ────────────────────────────────
    st.subheader("2 · Predicciones de esta sesión")
    st.caption("Incluye todas las predicciones realizadas (path, query y POST)")

    if st.session_state.historial:
        df_sesion = pd.DataFrame(st.session_state.historial)
        df_sesion["churn"] = df_sesion["churn"].map({1: "🔴 Abandona", 0: "🟢 Se queda", None: "—"})
        df_sesion["prob"] = df_sesion["prob"].apply(lambda x: f"{x*100:.1f}%" if x is not None else "—")
        df_sesion.columns = ["Endpoint", "Payload", "Churn", "Probabilidad"]
        st.dataframe(df_sesion[["Endpoint", "Churn", "Probabilidad"]], use_container_width=True)

        if st.button("🗑️ Limpiar historial de sesión"):
            st.session_state.historial = []
            st.rerun()
    else:
        st.info("Aún no hay predicciones en esta sesión.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Sección 3: Contador total ──────────────────────────────────────────────
    st.subheader("3 · Contador predicciones en BD")
    st.caption("Llama a `GET /api/v1/predicciones/count`")

    if st.button("🔢 Obtener contador de la API"):
        with st.spinner("Consultando la API..."):
            try:
                r = requests.get(f"{API_URL}/api/v1/predicciones/count", timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    st.metric("Total de predicciones realizadas", data.get("total_predicciones", "—"))
                else:
                    st.error(f"Error {r.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")   


# elif pagina == "📋 Historial":
#     st.title("📋 Historial de Predicciones")

#     # ── Sección 1: Tabla de predicciones ──────────────────────────────────────
#     st.subheader("1 · Predicciones de esta sesión")
#     st.caption("Llama a `GET /predicciones`")

#     if st.session_state.historial:
#         df = pd.DataFrame(st.session_state.historial)
#         df["churn"] = df["churn"].map({True: "✅ Sí", False: "❌ No"})
#         df["prob"]  = df["prob"].apply(lambda x: f"{x*100:.1f}%")
#         df.columns  = ["Endpoint", "Payload", "Churn", "Probabilidad"]
#         st.dataframe(df[["Endpoint", "Churn", "Probabilidad"]], use_container_width=True)

#         if st.button("🗑️ Limpiar historial"):
#             st.session_state.historial = []
#             st.rerun()
#     else:
#         st.info("Aún no hay predicciones en esta sesión. Ve a la página de Predicción y realiza algunas consultas.")

#     st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

#     # ── Sección 2: Contador total ──────────────────────────────────────────────
#     st.subheader("2 · Contador total de predicciones")
#     st.caption("Llama a `GET /predicciones/count`")

#     if st.button("🔢 Obtener contador de la API"):
#         with st.spinner("Consultando la API..."):
#             try:
#                 r = requests.get(f"{API_URL}/api/v1/predicciones/count", timeout=10)
#                 if r.status_code == 200:
#                     data  = r.json()
#                     total = data.get("total_predicciones", data.get("count", "—"))
#                     st.metric("Total de predicciones realizadas", total)
#                 else:
#                     st.error(f"Error {r.status_code}: {r.json().get('error', 'desconocido')}")
#             except requests.exceptions.Timeout:
#                 st.warning("⏳ Timeout. Espera 30 s e inténtalo de nuevo.")
#             except Exception as e:
#                 st.error(f"Error: {e}")
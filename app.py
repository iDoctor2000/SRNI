import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. CONFIGURACIÓN ESTRATÉGICA
# ==========================================
st.set_page_config(
    page_title="SRNI.app - Rezoagli '25",
    page_icon="🫁",
    layout="centered", # 'Centered' se ve mejor en móviles verticales
    initial_sidebar_state="collapsed"
)

# CSS Hack para mejorar la experiencia táctil en móviles
st.markdown("""
    <style>
    /* Fondo más limpio */
    .stApp { background-color: #f8fafc; }
    
    /* Botones más grandes para dedos */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5rem;
        font-weight: 700;
        font-size: 1.2rem;
        background-color: #2563eb;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }

    /* Métricas grandes */
    div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; }
    div[data-testid="stMetricLabel"] { font-size: 1rem; color: #64748b; }

    /* Inputs más legibles */
    label { font-size: 1rem !important; font-weight: 600 !important; color: #334155 !important; }
    
    /* Expander estilo tarjeta */
    .streamlit-expanderContent { background-color: white; border-radius: 0 0 10px 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTIÓN DE SEGURIDAD (API KEY)
# ==========================================
def get_api_key():
    """Busca la API Key en Secrets, Entorno o Input manual."""
    # 1. Streamlit Secrets (Nube)
    if 'GOOGLE_API_KEY' in st.secrets:
        return st.secrets['GOOGLE_API_KEY']
    # 2. Variables de Entorno (Local/Docker)
    if "GOOGLE_API_KEY" in os.environ:
        return os.environ["GOOGLE_API_KEY"]
    if "API_KEY" in os.environ:
        return os.environ["API_KEY"]
    return None

# Sidebar Logica
with st.sidebar:
    st.header("Configuración")
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ Sin Licencia Activa")
        user_key = st.text_input("Introduce tu Google API Key:", type="password")
        if user_key:
            api_key = user_key
            os.environ["GOOGLE_API_KEY"] = user_key # Set temporal
    else:
        st.success("✅ Licencia Activada")
    
    st.divider()
    st.info("SRNI.app v2.3\nBasado en Rezoagli et al. (2025)")

# ==========================================
# 3. INTERFAZ DE USUARIO (MOBILE FIRST)
# ==========================================

# Header
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.write("🫁")
with col_title:
    st.markdown("<h2 style='margin:0; padding:0; color:#1e3a8a;'>SRNI.app</h2>", unsafe_allow_html=True)
    st.caption("Decisión Clínica en Soporte Respiratorio")

st.markdown("---")

# --- BLOQUE A: Evaluación Clínica ---
st.markdown("### 1. Paciente")
patologia = st.selectbox(
    "Sospecha Clínica (Etiología)",
    [
        "Fallo Hipoxémico de Novo (Neumonía/SDRA)",
        "Edema Agudo de Pulmón (Cardiogénico)",
        "EPOC Agudizado / Hipercapnia",
        "Inmunocomprometido",
        "Traumatismo Torácico",
        "Otro / No filiado"
    ]
)

# Fila 1: Signos Vitales (Inputs numéricos grandes)
c1, c2 = st.columns(2)
with c1:
    rr = st.number_input("Frec. Resp (rpm)", min_value=8, max_value=60, value=24, step=1)
with c2:
    spo2 = st.number_input("SpO2 (%)", min_value=50, max_value=100, value=90, step=1)

# Fila 2: Sliders para ajustes rápidos
st.markdown("---")
fio2 = st.slider("FiO2 Suministrada (%)", 21, 100, 50, help="Desliza para ajustar la fracción inspirada de oxígeno")
glasgow = st.slider("Escala de Glasgow", 3, 15, 15, help="Nivel de conciencia")

# --- BLOQUE B: Gasometría (Opcional) ---
with st.expander("🩸 Gasometría Arterial (Toca para abrir)", expanded=False):
    g1, g2, g3 = st.columns(3)
    ph = g1.number_input("pH", 6.80, 7.80, 7.35, step=0.01)
    pco2 = g2.number_input("pCO2", 10, 150, 45)
    po2 = g3.number_input("pO2", 30, 300, 80)

# ==========================================
# 4. MOTOR DE CÁLCULO
# ==========================================
try:
    rox_index = (spo2 / (fio2/100)) / rr
except ZeroDivisionError:
    rox_index = 0.0

try:
    pafi_ratio = po2 / (fio2/100)
except ZeroDivisionError:
    pafi_ratio = 0.0

# Visualización de Índices (Tarjetas)
st.markdown("### 2. Monitorización")
m1, m2 = st.columns(2)

# Lógica de colores ROX
rox_delta_color = "normal" # Verde por defecto
rox_msg = "Estable"
if rox_index < 2.85:
    rox_delta_color = "inverse" # Rojo
    rox_msg = "RIESGO ALTO (<2.85)"
elif rox_index < 4.88:
    rox_delta_color = "off" # Gris/Amarillo
    rox_msg = "Riesgo Mod (<4.88)"

m1.metric("Índice ROX", f"{rox_index:.2f}", delta=rox_msg, delta_color=rox_delta_color)

# Lógica de colores PaFi
pafi_color = "normal"
pafi_msg = "Leve/Normal"
if pafi_ratio < 150:
    pafi_color = "inverse"
    pafi_msg = "Hipoxemia Severa"
elif pafi_ratio < 300:
    pafi_color = "off"
    pafi_msg = "Moderada"

m2.metric("PaO2/FiO2", f"{pafi_ratio:.0f}", delta=pafi_msg, delta_color=pafi_color)

# ==========================================
# 5. INTELIGENCIA ARTIFICIAL
# ==========================================
st.markdown("---")

# Prompt del Sistema (Instrucciones estrictas)
SYSTEM_PROMPT = """
ERES UN EXPERTO CLÍNICO EN SOPORTE RESPIRATORIO NO INVASIVO.
BASE BIBLIOGRÁFICA: Rezoagli et al. (2025) "A clinical guide to non-invasive respiratory support".

TU OBJETIVO: Dar una recomendación clara, breve y segura para un médico a pie de cama.

REGLAS DE DECISIÓN:
1. Fallo Hipoxémico de Novo (Neumonía/SDRA) -> 1ª Elección: HFNT (Alto Flujo).
2. Fallo Cardiogénico (EAP) -> 1ª Elección: CPAP o NIV.
3. Fallo Hipercápnico (EPOC/Asma) -> 1ª Elección: NIV (BiPAP).

FORMATO DE RESPUESTA:
### 🚑 Recomendación
(Indica la Interfaz exacta y por qué).

### ⚙️ Ajustes Iniciales
(Lista con viñetas los valores exactos de Flujo, Presión, FiO2, etc).

### ⚠️ Alertas
(Menciona riesgo de P-SILI y criterios de intubación si ROX < 4.88).

SE MUY CONCISO. NO TE ENROLLES.
"""

if st.button("🧠 ANALIZAR CASO AHORA"):
    if not api_key:
        st.error("⛔ ERROR: Falta la API Key. Configúrala en la barra lateral.")
    else:
        with st.spinner("Consultando guías clínicas..."):
            try:
                # Configurar cliente
                genai.configure(api_key=api_key)
                
                # Construir el caso clínico
                user_case = f"""
                CASO CLÍNICO:
                - Sospecha: {patologia}
                - Constantes: FR {rr}, SpO2 {spo2}%, FiO2 {fio2}%
                - Neuro: Glasgow {glasgow}
                - Gases: pH {ph}, pCO2 {pco2}, PaO2 {po2}
                - Índices calculados: ROX {rox_index:.2f}, PaFi {pafi_ratio:.0f}
                """
                
                # Llamada al modelo (Gemini 3 Pro para razonamiento complejo)
                model = genai.GenerativeModel(
                    model_name='gemini-3-pro-preview',
                    system_instruction=SYSTEM_PROMPT
                )
                
                response = model.generate_content(user_case)
                
                # Mostrar resultado
                st.success("Análisis Completado")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")
                st.caption("Verifique su conexión a internet y que la API Key sea válida.")

# Footer
st.markdown("<br><br><div style='text-align: center; color: #cbd5e1; font-size: 0.8rem;'>SRNI.app - Herramienta de ayuda. No sustituye el juicio clínico.</div>", unsafe_allow_html=True)



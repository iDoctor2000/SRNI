import streamlit as st
import google.generativeai as genai
import os
from google.api_core import exceptions

# ==========================================
# 1. CONFIGURACIÓN ESTRATÉGICA
# ==========================================
st.set_page_config(
    page_title="SRNI.app",
    page_icon="🫁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS AVANZADO: COMPACTACIÓN MÁXIMA
st.markdown("""
    <style>
    /* 1. Reducir padding general de la app */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* 2. Compactar espacios entre elementos */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: -0.5rem !important;
        gap: 0.5rem !important;
    }
    
    /* 3. Estilo de Botones */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        background-color: #2563eb;
        color: white;
        margin-top: 10px;
    }
    
    /* 4. Métricas más compactas */
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    
    /* 5. Inputs compactos */
    .stNumberInput input { height: 2rem; text-align: center !important; }
    
    /* 6. Header personalizado compacto */
    .header-box {
        background-color: white;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-bottom: 2px solid #f1f5f9;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTIÓN DE SEGURIDAD (API KEY)
# ==========================================
def get_api_key():
    if 'GOOGLE_API_KEY' in st.secrets: return st.secrets['GOOGLE_API_KEY']
    if "GOOGLE_API_KEY" in os.environ: return os.environ["GOOGLE_API_KEY"]
    if "API_KEY" in os.environ: return os.environ["API_KEY"]
    return None

with st.sidebar:
    st.header("Configuración")
    api_key = get_api_key()
    if not api_key:
        user_key = st.text_input("API Key:", type="password")
        if user_key: os.environ["GOOGLE_API_KEY"] = user_key
    st.info("SRNI.app v2.6 Compact\nRezoagli et al. (2025)")

# ==========================================
# 3. INTERFAZ COMPACTA (HEADER)
# ==========================================

# Cabecera Flexible que no se corta
st.markdown("""
<div class="header-box">
    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="font-size: 2.2rem; line-height: 1;">🫁</span>
        <div style="min-width: 150px;">
            <h2 style="margin: 0; color: #1e3a8a; font-size: 1.5rem; line-height: 1.1;">SRNI.app</h2>
            <div style="color: #64748b; font-size: 0.8rem; font-weight: 600;">By iDoctor</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. DATOS CLÍNICOS (CONTENEDOR ÚNICO)
# ==========================================

with st.container(border=True):
    # Selector de Patología
    patologia = st.selectbox(
        "Sospecha Clínica",
        [
            "Fallo Hipoxémico de Novo",
            "Edema Agudo Pulmón (EAP)",
            "EPOC / Hipercapnia",
            "Inmunocomprometido",
            "Traumatismo Torácico",
            "Otro"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---") 

    # GRID DE 3 COLUMNAS PARA NÚMEROS (Ahorra mucho espacio)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Frec. Resp") 
        rr = st.number_input("RR", 8, 60, 24, label_visibility="collapsed")
    with c2:
        st.caption("SpO2 (%)")
        spo2 = st.number_input("SpO2", 50, 100, 90, label_visibility="collapsed")
    with c3:
        st.caption("Glasgow")
        glasgow = st.number_input("GCS", 3, 15, 15, label_visibility="collapsed")

    # FiO2 Slider (Fila completa para precisión)
    st.write("") # Espaciador
    c_fio_label, c_fio_val = st.columns([3,1])
    with c_fio_label: st.caption("FiO2 Suministrada")
    with c_fio_val: st.markdown(f"**{st.session_state.get('fio2_val', 50)}%**")
    
    fio2 = st.slider("FiO2", 21, 100, 50, key="fio2_val", label_visibility="collapsed")

    # Gasometría (Grid de 3 columnas dentro del expander)
    with st.expander("🧪 Gasometría (Opcional)", expanded=False):
        g1, g2, g3 = st.columns(3)
        with g1:
            st.caption("pH")
            ph = st.number_input("pH", 6.80, 7.80, 7.35, step=0.01, label_visibility="collapsed")
        with g2:
            st.caption("pCO2")
            pco2 = st.number_input("pCO2", 10, 150, 45, label_visibility="collapsed")
        with g3:
            st.caption("pO2")
            po2 = st.number_input("pO2", 30, 300, 80, label_visibility="collapsed")

# ==========================================
# 5. CÁLCULOS Y RESULTADOS
# ==========================================
try:
    rox_index = (spo2 / (fio2/100)) / rr
    pafi_ratio = po2 / (fio2/100)
except:
    rox_index = 0.0
    pafi_ratio = 0.0

st.caption("Monitorización en tiempo real")
r1, r2 = st.columns(2)

# Colores ROX
rox_color = "normal"
if rox_index < 2.85: rox_color = "inverse"
elif rox_index < 4.88: rox_color = "off"

r1.metric("ROX", f"{rox_index:.2f}", delta_color=rox_color)

# Colores PaFi
pafi_color = "normal"
if pafi_ratio < 150: pafi_color = "inverse"
elif pafi_ratio < 300: pafi_color = "off"

r2.metric("PaFi", f"{pafi_ratio:.0f}", delta_color=pafi_color)

# ==========================================
# 6. IA / BOTÓN DE ACCIÓN
# ==========================================
SYSTEM_PROMPT = """
ACTÚA COMO EXPERTO CLÍNICO (Ref: Rezoagli 2025).
1. Fallo Hipoxémico -> HFNT.
2. EAP -> CPAP/NIV.
3. EPOC -> NIV.
Salida breve: 1. Recomendación, 2. Ajustes, 3. Alertas.
"""

if st.button("🧠 OBTENER RECOMENDACIÓN"):
    if not api_key:
        st.error("⚠️ Falta API Key. Configúrala en el menú lateral.")
    else:
        with st.spinner("Analizando caso con Gemini 3..."):
            try:
                genai.configure(api_key=api_key)
                user_case = f"Pat:{patologia}, FR:{rr}, SpO2:{spo2}, FiO2:{fio2}, GCS:{glasgow}, ROX:{rox_index:.2f}"
                model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=SYSTEM_PROMPT)
                response = model.generate_content(user_case)
                st.info("Recomendación Clínica:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")

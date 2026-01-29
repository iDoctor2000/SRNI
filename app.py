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
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem !important; }
    
    /* 5. Inputs compactos */
    .stNumberInput input { height: 2rem; }
    
    /* 6. Header personalizado compacto */
    .header-box {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 15px;
        text-align: left;
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
    st.info("SRNI.app v2.5 Compact\nRezoagli et al. (2025)")

# ==========================================
# 3. INTERFAZ COMPACTA (HEADER)
# ==========================================

# Usamos HTML directo para control total del espaciado del título
st.markdown("""
<div class="header-box">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 2.5rem;">🫁</span>
        <div style="line-height: 1.1;">
            <h2 style="margin: 0; color: #1e3a8a; font-size: 1.6rem;">SRNI.app</h2>
            <div style="color: #64748b; font-size: 0.8rem; font-weight: 600;">By iDoctor</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. DATOS CLÍNICOS (CONTENEDOR ÚNICO)
# ==========================================

# Agrupamos TODO en un solo contenedor con borde para ahorrar espacio visual
with st.container(border=True):
    # Selector de Patología (Full width)
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
        label_visibility="collapsed", # Ahorra espacio ocultando label (se entiende por contexto)
        placeholder="Selecciona Patología..."
    )

    st.markdown("---") # Separador sutil interno

    # Fila 1: Vitales (Columnas)
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Frec. Resp (rpm)") # Caption ocupa menos que Label
        rr = st.number_input("RR", 8, 60, 24, label_visibility="collapsed")
    with c2:
        st.caption("SpO2 (%)")
        spo2 = st.number_input("SpO2", 50, 100, 90, label_visibility="collapsed")

    # Fila 2: Ajustes (Columnas) - Antes ocupaban mucho espacio vertical
    c3, c4 = st.columns(2)
    with c3:
        st.caption(f"FiO2: {st.session_state.get('fio2_val', 50)}%")
        fio2 = st.slider("FiO2", 21, 100, 50, key="fio2_val", label_visibility="collapsed")
    with c4:
        st.caption(f"Glasgow: {st.session_state.get('gcs_val', 15)}")
        glasgow = st.slider("Glasgow", 3, 15, 15, key="gcs_val", label_visibility="collapsed")

    # Gasometría (Acordeón compacto)
    with st.expander("🧪 Gasometría (Opcional)", expanded=False):
        g1, g2, g3 = st.columns(3)
        ph = g1.number_input("pH", 6.80, 7.80, 7.35, step=0.01)
        pco2 = g2.number_input("pCO2", 10, 150, 45)
        po2 = g3.number_input("pO2", 30, 300, 80)

# ==========================================
# 5. CÁLCULOS Y RESULTADOS
# ==========================================
try:
    rox_index = (spo2 / (fio2/100)) / rr
    pafi_ratio = po2 / (fio2/100)
except:
    rox_index = 0.0
    pafi_ratio = 0.0

# Resultados visuales (Compactos)
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

if st.button("🧠 ANALIZAR CASO"):
    if not api_key:
        st.error("Falta API Key")
    else:
        with st.spinner("Analizando..."):
            try:
                genai.configure(api_key=api_key)
                user_case = f"Pat:{patologia}, FR:{rr}, SpO2:{spo2}, FiO2:{fio2}, GCS:{glasgow}, ROX:{rox_index:.2f}"
                model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=SYSTEM_PROMPT)
                response = model.generate_content(user_case)
                st.success("Recomendación:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error: {str(e)}")

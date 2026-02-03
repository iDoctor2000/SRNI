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

# CSS AVANZADO: COMPACTACIÓN Y ESTILOS DE INFO
st.markdown("""
    <style>
    /* Ajuste del contenedor principal para evitar corte superior */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: -0.5rem !important;
        gap: 0.5rem !important;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 700;
        background-color: #2563eb;
        color: white;
        margin-top: 15px;
    }
    
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    
    .stNumberInput input { height: 2rem; text-align: center !important; }
    
    /* Panel de Referencia Rápida */
    .ref-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .ref-title {
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 10px;
        text-transform: uppercase;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .param-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 8px;
        margin-top: 5px;
    }
    .param-item {
        background: white;
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid #f1f5f9;
        font-size: 0.8rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .param-label {
        font-weight: 700;
        color: #64748b;
        display: block;
        font-size: 0.7rem;
        text-transform: uppercase;
    }
    .param-value {
        color: #1e293b;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .safety-alert {
        margin-top: 12px;
        padding-top: 8px;
        border-top: 1px dashed #cbd5e1;
        font-size: 0.8rem;
        color: #b91c1c;
    }
    
    /* ESTILOS HEADER PERSONALIZADOS */
    .header-title {
        color: #1e3a8a;
        font-weight: 800;
        font-size: 2.2rem !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        display: flex;
        align-items: center; /* Alineación vertical centrada */
        height: 100%;
        padding-top: 10px !important;
    }
    
    .header-subtitle-inline {
        font-family: "Source Sans Pro", sans-serif;
        font-style: italic;
        font-size: 1rem !important; 
        color: #64748b;
        font-weight: 400;
        margin-left: 10px;
        padding-top: 8px; /* Pequeño ajuste visual para alinear con la base del texto grande */
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA DE REFERENCIA CLÍNICA (ESTRUCTURADA)
# ==========================================
REFERENCIAS = {
    "Fallo Hipoxémico de Novo": {
        "terapia": "Alto Flujo (HFNT)",
        "ipap": "N/A",
        "epap": "PEEP 5-10*",
        "ps": "N/A",
        "fio2": "92-96% SpO2",
        "vt": "Monit. P-SILI",
        "seguridad": "Si ROX < 4.88 (2-6h) considerar intubación inmediata. Riesgo de fatiga silente."
    },
    "Edema Agudo Pulmón (EAP)": {
        "terapia": "CPAP / BiPAP",
        "ipap": "12-16 cmH2O",
        "epap": "8-12 cmH2O",
        "ps": "4-8 cmH2O",
        "fio2": ">90% SpO2",
        "vt": "6-8 ml/kg",
        "seguridad": "Respuesta rápida esperada. Vigilar estabilidad hemodinámica y precarga."
    },
    "EPOC / Hipercapnia": {
        "terapia": "VNI (BiPAP)",
        "ipap": "10-14 cmH2O",
        "epap": "4-6 cmH2O",
        "ps": "6-10 cmH2O",
        "fio2": "88-92% SpO2",
        "vt": "6-8 ml/kg",
        "seguridad": "Objetivo: pH > 7.35. Evitar alcalosis respiratoria por sobre-asistencia."
    },
    "Inmunocomprometido": {
        "terapia": "HFNT + VNI interm.",
        "ipap": "12-15 cmH2O",
        "epap": "5-8 cmH2O",
        "ps": "7-10 cmH2O",
        "fio2": "Conservadora",
        "vt": "< 8 ml/kg",
        "seguridad": "Evitar intubación si es posible (alto riesgo infeccioso), pero no retrasar si falla."
    },
    "Traumatismo Torácico": {
        "terapia": "VNI / CPAP",
        "ipap": "12-14 cmH2O",
        "epap": "5-10 cmH2O",
        "ps": "6-8 cmH2O",
        "fio2": "Titular SpO2",
        "vt": "7-9 ml/kg",
        "seguridad": "Control de dolor fundamental. Descartar neumotórax antes de aplicar presión positiva."
    },
    "Otro": {
        "terapia": "Individualizar",
        "ipap": "10-12 cmH2O",
        "epap": "5 cmH2O",
        "ps": "5-7 cmH2O",
        "fio2": "50% inicial",
        "vt": "6 ml/kg",
        "seguridad": "Monitorización estrecha de la mecánica pulmonar y esfuerzo inspiratorio."
    }
}

# ==========================================
# 3. GESTIÓN DE API KEY
# ==========================================
def get_api_key():
    if 'GOOGLE_API_KEY' in st.secrets: return st.secrets['GOOGLE_API_KEY']
    if "GOOGLE_API_KEY" in os.environ: return os.environ["GOOGLE_API_KEY"]
    if "API_KEY" in os.environ: return os.environ["API_KEY"]
    return None

api_key = get_api_key()

# ==========================================
# 4. INTERFAZ (HEADER)
# ==========================================

# Ajustamos las columnas para reducir el tamaño del logo (ratio 1.2 a 8.8)
c_logo, c_text = st.columns([1.2, 8.8])

with c_logo:
    try:
        # Logo responsive
        st.image("IMG/SRNI.png", use_container_width=True)
    except Exception:
        st.error("Logo?")

with c_text:
    # Título alineado con el subtítulo "By iDoctor" en la misma línea
    st.markdown('<h1 class="header-title">Asistente SRNI <span class="header-subtitle-inline">By iDoctor</span></h1>', unsafe_allow_html=True)

# ==========================================
# 5. PANEL CENTRAL
# ==========================================

with st.container(border=True):
    patologia = st.selectbox(
        "Sospecha Clínica",
        list(REFERENCIAS.keys()),
        index=None,
        placeholder="Enfermedad Representativa...",
        label_visibility="collapsed"
    )

    # --- CUADRO DE RESUMEN DINÁMICO ---
    # Solo mostramos el panel de referencia si se ha seleccionado una patología
    if patologia:
        ref = REFERENCIAS[patologia]
        st.markdown(f"""
        <div class="ref-box">
            <div class="ref-title">📋 Configuración Inicial: {ref['terapia']}</div>
            <div class="param-grid">
                <div class="param-item">
                    <span class="param-label">IPAP</span>
                    <span class="param-value">{ref['ipap']}</span>
                </div>
                <div class="param-item">
                    <span class="param-label">EPAP / PEEP</span>
                    <span class="param-value">{ref['epap']}</span>
                </div>
                <div class="param-item">
                    <span class="param-label">P. Soporte</span>
                    <span class="param-value">{ref['ps']}</span>
                </div>
                <div class="param-item">
                    <span class="param-label">FiO2</span>
                    <span class="param-value">{ref['fio2']}</span>
                </div>
                <div class="param-item">
                    <span class="param-label">Vol. Corriente</span>
                    <span class="param-value">{ref['vt']}</span>
                </div>
            </div>
            <div class="safety-alert">
                🚨 <b>Aspectos de Seguridad:</b> {ref['seguridad']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 Seleccione una enfermedad representativa para ver la referencia clínica.")

    st.markdown("---") 

    # GRID DE 3 COLUMNAS PARA VITALES
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

    # FiO2 Slider
    st.write("") 
    c_fio_label, c_fio_val = st.columns([3,1])
    with c_fio_label: st.caption("FiO2 Programada Actual")
    with c_fio_val: st.markdown(f"**{st.session_state.get('fio2_val', 50)}%**")
    fio2 = st.slider("FiO2", 21, 100, 50, key="fio2_val", label_visibility="collapsed")

    with st.expander("🧪 Gasometría (Opcional)", expanded=False):
        g1, g2, g3 = st.columns(3)
        ph = g1.number_input("pH", 6.80, 7.80, 7.35, step=0.01)
        pco2 = g2.number_input("pCO2", 10, 150, 45)
        po2 = g3.number_input("pO2", 30, 300, 80)

# ==========================================
# 6. CÁLCULOS Y RESULTADOS
# ==========================================
rox_index = (spo2 / (fio2/100)) / rr if rr > 0 else 0
pafi_ratio = po2 / (fio2/100) if fio2 > 0 else 0

st.caption("Monitorización en tiempo real")
r1, r2 = st.columns(2)

rox_color = "normal"
if rox_index < 2.85: rox_color = "inverse"
elif rox_index < 4.88: rox_color = "off"
r1.metric("ROX Index", f"{rox_index:.2f}", delta_color=rox_color)

pafi_color = "normal"
if pafi_ratio < 150: pafi_color = "inverse"
elif pafi_ratio < 300: pafi_color = "off"
r2.metric("PaFi Ratio", f"{pafi_ratio:.0f}", delta_color=pafi_color)

# ==========================================
# 7. IA / BOTÓN DE ACCIÓN
# ==========================================
if st.button("🧠 OBTENER RECOMENDACIÓN IA PERSONALIZADA"):
    if not api_key:
        st.error("⚠️ API Key no detectada. Verifique configuración.")
    elif not patologia:
        st.warning("⚠️ Por favor, seleccione una Enfermedad Representativa antes de consultar a la IA.")
    else:
        with st.spinner("Gemini analizando el contexto clínico..."):
            try:
                genai.configure(api_key=api_key)
                prompt = f"""ERES EXPERTO CLÍNICO (Ref: Rezoagli 2025). 
                Caso: {patologia}, FR {rr}, SpO2 {spo2}, FiO2 {fio2}, Glasgow {glasgow}, ROX {rox_index:.2f}.
                Responde con:
                1. Interfaz específica recomendada.
                2. Parámetros de configuración inicial precisos (IPAP, EPAP, PS, FiO2, Flujo).
                3. Signos de alarma para fracaso de terapia y criterios de IOT.
                Se muy directo y usa formato Markdown."""
                model = genai.GenerativeModel('gemini-3-flash-preview')
                response = model.generate_content(prompt)
                st.success("Recomendación de la IA:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error en la consulta: {str(e)}")

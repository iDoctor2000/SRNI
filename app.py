import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SRNI.app - Rezoagli 2025",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; text-align: center; }
    h1 { color: #1e293b; }
    h2, h3 { color: #334155; }
    </style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL: API KEY Y INFO ---
with st.sidebar:
    st.title("🫁 SRNI.app")
    st.caption("Motor de Decisión Clínica v2.0")
    st.caption("Basado en: *Rezoagli et al., Critical Care (2025)*")
    
    st.divider()
    
    # Intenta obtener la API KEY de los secretos de Streamlit o del input manual
    api_key = st.text_input("Google API Key", type="password", help="Introduce tu clave de Google Gemini")
    
    # Si la clave está en los secretos (para producción), úsala
    if not api_key and 'GOOGLE_API_KEY' in st.secrets:
        api_key = st.secrets['GOOGLE_API_KEY']
        st.success("API Key detectada en Secrets ✅")

    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    st.info("⚠️ **Aviso de Seguridad**: Herramienta de soporte. El juicio clínico prevalece.")

# --- LÓGICA CLÍNICA (REZOAGLI PROMPT) ---
REZOAGLI_PROMPT = """
ERES EL MOTOR DE DECISIÓN CLÍNICA DE "SRNI.app".
TU FUENTE DE VERDAD ÚNICA: Rezoagli et al., 2025 ("A clinical guide to non-invasive respiratory support in acute respiratory failure").

REGLAS DE DECISIÓN (Jerarquía Estricta):

1. ETIOLOGÍA Y SELECCIÓN DE INTERFAZ/MODO:
   - **Fallo Hipoxémico de Novo (AHRF)**: 
     - 1ª LÍNEA: HFNT (Alto Flujo). Iniciar a 40-60 L/min.
     - COVID-19: Se puede considerar CPAP para evitar intubación, preferiblemente Helmet.
     - Advertencia P-SILI: Si no mejora, no retrasar intubación.
   - **Edema Agudo de Pulmón (CPE)**: 
     - 1ª LÍNEA: CPAP o BiPAP.
     - CPAP PEEP: 5-8 cmH2O (máscara), 8-12 cmH2O (helmet).
     - HFNT: Solo si intolerancia a VNI o para descansos.
   - **EPOC / Hipercapnia (AECOPD)**: 
     - 1ª LÍNEA: BiPAP con Mascarilla Facial (Oro-nasal o Full-face).
     - AJUSTES BiPAP: PEEP 5-8 cmH2O, PS 7-15 cmH2O (ajustar para VT 10-15 mL/kg).
     - Helmet NO recomendado rutinariamente para EPOC por riesgo de re-inhalación de CO2 y asincronías.

2. PARÁMETROS DE INICIO (TABLA 2 REZOAGLI 2025):
   - HFNT: Flujo 40-60 L/min, Temp 31-37°C.
   - CPAP Máscara: 5-8 cmH2O.
   - CPAP Helmet: 8-12 cmH2O (requiere >30 L/min flujo fresco).
   - BiPAP Máscara: PEEP 5-8, PS 7-10 inicial.

3. MONITORIZACIÓN:
   - Hipoxemia (HFNT/CPAP): Índice ROX (< 4.88 riesgo, < 3 alto riesgo).
   - Hipercapnia (BiPAP): Escala HACOR (>5 fallo).
   - Signos de P-SILI: Esfuerzo inspiratorio excesivo, VT > 9-9.5 mL/kg.

TU FORMATO DE SALIDA (MARKDOWN LIMPIO):
Genera un informe clínico estructurado:
### 1. Evaluación Rápida
(Interpretación de PaFi, ROX, pH y Gravedad).
### 2. Estrategia Recomendada
(Modalidad e Interfaz exacta según Rezoagli 2025. Sé directivo: "Usar HFNT" o "Usar BiPAP").
### 3. Parámetros de "Arranque"
(Valores numéricos precisos para configurar el ventilador/dispositivo).
### 4. Seguridad y Monitorización
(Alertas P-SILI, Criterios de Fracaso y qué vigilar en la próxima hora).
"""

# --- INTERFAZ PRINCIPAL ---
st.header("Soporte Respiratorio No Invasivo")
st.markdown("Protocolo basado en evidencia para Urgencias y UCI.")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Datos del Paciente")
    
    patologia = st.selectbox(
        "Sospecha Clínica (Etiología)",
        [
            "Fallo Hipoxémico de Novo (Neumonía/SDRA)",
            "Edema Agudo de Pulmón (Cardiogénico)",
            "EPOC Agudizado / Hipercapnia",
            "Crisis Asmática",
            "Traumatismo Torácico"
        ]
    )
    
    c1, c2 = st.columns(2)
    with c1:
        rr = st.number_input("Frecuencia (rpm)", 10, 60, 24)
        spo2 = st.number_input("SpO2 (%)", 50, 100, 92)
    with c2:
        fio2 = st.number_input("FiO2 (%)", 21, 100, 50)
        glasgow = st.number_input("Glasgow", 3, 15, 15)

    with st.expander("Gasometría (Opcional)", expanded=True):
        gc1, gc2, gc3 = st.columns(3)
        ph = gc1.number_input("pH", 6.8, 7.8, 7.35, step=0.01)
        pco2 = gc2.number_input("pCO2", 10, 150, 40)
        po2 = gc3.number_input("pO2", 30, 300, 80)

    # Cálculo de Índices en Python (Más preciso que la IA)
    try:
        rox = (spo2 / (fio2/100)) / rr
    except: rox = 0
    
    try:
        pafi = po2 / (fio2/100)
    except: pafi = 0

with col2:
    st.subheader("🧮 Índices Calculados")
    
    ic1, ic2 = st.columns(2)
    
    # Tarjeta ROX
    rox_color = "off"
    rox_msg = "Datos insuficientes"
    if rox > 0:
        if rox >= 4.88:
            rox_color = "normal"
            rox_msg = "Bajo Riesgo (>4.88)"
        elif rox >= 3:
            rox_color = "warning"
            rox_msg = "Riesgo Moderado (3-4.88)"
        else:
            rox_color = "inverse"
            rox_msg = "ALTO RIESGO (<3)"
            
    ic1.metric("Índice ROX", f"{rox:.2f}", rox_msg, delta_color=rox_color)
    
    # Tarjeta PaFi
    pafi_color = "off"
    pafi_msg = ""
    if pafi > 0:
        if pafi < 150:
            pafi_color = "inverse"
            pafi_msg = "Hipoxemia Severa"
        elif pafi < 300:
            pafi_color = "warning"
            pafi_msg = "Hipoxemia Mod/Leve"
        else:
            pafi_color = "normal"
            pafi_msg = "Normal"
            
    ic2.metric("PaO2/FiO2", f"{pafi:.0f}", pafi_msg, delta_color=pafi_color)

    st.divider()

    # Botón de Análisis
    analyze = st.button("ANALIZAR CASO (Dr. Gemini)", type="primary", use_container_width=True)
    
    if analyze:
        if not api_key:
            st.error("❌ Necesitas configurar la API Key en la barra lateral (o en Secrets).")
        else:
            with st.spinner("Consultando Guías Rezoagli 2025..."):
                try:
                    # Preparar Contexto
                    contexto_paciente = f"""
                    DATOS:
                    - Etiología: {patologia}
                    - Mecánica: FR {rr}, SpO2 {spo2}%, FiO2 {fio2}%
                    - Gasometría: pH {ph}, pCO2 {pco2}, pO2 {po2}
                    - Neuro: GCS {glasgow}
                    - ÍNDICES REALES: ROX {rox:.2f}, PaFi {pafi:.0f}
                    """
                    
                    # Llamada al Modelo
                    model = genai.GenerativeModel('gemini-1.5-pro-latest') # Usamos Pro para mejor razonamiento clínico
                    response = model.generate_content(REZOAGLI_PROMPT + "\n" + contexto_paciente)
                    
                    # Mostrar Resultado
                    st.markdown("---")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error de conexión: {str(e)}")

# --- FOOTER ---
st.markdown("---")
st.caption("SRNI.app v2.0 | Codificado para Streamlit")

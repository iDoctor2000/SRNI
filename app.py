import streamlit as st
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Ventila AI - iDoctor", page_icon="🫁", layout="wide")

# Título y contexto
st.title("🫁 Ventila AI: Asistente de Soporte Respiratorio")
st.markdown("""
**Herramienta de apoyo a la decisión clínica en Urgencias.**
Basada en las guías 'Ventila' y el 'Compendio de Ventilación Mecánica'.
*Advertencia: Esta herramienta es una ayuda y no sustituye el juicio clínico.*
""")

# --- BARRA LATERAL: Configuración ---
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Introduce tu Google API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    st.info("Desarrollado por iDoctor desde Murcia.")

# --- COLUMNA IZQUIERDA: Datos del Paciente ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Datos Clínicos")
    patologia = st.selectbox("Sospecha Clínica", 
                             ["Edema Agudo de Pulmón (EAP)", 
                              "EPOC Agudizado", 
                              "Neumonía / Hipoxemia de Novo", 
                              "Asma / Crisis Asmática",
                              "Traumatismo Torácico"])
    
    fr = st.number_input("Frecuencia Respiratoria (rpm)", min_value=0, max_value=60, value=20)
    spo2 = st.number_input("Saturación de Oxígeno (%)", min_value=50, max_value=100, value=92)
    fio2 = st.slider("FiO2 suministrada (%)", 21, 100, 21)
    
    st.subheader("2. Gasometría (Si disponible)")
    ph = st.number_input("pH", min_value=6.8, max_value=7.7, value=7.35, step=0.01)
    pco2 = st.number_input("pCO2 (mmHg)", value=45)
    po2 = st.number_input("pO2 (mmHg)", value=80)
    glasgow = st.slider("Escala de Glasgow", 3, 15, 15)

# --- CÁLCULOS AUTOMÁTICOS (Python puro) ---
# Índice de ROX = (SpO2 / FiO2) / FR
rox_index = 0
try:
    rox_index = (spo2 / (fio2/100)) / fr
except:
    rox_index = 0

# PaO2/FiO2 (Kirby)
pafi = 0
try:
    pafi = po2 / (fio2/100)
except:
    pafi = 0

# --- LÓGICA DE VISUALIZACIÓN ---
with col2:
    st.subheader("3. Monitorización e Índices")
    
    # Visualización ROX
    st.metric("Índice de ROX", f"{rox_index:.2f}")
    if rox_index < 3: # Criterio de riesgo 
        st.error("⚠️ ROX < 3: Alto riesgo de fracaso. Valorar Intubación.")
    elif rox_index < 4.88:
        st.warning("⚠️ ROX 3 - 4.88: Monitorización estrecha.")
    else:
        st.success("✅ ROX > 4.88: Probable éxito de TAF/VMNI.")

    # Visualización PaFi
    st.metric("PaO2/FiO2", f"{pafi:.0f}")
    if pafi < 150: # Criterio de gravedad [cite: 86]
        st.error("Grave (<150). Valorar VMI si no mejora rápido.")
    elif pafi < 250:
        st.warning("Moderado. Indicación clara de soporte.")
    
    # Botón para pedir consejo a la IA
    analyze_btn = st.button("Analizar Caso con IA (Gemini)", type="primary")

# --- LÓGICA DE IA (Gemini) ---
if analyze_btn and api_key:
    with st.spinner('El Dr. Gemini está pensando...'):
        try:
            # DEFINICIÓN DEL MODELO Y SYSTEM PROMPT (Basado en tus libros)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            system_prompt = f"""
            Actúa como un experto en Ventilación Mecánica No Invasiva.
            Analiza el siguiente paciente basándote ESTRICTAMENTE en la evidencia de los libros 'Ventila' y 'Compendio de VM'.
            
            DATOS PACIENTE:
            - Patología: {patologia}
            - FR: {fr} rpm (Normal <24, Fallo >30)
            - pH: {ph} (Grave < 7.25)
            - Glasgow: {glasgow}
            - PaO2/FiO2: {pafi}
            - Índice ROX: {rox_index}

            TU TAREA:
            1. **Escala de Gravedad:** Clasifica la IRA (Hipoxémica vs Hipercápnica) según Berlín y pH[cite: 83, 94].
            2. **Elección de Terapia:** Recomienda el escalón terapéutico (Alto Flujo, CPAP, BiLevel) según la patología.
               - Si es EAP: Prioriza CPAP o BiLevel[cite: 437].
               - Si es EPOC: Prioriza BiLevel (S/T)[cite: 462].
            3. **Parámetros de Inicio (Fase de Arranque):** Dame los valores exactos de IPAP, EPAP o Flujo para empezar y evitar el rechazo ('Efecto bofetada').
            4. **Criterios de Fracaso:** Indica qué vigilar en la próxima hora (HACOR, ROX, etc.)[cite: 362].
            
            Sé conciso, usa viñetas y habla en español profesional médico.
            """
            
            response = model.generate_content(system_prompt)
            st.markdown("### 🤖 Recomendación Clínica")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Error al conectar con Gemini: {e}")
elif analyze_btn and not api_key:
    st.warning("Por favor, introduce tu API Key en la barra lateral.")

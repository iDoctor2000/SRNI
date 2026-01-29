import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SRNI.app - Guía Clínica",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 2.2rem; }
    .reportview-container .main .block-container { max-width: 1000px; padding-top: 2rem; }
    h1 { color: #1e3a8a; }
    h2 { color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
    h3 { color: #334155; margin-top: 1rem; }
    .info-box { background-color: #e0f2fe; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #0284c7; color: #0c4a6e; }
    .warning-box { background-color: #fef3c7; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #d97706; color: #78350f; }
    .critical-box { background-color: #fee2e2; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #dc2626; color: #7f1d1d; }
    </style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=50)
    st.title("SRNI.app")
    st.caption("v2.1 | Rezoagli et al. 2025")
    
    st.divider()
    
    api_key = st.text_input("Google API Key", type="password", help="Introduce tu clave de Google Gemini")
    
    # Soporte para Secrets de Streamlit Cloud
    if not api_key and 'GOOGLE_API_KEY' in st.secrets:
        api_key = st.secrets['GOOGLE_API_KEY']
        st.success("Licencia Activada ✅")

    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    st.info("Esta App distingue fenotipos (Hipoxémico vs Hipercápnico) para indicar la interfaz correcta.")

# --- LÓGICA CLÍNICA (PROMPT) ---
REZOAGLI_PROMPT = """
ACTÚA COMO UN CONSULTOR EXPERTO EN VENTILACIÓN NO INVASIVA.
FUENTE: Rezoagli et al., "A clinical guide to non-invasive respiratory support in acute respiratory failure" (2025).

TAREA: Analiza el caso y recomienda estrategia ventilatoria.

1. CLASIFICACIÓN DEL FALLO:
   - ¿Es Hipoxémico de Novo (Neumonía/SDRA)? -> 1ª Elección: HFNT (Alto Flujo).
   - ¿Es Cardiogénico (EAP)? -> 1ª Elección: CPAP/NIV.
   - ¿Es Hipercápnico (EPOC/Asma)? -> 1ª Elección: NIV (BiPAP).

2. CONFIGURACIÓN INICIAL (Prescripción precisa):
   - HFNT: Flujo 40-60 L/min, T 34-37ºC.
   - CPAP: 5-10 cmH2O.
   - NIV (BiPAP): IPAP inicial para VT 6-8ml/kg, EPAP 5-8.

3. RIESGOS:
   - Calcular y mencionar Riesgo de P-SILI si hay alto drive respiratorio.
   - Definir criterio de INTUBACIÓN para este paciente específico.

SALIDA EN MARKDOWN ESTRUCTURADO. SE BREVE Y DIRECTO.
"""

# --- ESTRUCTURA DE PESTAÑAS ---
tab_calc, tab_book = st.tabs(["🧮 Calculadora & IA", "📖 Libro de Bolsillo (Rezoagli '25)"])

# ==========================================
# PESTAÑA 1: CALCULADORA E IA
# ==========================================
with tab_calc:
    st.header("Motor de Decisión Clínica")
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Evaluación")
        patologia = st.selectbox(
            "Sospecha Clínica (Fenotipo)",
            [
                "Fallo Hipoxémico de Novo (Neumonía/SDRA)",
                "Edema Agudo de Pulmón (Cardiogénico)",
                "EPOC Agudizado / Hipercapnia",
                "Inmunocomprometido",
                "Traumatismo Torácico"
            ]
        )
        
        c1, c2 = st.columns(2)
        with c1:
            rr = st.number_input("Frecuencia (rpm)", 10, 60, 24)
            spo2 = st.number_input("SpO2 (%)", 50, 100, 90)
        with c2:
            fio2 = st.number_input("FiO2 (%)", 21, 100, 50)
            glasgow = st.number_input("Glasgow", 3, 15, 15)

        with st.expander("➕ Gasometría (Opcional)"):
            gc1, gc2, gc3 = st.columns(3)
            ph = gc1.number_input("pH", 6.8, 7.8, 7.35, step=0.01)
            pco2 = gc2.number_input("pCO2", 10, 150, 45)
            po2 = gc3.number_input("pO2", 30, 300, 80)

        # Cálculos seguros en Python
        try:
            rox = (spo2 / (fio2/100)) / rr
        except: rox = 0
        
        try:
            pafi = po2 / (fio2/100)
        except: pafi = 0

    with col2:
        st.subheader("2. Monitorización")
        
        # Lógica de Color Corregida para evitar StreamlitAPIException
        # Streamlit solo acepta "normal", "inverse", "off" para delta_color
        
        # Tarjeta ROX
        rox_delta_color = "off"
        rox_text = "Monitorizar"
        
        if rox > 0:
            if rox >= 4.88:
                rox_delta_color = "normal" # Verde
                rox_text = "Bajo Riesgo (>4.88)"
            elif rox < 3:
                rox_delta_color = "inverse" # Rojo (Inverse porque bajo es malo)
                rox_text = "ALTO RIESGO (<3)"
            else:
                rox_delta_color = "off" # Gris (Zona gris 3-4.88)
                rox_text = "Zona Gris (3-4.88)"

        st.metric(
            label="Índice ROX",
            value=f"{rox:.2f}",
            delta=rox_text,
            delta_color=rox_delta_color 
        )
        
        # Tarjeta PaFi
        pafi_delta_color = "off"
        pafi_text = ""
        
        if pafi > 0:
            if pafi < 150:
                pafi_delta_color = "inverse" # Rojo
                pafi_text = "Hipoxemia Severa"
            elif pafi < 300:
                pafi_delta_color = "off" # Gris
                pafi_text = "Hipoxemia Moderada"
            else:
                pafi_delta_color = "normal" # Verde
                pafi_text = "Normal"

        st.metric(
            label="PaO2/FiO2",
            value=f"{pafi:.0f}",
            delta=pafi_text,
            delta_color=pafi_delta_color
        )

        st.divider()

        analyze = st.button("🧠 ANALIZAR CASO CON IA", type="primary")
        
        if analyze:
            if not api_key:
                st.warning("⚠️ Introduce tu API Key en la barra lateral")
            else:
                with st.spinner("El Dr. Gemini está pensando..."):
                    try:
                        contexto = f"""
                        PACIENTE: {patologia}
                        MECÁNICA: FR {rr}, SpO2 {spo2}, FiO2 {fio2}
                        GASES: pH {ph}, pCO2 {pco2}, pO2 {po2}
                        NEURO: GCS {glasgow}
                        CALCULADOS: ROX {rox:.2f}, PaFi {pafi:.0f}
                        """
                        model = genai.GenerativeModel('gemini-1.5-pro-latest')
                        response = model.generate_content(REZOAGLI_PROMPT + contexto)
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# PESTAÑA 2: LIBRO DE BOLSILLO
# ==========================================
with tab_book:
    st.markdown("## 📖 Guía de Bolsillo: Soporte Respiratorio")
    st.caption("Resumen práctico basado en *Rezoagli et al. Critical Care (2025)*")

    with st.expander("📌 CAPÍTULO 1: Algoritmo de Elección (Etiología)", expanded=True):
        st.markdown("""
        La decisión **NO** se basa solo en la hipoxemia, sino en la **CAUSA**:

        | Etiología | 1ª Línea | 2ª Línea | Justificación |
        | :--- | :--- | :--- | :--- |
        | **Fallo Hipoxémico de Novo**<br>(Neumonía, SDRA) | **HFNT (Alto Flujo)** | CPAP / Helmet | HFNT es más confortable y reduce daño pulmonar (P-SILI) comparado con NIV estándar. |
        | **Edema Agudo Pulmón**<br>(Cardiogénico) | **CPAP / NIV** | HFNT | La presión positiva (PEEP) reduce la postcarga del ventrículo izquierdo. |
        | **EPOC / Asma**<br>(Hipercapnia) | **NIV (BiPAP)** | HFNT | Se necesita soporte inspiratorio (IPAP) para barrer CO2 y descargar músculos. |
        | **Inmunocomprometido** | **HFNT** | NIV | HFNT reduce necesidad de intubación mejor que la oxigenoterapia estándar. |
        """)
        st.info("💡 **Perla Clínica:** En neumonía/SDRA, evita la BiPAP con mascarilla facial si es posible, ya que aumenta volúmenes corrientes y riesgo de lesión autoinfligida (P-SILI).")

    with st.expander("🎛️ CAPÍTULO 2: Parámetros de Inicio (Setting)"):
        st.markdown("""
        ### 1. Cánula Nasal de Alto Flujo (HFNT)
        *   **Flujo:** Iniciar agresivo a **40-60 L/min** para lavar espacio muerto.
        *   **Temperatura:** 37ºC (bajar a 34ºC si disconfort).
        *   **FiO2:** Titular para SpO2 92-96%.

        ### 2. CPAP (Presión Positiva Continua)
        *   **Interfaz:** Mascarilla Facial o Helmet.
        *   **Presión:** Iniciar en **5-8 cmH2O**. En Helmet subir a 10-12 cmH2O.
        *   **Objetivo:** Reclutamiento alveolar en EAP.

        ### 3. VNI / BiPAP (Doble Nivel)
        *   **Modo:** S/T (Spontaneous/Timed).
        *   **EPAP (PEEP):** 5-8 cmH2O (Mantiene vía aérea abierta).
        *   **IPAP (Presión Soporte):** Iniciar con PS de **8-10 cmH2O** sobre la EPAP.
        *   *Ejemplo de orden:* "BiPAP 12/5" (IPAP 12, EPAP 5).
        """)

    with st.expander("🔍 CAPÍTULO 3: Monitorización y Fracaso"):
        st.markdown("""
        ### Índice ROX (Para HFNT)
        $$ROX = (SpO_2 / FiO_2) / FR$$
        *   Medir a las **2, 6 y 12 horas**.
        *   ✅ **> 4.88:** Bajo riesgo de intubación. Continuar terapia.
        *   ⚠️ **3.85 - 4.87:** Zona gris. Reevaluar en 1 hora.
        *   ❌ **< 3.85:** Alto riesgo de fracaso. **CONSIDERAR INTUBACIÓN**.

        ### Signos de P-SILI (Lesión Autoinfligida)
        Si el paciente "pelea" con el aire, se daña el pulmón:
        1.  Uso intenso de músculos accesorios (esternocleidomastoideo).
        2.  Volúmenes tidal excesivos (> 9.5 ml/kg) en VNI.
        3.  Grandes oscilaciones de presión esofágica (si se mide).
        
        **Acción:** Si persiste alto drive respiratorio a pesar de optimizar HFNT/VNI -> **INTUBAR** para proteger el pulmón.
        """)

    with st.expander("🚪 CAPÍTULO 4: Destete (Liberación)"):
        st.markdown("""
        **¿Cuándo retirar el soporte?**
        1.  Estabilidad clínica (FR < 25-30).
        2.  SpO2 > 90-92% con FiO2 < 40-50%.
        3.  Ausencia de tiraje intercostal.

        **Estrategia:**
        *   **HFNT:** Bajar primero FiO2 (<40%). Luego bajar flujo de 10 en 10 L/min.
        *   **NIV:** Hacer pruebas de ventilación espontánea o intercalar con HFNT.
        """)

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748b;'>SRNI.app © 2025 | Diseñado para iDoctor</div>", unsafe_allow_html=True)

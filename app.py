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
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
    h1 { color: #1e3a8a; }
    h2 { color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
    h3 { color: #334155; margin-top: 1rem; }
    /* Estilos para las tarjetas de información del libro */
    .stExpander { border: 1px solid #e2e8f0; border-radius: 8px; background: white; }
    </style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (GESTIÓN DE SECRETOS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=50)
    st.title("SRNI.app")
    st.caption("v2.3 | Rezoagli et al. 2025")
    
    st.divider()
    
    # Lógica de seguridad para API Key
    api_key = None
    
    if 'GOOGLE_API_KEY' in st.secrets:
        # CASO A: La clave está en el archivo seguro secrets.toml
        api_key = st.secrets['GOOGLE_API_KEY']
        st.success("🔑 Licencia Activada (Secrets)")
        st.caption("Clave cargada de forma segura.")
    else:
        # CASO B: Solicitud manual (Menos seguro, pero funcional)
        api_key = st.text_input("Google API Key", type="password", help="Pega tu clave AIza... aquí")
        if not api_key:
            st.warning("⚠️ Se requiere API Key")
            st.markdown("[Obtener Clave Gratis](https://aistudio.google.com/app/apikey)")

    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    st.info("Esta App distingue fenotipos (Hipoxémico vs Hipercápnico) para indicar la interfaz correcta.")
    st.markdown("---")
    st.caption("Diseñado para uso clínico a pie de cama.")

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

# --- ESTRUCTURA DE PESTAÑAS (Tabbed Interface) ---
tab_calc, tab_book = st.tabs(["🧮 Calculadora & IA", "📖 Libro de Bolsillo (Rezoagli '25)"])

# ==========================================
# PESTAÑA 1: CALCULADORA E IA
# ==========================================
with tab_calc:
    st.header("Motor de Decisión Clínica")
    
    col1, col2 = st.columns([1, 1.1])

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
        
        # --- LÓGICA DE COLOR CORREGIDA ---
        cc1, cc2 = st.columns(2)
        
        # Tarjeta ROX
        rox_delta_color = "off"
        rox_text = "Monitorizar"
        
        if rox > 0:
            if rox >= 4.88:
                rox_delta_color = "normal" # Verde
                rox_text = "Bajo Riesgo (>4.88)"
            elif rox < 3:
                rox_delta_color = "inverse" # Rojo
                rox_text = "ALTO RIESGO (<3)"
            else:
                rox_delta_color = "off" # Gris
                rox_text = "Zona Gris (3-4.88)"

        with cc1:
            st.metric(
                label="Índice ROX",
                value=f"{rox:.2f}",
                delta=rox_text,
                delta_color=rox_delta_color 
            )
        
        # Tarjeta PaFi
        pafi_delta_color = "off"
        pafi_text = "Monitorizar"
        
        if pafi > 0:
            if pafi < 150:
                pafi_delta_color = "inverse" # Rojo
                pafi_text = "Hipoxemia Severa"
            elif pafi > 300:
                pafi_delta_color = "normal" # Verde
                pafi_text = "Normal"
            else:
                pafi_delta_color = "off" # Gris
                pafi_text = "Hipoxemia Mod/Leve"

        with cc2:
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
                st.error("❌ FALTA API KEY: Configura .streamlit/secrets.toml o introdúcela en la barra lateral.")
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
                        st.markdown("### 🤖 Recomendación Clínica")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Error de conexión con Gemini: {e}")

# ==========================================
# PESTAÑA 2: LIBRO DE BOLSILLO
# ==========================================
with tab_book:
    st.header("📖 Protocolo Rezoagli et al. (2025)")
    st.markdown("Guía rápida para la selección y manejo de soporte respiratorio no invasivo.")

    with st.expander("📌 CAPÍTULO 1: Selección de Interfaz (Etiología)", expanded=True):
        st.markdown("""
        **Regla de Oro:** No tratar solo la hipoxemia, tratar la fisiopatología.

        | Escenario Clínico | Fisiopatología | 1ª Línea Recomendada |
        | :--- | :--- | :--- |
        | **Neumonía / SDRA** | Fallo Hipoxémico de Novo | **HFNT (Alto Flujo)** |
        | **Edema Agudo Pulmón** | Fallo Cardiogénico (CPAP recluta) | **CPAP o NIV** |
        | **EPOC / Asma** | Fallo Hipercápnico (Fatiga Muscular) | **NIV (BiPAP)** |
        | **Inmunocomprometido** | Hipoxemia | **HFNT** (Menos intubación) |
        """)
        st.info("💡 **COVID-19:** Se puede intentar CPAP/Helmet para evitar intubación, pero vigilar P-SILI.")

    with st.expander("🎛️ CAPÍTULO 2: Parámetros de Arranque (Setting)"):
        c_set1, c_set2 = st.columns(2)
        with c_set1:
            st.markdown("### 1. HFNT (Alto Flujo)")
            st.markdown("""
            *   **Flujo:** 40-60 L/min (Empezar alto).
            *   **Temp:** 37ºC (34ºC si disconfort).
            *   **FiO2:** Para SpO2 92-96%.
            """)
            st.markdown("### 2. CPAP")
            st.markdown("""
            *   **Máscara:** 5-8 cmH2O.
            *   **Helmet:** 8-12 cmH2O (Requiere flujo alto).
            """)
        
        with c_set2:
            st.markdown("### 3. VNI (BiPAP)")
            st.markdown("""
            *   **Modo:** S/T (Spont/Timed).
            *   **EPAP (PEEP):** 5-8 cmH2O.
            *   **IPAP (Presión Soporte):** Ajustar para VT 6-8 ml/kg.
            *   *Inicio típico:* PS 8-10 sobre PEEP.
            """)

    with st.expander("⚠️ CAPÍTULO 3: Criterios de Fracaso y P-SILI"):
        st.error("""
        **¡ALERTA P-SILI (Lesión Pulmonar Autoinfligida)!**
        Si el paciente mantiene un esfuerzo inspiratorio vigoroso (tiraje) a pesar del soporte, está dañando sus propios pulmones. **NO RETRASAR INTUBACIÓN.**
        """)
        st.markdown("""
        **Índice ROX (HFNT):**
        *   Medir a las 2, 6 y 12 horas.
        *   **ROX < 3.85:** Alto riesgo de fracaso -> Valorar IOT.
        *   **ROX > 4.88:** Éxito probable.
        
        **Escala HACOR (VNI en EPOC):**
        *   Evaluar FC, pH, Glasgow, PaO2/FiO2 y FR.
        *   > 5 puntos a la hora = Fracaso probable.
        """)

# --- FOOTER ---
st.markdown("---")
st.caption("SRNI.app - Herramienta de soporte a la decisión clínica. Verificar siempre con juicio médico.")

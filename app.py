import streamlit as st
import google.generativeai as genai
import os
import time
import base64
import streamlit.components.v1 as components
from google.api_core import exceptions

# ==========================================
# 1. CONFIGURACIÓN ESTRATÉGICA
# ==========================================
st.set_page_config(
    page_title="SRNI",
    page_icon="🫁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 1.1 CONFIGURACIÓN PWA (Mobile Icon Fix)
# ==========================================
def setup_pwa(icon_path):
    """
    Inyecta metadatos para que la app se vea bien al guardarla
    en el escritorio de iOS/Android (Icono y Nombre).
    Usa Base64 para evitar problemas de rutas de archivos.
    """
    try:
        # 1. Leer imagen y convertir a Base64
        with open(icon_path, "rb") as f:
            icon_data = f.read()
        icon_b64 = base64.b64encode(icon_data).decode()
        icon_data_uri = f"data:image/png;base64,{icon_b64}"
        
        # 2. Crear manifiesto dinámico
        manifest_json = f"""
        {{
            "name": "SRNI",
            "short_name": "SRNI",
            "start_url": ".",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#2563eb",
            "icons": [
                {{
                    "src": "{icon_data_uri}",
                    "sizes": "192x192",
                    "type": "image/png"
                }}
            ]
        }}
        """
        manifest_b64 = base64.b64encode(manifest_json.encode()).decode()
        manifest_data_uri = f"data:application/manifest+json;base64,{manifest_b64}"
        
        # 3. Script JS para inyectar etiquetas en el <head>
        pwa_script = f"""
        <script>
            (function() {{
                const head = document.head;
                
                // Función auxiliar para crear/actualizar links
                function setLink(rel, href) {{
                    let link = document.querySelector(`link[rel="${{rel}}"]`);
                    if (!link) {{
                        link = document.createElement('link');
                        link.rel = rel;
                        head.appendChild(link);
                    }}
                    link.href = href;
                }}
                
                // Función auxiliar para meta tags
                function setMeta(name, content) {{
                    let meta = document.querySelector(`meta[name="${{name}}"]`);
                    if (!meta) {{
                        meta = document.createElement('meta');
                        meta.name = name;
                        head.appendChild(meta);
                    }}
                    meta.content = content;
                }}

                // --- IOS / APPLE ---
                // Icono (El que sale en la pantalla de inicio)
                setLink('apple-touch-icon', '{icon_data_uri}');
                
                // Nombre de la App debajo del icono
                setMeta('apple-mobile-web-app-title', 'SRNI');
                
                // Modo pantalla completa
                setMeta('apple-mobile-web-app-capable', 'yes');
                setMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');

                // --- ANDROID / CHROME ---
                // Manifiesto
                setLink('manifest', '{manifest_data_uri}');
            }})();
        </script>
        """
        st.markdown(pwa_script, unsafe_allow_html=True)
        
    except Exception as e:
        # Si falla (ej. no encuentra la imagen), no rompe la app
        print(f"PWA Setup Error: {e}")

# Ejecutar configuración PWA (Intenta leer la imagen local)
setup_pwa("IMG/SRNI.png")

# ==========================================
# 2. CSS AVANZADO Y ESTILOS
# ==========================================
st.markdown("""
    <style>
    /* Ajuste del contenedor principal */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Espaciado entre elementos */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.8rem !important;
    }
    
    /* ESTILO DE LA CAJA PRINCIPAL (CONTENEDOR) */
    /* Apuntamos al contenedor con borde */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #fff7ed !important; /* Naranja muy pálido */
        border: 1px solid #fed7aa !important; /* Borde naranja suave */
        border-radius: 12px !important;
        padding: 20px !important;
        margin-top: 25px !important; /* Separación del título */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Botones */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 700;
        background-color: #2563eb;
        color: white;
        margin-top: 10px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
    
    /* Inputs numéricos */
    .stNumberInput input { height: 2rem; text-align: center !important; }
    
    /* Panel de Referencia Rápida */
    .ref-box {
        background-color: #ffffff;
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
        background: #f8fafc;
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid #f1f5f9;
        font-size: 0.8rem;
        text-align: center;
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
        font-size: 0.9rem;
    }
    .safety-alert {
        margin-top: 12px;
        padding-top: 8px;
        border-top: 1px dashed #cbd5e1;
        font-size: 0.8rem;
        color: #b91c1c;
    }
    
    /* Header Styles */
    .header-title {
        color: #1e3a8a;
        font-weight: 800;
        font-size: 2.2rem !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        display: flex;
        align-items: center;
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
        padding-top: 8px;
    }
    
    /* Estilos para el Cronómetro */
    .timer-container {
        font-family: 'Courier New', monospace;
        background: #1e293b;
        color: #22c55e;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        border: 2px solid #475569;
        margin-bottom: 10px;
        letter-spacing: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNCIONES AUXILIARES (GRÁFICOS)
# ==========================================

def render_gauge(value, title, min_val, max_val, thresholds, labels, inverse=False):
    """
    Genera una barra de progreso visual HTML/CSS (Gauge lineal)
    thresholds: [limite_bajo, limite_alto]
    """
    # Normalizar valor para el ancho (0-100%)
    range_span = max_val - min_val
    pct_value = ((value - min_val) / range_span) * 100
    pct_value = max(0, min(100, pct_value)) # Clampar entre 0 y 100
    
    # Calcular anchos de segmentos
    # Asumimos estructura: Rojo | Gris | Verde (o invertido)
    t1 = thresholds[0]
    t2 = thresholds[1]
    
    pct_t1 = ((t1 - min_val) / range_span) * 100
    pct_t2 = ((t2 - min_val) / range_span) * 100
    
    width_seg1 = pct_t1
    width_seg2 = pct_t2 - pct_t1
    width_seg3 = 100 - pct_t2
    
    # Colores
    c_danger = "#ef4444" # Rojo
    c_warn = "#f59e0b"   # Naranja/Amarillo oscuro
    c_safe = "#22c55e"   # Verde
    
    if inverse: # Para HACOR: Bajo es bueno (Verde), Medio (Naranja), Alto es malo (Rojo)
        col1, col2, col3 = c_safe, c_warn, c_danger
    else: # ROX y PAFI: Bajo es malo (Rojo), Medio es alerta (Naranja), Alto es bueno (Verde)
        col1, col2, col3 = c_danger, c_warn, c_safe

    # Posición del marcador
    marker_left = pct_value
    
    # IMPORTANTE: No indentar el HTML dentro de la f-string
    html = f"""
<div style="margin-bottom: 15px;">
    <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-weight:700; font-size:0.9rem; color:#334155;">
        <span>{title}: <span style="font-size:1.1rem; color:#1e3a8a;">{value:.0f}</span></span>
    </div>
    <div style="position: relative; height: 24px; background: #e2e8f0; border-radius: 12px; overflow: hidden; display: flex; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
        <div style="width: {width_seg1}%; background: {col1};" title="{labels[0]}"></div>
        <div style="width: {width_seg2}%; background: {col2};" title="{labels[1]}"></div>
        <div style="width: {width_seg3}%; background: {col3};" title="{labels[2]}"></div>
        <div style="position: absolute; left: calc({marker_left}% - 2px); top: 0; bottom: 0; width: 4px; background: #000; border: 1px solid white; z-index: 10;"></div>
        <div style="position: absolute; left: calc({marker_left}% - 12px); top: -2px; font-size: 18px; line-height:1; color: black; z-index: 11; text-shadow: 0 0 2px white;">⬇</div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:#64748b; margin-top:2px;">
        <span style="width:{width_seg1}%; text-align:center;">{labels[0]}</span>
        <span style="width:{width_seg2}%; text-align:center;">{labels[1]}</span>
        <span style="width:{width_seg3}%; text-align:center;">{labels[2]}</span>
    </div>
</div>
"""
    return html

def calculate_hacor(ph, pafi, rr, hr, gcs):
    score = 0
    # pH
    if ph >= 7.35: score += 0
    elif 7.30 <= ph < 7.35: score += 2
    elif 7.25 <= ph < 7.30: score += 3
    else: score += 4 # < 7.25

    # PaFi (PaO2/FiO2)
    if pafi > 200: score += 0
    elif 176 <= pafi <= 200: score += 2
    elif 151 <= pafi <= 175: score += 3
    elif 126 <= pafi <= 150: score += 4
    elif 101 <= pafi <= 125: score += 5
    else: score += 6 # <= 100

    # RR (Frecuencia Respiratoria)
    if rr <= 30: score += 0
    elif 31 <= rr <= 35: score += 2
    elif 36 <= rr <= 40: score += 3
    elif 41 <= rr <= 45: score += 4
    else: score += 5 # > 45

    # HR (Frecuencia Cardiaca)
    if hr <= 120: score += 0
    else: score += 1

    # GCS (Glasgow)
    if gcs >= 15: score += 0
    elif 13 <= gcs <= 14: score += 2
    elif 11 <= gcs <= 12: score += 5
    else: score += 10 # <= 10

    return score

# ==========================================
# 4. LÓGICA DE REFERENCIA
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

def get_api_key():
    if 'GOOGLE_API_KEY' in st.secrets: return st.secrets['GOOGLE_API_KEY']
    if "GOOGLE_API_KEY" in os.environ: return os.environ["GOOGLE_API_KEY"]
    if "API_KEY" in os.environ: return os.environ["API_KEY"]
    return None

api_key = get_api_key()

# ==========================================
# 5. HEADER
# ==========================================
c_logo, c_text = st.columns([1.2, 8.8])
with c_logo:
    try:
        st.image("IMG/SRNI.png", use_container_width=True)
    except Exception:
        st.error("Logo?")
with c_text:
    st.markdown('<h1 class="header-title">Asistente SRNI <span class="header-subtitle-inline">By iDoctor</span></h1>', unsafe_allow_html=True)

# ==========================================
# 6. PANEL CENTRAL
# ==========================================
with st.container(border=True):
    # --- CRONÓMETRO ---
    st.markdown("### ⏱️ Tiempo de Terapia")
    
    # Control del estado del cronómetro en Python
    if 'timer_active' not in st.session_state:
        st.session_state.timer_active = False
    if 'start_time_ts' not in st.session_state:
        st.session_state.start_time_ts = 0.0

    col_timer_disp, col_timer_btn = st.columns([3, 1])

    with col_timer_btn:
        if st.button("⏯️ Iniciar / Pausar", key="toggle_timer"):
            if not st.session_state.timer_active:
                st.session_state.timer_active = True
                # Si es 0, empezamos de nuevo, si no, continuamos (lógica simple para este ejemplo)
                if st.session_state.start_time_ts == 0:
                    st.session_state.start_time_ts = time.time()
                else:
                    # Ajuste para pausar/reanudar requeriría más lógica, 
                    # para simplificar "Iniciar" resetea al momento actual si estaba parado
                    st.session_state.start_time_ts = time.time()
            else:
                st.session_state.timer_active = False
                st.session_state.start_time_ts = 0 # Reset al parar

    with col_timer_disp:
        # Javascript para el contador en cliente (sin re-run de Streamlit)
        if st.session_state.timer_active:
            # Pasamos el timestamp de inicio a JS
            start_ts_js = st.session_state.start_time_ts * 1000 
            components.html(
                f"""
                <div id="clock" style="font-family: 'Courier New', monospace; background: #1e293b; color: #22c55e; padding: 10px; border-radius: 8px; text-align: center; font-size: 24px; font-weight: bold; border: 2px solid #475569; letter-spacing: 2px;">
                    00:00:00
                </div>
                <script>
                    var start = {start_ts_js};
                    function update() {{
                        var now = new Date().getTime();
                        var distance = now - start;
                        
                        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                        
                        hours = hours < 10 ? "0" + hours : hours;
                        minutes = minutes < 10 ? "0" + minutes : minutes;
                        seconds = seconds < 10 ? "0" + seconds : seconds;
                        
                        document.getElementById("clock").innerHTML = hours + ":" + minutes + ":" + seconds;
                    }}
                    setInterval(update, 1000);
                    update();
                </script>
                """,
                height=60
            )
        else:
             st.markdown('<div class="timer-container">00:00:00</div>', unsafe_allow_html=True)

    st.markdown("---")

    patologia = st.selectbox(
        "Sospecha Clínica",
        list(REFERENCIAS.keys()),
        index=None,
        placeholder="Enfermedad Representativa...",
        label_visibility="collapsed"
    )

    if patologia:
        ref = REFERENCIAS[patologia]
        st.markdown(f"""
        <div class="ref-box">
            <div class="ref-title">📋 Configuración: {ref['terapia']}</div>
            <div class="param-grid">
                <div class="param-item"><span class="param-label">IPAP</span><br><span class="param-value">{ref['ipap']}</span></div>
                <div class="param-item"><span class="param-label">EPAP</span><br><span class="param-value">{ref['epap']}</span></div>
                <div class="param-item"><span class="param-label">PS</span><br><span class="param-value">{ref['ps']}</span></div>
                <div class="param-item"><span class="param-label">FiO2</span><br><span class="param-value">{ref['fio2']}</span></div>
                <div class="param-item"><span class="param-label">VT</span><br><span class="param-value">{ref['vt']}</span></div>
            </div>
            <div class="safety-alert">🚨 {ref['seguridad']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 Seleccione enfermedad para ver referencia.")

    st.markdown("#### Monitorización") 

    # Layout de 4 columnas para incluir FC
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("F. Card (lpm)")
        hr = st.number_input("FC", 30, 250, 90, label_visibility="collapsed")
    with c2:
        st.caption("F. Resp (rpm)") 
        rr = st.number_input("RR", 8, 60, 24, label_visibility="collapsed")
    with c3:
        st.caption("SpO2 (%)")
        spo2 = st.number_input("SpO2", 50, 100, 90, label_visibility="collapsed")
    with c4:
        st.caption("Glasgow")
        glasgow = st.number_input("GCS", 3, 15, 15, label_visibility="collapsed")

    c_fio_label, c_fio_val = st.columns([3,1])
    with c_fio_label: st.caption("FiO2 Programada (%)")
    with c_fio_val: st.markdown(f"**{st.session_state.get('fio2_val', 50)}%**")
    fio2 = st.slider("FiO2", 21, 100, 50, key="fio2_val", label_visibility="collapsed")

    with st.expander("🧪 Gasometría (Requerido para HACOR)", expanded=False):
        g1, g2, g3 = st.columns(3)
        ph = g1.number_input("pH", 6.80, 7.80, 7.35, step=0.01)
        pco2 = g2.number_input("pCO2", 10, 150, 45)
        po2 = g3.number_input("pO2", 30, 300, 80)

# ==========================================
# 7. RESULTADOS GRÁFICOS
# ==========================================
# Cálculos
rox_index = (spo2 / (fio2/100)) / rr if rr > 0 else 0
pafi_ratio = po2 / (fio2/100) if fio2 > 0 else 0
hacor_score = calculate_hacor(ph, pafi_ratio, rr, hr, glasgow)

st.write("")
st.markdown("### 📊 Índices de Seguridad")

# Renderizar Gráfico ROX
html_rox = render_gauge(
    value=rox_index,
    title="Índice ROX",
    min_val=0,
    max_val=12,
    thresholds=[2.85, 4.88],
    labels=["Alto Riesgo (<2.85)", "Vigilancia (2.85-4.88)", "Bajo Riesgo (>4.88)"],
    inverse=False
)
st.markdown(html_rox, unsafe_allow_html=True)

# Renderizar Gráfico HACOR
# Puntos de corte: <= 5 éxito, > 5 fallo.
# Usamos thresholds [5, 10] para mostrar gradiente
html_hacor = render_gauge(
    value=hacor_score,
    title="Índice HACOR (1h VNI)",
    min_val=0,
    max_val=25,
    thresholds=[5, 10], 
    labels=["Éxito (≤5)", "Riesgo (>5)", "Fallo (>10)"],
    inverse=True # Inverso: Bajo es bueno, Alto es malo
)
st.markdown(html_hacor, unsafe_allow_html=True)

# Renderizar Gráfico PaFi
html_pafi = render_gauge(
    value=pafi_ratio,
    title="PaFi Ratio",
    min_val=0,
    max_val=500,
    thresholds=[150, 300],
    labels=["Severo (<150)", "Leve/Mod (150-300)", "Normal (>300)"],
    inverse=False
)
st.markdown(html_pafi, unsafe_allow_html=True)

# ==========================================
# 8. IA BOTÓN
# ==========================================
st.write("")
if st.button("🧠 OBTENER RECOMENDACIÓN IA PERSONALIZADA"):
    if not api_key:
        st.error("⚠️ API Key no detectada.")
    elif not patologia:
        st.warning("⚠️ Seleccione una patología primero.")
    else:
        with st.spinner("Analizando..."):
            try:
                genai.configure(api_key=api_key)
                prompt = f"""ERES EXPERTO CLÍNICO. Contexto: {patologia}, FR {rr}, FC {hr}, SpO2 {spo2}, FiO2 {fio2}, GCS {glasgow}, pH {ph}, pO2 {po2}.
                Índices Calculados: ROX {rox_index:.2f}, PaFi {pafi_ratio:.0f}, HACOR {hacor_score}.
                Dame una recomendación clínica breve.
                IMPORTANTE: Si HACOR > 5 tras 1h de VNI, alerta sobre alto riesgo de fracaso e intubación.
                Prioriza seguridad del paciente, ajustes del ventilador. Formato Markdown."""
                model = genai.GenerativeModel('gemini-3-flash-preview')
                response = model.generate_content(prompt)
                st.info("Recomendación IA:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error: {str(e)}")

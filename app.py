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
                
                function setLink(rel, href) {{
                    let link = document.querySelector(`link[rel="${{rel}}"]`);
                    if (!link) {{
                        link = document.createElement('link');
                        link.rel = rel;
                        head.appendChild(link);
                    }}
                    link.href = href;
                }}
                
                function setMeta(name, content) {{
                    let meta = document.querySelector(`meta[name="${{name}}"]`);
                    if (!meta) {{
                        meta = document.createElement('meta');
                        meta.name = name;
                        head.appendChild(meta);
                    }}
                    meta.content = content;
                }}

                setLink('apple-touch-icon', '{icon_data_uri}');
                setMeta('apple-mobile-web-app-title', 'SRNI');
                setMeta('apple-mobile-web-app-capable', 'yes');
                setMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');
                setLink('manifest', '{manifest_data_uri}');
            }})();
        </script>
        """
        st.markdown(pwa_script, unsafe_allow_html=True)
        
    except Exception as e:
        print(f"PWA Setup Error: {e}")

# Ejecutar configuración PWA
setup_pwa("IMG/SRNI.png")

# ==========================================
# 2. CSS AVANZADO Y ESTILOS (RESPONSIVE)
# ==========================================
st.markdown("""
    <style>
    /* 1. Ajuste global del contenedor (Más espacio útil) */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* 2. Header Compacto */
    h1 {
        font-size: 1.6rem !important;
        margin-bottom: 0 !important;
    }
    
    /* 3. Inputs Numéricos ULTRA COMPACTOS */
    /* Ocultar botones +/- para ganar espacio y limpieza */
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        display: none !important;
    }
    
    /* Input Box styling */
    div[data-testid="stNumberInput"] input {
        text-align: center !important;
        padding: 0px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #1e3a8a !important;
        height: 2.5rem !important; /* Altura táctil cómoda */
        border-radius: 8px !important;
    }

    /* Reducir espacio entre label y input */
    div[data-testid="stNumberInput"] {
        margin-bottom: 0px !important;
    }
    
    /* Etiquetas pequeñas y centradas */
    .compact-label {
        font-size: 0.75rem !important;
        color: #64748b;
        font-weight: 600;
        text-align: center;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* 4. Tarjeta de Referencia (Grid Responsive) */
    .ref-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .ref-title {
        font-weight: 700;
        color: #1e3a8a;
        font-size: 0.85rem;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Grid mágica: se ajusta automáticamente */
    .param-grid {
        display: grid;
        /* Minimo 70px por item permite 4 columnas en móviles modernos */
        grid-template-columns: repeat(auto-fit, minmax(75px, 1fr)); 
        gap: 6px; 
    }
    
    .param-item {
        background: white;
        padding: 4px;
        border-radius: 6px;
        border: 1px solid #cbd5e1;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .param-label {
        font-size: 0.6rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .param-value {
        font-size: 0.8rem;
        color: #0f172a;
        font-weight: 700;
        line-height: 1.1;
    }

    /* 5. Contenedor Principal (Tarjeta Blanca) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* 6. Cronómetro */
    .timer-display {
        font-family: 'Courier New', monospace;
        background: #0f172a;
        color: #4ade80;
        border-radius: 6px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 700;
        padding: 8px 0;
        letter-spacing: 1px;
    }

    /* 7. Botones */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    /* Ajustes para Sliders */
    div[data-testid="stSlider"] {
        padding-top: 0px !important;
        padding-bottom: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNCIONES AUXILIARES
# ==========================================

def render_gauge(value, title, min_val, max_val, thresholds, labels, inverse=False):
    # Lógica de Gauge simplificada para renderizado
    range_span = max_val - min_val
    pct_value = ((value - min_val) / range_span) * 100
    pct_value = max(0, min(100, pct_value))
    
    t1 = thresholds[0]
    t2 = thresholds[1]
    
    pct_t1 = ((t1 - min_val) / range_span) * 100
    pct_t2 = ((t2 - min_val) / range_span) * 100
    
    width_seg1 = pct_t1
    width_seg2 = pct_t2 - pct_t1
    width_seg3 = 100 - pct_t2
    
    c_danger, c_warn, c_safe = "#ef4444", "#f59e0b", "#22c55e"
    if inverse: col1, col2, col3 = c_safe, c_warn, c_danger
    else: col1, col2, col3 = c_danger, c_warn, c_safe

    marker_left = pct_value
    
    html = f"""
    <div style="margin-top: 10px; margin-bottom: 5px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:2px; font-weight:700; font-size:0.8rem; color:#334155;">
            <span>{title}</span>
            <span style="color:#1e3a8a;">{value:.1f}</span>
        </div>
        <div style="position: relative; height: 12px; background: #e2e8f0; border-radius: 6px; overflow: hidden; display: flex;">
            <div style="width: {width_seg1}%; background: {col1};"></div>
            <div style="width: {width_seg2}%; background: {col2};"></div>
            <div style="width: {width_seg3}%; background: {col3};"></div>
            <div style="position: absolute; left: calc({marker_left}% - 2px); top: 0; bottom: 0; width: 4px; background: #0f172a; border: 1px solid white;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.6rem; color:#94a3b8; margin-top:2px;">
            <span>{labels[0]}</span>
            <span>{labels[-1]}</span>
        </div>
    </div>
    """
    return html

def calculate_hacor(ph, pafi, rr, hr, gcs):
    score = 0
    if ph < 7.25: score += 4
    elif ph < 7.30: score += 3
    elif ph < 7.35: score += 2
    
    if pafi <= 100: score += 6
    elif pafi <= 125: score += 5
    elif pafi <= 150: score += 4
    elif pafi <= 175: score += 3
    elif pafi <= 200: score += 2
    
    if rr > 45: score += 5
    elif rr > 40: score += 4
    elif rr > 35: score += 3
    elif rr > 30: score += 2
    
    if hr > 120: score += 1
    
    if gcs <= 10: score += 10
    elif gcs <= 12: score += 5
    elif gcs <= 14: score += 2
    
    return score

# ==========================================
# 4. DATOS DE REFERENCIA
# ==========================================
REFERENCIAS = {
    "Fallo Hipoxémico": {"terapia": "Alto Flujo", "ipap": "-", "epap": "5-10", "ps": "-", "fio2": "92-96%", "vt": "P-SILI", "seguridad": "ROX < 4.88: Intubar"},
    "EAP (Edema Pulmón)": {"terapia": "CPAP/BiPAP", "ipap": "12-16", "epap": "8-12", "ps": "4-8", "fio2": ">90%", "vt": "6-8ml", "seguridad": "Vigilar shock"},
    "EPOC Agudizado": {"terapia": "BiPAP", "ipap": "10-14", "epap": "4-6", "ps": "6-10", "fio2": "88-92%", "vt": "6-8ml", "seguridad": "pH > 7.35 meta"},
    "Inmunosuprimido": {"terapia": "HFNT/VNI", "ipap": "12-15", "epap": "5-8", "ps": "7-10", "fio2": "Min", "vt": "<8ml", "seguridad": "Intubación precoz"},
    "Trauma Torácico": {"terapia": "CPAP/VNI", "ipap": "12-14", "epap": "5-10", "ps": "6-8", "fio2": "Variable", "vt": "7-9ml", "seguridad": "Analgesia clave"}
}

def get_api_key():
    if 'GOOGLE_API_KEY' in st.secrets: return st.secrets['GOOGLE_API_KEY']
    if "GOOGLE_API_KEY" in os.environ: return os.environ["GOOGLE_API_KEY"]
    if "API_KEY" in os.environ: return os.environ["API_KEY"]
    return None

api_key = get_api_key()

# ==========================================
# 5. HEADER COMPACTO
# ==========================================
c_head1, c_head2 = st.columns([1, 6])
with c_head1:
    st.image("IMG/SRNI.png", use_container_width=True)
with c_head2:
    st.markdown("### **Asistente SRNI**", unsafe_allow_html=True)
    st.caption("Soporte Respiratorio No Invasivo | iDoctor")

# ==========================================
# 6. INTERFAZ PRINCIPAL
# ==========================================

# --- CRONÓMETRO COMPACTO ---
col_t_btn, col_t_display = st.columns([1, 2], gap="small")
with col_t_btn:
    if 'timer_active' not in st.session_state: st.session_state.timer_active = False
    if 'start_time_ts' not in st.session_state: st.session_state.start_time_ts = 0.0
    
    btn_label = "⏹ Detener" if st.session_state.timer_active else "▶ Iniciar"
    type_btn = "secondary" if st.session_state.timer_active else "primary"
    
    if st.button(btn_label, type=type_btn, use_container_width=True):
        st.session_state.timer_active = not st.session_state.timer_active
        if st.session_state.timer_active: st.session_state.start_time_ts = time.time()

with col_t_display:
    if st.session_state.timer_active:
        start_ts_js = st.session_state.start_time_ts * 1000 
        components.html(
            f"""<div id="clock" style="font-family:'Courier New';background:#0f172a;color:#4ade80;border-radius:6px;text-align:center;font-size:1.2rem;font-weight:700;padding:6px 0;">00:00:00</div>
            <script>
                var start = {start_ts_js};
                setInterval(function() {{
                    var dist = new Date().getTime() - start;
                    var h = Math.floor((dist % 86400000) / 3600000);
                    var m = Math.floor((dist % 3600000) / 60000);
                    var s = Math.floor((dist % 60000) / 1000);
                    document.getElementById("clock").innerHTML = (h<10?"0"+h:h) + ":" + (m<10?"0"+m:m) + ":" + (s<10?"0"+s:s);
                }}, 1000);
            </script>""", height=40)
    else:
        st.markdown('<div class="timer-display">00:00:00</div>', unsafe_allow_html=True)

# --- SELECTOR PATOLOGÍA ---
patologia = st.selectbox("Patología", list(REFERENCIAS.keys()), index=None, placeholder="Seleccionar patología...", label_visibility="collapsed")

if patologia:
    ref = REFERENCIAS[patologia]
    st.markdown(f"""
    <div class="ref-box">
        <div class="ref-title">
            <span>{patologia}</span>
            <span style="font-size:0.7rem; color:#64748b; font-weight:400;">{ref['terapia']}</span>
        </div>
        <div class="param-grid">
            <div class="param-item"><span class="param-label">IPAP</span><span class="param-value">{ref['ipap']}</span></div>
            <div class="param-item"><span class="param-label">EPAP</span><span class="param-value">{ref['epap']}</span></div>
            <div class="param-item"><span class="param-label">PS</span><span class="param-value">{ref['ps']}</span></div>
            <div class="param-item"><span class="param-label">FiO2</span><span class="param-value">{ref['fio2']}</span></div>
            <div class="param-item"><span class="param-label">VT</span><span class="param-value">{ref['vt']}</span></div>
        </div>
        <div style="margin-top:5px; font-size:0.7rem; color:#b91c1c; font-weight:600;">⚠ {ref['seguridad']}</div>
    </div>
    """, unsafe_allow_html=True)

# --- MONITORIZACIÓN (GRID DE 4) ---
# Usamos un contenedor con borde sutil para agrupar visualmente los inputs
with st.container(border=True):
    st.caption("Monitorización (Signos Vitales)")
    
    # Fila 1: Signos Vitales
    c1, c2, c3, c4 = st.columns(4, gap="small")
    
    with c1:
        st.markdown('<div class="compact-label">FC (lpm)</div>', unsafe_allow_html=True)
        hr = st.number_input("FC", 0, 300, 90, label_visibility="collapsed")
        
    with c2:
        st.markdown('<div class="compact-label">FR (rpm)</div>', unsafe_allow_html=True)
        rr = st.number_input("RR", 0, 60, 24, label_visibility="collapsed")
        
    with c3:
        st.markdown('<div class="compact-label">SpO2 (%)</div>', unsafe_allow_html=True)
        spo2 = st.number_input("SpO2", 0, 100, 90, label_visibility="collapsed")
        
    with c4:
        st.markdown('<div class="compact-label">GCS</div>', unsafe_allow_html=True)
        glasgow = st.number_input("GCS", 3, 15, 15, label_visibility="collapsed")

    # Fila 2: FiO2 Slider (Más intuitivo que input numérico)
    st.markdown('<div class="compact-label" style="text-align:left; margin-top:8px;">FiO2 Programada: <b>'+str(st.session_state.get('fio2_val', 50))+'%</b></div>', unsafe_allow_html=True)
    fio2 = st.slider("FiO2", 21, 100, 50, key="fio2_val", label_visibility="collapsed")

    # Fila 3: Gasometría (Expandible para ahorrar espacio)
    with st.expander("Gasometría (pH, pCO2, pO2)", expanded=False):
        g1, g2, g3 = st.columns(3, gap="small")
        with g1:
            st.markdown('<div class="compact-label">pH</div>', unsafe_allow_html=True)
            ph = st.number_input("pH", 6.8, 7.8, 7.35, step=0.01, format="%.2f", label_visibility="collapsed")
        with g2:
            st.markdown('<div class="compact-label">pCO2</div>', unsafe_allow_html=True)
            pco2 = st.number_input("pCO2", 10, 150, 45, label_visibility="collapsed")
        with g3:
            st.markdown('<div class="compact-label">pO2</div>', unsafe_allow_html=True)
            po2 = st.number_input("pO2", 30, 300, 80, label_visibility="collapsed")

# ==========================================
# 7. CÁLCULOS Y VISUALIZACIÓN
# ==========================================
rox_index = (spo2 / (fio2/100)) / rr if rr > 0 else 0
pafi_ratio = po2 / (fio2/100) if fio2 > 0 else 0
hacor_score = calculate_hacor(ph, pafi_ratio, rr, hr, glasgow)

col_g1, col_g2, col_g3 = st.columns(3, gap="small")
with col_g1:
    st.markdown(render_gauge(rox_index, "ROX", 0, 12, [2.85, 4.88], ["<2.85", ">4.88"]), unsafe_allow_html=True)
with col_g2:
    st.markdown(render_gauge(hacor_score, "HACOR", 0, 15, [5, 10], ["≤5", ">10"], inverse=True), unsafe_allow_html=True)
with col_g3:
    st.markdown(render_gauge(pafi_ratio, "PAFI", 0, 400, [150, 300], ["<150", ">300"]), unsafe_allow_html=True)

# ==========================================
# 8. IA BOTÓN
# ==========================================
st.write("")
if st.button("✨ Análisis IA", type="primary", use_container_width=True):
    if not api_key:
        st.error("Falta API Key")
    else:
        with st.spinner("Consultando..."):
            try:
                genai.configure(api_key=api_key)
                prompt = f"""Actúa como Neumólogo Experto. 
                Datos: Patología: {patologia or 'No esp.'}, FR:{rr}, FC:{hr}, SpO2:{spo2}%, FiO2:{fio2}%, GCS:{glasgow}, pH:{ph}, pO2:{po2}.
                Indices: ROX:{rox_index:.2f}, PAFI:{pafi_ratio:.0f}, HACOR:{hacor_score}.
                
                Dame 3 puntos clave de actuación inmediata en formato lista bullet points muy breve y directa. 
                Si HACOR > 5 alerta de fallo VNI."""
                
                model = genai.GenerativeModel('gemini-3-flash-preview')
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e:
                st.error("Error conexión IA")

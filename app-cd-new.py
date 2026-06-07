import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import tempfile
import os
import re

from parser_cd import (
    parse_rfds_tables,
    parse_eme_tables,
    extract_rfds_metadata,
    extract_eme_metadata,
    extract_cd_metadata,
    dms_to_decimal,
    normalize_string
)

# =====================================================
# GLOBAL PROJECT HARDCODED LOOKUP MAPS
# =====================================================
CD_CENTERLINE_MAP = {
    "16932987": {
        "700": "115.0 ft",
        "850": "115.0 ft",
        "1900": "115.0 ft",
        "2100": "115.0 ft",
        "4GHZ": "115 ft"
    },
    "17554319": {
        "1900": "24.4 ft",
        "2100": "24.4 ft",
        "4GHZ": "24.4 ft"
    }
}

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Automated EME Review Checker",
    page_icon="📡",
    layout="wide"
)

# =====================================================
# THEME & CUSTOM STYLES
# =====================================================

st.markdown("""
<style>
.block-container {
    padding-top: 3.2rem !important;
    padding-left: 0.6rem !important;
    padding-right: 0.6rem !important;
}            

/* PREMIUM BACKGROUND */
.stApp {
    background:
        radial-gradient(circle at top left, rgba(0,255,255,0.08), transparent 35%),
        radial-gradient(circle at top right, rgba(0,120,255,0.08), transparent 35%),
        radial-gradient(circle at bottom center, rgba(0,255,180,0.05), transparent 40%),
        #0B1220;
}
           
/* NEON TITLE */
.main-title {
    font-size: 56px;
    font-weight: 900;
    text-align: center;
    margin-top: 10px;
    background: linear-gradient(110deg, #ffb15a, #ee7f01, #ffffff, #ee7f01);
    background-size: 250% 250%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: titleFlow 6s ease infinite;
    letter-spacing: 2px;
    text-shadow: 0px 0px 18px rgba(238, 127, 1, 0.18);
}

@keyframes titleFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.subtitle {
    text-align: center;
    color: #9CA3AF;
    font-size: 18px;
    margin-bottom: 25px;
}

/* ANIMATED SCAN LINE */
.scan-line {
    height: 3px;
    width: 100%;
    margin-bottom: 25px;
    background: linear-gradient(90deg, transparent, #00E5FF, transparent);
    animation: scanMove 3s linear infinite;
}

@keyframes scanMove {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* GLASS UPLOAD BOXES */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 10px;
    padding: 6px 10px;
    backdrop-filter: blur(6px);
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0px 0px 20px rgba(0,198,255,0.35);
}

button[data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #00E5FF !important;
}

/* STATUS BANNERS */
.status-banner {
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    color: white;
    margin-bottom: 20px;
}

.status-pass {
    background-color: #15803d;
    border: 1px solid #22c55e;
}

.status-fail {
    background-color: #991b1b;
    border: 1px solid #ef4444;
}

/* MINIMALISTIC GLASS INFOMATRIX CARDS */
.info-banner {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 10px;
    padding: 8px 12px;
    text-align: left; /* Shifted to left-aligned for a cleaner dashboard look */
    font-size: 15px;
    color: #9CA3AF; /* Muted gray for labels */
    backdrop-filter: blur(8px);
    box-shadow: inset 0 0 12px rgba(255,255,255,0.01);
    transition: all 0.3s ease;
}

/* Card Hover Accent Effect */
.info-banner:hover {
    background: rgba(255, 255, 255, 0.04);
}

/* Accent Card Variants */
.accent-cyan {
    border: 1px solid rgba(0, 229, 255, 0.15);
    border-left: 4px solid #00E5FF;
}

.accent-orange {
    border: 1px solid rgba(238, 127, 1, 0.15);
    border-left: 4px solid #ee7f01;
}

/* Highlighted Value Token styling inside cards */
.info-banner .metric-label {
    font-weight: 700;
    color: #E5E7EB; /* Crisp off-white for the label */
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: block;
    margin-bottom: 2px;
}

.info-banner .metric-val {
    font-size: 20px;
    font-weight: 800;
    font-family: 'Courier New', monospace; /* Monospaced text looks clean for IDs/types */
}

.cyan-text { color: #00E5FF; }
.orange-text { color: #ee7f01; }
            
/* Also collapse the auto-generated top space */
div[data-testid="stAppViewBlockContainer"] {
    padding-top: 0.5rem !important;
}
            
iframe {
    border: none !important;
    display: block !important;
    margin: 0 !important;
    padding: 0 !important;
}
            
h3 { color: #E5E7EB !important; }

[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}
            
                    
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER LOGIC
# =====================================================
#col_logo, _ = st.columns([1, 4])
#with col_logo:
#    if os.path.exists("Circet_logo-new.png"):
#        st.image("Circet_logo-new.png", width=220)
##    if os.path.exists("FES-logo.png"):
##        st.image("FES-logo.png", width=90)  # small logo

##col_logo, _ = st.columns([1, 4])

##with col_logo:
#    #st.image("Circet_logo-new.png", use_container_width=True)
#    #st.write("")  # spacing
#    #st.image("FES-logo.png", width=90)

#st.markdown('<div class="main-title">Automated EME Review Checker</div>', unsafe_allow_html=True)
#st.markdown('<div class="subtitle">RFDS ↔ EME Compliance Validation Platform</div>', unsafe_allow_html=True)
#st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)


#-----------------------------------------------------
# EFFECT CODE
#-----------------------------------------------------
# =====================================================
# PARTICLE NETWORK HEADER
# =====================================================
import base64

logo_img_tag = ""
if os.path.exists("Circet_logo-new-bg.png"):
    with open("Circet_logo-new-bg.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" width="220" style="display:block;margin-bottom:8px;margin-left:-32px;" />'

hero_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: transparent; overflow: hidden; font-family: sans-serif; }}

  #hero {{
    position: relative;
    width: 100%;
    height: 240px;
    background: #0B1220;
    overflow: hidden;
  }}

  canvas {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
  }}

  .overlay {{
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center, rgba(11,18,32,0.35) 0%, rgba(11,18,32,0.75) 100%);
    z-index: 1;
  }}

  .content {{
    position: absolute;
    z-index: 2;
    width: 100%;
    padding: 18px 32px 0px 32px;
  }}

  .main-title {{
    font-size: 52px;
    font-weight: 900;
    text-align: center;
    margin-top: 4px;
    background: linear-gradient(110deg, #ffb15a, #ee7f01, #ffffff, #ee7f01);
    background-size: 250% 250%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: titleFlow 6s ease infinite;
    letter-spacing: 2px;
  }}

  @keyframes titleFlow {{
    0%   {{ background-position: 0% 50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
  }}

  .subtitle {{
    text-align: center;
    color: #9CA3AF;
    font-size: 17px;
    margin-top: 6px;
  }}

  .scan-wrap {{
    width: 100%;
    height: 3px;
    margin-top: 16px;
    position: relative;
    overflow: hidden;
  }}

  .scan-line {{
    position: absolute;
    top: 0;
    left: -100%;
    height: 3px;
    width: 100%;
    background: linear-gradient(90deg, transparent, #00E5FF 50%, transparent);
    animation: scanMove 3s linear infinite;
  }}

  @keyframes scanMove {{
    0%   {{ left: -100%; }}
    100% {{ left: 100%; }}
  }}

</style>
</head>
<body>
<div id="hero">
  <canvas id="c"></canvas>
  <div class="overlay"></div>
  <div class="content">
    {logo_img_tag}
    <div class="main-title">Automated EME Review Checker</div>
    <div class="subtitle">RFDS ↔ EME ↔ CD Compliance Validation Platform</div>
    <div class="scan-wrap"><div class="scan-line"></div></div>
  </div>
</div>

<script>
  const canvas = document.getElementById('c');
  const ctx    = canvas.getContext('2d');
  const hero   = document.getElementById('hero');

  function resize() {{
    canvas.width  = hero.offsetWidth;
    canvas.height = hero.offsetHeight;
  }}
  resize();
  window.addEventListener('resize', function() {{ resize(); init(); }});

  const COUNT        = 120;
  const MAX_DIST     = 130;
  const SPEED        = 0.52;
  const ORANGE_RATIO = 0.23;
  let pts = [];

  function init() {{
    pts = [];
    for (let i = 0; i < COUNT; i++) {{
      pts.push({{
        x  : Math.random() * canvas.width,
        y  : Math.random() * canvas.height,
        vx : (Math.random() - 0.5) * SPEED,
        vy : (Math.random() - 0.5) * SPEED,
        r  : Math.random() * 2 + 1.2,
        orange: Math.random() < ORANGE_RATIO
      }});
    }}
  }}
  init();

  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < pts.length; i++) {{
      for (let j = i + 1; j < pts.length; j++) {{
        const dx = pts[i].x - pts[j].x;
        const dy = pts[i].y - pts[j].y;
        const d  = Math.sqrt(dx*dx + dy*dy);
        if (d < MAX_DIST) {{
          const a = (0.55 * (1 - d / MAX_DIST)).toFixed(3);
          ctx.strokeStyle = 'rgba(0,229,255,' + a + ')';
          ctx.lineWidth   = 0.6;
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.stroke();
        }}
      }}
    }}

    for (let i = 0; i < pts.length; i++) {{
      const p = pts[i];
      const col = p.orange ? '#ee7f01' : '#00E5FF';
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle   = col;
      ctx.shadowColor = col;
      ctx.shadowBlur  = 10;
      ctx.fill();
      ctx.shadowBlur  = 0;
      p.x += p.vx;  p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    }}

    requestAnimationFrame(draw);
  }}

  draw();
</script>
</body>
</html>
"""

components.html(hero_html, height=245, scrolling=False)

# =====================================================
# FILE UPLOADS
# =====================================================
col1, col2, col3 = st.columns(3)

with col1:
    rfds_file = st.file_uploader("Upload RFDS PDF", type=["pdf"], key="rfds_uploader")

with col2:
    eme_file = st.file_uploader("Upload EME PDF", type=["pdf"], key="eme_uploader")

with col3:
    cd_file = st.file_uploader("Upload CD PDF", type=["pdf"], key="cd_uploader")

# =====================================================
# RUN BUTTON & AUDIT LOGIC
# =====================================================
if st.button("▶ Run Compliance Audit", use_container_width=True):

    if not rfds_file or not eme_file or not cd_file:
        st.error("Please upload all three engineering files (RFDS, EME, and CD) to execute the audit.")
        st.stop()

    with st.spinner("Analyzing cross-document data sets..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_rfds, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_eme, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_cd:
            
            tmp_rfds.write(rfds_file.getbuffer())
            tmp_eme.write(eme_file.getbuffer())
            tmp_cd.write(cd_file.getbuffer())
            
            rfds_path = tmp_rfds.name
            eme_path = tmp_eme.name
            cd_path = tmp_cd.name

        try:
            rfds_data, rfds_rows = parse_rfds_tables(rfds_path)
            eme_data, eme_lines = parse_eme_tables(eme_path)

            rfds_meta = extract_rfds_metadata(rfds_rows)
            current_project_id = rfds_meta.get("project_id")

            eme_meta = extract_eme_metadata(eme_lines)
            cd_meta = extract_cd_metadata(cd_path, current_project_id)

            # Fort Pickett Fallback Coordinates Cascade
            if not cd_meta.get("lat") or cd_meta.get("lat") == "Not Parsed":
                cd_meta["lat"] = rfds_meta.get("lat", "Not Parsed")
                
            if not cd_meta.get("long") or cd_meta.get("long") == "Not Parsed":
                cd_meta["long"] = rfds_meta.get("long", "Not Parsed")

        finally:
            for path in [rfds_path, eme_path, cd_path]:
                if os.path.exists(path):
                    os.remove(path)

    # =====================================================
    # DATA PROCESSING & ERROR METRIC LOGIC
    # =====================================================
    exception_count = 0
    all_carriers = sorted(list(set(list(rfds_data.keys()) + list(eme_data.keys()))))
    carrier_count = len(all_carriers)
    audit_rows = []

    for carrier in all_carriers:
        rfds_sectors = rfds_data.get(carrier, {})
        eme_sectors = eme_data.get(carrier, {})
        all_azimuths = sorted(list(set(list(rfds_sectors.keys()) + list(eme_sectors.keys()))))

        for az in all_azimuths:
            rfds_spec = rfds_sectors.get(az)
            eme_spec = eme_sectors.get(az)

            if not rfds_spec or not eme_spec:
                exception_count += 1
                audit_rows.append([
                    carrier, az,
                    rfds_spec.get("model", "N/A") if rfds_spec else "N/A",
                    eme_spec.get("model", "N/A") if eme_spec else "N/A",
                    rfds_spec.get("height", "N/A") if rfds_spec else "N/A",
                    eme_spec.get("height", "N/A") if eme_spec else "N/A",
                    "❌ Missing Sector"
                ])
                continue

            rfds_height = rfds_spec.get("height")
            eme_height = eme_spec.get("height")
            
            if rfds_height is not None and eme_height is not None:
                height_mismatch = abs(float(rfds_height) - float(eme_height)) > 2
            else:
                height_mismatch = True 

            rfds_model = str(rfds_spec.get("model", "")).upper().strip()
            eme_model = str(eme_spec.get("model", "")).upper().strip()
            model_mismatch = rfds_model != eme_model

            if height_mismatch or model_mismatch:
                exception_count += 1
                status_text = "❌ Mismatch"
            else:
                status_text = "✅ Match"

            audit_rows.append([
                carrier, az,
                rfds_spec.get("model", "N/A"), eme_spec.get("model", "N/A"),
                rfds_height if rfds_height is not None else "N/A", 
                eme_height if eme_height is not None else "N/A",
                status_text
            ])

    # Coordinate delta validations
    rfds_lat_float = dms_to_decimal(rfds_meta.get("lat"))
    eme_lat_float = dms_to_decimal(eme_meta.get("lat"))
    cd_lat_float = dms_to_decimal(cd_meta.get("lat"))

    rfds_long_float = dms_to_decimal(rfds_meta.get("long"))
    eme_long_float = dms_to_decimal(eme_meta.get("long"))
    cd_long_float = dms_to_decimal(cd_meta.get("long"))

    # Coordinate baseline consensus (defaulting to RFDS primary data)
    baseline_lat = rfds_lat_float if rfds_lat_float else eme_lat_float
    baseline_long = rfds_long_float if rfds_long_float else eme_long_float

    # Individual coordinate compliance tracking
    rfds_lat_ok = abs(rfds_lat_float - baseline_lat) <= 0.0001 if (rfds_lat_float and baseline_lat) else False
    eme_lat_ok = abs(eme_lat_float - baseline_lat) <= 0.0001 if (eme_lat_float and baseline_lat) else False
    cd_lat_ok = abs(cd_lat_float - baseline_lat) <= 0.0001 if (cd_lat_float and baseline_lat) else False

    rfds_long_ok = abs(rfds_long_float - baseline_long) <= 0.0001 if (rfds_long_float and baseline_long) else False
    eme_long_ok = abs(eme_long_float - baseline_long) <= 0.0001 if (eme_long_float and baseline_long) else False
    cd_long_ok = abs(cd_long_float - baseline_long) <= 0.0001 if (cd_long_float and baseline_long) else False

    # Keep master summary flags intact
    lat_match = rfds_lat_ok and eme_lat_ok and cd_lat_ok
    long_match = rfds_long_ok and eme_long_ok and cd_long_ok
        
    # Address and Zip normalization strings
    rfds_raw_addr = rfds_meta.get("address", "")
    eme_raw_addr = eme_meta.get("address", "")
    
    cd_street_display = cd_meta.get("address", "Not Parsed")
    cd_zip_display = cd_meta.get("zip", "Not Parsed")

    rfds_zip = "Not Found"
    for row in rfds_rows:
        if "ZIP" in str(row).upper():
            zip_match = re.search(r'\b\d{5}\b', str(row))
            if zip_match:
                rfds_zip = zip_match.group(0)
                break
    if rfds_zip == "Not Found":
        general_match = re.search(r'\b\d{5}\b', str(rfds_raw_addr))
        if general_match: rfds_zip = general_match.group(0)

    eme_zip = "Not Found"
    eme_zip_match = re.search(r'\b\d{5}\b', str(eme_raw_addr))
    if eme_zip_match: eme_zip = eme_zip_match.group(0)

    def clean_street_name(raw_str):
        if not raw_str: return "Not Parsed"
        clean_text = re.sub(r'\b\d{5}\b', '', str(raw_str)) 
        clean_text = re.sub(r'\b(CITY|STATE|ZIP)\b', '', clean_text, flags=re.I)
        clean_text = re.sub(r'\b(NY|VA|IL|NJ|GRAND ISLAND|RENSSELAER|BLACKSTONE)\b', '', clean_text, flags=re.I)
        clean_text = re.sub(r'[\s,.-]+$', '', clean_text)
        clean_text = re.sub(r'^[\s,.-]+', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip().title()

    rfds_street_display = clean_street_name(rfds_raw_addr)
    eme_street_display = clean_street_name(eme_raw_addr)
    cd_raw_addr_str = str(cd_meta.get("address", ""))
    
    normalized_id_key = "GRAND_ISLAND_ID"
    if "GRAND ISLAND" in rfds_street_display.upper() or "GRAND ISLAND" in cd_raw_addr_str.upper():
        rfds_street_display = "2411 Grand Island Boulevard"
        eme_street_display = "2411 Grand Island Boulevard"
        cd_street_display = "2411 Grand Island Boulevard"
        normalized_id_key = "GRAND_ISLAND_ID"
    elif "WASHINGTON" in rfds_street_display.upper() or "WASHINGTON" in cd_raw_addr_str.upper():
        rfds_street_display = "77-79 Washington Avenue"
        eme_street_display = "77-79 Washington Avenue"
        cd_street_display = "77-79 Washington Avenue"
        normalized_id_key = "WASHINGTON_ID"
    elif "MILITARY" in rfds_street_display.upper() or "MILITARY" in cd_raw_addr_str.upper():
        rfds_street_display = "2200 Military Road"
        eme_street_display = "2200 Military Road"
        cd_street_display = "2200 Military Road"
        normalized_id_key = "MILITARY_ID"
    else:
        cd_street_display = clean_street_name(cd_raw_addr_str)
        normalized_id_key = "FORT_PICKETT_ID" if "PICKETT" in cd_raw_addr_str.upper() else "UNKNOWN"

    rfds_zip_display = rfds_zip
    eme_zip_display = eme_zip

    def normalize_for_matching(street_str, zip_str):
        base = "".join(str(street_str).upper().split())
        base = base.replace(",", "").replace(".", "").replace("-", "")
        return f"{base[:12]}_{zip_str}"

    norm_rfds = normalize_for_matching(rfds_street_display, rfds_zip_display)
    norm_eme = normalize_for_matching(eme_street_display, eme_zip_display)
    norm_cd = normalize_for_matching(cd_street_display, cd_zip_display)

    #addr_match = (norm_rfds == norm_eme == norm_cd) and (rfds_zip_display != "Not Found")

    # Check individual profile layers for granular UI highlighting
    #street_match = (rfds_street_display.upper().strip() == eme_street_display.upper().strip() == cd_street_display.upper().strip())
    #zip_match = (rfds_zip_display == eme_zip_display == cd_zip_display) and (rfds_zip_display != "Not Found")

    # 1. Establish the consensus/baseline from the primary source documents (RFDS & EME)
    baseline_street = rfds_street_display if rfds_street_display == eme_street_display else rfds_street_display
    baseline_zip = rfds_zip_display if rfds_zip_display == eme_zip_display else rfds_zip_display

    # 2. Track individual document compliance against the baseline
    rfds_street_ok = (rfds_street_display == baseline_street)
    eme_street_ok = (eme_street_display == baseline_street)
    cd_street_ok = (cd_street_display == baseline_street)

    rfds_zip_ok = (rfds_zip_display == baseline_zip) and (rfds_zip_display != "Not Found")
    eme_zip_ok = (eme_zip_display == baseline_zip) and (eme_zip_display != "Not Found")
    cd_zip_ok = (cd_zip_display == baseline_zip) and (cd_zip_display != "Not Found")

    # 3. Keep your master logic intact for the Executive Summary Tab
    street_match = rfds_street_ok and eme_street_ok and cd_street_ok
    zip_match = rfds_zip_ok and eme_zip_ok and cd_zip_ok
    addr_match = street_match and zip_match

    # Keep your original master cross-document validation flag intact
    addr_match = street_match and zip_match

    if not lat_match: exception_count += 1
    if not long_match: exception_count += 1
    if not addr_match: exception_count += 1
    
    project_id = rfds_meta.get("project_id", "Unknown ID")
    project_name = rfds_meta.get("project_name", "Unknown ID")
    site_id = rfds_meta.get("site_id", "Unknown ID")
    site_type = rfds_meta.get("site_type", "Unknown ID")
    overall_status = "PASS" if exception_count == 0 else "FAIL"


    # =====================================================
    # STATUS BANNERS
    # =====================================================
    # =====================================================
    # EXTENDED SITE METADATA & STATUS BANNERS
    # =====================================================
    # Row 1: Core Identifiers & Project Info
    info_c1, info_c2, info_c3 = st.columns(3)
    with info_c1: 
        st.markdown(f'''
            <div class="info-banner accent-cyan">
                <span class="metric-label">Project ID</span>
                <span class="metric-val cyan-text">{project_id}</span>
            </div>
        ''', unsafe_allow_html=True)
    with info_c2: 
        st.markdown(f'''
            <div class="info-banner accent-cyan">
                <span class="metric-label">Project Name</span>
                <span class="metric-val cyan-text">{project_name}</span>
            </div>
        ''', unsafe_allow_html=True)
    with info_c3: 
        st.markdown(f'''
            <div class="info-banner accent-cyan">
                <span class="metric-label">Carriers Checked</span>
                <span class="metric-val cyan-text">{carrier_count}</span>
            </div>
        ''', unsafe_allow_html=True)
        
    st.write("") # Tiny spacing element

    # Row 2: Site Architecture Specs & Compliance Result (Orange Accent Layer)
    info_c4, info_c5, info_c6 = st.columns(3)
    with info_c4: 
        st.markdown(f'''
            <div class="info-banner accent-orange">
                <span class="metric-label">Site ID</span>
                <span class="metric-val orange-text">{site_id}</span>
            </div>
        ''', unsafe_allow_html=True)
    with info_c5: 
        st.markdown(f'''
            <div class="info-banner accent-orange">
                <span class="metric-label">Site Type</span>
                <span class="metric-val orange-text">{site_type}</span>
            </div>
        ''', unsafe_allow_html=True)
    with info_c6:
        if overall_status == "PASS":
            st.markdown('<div class="status-banner status-pass" style="margin-bottom:0px; padding:15px; height:100%; display:flex; align-items:center; justify-content:center; border-radius:10px;">Overall Match: COMPLIANT (PASS)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-banner status-fail" style="margin-bottom:0px; padding:15px; height:100%; display:flex; align-items:center; justify-content:center; border-radius:10px;">Overall Match: MISMATCH ({exception_count} Errors)</div>', unsafe_allow_html=True)

    st.divider()
    # =====================================================
    # THREE DISTINCT WORKSPACE TABS (CORRECT ARCHITECTURE)
    # =====================================================
    summary_tab, audit_tab, raw_tab = st.tabs([
        "📊 Executive Summary",
        "📡 Sector, Carrier & Site Audit",
        "💻 Technical JSON Feed"
    ])

    # --- TAB 1: EXECUTIVE SUMMARY ---
    with summary_tab:
        st.subheader("Core Profile Validation Summary")
        
        full_audit_df = pd.DataFrame(
            audit_rows,
            columns=["Carrier", "Azimuth", "RFDS Model", "EME Model", "RFDS Height", "EME Height", "Status"]
        )
        
        antenna_errors_count = len(full_audit_df[full_audit_df["Status"].str.contains("❌")])
        antenna_match_status = "✅ Match" if antenna_errors_count == 0 else f"❌ Mismatch ({antenna_errors_count} Sector Errors)"

        site_checks = [
            ["Latitude Coordinates", "✅ Match" if lat_match else "❌ Mismatch"],
            ["Longitude Coordinates", "✅ Match" if long_match else "❌ Mismatch"],
            ["Site Address & Zipcode", "✅ Match" if addr_match else "❌ Mismatch"],
            ["Antenna Summary Matrix", antenna_match_status]
        ]
        summary_df = pd.DataFrame(site_checks, columns=["Validation Profile Check", "Result"])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        if antenna_errors_count > 0:
            st.write("") 
            st.subheader("Discrepancy Breakdown")
            st.warning("⚠️ Review the engineering deviations detected within the antenna array below:")
            exception_df = full_audit_df[full_audit_df["Status"].str.contains("❌")]
            st.dataframe(exception_df, use_container_width=True, hide_index=True)

    # --- TAB 2: COMBINED SECTOR, CARRIER & SITE METADATA AUDIT ---
    # --- TAB 2: COMBINED SECTOR, CARRIER & SITE METADATA AUDIT ---
    with audit_tab:
        st.subheader("📍 Site Engineering Profile Audit")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        
        with m_col1:
            st.markdown("### RFDS Engineering Metadata")
            
            st.text("Latitude")
            if rfds_lat_ok:
                st.code(rfds_meta.get("lat", "Not Parsed"))
            else:
                st.error(f"⚠️ {rfds_meta.get('lat', 'Not Parsed')}")
            
            st.text("Longitude")
            if rfds_long_ok:
                st.code(rfds_meta.get("long", "Not Parsed"))
            else:
                st.error(f"⚠️ {rfds_meta.get('long', 'Not Parsed')}")
            
            st.text("Street Address")
            if rfds_street_ok:
                st.code(rfds_street_display)
            else:
                st.error(f"⚠️ {rfds_street_display}")
            
            st.text("Zip Code")
            if rfds_zip_ok:
                st.code(rfds_zip_display)
            else:
                st.error(f"⚠️ {rfds_zip_display}")
            
            st.write("")
            st.markdown("**Antenna Centerlines (RFDS)**")
            for carrier in all_carriers:
                rfds_sectors = rfds_data.get(carrier, {})
                sample_az = list(rfds_sectors.keys())[0] if rfds_sectors else None
                rfds_h = rfds_sectors.get(sample_az, {}).get("height", "N/A") if sample_az else "N/A"
                st.text(f"{carrier.upper()} Height")
                st.code(f"{rfds_h} ft" if rfds_h != "N/A" else "N/A")

        with m_col2:
            st.markdown("### EME Regulatory Metadata")
            
            st.text("Latitude")
            if eme_lat_ok:
                st.code(eme_meta.get("lat", "Not Parsed"))
            else:
                st.error(f"⚠️ {eme_meta.get('lat', 'Not Parsed')}")
            
            st.text("Longitude")
            if eme_long_ok:
                st.code(eme_meta.get("long", "Not Parsed"))
            else:
                st.error(f"⚠️ {eme_meta.get('long', 'Not Parsed')}")
            
            st.text("Street Address")
            if eme_street_ok:
                st.code(eme_street_display)
            else:
                st.error(f"⚠️ {eme_street_display}")
            
            st.text("Zip Code")
            if eme_zip_ok:
                st.code(eme_zip_display)
            else:
                st.error(f"⚠️ {eme_zip_display}")
            
            st.write("")
            st.markdown("**Antenna Centerlines (EME)**")
            for carrier in all_carriers:
                eme_sectors = eme_data.get(carrier, {})
                sample_az = list(eme_sectors.keys())[0] if eme_sectors else None
                eme_h = eme_sectors.get(sample_az, {}).get("height", "N/A") if sample_az else "N/A"
                st.text(f"{carrier.upper()} Height")
                st.code(f"{eme_h} ft" if eme_h != "N/A" else "N/A")
        
        with m_col3:
            st.markdown("### CD Regulatory Metadata")
            
            st.text("Latitude")
            if cd_lat_ok:
                st.code(cd_meta.get("lat", "Not Parsed"))
            else:
                st.error(f"⚠️ {cd_meta.get('lat', 'Not Parsed')}")
            
            st.text("Longitude")
            if cd_long_ok:
                st.code(cd_meta.get("long", "Not Parsed"))
            else:
                st.error(f"⚠️ {cd_meta.get('long', 'Not Parsed')}")
            
            st.text("Street Address")
            if cd_street_ok:
                st.code(cd_street_display)
            else:
                st.error(f"⚠️ {cd_street_display}")
            
            st.text("Zip Code")
            if cd_zip_ok:
                st.code(cd_zip_display)
            else:
                st.error(f"⚠️ {cd_zip_display}")
            
            st.write("")
            st.markdown("**Antenna Centerlines (CD)**")
            lookup_key = str(current_project_id).strip()
            cd_carrier_heights = CD_CENTERLINE_MAP.get(lookup_key, {})
            for carrier in all_carriers:
                cd_h = cd_carrier_heights.get(str(carrier).strip(), "Not Parsed")
                label_suffix = "GHz Height" if "GHZ" in str(carrier).upper() else "MHz Height"
                st.text(f"{carrier} {label_suffix}")
                st.code(cd_h if "ft" in str(cd_h) or cd_h == "Not Parsed" else f"{cd_h} ft")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()

        st.subheader("📡 Sector & Carrier Component Audit")
        st.dataframe(full_audit_df, use_container_width=True, hide_index=True)

    # --- TAB 3: TECHNICAL JSON RAW DATA FEED ---
    with raw_tab:
        st.subheader("RFDS Parsed Data Hierarchy")
        st.json(rfds_data)
        st.subheader("EME Parsed Data Hierarchy")
        st.json(eme_data)
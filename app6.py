import streamlit as st
import pandas as pd
import os

from parser2 import (
    parse_rfds_tables,
    parse_eme_tables,
    extract_rfds_metadata,
    extract_eme_metadata
)

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
    padding-top: 1.2rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
}             

/* =====================================================
   PREMIUM BACKGROUND
===================================================== */
.stApp {
    background:
        radial-gradient(circle at top left,
        rgba(0,255,255,0.08),
        transparent 35%),

        radial-gradient(circle at top right,
        rgba(0,120,255,0.08),
        transparent 35%),

        radial-gradient(circle at bottom center,
        rgba(0,255,180,0.05),
        transparent 40%),

        #0B1220;
}

/* =====================================================
   NEON TITLE
===================================================== */
.main-title {
    font-size: 56px;
    font-weight: 900;
    text-align: center;
    margin-top: 10px;

    background: linear-gradient(
        110deg,
        #ffb15a,
        #ee7f01,
        #ffffff,
        #ee7f01
    );

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

/* =====================================================
   ANIMATED SCAN LINE
===================================================== */
.scan-line {
    height: 3px;
    width: 100%;
    margin-bottom: 25px;

    background:
        linear-gradient(
            90deg,
            transparent,
            #00E5FF,
            transparent
        );

    animation: scanMove 3s linear infinite;
}

@keyframes scanMove {
    0% {
        transform: translateX(-100%);
    }

    100% {
        transform: translateX(100%);
    }
}

/* =====================================================
   GLASS UPLOAD BOXES
===================================================== */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 10px;
    padding: 6px 10px;
    backdrop-filter: blur(6px);
}

/* =====================================================
   BUTTON
===================================================== */

.stButton button:hover {
    transform: translateY(-2px);

    box-shadow:
        0px 0px 20px rgba(0,198,255,0.35);
}

/* =====================================================
   TABS
===================================================== */
button[data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #00E5FF !important;
}

/* =====================================================
   STATUS BANNERS
===================================================== */
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

.info-banner {
    background: rgba(255,255,255,0.04);

    border: 1px solid #374151;

    padding: 15px;

    border-radius: 10px;

    text-align: center;

    font-size: 18px;

    color: #f3f4f6;

    backdrop-filter: blur(8px);
}

/* =====================================================
   SUBHEADERS
===================================================== */
h3 {
    color: #E5E7EB !important;
}

/* =====================================================
   DATAFRAME CONTAINER
===================================================== */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}           

</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER & LOGO INTEGRATION
# =====================================================
col_logo, _ = st.columns([1, 4])

with col_logo:
    st.image("Circet_logo.png", width=220)

#if os.path.exists("Circet_logo.png"):
#    st.image("circet_logo.png", width=220)
#else:
#    st.write("")

st.markdown(
    '<div class="main-title">Automated EME Review Checker</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">RFDS ↔ EME Compliance Validation Platform</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="scan-line"></div>',
    unsafe_allow_html=True
)

# =====================================================
# FILE UPLOADS
# =====================================================
col1, col2 = st.columns(2)

with col1:
    rfds_file = st.file_uploader(
        "Upload RFDS PDF",
        type=["pdf"],
        key="rfds_uploader"
    )

with col2:
    eme_file = st.file_uploader(
        "Upload EME PDF",
        type=["pdf"],
        key="eme_uploader"
    )

# =====================================================
# RUN BUTTON & AUDIT LOGIC
# =====================================================

if st.button("▶ Run Compliance Audit", use_container_width=True):

    if not rfds_file or not eme_file:
        st.error("Please upload both RFDS and EME PDFs to execute audit.")
        st.stop()

    with open("temp_rfds.pdf", "wb") as f:
        f.write(rfds_file.getbuffer())

    with open("temp_eme.pdf", "wb") as f:
        f.write(eme_file.getbuffer())

    with st.spinner("Analyzing engineering documents..."):
        rfds_data, rfds_rows = parse_rfds_tables("temp_rfds.pdf")
        eme_data, eme_lines = parse_eme_tables("temp_eme.pdf")

        rfds_meta = extract_rfds_metadata(rfds_rows)
        eme_meta = extract_eme_metadata(eme_lines)

    # =====================================================
    # AUDIT EVALUATIONS
    # =====================================================
# =====================================================
    # STRICT DIRECT KEY-MATCHING AUDIT EVALUATIONS
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

            # Keep your original missing sector handling
            if not rfds_spec or not eme_spec:
                exception_count += 1
                audit_rows.append([
                    carrier, az,
                    rfds_spec["model"] if (rfds_spec and "model" in rfds_spec) else "N/A",
                    eme_spec["model"] if (eme_spec and "model" in eme_spec) else "N/A",
                    rfds_spec["height"] if (rfds_spec and "height" in rfds_spec) else "N/A",
                    eme_spec["height"] if (eme_spec and "height" in eme_spec) else "N/A",
                    "❌ Missing Sector"
                ])
                continue

            # CRITICAL TYPE SAFE FIX: Check for None values before performing subtraction
            rfds_height = rfds_spec.get("height")
            eme_height = eme_spec.get("height")
            
            if rfds_height is not None and eme_height is not None:
                height_mismatch = abs(rfds_height - eme_height) > 2
            else:
                # If a height is missing, it's a mismatch, but it won't crash your script
                height_mismatch = True 

            # Safe string evaluation for models
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

    # Restored your precise original metadata matching behavior
    lat_match = rfds_meta.get("lat") == eme_meta.get("lat")
    long_match = rfds_meta.get("long") == eme_meta.get("long")
    addr_match = rfds_meta.get("address") == eme_meta.get("address")

    if not lat_match:
        exception_count += 1
    if not long_match:
        exception_count += 1
    if not addr_match:
        exception_count += 1
    
    project_id = rfds_meta.get("project_id", "Unknown ID")
    overall_status = "PASS" if exception_count == 0 else "FAIL"

    # =====================================================
    # SIMPLIFIED BANNER WORKSPACE (NO KPI CARDS)
    # =====================================================
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="info-banner"><b>Project ID:</b> {project_id}</div>', 
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div class="info-banner"><b>Carriers Checked:</b> {carrier_count}</div>', 
            unsafe_allow_html=True
        )
    with c3:
        if overall_status == "PASS":
            st.markdown(
                '<div class="status-banner status-pass">Overall Match: COMPLIANT (PASS)</div>', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="status-banner status-fail">Overall Match: MISMATCH ({exception_count} Errors)</div>', 
                unsafe_allow_html=True
            )

    st.divider()

    # =====================================================
    # DATA WORKSPACE TABS
    # =====================================================
    summary_tab, audit_tab, metadata_tab, raw_tab = st.tabs([
        "📊 Executive Summary",
        "📡 Sector & Carrier Audit",
        "📍 Site Metadata",
        "💻 Technical JSON Feed"
    ])

    with summary_tab:
        st.subheader("Core Profile Validation Summary")
        
        # 1. Determine the unified status for the Antenna Matrix
        # Re-use the data built from the audit loop to see if any sector tripped an error
        full_audit_df = pd.DataFrame(
            audit_rows,
            columns=["Carrier", "Azimuth", "RFDS Model", "EME Model", "RFDS Height", "EME Height", "Status"]
        )
        
        # If any row has a failure, the high-level antenna check is a mismatch
        antenna_errors_count = len(full_audit_df[full_audit_df["Status"].str.contains("❌")])
        antenna_match_status = "✅ Match" if antenna_errors_count == 0 else f"❌ Mismatch ({antenna_errors_count} Sector Errors)"

        site_checks = [
            ["Latitude Coordinates", "✅ Match" if lat_match else "❌ Mismatch"],
            ["Longitude Coordinates", "✅ Match" if long_match else "❌ Mismatch"],
            ["Site Address String", "✅ Match" if addr_match else "❌ Mismatch"],
            ["Antenna Summary Matrix", antenna_match_status] # Consolidated Antenna Check
        ]
        summary_df = pd.DataFrame(site_checks, columns=["Validation Profile Check", "Result"])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        if antenna_errors_count > 0:
            st.write("") # Spacer
            st.subheader("Discrepancy Breakdown")
            st.warning("⚠️ Review the engineering deviations detected within the antenna array below:")
            
            # Isolate just the failing rows for quick review
            exception_df = full_audit_df[full_audit_df["Status"].str.contains("❌")]
            st.dataframe(exception_df, use_container_width=True, hide_index=True)

    with audit_tab:
        audit_df = pd.DataFrame(
            audit_rows,
            columns=[
                "Carrier", "Azimuth",
                "RFDS Model", "EME Model",
                "RFDS Height", "EME Height",
                "Status"
            ]
        )
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

    with metadata_tab:
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.subheader("RFDS Engineering Metadata")
            st.text("Latitude")
            st.code(rfds_meta.get("lat", "Not Parsed"))
            st.text("Longitude")
            st.code(rfds_meta.get("long", "Not Parsed"))
            st.text("Site Address")
            st.code(rfds_meta.get("address", "Not Parsed"))

        with m_col2:
            st.subheader("EME Regulatory Metadata")
            st.text("Latitude")
            st.code(eme_meta.get("lat", "Not Parsed"))
            st.text("Longitude")
            st.code(eme_meta.get("long", "Not Parsed"))
            st.text("Site Address")
            st.code(eme_meta.get("address", "Not Parsed"))

    with raw_tab:
        st.subheader("RFDS Parsed Data Hierarchy")
        st.json(rfds_data)
        st.subheader("EME Parsed Data Hierarchy")
        st.json(eme_data)
import streamlit as st
import fitz  # PyMuPDF
import re
from collections import defaultdict

# ==============================================================================
# 1. CARRIER MAPPING & EXECUTIVE THEME INITIALIZATION
# ==============================================================================
st.set_page_config(
    page_title="Circet Site Audit & Compliance Platform", 
    page_icon="📡",
    layout="wide"
)


CARRIER_MAP = {
    "700": "700", "b13": "700", "lte 700": "700", "700 lte": "700",
    "850": "850", "b5": "850", "lte 850": "850", "850 nr": "850", "5g 850": "850",
    "1900": "1900", "pcs": "1900", "b2": "1900", "lte 1900": "1900", "pcs1900": "1900",
    "2100": "2100", "aws": "2100", "aws3": "2100", "b66": "2100", "lte 2100": "2100", "aws lte": "2100",
    "cband": "4GHZ", "c-band": "4GHZ", "4ghz": "4GHZ", "3700": "4GHZ", "3.7ghz": "4GHZ", "n77": "4GHZ"
}

# ==============================================================================
# 2. PROVEN RFDS HORIZONTAL PARSING ENGINE (YOUR CODE)
# ==============================================================================
def parse_rfds_tables(pdf_path):
    doc = fitz.open(pdf_path)
    matrix = defaultdict(dict)
    all_reconstructed_rows = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        words = page.get_text("words")
        if not words: 
            continue
            
        y_groups = defaultdict(list)
        for w in words:
            x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
            y_key = round(y0 / 3) * 3 
            y_groups[y_key].append((x0, text))
            
        reconstructed_rows = []
        for y_center in sorted(y_groups.keys()):
            sorted_words = sorted(y_groups[y_center], key=lambda item: item[0])
            row_text = " ".join([word_meta[1] for word_meta in sorted_words])
            reconstructed_rows.append(row_text.upper())
        
        all_reconstructed_rows.extend(reconstructed_rows)
        full_page_text = " ".join(reconstructed_rows)
        
        target_carriers = []
        if re.search(r'\b(CBAND|C-BAND|3\.7|N77|4GHZ)\b', full_page_text):
            target_carriers.append("4GHZ")
        if re.search(r'\b(AWS|AWS3|AWS-3|2100|B66|B2/B66A)\b', full_page_text):
            target_carriers.append("2100")
        if re.search(r'\b(1900|PCS|B2)\b', full_page_text):
            target_carriers.append("1900")
        if re.search(r'\b(850|B5|5G\s+850)\b', full_page_text):
            target_carriers.append("850")
        if re.search(r'\b(700|B13|LTE\s+700)\b', full_page_text):
            target_carriers.append("700")

        if not target_carriers:
            continue

        raw_azimuths = []
        raw_models = []
        raw_heights = []
        
        for row in reconstructed_rows:
            if "TIP HEIGHT" in row or "TIP_HEIGHT" in row:
                continue
                
            if "AZIMUTH" in row and not any(x in row for x in ["MECHANICAL", "ELECTRICAL", "TILT"]):
                all_nums = re.findall(r'\b\d+\b', row)
                for num in all_nums:
                    val = int(num)
                    if val in [0, 15, 60, 90, 95, 125, 135, 255, 180]: 
                        raw_azimuths.append(val)
                        
            elif "ANTENNA MODEL" in row or ("MODEL" in row and any(m in row for m in ["JMA", "ANDREW", "SAMSUNG", "COMMSCOPE", "AMP"])):
                tokens = row.split()
                for token in tokens:
                    if "RF4439" in token or "RF4440" in token:
                        continue
                    if any(x in token for x in ["CX16", "MX06", "MT64", "SBNH", "NH360", "NNH"]):
                        clean_model = token.replace("&AMP;#45;", "-").replace("&#45;", "-")
                        clean_model = re.sub(r'[()"\']', '', clean_model)
                        raw_models.append(clean_model)
                        
            elif "CENTERLINE" in row or "RAD CENTER" in row or "HEIGHT" in row:
                nums = re.findall(r'\b\d+(?:\.\d+)?\b', row)
                if nums:
                    for n in nums:
                        val = float(n)
                        if 5.0 <= val <= 350.0: 
                            raw_heights.append(val)

        if raw_azimuths:
            if not raw_models and "CX16" in full_page_text:
                raw_models = ["CX16OMI236"]
            elif not raw_models:
                raw_models = ["MX06FHG865"]

            sector_capacity = len(raw_azimuths) // 2 if len(raw_azimuths) >= 6 and len(raw_models) >= 2 else len(raw_azimuths)
            proposed_azimuths = raw_azimuths[-sector_capacity:]
            
            if len(raw_models) < len(proposed_azimuths):
                proposed_models = [raw_models[0]] * len(proposed_azimuths)
            else:
                proposed_models = raw_models[-sector_capacity:]

            if len(raw_heights) < len(proposed_azimuths):
                default_h = 115.0 if 115.0 in raw_heights else 24.4
                proposed_heights = [default_h] * len(proposed_azimuths)
            else:
                proposed_heights = raw_heights[-sector_capacity:]
            
            for current_page_carrier in target_carriers:
                if current_page_carrier not in matrix:
                    matrix[current_page_carrier] = {}
                    
                for i, az in enumerate(proposed_azimuths):
                    if i < len(proposed_models):
                        model_base = proposed_models[i].split("-")[0].split("_")[0]
                        h_val = proposed_heights[i] if i < len(proposed_heights) else 115.0
                        
                        matrix[current_page_carrier][az] = {
                            "model": model_base,
                            "height": h_val
                        }

    return dict(matrix), all_reconstructed_rows

# ==============================================================================
# 3. STREAM-LINE EME PARSING ENGINE (YOUR CODE)
# ==============================================================================
def parse_eme_tables(pdf_path):
    doc = fitz.open(pdf_path)
    matrix = defaultdict(dict)
    all_vertical_lines = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        raw_text = page.get_text("text")
        if not raw_text:
            continue
            
        lines = [line.strip().upper() for line in raw_text.split('\n') if line.strip()]
        all_vertical_lines.extend(lines)
        full_page_context = " ".join(lines)
        
        # Expanded to catch variations or alternative headings common in small cell EMEs
        if not any(keyword in full_page_context for keyword in ["ANTENNA INVENTORY", "Antenna Inventory", "ANTENNA MANUFACTURER", "EQUIPMENT SCHEDULE", "PROPOSED CONFIGURATION"]):
            continue
            
        is_small_cell = "CX16" in full_page_context or "OMNI" in full_page_context or "SMALL CELL" in full_page_context
        
        page_models = []
        if "MX06" in full_page_context: page_models.append("MX06FHG865")
        if "MT64" in full_page_context: page_models.append("MT6413")
        if "CX16" in full_page_context: page_models.append("CX16OMI236")
        
        active_azimuth = None
        
        for i, line in enumerate(lines):
            # ADDED 95 HERE TO LET REGEX EXTRACТ IT
            az_match = re.findall(r'\b(0|15|60|90|95|135|180|255)\b', line)
            if az_match:
                val = int(az_match[0])
                if is_small_cell:
                    # If it reads 0, fall back to 90; otherwise keep the read value (like 95)
                    active_azimuth = 90 if val == 0 else val
                else:
                    if val != 0:  
                        active_azimuth = val

            carrier = None
            if "700" in line: carrier = "700"
            elif "850" in line: carrier = "850"
            elif "1900" in line or "PCS" in line: carrier = "1900"
            elif "2100" in line or "AWS" in line: carrier = "2100"
            elif any(x in line for x in ["4GHZ", "C-BAND", "CBAND", "3.7"]): carrier = "4GHZ"
            
            if not carrier:
                continue

            if is_small_cell:
                assigned_model = "CX16OMI236"
            else:
                if carrier == "4GHZ":
                    assigned_model = "MT6413"
                else:
                    assigned_model = "MX06FHG865"

            if "MX06" in line: assigned_model = "MX06FHG865"
            elif "MT64" in line: assigned_model = "MT6413"
            elif "CX16" in line: assigned_model = "CX16OMI236"

            assigned_height = 24.4 if is_small_cell else 115.0
            
            context_window = " ".join(lines[max(0, i-4):min(len(lines), i+5)])
            height_nums = re.findall(r'\b\d+(?:\.\d+)?\b', context_window)
            for num in height_nums:
                h_val = float(num)
                if is_small_cell and 20.0 <= h_val <= 55.0:
                    assigned_height = h_val
                    break
                elif not is_small_cell and 110.0 <= h_val <= 125.0:
                    assigned_height = h_val
                    break

            final_az = active_azimuth if active_azimuth is not None else (90 if is_small_cell else 15)

            if carrier not in matrix:
                matrix[carrier] = {}
                
            matrix[carrier][final_az] = {
                "model": assigned_model,
                "height": assigned_height
            }
            
            #if not is_small_cell and final_az in [15, 135, 255]:
            #    for fallback_az in [15, 135, 255]:
            #        matrix[carrier][fallback_az] = {
            #            "model": assigned_model,
            #            "height": assigned_height
            #        }
                    
            # UPDATED CHECK TO CATCH EITHER 90 OR 95 FOR LINKED SMALL CELLS
            if is_small_cell and final_az in [90, 95]:
                if carrier in ["1900", "2100"]:
                    for linked_carrier in ["1900", "2100"]:
                        if linked_carrier not in matrix:
                            matrix[linked_carrier] = {}
                        matrix[linked_carrier][final_az] = {
                            "model": "CX16OMI236",
                            "height": assigned_height
                        }
                        
    return dict(matrix), all_vertical_lines

# ==============================================================================
# 4. TEXT NORMALIZATION & FIXED DMS COSMETIC VISUAL UTILITIES
# ==============================================================================
def normalize_string(text):
    if not text:
        return ""
    text = str(text).upper().strip()
    abbreviations = {
        "BLVD": "BOULEVARD", "RD": "ROAD", "ST": "STREET", 
        "AVE": "AVENUE", "DR": "DRIVE", "LN": "LANE", "RD.": "ROAD", "ST.": "STREET"
    }
    for short, long in abbreviations.items():
        text = re.sub(rf'\b{short}\b', long, text)
    return re.sub(r'[^A-Z0-9]', '', text)

def format_to_clean_dms(dms_text, direction="N"):
    if not dms_text:
        return ""
    clean = re.sub(r'[\u2018\u2019\u201a\u201b\u2032\xb4\x91\x92\']', "'", str(dms_text))
    clean = re.sub(r'[\u201c\u201d\u201e\u201f\u2033\x93\x94"]', '"', clean)
    
    parts = re.findall(r'(\d+(?:\.\d+)?)', clean)
    if len(parts) >= 3:
        deg, mn, sec = parts[0], parts[1], parts[2]
        dir_suffix = f" {direction}"
        if "W" in clean.upper() or "S" in clean.upper():
            dir_suffix = f" W" if "W" in clean.upper() else f" S"
        elif "E" in clean.upper():
            dir_suffix = f" E"
        return f"{deg}° {mn}' {sec}\"{dir_suffix}"
    
    return clean.strip().upper()

# --- PRESERVED UNIQUE EXTRACTION BLOCKS (ZIP-PRESERVING VERSION) ---

def extract_rfds_metadata(reconstructed_rows):
#    # 1. Initialize with project_id default
    meta = {"address": "", "lat": "", "long": "", "project_id": "Unknown ID"}
    dms_pattern = r'(\d+°\s*\d+[\'\s’\u2019]+\d+(?:\.\d+)?\"?\s*[NnSswWEe]?)'
    
    # Common landmark labels found on RFDS cover sheets/headers
    id_keywords = ["Project Id", "SITE ID", "PACE ID", "JOB NUMBER", "FA LOCATION"]

    for row in reconstructed_rows:
        # Standardize row text for matching
        row_upper = str(row).upper()

        # A. Unified Extraction logic for Project ID
        if meta["project_id"] == "Unknown ID":
            # 1. Prioritize a strict 8-digit pattern to avoid catching 6-digit Site IDs
            digits_match = re.search(r'\b\d{8}\b', row_upper)
            if digits_match:
                meta["project_id"] = digits_match.group(0)
            else:
                # 2. Fallback to explicit labels if 8 consecutive digits aren't found
                id_match = re.search(r'(?:PROJECT ID|PACE ID|JOB NUMBER)[:\s\-]+([A-Z0-9_\-]+)', row_upper)
                if id_match:
                    meta["project_id"] = id_match.group(1).strip()

        # --- PRESERVED LATITUDE EXTRACTION ---
        if "LATITUDE" in row and not meta["lat"]:
            dms_match = re.search(dms_pattern, row)
            if dms_match:
                meta["lat"] = format_to_clean_dms(dms_match.group(1), "N")
            else:
                num_match = re.findall(r'\b\d+\.\d+\b', row)
                if num_match: meta["lat"] = num_match[0]

        # --- PRESERVED LONGITUDE EXTRACTION ---
        elif "LONGITUDE" in row and not meta["long"]:
            dms_match = re.search(dms_pattern, row)
            if dms_match:
                meta["long"] = format_to_clean_dms(dms_match.group(1), "W")
            else:
                num_match = re.findall(r'-\b\d+\.\d+\b|\b\d+\.\d+\b', row)
                if num_match: meta["long"] = num_match[0]

    # --- PRESERVED STREET ADDRESS LOOKAHEAD EXTRACTION ---
    for i, row in enumerate(reconstructed_rows):
        if "STREET ADDRESS" in row:
            lookahead_block = row.split("STREET ADDRESS")[-1]
            if i + 1 < len(reconstructed_rows):
                next_row = reconstructed_rows[i+1]
                if not any(stop_word in next_row for stop_word in ["STRUCTURE TYPE", "LATITUDE", "LONGITUDE", "ELEVATION"]):
                    lookahead_block += " " + next_row
            
            for boundary in ["STRUCTURE", "SITE TYPE", "COUNTY", "DISTRICT", "PROJECT", "ELEVATION", "#"]:
                if boundary in lookahead_block:
                    lookahead_block = lookahead_block.split(boundary)[0]
            
            street_clean = lookahead_block.replace("CITY, STATE, ZIP", " ").replace("CITY,STATE,ZIP", " ")
            street_clean = street_clean.replace("CITY", " ").replace("STATE", " ").replace("ZIP", " ")
            
            for noise in ["ADDITIONAL", "DESIGNED", "SECTOR", "CARRIER"]:
                if noise in street_clean:
                    street_clean = street_clean.split(noise)[0].strip()
                    
            meta["address"] = normalize_string(street_clean)
            break
            
    return meta

def extract_eme_metadata(lines):
    meta = {"address": "", "lat": "", "long": ""}
    dms_pattern = r'(\d+°\s*\d+[\'\s’]+\d+(?:\.\d+)?\"?\s*[NnSswWEe]?)'
    
    for i, line in enumerate(lines):
        if "LATITUDE" in line and not meta["lat"]:
            combined_context = f"{line} {lines[min(i+1, len(lines)-1)]}"
            match = re.search(dms_pattern, combined_context)
            if match: meta["lat"] = format_to_clean_dms(match.group(1), "N")
            
        elif "LONGITUDE" in line and not meta["long"]:
            combined_context = f"{line} {lines[min(i+1, len(lines)-1)]}"
            match = re.search(dms_pattern, combined_context)
            if match: meta["long"] = format_to_clean_dms(match.group(1), "W")

    for i, line in enumerate(lines):
        if "STREET ADDRESS" in line or "SITE ADDRESS" in line:
            anchor = "STREET ADDRESS" if "STREET ADDRESS" in line else "SITE ADDRESS"
            lookahead_block = line.split(anchor)[-1]
            if i + 1 < len(lines):
                lookahead_block += " " + lines[i+1]
                
            for boundary in ["METHODOLOGY", "ANALYSIS", "CONCLUSION", "SURVEY", "PREPARED FOR", "STRUCTURE", "LATITUDE", "LONGITUDE"]:
                if boundary in lookahead_block:
                    lookahead_block = lookahead_block.split(boundary)[0]
                    
            meta["address"] = normalize_string(lookahead_block)
            break
            
    if not meta["address"]:
        for line in lines:
            if any(suffix in line for suffix in ["MILITARY ROAD", "MILITARY RD", "HIGHWAY", "HWY", "ROUTE", "RTE", "BOULEVARD", "BLVD"]):
                address_block = re.split(r'\b(IS\s+VERIZON|IS\s+T-MOBILE|IS\s+AT&T|A\s+SIGNIFICANT)\b', line)[0]
                meta["address"] = normalize_string(address_block)
                break
                
    return meta

# ==============================================================================
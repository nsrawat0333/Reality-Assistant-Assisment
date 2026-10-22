import json
import time
import streamlit as st
from pdf_utils import (
    extract_text, pdf_has_extractable_text,
    convert_pdf_pages_to_images, open_image,
)
from extractor import extract_property_info, extract_property_info_from_images, result_to_flat_json

st.set_page_config(
    page_title="Property Brochure Intelligence Extractor",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .hero-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(48, 43, 99, 0.3);
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        inset: -50%;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
        animation: shimmer 8s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% { transform: translate(-30%, -30%); }
        50%       { transform: translate(30%, 30%); }
    }
    .hero-header h1 { color: #fff; font-size: 2.2rem; font-weight: 800; margin: 0; letter-spacing: -0.02em; position: relative; z-index: 1; }
    .hero-header p  { color: rgba(255,255,255,0.7); font-size: 1.05rem; margin-top: 0.5rem; position: relative; z-index: 1; }

    .glass-card {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-card:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.2); }

    .badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: .75rem; font-weight: 600; letter-spacing: .03em; text-transform: uppercase; }
    .badge-high            { background: linear-gradient(135deg, #00b09b, #96c93d); color: #fff; }
    .badge-medium          { background: linear-gradient(135deg, #f7971e, #ffd200); color: #1a1a2e; }
    .badge-low             { background: linear-gradient(135deg, #ff416c, #ff4b2b); color: #fff; }
    .badge-not_found       { background: linear-gradient(135deg, #636e72, #b2bec3); color: #fff; }
    .badge-reviewer_edited { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: #fff; }

    .section-title { font-size: 1.3rem; font-weight: 700; color: #e0e0e0; margin-bottom: 1rem; padding-bottom: .5rem; border-bottom: 2px solid rgba(255,255,255,0.1); }
    .field-label   { font-size: .85rem; font-weight: 600; color: #a0a0b0; text-transform: uppercase; letter-spacing: .05em; margin-bottom: .25rem; }

    .stat-card   { background: linear-gradient(135deg, rgba(99,102,241,.15), rgba(168,85,247,.15)); border: 1px solid rgba(99,102,241,.2); border-radius: 12px; padding: 1rem 1.25rem; text-align: center; }
    .stat-number { font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-label  { font-size: .8rem; color: #a0a0b0; text-transform: uppercase; letter-spacing: .05em; margin-top: .25rem; }

    .step-item    { display: flex; align-items: center; padding: .6rem 1rem; margin: .3rem 0; border-radius: 10px; font-size: .95rem; }
    .step-done    { background: rgba(0,176,155,.1);   border-left: 3px solid #00b09b; color: #a0f0d0; }
    .step-active  { background: rgba(99,102,241,.15); border-left: 3px solid #818cf8; color: #c0c0ff; animation: pulse 1.5s ease-in-out infinite; }
    .step-pending { background: rgba(255,255,255,.03); border-left: 3px solid #444;   color: #555; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .6; } }

    .history-item { background: rgba(255,255,255,.05); border-radius: 8px; padding: .6rem .8rem; margin: .3rem 0; border-left: 3px solid #818cf8; font-size: .85rem; color: #c0c0d0; }

    .method-badge { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: .8rem; font-weight: 600; margin-right: .5rem; }
    .method-text   { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
    .method-vision { background: linear-gradient(135deg, #f093fb, #f5576c); color: #fff; }

    [data-testid="stFileUploader"] { border: 2px dashed rgba(255,255,255,.15); border-radius: 16px; padding: 1rem; }
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <h1>🏢 Property Brochure Intelligence Extractor</h1>
    <p>Upload a property brochure PDF or image — AI extracts key details instantly</p>
</div>
""", unsafe_allow_html=True)

FIELD_LABELS = {
    "project_name":    "🏗️ Project Name",
    "developer_name":  "🏭 Developer / Builder",
    "location_address":"📍 Location / Address",
    "price_range":     "💰 Price / Price Range",
    "unit_types":      "🏠 Unit Types",
    "area":            "📐 Area / Size",
    "amenities":       "🏊 Amenities",
    "possession_date": "📅 Possession Date",
    "rera_number":     "🔖 RERA Number",
    "total_units":     "🏢 Total Units",
}

# ── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.markdown("---")
    st.markdown("**AI Model:** Gemini 3.8 Flash")
    st.markdown("**Formats:** PDF, JPG, PNG")
    st.markdown("**Mode:** Text + Vision (auto)")
    st.markdown("---")
    st.markdown("### 📋 How It Works")
    st.markdown("1. **Upload** a property brochure\n2. **AI extracts** key fields\n3. **Review & correct** values\n4. **Download** structured JSON")
    st.markdown("---")
    st.markdown("### 🧪 Testing")
    if st.button("🔧 Generate Sample PDFs", use_container_width=True):
        try:
            from create_samples import create_brochure_skyline, create_brochure_greenview, create_sample_outputs
            create_brochure_skyline()
            create_brochure_greenview()
            create_sample_outputs()
            st.success("✅ Samples created in `sample_inputs/`")
        except Exception as e:
            st.error(f"Failed: {e}")
    st.markdown("---")
    st.markdown("### 📜 Recent Extractions")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-5:]):
            icon = "👁️" if h["mode"] == "vision" else "📝"
            st.markdown(
                f'<div class="history-item">{icon} <b>{h["name"]}</b><br>'
                f'<span style="color:#888;font-size:.75rem">{h["found"]}/{h["total"]} fields found</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No extractions yet.")
    st.markdown("---")
    st.markdown('<p style="color:#666;font-size:.8rem">Built for Realty Assistant Pvt. Ltd.</p>', unsafe_allow_html=True)

# ── Upload ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📤 Upload Brochure</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Drag and drop your property brochure here",
    type=["pdf", "jpg", "jpeg", "png"],
    key="brochure_upload",
)

if not uploaded_file:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:3rem">
        <p style="font-size:3rem;margin:0">📄</p>
        <p style="font-size:1.1rem;color:#aaa;margin-top:.5rem">Upload a property brochure to get started</p>
        <p style="font-size:.85rem;color:#666">Supports PDF, JPG, JPEG, PNG</p>
        <p style="font-size:.8rem;color:#555;margin-top:1rem">💡 <em>Use the sidebar to generate sample test PDFs</em></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

file_bytes = uploaded_file.read()
file_name  = uploaded_file.name
ext        = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""

# decide extraction mode
is_image   = ext in ("jpg", "jpeg", "png", "bmp", "tiff", "webp")
use_vision = is_image or (ext == "pdf" and not pdf_has_extractable_text(file_bytes))

if use_vision:
    st.markdown(
        '<span class="method-badge method-vision">👁️ Vision Mode</span>'
        '<span style="color:#aaa;font-size:.85rem">Gemini reads the image directly</span>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<span class="method-badge method-text">📝 Text Mode</span>'
        '<span style="color:#aaa;font-size:.85rem">pdfplumber extracts text → Gemini analyzes</span>',
        unsafe_allow_html=True,
    )

# ── Processing ───────────────────────────────────────────────────────────────────
steps_placeholder = st.empty()

def show_steps(active):
    labels = [("📄", "Reading file"), ("🔍", "Extracting content"), ("🤖", "AI analyzing"), ("✅", "Done")]
    html = ""
    for i, (icon, label) in enumerate(labels):
        if i < active:    css, suffix = "step-done",    "✓"
        elif i == active: css, suffix = "step-active",  "..."
        else:             css, suffix = "step-pending",  ""
        html += f'<div class="step-item {css}">{icon} {label} {suffix}</div>'
    steps_placeholder.markdown(html, unsafe_allow_html=True)

show_steps(0)
show_steps(1)

images   = []
raw_text = ""

if use_vision:
    images = [open_image(file_bytes)] if is_image else convert_pdf_pages_to_images(file_bytes, max_pages=5)
    if not images:
        st.error("❌ Could not extract images from the file.")
        st.stop()
    raw_text = f"[{len(images)} page(s) sent to Gemini Vision]"
else:
    try:
        raw_text = extract_text(file_bytes, file_name)
    except Exception as e:
        st.error(f"❌ Text extraction failed: {e}")
        st.stop()

    # fallback to Vision if PDF had no selectable text
    if not raw_text.strip():
        st.warning("⚠️ No text found — switching to Vision mode...")
        use_vision = True
        images   = convert_pdf_pages_to_images(file_bytes, max_pages=5)
        raw_text = f"[{len(images)} page(s) sent to Gemini Vision]"

show_steps(2)

try:
    result = extract_property_info_from_images(images) if use_vision else extract_property_info(raw_text)
except Exception as e:
    st.error(f"❌ AI extraction failed: {e}")
    st.stop()

show_steps(3)
time.sleep(0.4)
steps_placeholder.empty()

# ── Stats ────────────────────────────────────────────────────────────────────────
fields    = [k for k in result if not k.startswith("_")]
found     = sum(1 for f in fields if result[f].get("confidence") != "not_found")
high_conf = sum(1 for f in fields if result[f].get("confidence") == "high")
uncertain = sum(1 for f in fields if result[f].get("confidence") in ("low", "medium"))

st.session_state.history.append({
    "name": file_name, "found": found,
    "total": len(fields), "mode": "vision" if use_vision else "text",
})

st.markdown("---")
st.markdown('<div class="section-title">📊 Extraction Summary</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
for col, num, label in [(c1, len(fields), "Total Fields"), (c2, found, "Found"), (c3, high_conf, "High Confidence"), (c4, uncertain, "Needs Review")]:
    col.markdown(
        f'<div class="stat-card"><div class="stat-number">{num}</div><div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

# ── Editable Results ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">✏️ Review & Edit Extracted Data</div>', unsafe_allow_html=True)
st.caption("All fields are editable — correct anything before exporting.")

edited_result = {}

for field_key, field_label in FIELD_LABELS.items():
    if field_key not in result:
        continue

    val  = result[field_key].get("value", "Not found")
    conf = result[field_key].get("confidence", "not_found")

    col_label, col_badge = st.columns([4, 1])
    col_label.markdown(f'<div class="field-label">{field_label}</div>', unsafe_allow_html=True)
    col_badge.markdown(f'<span class="badge badge-{conf}">{conf}</span>', unsafe_allow_html=True)

    widget    = st.text_area if field_key == "amenities" else st.text_input
    kwargs    = {"height": 80} if field_key == "amenities" else {}
    new_value = widget(label=field_key, value=val, key=f"edit_{field_key}", label_visibility="collapsed", **kwargs)

    edited_result[field_key] = {
        "value": new_value,
        "confidence": conf if new_value == val else "reviewer_edited",
    }

# ── Export ────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">📥 Export</div>', unsafe_allow_html=True)

detailed_json = json.dumps(edited_result, indent=2, ensure_ascii=False)
flat_json     = json.dumps(result_to_flat_json(edited_result), indent=2, ensure_ascii=False)
base_name     = file_name.rsplit(".", 1)[0]

col_a, col_b = st.columns(2)
col_a.download_button("⬇️ Download Detailed JSON", detailed_json, f"{base_name}_extracted.json", "application/json", use_container_width=True)
col_b.download_button("⬇️ Download Simple JSON",   flat_json,     f"{base_name}_simple.json",    "application/json", use_container_width=True)

st.markdown("##### 📋 Copy JSON")
st.code(detailed_json, language="json")

with st.expander("📄 Raw Extracted Text"):
    st.text(raw_text)

with st.expander("ℹ️ Extraction Details"):
    st.markdown(f"**Mode:** {'Gemini Vision (multimodal)' if use_vision else 'pdfplumber + Gemini'}")
    st.markdown(f"**File:** `{file_name}`")
    st.markdown(f"**Fields found:** {found}/{len(fields)}")
    if use_vision and images:
        st.markdown(f"**Pages sent to Gemini:** {len(images)}")

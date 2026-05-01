import streamlit as st
import pandas as pd
import anthropic
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP MODELS & CLIENT ---
# Updated to current active model versions (May 2026)
SONNET_MODEL = "claude-sonnet-4-6"  # High-level synthesis for Baselines
HAIKU_MODEL = "claude-haiku-4-5"    # Rapid response for Troubleshooting

try:
    client = anthropic.Anthropic(api_key=st.secrets["CLAUDE_KEY"])
except Exception:
    st.error("Missing CLAUDE_KEY in Streamlit Secrets!")
    st.stop()

# --- 2. DATA CONNECTIONS & HELPER FUNCTIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_technical_manuals():
    """Reads external TXT files from the /knowledge directory"""
    # Note: Ensure these files exist in a folder named 'knowledge'
    paths = ["knowledge/quick_guide.txt", "knowledge/settings_guide.txt"]
    combined_knowledge = ""
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                combined_knowledge += f"\n--- {path.upper()} ---\n{f.read()}\n"
    return combined_knowledge if combined_knowledge else "Technical manuals not found in /knowledge folder."

def clear_and_reset():
    """Clears session data for a fresh analysis"""
    keys_to_delete = ['current_ai_response', 'last_issue', 'standardized_issue', 'formatted_settings', 'current_baseline']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.toast("System Reset")

def log_to_google_sheets(software, machine, issue, settings, notes):
    """Appends successful calibration data to Google Sheets"""
    try:
        existing_data = conn.read()
        new_entry = pd.DataFrame([{
            "machine": machine,
            "software": software,
            "issue": issue,
            "settings": settings,
            "notes": notes if notes.strip() != "" else "none"
        }])
        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"DATABASE ERROR: {e}")
        return False

def get_ai_baseline(software, machine, df, knowledge):
    """Uses SONNET to analyze past successful logs and create a smart baseline"""
    history = df[(df['software'] == software) & (df['machine'] == machine)]
    past_data = history.tail(10).to_string(index=False) if not history.empty else "No previous successful logs found."
    
    baseline_prompt = f"""
    You are a Senior Dental Imaging Specialist. 
    Task: Synthesize a "Gold Standard" baseline for: {software} | {machine}.
    
    KNOWLEDGE BASE RULES:
    {knowledge}
    
    PAST SUCCESSFUL LOGS (Evidence):
    {past_data}
    
    Requirements:
    1. If history exists, find the common successful settings.
    2. If no history exists, use the Knowledge Base to define the best starting point.
    3. Return ONLY the settings list. Be extremely concise.
    """
    try:
        response = client.messages.create(
            model=SONNET_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": baseline_prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        # Debug helper: shows the actual error if the AI call fails
        return f"Synthesis Error: {str(e)}"

# --- 3. LOAD DATA & ASSETS ---
knowledge_context = load_technical_manuals()
try:
    df_baseline = pd.read_csv("iq_settings.csv")
except:
    df_baseline = pd.DataFrame(columns=['machine', 'software', 'issue', 'settings', 'notes'])

# --- 4. UI CONFIGURATION ---
st.set_page_config(page_title="Jazz AI Image quality", page_icon="🦷")

st.markdown(
    """
    <style>
    div[data-testid="stTextArea"] textarea { background-color: #e7e5f5 !important; border: 2px solid #ce93d8 !important; color: #4a148c !important; }
    blockquote { border-left: 5px solid #ce93d8 !important; background-color: #f8f9fa !important; padding: 10px 15px !important; color: #4a148c !important; border-radius: 4px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🦷 Jazz AI Image Quality Assistant")

# --- 5. SIDEBAR: SETUP ---
st.sidebar.header("Initial Setup")
machine = st.sidebar.selectbox("X-ray Source", ["Select...", "Wall-mounted", "Hand-held"], index=0)

software_options = ["Select..."] + sorted([
    "CDR DICOM", "Carestream", "Dentrix Ascend", "DEXIS", "Eaglesoft", "Sidexis", "Vixwin", 
    "XDR", "Edge Cloud", "Curve Hero", "Planmeca Romexis", "Oryx", "Tigerview", "Tracker", 
    "iDental", "Clio", "DTX Studio", "SOTA", "EzDent-i", "Open Dental", "Tab32", "SOPRO", 
    "Mipacs", "Denticon XV Capture", "Denticon XV Web", "CliniView", "Dentiray Capture", 
    "Imaging XL", "Prof. Suni", "Xray Vision", "SIGMA", "PatientGallery", "Xelis Dental", 
    "Overjet", "Aeka", "CLASSIC", "Archy", "OTHER", "Harmony"
])
software = st.sidebar.selectbox("Imaging Software", software_options, index=0)
st.sidebar.caption("v1.0.1 | Jazz AI Support")

# --- 6. MAIN LOGIC FLOW ---
if software == "Select..." or machine == "Select...":
    st.info("👈 Please select the setup on the sidebar to begin.")
else:
    # --- STEP 1: SMART BASELINE ---
    if 'current_baseline' not in st.session_state or st.session_state.get('last_setup') != f"{software}-{machine}":
        with st.spinner("AI is synthesizing a smart baseline..."):
            st.session_state['current_baseline'] = get_ai_baseline(software, machine, df_baseline, knowledge_context)
            st.session_state['last_setup'] = f"{software}-{machine}"

    st.markdown(f"""
        <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;">
            <h3 style="color: #155724; margin: 0;">📍 Recommended Baseline</h3>
            <p style="color: #155724; font-size: 1.1em; margin-top: 10px;">{st.session_state['current_baseline']}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- STEP 2: REFINEMENT ---
    st.markdown("---")
    st.markdown("### 🛠️ Refine Image Quality")
    user_feedback = st.text_area("Describe the issue:", placeholder="e.g., 'Image is too dark'...")

    if st.button("Analyze Image Issue"):
        if user_feedback:
            with st.spinner("Analyzing with Haiku..."):
                prompt = f"""
                <knowledge_base>{knowledge_context}</knowledge_base>
                Task: Troubleshoot {software} | {machine}.
                Current Baseline: {st.session_state['current_baseline']}
                User Feedback: {user_feedback}
                
                Constraints:
                1. STEADY STATE: Suggest 5-10% increments only.
                2. ADAPTIVE NORMALIZATION: Value N = N% of data levels removed.
                3. FORMAT: **Issue**, then numbered **Actions**.
                
                LOG_ISSUE: [Tag]
                LOG_SETTINGS: [Settings string]
                """
                try:
                    response = client.messages.create(
                        model=HAIKU_MODEL,
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state['current_ai_response'] = response.content[0].text
                except Exception as e:
                    st.error(f"Analysis Error: {str(e)}")

    if 'current_ai_response' in st.session_state:
        st.success(st.session_state['current_ai_response'])
        

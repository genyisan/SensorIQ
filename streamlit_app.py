import streamlit as st
import pandas as pd
import anthropic
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP MODELS & CLIENT ---
# Strategic dual-model setup
SONNET_MODEL = "claude-sonnet-4-6" # High-level synthesis for Baselines
HAIKU_MODEL = "claude-haiku-4-5" # Rapid response for Troubleshooting

try:
    client = anthropic.Anthropic(api_key=st.secrets["CLAUDE_KEY"])
except Exception:
    st.error("Missing CLAUDE_KEY in Streamlit Secrets!")
    st.stop()

# --- 2. DATA CONNECTIONS & HELPER FUNCTIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_technical_manuals():
    """Reads external TXT files from the /knowledge directory to ground the AI"""
    paths = ["knowledge/quick_guide.txt", "knowledge/settings_guide.txt"]
    combined_knowledge = ""
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                combined_knowledge += f"\n--- {path.upper()} ---\n{f.read()}\n"
    return combined_knowledge if combined_knowledge else "Technical manuals not found."

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
    # Filter for exact matches in the logs
    history = df[(df['software'] == software) & (df['machine'] == machine)]
    past_data = history.tail(10).to_string(index=False) if not history.empty else "No previous successful logs found for this setup."
    
    baseline_prompt = f"""
    You are a Senior Dental Imaging Specialist. 
    Task: Synthesize a "Gold Standard" baseline for: {software} | {machine}.
    
    KNOWLEDGE BASE RULES:
    {knowledge}
    
    PAST SUCCESSFUL LOGS (Use these as evidence):
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
    except:
        return "Generic manufacturer defaults."

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
    div[data-testid="stTextInput"] input { background-color: #e7e5f5 !important; border: 2px solid #ce93d8 !important; color: #4a148c !important; }
    blockquote { border-left: 5px solid #ce93d8 !important; background-color: #f8f9fa !important; padding: 10px 15px !important; color: #4a148c !important; border-radius: 4px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🦷 Jazz AI Image Quality Assistant")

# --- 5. SIDEBAR: SETUP ---
st.sidebar.header("Initial Setup")
machine_options = ["Select...", "Wall-mounted", "Hand-held"]
machine = st.sidebar.selectbox("X-ray Source", machine_options, index=0)

software_options = ["Select..."] + sorted([
    "CDR DICOM", "Carestream", "Dentrix Ascend", "DEXIS", "Eaglesoft", "Sidexis", "Vixwin", 
    "XDR", "Edge Cloud", "Curve Hero", "Planmeca Romexis", "Oryx", "Tigerview", "Tracker", 
    "iDental", "Clio", "DTX Studio", "SOTA", "EzDent-i", "Open Dental", "Tab32", "SOPRO", 
    "Mipacs", "Denticon XV Capture", "Denticon XV Web", "CliniView", "Dentiray Capture", 
    "Imaging XL", "Prof. Suni", "Xray Vision", "SIGMA", "PatientGallery", "Xelis Dental", 
    "Overjet", "Aeka", "CLASSIC", "Archy", "OTHER", "Harmony"
])
software = st.sidebar.selectbox("Imaging Software", software_options, index=0)

st.sidebar.markdown("---") 
st.sidebar.link_button("🚀 Submit Feedback", "https://www.notion.so/jazzsupport/345f0a2e8ff5807d8f24d9a86bf4e742?v=345f0a2e8ff58080ae22000c286546a3", use_container_width=True)
st.sidebar.caption("v1.0.0 | Jazz AI Support")

# --- 6. MAIN LOGIC FLOW ---
if software == "Select..." or machine == "Select...":
    st.markdown("""
        <div style="text-align: center; margin-top: 100px;">
            <h1 style="font-size: 3.5em; margin-bottom: 0;">👈 Start Here</h1>
            <p style="font-size: 1.5em; color: #666;">
                Please select the <b>X-ray Source</b> and <b>Imaging Software</b> <br>on the sidebar to begin.
            </p>
        </div>
    """, unsafe_allow_html=True)
else:
    # --- STEP 1: SMART BASELINE ---
    st.divider()
    
    # Synthesize baseline only if we haven't already for this selection
    if 'current_baseline' not in st.session_state:
        with st.spinner("AI is synthesizing a smart baseline from success history..."):
            st.session_state['current_baseline'] = get_ai_baseline(software, machine, df_baseline, knowledge_context)

    st.markdown(f"""
        <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;">
            <h3 style="color: #155724; margin: 0;">📍 STEP 1: Apply Recommended Baseline</h3>
            <p style="color: #155724; font-size: 1.1em; margin-top: 10px;">
                <b>AI Synthesis of successful cases:</b><br>{st.session_state['current_baseline']}
            </p>
            <p style="color: #155724; font-size: 0.9em;">
                <i>Try these settings first. If the image needs more work, use Step 2 below.</i>
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.write("") 

    # --- STEP 2: REFINEMENT ---
    st.markdown("---")
    st.markdown("### 🛠️ STEP 2: Refine Image Quality")
    st.info("**Instructions:** If the baseline isn't perfect, describe the issue below. The AI will suggest **gradual** adjustments.")

    user_feedback = st.text_area(
        label="Describe the image issue:", 
        height=150, 
        placeholder="e.g., 'The posterior images are still a bit too dark'..."
    )

    if st.button("Analyze Image Issue"):
        if user_feedback:
            with st.spinner("Analyzing with Haiku..."):
                apteryx_software = ["Dentiray", "Harmony", "Imaging XL", "Denticon XV Capture", "Denticon XV Web"]
                is_apteryx = any(brand.lower() in software.lower() for brand in apteryx_software)
                
                prompt = f"""
                <knowledge_base>
                {knowledge_context}
                </knowledge_base>

                <task>
                Troubleshoot: {software} | {machine}.
                Current Baseline: {st.session_state['current_baseline']}
                User Feedback: {user_feedback}
                </task>

                <constraints>
                1. STEADY STATE RULE: Suggest adjustments in steady, gradual increments (5-10% changes). No extreme jumps unless the user says "unusable."
                
                2. ADAPTIVE NORMALIZATION (AN) LOGIC:
                   - AN is a "Data Removal" tool.
                   - Low Percentile = Removes Dips (Shadows/Dark Data).
                   - High Percentile = Removes Peaks (Highlights/Bright Data).
                   - Setting a value of 'N' removes N% of those specific data levels.
                   - Recommendation MUST state: "Set [Low/High] Percentile to [N] to remove [N]% of data levels."

                3. APTERYX LOGIC:
                   {"- DEVICE DETECTED: Note that values are REVERSED (higher % = more data cut off)." if is_apteryx else ""}
                
                4. FORMAT: **Issue**, followed by a numbered list of **Actions**. NO conversational filler.

                At the very bottom, include:
                LOG_ISSUE: [Standardized tag: dark, grainy, low contrast, etc.]
                LOG_SETTINGS: [Feature: Enabled (Param: Value)]
                </constraints>
                """

                try:
                    response = client.messages.create(
                        model=HAIKU_MODEL,
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    full_text = response.content[0].text
                    
                    # Parse tags
                    main_advice = []
                    log_issue = "general"
                    log_settings = "none"
                    for line in full_text.split('\n'):
                        if "LOG_ISSUE:" in line: log_issue = line.split("LOG_ISSUE:")[1].strip()
                        elif "LOG_SETTINGS:" in line: log_settings = line.split("LOG_SETTINGS:")[1].strip()
                        else: main_advice.append(line)
                    
                    st.session_state['current_ai_response'] = "\n".join(main_advice).strip()
                    st.session_state['standardized_issue'] = log_issue
                    st.session_state['formatted_settings'] = log_settings
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- 8. RESULTS & LOGGING ---
    if 'current_ai_response' in st.session_state:
        st.success(f"**Jazz Support AI Advice:** \n\n {st.session_state['current_ai_response']}")
        
        st.divider()
        st.write("### 📝 Finalize Log Entry")
        tech_notes = st.text_input("Add tech notes (e.g., 'Client happy'):", placeholder="none")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Log Success", key="log_btn"):
                with st.spinner("Logging..."):
                    if log_to_google_sheets(software, machine, st.session_state['standardized_issue'], st.session_state['formatted_settings'], tech_notes):
                        st.toast("✅ Success Logged!")
                        clear_and_reset()
                        st.rerun()
        with col2:
            if st.button("🔄 Clear & Start Over", key="clear_btn"):
                clear_and_reset()
                st.rerun()

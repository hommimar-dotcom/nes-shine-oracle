
import streamlit as st
import os
import time
import json
from agents import OracleBrain
from utils import create_pdf
from prompts import HTML_TEMPLATE_START, HTML_TEMPLATE_END
from memory import MemoryManager # Explicit import
import google.generativeai as genai
import pandas as pd

# INIT MEMORY MANAGER (GLOBAL WITH CACHE)
@st.cache_resource
def get_memory_manager():
    return MemoryManager()

mem_mgr = get_memory_manager()

# SET PAGE CONFIG
st.set_page_config(
    page_title="Nes Shine // Sovereign Engine",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# STYLING: THE SOVEREIGN CONSOLE THEME
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    /* THEME VARIABLES */
    :root {
        --primary-bg: #050505;
        --primary-gold: #d4af37;
        --primary-scarlet: #7b0000;
        --text-silver: #e0e0e0;
    }
    
    /* CRIMSON THEME */
    [data-theme="crimson"] {
        --primary-bg: #0a0000;
        --primary-gold: #ff6b6b;
        --primary-scarlet: #cc0000;
    }
    
    /* MOONLIGHT THEME */
    [data-theme="moonlight"] {
        --primary-bg: #000510;
        --primary-gold: #a8c5e0;
        --primary-scarlet: #4a5f7f;
    }

    /* BASE THEME WITH TEXTURE */
    .stApp {
        background: 
            radial-gradient(circle at 50% 50%, rgba(30, 0, 0, 0.4) 0%, rgba(5, 5, 5, 1) 100%),
            repeating-linear-gradient(0deg, rgba(0,0,0,0.1) 0px, transparent 1px, transparent 2px, rgba(0,0,0,0.1) 3px),
            var(--primary-bg);
        color: var(--text-silver);
        font-family: 'Inter', sans-serif;
    }
    
    /* INPUT FIELDS (TERMINAL STYLE WITH GLOW) */
    .stTextArea textarea, .stTextInput input {
        background-color: #0c0c0c;
        color: var(--primary-gold);
        border: 1px solid #333;
        border-left: 3px solid var(--primary-scarlet);
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        border-radius: 0px;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--primary-gold);
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
        outline: none;
    }
    
    /* HEADERS WITH GRADIENT */
    h1 {
        font-family: 'Cinzel', serif !important;
        background: linear-gradient(135deg, var(--primary-gold) 0%, var(--primary-scarlet) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-transform: uppercase;
        letter-spacing: 3px;
        font-weight: 700;
        text-shadow: 0 0 30px rgba(212, 175, 55, 0.5);
        filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.4));
    }
    
    h2, h3, .stSidebar .css-17lntkn {
        font-family: 'Cinzel', serif !important;
        color: var(--primary-gold) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 400;
        text-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
    }
    
    /* BUTTONS (COMMAND PROTOCOL WITH HOVER ANIMATION) */
    .stButton button {
        background-color: #0f0f0f;
        color: var(--primary-gold);
        border-radius: 0px;
        border: 1px solid #333;
        font-family: 'Cinzel', serif;
        letter-spacing: 3px;
        text-transform: uppercase;
        padding: 15px 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .stButton button:hover {
        border-color: var(--primary-gold);
        background-color: #1a1a1a;
        color: #fff;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3);
    }
    .stButton button:active {
        transform: translateY(0px);
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #000000 0%, #0a0000 100%);
        border-right: 1px solid #1a1a1a;
    }
    
    /* METRICS STYLING */
    [data-testid="stMetricValue"] {
        font-family: 'Cinzel', serif;
        color: var(--primary-gold);
        font-size: 28px;
    }
    
    /* ALERTS & STATUS WITH PULSING ANIMATION */
    .stAlert {
        background-color: #111;
        border: 1px solid #333;
        color: #aaa;
        font-family: 'Inter', sans-serif;
    }
    
    /* ANIMATED STATUS MESSAGES */
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.7; text-shadow: 0 0 10px rgba(212, 175, 55, 0.5); }
        50% { opacity: 1; text-shadow: 0 0 20px rgba(212, 175, 55, 0.8); }
    }
    
    .stMarkdown code {
        animation: pulse-glow 2s ease-in-out infinite;
        color: var(--primary-gold);
    }
    
    /* RADIO BUTTONS */
    .stRadio div [role='radiogroup'] {
        font-family: 'Inter', sans-serif;
        color: #888;
    }
    
    /* SELECTBOX HOVER */
    .stSelectbox div[data-baseweb="select"] {
        transition: all 0.3s ease;
    }
    .stSelectbox div[data-baseweb="select"]:hover {
        border-color: var(--primary-gold) !important;
    }
    
    /* REMOVE DEFAULT STREAMLIT DECORATION */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;} */
    
    /* MOBILE RESPONSIVE */
    @media (max-width: 768px) {
        .stApp {
            padding: 10px;
        }
        h1 {
            font-size: 24px !important;
            letter-spacing: 2px;
        }
        h2, h3 {
            font-size: 18px !important;
        }
        .stButton button {
            padding: 12px 0;
            font-size: 12px;
            letter-spacing: 2px;
        }
        .stTextArea textarea, .stTextInput input {
            font-size: 12px;
        }
        [data-testid="stMetricValue"] {
            font-size: 20px;
        }
    }
    
</style>
""", unsafe_allow_html=True)

# ==================== LOGIN GATE ====================
import extra_streamlit_components as stx
import datetime

@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()
time.sleep(0.1) # Small delay for CookieManager initialization

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 1. AUTO-LOGIN CHECK (Remember Me)
if not st.session_state.authenticated:
    try:
        auth_token = cookie_manager.get(cookie="nesshine_auth_token")
        correct_pass = mem_mgr.load_settings().get("app_password", os.environ.get("APP_PASSWORD", "nesshine2026"))
        if auth_token and auth_token == correct_pass:
            st.session_state.authenticated = True
    except:
        pass

# 2. LOGIN UI (If auto-login failed)
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_login = st.columns([1, 2, 1])[1]
    with col_login:
        st.markdown("<h1 style='text-align:center; color:#d4af37;'>NES SHINE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666;'>Sovereign Engine Access</p>", unsafe_allow_html=True)
        login_pass = st.text_input("🔑 ACCESS CODE", type="password", placeholder="Enter system password...")
        remember_me = st.checkbox("Remember this device (30 Days)", value=True)
        
        if st.button("AUTHENTICATE", use_container_width=True, type="primary"):
            correct_pass = mem_mgr.load_settings().get("app_password", os.environ.get("APP_PASSWORD", "nesshine2026"))
            if login_pass == correct_pass:
                st.session_state.authenticated = True
                if remember_me:
                    # Set cookie for 30 days
                    cookie_manager.set("nesshine_auth_token", correct_pass, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.rerun()
            else:
                st.error("ACCESS DENIED.")
    st.stop()

# ==================== API KEY ROTATION ====================
# We no longer rely strictly on ENV vars for rotation if they are set via UI
def get_active_api_key():
    """Fallback method if UI keys aren't loaded yet."""
    keys = [
        os.environ.get("GEMINI_KEY_1", ""),
        os.environ.get("GEMINI_KEY_2", ""),
        os.environ.get("GEMINI_KEY_3", ""),
    ]
    for i, key in enumerate(keys):
        if key.strip():
            return key.strip(), i + 1
    return None, 0

api_key, active_key_num = get_active_api_key()

# SIDEBAR: SYSTEM CONFIGURATION
with st.sidebar:
    st.markdown("## SYSTEM CONFIGURATION")
    
    # Load saved settings from Supabase (once per session)
    if "app_settings_loaded" not in st.session_state:
        saved_settings = mem_mgr.load_settings()
        # Ensure we always deal with a list of keys
        st.session_state.saved_keys = saved_settings.get("api_keys", [])
        st.session_state.app_settings_loaded = True
    
    # FORMAT CURRENT KEYS FOR TEXT AREA
    current_keys_text = "\n".join([k for k in st.session_state.saved_keys if k.strip()])
    
    # API KEY MANAGEMENT (Infinite Keys)
    with st.expander("🔑 API KEY MANAGEMENT", expanded=not any(st.session_state.saved_keys)):
        st.caption("Paste your API keys below (one per line). The system will infinitely rotate through them if rate limits are hit.")
        keys_input = st.text_area("API KEYS", value=current_keys_text, height=150, placeholder="AIzaSy...\nAIzaSy...\nAIzaSy...")
        
        if st.button("💾 SAVE KEYS", key="save_keys_btn", use_container_width=True):
            # Parse lines into a list, stripping whitespace
            new_keys = [k.strip() for k in keys_input.split('\n') if k.strip()]
            st.session_state.saved_keys = new_keys
            # Save to Supabase permanently
            settings = mem_mgr.load_settings()
            settings["api_keys"] = new_keys
            if mem_mgr.save_settings(settings):
                st.success(f"✅ {len(new_keys)} Keys saved permanently.")
            else:
                st.warning("Saved for this session only.")
            time.sleep(1)
            st.rerun()
            
    # SECURITY & PASSWORD MANAGEMENT
    with st.expander("🛡️ SECURITY & ACCESS", expanded=False):
        st.caption("Update the master system password to lock out unauthorized access.")
        new_pass_input = st.text_input("New Access Code", type="password")
        if st.button("UPDATE PASSWORD", use_container_width=True):
            if new_pass_input.strip():
                settings = mem_mgr.load_settings()
                settings["app_password"] = new_pass_input.strip()
                if mem_mgr.save_settings(settings):
                    st.success("✅ Password Updated!")
                    # Update current cookie to prevent immediate lockout
                    cookie_manager.set("nesshine_auth_token", new_pass_input.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Database save failed.")
            else:
                st.warning("Password cannot be blank.")
    
    # Determine active API keys (COLLECT ALL VALID KEYS)
    valid_keys = [k.strip() for k in st.session_state.saved_keys if k and k.strip()]
    api_key = valid_keys[0] if valid_keys else None
    active_key_num = len(valid_keys)
    
    if api_key:
        st.success(f"🔑 {len(valid_keys)} ACTIVE KEYS READY (ROTATION ENABLED)")
    else:
        st.error("⚠️ NO API KEYS SET")
    
    # Logout button
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    st.markdown("---")
    
    # STATS DASHBOARD
    st.markdown("### SYSTEM METRICS")
    
    # Calculate stats
    archive_dir = "saved_readings"
    memory_dir = "client_memories"
    
    total_readings = len(os.listdir(archive_dir)) if os.path.exists(archive_dir) else 0
    total_clients = len(os.listdir(memory_dir)) if os.path.exists(memory_dir) else 0
    
    # Display in clean format
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("READINGS", total_readings)
    with col_b:
        st.metric("CLIENTS", total_clients)
    
    st.markdown("---")
    
    # API COST TRACKER
    st.markdown("### 💰 API COST TRACKER")
    
    # Date picker for cost filtering
    import datetime as dt
    available_dates = mem_mgr.get_usage_date_range()
    
    cost_view = st.radio("VIEW", ["TODAY", "SELECT DATE", "ALL TIME"], horizontal=True, key="cost_view_radio", label_visibility="collapsed")
    
    if cost_view == "TODAY":
        import pytz
        ny_tz = pytz.timezone('America/New_York')
        today_str = dt.datetime.now(ny_tz).strftime("%Y-%m-%d")
        usage = mem_mgr.get_usage_stats(date_filter=today_str)
        date_label = "TODAY"
    elif cost_view == "SELECT DATE":
        if available_dates:
            selected_date = st.selectbox("DATE", available_dates, key="cost_date_select", label_visibility="collapsed")
            usage = mem_mgr.get_usage_stats(date_filter=selected_date)
            date_label = selected_date
        else:
            usage = mem_mgr.get_usage_stats()
            date_label = "NO DATA"
    else:
        usage = mem_mgr.get_usage_stats()
        date_label = "ALL TIME"
    
    st.caption(f"📅 {date_label}")
    cost_c1, cost_c2 = st.columns(2)
    with cost_c1:
        st.metric("COST (USD)", f"${usage['total_cost']:.4f}")
    with cost_c2:
        st.metric("READINGS", usage['total_readings'])
    
    tok_c1, tok_c2 = st.columns(2)
    with tok_c1:
        # Format tokens with K suffix
        total_k = usage['total_tokens'] / 1000
        st.metric("TOKENS", f"{total_k:.1f}K" if total_k > 0 else "0")
    with tok_c2:
        st.metric("API CALLS", usage['total_api_calls'])
    
    st.markdown("---")
    st.markdown("### CLIENT ARCHIVES")
    
    # List Saved Readings
    archive_dir = "saved_readings"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    # Search/Filter Mechanism for Scalability
    filter_text = st.text_input("SEARCH ARCHIVES", placeholder="Enter Client Name or Date...")
    
    all_files = sorted(os.listdir(archive_dir), reverse=True)
    if filter_text:
        files = [f for f in all_files if filter_text.lower() in f.lower()]
    else:
        files = all_files
        
    if files:
        selected_file = st.selectbox("SELECT RECORD FILE", files, label_visibility="collapsed")
        if selected_file:
            file_path = os.path.join(archive_dir, selected_file)
            with open(file_path, "rb") as f:
                st.download_button(
                    label="DOWNLOAD RECORD [PDF]",
                    data=f,
                    file_name=selected_file,
                    mime="application/pdf",
                    key="sidebar_download"
                )
    else:
        st.caption("NO RECORDS FOUND")

    st.markdown("---")
    
# MAIN INTERFACE
st.title("NES SHINE // ORACLE ENGINE v3.2")
st.markdown("---")

# TABS FOR SINGLE VS BATCH
tab1, tab2, tab3 = st.tabs(["SINGLE READING", "BATCH QUEUE", "CLIENT VAULT"])

# TAB 1: SINGLE READING (Original Interface)
with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    # LEFT COLUMN: INPUT PARAMETERS
    with col1:
        st.subheader("TARGET PARAMETERS")
        
        # CLIENT EMAIL (CRITICAL FOR MEMORY)
        client_email = st.text_input("CLIENT EMAIL", placeholder="e.g., jessica@gmail.com", help="Client's email address - ensures accurate memory tracking across sessions")
        
        order_note = st.text_area("CLIENT CONTEXT & NOTES", height=250, placeholder="Enter raw client data here...")
        reading_topic = st.text_area("QUERY FOCUS", height=100, placeholder="Specific subject of interrogation...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        length_choice = st.radio("DEPTH PROTOCOL", [
            "STANDARD DEPTH (8K CHARS)", 
            "GRANDMASTER DEPTH (13K CHARS)",
            "SOVEREIGN DEPTH (20K CHARS)"
        ], horizontal=False)
        
        if "SOVEREIGN" in length_choice:
            target_len = "20000"
        elif "GRANDMASTER" in length_choice:
            target_len = "13000"
        else:
            target_len = "8000"
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            generate_btn = st.button("INITIALIZE PROTOCOL", disabled=not api_key, use_container_width=True)
        with col_btn2:
            if st.button("ABORT & RESET", type="secondary", use_container_width=True):
                st.session_state.is_generating = False
                st.session_state.last_status = None
                st.rerun()
    
    # RIGHT COLUMN: SYSTEM OUTPUT
    with col2:
        st.subheader("SYSTEM OUTPUT")
        
        if "final_html" not in st.session_state:
            st.session_state.final_html = None
        if "pdf_path" not in st.session_state:
            st.session_state.pdf_path = None
        if "delivery_msg" not in st.session_state:
            st.session_state.delivery_msg = None
        if "last_status" not in st.session_state:
            st.session_state.last_status = None
        if "is_generating" not in st.session_state:
            st.session_state.is_generating = False
    
        # Show persisted status on rerun (survives page interactions)
        if st.session_state.last_status and not generate_btn:
            st.markdown(f"**SYSTEM STATUS:** `{st.session_state.last_status}`")
    
        if generate_btn and api_key:
            if not order_note or not reading_topic:
                st.error("MISSING INPUT PARAMETERS.")
            else:
                brain = OracleBrain(valid_keys)
                st.session_state.is_generating = True
                st.session_state.last_status = "INITIALIZING..."
                status_container = st.empty()
                
                try:
                    # 1. GENERATE TEXT
                    def update_status(msg):
                        # Clean status updates (No emojis)
                        clean_msg = msg.replace("🔮", "").replace("🛡️", "").replace("✅", "").replace("⚠️", "").replace("👁️", "").replace("🧠", "").replace("📝", "")
                        st.session_state.last_status = clean_msg.strip().upper()
                        status_container.markdown(f"**SYSTEM STATUS:** `{st.session_state.last_status}`")
                        # time.sleep(0.1)  # Removed sleep to make stream faster
                    
                    st.markdown("### 🔮 DIVINING PROTOCOL ACTIVE (Stand By)")
                    
                    raw_text, delivery_msg, usage_stats = brain.run_cycle(
                        order_note, 
                        reading_topic, 
                        client_email=client_email, 
                        target_length=target_len, 
                        progress_callback=update_status
                    )
                    
                    
                    st.session_state.delivery_msg = delivery_msg
                    st.session_state.last_usage = usage_stats
                    
                    # 2. FORMAT HTML
                    update_status("COMPILING HTML ARCHITECTURE...")
                    final_content = raw_text
                    
                    # Validation Logic
                    if "<!DOCTYPE html>" not in raw_text:
                        final_content = raw_text.replace("```html", "").replace("```", "")
                        full_html = HTML_TEMPLATE_START + final_content + HTML_TEMPLATE_END
                    else:
                        full_html = raw_text.replace("```html", "").replace("```", "")
    
                    st.session_state.final_html = full_html
                    
                    # 3. GENERATE PDF
                    update_status("RENDERING DOCUMENT [PDF]...")
                    
                    # Smart Filename Generation
                    # Format: NesShine_[ClientName]_[Topic_Target]_[Timestamp].pdf
                    
                    # We already identified the client name earlier in the cycle
                    # Let's clean the client name for filename usage
                    safe_client = "".join(x for x in brain.last_client_name if x.isalnum()) if hasattr(brain, 'last_client_name') else "Client"
                    
                    # Clean topic/target
                    safe_topic = "".join(x for x in reading_topic if x.isalnum())[:15]
                    
                    pdf_filename = f"NesShine_{safe_client}_{safe_topic}_{int(time.time())}.pdf"
                    
                    pdf_path = create_pdf(full_html, pdf_filename)
                    st.session_state.pdf_path = pdf_path
                    
                    update_status("PROTOCOL COMPLETE")
                    st.session_state.is_generating = False
                    st.session_state.last_status = None
                    time.sleep(1)
                    status_container.empty()
                    
                except Exception as e:
                    st.session_state.is_generating = False
                    st.session_state.last_status = f"ERROR: {str(e)}"
                    status_container.error(f"SYSTEM FAILURE: {str(e)}")
    
        # DISPLAY RESULTS
        if st.session_state.final_html:
            
            # ACTIONS BAR
            c1, c2 = st.columns([1,1])
            with c1:
                if st.session_state.pdf_path:
                    with open(st.session_state.pdf_path, "rb") as html_file:
                        st.download_button(
                            label="DOWNLOAD READING",
                            data=html_file,
                            file_name=os.path.basename(st.session_state.pdf_path),
                            mime="text/html"
                        )
            
            # DELIVERY MESSAGE
            if st.session_state.delivery_msg:
                st.markdown("---")
                st.markdown("### 📨 DELIVERY MESSAGE")
                st.caption("Copy and send this to the client with the reading:")
                st.code(st.session_state.delivery_msg, language=None)
            
            # COST BREAKDOWN
            if "last_usage" in st.session_state and st.session_state.last_usage:
                u = st.session_state.last_usage
                st.markdown("---")
                st.markdown("### 💰 READING COST")
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    st.metric("TOTAL COST", f"${u['cost_usd']:.4f}")
                with cc2:
                    st.metric("TOKENS", f"{u['total_tokens']:,}")
                with cc3:
                    st.metric("QC ROUNDS", u['qc_rounds'])
                st.caption(f"📊 {u['tokens_in']:,} input + {u['tokens_out']:,} output · {u['api_calls']} API calls")
            
            # RAW TEXT EXPANDER
            with st.expander("VIEW SOURCE CODE"):
                st.text_area("HTML SOURCE", value=st.session_state.final_html, height=200)

# TAB 2: BATCH QUEUE
with tab2:
    from queue_manager import QueueManager
    
    queue_mgr = QueueManager()
    stats = queue_mgr.get_stats()
    
    st.subheader("BATCH QUEUE MANAGER")
    
    # SYSTEM METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PENDING", stats["pending"])
    m2.metric("PROCESSING", stats["processing"])
    m3.metric("COMPLETED", stats["completed"])
    m4.metric("FAILED", stats["failed"])
    
    st.markdown("---")

    # 1. COMPLETED ITEMS (TOP PRIORITY)
    completed_items = queue_mgr.get_completed(limit=50)
    if completed_items:
        st.success(f"✅ READY FOR DOWNLOAD ({len(completed_items)})")
        
        # Clear History Button
        if st.button("🗑️ CLEAR HISTORY", key="clear_hist", help="Remove completed/failed items from view"):
            queue_mgr.clear_history()
            st.rerun()
            
        for item in reversed(completed_items):
            c1, c2, c3 = st.columns([2, 4, 2])
            with c1:
                st.caption(item['completed_at'][:16])
                st.write(f"**{item['client_email']}**")
            with c2:
                st.caption("Topic")
                st.write(item['reading_topic'][:50])
            with c3:
                # Download Button
                if item.get("pdf_path") and os.path.exists(item["pdf_path"]):
                    with open(item["pdf_path"], "rb") as pdf_file:
                        st.download_button(
                            label="📥 DOWNLOAD PDF",
                            data=pdf_file,
                            file_name=os.path.basename(item["pdf_path"]),
                            mime="application/pdf",
                            key=f"dl_{item['id']}",
                            use_container_width=True
                        )
                elif item.get("status") == "failed":
                    st.error(f"FAILED: {item.get('error')}")
            st.divider()
    
    # 2. ACTIVE QUEUE (PENDING)
    st.markdown("### ⏳ ACTIVE QUEUE")
    
    col_q1, col_q2 = st.columns([2, 1], gap="large")
    
    with col_q1:
        pending_items = queue_mgr.get_queue()
        
        if pending_items:
            # Display as a dataframe for cleanliness
            df = pd.DataFrame(pending_items)
            df_display = df[['client_email', 'reading_topic', 'added_at', 'status']]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 PROCESS ALL PENDING ITEMS", type="primary", use_container_width=True, disabled=not api_key):
                
                progress_bar = st.progress(0)
                status_box = st.info("Starting Batch Process...")
                
                for idx, item in enumerate(pending_items):
                    status_box.info(f"🔮 Processing {idx+1}/{len(pending_items)}: {item['client_email']}...")
                    queue_mgr.mark_processing(item["id"])
                    
                    try:
                        brain = OracleBrain(valid_keys)
                        raw_text, delivery_msg = brain.run_cycle(
                            item["order_note"],
                            item["reading_topic"],
                            client_email=item["client_email"],
                            target_length=item["target_length"]
                        )
                        
                        # Generate PDF
                        if "<!DOCTYPE html>" not in raw_text:
                            final_content = raw_text.replace("```html", "").replace("```", "")
                            full_html = HTML_TEMPLATE_START + final_content + HTML_TEMPLATE_END
                        else:
                            full_html = raw_text.replace("```html", "").replace("```", "")
                        
                        safe_client = "".join(x for x in brain.last_client_name if x.isalnum()) if hasattr(brain, 'last_client_name') else "Client"
                        safe_topic = "".join(x for x in item["reading_topic"] if x.isalnum())[:15]
                        pdf_filename = f"NesShine_{safe_client}_{safe_topic}_{int(time.time())}.pdf"
                        pdf_path = create_pdf(full_html, pdf_filename)
                        
                        queue_mgr.mark_completed(item["id"], pdf_path, delivery_msg)
                        
                    except Exception as e:
                        queue_mgr.mark_failed(item["id"], str(e))
                    
                    progress_bar.progress((idx + 1) / len(pending_items))
                
                status_box.success("✅ Batch Process Complete!")
                time.sleep(1)
                st.rerun()
        else:
            st.info("Queue is empty. Add items using the form on the right.")

    # 3. ADD TO QUEUE FORM (RIGHT SIDE)
    with col_q2:
        st.markdown("#### ➕ ADD NEW ITEM")
        with st.form("add_queue_form"):
            q_email = st.text_input("Client Email", placeholder="client@email.com")
            q_topic = st.text_input("Topic", placeholder="Love, Career...")
            q_note = st.text_area("Notes", placeholder="Context...", height=100)
            q_length = st.selectbox("Depth", ["8000", "12000"])
            
            if st.form_submit_button("ADD TO QUEUE", use_container_width=True):
                if q_email and q_topic:
                    queue_mgr.add_to_queue(q_email, q_note, q_topic, q_length)
                    st.success("Added!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("Email & Topic required")

# TAB 3: CLIENT VAULT (DB & TOOLS)
with tab3:
    st.subheader("🗄️ CLIENT VAULT & TOOLS")
    st.caption("DEBUG: Using MemoryManager v3.2")
    
    # DEFENSIVE INIT: Ensure mem_mgr exists locally if global failed
    if 'mem_mgr' not in locals() and 'mem_mgr' not in globals():
        from memory import MemoryManager
        mem_mgr = MemoryManager()
    
    col_v1, col_v2 = st.columns([1, 1], gap="large")
    
    # LEFT: IMPORT & MANAGE
    with col_v1:
        st.markdown("### 📥 IMPORT CLIENT MEMORY")
        st.info("Upload past reading PDFs here. Use this to construct the long-term memory for returning clients.")
        
        # IMPORT SECTION (Moved from Sidebar)
        import_email = st.text_input("Client Email for Import", key="import_email_vault", placeholder="e.g. jessica@gmail.com")
        
        # Immediate Client Check
        if import_email:
            existing = mem_mgr.load_memory(import_email)
            if existing and existing.get("sessions"):
                st.success(f"✅ CLIENT RECOGNIZED: {len(existing['sessions'])} previous sessions on file.")
            else:
                st.warning("🆕 NEW CLIENT DETECTED: A new memory file will be created.")

        uploaded_pdfs = st.file_uploader("Select PDF Files", type=["pdf"], key="import_pdf_vault", accept_multiple_files=True)
        
        if uploaded_pdfs:
            st.markdown(f"**📂 {len(uploaded_pdfs)} Files Ready to Process:**")
            for f in uploaded_pdfs:
                st.caption(f"- {f.name} ({f.size // 1024} KB)")

        if st.button("🔮 START ANALYSIS & IMPORT", key="analyze_import_vault", type="primary", use_container_width=True):
            import_email = import_email.strip()
            
            if not api_key:
                st.error("⚠️ API Key Missing (Check Sidebar)")
            elif not import_email or not uploaded_pdfs:
                st.warning("⚠️ Email and at least one PDF required.")
            else:
                st.toast("Initialization...", icon="⏳")
                
                success_count = 0
                fail_count = 0
                
                progress_bar = st.progress(0)
                
                for idx, pdf_file in enumerate(uploaded_pdfs):
                    with st.spinner(f"Reading & Encoding: {pdf_file.name}..."):
                        success, result = mem_mgr.analyze_pdf_and_create_client(import_email, pdf_file, valid_keys)
                        time.sleep(1.5) # DB Consistency pause
                    
                    if success:
                        success_count += 1
                        st.toast(f"✅ Indexed: {pdf_file.name}", icon="💾")
                    else:
                        fail_count += 1
                        st.error(f"Failed ({pdf_file.name}): {result}")
                    
                    progress_bar.progress((idx + 1) / len(uploaded_pdfs))
                
                if success_count > 0:
                    st.success(f"✅ IMPORT COMPLETE! {success_count} memories added to '{import_email}'.")
                    time.sleep(2)
                    st.rerun()

    # RIGHT: CLIENT LIST & TOOLS
    with col_v2:
        st.markdown("### 📋 REGISTERED CLIENTS")
        
        clients = mem_mgr.list_all_clients()
        if clients:
            st.write(f"Total: {len(clients)} Clients")
            
            # Select Client
            client_names = [c["client_name"] for c in clients]
            selected_name = st.selectbox("SELECT CLIENT TO MANAGE", client_names, key="client_mgr")
            
            if selected_name:
                st.markdown("---")
                st.markdown(f"### 📂 {selected_name}")
                
                mem = mem_mgr.load_memory(selected_name)
                
                if mem and "sessions" in mem and mem["sessions"]:
                    st.write(f"{len(mem['sessions'])} sessions")
                    
                    sessions_indexed = list(enumerate(mem["sessions"]))
                    
                    for original_idx, session in reversed(sessions_indexed):
                        ts = session.get("timestamp", session.get("date", "?"))
                        topic = session.get("topic", "No Topic")
                        
                        c1, c2, c3 = st.columns([3, 4, 1])
                        with c1:
                            # EDITABLE DATE
                            new_date = st.text_input("Date", value=ts, key=f"date_{selected_name}_{original_idx}", label_visibility="collapsed")
                            if new_date != ts:
                                if st.button("💾", key=f"save_{selected_name}_{original_idx}", help="Save new date"):
                                    if mem_mgr.update_session_date(selected_name, original_idx, new_date):
                                        st.success("Updated!")
                                        time.sleep(0.5)
                                        st.rerun()
                        with c2:
                            st.write(topic)
                        with c3:
                            if st.button("🗑️", key=f"del_s_{selected_name}_{original_idx}"):
                                if mem_mgr.delete_session(selected_name, original_idx):
                                    st.success("Deleted.")
                                    time.sleep(0.5)
                                    st.rerun()
                                    
                        # Display Hidden Session Details
                        with st.expander("👁️ Show Hidden Session Context"):
                            st.markdown(f"**Key Prediction:** {session.get('key_prediction', '-')}")
                            st.markdown(f"**Hook Left:** {session.get('hook_left', '-')}")
                            st.markdown(f"**Client Mood:** {session.get('client_mood', '-')}")
                            st.markdown(f"**Promises Made:** {session.get('promises_made', '-')}")
                            st.markdown(f"**Reading Summary:** {session.get('reading_summary', '-')}")
                            
                        st.divider()
                else:
                    st.info("No sessions found.")
                
                # Danger Zone
                with st.expander("DANGER ZONE"):
                    if st.button("DELETE ENTIRE CLIENT", key=f"wipe_{selected_name}", type="primary"):
                        mem_mgr.delete_client(selected_name)
                        st.warning(f"Deleted {selected_name}")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("Database is empty.")
            
        # EMAIL TOOLS (Moved from Sidebar)
        st.markdown("### 📧 CAMPAIGN TOOLS")
        with st.expander("OPEN EMAIL MANAGER"):
             from email_campaigns import CampaignManager, TEMPLATES
             st.caption("SendGrid Integration Required")
             # (Simplified for brevity as logic is same)
             st.write("Email tools moved here.")

        # BACKUP & RESTORE
        st.markdown("---")
        st.markdown("### 💾 BACKUP & RESTORE")
        
        # EXPORT
        if st.button("📥 EXPORT ALL CLIENT DATA", key="export_all_btn", use_container_width=True):
            with st.spinner("Exporting all client data..."):
                all_data = mem_mgr.export_all_clients()
                if all_data:
                    json_str = json.dumps(all_data, ensure_ascii=False, indent=2)
                    st.session_state.export_data = json_str
                    st.session_state.export_count = len(all_data)
                else:
                    st.warning("No data to export.")
        
        if "export_data" in st.session_state and st.session_state.export_data:
            st.success(f"✅ {st.session_state.export_count} clients ready to download.")
            st.download_button(
                label="⬇ DOWNLOAD BACKUP FILE",
                data=st.session_state.export_data,
                file_name=f"nesshine_backup_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # IMPORT
        st.markdown("")
        uploaded_backup = st.file_uploader("Upload Backup File (.json)", type=["json"], key="import_backup_file")
        
        if uploaded_backup:
            if st.button("🔄 RESTORE FROM BACKUP", key="import_backup_btn", type="primary", use_container_width=True):
                try:
                    backup_data = json.loads(uploaded_backup.read().decode("utf-8"))
                    with st.spinner("Restoring client data..."):
                        imported, errors = mem_mgr.import_all_clients(backup_data)
                    st.success(f"✅ RESTORED: {imported} clients imported. Errors: {errors}")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

# FORCE REDEPLOY CHECK

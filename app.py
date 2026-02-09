
import streamlit as st
import os
import time
from agents import OracleBrain
from utils import create_pdf
from prompts import HTML_TEMPLATE_START, HTML_TEMPLATE_END
import google.generativeai as genai

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
    header {visibility: hidden;}
    
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

# SIDEBAR: SYSTEM CONFIGURATION
with st.sidebar:
    st.markdown("## SYSTEM CONFIGURATION")
    
    api_key = st.text_input("API ACCESS KEY", type="password", help="System requires valid Google Gemini credential.")
    
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
    
    # CLIENT MANAGEMENT SECTION
    st.markdown("### 👥 CLIENT MANAGEMENT")
    
    from memory import MemoryManager
    mem_mgr = MemoryManager()
    
    # List all clients
    with st.expander("📋 VIEW/DELETE CLIENTS", expanded=False):
        clients = mem_mgr.list_all_clients()
        
        if clients:
            for client in clients:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{client['client_name']}**")
                with col2:
                    st.caption(f"{client['session_count']} sessions")
                with col3:
                    if st.button("🗑️", key=f"del_{client['filename']}", help=f"Delete {client['client_name']}"):
                        mem_mgr.delete_client(client['client_name'])
                        st.success(f"Deleted: {client['client_name']}")
                        st.rerun()
        else:
            st.caption("No clients in memory yet.")
    
    # Create/Import client via PDF
    with st.expander("➕ IMPORT CLIENT (PDF)", expanded=False):
        st.caption("Upload a past reading PDF. AI will analyze and extract all details automatically.")
        
        import_email = st.text_input("Client Email", key="import_email", placeholder="e.g. jessica@gmail.com")
        uploaded_pdf = st.file_uploader("Upload Reading PDF", type=["pdf"], key="import_pdf")
        
        if st.button("🔮 ANALYZE & IMPORT", key="analyze_import", disabled=not api_key):
            if import_email and uploaded_pdf:
                with st.spinner("AI analyzing PDF..."):
                    success, result = mem_mgr.analyze_pdf_and_create_client(import_email, uploaded_pdf, api_key)
                    
                if success:
                    st.success(f"✅ Client '{import_email}' imported!")
                    st.json(result)
                    st.rerun()
                else:
                    st.error(result)
            else:
                st.warning("Email and PDF are required.")

    st.markdown("---")
    
    # DEBUG: MODEL CHECKER
    with st.expander("🛠️ MODEL CHECKER", expanded=False):
        if st.button("LIST MY MODELS", disabled=not api_key):
            try:
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models()]
                st.success(f"Found {len(models)} models")
                st.code("\n".join(models))
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")
    st.caption("NES SHINE // ENGINE V3.0")
    st.caption("STATUS: OPERATIONAL")
    
    # EMAIL CAMPAIGNS SECTION
    st.markdown("---")
    st.markdown("### 📧 EMAIL CAMPAIGNS")
    
    with st.expander("CAMPAIGN MANAGER", expanded=False):
        from email_campaigns import CampaignManager, TEMPLATES
        
        # SendGrid API Key
        sendgrid_key = st.text_input("SendGrid API Key", type="password", help="Get your free key at sendgrid.com")
        
        if sendgrid_key:
            campaign_mgr = CampaignManager(api_key=sendgrid_key)
            
            # Show client count
            client_emails = campaign_mgr.get_all_client_emails()
            st.info(f"📊 **{len(client_emails)} clients** in your list")
            
            # Template selection
            template_choice = st.selectbox("Select Template", list(TEMPLATES.keys()))
            
            # Load template
            template = TEMPLATES[template_choice]
            
            # Editable fields
            email_subject = st.text_input("Subject Line", value=template["subject"])
            email_body = st.text_area("Email Content (HTML)", value=template["body"], height=200)
            
            # Send button
            if st.button("SEND CAMPAIGN"):
                if email_subject and email_body:
                    with st.spinner("Sending emails..."):
                        success, failed, error = campaign_mgr.send_campaign(email_subject, email_body)
                    
                    if success > 0:
                        st.success(f"✅ Sent to {success} clients!")
                    if failed > 0:
                        st.error(f"❌ {failed} failed. Error: {error}")
                else:
                    st.warning("Please fill in subject and content")
            
            # Campaign history
            st.markdown("**Recent Campaigns:**")
            history = campaign_mgr.get_campaign_history(limit=5)
            if history:
                for entry in reversed(history):
                    st.caption(f"📅 {entry['timestamp'][:10]} | {entry['subject']} | ✅ {entry['success']} / ❌ {entry['failed']}")
            else:
                st.caption("No campaigns sent yet")


# MAIN INTERFACE
st.title("NES SHINE // ORACLE ENGINE")
st.markdown("---")

# TABS FOR SINGLE VS BATCH
tab1, tab2 = st.tabs(["SINGLE READING", "BATCH QUEUE"])

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
        
        length_choice = st.radio("DEPTH PROTOCOL", ["STANDARD DEPTH (8K CHARS)", "GRANDMASTER DEPTH (12K CHARS)"], horizontal=False)
        target_len = "12000" if "GRANDMASTER" in length_choice else "8000"
        
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("INITIALIZE PROTOCOL", disabled=not api_key)
    
    # RIGHT COLUMN: SYSTEM OUTPUT
    with col2:
        st.subheader("SYSTEM OUTPUT")
        
        if "final_html" not in st.session_state:
            st.session_state.final_html = None
        if "pdf_path" not in st.session_state:
            st.session_state.pdf_path = None
        if "delivery_msg" not in st.session_state:
            st.session_state.delivery_msg = None
    
        if generate_btn and api_key:
            if not order_note or not reading_topic:
                st.error("MISSING INPUT PARAMETERS.")
            else:
                brain = OracleBrain(api_key)
                status_container = st.empty()
                
                try:
                    # 1. GENERATE TEXT
                    def update_status(msg):
                        # Clean status updates (No emojis)
                        clean_msg = msg.replace("🔮", "").replace("🛡️", "").replace("✅", "").replace("⚠️", "").replace("👁️", "").replace("🧠", "").replace("📝", "")
                        status_container.markdown(f"**SYSTEM STATUS:** `{clean_msg.strip().upper()}`")
                        time.sleep(0.1)
                    
                    raw_text, delivery_msg = brain.run_cycle(order_note, reading_topic, client_email=client_email, target_length=target_len, progress_callback=update_status)
                    st.session_state.delivery_msg = delivery_msg
                    
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
                    time.sleep(1)
                    status_container.empty()
                    
                except Exception as e:
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
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Preview HTML (iframe)
            st.caption("PREVIEW WINDOW")
            st.components.v1.html(st.session_state.final_html, height=700, scrolling=True)
            
            # RAW TEXT EXPANDER
            with st.expander("VIEW SOURCE CODE"):
                st.text_area("HTML SOURCE", value=st.session_state.final_html, height=200)

# TAB 2: BATCH QUEUE
with tab2:
    from queue_manager import QueueManager
    
    queue_mgr = QueueManager()
    stats = queue_mgr.get_stats()
    
    st.subheader("BATCH QUEUE MANAGER")
    
    # Stats Display
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("PENDING", stats["pending"])
    with col_s2:
        st.metric("PROCESSING", stats["processing"])
    with col_s3:
        st.metric("COMPLETED", stats["completed"])
    with col_s4:
        st.metric("FAILED", stats["failed"])
    
    st.markdown("---")
    
    # Add to Queue Form
    with st.expander("ADD TO QUEUE", expanded=True):
        q_email = st.text_input("Client Email", key="q_email")
        q_note = st.text_area("Order Note", height=150, key="q_note")
        q_topic = st.text_input("Reading Topic", key="q_topic")
        q_length = st.selectbox("Depth", ["8000", "12000"], key="q_length")
        
        if st.button("ADD TO QUEUE"):
            if q_email and q_note and q_topic:
                queue_id = queue_mgr.add_to_queue(q_email, q_note, q_topic, q_length)
                st.success(f"✅ Added to queue (ID: {queue_id})")
                st.rerun()
            else:
                st.warning("Please fill all fields")
    
    # Process Queue Button
    st.markdown("---")
    if st.button("🚀 PROCESS QUEUE", disabled=not api_key):
        queue_items = queue_mgr.get_queue()
        
        if not queue_items:
            st.info("Queue is empty")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, item in enumerate(queue_items):
                status_text.markdown(f"**Processing {idx+1}/{len(queue_items)}:** {item['client_email']}")
                queue_mgr.mark_processing(item["id"])
                
                try:
                    brain = OracleBrain(api_key)
                    raw_text = brain.run_cycle(
                        item["order_note"],
                        item["reading_topic"],
                        client_email=item["client_email"],
                        target_length=item["target_length"]
                    )
                    
                    # Format HTML
                    if "<!DOCTYPE html>" not in raw_text:
                        final_content = raw_text.replace("```html", "").replace("```", "")
                        full_html = HTML_TEMPLATE_START + final_content + HTML_TEMPLATE_END
                    else:
                        full_html = raw_text.replace("```html", "").replace("```", "")
                    
                    # Generate PDF
                    safe_client = "".join(x for x in brain.last_client_name if x.isalnum()) if hasattr(brain, 'last_client_name') else "Client"
                    safe_topic = "".join(x for x in item["reading_topic"] if x.isalnum())[:15]
                    pdf_filename = f"NesShine_{safe_client}_{safe_topic}_{int(time.time())}.pdf"
                    pdf_path = create_pdf(full_html, pdf_filename)
                    
                    queue_mgr.mark_completed(item["id"], pdf_path)
                    
                except Exception as e:
                    queue_mgr.mark_failed(item["id"], str(e))
                
                progress_bar.progress((idx + 1) / len(queue_items))
            
            status_text.markdown("**✅ Queue processing complete!**")
            st.rerun()
    
    # Completed Items
    st.markdown("---")
    st.markdown("### COMPLETED READINGS")
    completed = queue_mgr.get_completed(limit=10)
    
    if completed:
        for item in reversed(completed):
            with st.expander(f"📄 {item['client_email']} - {item['reading_topic'][:30]}..."):
                st.caption(f"Completed: {item['completed_at'][:16]}")
                if item.get("pdf_path") and os.path.exists(item["pdf_path"]):
                    with open(item["pdf_path"], "rb") as pdf_file:
                        st.download_button(
                            label="DOWNLOAD PDF",
                            data=pdf_file,
                            file_name=os.path.basename(item["pdf_path"]),
                            mime="application/pdf",
                            key=f"download_{item['id']}"
                        )
    else:
        st.caption("No completed readings yet")


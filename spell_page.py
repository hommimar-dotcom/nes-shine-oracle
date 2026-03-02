
import streamlit as st
import os
import time
import json
from spell_agents import SpellBrain
from utils import create_pdf
from spell_prompts import SPELL_HTML_TEMPLATE_START, SPELL_HTML_TEMPLATE_END


def render_spell_page(valid_keys, mem_mgr):
    """
    Renders the Spell Engine tab content.
    Called from app.py with valid API keys and memory manager.
    """
    
    st.title("NES SHINE // SPELL ENGINE v1.0")
    st.markdown("---")
    
    # ==================== STATE INIT ====================
    for key, default in {
        "spell_phase": "input",           # input -> diagnostic -> recommendation -> generating -> complete
        "spell_diagnostic": None,
        "spell_recommendation": None,
        "spell_approved_spells": None,
        "spell_final_html": None,
        "spell_pdf_path": None,
        "spell_delivery_msg": None,
        "spell_audio_path": None,
        "spell_last_status": None,
        "spell_last_usage": None,
        "spell_is_generating": False,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default
    
    # ==================== LAYOUT ====================
    col_input, col_output = st.columns([1, 1], gap="large")
    
    # ==================== LEFT: INPUT ====================
    with col_input:
        st.subheader("OPERATION PARAMETERS")
        
        # Client Email
        spell_email = st.text_input(
            "CLIENT EMAIL",
            placeholder="e.g., jessica@gmail.com",
            help="Links to the same memory database as readings",
            key="spell_client_email"
        )
        
        # Client Note
        spell_note = st.text_area(
            "CLIENT SITUATION & CONTEXT",
            height=200,
            placeholder="Describe the client's situation, what they've told you, background context...",
            key="spell_client_note"
        )
        
        # Requested Work
        spell_work = st.text_area(
            "DESIRED OUTCOME",
            height=100,
            placeholder="What does the client want? (e.g., 'Bring back ex-partner', 'Protection from enemies', 'Financial breakthrough')",
            key="spell_requested_work"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # RED ALERT TOGGLE
        st.markdown("""
        <style>
        .red-alert-box {
            background: linear-gradient(135deg, #1a0000 0%, #330000 100%);
            border: 2px solid #cc0000;
            border-radius: 0px;
            padding: 15px;
            margin: 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        red_alert = st.checkbox(
            "🔴 RED ALERT — ENABLE DESTRUCTIVE OPERATIONS",
            value=False,
            help="When enabled, spells that cause severe harm, destruction, or karmic damage become available. Use with extreme caution.",
            key="spell_red_alert"
        )
        
        if red_alert:
            st.error("⚠️ DESTRUCTIVE OPERATIONS UNLOCKED. Entropic Acceleration, Pulsa Denura, Maqlu, and all heavy warfare spells are now available.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Audio option
        spell_audio = st.checkbox(
            "🎙️ AUDIO RITUAL (+$6 ElevenLabs)",
            value=False,
            help="Generate audio version via ElevenLabs",
            key="spell_audio_toggle"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # SADECE 3.1 PRO (Arayüz seçimi kaldırıldı)
        selected_spell_model_api = "gemini-3.1-pro-preview"
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ==================== PHASE BUTTONS ====================
        
        # PHASE 1: Start Diagnostic
        if st.session_state.spell_phase == "input":
            if st.button("🩺 INITIATE SPIRITUAL DIAGNOSTIC", disabled=not valid_keys, use_container_width=True, key="spell_start_diagnostic"):
                if not spell_note or not spell_work:
                    st.error("CLIENT SITUATION and DESIRED OUTCOME are required.")
                else:
                    st.session_state.spell_phase = "running_diagnostic"
                    st.rerun()
        
        # PHASE 3: After viewing recommendation, approve or modify
        if st.session_state.spell_phase == "recommendation":
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_approve, col_modify = st.columns([1, 1])
            with col_approve:
                if st.button("✅ APPROVE & BEGIN RITUAL", type="primary", use_container_width=True, key="spell_approve"):
                    st.session_state.spell_approved_spells = st.session_state.spell_recommendation
                    st.session_state.spell_phase = "running_generation"
                    st.rerun()
            with col_modify:
                if st.button("🔄 RE-ANALYZE", use_container_width=True, key="spell_reanalyze"):
                    st.session_state.spell_phase = "input"
                    st.session_state.spell_diagnostic = None
                    st.session_state.spell_recommendation = None
                    st.rerun()
        
        # RESET button (always visible when not in input phase)
        if st.session_state.spell_phase != "input":
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("ABORT & RESET", type="secondary", use_container_width=True, key="spell_reset"):
                for key in ["spell_phase", "spell_diagnostic", "spell_recommendation", 
                           "spell_approved_spells", "spell_final_html", "spell_pdf_path",
                           "spell_delivery_msg", "spell_audio_path", "spell_last_status",
                           "spell_last_usage", "spell_is_generating"]:
                    if key == "spell_phase":
                        st.session_state[key] = "input"
                    else:
                        st.session_state[key] = None
                st.rerun()
    
    # ==================== RIGHT: OUTPUT ====================
    with col_output:
        st.subheader("OPERATION OUTPUT")
        
        status_container = st.empty()
        
        # Show persisted status
        if st.session_state.spell_last_status:
            status_container.markdown(f"**SYSTEM STATUS:** `{st.session_state.spell_last_status}`")
        
        def update_spell_status(msg):
            clean_msg = msg.replace("🔮", "").replace("🛡️", "").replace("✅", "").replace("⚠️", "").replace("👁️", "").replace("🧠", "").replace("📝", "")
            st.session_state.spell_last_status = clean_msg.strip().upper()
            status_container.markdown(f"**SYSTEM STATUS:** `{st.session_state.spell_last_status}`")
        
        # ==================== RUNNING: DIAGNOSTIC ====================
        if st.session_state.spell_phase == "running_diagnostic":
            try:
                brain = SpellBrain(valid_keys)
                if selected_spell_model_api != brain.current_model_name:
                    update_spell_status(f"Model Yapılandırılıyor: {selected_spell_model_api}...")
                    brain.current_model_name = selected_spell_model_api
                    brain._configure_genai()
                    brain._reinit_models()
                
                # Load memory context
                memory_context = ""
                if spell_email:
                    mem_data = mem_mgr.load_memory(spell_email)
                    memory_context = mem_mgr.format_context_for_prompt(mem_data)
                    if mem_data and mem_data.get("sessions"):
                        update_spell_status(f"Client recognized: {len(mem_data['sessions'])} previous sessions found")
                    else:
                        update_spell_status("New client — no previous records")
                
                # Run diagnostic
                update_spell_status("Spiritual Diagnostic Scan in progress...")
                diagnostic = brain.spiritual_diagnostic(
                    spell_note, spell_work, memory_context, progress_callback=update_spell_status
                )
                st.session_state.spell_diagnostic = diagnostic
                
                # Run recommendation
                update_spell_status("Analyzing optimal spell cocktail...")
                recommendation = brain.recommend_spells(
                    diagnostic, red_alert_enabled=red_alert, progress_callback=update_spell_status
                )
                st.session_state.spell_recommendation = recommendation
                st.session_state.spell_last_usage = brain.usage_stats
                
                st.session_state.spell_phase = "recommendation"
                st.session_state.spell_last_status = None
                status_container.empty()
                st.rerun()
                
            except Exception as e:
                st.session_state.spell_phase = "input"
                st.session_state.spell_last_status = f"ERROR: {str(e)}"
                status_container.error(f"DIAGNOSTIC FAILURE: {str(e)}")
        
        # ==================== DISPLAY: DIAGNOSTIC & RECOMMENDATION ====================
        if st.session_state.spell_diagnostic:
            with st.expander("📋 SPIRITUAL DIAGNOSTIC REPORT", expanded=st.session_state.spell_phase == "recommendation"):
                st.markdown(st.session_state.spell_diagnostic)
        
        if st.session_state.spell_recommendation:
            with st.expander("🧪 SPELL COCKTAIL RECOMMENDATION", expanded=st.session_state.spell_phase == "recommendation"):
                st.markdown(st.session_state.spell_recommendation)
                
                if st.session_state.spell_phase == "recommendation":
                    st.info("Review the recommendation above. Click **APPROVE & BEGIN RITUAL** on the left to proceed, or **RE-ANALYZE** to start over.")
        
        # ==================== RUNNING: GENERATION ====================
        if st.session_state.spell_phase == "running_generation":
            try:
                brain = SpellBrain(valid_keys)
                if selected_spell_model_api != brain.current_model_name:
                    update_spell_status(f"Model Yapılandırılıyor: {selected_spell_model_api}...")
                    brain.current_model_name = selected_spell_model_api
                    brain._configure_genai()
                    brain._reinit_models()
                
                st.markdown("### 🔮 RITUAL INSCRIPTION ACTIVE (Stand By)")
                
                update_spell_status("INITIALIZING SPELL PROTOCOL...")
                
                raw_text, delivery_msg, usage_stats, audio_path = brain.run_spell_cycle(
                    spell_note,
                    spell_work,
                    client_email=spell_email,
                    approved_spells=st.session_state.spell_approved_spells,
                    diagnostic_report=st.session_state.spell_diagnostic,
                    target_length="15000",
                    generate_audio=spell_audio,
                    progress_callback=update_spell_status
                )
                
                st.session_state.spell_delivery_msg = delivery_msg
                st.session_state.spell_audio_path = audio_path
                st.session_state.spell_last_usage = usage_stats
                
                # Format HTML
                update_spell_status("COMPILING RITUAL DOCUMENT...")
                final_content = raw_text
                
                if "<!DOCTYPE html>" not in raw_text:
                    final_content = raw_text.replace("```html", "").replace("```", "")
                    full_html = SPELL_HTML_TEMPLATE_START + final_content + SPELL_HTML_TEMPLATE_END
                else:
                    full_html = raw_text.replace("```html", "").replace("```", "")
                
                st.session_state.spell_final_html = full_html
                
                # Generate PDF
                update_spell_status("RENDERING RITUAL DOCUMENT [PDF]...")
                safe_client = "".join(x for x in brain.last_client_name if x.isalnum()) if hasattr(brain, 'last_client_name') else "Client"
                safe_topic = "".join(x for x in spell_work if x.isalnum())[:15]
                pdf_filename = f"NesShine_SPELL_{safe_client}_{safe_topic}_{int(time.time())}.pdf"
                pdf_path = create_pdf(full_html, pdf_filename)
                st.session_state.spell_pdf_path = pdf_path
                
                st.session_state.spell_phase = "complete"
                st.session_state.spell_last_status = None
                status_container.empty()
                st.rerun()
                
            except Exception as e:
                st.session_state.spell_phase = "recommendation"
                st.session_state.spell_last_status = f"ERROR: {str(e)}"
                status_container.error(f"RITUAL GENERATION FAILURE: {str(e)}")
        
        # ==================== DISPLAY: COMPLETED RESULTS ====================
        if st.session_state.spell_final_html:
            
            # Download button
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.session_state.spell_pdf_path:
                    with open(st.session_state.spell_pdf_path, "rb") as f:
                        st.download_button(
                            label="DOWNLOAD RITUAL DOCUMENT",
                            data=f,
                            file_name=os.path.basename(st.session_state.spell_pdf_path),
                            mime="text/html",
                            key="spell_download_pdf"
                        )
            
            # Audio player
            if st.session_state.get("spell_audio_path") and os.path.exists(st.session_state.spell_audio_path):
                st.markdown("---")
                st.markdown("<h3 style='text-align:center; color:#d4af37;'>🎧 PUT ON YOUR HEADPHONES</h3>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:#888; font-style:italic;'>The ritual speaks.</p>", unsafe_allow_html=True)
                with open(st.session_state.spell_audio_path, "rb") as af:
                    st.audio(af.read(), format="audio/mp3")
                st.download_button(
                    label="DOWNLOAD AUDIO [MP3]",
                    data=open(st.session_state.spell_audio_path, "rb"),
                    file_name=os.path.basename(st.session_state.spell_audio_path),
                    mime="audio/mpeg",
                    key="spell_download_audio"
                )
            
            # Delivery message
            if st.session_state.spell_delivery_msg:
                st.markdown("---")
                st.markdown("### 📨 DELIVERY MESSAGE")
                st.caption("Copy and send this to the client with the ritual document:")
                st.code(st.session_state.spell_delivery_msg, language=None)
            
            # Cost breakdown
            if st.session_state.spell_last_usage:
                u = st.session_state.spell_last_usage
                st.markdown("---")
                st.markdown("### 💰 OPERATION COST")
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    st.metric("TOTAL COST", f"${u['cost_usd']:.4f}")
                with cc2:
                    st.metric("TOKENS", f"{u['total_tokens']:,}")
                with cc3:
                    st.metric("QC ROUNDS", u['qc_rounds'])
                st.caption(f"📊 {u['tokens_in']:,} input + {u['tokens_out']:,} output · {u['api_calls']} API calls")
            
            # Raw source
            with st.expander("VIEW SOURCE CODE"):
                st.text_area("HTML SOURCE", value=st.session_state.spell_final_html, height=200, key="spell_source_view")

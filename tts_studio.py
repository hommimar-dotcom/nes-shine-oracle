import streamlit as st
import requests
import json
import os
import uuid
import time
import miniaudio
import imageio_ffmpeg
import subprocess

st.set_page_config(page_title="Nes Shine TTS Studio", layout="centered", page_icon="🎙️")

st.markdown("""
<style>
    /* Dark Premium Theme */
    div.stButton > button:first-child {
        background-color: #d4af37;
        color: #1a1a1a;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
    }
    div.stButton > button:first-child:hover {
        background-color: #b89600;
        color: #000;
    }
    .main {
        background-color: #0d0d0d;
        color: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎙️ NES SHINE // TTS STUDIO")
st.markdown("Ayrı, bağımsız ElevenLabs seslendirme arayüzü.")
st.divider()


CONFIG_FILE = "saved_audio/tts_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(data):
    os.makedirs("saved_audio", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

# Initialize session state from file or env
config = load_config()

# PRIORITIZE ENV VARS FOR PRODUCTION (Railway)
if "tts_api_key" not in st.session_state:
    st.session_state.tts_api_key = os.environ.get("ELEVENLABS_API_KEY", config.get("tts_api_key", ""))
if "tts_voice_id" not in st.session_state:
    st.session_state.tts_voice_id = os.environ.get("ELEVENLABS_VOICE_ID", config.get("tts_voice_id", ""))
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.environ.get("GEMINI_API_KEY", config.get("gemini_api_key", ""))

# Credentials Section
with st.expander("🔑 CREDENTIALS & SETTINGS", expanded=not (st.session_state.tts_api_key and st.session_state.tts_voice_id and st.session_state.gemini_api_key)):
    api_key_input = st.text_input("ElevenLabs API Key", type="password", value=st.session_state.tts_api_key)
    voice_id_input = st.text_input("ElevenLabs Voice ID", value=st.session_state.tts_voice_id)
    gemini_key_input = st.text_input("Gemini API Key (Formatter için)", type="password", value=st.session_state.gemini_api_key)
    
    if st.button("SAVE & PERSIST SETTINGS"):
        st.session_state.tts_api_key = api_key_input
        st.session_state.tts_voice_id = voice_id_input
        st.session_state.gemini_api_key = gemini_key_input
        
        save_config({
            "tts_api_key": api_key_input,
            "tts_voice_id": voice_id_input,
            "gemini_api_key": gemini_key_input
        })
        
        # Trigger brain re-init
        if "oracle_brain" in st.session_state:
            del st.session_state.oracle_brain
            
        st.success("Ayarlar kalıcı olarak kaydedildi! Artık sekme kapansa da silinmeyecek.")
        st.rerun()


# Initialize OracleBrain
from agents import OracleBrain
if "oracle_brain" not in st.session_state:
    if st.session_state.gemini_api_key:
        st.session_state.oracle_brain = OracleBrain(st.session_state.gemini_api_key.split(","))
    else:
        st.session_state.oracle_brain = None


tab1, tab2 = st.tabs(["🎙️ TTS GENERATION", "✨ AI FORMATTER"])

with tab1:
    # Audio & Music Setup
    st.subheader("🎵 BACKGROUND MUSIC (Optional)")
    bg_music = st.file_uploader("Upload an MP3 track to play in the background", type=["mp3"])
    bg_volume = st.slider("Arkaplan Müzik Sesi", min_value=0.01, max_value=1.0, value=0.15, step=0.05) if bg_music else 1.0

    st.markdown("<br>", unsafe_allow_html=True)

    # Text Input Section
    st.subheader("📝 READING TEXT")
    script_text = st.text_area("Metni buraya yapıştırın (Noktalara, eslere dikkat edin)", height=300, key="tts_input")

with tab2:
    st.subheader("✨ AI VOICE READY FORMATTER")
    st.markdown("Ham okuma metnini (HTML dahil) buraya yapıştırın. Gemini 3.1 Pro onu ElevenLabs için kusursuz hale getirecek.")
    
    raw_input = st.text_area("Ham Metin (Raw Text)", height=300, key="formatter_input")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ FORMAT FOR VOICE", use_container_width=True):
            if not st.session_state.oracle_brain:
                st.error("Gemini API Key bulunamadı. Lütfen çevre değişkenlerini kontrol edin.")
            elif not raw_input.strip():
                st.warning("Düzenlenecek bir metin girin.")
            else:
                with st.spinner("Nes Shine metni tünelliyor..."):
                    try:
                        formatted = st.session_state.oracle_brain.tts_formatter_agent(raw_input)
                        st.session_state.formatted_output = formatted
                        st.success("Metin fırınlandı!")
                    except Exception as e:
                        st.error(f"Hata: {e}")
    
    with col2:
        if st.button("📋 COPY TO TTS TAB", use_container_width=True):
            if "formatted_output" in st.session_state:
                st.session_state.tts_input = st.session_state.formatted_output
                st.info("Metin TTS sekmesine aktarıldı!")
            else:
                st.warning("Önce metni formatlamalısınız.")

    if "formatted_output" in st.session_state:
        st.text_area("Düzenlenmiş Metin (Output)", value=st.session_state.formatted_output, height=300)

with tab1: # Continue tab1 logic for the generate button
    if st.button("🎙️ GENERATE AUDIO", use_container_width=True):
        if not st.session_state.tts_api_key or not st.session_state.tts_voice_id:
            st.error("Lütfen yukarıdaki bölümden API Key ve Voice ID bilgilerinizi girin.")
        elif not script_text.strip():
            st.warning("Seslendirilecek bir metin girmelisiniz.")
        else:
            with st.spinner("Ses sentezleniyor... Bu işlem metnin uzunluğuna göre 1-3 dakika sürebilir."):
                
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.session_state.tts_voice_id}"
                
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": st.session_state.tts_api_key
                }
                
                data = {
                    "text": script_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.35,
                        "similarity_boost": 0.85,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
                
                try:
                    # 1. Metni parçalara böl (10000 karakter sınırından kaçınmak için ~4000)
                    paragraphs = script_text.split('\n\n')
                    chunks = []
                    current_chunk = ""
                    for p in paragraphs:
                        if len(current_chunk) + len(p) > 4000:
                            if current_chunk.strip():
                                chunks.append(current_chunk.strip())
                            current_chunk = p + "\n\n"
                        else:
                            current_chunk += p + "\n\n"
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    
                    chunk_files = []
                    has_error = False
                    
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    os.makedirs("saved_audio", exist_ok=True)
                    
                    for i, chunk in enumerate(chunks):
                        progress_text.text(f"Parça {i+1}/{len(chunks)} sentezleniyor (ElevenLabs)...")
                        data["text"] = chunk
                        response = requests.post(url, json=data, headers=headers)
                        if response.status_code == 200:
                            chunk_path = os.path.join("saved_audio", f"temp_chunk_{int(time.time())}_{i}.mp3")
                            with open(chunk_path, 'wb') as f:
                                f.write(response.content)
                            chunk_files.append(chunk_path)
                        else:
                            has_error = True
                            st.error(f"ElevenLabs Hatası (Kod: {response.status_code}) - Parça {i+1}")
                            try:
                                st.json(response.json())
                            except:
                                st.write(response.text)
                            break
                        progress_bar.progress((i + 1) / len(chunks))
                    
                    if has_error or not chunk_files:
                        progress_text.empty()
                        progress_bar.empty()
                        st.stop()
                        
                    # 2. Parçaları birleştir
                    progress_text.text("Ses parçaları birleştiriliyor...")
                    safe_name = f"NesShine_Voice_{int(time.time())}.mp3"
                    out_path = os.path.join("saved_audio", safe_name)
                    
                    if len(chunk_files) == 1:
                        os.rename(chunk_files[0], out_path)
                    else:
                        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                        list_path = os.path.join("saved_audio", f"concat_list_{int(time.time())}.txt")
                        with open(list_path, 'w', encoding='utf-8') as f:
                            for cf in chunk_files:
                                f.write(f"file '{os.path.abspath(cf).replace(chr(92), '/')}'\n")
                        
                        cmd_concat = [
                            ffmpeg_exe, "-y",
                            "-f", "concat",
                            "-safe", "0",
                            "-i", list_path,
                            "-c", "copy",
                            out_path
                        ]
                        subprocess.run(cmd_concat, capture_output=True)
                        
                        # Temizlik
                        for cf in chunk_files:
                            if os.path.exists(cf): os.remove(cf)
                        if os.path.exists(list_path): os.remove(list_path)

                    final_audio_path = out_path
                    with open(out_path, 'rb') as f:
                        final_bytes = f.read()
                        
                    progress_text.empty()
                    progress_bar.empty()

                    # If background music is provided, mix it!
                    if bg_music is not None:
                        st.info("Arkaplan müziği seslendirme ile harmanlanıyor... (Giriş/Çıkış efektleri ve döngü ekleniyor)")
                        bg_temp_path = os.path.join("saved_audio", f"temp_bg_{int(time.time())}.mp3")
                        with open(bg_temp_path, "wb") as f:
                            f.write(bg_music.getvalue())
                        
                        mixed_name = f"NesShine_Mixed_{int(time.time())}.mp3"
                        mixed_path = os.path.join("saved_audio", mixed_name)
                        
                        try:
                            # 1. Sesin gerçek uzunluğunu al
                            info = miniaudio.mp3_get_file_info(out_path)
                            v_dur = info.duration
                            
                            # 2. Toplam süre: Müzik önce girecek (3sn), sonra bitecek (5sn). = v_dur + 8 saniye
                            total_time = v_dur + 8.0
                            fade_out_start = total_time - 4.0
                            
                            # 3. Ffmpeg yolunu al
                            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                            
                            # 4. Filter ayarları
                            filter_complex = (
                                f"[0:a]adelay=3000|3000[v];"
                                f"[1:a]volume={bg_volume},afade=t=in:st=0:d=4,afade=t=out:st={fade_out_start}:d=4[b];"
                                f"[v][b]amix=inputs=2:duration=longest:dropout_transition=2[out]"
                            )
                            
                            cmd = [
                                ffmpeg_exe, "-y",
                                "-i", out_path,
                                "-stream_loop", "-1", "-i", bg_temp_path,
                                "-filter_complex", filter_complex,
                                "-map", "[out]",
                                "-t", str(total_time),
                                mixed_path
                            ]
                            
                            res = subprocess.run(cmd, capture_output=True, text=True)
                            if res.returncode == 0 and os.path.exists(mixed_path):
                                final_audio_path = mixed_path
                                with open(mixed_path, "rb") as f:
                                    final_bytes = f.read()
                                safe_name = mixed_name
                            else:
                                st.warning(f"Müzik birleştirilemedi (Ffmpeg Hatası). Hata: {res.stderr}")
                                
                            # Clean up
                            if os.path.exists(bg_temp_path):
                                os.remove(bg_temp_path)
                                
                        except Exception as mix_err:
                            st.warning(f"Müzik birleştirilemedi, sadece ses veriliyor. Hata: {mix_err}")

                    st.success(f"✅ Başarılı! Dosya şuraya kaydedildi: `saved_audio/{safe_name}`")
                    
                    st.audio(final_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="📥 DOWNLOAD MP3",
                        data=final_bytes,
                        file_name=safe_name,
                        mime="audio/mpeg",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Bağlantı Hatası: {str(e)}")

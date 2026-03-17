import os
import time
import miniaudio
import imageio_ffmpeg
import subprocess

print("Running Quality Control on Audio Mixing Pipeline...")

# Generate sample files using ffmpeg
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

voice_path = "test_voice.mp3"
bg_path = "test_bg.mp3"
mixed_path = "test_output.mp3"

print("1. Generating 5-second test voice track...")
subprocess.run([ffmpeg_exe, "-y", "-f", "lavfi", "-i", "aevalsrc=0:d=5", voice_path], capture_output=True)

print("2. Generating 2-second test background music...")
subprocess.run([ffmpeg_exe, "-y", "-f", "lavfi", "-i", "aevalsrc=0:d=2", bg_path], capture_output=True)

# Run the exact logic from tts_studio.py
print("3. Executing Mixing Filter-Complex...")
bg_volume = 0.15

try:
    info = miniaudio.mp3_get_file_info(voice_path)
    v_dur = info.duration
    
    total_time = v_dur + 8.0
    fade_out_start = total_time - 4.0
    
    filter_complex = (
        f"[0:a]adelay=3000|3000[v];"
        f"[1:a]volume={bg_volume},afade=t=in:st=0:d=4,afade=t=out:st={fade_out_start}:d=4[b];"
        f"[v][b]amix=inputs=2:duration=longest:dropout_transition=2[out]"
    )
    
    cmd = [
        ffmpeg_exe, "-y",
        "-i", voice_path,
        "-stream_loop", "-1", "-i", bg_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", str(total_time),
        mixed_path
    ]
    
    start_t = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration_time = time.time() - start_t
    
    if res.returncode == 0 and os.path.exists(mixed_path):
        out_info = miniaudio.mp3_get_file_info(mixed_path)
        print(f"✅ SUCCESS: Mixed audio generated.")
        print(f"   Voice duration: {v_dur:.2f}s")
        print(f"   Expected Total: {total_time:.2f}s")
        print(f"   Actual Total: {out_info.duration:.2f}s")
        print(f"   Process Time: {duration_time:.2f}s")
        diff = abs(total_time - out_info.duration)
        if diff < 0.5:
             print("✅ PERFECT MATCH: Audio duration matches expected math!")
        else:
             print(f"⚠️ WARNING: Duration mismatch of {diff:.2f} seconds.")
    else:
        print("❌ ERROR: Ffmpeg failed with return code", res.returncode)
        print(res.stderr)

except Exception as e:
    print("❌ PYTHON EXCEPTION:", str(e))

# Cleanup
for f in [voice_path, bg_path, mixed_path]:
    if os.path.exists(f):
        os.remove(f)

print("Quality Control Check complete.")

"""
Streamlit Video Aspect Ratio Converter (Fast UI + FFmpeg Backend)
Keeps original UI, uses direct FFmpeg for speed.
"""

import streamlit as st
import tempfile
import subprocess
import shutil
from moviepy import VideoFileClip
from pathlib import Path
import os
import time


# ---- Page Configuration ----
st.set_page_config(
    page_title="Video Aspect Ratio Converter",
    page_icon="🎬",
    layout="wide"
)

# ---- Header ----
st.title("🎬 Streamlit Video Aspect Ratio Converter")
st.caption("Convert your 16:9 videos to 9:16 format for Instagram Reels, YouTube Shorts, and TikTok — now 5× faster!")

# ---- Check FFmpeg ----
FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    st.error("⚠️ FFmpeg not found! Install it from https://ffmpeg.org/download.html and restart the app.")
    st.stop()

# ---- Upload Section ----
uploaded = st.file_uploader("📤 Upload a 16:9 video", type=["mp4", "mov", "mkv", "avi"])

if uploaded:
    st.video(uploaded)
    
    # Extract original filename (without extension)
    original_filename = uploaded.name
    original_name = Path(original_filename).stem
    original_ext = Path(original_filename).suffix
    
    # Display the detected filename
    st.info(f"📁 Uploaded file: **{original_filename}**")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as tmp:
        tmp.write(uploaded.read())
        input_path = tmp.name

    clip = VideoFileClip(input_path)
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("Width", f"{clip.w}px")
    with info_col2:
        st.metric("Height", f"{clip.h}px")
    with info_col3:
        st.metric("FPS", f"{clip.fps:.1f}")
    st.info(f"🎞️ Duration: {clip.duration:.1f}s | Aspect Ratio: {clip.w/clip.h:.2f}:1")
    clip.close()

    # ---- Conversion Controls ----
    st.markdown("### ⚙️ Conversion Settings")
    method = st.radio("Choose conversion style:", ["Letterbox", "Crop", "Zoom"], horizontal=True)
    quality = st.select_slider("Select Quality", ["low", "medium", "high"], value="high")
    crf = {"low": 28, "medium": 23, "high": 18}[quality]
    
    # Create output filename - sanitize special characters that might cause issues
    safe_name = original_name.replace("|", "-").replace("/", "-").replace("\\", "-")
    output_filename = f"{safe_name}_9x16.mp4"
    
    # Show what the output filename will be
    st.info(f"💾 Output file will be named: **{output_filename}**")
    
    # Create output path
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, output_filename)

    # ---- Conversion ----
    if st.button("🚀 Convert Now", use_container_width=True):
        with st.spinner("⚙️ Converting via FFmpeg... Please wait"):
            start_time = time.time()

            # Get input dimensions
            clip = VideoFileClip(input_path)
            w, h = clip.w, clip.h
            clip.close()

            # Determine filter based on method
            if method == "Letterbox":
                out_h = int(w * 16 / 9)
                if out_h % 2: out_h += 1
                vf = f"pad={w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black"
            elif method == "Crop":
                new_w = int(h * 9 / 16)
                if new_w % 2: new_w -= 1
                x = (w - new_w) // 2
                vf = f"crop={new_w}:{h}:{x}:0"
            else:
                vf = "scale=-2:1920,crop=1080:1920"

            cmd = [
                FFMPEG, "-y", "-i", input_path,
                "-vf", vf,
                "-preset", "ultrafast",
                "-crf", str(crf),
                "-c:v", "libx264",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                output_path
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)

            end_time = time.time()
            elapsed = end_time - start_time

        if process.returncode == 0:
            st.success(f"✅ Conversion completed in {elapsed:.1f} seconds!")
            st.write(f"🎬 Output file created at: `{output_path}`")
            st.video(output_path)
            
            # Read the converted file and provide download with explicit filename
            try:
                with open(output_path, "rb") as f:
                    video_data = f.read()
                
                st.download_button(
                    label="⬇️ Download Converted Video",
                    data=video_data,
                    file_name=output_filename,
                    mime="video/mp4",
                    use_container_width=True,
                    key="download_btn"
                )
                
                st.success(f"✅ Click the button above to download as: **{output_filename}**")
                
            except Exception as e:
                st.error(f"Error preparing download: {e}")
        else:
            st.error("❌ Conversion failed! Check your FFmpeg installation.")
            st.code(process.stderr)

        # Cleanup temp files (after a delay to allow download)
        try:
            # Don't delete immediately, wait for download
            pass
        except:
            pass

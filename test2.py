"""
Streamlit Video Aspect Ratio Converter
Convert 16:9 videos to 9:16 for Instagram and TikTok
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from moviepy import VideoFileClip, ColorClip, CompositeVideoClip
from moviepy.video.fx.Crop import Crop
from moviepy.video.fx.Resize import Resize

# Page configuration
st.set_page_config(
    page_title="Video Aspect Ratio Converter",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF4B4B;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 1rem;
    }
    .stProgress > div > div > div > div {
        background-color: #FF4B4B;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D4EDDA;
        border: 1px solid #C3E6CB;
        color: #155724;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🎬 Video Aspect Ratio Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Convert 16:9 videos to 9:16 for Instagram, TikTok & Reels</div>', unsafe_allow_html=True)

# Conversion Functions
def letterbox_to_9_16(input_file, output_file, quality='high', progress_callback=None):
    """Convert video to 9:16 by adding black bars"""
    clip = VideoFileClip(input_file)
    
    # Get original dimensions
    original_width = clip.w
    original_height = clip.h
    
    # Calculate output dimensions (9:16 aspect ratio)
    output_width = original_width
    output_height = int((original_width * 16) / 9)
    
    # Make sure height is even
    if output_height % 2 != 0:
        output_height += 1
    
    # Calculate padding
    padding_total = output_height - original_height
    padding_top = padding_total // 2
    
    # Set CRF based on quality
    crf_values = {'high': 18, 'medium': 23, 'low': 28}
    crf = crf_values.get(quality, 18)
    
    # Create black background
    background = ColorClip(
        size=(output_width, output_height),
        color=(0, 0, 0),
        duration=clip.duration
    )
    
    # Position original video in center
    clip_centered = clip.with_position(('center', padding_top))
    
    # Composite video on black background
    final_clip = CompositeVideoClip([background, clip_centered])
    final_clip = final_clip.with_audio(clip.audio)
    
    # Write output video
    final_clip.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='192k',
        preset='medium',
        ffmpeg_params=['-crf', str(crf), '-movflags', '+faststart'],
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger=None
    )
    
    # Clean up
    clip.close()
    final_clip.close()
    background.close()
    
    return output_width, output_height


def crop_to_9_16(input_file, output_file, crop_position='center', progress_callback=None):
    """Convert video to 9:16 by cropping the sides"""
    clip_16_9 = VideoFileClip(input_file)
    
    # Get original dimensions
    original_width = clip_16_9.w
    original_height = clip_16_9.h
    
    # Calculate crop dimensions for 9:16 aspect ratio
    crop_height = original_height
    crop_width = int(crop_height * 9 / 16)
    
    # Make sure crop_width is even
    if crop_width % 2 != 0:
        crop_width -= 1
    
    # Calculate crop starting position
    if crop_position == 'center':
        x1 = (original_width - crop_width) / 2
        y1 = 0
    elif crop_position == 'left':
        x1 = 0
        y1 = 0
    elif crop_position == 'right':
        x1 = original_width - crop_width
        y1 = 0
    else:
        x1 = (original_width - crop_width) / 2
        y1 = 0
    
    # Apply crop
    clip_9_16 = Crop(x1=x1, y1=y1, width=crop_width, height=crop_height).apply(clip_16_9)
    
    # Write output video
    clip_9_16.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='192k',
        preset='medium',
        ffmpeg_params=['-crf', '18', '-movflags', '+faststart'],
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger=None
    )
    
    # Clean up
    clip_16_9.close()
    clip_9_16.close()
    
    return crop_width, crop_height


def convert_with_zoom(input_file, output_file, target_width=1080, target_height=1920, progress_callback=None):
    """Convert video to 9:16 with zooming to fill canvas"""
    clip = VideoFileClip(input_file)
    
    # Calculate scaling factor
    scale_w = target_width / clip.w
    scale_h = target_height / clip.h
    scale = max(scale_w, scale_h)
    
    # Resize video
    clip_resized = Resize(newsize=scale).apply(clip)
    
    # Calculate crop position (center)
    x_center = clip_resized.w / 2
    y_center = clip_resized.h / 2
    x1 = x_center - target_width / 2
    y1 = y_center - target_height / 2
    
    # Crop to final dimensions
    clip_final = Crop(x1=x1, y1=y1, width=target_width, height=target_height).apply(clip_resized)
    
    # Write output video
    clip_final.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='192k',
        preset='medium',
        ffmpeg_params=['-crf', '18', '-movflags', '+faststart'],
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger=None
    )
    
    clip.close()
    clip_final.close()
    
    return target_width, target_height


# Main App Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Video")
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'mov', 'avi', 'mkv'],
        help="Upload a 16:9 video to convert to 9:16"
    )
    
    if uploaded_file:
        st.video(uploaded_file)
        
        # Get video info
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        try:
            clip = VideoFileClip(tmp_path)
            st.info(f"""
            **Video Information:**
            - Resolution: {clip.w}×{clip.h}
            - Duration: {clip.duration:.2f} seconds
            - FPS: {clip.fps}
            - Aspect Ratio: {clip.w/clip.h:.2f}:1
            """)
            clip.close()
        except Exception as e:
            st.error(f"Error reading video: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

with col2:
    st.subheader("⚙️ Conversion Settings")
    
    # Conversion method
    conversion_method = st.radio(
        "Select Conversion Method",
        options=["Letterbox (Add Black Bars)", "Crop (Cut Sides)", "Zoom & Fill"],
        help="Choose how to convert your video to 9:16 format"
    )
    
    # Method-specific settings
    if conversion_method == "Letterbox (Add Black Bars)":
        st.info("✨ **Recommended for Instagram!** Adds black bars to preserve the entire video.")
        quality = st.select_slider(
            "Quality",
            options=['low', 'medium', 'high'],
            value='high',
            help="Higher quality = larger file size"
        )
        quality_info = {'low': 'CRF 28 - Smaller file', 'medium': 'CRF 23 - Balanced', 'high': 'CRF 18 - Best quality'}
        st.caption(quality_info[quality])
        
    elif conversion_method == "Crop (Cut Sides)":
        st.warning("⚠️ This will cut the left and right sides of your video.")
        crop_position = st.selectbox(
            "Crop Position",
            options=['center', 'left', 'right'],
            help="Choose which part of the video to keep"
        )
        
    else:  # Zoom & Fill
        st.info("🔍 Scales and crops video to fill the 9:16 canvas.")
        col_w, col_h = st.columns(2)
        with col_w:
            target_width = st.number_input("Width", value=1080, min_value=720, max_value=4320, step=1)
        with col_h:
            target_height = st.number_input("Height", value=1920, min_value=1280, max_value=7680, step=1)

# Convert button
st.markdown("---")
convert_button = st.button("🎬 Convert Video", type="primary", use_container_width=True)

if convert_button and uploaded_file:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_input:
        tmp_input.write(uploaded_file.getvalue())
        input_path = tmp_input.name
    
    # Create output file path
    output_path = tempfile.mktemp(suffix='_converted.mp4')
    
    try:
        with st.spinner("🎬 Converting video... This may take a few minutes..."):
            progress_bar = st.progress(0)
            
            # Perform conversion based on selected method
            if conversion_method == "Letterbox (Add Black Bars)":
                width, height = letterbox_to_9_16(input_path, output_path, quality)
                method_name = "Letterbox"
                
            elif conversion_method == "Crop (Cut Sides)":
                width, height = crop_to_9_16(input_path, output_path, crop_position)
                method_name = "Crop"
                
            else:  # Zoom & Fill
                width, height = convert_with_zoom(input_path, output_path, target_width, target_height)
                method_name = "Zoom"
            
            progress_bar.progress(100)
        
        # Success message
        st.markdown(f"""
        <div class="success-box">
            <h3>✅ Conversion Complete!</h3>
            <p><strong>Method:</strong> {method_name}</p>
            <p><strong>Output Resolution:</strong> {width}×{height} (9:16)</p>
            <p><strong>Audio:</strong> Preserved at 192k bitrate</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display converted video
        st.subheader("📺 Preview Converted Video")
        with open(output_path, 'rb') as video_file:
            video_bytes = video_file.read()
            st.video(video_bytes)
        
        # Download button
        st.subheader("💾 Download Your Video")
        output_filename = f"{Path(uploaded_file.name).stem}_9x16_{method_name.lower()}.mp4"
        st.download_button(
            label="⬇️ Download Converted Video",
            data=video_bytes,
            file_name=output_filename,
            mime="video/mp4",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error during conversion: {str(e)}")
        st.exception(e)
        
    finally:
        # Cleanup temporary files
        if os.path.exists(input_path):
            try:
                os.unlink(input_path)
            except:
                pass
        if os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass

elif convert_button and not uploaded_file:
    st.warning("⚠️ Please upload a video file first!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>📱 Perfect for Instagram, TikTok & Reels!</strong></p>
    <p>Supported formats: MP4, MOV, AVI, MKV</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown("""
    1. **Upload** your 16:9 video
    2. **Choose** a conversion method:
       - 🎯 **Letterbox**: Adds black bars (recommended)
       - ✂️ **Crop**: Cuts the sides
       - 🔍 **Zoom**: Scales to fill canvas
    3. **Configure** settings
    4. **Click** Convert Video
    5. **Download** your 9:16 video!
    """)
    
    st.header("💡 Tips")
    st.markdown("""
    - **Letterbox mode** is best for preserving your entire video
    - **Crop mode** works well for videos with centered subjects
    - **Zoom mode** is great for filling the screen completely
    - Higher quality = larger file size
    - Audio is always preserved at high quality!
    """)
    
    st.header("🎬 Conversion Methods")
    st.markdown("""
    **Letterbox** 📺
    - Adds black bars top/bottom
    - Keeps entire video visible
    - Best for most content
    
    **Crop** ✂️
    - Removes left/right sides
    - No black bars
    - May lose some content
    
    **Zoom** 🔍
    - Scales up to fill screen
    - Crops excess
    - Most immersive
    """)
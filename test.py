"""
Video Aspect Ratio Converter: 16:9 to 9:16
Two methods: Crop (cuts sides) or Letterbox (adds black bars)
Compatible with MoviePy 2.x - AUDIO PRESERVED
"""

from moviepy import VideoFileClip, ColorClip, CompositeVideoClip
from moviepy.video.fx.Crop import Crop
from moviepy.video.fx.Resize import Resize
def letterbox_to_9_16(input_file, output_file, quality='high'):
    """
    Convert video to 9:16 by adding black bars (letterbox) - NO CROPPING!
    Perfect for Instagram posts where you want to show the full video.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output video file
        quality (str): 'high' (CRF 18), 'medium' (CRF 23), 'low' (CRF 28)
    """
    print("="*60)
    print("🎬 LETTERBOX MODE - Adding Black Bars (No Cropping)")
    print("="*60)
    
    print(f"\n📂 Loading video: {input_file}")
    clip = VideoFileClip(input_file)
    
    # Get original dimensions
    original_width = clip.w
    original_height = clip.h
    original_aspect = original_width / original_height
    
    print(f"📊 Original dimensions: {original_width}×{original_height}")
    print(f"📐 Original aspect ratio: {original_aspect:.2f}:1")
    
    # Calculate output dimensions (9:16 aspect ratio)
    output_width = original_width
    output_height = int((original_width * 16) / 9)
    
    # Make sure height is even (required by some codecs)
    if output_height % 2 != 0:
        output_height += 1
    
    # Calculate padding
    padding_total = output_height - original_height
    padding_top = padding_total // 2
    padding_bottom = padding_total - padding_top
    
    print(f"\n✨ Output dimensions: {output_width}×{output_height}")
    print(f"📏 Black padding: {padding_top}px (top) + {padding_bottom}px (bottom)")
    print(f"🎯 Total padding: {padding_total}px")
    
    # Detect common resolutions
    resolution_name = "Custom"
    if original_width == 1280 and original_height == 720:
        resolution_name = "720p"
    elif original_width == 1920 and original_height == 1080:
        resolution_name = "1080p"
    elif original_width == 2560 and original_height == 1440:
        resolution_name = "2K"
    elif original_width == 3840 and original_height == 2160:
        resolution_name = "4K"
    
    print(f"📺 Detected resolution: {resolution_name}")
    
    # Set CRF based on quality
    crf_values = {'high': 18, 'medium': 23, 'low': 28}
    crf = crf_values.get(quality, 18)
    
    print(f"\n⚙️  Quality setting: {quality.upper()} (CRF {crf})")
    
    # Create black background
    background = ColorClip(
        size=(output_width, output_height),
        color=(0, 0, 0),
        duration=clip.duration
    )
    
    # Position original video in center
    clip_centered = clip.with_position(('center', padding_top))
    
    # Composite video on black background - AUDIO IS PRESERVED FROM ORIGINAL CLIP
    final_clip = CompositeVideoClip([background, clip_centered])
    final_clip = final_clip.with_audio(clip.audio)  # Explicitly set audio
    
    # Write output video with proper audio settings
    print(f"\n🎬 Writing output video: {output_file}")
    print("⏳ This may take a while depending on video length...")
    
    final_clip.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='192k',  # High quality audio
        preset='medium',
        ffmpeg_params=['-crf', str(crf), '-movflags', '+faststart'],
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger='bar'
    )
    
    # Clean up
    clip.close()
    final_clip.close()
    background.close()
    
    print("\n" + "="*60)
    print("✅ CONVERSION COMPLETE!")
    print("="*60)
    print(f"📁 Output saved to: {output_file}")
    print(f"📐 Final dimensions: {output_width}×{output_height} (9:16)")
    print("🔊 Audio: Preserved at 192k bitrate")
    print("🎉 Ready to upload to Instagram!")


def crop_to_9_16(input_file, output_file, crop_position='center'):
    """
    Convert a 16:9 video to 9:16 by cropping the sides.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output video file
        crop_position (str): 'center', 'left', or 'right' - where to crop from
    """
    print("="*60)
    print("✂️  CROP MODE - Cutting Left and Right Sides")
    print("="*60)
    
    print(f"\n📂 Loading video: {input_file}")
    clip_16_9 = VideoFileClip(input_file)
    
    # Get original dimensions
    original_width = clip_16_9.w
    original_height = clip_16_9.h
    
    print(f"📊 Original dimensions: {original_width}×{original_height}")
    
    # Calculate crop dimensions for 9:16 aspect ratio
    crop_height = original_height
    crop_width = int(crop_height * 9 / 16)
    
    # Make sure crop_width is even
    if crop_width % 2 != 0:
        crop_width -= 1
    
    print(f"✨ Crop dimensions: {crop_width}×{crop_height}")
    
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
        raise ValueError("crop_position must be 'center', 'left', or 'right'")
    
    print(f"🎯 Cropping from: {crop_position} (x={x1}, y={y1})")
    
    # Apply crop - audio is automatically preserved
    clip_9_16 = Crop(x1=x1, y1=y1, width=crop_width, height=crop_height).apply(clip_16_9)
    
    # Write output video with proper audio settings
    print(f"\n🎬 Writing output video: {output_file}")
    clip_9_16.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='192k',  # High quality audio
        preset='medium',
        ffmpeg_params=['-crf', '18', '-movflags', '+faststart'],
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger='bar'
    )
    
    # Clean up
    clip_16_9.close()
    clip_9_16.close()
    
    print("\n✅ Conversion complete!")
    print("🔊 Audio: Preserved at 192k bitrate")


def convert_with_zoom(input_file, output_file, target_width=1080, target_height=1920):
    """
    Convert video to 9:16 with zooming to fill the canvas.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output video file
        target_width (int): Desired output width (default: 1080)
        target_height (int): Desired output height (default: 1920)
    """
    print("="*60)
    print("🔍 ZOOM MODE - Scaling to Fill Canvas")
    print("="*60)
    
    print(f"\n📂 Loading video: {input_file}")
    clip = VideoFileClip(input_file)
    
    # Calculate scaling factor
    scale_w = target_width / clip.w
    scale_h = target_height / clip.h
    scale = max(scale_w, scale_h)
    
    print(f"📊 Original dimensions: {clip.w}×{clip.h}")
    print(f"🎯 Target dimensions: {target_width}×{target_height}")
    print(f"📈 Scale factor: {scale:.2f}x")
    
    # Resize video - audio is automatically preserved
    clip_resized = Resize(newsize=scale).apply(clip)
    
    # Calculate crop position (center)
    x_center = clip_resized.w / 2
    y_center = clip_resized.h / 2
    x1 = x_center - target_width / 2
    y1 = y_center - target_height / 2
    
    # Crop to final dimensions
    clip_final = Crop(x1=x1, y1=y1, width=target_width, height=target_height).apply(clip_resized)
    
    print(f"\n🎬 Writing output video: {output_file}")
    clip_final.write_videofile(
        output_file,
        codec='libx264',
        audio_codec='aac',
        audio_bitrate='192k',  # High quality audio
        preset='medium',
        ffmpeg_params=['-crf', '18', '-movflags', '+faststart'],
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger='bar'
    )
    
    clip.close()
    clip_final.close()
    print("\n✅ Conversion complete!")
    print("🔊 Audio: Preserved at 192k bitrate")


# Example usage
if __name__ == "__main__":
    input_video = "⚡🎵 Epic Electric Timer - 30 Seconds Countdown 🎵⚡.mp4"
    
    # ⭐ RECOMMENDED FOR INSTAGRAM: Letterbox mode (adds black bars, no cropping)
    # This keeps your entire video visible!
    letterbox_to_9_16(
        input_file=input_video,
        output_file="output_letterbox.mp4",
        quality='high'  # Options: 'high' (CRF 18), 'medium' (CRF 23), 'low' (CRF 28)
    )
    
    # Method 2: Crop mode (cuts left and right sides)
    # Uncomment to use:
    # crop_to_9_16(
    #     input_file=input_video,
    #     output_file="output_cropped.mp4",
    #     crop_position='center'  # Options: 'center', 'left', 'right'
    # )
    
    # Method 3: Zoom and crop to fill canvas
    # Uncomment to use:
    # convert_with_zoom(
    #     input_file=input_video,
    #     output_file="output_zoomed.mp4",
    #     target_width=1080,
    #     target_height=1920
    # )
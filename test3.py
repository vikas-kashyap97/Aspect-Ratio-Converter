"""
Terminal-Based Video Aspect Ratio Converter
Batch convert 16:9 videos to 9:16 format with parallel processing
Usage: python video_converter.py /path/to/videos/
"""

import os
import sys
import subprocess
import shutil
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy import VideoFileClip
import threading
from datetime import datetime


# Thread-safe lock for console output
print_lock = threading.Lock()


def safe_print(message, color=None):
    """Thread-safe colored printing."""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'reset': '\033[0m'
    }
    
    with print_lock:
        if color and color in colors:
            print(f"{colors[color]}{message}{colors['reset']}")
        else:
            print(message)


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        safe_print("❌ ERROR: FFmpeg not found! Please install FFmpeg first.", 'red')
        safe_print("Visit: https://ffmpeg.org/download.html", 'yellow')
        sys.exit(1)
    return ffmpeg


def get_video_info(video_path):
    """Extract video dimensions and metadata."""
    clip = None
    try:
        clip = VideoFileClip(video_path)
        info = {
            'width': clip.w,
            'height': clip.h,
            'fps': clip.fps,
            'duration': clip.duration,
            'aspect_ratio': clip.w / clip.h
        }
        return info
    except Exception as e:
        safe_print(f"⚠️  Failed to read {os.path.basename(video_path)}: {str(e)}", 'yellow')
        return None
    finally:
        if clip:
            try:
                clip.close()
            except:
                pass


def sanitize_filename(filename):
    """Remove problematic characters from filename."""
    # Remove file extension
    name = Path(filename).stem
    
    # Replace problematic characters
    for char in ['|', '/', '\\', ':', '*', '?', '"', '<', '>', '\x00', '｜']:
        name = name.replace(char, '-')
    
    return name


def convert_video(input_path, output_dir, method, quality, video_name):
    """
    Convert a single video with retry logic.
    """
    max_retries = 2
    crf_map = {"low": 28, "medium": 23, "high": 18}
    crf = crf_map.get(quality, 23)
    
    safe_name = sanitize_filename(video_name)
    output_filename = f"{safe_name}_9x16.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    # Check if output already exists
    if os.path.exists(output_path):
        safe_print(f"⏭️  Skipping {video_name} (already exists)", 'cyan')
        return {"success": True, "skipped": True, "output": output_path}
    
    for attempt in range(max_retries):
        clip = None
        try:
            # Verify input file
            if not os.path.exists(input_path):
                return {"success": False, "error": "Input file not found"}
            
            if os.path.getsize(input_path) == 0:
                return {"success": False, "error": "Input file is empty"}
            
            # Get dimensions
            try:
                clip = VideoFileClip(input_path)
                w, h = clip.w, clip.h
                clip.close()
                clip = None
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {"success": False, "error": f"Failed to read dimensions: {str(e)}"}
            
            # Validate dimensions
            if w <= 0 or h <= 0:
                return {"success": False, "error": f"Invalid dimensions: {w}x{h}"}
            
            # Determine filter based on method
            if method == "letterbox":
                out_h = int(w * 16 / 9)
                if out_h % 2:
                    out_h += 1
                vf = f"pad={w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black"
            elif method == "crop":
                new_w = int(h * 9 / 16)
                if new_w % 2:
                    new_w -= 1
                x = (w - new_w) // 2
                vf = f"crop={new_w}:{h}:{x}:0"
            else:  # zoom
                vf = "scale=-2:1920,crop=1080:1920"
            
            # FFmpeg command with proper encoding settings
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-vf", vf,
                "-preset", "fast",  # Changed from medium for better speed
                "-crf", str(crf),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",  # Ensure compatibility
                "-c:a", "aac",
                "-b:a", "192k",  # Increased audio bitrate
                "-ar", "48000",  # Standard audio sample rate
                "-movflags", "+faststart",
                "-max_muxing_queue_size", "9999",  # Increased from 1024
                "-async", "1",  # Audio sync
                output_path
            ]
            
            # Execute with proper encoding handling and suppressed output
            process = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,  # Completely suppress stderr to avoid Unicode errors
                timeout=600,  # 10 minute timeout
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Verify success
            if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return {"success": True, "output": output_path, "skipped": False}
            else:
                if attempt < max_retries - 1:
                    # Clean up failed attempt
                    if os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                        except:
                            pass
                    time.sleep(2)
                    continue
                
                return {"success": False, "error": f"FFmpeg process failed (exit code: {process.returncode})"}
        
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                safe_print(f"⚠️  Timeout on {video_name}, retrying...", 'yellow')
                # Clean up
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except:
                        pass
                continue
            return {"success": False, "error": "Conversion timeout (>10 minutes)"}
        
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": str(e)}
        
        finally:
            if clip:
                try:
                    clip.close()
                except:
                    pass
    
    return {"success": False, "error": "Max retries exceeded"}


def find_videos(input_path):
    """Find all video files in the given path."""
    video_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.MP4', '.MOV', '.MKV', '.AVI'}
    videos = []
    
    if os.path.isfile(input_path):
        # Single file
        if Path(input_path).suffix in video_extensions:
            videos.append(input_path)
    elif os.path.isdir(input_path):
        # Directory - find all videos
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if Path(file).suffix in video_extensions:
                    videos.append(os.path.join(root, file))
    
    return videos


def format_duration(seconds):
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def main():
    # ASCII Art Banner
    banner = """
╔═══════════════════════════════════════════════════════════╗
║     🎬 VIDEO ASPECT RATIO CONVERTER (16:9 → 9:16)       ║
║          Batch Processing with Parallel Execution         ║
╚═══════════════════════════════════════════════════════════╝
"""
    
    print(banner)
    
    # Check FFmpeg
    check_ffmpeg()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Convert 16:9 videos to 9:16 format for social media",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python video_converter.py /path/to/videos/
  python video_converter.py /path/to/video.mp4 --method crop --quality high
  python video_converter.py /path/to/videos/ --workers 4 --output /output/dir/
        """
    )
    
    parser.add_argument('input', help='Input video file or directory')
    parser.add_argument('-o', '--output', help='Output directory (default: input_dir/converted/)', default=None)
    parser.add_argument('-m', '--method', choices=['letterbox', 'crop', 'zoom'], 
                       default='letterbox', help='Conversion method (default: letterbox)')
    parser.add_argument('-q', '--quality', choices=['low', 'medium', 'high'],
                       default='high', help='Output quality (default: high)')
    parser.add_argument('-w', '--workers', type=int, default=2,
                       help='Number of parallel conversions (default: 2)')
    parser.add_argument('--skip-info', action='store_true',
                       help='Skip displaying video information')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input):
        safe_print(f"❌ ERROR: Input path does not exist: {args.input}", 'red')
        sys.exit(1)
    
    # Find all videos
    safe_print("🔍 Scanning for video files...", 'cyan')
    videos = find_videos(args.input)
    
    if not videos:
        safe_print("❌ No video files found!", 'red')
        sys.exit(1)
    
    safe_print(f"✅ Found {len(videos)} video file(s)\n", 'green')
    
    # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        if os.path.isfile(args.input):
            output_dir = os.path.join(os.path.dirname(args.input), 'converted')
        else:
            output_dir = os.path.join(args.input, 'converted')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    safe_print(f"📁 Output directory: {output_dir}", 'cyan')
    
    # Display video information
    if not args.skip_info:
        safe_print("\n📋 VIDEO INFORMATION:", 'blue')
        safe_print("─" * 80)
        
        for i, video in enumerate(videos, 1):
            info = get_video_info(video)
            if info:
                filename = os.path.basename(video)
                size_mb = os.path.getsize(video) / (1024 * 1024)
                safe_print(f"{i}. {filename}")
                safe_print(f"   Size: {size_mb:.1f}MB | Dimensions: {info['width']}x{info['height']} | "
                          f"FPS: {info['fps']:.1f} | Duration: {info['duration']:.1f}s")
        
        safe_print("─" * 80 + "\n")
    
    # Display settings
    safe_print("⚙️  CONVERSION SETTINGS:", 'blue')
    safe_print(f"   Method: {args.method.upper()}")
    safe_print(f"   Quality: {args.quality.upper()}")
    safe_print(f"   Parallel workers: {args.workers}")
    safe_print("")
    
    # Confirm
    response = input("🚀 Start conversion? [Y/n]: ").strip().lower()
    if response and response != 'y':
        safe_print("❌ Conversion cancelled.", 'yellow')
        sys.exit(0)
    
    print("\n" + "="*80)
    safe_print("🔄 STARTING BATCH CONVERSION...", 'cyan')
    print("="*80 + "\n")
    
    # Process videos
    start_time = time.time()
    results = []
    completed = 0
    total = len(videos)
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        future_to_video = {
            executor.submit(
                convert_video,
                video,
                output_dir,
                args.method,
                args.quality,
                os.path.basename(video)
            ): video for video in videos
        }
        
        # Process as they complete
        for future in as_completed(future_to_video):
            video = future_to_video[future]
            video_name = os.path.basename(video)
            
            try:
                result = future.result()
                completed += 1
                
                if result['success']:
                    if result.get('skipped'):
                        safe_print(f"[{completed}/{total}] ⏭️  SKIPPED: {video_name}", 'cyan')
                    else:
                        safe_print(f"[{completed}/{total}] ✅ SUCCESS: {video_name}", 'green')
                    results.append({'file': video_name, 'success': True})
                else:
                    safe_print(f"[{completed}/{total}] ❌ FAILED: {video_name}", 'red')
                    safe_print(f"           Error: {result['error']}", 'red')
                    results.append({'file': video_name, 'success': False, 'error': result['error']})
                
            except Exception as e:
                completed += 1
                safe_print(f"[{completed}/{total}] ❌ ERROR: {video_name}", 'red')
                safe_print(f"           Exception: {str(e)}", 'red')
                results.append({'file': video_name, 'success': False, 'error': str(e)})
    
    # Summary
    end_time = time.time()
    elapsed = end_time - start_time
    
    print("\n" + "="*80)
    safe_print("📊 CONVERSION SUMMARY", 'cyan')
    print("="*80)
    
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    safe_print(f"✅ Successful: {successful}/{total}", 'green')
    if failed > 0:
        safe_print(f"❌ Failed: {failed}/{total}", 'red')
    safe_print(f"⏱️  Total time: {format_duration(elapsed)}", 'cyan')
    safe_print(f"📁 Output location: {output_dir}", 'blue')
    
    # Failed files details
    if failed > 0:
        print("\n" + "─"*80)
        safe_print("❌ FAILED FILES:", 'red')
        for r in results:
            if not r['success']:
                safe_print(f"   • {r['file']}", 'red')
                safe_print(f"     Reason: {r.get('error', 'Unknown')}", 'yellow')
    
    print("="*80)
    
    if successful > 0:
        safe_print("\n🎉 Conversion completed! Check the output directory for converted videos.", 'green')
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n\n❌ Conversion interrupted by user.", 'yellow')
        sys.exit(1)
    except Exception as e:
        safe_print(f"\n\n❌ Fatal error: {str(e)}", 'red')
        sys.exit(1)
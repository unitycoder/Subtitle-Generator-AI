import subprocess

try:
    # Try to run ffmpeg -version
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=False)
    
    if result.returncode == 0:
        print("FFmpeg is installed and working:")
        print(result.stdout[:200] + "...")  # Print just the beginning of the output
    else:
        print("FFmpeg command failed with error:")
        print(result.stderr)
except Exception as e:
    print(f"Error running FFmpeg: {e}")

# Also check if imageio-ffmpeg is working
try:
    import imageio_ffmpeg
    print(f"\nimageio_ffmpeg version: {imageio_ffmpeg.__version__}")
    print(f"FFmpeg executable path: {imageio_ffmpeg.get_ffmpeg_exe()}")
except Exception as e:
    print(f"Error with imageio_ffmpeg: {e}") 
import whisper
import imageio_ffmpeg
import os
import sys

# Get FFmpeg path
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
print(f"FFmpeg path: {ffmpeg_path}")

# Set FFmpeg in environment
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")

# Load model
print("Loading tiny Whisper model...")
model = whisper.load_model("tiny")
print("Model loaded successfully!")

# Try transcribing a test audio file if provided
if len(sys.argv) > 1:
    audio_path = sys.argv[1]
    if os.path.exists(audio_path):
        print(f"Transcribing {audio_path}...")
        try:
            result = model.transcribe(audio_path)
            print("Transcription successful!")
            print("First 100 characters of transcript:")
            print(result["text"][:100] + "...")
        except Exception as e:
            print(f"Error transcribing: {e}")
    else:
        print(f"Audio file not found: {audio_path}")
else:
    print("No audio file provided for transcription.") 
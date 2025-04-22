import whisper
import srt
import datetime
import warnings
import os
import subprocess
import shlex
import imageio_ffmpeg  # Import imageio_ffmpeg to get the binary path
import numpy as np
import sys

# Suppress specific warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")

# Get the path to the FFmpeg binary
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
print(f"Using FFmpeg from: {FFMPEG_PATH}")

# Add FFmpeg to environment PATH so whisper can find it
ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# Monkey patch Whisper's audio loading function to use our FFmpeg path
def patch_whisper_audio_loading():
    from whisper.audio import load_audio, N_FRAMES, log_mel_spectrogram, pad_or_trim
    
    # Create a patched version that uses our FFmpeg path
    def patched_load_audio(file, sr=16000):
        """
        Load an audio file and return a numpy array of the audio data, resampled to 16kHz.
        """
        try:
            # Use our FFmpeg path
            cmd = [
                FFMPEG_PATH,
                "-nostdin",
                "-threads", "0",
                "-i", file,
                "-f", "s16le",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                "-ar", str(sr),
                "-"
            ]
            
            print(f"Running FFmpeg command: {' '.join(cmd)}")
            out = subprocess.run(cmd, capture_output=True, check=True).stdout
            return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            print(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"FFmpeg error: {error_msg}") from e
            
    # Replace the original function with our patched version
    import whisper.audio
    whisper.audio.load_audio = patched_load_audio

# Apply the patch
patch_whisper_audio_loading()

# Function to extract audio from video using ffmpeg
def extract_audio(video_path):
    # Generate the output audio file path
    audio_path = os.path.splitext(video_path)[0] + ".mp3"  # Save as .mp3 with same name
    
    # Properly quote the file paths for cmd
    command = f'"{FFMPEG_PATH}" -i "{video_path}" -vn -acodec mp3 -ar 44100 -ac 2 -ab 192k "{audio_path}"'
    
    # Execute the ffmpeg command
    print(f"Running extraction command: {command}")
    subprocess.run(command, check=True, shell=True)
    print(f"Audio extracted to: {audio_path}")
    return audio_path

# Function to generate SRT subtitles
def generate_srt(segments):
    subtitles = []
    for index, segment in enumerate(segments):
        start = datetime.timedelta(seconds=segment['start'])
        end = datetime.timedelta(seconds=segment['end'])
        content = segment['text']
        subtitle = srt.Subtitle(index=index + 1, start=start, end=end, content=content)
        subtitles.append(subtitle)
    return srt.compose(subtitles)

# Main script logic
def process_video(video_path):
    # Extract audio
    audio_file_path = extract_audio(video_path)

    # Load Whisper model
    print("Loading Whisper model...")
    model = whisper.load_model("tiny")  # Using tiny model for quick testing

    # Transcribe audio
    print(f"Transcribing audio from {audio_file_path}...")
    result = model.transcribe(audio_file_path)

    # Generate subtitles and save
    print("Generating subtitles...")
    subtitles = generate_srt(result['segments'])

    srt_output_path = os.path.splitext(video_path)[0] + ".srt"  # Subtitle file with same name
    with open(srt_output_path, "w", encoding="utf-8") as f:
        f.write(subtitles)

    print(f"Subtitles saved to: {srt_output_path}")
    print("Process completed successfully!")

if __name__ == "__main__":
    # Check if a video path was provided as a command-line argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print(f"Processing video: {video_path}")
        process_video(video_path)
    else:
        print("Please provide a video file path as a command-line argument.")
        print("Example: python test_sub.py path/to/your/video.mp4") 
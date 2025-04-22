import whisper
import srt
import datetime
import warnings
import os
import subprocess
import shlex
from tkinter import Tk, filedialog  # For file dialog
import imageio_ffmpeg  # Import imageio_ffmpeg to get the binary path
import numpy as np

# Suppress specific warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")

# Get the path to the FFmpeg binary
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

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
            
            out = subprocess.run(cmd, capture_output=True, check=True).stdout
            return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}") from e
            
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
    model = whisper.load_model("base")  # You can change the model size

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

# Example Usage
if __name__ == "__main__":
    # Use Tkinter file dialog to select the video file
    Tk().withdraw()  # Hide the main Tkinter window
    video_input = filedialog.askopenfilename(
        title="Select Video File",
        filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("All Files", "*.*")]
    )

    if video_input:
        process_video(video_input)
    else:
        print("No file selected. Exiting.")



import whisper

# Load a small model to test if whisper is properly installed
print("Loading Whisper model...")
model = whisper.load_model("tiny")  # Use the smallest model for quick test
print("Whisper model loaded successfully!") 
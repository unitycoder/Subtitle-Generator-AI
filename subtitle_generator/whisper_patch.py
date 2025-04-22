"""
Whisper Patch Module

Contains functionality for patching the Whisper audio loading function
to work with our custom FFmpeg configuration.
"""

import subprocess
import numpy as np


def patch_whisper_audio_loading(ffmpeg_path, log_callback=None):
    """
    Patch the Whisper audio loading function to use our FFmpeg path.
    
    Args:
        ffmpeg_path (str): Path to the FFmpeg executable
        log_callback (callable, optional): Function to call for logging
    """
    from whisper.audio import load_audio
    
    def log(message):
        """Log message using the callback if provided"""
        if log_callback:
            log_callback(message)
    
    # Create a patched version that uses our FFmpeg path
    def patched_load_audio(file, sr=16000):
        """
        Load an audio file and return a numpy array of the audio data, resampled to 16kHz.
        
        Args:
            file (str): Path to the audio file
            sr (int): Sample rate to resample to
            
        Returns:
            numpy.ndarray: Audio data as a numpy array
            
        Raises:
            RuntimeError: If FFmpeg fails to process the audio
        """
        try:
            # Use our FFmpeg path
            cmd = [
                ffmpeg_path,
                "-nostdin",
                "-threads", "0",
                "-i", file,
                "-f", "s16le",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                "-ar", str(sr),
                "-"
            ]
            
            log(f"Loading audio with FFmpeg...")
            out = subprocess.run(cmd, capture_output=True, check=True).stdout
            return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            log(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"FFmpeg error: {error_msg}") from e
    
    # Replace the original function with our patched version
    import whisper.audio
    whisper.audio.load_audio = patched_load_audio
    
    return patched_load_audio 
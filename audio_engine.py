import pyttsx3
import winsound
import subprocess
import os
import json
import wave
import threading

class AudioEngine:
    def __init__(self, offline_model_path="models/vosk-model-small-en-us-0.15"):
        # Initialize Text-to-Speech (Offline Fallback)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)

    def play_sound_cue(self, cue_type):
        """Plays a distinct sound cue for accessibility feedback."""
        def _play():
            if cue_type == "listening":
                winsound.Beep(800, 150) # High short beep
            elif cue_type == "success":
                winsound.Beep(600, 100)
                winsound.Beep(800, 150)
            elif cue_type == "error":
                winsound.Beep(300, 300) # Low long beep
                
        threading.Thread(target=_play, daemon=True).start()

    def speak(self, text):
        """
        Attempts to use edge-tts for high-quality online speech.
        Falls back to pyttsx3 if offline or if edge-tts fails.
        """
        
        # Try edge-tts first
        try:
            # We use the edge-tts CLI with --play to avoid needing pygame/mp3 players
            # This requires internet.
            command = ['edge-tts', '--text', text, '--play']
            # Hide console window for subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo)
            if result.returncode == 0:
                return # Successfully played online
        except Exception as e:
            pass # Fallthrough to offline

        # Fallback to pyttsx3 (offline)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def generate_audio_file(self, text, filepath="static/response.mp3"):
        """
        Generates an audio file from text. Useful for web frontend playback.
        """
        print(f"Generating audio file for: {text}")
        
        # Try edge-tts first
        try:
            command = ['edge-tts', '--text', text, '--write-media', filepath]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo)
            if result.returncode == 0:
                return True
        except Exception as e:
            pass
            
        # Fallback to pyttsx3
        try:
            self.engine.save_to_file(text, filepath)
            self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"TTS File Generation Error: {e}")
            return False

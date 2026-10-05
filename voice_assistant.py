"""
Required Dependencies:
pip install SpeechRecognition pyttsx3 customtkinter pyaudio

Note: PyAudio is required by SpeechRecognition for microphone access.
On Windows, 'pip install pyaudio' usually works directly if you have the necessary C++ build tools, 
or you can use precompiled wheels.
"""

import speech_recognition as sr
import pyttsx3
import customtkinter as ctk
import threading
import queue
import time
import sys

class VoiceAssistant:
    def __init__(self):
        # State can be "IDLE" or "ACTIVE"
        self.state = "IDLE" 
        
        # Queues for thread-safe communication
        # command_queue sends instructions to the main thread (e.g., open/close GUI)
        # ui_queue sends text updates to the GUI from the background thread
        self.command_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        
        # Start the background listening thread
        # daemon=True ensures the thread exits when the main program exits
        self.listener_thread = threading.Thread(target=self.listening_loop, daemon=True)
        self.listener_thread.start()
        
    def listening_loop(self):
        # Initialize pyttsx3 in the thread it will be used to prevent COM thread issues on Windows
        engine = pyttsx3.init()
        
        def speak(text):
            """Helper function to play text-to-speech synchronously."""
            engine.say(text)
            engine.runAndWait()

        recognizer = sr.Recognizer()
        
        try:
            microphone = sr.Microphone()
        except OSError:
            print("Error: No default microphone found. Please connect a microphone.")
            return

        print("Calibrating microphone for ambient noise...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Ready. Waiting for trigger word 'start'...")

        while True:
            try:
                with microphone as source:
                    # Update UI status if active
                    if self.state == "ACTIVE":
                        self.ui_queue.put({"type": "status", "text": "Listening..."})
                    
                    # Listen for audio (timeout avoids blocking forever if there's no sound)
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    if self.state == "ACTIVE":
                        self.ui_queue.put({"type": "status", "text": "Processing..."})
                        
                    # Recognize speech using Google Web Speech API
                    text = recognizer.recognize_google(audio).lower()
                    print(f"[{self.state}] Heard: {text}")
                    
                    # Handle commands based on current state
                    if self.state == "IDLE":
                        if "start" in text:
                            self.state = "ACTIVE"
                            speak("Assistant activated.")
                            # Signal main thread to launch the GUI
                            self.command_queue.put("start")
                            
                    elif self.state == "ACTIVE":
                        # Send user transcript to UI
                        self.ui_queue.put({"type": "transcript", "text": f"User: {text}"})
                        
                        # Stop Logic
                        if "stop" in text or "exit" in text:
                            speak("Shutting down assistant.")
                            self.state = "IDLE"
                            # Signal main thread to close GUI and clear UI
                            self.command_queue.put("stop")
                            self.ui_queue.put({"type": "stop"})
                        else:
                            # Echo back or process other commands here
                            response = f"I heard: {text}"
                            self.ui_queue.put({"type": "transcript", "text": f"Assistant: {response}"})
                            speak(response)
                            
            except sr.WaitTimeoutError:
                # No speech detected within timeout, loop again cleanly
                continue
            except sr.UnknownValueError:
                # Speech was detected but was unintelligible
                if self.state == "ACTIVE":
                    self.ui_queue.put({"type": "status", "text": "Didn't catch that."})
            except sr.RequestError as e:
                # API was unreachable or unresponsive
                if self.state == "ACTIVE":
                    self.ui_queue.put({"type": "status", "text": "Network error."})
                print(f"Could not request results; {e}")
            except Exception as e:
                print(f"Unexpected error in listener loop: {e}")
                time.sleep(1) # Prevent rapid error spam in the console

class AssistantGUI(ctk.CTk):
    def __init__(self, ui_queue):
        super().__init__()
        self.ui_queue = ui_queue
        
        # Configure window
        self.title("Voice Assistant")
        self.geometry("450x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # UI Elements
        self.status_label = ctk.CTkLabel(
            self, 
            text="Initializing...", 
            font=ctk.CTkFont(family="Inter", size=20, weight="bold")
        )
        self.status_label.pack(pady=(20, 10))
        
        self.log_box = ctk.CTkTextbox(
            self, 
            width=400, 
            height=500, 
            font=ctk.CTkFont(family="Inter", size=14),
            wrap="word"
        )
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)
        self.log_box.insert("end", "Assistant started. Say 'stop' to minimize.\n\n")
        self.log_box.configure(state="disabled")
        
        # Start checking the queue for updates
        self.after(100, self.process_queue)
        
    def process_queue(self):
        """Thread-safe method to process UI updates from the background listener thread."""
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg["type"] == "status":
                    self.status_label.configure(text=msg["text"])
                elif msg["type"] == "transcript":
                    self.log_box.configure(state="normal")
                    self.log_box.insert("end", msg["text"] + "\n\n")
                    self.log_box.see("end")
                    self.log_box.configure(state="disabled")
                elif msg["type"] == "stop":
                    self.destroy()
                    return
        except queue.Empty:
            pass
            
        # Schedule the next check in 100 milliseconds
        self.after(100, self.process_queue)

def main():
    print("Initializing Voice Assistant System...")
    assistant = VoiceAssistant()
    
    # The main thread serves as the UI manager and lifecycle controller.
    # It waits for the background thread to signal that it should open the GUI.
    while True:
        try:
            # Block until a command is received from the background thread
            cmd = assistant.command_queue.get()
            
            if cmd == "start":
                # Create and launch the GUI (mainloop blocks until the GUI is destroyed)
                print("Trigger word detected. Opening GUI...")
                app = AssistantGUI(assistant.ui_queue)
                app.mainloop()
                
                # Once GUI is destroyed, clear any stale messages from the UI queue
                while not assistant.ui_queue.empty():
                    try:
                        assistant.ui_queue.get_nowait()
                    except queue.Empty:
                        break
                        
        except KeyboardInterrupt:
            print("\nExiting application...")
            sys.exit(0)

if __name__ == "__main__":
    main()

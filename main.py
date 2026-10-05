import customtkinter as ctk
import threading
import sys
from assistant import Assistant

class PrintRedirector:
    def __init__(self, text_widget, original_stream=None):
        self.text_widget = text_widget
        self.original_stream = original_stream

    def write(self, string):
        if self.original_stream:
            try:
                self.original_stream.write(string)
                self.original_stream.flush()
            except UnicodeEncodeError:
                safe_string = string.encode('ascii', 'replace').decode('ascii')
                self.original_stream.write(safe_string)
                self.original_stream.flush()
            
        def update_gui():
            self.text_widget.insert("end", string)
            self.text_widget.see("end")
        self.text_widget.after(0, update_gui)

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()

class VoiceAssistantUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide window until loaded

        self.title("Voice Assistant Monitor")
        self.geometry("600x400")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="Voice Assistant is Running (Headless Mode Active)", font=ctk.CTkFont(size=16, weight="bold"))
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Log Box
        self.log_box = ctk.CTkTextbox(self, state="normal")
        self.log_box.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        # Input Frame
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your command here...")
        self.entry.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")
        self.entry.bind("<Return>", self.send_command)

        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", command=self.send_command)
        self.send_btn.grid(row=0, column=1, padx=0, pady=10)

        # Redirect stdout/stderr to the text box
        sys.stdout = PrintRedirector(self.log_box, sys.stdout)
        sys.stderr = PrintRedirector(self.log_box, sys.stderr)
        
        print("Application Started. Type your command below.")
        
        # Initialize Assistant
        self.assistant = Assistant()
        self.check_loaded()

    def check_loaded(self):
        if self.assistant.intelligence is not None:
            self.log_box.delete("1.0", "end") # Clear loading logs
            self.deiconify() # Show window
            print("Hello sir all commands are ready\n")
        else:
            self.after(500, self.check_loaded)

    def send_command(self, event=None):
        text = self.entry.get().strip()
        if text:
            if getattr(self.assistant, 'is_processing', False):
                print("\n[Jarvis is currently thinking. Please wait before asking another question!]\n")
                return
                
            self.assistant.is_processing = True
            self.entry.delete(0, 'end')
            print(f"\nUser: {text}")
            
            # Run command processing in background to avoid freezing the UI
            def run_and_unlock():
                try:
                    self.assistant.process_command(text)
                finally:
                    self.assistant.is_processing = False
                    
            threading.Thread(target=run_and_unlock, daemon=True).start()

    def on_closing(self):
        print("Shutting down...")
        self.assistant.running = False
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = VoiceAssistantUI()
    app.mainloop()

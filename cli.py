import sys
import threading
import time
from assistant import Assistant

def run_cli():
    print("=============================================")
    print("         JARVIS AI TERMINAL INTERFACE        ")
    print("=============================================")
    print("Initializing Assistant Core...")
    
    jarvis = Assistant()
    
    print("Waiting for Intelligence Core & RAG to load...")
    # Wait until daemon thread finishes loading the brain
    while jarvis.intelligence is None:
        time.sleep(1)
        
    print("\n✅ Jarvis is online!")
    print("Type your commands below. Type 'exit' or 'quit' to close.")
    print("=============================================\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("Jarvis: Shutting down. Goodbye!")
                break
                
            response = jarvis.process_web_command(user_input)
            print(f"Jarvis: {response}")
            
        except KeyboardInterrupt:
            print("\nJarvis: Force shutting down. Goodbye!")
            break
        except Exception as e:
            print(f"Jarvis encountered an error: {e}")

if __name__ == "__main__":
    run_cli()

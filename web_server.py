from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from assistant import Assistant
import os
import time
import glob

app = Flask(__name__)
CORS(app)

# Initialize Assistant
print("Initializing Jarvis Assistant...")
jarvis = Assistant()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/command', methods=['POST'])
def handle_command():
    data = request.json
    text = data.get('text', '')
    
    print(f"Received command from web: {text}")
    
    # Process the text
    response_text = jarvis.process_web_command(text)
    
    # Generate audio for the response
    if response_text:
        static_dir = os.path.join(app.root_path, 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        # Cleanup old response files to prevent disk bloat
        for old_file in glob.glob(os.path.join(static_dir, "response_*.mp3")):
            try:
                os.remove(old_file)
            except:
                pass
                
        audio_filename = f"response_{int(time.time())}.mp3"
        audio_path = os.path.join(static_dir, audio_filename)
        
        success = jarvis.audio.generate_audio_file(response_text, filepath=audio_path)
        
        audio_url = f"/static/{audio_filename}" if success else None
    else:
        response_text = "I couldn't understand that."
        audio_url = None

    return jsonify({
        "response": response_text,
        "audio_url": audio_url
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Render-compatible audio directory
AUDIO_DIR = '/tmp/tts_audio'
os.makedirs(AUDIO_DIR, exist_ok=True)

# Available voices
VOICES = {
    'en-US-AriaNeural': 'Aria (US English - Female)',
    'en-US-DavisNeural': 'Davis (US English - Male)',
    'en-US-JennyNeural': 'Jenny (US English - Female)',
    'en-US-GuyNeural': 'Guy (US English - Male)',
    'en-GB-SoniaNeural': 'Sonia (UK English - Female)',
    'en-GB-RyanNeural': 'Ryan (UK English - Male)',
    'en-AU-NatashaNeural': 'Natasha (Australian - Female)',
    'en-AU-WilliamNeural': 'William (Australian - Male)',
    'fr-FR-DeniseNeural': 'Denise (French - Female)',
    'fr-FR-HenriNeural': 'Henri (French - Male)',
    'es-ES-ElviraNeural': 'Elvira (Spanish - Female)',
    'es-ES-AlvaroNeural': 'Alvaro (Spanish - Male)',
    'de-DE-KatjaNeural': 'Katja (German - Female)',
    'de-DE-ConradNeural': 'Conrad (German - Male)',
    'it-IT-ElsaNeural': 'Elsa (Italian - Female)',
    'it-IT-DiegoNeural': 'Diego (Italian - Male)',
    'ja-JP-NanamiNeural': 'Nanami (Japanese - Female)',
    'ja-JP-KeitaNeural': 'Keita (Japanese - Male)',
    'ko-KR-SunHiNeural': 'SunHi (Korean - Female)',
    'ko-KR-InJoonNeural': 'InJoon (Korean - Male)',
    'zh-CN-XiaoxiaoNeural': 'Xiaoxiao (Chinese - Female)',
    'zh-CN-YunxiNeural': 'Yunxi (Chinese - Male)',
}

async def generate_speech(text, voice, rate, pitch):
    """Generate speech using edge-tts"""
    try:
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        rate_str = f"{rate:+d}%" if rate != 0 else "+0%"
        pitch_str = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"
        
        communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        await communicate.save(filepath)
        
        return filepath, filename
    except Exception as e:
        raise Exception(f"Failed to generate speech: {str(e)}")

def cleanup_old_files():
    """Clean up audio files older than 1 hour"""
    try:
        current_time = datetime.now().timestamp()
        for filename in os.listdir(AUDIO_DIR):
            filepath = os.path.join(AUDIO_DIR, filename)
            if os.path.isfile(filepath):
                file_time = os.path.getctime(filepath)
                if current_time - file_time > 3600:
                    os.remove(filepath)
    except Exception:
        pass

@app.route('/')
def index():
    """Main page with TTS form"""
    cleanup_old_files()
    return render_template('index.html', voices=VOICES)

@app.route('/generate', methods=['POST'])
def generate():
    """Generate TTS audio"""
    try:
        text = request.form.get('text', '').strip()
        voice = request.form.get('voice', 'en-US-AriaNeural')
        rate = int(request.form.get('rate', 0))
        pitch = int(request.form.get('pitch', 0))
        
        if not text:
            return jsonify({'error': 'Please enter some text'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Text is too long (max 5000 characters)'}), 400
        
        if voice not in VOICES:
            return jsonify({'error': 'Invalid voice selected'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            filepath, filename = loop.run_until_complete(generate_speech(text, voice, rate, pitch))
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'Audio generated successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio file"""
    try:
        filepath = os.path.join(AUDIO_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=False, mimetype='audio/mpeg')
        else:
            return "Audio file not found", 404
    except Exception as e:
        return f"Error serving audio: {str(e)}", 500

@app.route('/download/<filename>')
def download_audio(filename):
    """Download generated audio file"""
    try:
        filepath = os.path.join(AUDIO_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=f'tts_{filename}')
        else:
            return "Audio file not found", 404
    except Exception as e:
        return f"Error downloading audio: {str(e)}", 500

@app.route('/voices')
def get_voices():
    """Get available voices as JSON"""
    return jsonify(VOICES)

# Important: Render needs this
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

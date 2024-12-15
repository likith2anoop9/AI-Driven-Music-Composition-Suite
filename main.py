from flask import Flask, render_template, request, send_file, jsonify
import requests
import openai
import os
import json
from pydub import AudioSegment
import subprocess
import uuid
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
import music21

app = Flask(__name__)

# Constants
CHUNK_SIZE = 1024
XI_API_KEY = "your_elevenlabs_api_key"

# Create necessary directories
os.makedirs("static/sheets", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Musical presets and settings
GENRE_PRESETS = {
    'pop': {
        'tempo': 120,
        'instruments': ['piano', 'drums', 'bass', 'synth', 'guitar', 'strings'],
        'default_key': 'C'
    },
    'rock': {
        'tempo': 130,
        'instruments': ['guitar', 'drums', 'bass', 'piano', 'synth'],
        'default_key': 'E'
    },
    'jazz': {
        'tempo': 90,
        'instruments': ['piano', 'bass', 'drums', 'saxophone', 'trumpet', 'strings'],
        'default_key': 'Dm'
    },
    'hip_hop': {
        'tempo': 95,
        'instruments': ['drums', 'bass', 'synth', 'piano', 'turntable', 'beatbox'],
        'default_key': 'Am'
    }
}

MOOD_SETTINGS = {
    "happy": {
        "key_preference": ["C", "G", "D"],
        "tempo_range": (120, 140),
        "instrument_preference": ["piano", "guitar", "strings"]
    },
    "sad": {
        "key_preference": ["Am", "Em", "Dm"],
        "tempo_range": (60, 80),
        "instrument_preference": ["piano", "strings"]
    },
    "energetic": {
        "key_preference": ["E", "A"],
        "tempo_range": (140, 180),
        "instrument_preference": ["drums", "guitar", "synth"]
    }
}

def generate_lyric_sheet(lyrics, title, tempo, key):
    """Generate a PDF containing formatted lyrics and musical information."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"static/sheets/lyrics_{timestamp}_{uuid.uuid4()}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        textColor=colors.HexColor('#1DB954'),
        spaceAfter=30
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        textColor=colors.gray,
        fontSize=10,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        textColor=colors.white,
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10
    )
    
    lyric_style = ParagraphStyle(
        'Lyric',
        parent=styles['Normal'],
        textColor=colors.black,
        fontSize=12,
        leading=16
    )
    
    # Add title
    story.append(Paragraph(title, title_style))
    
    # Add musical information
    info_text = f"Key: {key} | Tempo: {tempo} BPM | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(info_text, info_style))
    
    # Process lyrics
    for line in lyrics.split('\n'):
        if line.strip():
            if line.startswith('['):
                # Section header
                story.append(Paragraph(line, section_style))
            else:
                # Regular lyric line
                story.append(Paragraph(line, lyric_style))
    
    doc.build(story)
    return filename.replace("static/", "/static/")

def generate_musical_notation(melody, title, key, tempo):
    """Generate musical notation in both MusicXML and PDF formats."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"score_{timestamp}_{uuid.uuid4()}"
        xml_filename = f"static/sheets/{base_filename}.xml"
        
        # Create score
        score = music21.stream.Score()
        
        # Add metadata
        score.insert(0, music21.metadata.Metadata())
        score.metadata.title = title
        
        # Create part
        part = music21.stream.Part()
        
        # Add time signature and key signature
        part.append(music21.meter.TimeSignature('4/4'))
        part.append(music21.key.Key(key))
        
        # Add tempo marking
        part.append(music21.tempo.MetronomeMark(number=tempo))
        
        # Add melody notes with more musical variety
        for note_data in melody:
            note = music21.note.Note(
                note_data['pitch'],
                quarterLength=note_data['duration']
            )
            # Add articulations and dynamics for more musical detail
            if 'articulation' in note_data:
                note.articulations.append(
                    music21.articulations.articleToArticulation(note_data['articulation'])
                )
            if 'dynamic' in note_data:
                note.dynamic = note_data['dynamic']
            part.append(note)
        
        score.append(part)
        
        # Export as MusicXML
        score.write('musicxml', xml_filename)
        
        return {
            'xml': xml_filename.replace("static/", "/static/"),
            'preview_url': f"/preview_sheet/{base_filename}"  # New preview URL
        }
    except Exception as e:
        print(f"Error generating notation: {str(e)}")
        return None

def apply_genre_preset(genre):
    return GENRE_PRESETS.get(genre.lower(), GENRE_PRESETS["pop"])

def create_arrangement(instruments, sections=["intro", "verse", "chorus", "bridge", "outro"]):
    arrangement = {}
    for section in sections:
        if section == "intro":
            arrangement[section] = instruments[:2]
        elif section == "chorus":
            arrangement[section] = instruments
        elif section == "bridge":
            arrangement[section] = instruments[1:-1]
        else:
            arrangement[section] = instruments[:-1]
    return arrangement

# Download file function (unchanged)
def download_file(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return filename
    except Exception as e:
        return f"Error downloading {filename}: {e}"

def get_available_voices():
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        if response.ok:
            voices = response.json().get("voices", [])
            return [{"id": voice["voice_id"], "name": voice["name"]} for voice in voices]
        else:
            raise Exception("Failed to fetch voices: " + response.text)
    except Exception as e:
        return []

def clone_voice(audio_file_path, voice_id, output_path="cloned_output.mp3"):
    sts_url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}/stream"
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }
    data = {
        "model_id": "eleven_english_sts_v2",
        "voice_settings": json.dumps({
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        })
    }

    try:
        # Check if the audio path is from a pre-loaded source
        if isinstance(audio_file_path, str) and audio_file_path.startswith("uploads/temp_source_"):
            input_path = audio_file_path
        else:
            # Normal file upload handling
            input_path = audio_file_path
        # Step 1: Run Demucs for source separation
        subprocess.run(["demucs", audio_file_path], check=True)
        demucs_output_dir = os.path.join("separated", "htdemucs", os.path.splitext(os.path.basename(audio_file_path))[0])
        
        bass_path = os.path.join(demucs_output_dir, "bass.wav")
        drums_path = os.path.join(demucs_output_dir, "drums.wav")
        other_path = os.path.join(demucs_output_dir, "other.wav")

        if not all(os.path.exists(p) for p in [bass_path, drums_path, other_path]):
            raise FileNotFoundError("One or more instrumental components are missing!")

        bass = AudioSegment.from_file(bass_path)
        drums = AudioSegment.from_file(drums_path)
        other = AudioSegment.from_file(other_path)
        instrumental = bass.overlay(drums).overlay(other)

        instrumental_path = "combined_instrumental.wav"
        instrumental.export(instrumental_path, format="wav")

        # Step 2: Use ElevenLabs API for voice cloning
        with open(audio_file_path, "rb") as audio_file:
            files = {"audio": audio_file}
            response = requests.post(sts_url, headers=headers, data=data, files=files, stream=True)

        if response.ok:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)

            # Step 3: Merge cloned voice with instrumentals
            cloned_audio = AudioSegment.from_file(output_path)
            combined_audio = instrumental.overlay(cloned_audio)
            combined_audio.export(output_path, format="mp3")
            return output_path
        else:
            error_message = response.json().get("detail", {}).get("message", "Unknown error")
            raise Exception(f"Error from ElevenLabs API: {error_message}")

    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")
    finally:
        # Clean up temporary files
        if isinstance(audio_file_path, str) and audio_file_path.startswith("uploads/temp_source_"):
            try:
                os.remove(audio_file_path)
            except:
                pass

# Feedback storage (in-memory for demo, should use database in production)
feedback_storage = {}

def store_feedback(song_id, feedback_type, feedback_text):
    """Store feedback for a song."""
    if song_id not in feedback_storage:
        feedback_storage[song_id] = []
    
    feedback_storage[song_id].append({
        'type': feedback_type,
        'text': feedback_text,
        'timestamp': datetime.now().isoformat()
    })

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/preview_sheet/<filename>')
def preview_sheet(filename):
    return render_template('sheet_preview.html', 
                         xml_path=f"/static/sheets/{filename}.xml")

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form
    prompt = data.get('prompt')
    style = data.get('style', 'bollywood hip hop')
    title = data.get('title', '')
    key = data.get('key')
    tempo = int(data.get('tempo', 120))
    artist = data.get('artist')
    mood = data.get('mood')
    genre = data.get('genre')
    # Get the previewed lyrics
    previewed_lyrics = data.get('previewed_lyrics')
    
    try:
        instruments = json.loads(data.get('instruments', '[]'))
    except:
        instruments = []

    result = generate_lyrics(
        prompt=prompt,
        style=style,
        title=title,
        key=key,
        tempo=tempo,
        instruments=instruments,
        artist=artist,
        mood=mood,
        genre=genre,
        previewed_lyrics=previewed_lyrics  # Pass the previewed lyrics
    )
    
    if isinstance(result, str):
        return jsonify({"error": result})

    return jsonify(result)



@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    song_id = data.get('song_id')
    feedback_type = data.get('type')
    feedback_text = data.get('feedback')
    
    if not all([song_id, feedback_type, feedback_text]):
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields'
        }), 400
    
    # Store feedback
    store_feedback(song_id, feedback_type, feedback_text)
    
    # Return appropriate next steps based on feedback type
    next_steps = []
    if feedback_type == 'lyrics':
        next_steps = [
            'Analyzing lyrical feedback...',
            'Maintaining musical elements and style',
            'Regenerating lyrics with adjustments'
        ]
    elif feedback_type == 'melody':
        next_steps = [
            'Analyzing melodic feedback...',
            'Keeping current key and tempo',
            'Adjusting melody progression'
        ]
    elif feedback_type == 'instruments':
        next_steps = [
            'Analyzing arrangement feedback...',
            'Maintaining core musical elements',
            'Adjusting instrumental balance'
        ]
    
    return jsonify({
        'status': 'success',
        'message': 'Feedback received',
        'next_steps': next_steps
    })

@app.route('/download_sheet/<filename>')
def download_sheet(filename):
    filepath = f'static/sheets/{filename}.xml'
    return send_file(filepath, as_attachment=True)

@app.route('/generate_lyrics', methods=['POST'])
def generate_lyrics_preview():
    data = request.form
    prompt = data.get('prompt')
    edits = data.get('edits', '')
    
    try:
        # Build enhanced prompt that includes previous lyrics if edits are provided
        if edits:
            # Get the current lyrics from the frontend
            current_lyrics = data.get('current_lyrics', '')
            # Create a more detailed prompt with both current lyrics and requested changes
            enhanced_prompt = f"""
Current lyrics:
{current_lyrics}

Requested changes:
{edits}

Please generate new lyrics that incorporate these changes while maintaining the overall theme:
{prompt}
"""
        else:
            enhanced_prompt = prompt
            
        # Generate lyrics using GPT
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative assistant generating song lyrics."},
                {"role": "user", "content": f"Generate song lyrics in the format:\n[Verse]\n<lyrics line 1>\n<lyrics line 2>\n...\n[Chorus]\n<chorus line 1>\n<chorus line 2>\n...\n based on this prompt: {enhanced_prompt}"}
            ]
        )
        
        generated_lyrics = gpt_response["choices"][0]["message"]["content"]
        
        return jsonify({
            "lyrics": generated_lyrics,
            "success": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clone_voice', methods=['GET', 'POST'])
def clone_voice_page():
    if request.method == 'POST':
        # Check if we're using source audio or file upload
        source_audio = request.form.get('source_audio')
        
        if source_audio:
            # Using pre-downloaded source audio
            file_path = source_audio
        else:
            # Using uploaded file
            if 'audio' not in request.files:
                return jsonify({"error": "No audio file provided"}), 400
            audio_file = request.files['audio']
            file_path = os.path.join("uploads", audio_file.filename)
            audio_file.save(file_path)

        selected_voice_id = request.form.get('voice_id')
        if not selected_voice_id:
            return jsonify({"error": "No voice selected"}), 400

        try:
            output_file = clone_voice(file_path, selected_voice_id)
            return send_file(output_file, as_attachment=True)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            # Clean up temporary files
            if os.path.exists(file_path):
                os.remove(file_path)

    # Handle GET request with source URL
    source_url = request.args.get('source')
    if source_url:
        try:
            # Download the source audio
            temp_filename = f"temp_source_{uuid.uuid4()}.mp3"
            temp_filepath = os.path.join("uploads", temp_filename)
            os.makedirs("uploads", exist_ok=True)
            
            response = requests.get(source_url)
            with open(temp_filepath, 'wb') as f:
                f.write(response.content)
                
            # Pass this file path to the template
            available_voices = get_available_voices()
            return render_template('clone_voice.html', 
                                voices=available_voices,
                                source_audio=temp_filepath,
                                source_url=source_url)
        except Exception as e:
            print(f"Error downloading source audio: {str(e)}")
            available_voices = get_available_voices()
            return render_template('clone_voice.html', voices=available_voices)
    
    # Normal page load without source audio
    available_voices = get_available_voices()
    return render_template('clone_voice.html', voices=available_voices)


# The generate_lyrics function needs to be added here - should I continue with that?

def generate_lyrics(prompt, style="bollywood hip hop", title="", key=None, tempo=120, 
                   instruments=None, artist=None, mood=None, genre=None, previewed_lyrics=None):
    url = "https://api.acedata.cloud/suno/audios"
    
    headers = {
        "accept": "application/json",
        "authorization": "Bearer your_ace_data_api_key",
        "content-type": "application/json"
    }

    # Apply genre preset if specified
    if genre:
        preset = apply_genre_preset(genre)
        tempo = tempo or preset["tempo"]
        key = key or preset["default_key"]
        instruments = instruments or preset["instruments"]

    # Apply mood settings if specified
    if mood and mood in MOOD_SETTINGS:
        mood_preset = MOOD_SETTINGS[mood]
        if not key:
            key = mood_preset["key_preference"][0]
        if not tempo:
            tempo = (mood_preset["tempo_range"][0] + mood_preset["tempo_range"][1]) // 2
        if not instruments:
            instruments = mood_preset["instrument_preference"]

    # Create enhanced prompt
    enhanced_prompt = f"Create a song in {key if key else 'any key'} "
    if artist:
        enhanced_prompt += f"in the style of {artist} "
    enhanced_prompt += f"at {tempo} BPM. "
    if instruments:
        enhanced_prompt += f"Using {', '.join(instruments)}. "
    if mood:
        enhanced_prompt += f"The mood should be {mood}. "
    enhanced_prompt += prompt

    try:
        # Use previewed lyrics if available, otherwise generate new ones
        if previewed_lyrics:
            generated_lyrics = previewed_lyrics
        else:
            gpt_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative assistant generating song lyrics."},
                    {"role": "user", "content": f"Generate song lyrics in the format:\n[Verse]\n<lyrics line 1>\n<lyrics line 2>\n...\n[Chorus]\n<chorus line 1>\n<chorus line 2>\n...\n based on this prompt: {enhanced_prompt}"}
                ]
            )
            generated_lyrics = gpt_response["choices"][0]["message"]["content"]

        # Create arrangement
        arrangement = create_arrangement(instruments if instruments else ["piano", "drums", "bass"])

        payload = {
            "action": "generate",
            "prompt": enhanced_prompt,
            "model": "chirp-v3-5",
            "lyric": generated_lyrics,  # Use either previewed or generated lyrics
            "custom": True,
            "instrumental": False,
            "title": title if title else "Generated Song",
            "style": style,
            "musical_settings": {
                "key": key,
                "tempo": int(tempo),
                "instruments": instruments or [],
                "arrangement": arrangement
            }
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success", False):
                results = response_data.get("data", [])
                output = []
                
                for result in results:
                    try:
                        # Generate lyric sheet
                        lyric_sheet = generate_lyric_sheet(
                            generated_lyrics,
                            title if title else "Generated Song",
                            tempo,
                            key
                        )
                    except Exception as e:
                        print(f"Error generating lyric sheet: {str(e)}")
                        lyric_sheet = None

                    # Create song ID for feedback tracking
                    song_id = str(uuid.uuid4())
                    if song_id not in feedback_storage:
                        feedback_storage[song_id] = []

                    output_item = {
                        "audio_url": result.get("audio_url"),
                        "video_url": result.get("video_url"),
                        "lyric_sheet": lyric_sheet,
                        "lyrics": generated_lyrics,
                        "song_id": song_id,
                        "settings_used": {
                            "key": key,
                            "tempo": tempo,
                            "instruments": instruments,
                            "mood": mood,
                            "genre": genre,
                            "style": style,
                            "artist_reference": artist
                        },
                        "feedback_options": {
                            "lyrics": True,
                            "melody": True,
                            "instruments": True
                        },
                        "revision_count": 0,
                        "can_revise": True
                    }
                    output.append(output_item)
                
                return output
            else:
                error_message = response_data.get("message", "Task did not succeed.")
                print(f"API Error: {error_message}")
                return {"error": error_message}
        else:
            error_message = f"Failed to connect to the API. Status Code: {response.status_code}"
            print(error_message)
            return {"error": error_message}

    except openai.error.OpenAIError as e:
        error_message = f"Error generating lyrics: {str(e)}"
        print(error_message)
        return {"error": error_message}
    except requests.exceptions.RequestException as e:
        error_message = f"Network error: {str(e)}"
        print(error_message)
        return {"error": error_message}
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(error_message)
        return {"error": error_message}

if __name__ == '__main__':
    app.run(debug=True)
